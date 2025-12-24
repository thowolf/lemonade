# AMD AI Max+ 395 ROCm Production Deployment Script
# This script automates the complete deployment process for AMD AI Max+ 395 hardware

param(
    [Parameter(Mandatory=$false)]
    [switch]$SkipHardwareCheck,

    [Parameter(Mandatory=$false)]
    [switch]$SkipROCmInstall,

    [Parameter(Mandatory=$false)]
    [switch]$SkipPythonSetup,

    [Parameter(Mandatory=$false)]
    [switch]$SkipLemonadeServer,

    [Parameter(Mandatory=$false)]
    [switch]$SkipTestingFramework,

    [Parameter(Mandatory=$false)]
    [switch]$SkipValidation,

    [Parameter(Mandatory=$false)]
    [string]$LemonadeVersion = "9.1.1",

    [Parameter(Mandatory=$false)]
    [string]$PythonVersion = "3.11",

    [Parameter(Mandatory=$false)]
    [string]$ROCmVersion = "7.1.1",

    [Parameter(Mandatory=$false)]
    [string]$LogFile = "$PSScriptRoot\deployment_log_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt",

    [Parameter(Mandatory=$false)]
    [switch]$EnableVerbose
)

# Configuration
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# Global variables
$ScriptRoot = $PSScriptRoot
$DeploymentRoot = Split-Path $PSScriptRoot -Parent
$LogStream = $null

# Logging functions
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")

    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "[$Timestamp] [$Level] $Message"

    # Write to console with color
    switch ($Level) {
        "ERROR" { Write-Host $LogMessage -ForegroundColor Red }
        "WARNING" { Write-Host $LogMessage -ForegroundColor Yellow }
        "SUCCESS" { Write-Host $LogMessage -ForegroundColor Green }
        "INFO" { if ($EnableVerbose) { Write-Host $LogMessage -ForegroundColor White } }
        default { Write-Host $LogMessage -ForegroundColor Gray }
    }

    # Write to log file
    if ($LogStream) {
        $LogStream.WriteLine($LogMessage)
    }
}

function Start-Logging {
    try {
        $script:LogStream = [System.IO.StreamWriter]::new($LogFile, $false, [System.Text.Encoding]::UTF8)
        Write-Log "Starting AMD AI Max+ 395 deployment script" "INFO"
        Write-Log "Log file: $LogFile" "INFO"
    } catch {
        Write-Error "Failed to create log file: $_"
        exit 1
    }
}

function Stop-Logging {
    if ($LogStream) {
        Write-Log "Deployment script completed" "INFO"
        $LogStream.Close()
        $script:LogStream = $null
    }
}

# Utility functions
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Invoke-CommandWithRetry {
    param(
        [ScriptBlock]$Command,
        [int]$MaxRetries = 3,
        [int]$DelaySeconds = 5,
        [string]$CommandName = "Command"
    )

    for ($i = 1; $i -le $MaxRetries; $i++) {
        try {
            Write-Log "Executing $CommandName (attempt $i/$MaxRetries)" "INFO"
            & $Command
            Write-Log "$CommandName completed successfully" "SUCCESS"
            return $true
        } catch {
            Write-Log "$CommandName failed (attempt $i/$MaxRetries): $_" "WARNING"
            if ($i -lt $MaxRetries) {
                Write-Log "Retrying in $DelaySeconds seconds..." "INFO"
                Start-Sleep -Seconds $DelaySeconds
            }
        }
    }

    Write-Log "$CommandName failed after $MaxRetries attempts" "ERROR"
    return $false
}

