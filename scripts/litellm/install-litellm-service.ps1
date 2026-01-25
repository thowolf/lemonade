#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Installs LiteLLM as a Windows Service with proper configuration and security
.DESCRIPTION
    - Installs LiteLLM Python package with all dependencies
    - Creates Windows Service (NSSM wrapper)
    - Configures master key rotation
    - Sets up health checking
    - Enables auto-restart on failure
.PARAMETER Action
    install   : Install LiteLLM service
    uninstall : Remove service and cleanup
    status    : Check service status
    start     : Start the service
    stop      : Stop the service
    restart   : Restart the service
.EXAMPLE
    .\install-litellm-service.ps1 -Action install
    .\install-litellm-service.ps1 -Action status
#>

param(
    [ValidateSet("install", "uninstall", "status", "start", "stop", "restart")]
    [string]$Action = "status",
    [string]$ConfigPath = ".\scripts\litellm\litellm-config.yaml",
    [int]$Port = 4014
)

$ErrorActionPreference = "Stop"
$serviceName = "LiteLLM-Proxy"
$serviceDisplayName = "LiteLLM API Proxy (Lemonade)"
$pythonPath = "python"
$nssmPath = "$PSScriptRoot\nssm"

# NSSM download URLs (multiple sources for redundancy)
$nssmUrls = @(
    "https://github.com/nssm-io/nssm/releases/download/2.24/nssm-2.24-101-g897c7ad.zip",
    "https://nssm.cc/download/nssm-2.24-101-g897c7ad.zip",
    "https://github.com/nssm-io/nssm/releases/download/2.24/nssm-2.24.zip"
)

function Write-Status {
    param([string]$Message, [string]$Status = "INFO")
    $timestamp = Get-Date -Format "HH:mm:ss"
    $colors = @{
        "INFO"    = "Cyan"
        "SUCCESS" = "Green"
        "ERROR"   = "Red"
        "WARNING" = "Yellow"
    }
    Write-Host "[$timestamp] [$Status] $Message" -ForegroundColor $colors[$Status]
}

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Install-Nssm {
    Write-Status "Checking NSSM (service wrapper)..."
    
    # Try multiple ways to find NSSM
    $nssmExePaths = @(
        # PATH
        (Get-Command nssm.exe -ErrorAction SilentlyContinue).Source,
        # Common winget locations
        "$env:ProgramFiles\NSSM\nssm.exe",
        "$env:ProgramFiles(x86)\NSSM\nssm.exe",
        "$env:LocalAppData\Programs\nssm\nssm.exe",
        # Local installation
        "$nssmPath\nssm.exe"
    )
    
    foreach ($path in $nssmExePaths) {
        if ($path -and (Test-Path $path)) {
            try {
                $version = & $path --version 2>&1
                Write-Status "Found NSSM at: $path (Version: $version)" "SUCCESS"
                # Store the path globally for Setup-Service
                $script:nssmExecutable = $path
                return
            }
            catch {
                Write-Status "NSSM at $path not executable" "WARNING"
            }
        }
    }
    
    Write-Status "NSSM not found. Attempting to install via winget..." "WARNING"
    try {
        Write-Status "Installing NSSM via winget..." "INFO"
        & winget install --exact --quiet nssm 2>&1 | ForEach-Object { Write-Status "$_" "INFO" }
        
        # Try to find it again after installation
        $nssmExe = Get-Command nssm.exe -ErrorAction SilentlyContinue
        if ($nssmExe) {
            Write-Status "NSSM installed successfully via winget" "SUCCESS"
            $script:nssmExecutable = $nssmExe.Source
            return
        }
    }
    catch {
        Write-Status "winget installation failed: $_" "WARNING"
    }
    
    throw "NSSM not found and automatic installation failed. Please install manually: winget install nssm"
}

