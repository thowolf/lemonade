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
    
    # First, check if NSSM is already in PATH (from winget or manual installation)
    try {
        $nssmCheck = & nssm.exe --version 2>&1
        Write-Status "NSSM already in PATH: $nssmCheck" "SUCCESS"
        return
    }
    catch {
        Write-Status "NSSM not in PATH, attempting download..." "WARNING"
    }
    
    if (Test-Path "$nssmPath\nssm.exe") {
        Write-Status "NSSM already installed locally" "SUCCESS"
        return
    }
    
    Write-Status "Downloading NSSM from multiple sources..."
    $tempZip = "$PSScriptRoot\nssm-temp.zip"
    $downloaded = $false
    
    foreach ($url in $nssmUrls) {
        try {
            Write-Status "Trying: $url" "INFO"
            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
            Invoke-WebRequest -Uri $url -OutFile $tempZip -ErrorAction Stop
            $downloaded = $true
            Write-Status "Download successful from: $url" "SUCCESS"
            break
        }
        catch {
            Write-Status "Failed: $_" "WARNING"
        }
    }
    
    if (-not $downloaded) {
        Write-Status "All NSSM download sources failed. Trying manual fallback..." "WARNING"
        Write-Status "Please download NSSM manually from: https://nssm.cc/download" "WARNING"
        Write-Status "Extract to: $nssmPath" "WARNING"
        Write-Status "Then run: .\install-litellm-service.ps1 -Action install" "WARNING"
        throw "NSSM download failed from all sources"
    }
    
    try {
        Expand-Archive -Path $tempZip -DestinationPath "$PSScriptRoot\nssm-extract" -Force
        
        Get-ChildItem "$PSScriptRoot\nssm-extract" -Recurse -Filter "nssm.exe" | 
            ForEach-Object { Copy-Item -Path $_.Directory -Destination $nssmPath -Recurse -Force }
        
        Remove-Item $tempZip, "$PSScriptRoot\nssm-extract" -Recurse -Force
        Write-Status "NSSM installed" "SUCCESS"
    }
    catch {
        Write-Status "Failed to extract NSSM: $_" "ERROR"
        throw
    }
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
    }
    catch {
        Write-Status "Failed to install LiteLLM: $_" "ERROR"
        throw
    }
}

function Generate-MasterKey {
    Write-Status "Generating secure master key..."
    $key = "sk-" + [Convert]::ToBase64String([byte[]]@((1..32) | ForEach-Object { Get-Random -Maximum 256 })) -replace '=+$'
    return $key.Substring(0, 40)  # Keep reasonable length
}

function Setup-Service {
    Write-Status "Setting up LiteLLM Windows Service..."
    
    $configFullPath = Resolve-Path $ConfigPath
    $masterKey = Generate-MasterKey
    $pythonExe = (& $pythonPath -c "import sys; print(sys.executable)").Trim()
    
    # Find nssm.exe (either in PATH or local)
    $nssmExe = $null
    try {
        $nssmExe = (Get-Command nssm.exe -ErrorAction Stop).Source
        Write-Status "Using NSSM from PATH: $nssmExe" "INFO"
    }
    catch {
        if (Test-Path "$nssmPath\nssm.exe") {
            $nssmExe = "$nssmPath\nssm.exe"
            Write-Status "Using local NSSM: $nssmExe" "INFO"
        }
        else {
            throw "NSSM not found in PATH or local directory"
        }
    }
    
    # Environment for service
    $env:PYTHONIOENCODING = "utf-8"
    $env:LITELLM_MASTER_KEY = $masterKey
    
    # Check if service exists
    if (Get-Service -Name $serviceName -ErrorAction SilentlyContinue) {
        Write-Status "Service already exists. Removing..." "WARNING"
        & $nssmExe stop $serviceName
        & $nssmExe remove $serviceName confirm
        Start-Sleep -Seconds 2
    }
    
    # Create service command
    $serviceCmd = "$pythonExe -m litellm.main --config `"$configFullPath`" --port $Port"
    
    Write-Status "Creating service with NSSM..."
    & $nssmExe install $serviceName $serviceCmd
    & $nssmExe set $serviceName DisplayName "$serviceDisplayName"
    & $nssmExe set $serviceName Description "LiteLLM API Proxy - Routes requests to Lemonade Server"
    
    # Set startup type
    & $nssmExe set $serviceName Start SERVICE_AUTO_START
    
    # Environment variables
    & $nssmExe set $serviceName AppEnvironmentExtra "PYTHONIOENCODING=utf-8"
    & $nssmExe set $serviceName AppEnvironmentExtra "LITELLM_MASTER_KEY=$masterKey"
    
    # Auto-restart on failure
    & $nssmExe set $serviceName AppRestartDelay 5000
    & $nssmExe set $serviceName AppRotateFiles 1
    & $nssmExe set $serviceName AppRotateOnline 1
    & $nssmExe set $serviceName AppRotateSeconds 86400
    & $nssmExe set $serviceName AppRotateBytes 10485760
    
    # Logging
    $logPath = Join-Path $PSScriptRoot "logs"
    New-Item -ItemType Directory -Path $logPath -Force | Out-Null
    & $nssmExe set $serviceName AppStdout "$logPath\litellm-service.log"
    & $nssmExe set $serviceName AppStderr "$logPath\litellm-error.log"
    
    Write-Status "Service created successfully" "SUCCESS"
    Write-Status "Master Key (SAVE THIS SECURELY): $masterKey" "SUCCESS"
    
    return $masterKey
}

function Start-Service {
    Write-Status "Starting LiteLLM service..."
    try {
        Start-Service -Name $serviceName -ErrorAction Stop
        Start-Sleep -Seconds 2
        
        $service = Get-Service -Name $serviceName
        if ($service.Status -eq "Running") {
            Write-Status "Service started successfully" "SUCCESS"
            return $true
        } else {
            Write-Status "Service failed to start" "ERROR"
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
    
    $maxRetries = 10
    $retryCount = 0
    
    while ($retryCount -lt $maxRetries) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:$Port/v1/health" -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-Status "Health check passed (HTTP 200)" "SUCCESS"
                return $true
            }
        }
        catch {
            $retryCount++
            if ($retryCount -lt $maxRetries) {
                Write-Status "Health check attempt $retryCount/$maxRetries failed, retrying..." "WARNING"
                Start-Sleep -Seconds 1
            }
        }
    }
    
    Write-Status "Health check failed after $maxRetries attempts" "ERROR"
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
            Start-Service
            Check-ServiceHealth
            Write-Status "`nLiteLLM Production Service installed and running" "SUCCESS"
            Write-Status "API available at: http://localhost:$Port" "INFO"
            Write-Status "Master Key: $key (save this!)" "SUCCESS"
        }
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
            Start-Service
            Check-ServiceHealth
        }
        "stop" {
            Write-Status "Stopping service..."
            Stop-Service -Name $serviceName
        }
        "restart" {
            Write-Status "Restarting service..."
            Restart-Service -Name $serviceName
            Start-Sleep -Seconds 2
            Check-ServiceHealth
        }
    }
}
catch {
    $errorMsg = $_.ToString()
    Write-Status "Error: $errorMsg" "ERROR"
    exit 1
}