function Test-CommandExists {
    param([string]$Command)

    try {
        $null = Get-Command $Command -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

# Hardware validation functions
function Test-HardwareRequirements {
    Write-Log "Checking hardware requirements..." "INFO"

    # Check CPU cores
    $cpuInfo = Get-WmiObject -Class Win32_Processor
    $logicalCores = $cpuInfo.NumberOfLogicalProcessors
    $physicalCores = $cpuInfo.NumberOfCores

    Write-Log "CPU: $physicalCores physical cores, $logicalCores logical cores" "INFO"

    if ($logicalCores -lt 16) {
        Write-Log "WARNING: CPU has $logicalCores logical cores, recommend 16+" "WARNING"
    }

    # Check RAM
    $ramGB = [math]::Round((Get-WmiObject -Class Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 1)
    Write-Log "RAM: $ramGB GB" "INFO"

    if ($ramGB -lt 30) {
        throw "Insufficient RAM: $ramGB GB, require 30GB+"
    }

    if ($ramGB -lt 32) {
        Write-Log "WARNING: RAM is $ramGB GB, recommend 32GB+ for optimal performance" "WARNING"
    }

    # Check GPU (will be validated after ROCm install)
    Write-Log "Hardware requirements check completed" "SUCCESS"
}

# ROCm installation functions
function Install-ROCmDrivers {
    param([string]$Version = $ROCmVersion)

    Write-Log "Checking ROCm drivers installation..." "INFO"

    # First check if ROCm is already working
    try {
        $rocmTest = & rocm-smi --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Log "ROCm tools found and working" "SUCCESS"
            Test-ROCmInstallation
            return
        }
    } catch {
        Write-Log "ROCm tools not found or not working" "WARNING"
    }

    # ROCm installation on Windows is complex - provide manual instructions
    Write-Log "ROCm automatic installation not available for Windows" "WARNING"
    Write-Log "Please install ROCm drivers manually:" "INFO"
    Write-Log "1. Visit: https://www.amd.com/en/support" "INFO"
    Write-Log "2. Download Radeon Software for your GPU model" "INFO"
    Write-Log "3. Install with ROCm support enabled" "INFO"
    Write-Log "4. Re-run this deployment script after installation" "INFO"

    # Ask user if they want to continue without ROCm (for testing purposes)
    $continue = Read-Host "Continue deployment without ROCm installation? (y/N)"
    if ($continue -ne 'y' -and $continue -ne 'Y') {
        throw "ROCm installation required. Please install manually and re-run."
    }

    Write-Log "Continuing without ROCm installation (limited functionality)" "WARNING"
}

function Test-ROCmInstallation {
    Write-Log "Testing ROCm installation..." "INFO"

    # Test rocm-smi
    try {
        $rocmOutput = & rocm-smi --showproductname 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Log "ROCm GPU detected: $rocmOutput" "INFO"

            if ($rocmOutput -notcontains "Radeon RX 9100") {
                Write-Log "WARNING: AMD Radeon RX 9100 not detected in ROCm output" "WARNING"
            }
            Write-Log "ROCm installation test completed" "SUCCESS"
        } else {
            Write-Log "ROCm tools not available or not working properly" "WARNING"
            Write-Log "GPU acceleration may not be available" "WARNING"
        }
    } catch {
        Write-Log "ROCm GPU detection failed: $_" "WARNING"
        Write-Log "Continuing without GPU acceleration" "WARNING"
    }
}

# Python environment functions
function Install-PythonEnvironment {
    param([string]$Version = $PythonVersion)

    Write-Log "Setting up Python $Version environment..." "INFO"

    # Check if Python is already available
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        $pythonVersion = & python --version 2>$null
        Write-Log "Python found: $pythonVersion" "INFO"

        # Check version
        if ($pythonVersion -match "Python (\d+)\.(\d+)\.") {
            $major = [int]$matches[1]
            $minor = [int]$matches[2]

            if ($major -eq 3 -and $minor -ge 10 -and $minor -le 13) {
                Write-Log "Python version is compatible" "SUCCESS"
                return
            }
        }
    }

    # Install Python using winget or chocolatey
    if (Test-CommandExists "winget") {
        Write-Log "Installing Python using winget..." "INFO"
        & winget install --id Python.Python.$Version --exact --silent --accept-source-agreements --accept-package-agreements
    } elseif (Test-CommandExists "choco") {
        Write-Log "Installing Python using chocolatey..." "INFO"
        & choco install python --version $Version -y
    } else {
        throw "Neither winget nor chocolatey found for Python installation"
    }

    # Refresh environment
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")

    Write-Log "Python environment setup completed" "SUCCESS"
}

function Install-PythonPackages {
    Write-Log "Installing Python packages..." "INFO"

    $requirements = @"
pytest>=7.0.0
openai>=1.0.0
psutil>=5.9.0
requests>=2.31.0
tabulate>=0.9.0
numpy>=1.24.0
pandas>=2.0.0
matplotlib>=3.7.0
seaborn>=0.12.0
jupyter>=1.0.0
ipykernel>=6.0.0
"@

    $reqFile = "$env:TEMP\requirements.txt"
    $requirements | Out-File -FilePath $reqFile -Encoding UTF8

    & python -m pip install --upgrade pip
    & python -m pip install -r $reqFile

    if ($LASTEXITCODE -ne 0) {
        throw "Python package installation failed"
    }

    Remove-Item $reqFile -ErrorAction SilentlyContinue

    Write-Log "Python packages installed successfully" "SUCCESS"
}

# Lemonade Server functions
function Install-LemonadeServer {
    param([string]$Version = $LemonadeVersion)

    Write-Log "Installing Lemonade Server version $Version..." "INFO"

    # Create installation directory
    $installDir = "$env:ProgramFiles\Lemonade"
    New-Item -ItemType Directory -Path $installDir -Force | Out-Null

    # Download Lemonade Server
    $downloadUrl = "https://github.com/lemonade/standalone/releases/download/v$Version/lemonade-standalone-windows-amd64.zip"
    $zipPath = "$env:TEMP\lemonade-standalone-v$Version.zip"
    $extractPath = "$env:TEMP\lemonade-extract"

    Write-Log "Downloading Lemonade Server..." "INFO"
    Invoke-WebRequest -Uri $downloadUrl -OutFile $zipPath -UseBasicParsing

    Write-Log "Extracting Lemonade Server..." "INFO"
    Expand-Archive -Path $zipPath -DestinationPath $extractPath -Force

    # Copy files to installation directory
    Copy-Item "$extractPath\*" $installDir -Recurse -Force

    # Clean up
    Remove-Item $zipPath -ErrorAction SilentlyContinue
    Remove-Item $extractPath -Recurse -ErrorAction SilentlyContinue

    Write-Log "Lemonade Server installed successfully" "SUCCESS"
}