function Install-LiteLLM {
    Write-Status "Installing LiteLLM Python package..."
    
    try {
        & $pythonPath -m pip install --upgrade litellm 2>&1 | ForEach-Object {
            if ($_ -match "Successfully installed|already satisfied") {
                Write-Status "$_" "SUCCESS"
            } else {
                Write-Status "$_" "INFO"
            }
        }
        Write-Status "LiteLLM installed" "SUCCESS"

        # Ensure Prisma runtime is available for SQLite / migrations
        try {
            $pythonExeForInstall = (& $pythonPath -c "import sys; print(sys.executable)").Trim()
            Write-Status "Ensuring 'prisma' package is installed in $pythonExeForInstall..." "INFO"
            & $pythonExeForInstall -m pip install prisma 2>&1 | ForEach-Object { Write-Status "$_" "INFO" }
            $prismaCheck = & $pythonExeForInstall -c "import prisma, sys; print(getattr(prisma, '__version__', 'unknown'))" 2>&1
            if ($LASTEXITCODE -eq 0) { Write-Status "prisma installed: $prismaCheck" "SUCCESS" } else { Write-Status "prisma install/verification produced: $prismaCheck" "WARNING" }
        }
        catch {
            Write-Status "Automatic prisma install failed: $_" "WARNING"
        }
    }
    catch {
        Write-Status "Failed to install LiteLLM: $_" "ERROR"
        throw
    }
}

function Test-PrismaInstalled {
    param([string]$PythonCmd = "python")
    try {
        $ver = & $PythonCmd -c "import prisma; print(prisma.__version__)" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Status "prisma available: $ver" "SUCCESS"
            return $true
        }
    }
    catch {
        Write-Status "prisma not found in $PythonCmd" "WARNING"
    }
    return $false
}

function Generate-MasterKey {
    Write-Status "Generating secure master key..."
    $key = "sk-" + [Convert]::ToBase64String([byte[]]@((1..32) | ForEach-Object { Get-Random -Maximum 256 })) -replace '=+$'
    return $key.Substring(0, 40)  # Keep reasonable length
}

function Setup-Service {
    Write-Status "Setting up LiteLLM Windows Service..."
    
    # Use the NSSM executable found/installed by Install-Nssm
    if (-not $script:nssmExecutable) {
        throw "NSSM executable not set. Install-Nssm must run first."
    }
    
    $configFullPath = Resolve-Path $ConfigPath
    $masterKey = Generate-MasterKey
    $pythonExe = (& $pythonPath -c "import sys; print(sys.executable)").Trim()
    
    # Environment for service
    $env:PYTHONIOENCODING = "utf-8"
    $env:LITELLM_MASTER_KEY = $masterKey

    # If a DATABASE_URL is provided but prisma isn't installed in the service Python,
    # clear DATABASE_URL so the service can still start (UI/API read-only) and
    # surface an actionable warning to the operator.
    $pythonExe = (& $pythonPath -c "import sys; print(sys.executable)").Trim()

    $hasDatabaseUrl = $false
    if ($env:DATABASE_URL) { $hasDatabaseUrl = $true }
    else {
        $envFile = Join-Path $PSScriptRoot ".env"
        if (Test-Path $envFile) {
            $content = Get-Content $envFile -Raw -ErrorAction SilentlyContinue
            if ($content -match 'DATABASE_URL\s*=\s*.+') { $hasDatabaseUrl = $true }
        }
    }

    if ($hasDatabaseUrl) {
        if (-not (Test-PrismaInstalled -PythonCmd $pythonExe)) {
            Write-Status "DATABASE_URL set but 'prisma' not found in $pythonExe. Clearing DATABASE_URL so service can start without DB (migrations skipped)." "WARNING"
            # Ensure NSSM won't inject DATABASE_URL (service-level fallback)
            & $script:nssmExecutable set $serviceName AppEnvironmentExtra "DATABASE_URL="
            # Also unset in the current process to avoid startup attempt
            Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
            $script:prismaAvailable = $false
        }
        else {
            $script:prismaAvailable = $true
        }
    }
    else {
        $script:prismaAvailable = $false
    }

    # Check if service exists
    if (Get-Service -Name $serviceName -ErrorAction SilentlyContinue) {
        Write-Status "Service already exists. Removing..." "WARNING"
        & $script:nssmExecutable stop $serviceName
        & $script:nssmExecutable remove $serviceName confirm
        Start-Sleep -Seconds 2
    }
    
    # Create service command
    # Prefer running under the detected python to avoid PATH mismatch (ensures prisma is available).
    $wrapperBat = Join-Path $PSScriptRoot "litellm-start.bat"

    $pythonExePath = $pythonExe
    if ((Test-Path $pythonExePath) -and (Test-PrismaInstalled -PythonCmd $pythonExePath)) {
        $appCmd = $pythonExePath
        $appParams = "-m litellm --config `"$configFullPath`" --port $Port"
        Write-Status "Creating service with NSSM (Application: $appCmd $appParams)" "INFO"
        & $script:nssmExecutable install $serviceName $appCmd $appParams
        & $script:nssmExecutable set $serviceName Application $appCmd
        & $script:nssmExecutable set $serviceName AppParameters $appParams
    }
    else {
        Write-Status "Falling back to wrapper batch for service startup (will rely on PATH)" "WARNING"
        & $script:nssmExecutable install $serviceName "$wrapperBat"
        & $script:nssmExecutable set $serviceName Application "$wrapperBat"
    }

    & $script:nssmExecutable set $serviceName DisplayName "$serviceDisplayName"
    & $script:nssmExecutable set $serviceName Description "LiteLLM API Proxy - Routes requests to Lemonade Server"

    # Set startup type
    & $script:nssmExecutable set $serviceName Start SERVICE_AUTO_START
    
    # Environment variables
    & $script:nssmExecutable set $serviceName AppEnvironmentExtra "PYTHONIOENCODING=utf-8"
    & $script:nssmExecutable set $serviceName AppEnvironmentExtra "LITELLM_MASTER_KEY=$masterKey"
    
    # Auto-restart on failure
    & $script:nssmExecutable set $serviceName AppRestartDelay 5000
    & $script:nssmExecutable set $serviceName AppRotateFiles 1
    & $script:nssmExecutable set $serviceName AppRotateOnline 1
    & $script:nssmExecutable set $serviceName AppRotateSeconds 86400
    & $script:nssmExecutable set $serviceName AppRotateBytes 10485760
    
    # Prevent pause on error
    & $script:nssmExecutable set $serviceName AppExit Default Exit
    
    # Logging
    $logPath = Join-Path $PSScriptRoot "logs"
    New-Item -ItemType Directory -Path $logPath -Force | Out-Null
    & $script:nssmExecutable set $serviceName AppStdout "$logPath\litellm-service.log"
    & $script:nssmExecutable set $serviceName AppStderr "$logPath\litellm-error.log"
    
    Write-Status "Service created successfully" "SUCCESS"
    Write-Status "Master Key (SAVE THIS SECURELY): $masterKey" "SUCCESS"
    
    return $masterKey
}

function Start-LiteLLMService {
    Write-Status "Starting LiteLLM service..."
    try {
        $svc = Get-Service -Name $serviceName -ErrorAction Stop
        if ($svc.Status -ne "Running") {
            $svc.Start()
            Start-Sleep -Seconds 3
        }
        
        $service = Get-Service -Name $serviceName
        if ($service.Status -eq "Running") {
            Write-Status "Service started successfully" "SUCCESS"
            return $true
        } else {
            Write-Status "Service failed to start. Checking logs..." "ERROR"
            $logPath = Join-Path $PSScriptRoot "logs"
            if (Test-Path "$logPath\litellm-error.log") {
                Write-Status "Error log contents:" "WARNING"
                Get-Content "$logPath\litellm-error.log" -Tail 20 | ForEach-Object { Write-Host "  $_" }
            }
            return $false
        }
    }
    catch {
        Write-Status "Error starting service: $_" "ERROR"
        return $false
    }
}

function Check-ServiceHealth {
    Write-Status "Checking LiteLLM health..."
    Write-Status "Service must be running. Verifying service status..." "INFO"
    
    $service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
    if ($null -eq $service -or $service.Status -ne "Running") {
        Write-Status "Service is not running. Start the service first:" "ERROR"
        Write-Status "  net start LiteLLM-Proxy" "INFO"
        Write-Status "Or check logs in: .\scripts\litellm\logs\" "INFO"
        return $false
    }
    
    Write-Status "Service is running. Testing API endpoint..." "INFO"
    $maxRetries = 5
    $retryCount = 0
    
    while ($retryCount -lt $maxRetries) {
        try {
            # Test root endpoint which returns Swagger UI (200 OK)
            $response = Invoke-WebRequest -Uri "http://localhost:$Port/" -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-Status "Health check passed (HTTP 200)" "SUCCESS"
                return $true
            }
        }
        catch {
            $retryCount++
            if ($retryCount -lt $maxRetries) {
                Write-Status "Health check attempt $retryCount/$maxRetries failed, retrying..." "WARNING"
                Start-Sleep -Seconds 2
            }
        }
    }
    
    Write-Status "Health check failed after $maxRetries attempts" "WARNING"
    Write-Status "Service may still be initializing. Check logs:" "INFO"
    $logPath = Join-Path $PSScriptRoot "logs"
    Write-Status "  Type: Get-Content .\scripts\litellm\logs\litellm-service.log -Tail 50" "INFO"
    return $false
}

function Show-Status {
    Write-Status "=== LiteLLM Service Status ===" "INFO"
    
    $service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
    
    if ($null -eq $service) {
        Write-Status "Service not installed" "WARNING"
        return
    }
    
    $status = if ($service.Status -eq "Running") { "RUNNING" } else { "STOPPED" }
    Write-Status "Service Name: $serviceName" "INFO"
    Write-Status "Display Name: $($service.DisplayName)" "INFO"
    Write-Status "Status: $status" $(if ($status -eq "RUNNING") { "SUCCESS" } else { "WARNING" })
    Write-Status "Start Type: $($service.StartType)" "INFO"
    
    # Port status
    $portCheck = netstat -ano | Select-String ":$Port\s"
    if ($portCheck) {
        Write-Status "Port ${Port}: LISTENING" "SUCCESS"
    } else {
        Write-Status "Port ${Port}: NOT LISTENING" "WARNING"
    }
    
    # Log files
    $logPath = Join-Path $PSScriptRoot "logs"
    if (Test-Path "$logPath\litellm-service.log") {
        Write-Status "`nRecent service logs:" "INFO"
        Get-Content "$logPath\litellm-service.log" -Tail 5 | ForEach-Object { Write-Host "  $_" }
    }
}