function Configure-LemonadeServer {
    Write-Log "Configuring Lemonade Server..." "INFO"

    $configDir = "$env:APPDATA\lemonade"
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null

    # Create basic configuration
    $config = @"
# Lemonade Server Configuration for AMD AI Max+ 395
server:
  host: 0.0.0.0
  port: 8000
  workers: 4

models:
  - name: "llama-3.1-8b-instruct"
    path: "models/llama-3.1-8b-instruct.gguf"
    type: "llama"
    context_length: 4096
    gpu_layers: 99

rocm:
  enabled: true
  gpu_device: 0
  vram_budget: 120

logging:
  level: "INFO"
  file: "logs/lemonade.log"
"@

    $config | Out-File -FilePath "$configDir\config.yaml" -Encoding UTF8

    Write-Log "Lemonade Server configuration created" "SUCCESS"
}

# Testing framework functions
function Deploy-TestingFramework {
    Write-Log "Deploying testing framework..." "INFO"

    $testDir = "$DeploymentRoot\tests\rocm_max395"
    if (-not (Test-Path $testDir)) {
        throw "Testing framework directory not found: $testDir"
    }

    # Create virtual environment
    $venvPath = "$testDir\.venv"
    & python -m venv $venvPath

    # Activate virtual environment and install dependencies
    & "$venvPath\Scripts\Activate.ps1"
    & python -m pip install --upgrade pip
    & python -m pip install -e "$DeploymentRoot"

    # Create necessary directories
    $dirs = @(
        "$testDir\results",
        "$testDir\logs",
        "$testDir\models",
        "$testDir\reports"
    )

    foreach ($dir in $dirs) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }

    Write-Log "Testing framework deployed successfully" "SUCCESS"
}

# Validation functions
function Test-Deployment {
    Write-Log "Running deployment validation..." "INFO"

    # Run the Python validation script
    $validationScript = "$DeploymentRoot\deployment_validation.py"

    if (-not (Test-Path $validationScript)) {
        Write-Log "Validation script not found, skipping validation" "WARNING"
        return
    }

    & python $validationScript --verbose

    if ($LASTEXITCODE -ne 0) {
        throw "Deployment validation failed with exit code $LASTEXITCODE"
    }

    Write-Log "Deployment validation completed successfully" "SUCCESS"
}

# Main deployment function
function Invoke-Deployment {
    try {
        Start-Logging

        Write-Log "AMD AI Max+ 395 ROCm Production Deployment Started" "INFO"
        Write-Log "Parameters: SkipHardwareCheck=$SkipHardwareCheck, SkipROCmInstall=$SkipROCmInstall, SkipPythonSetup=$SkipPythonSetup, SkipLemonadeServer=$SkipLemonadeServer, SkipTestingFramework=$SkipTestingFramework, SkipValidation=$SkipValidation" "INFO"

        # Check administrator privileges
        if (-not (Test-Administrator)) {
            throw "This script must be run as Administrator"
        }

        # Hardware check
        if (-not $SkipHardwareCheck) {
            Test-HardwareRequirements
        } else {
            Write-Log "Skipping hardware requirements check" "INFO"
        }

        # ROCm installation
        if (-not $SkipROCmInstall) {
            Install-ROCmDrivers -Version $ROCmVersion
            Test-ROCmInstallation
        } else {
            Write-Log "Skipping ROCm installation" "INFO"
        }

        # Python setup
        if (-not $SkipPythonSetup) {
            Install-PythonEnvironment -Version $PythonVersion
            Install-PythonPackages
        } else {
            Write-Log "Skipping Python setup" "INFO"
        }

        # Lemonade Server
        if (-not $SkipLemonadeServer) {
            Install-LemonadeServer -Version $LemonadeVersion
            Configure-LemonadeServer
        } else {
            Write-Log "Skipping Lemonade Server installation" "INFO"
        }

        # Testing framework
        if (-not $SkipTestingFramework) {
            Deploy-TestingFramework
        } else {
            Write-Log "Skipping testing framework deployment" "INFO"
        }

        # Validation
        if (-not $SkipValidation) {
            Test-Deployment
        } else {
            Write-Log "Skipping deployment validation" "INFO"
        }

        Write-Log "AMD AI Max+ 395 ROCm Production Deployment Completed Successfully" "SUCCESS"

    } catch {
        Write-Log "Deployment failed: $_" "ERROR"
        throw
    } finally {
        Stop-Logging
    }
}

# Script entry point
if ($MyInvocation.InvocationName -ne '.') {
    Invoke-Deployment
}