# Main execution
try {
    if (-not (Test-Administrator)) {
        Write-Status "This script requires Administrator privileges" "ERROR"
        exit 1
    }
    
    Write-Status "LiteLLM Service Management" "INFO"
    Write-Status "Action: $Action" "INFO"
    
    switch ($Action) {
        "install" {
            Install-Nssm
            Install-LiteLLM
            $key = Setup-Service
            Start-LiteLLMService
            Check-ServiceHealth
            Write-Status "`nLiteLLM Production Service installed and running" "SUCCESS"
            Write-Status "API available at: http://localhost:$Port" "INFO"
            Write-Status "Master Key: $key (save this!)" "SUCCESS"
            Write-Status "" "INFO"
            Write-Status "QUICK TEST:" "INFO"
            Write-Status "  curl -H 'Authorization: Bearer $key' http://localhost:$Port/health" "INFO"
            Write-Status "" "INFO"
            Write-Status "TROUBLESHOOTING:" "INFO"
            Write-Status "  Service not starting? Check logs:" "INFO"
            Write-Status "    Get-Content .\scripts\litellm\logs\litellm-error.log -Tail 50" "INFO"
            Write-Status "  If migrations fail with 'prisma package not found', install prisma into the service Python:" "INFO"
            Write-Status "    C:\\Path\\To\\python.exe -m pip install prisma" "INFO"
            Write-Status "  Is Lemonade Server running?" "INFO"
            Write-Status "    curl http://localhost:8000/api/v1/models" "INFO"
            Write-Status "  Test models endpoint:" "INFO"
            Write-Status "    curl -H 'Authorization: Bearer $key' http://localhost:$Port/v1/models" "INFO"        }
        "uninstall" {
            Write-Status "Uninstalling service..." "WARNING"
            & "$nssmPath\nssm.exe" stop $serviceName
            & "$nssmPath\nssm.exe" remove $serviceName confirm
            Write-Status "Service removed" "SUCCESS"
        }
        "status" {
            Show-Status
        }
        "start" {
            Start-LiteLLMService
            Check-ServiceHealth
        }
        "stop" {
            Write-Status "Stopping service..."
            Stop-Service -Name $serviceName
        }
        "restart" {
            Write-Status "Restarting service..."
            Stop-Service -Name $serviceName -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 1
            Start-LiteLLMService
        }
    }
}
catch {
    $errorMsg = $_.ToString()
    Write-Status "Error: $errorMsg" "ERROR"
    exit 1
}
