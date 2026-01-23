<#
.SYNOPSIS
    Downloads and extracts NSSM (Non-Sucking Service Manager) for Windows
.DESCRIPTION
    Standalone script to download NSSM from GitHub with retry logic
    Useful if the main installer has network issues
.EXAMPLE
    .\download-nssm.ps1
#>

param(
    [string]$TargetPath = "$PSScriptRoot\nssm",
    [int]$MaxRetries = 3
)

$ErrorActionPreference = "Stop"

function Write-Log {
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

# GitHub API URLs
$githubReleaseApi = "https://api.github.com/repos/nssm-io/nssm/releases/latest"
$nssmUrls = @(
    "https://github.com/nssm-io/nssm/releases/download/2.24/nssm-2.24-101-g897c7ad.zip",
    "https://github.com/nssm-io/nssm/releases/latest/download/nssm-2.24.zip"
)

try {
    Write-Log "NSSM Standalone Downloader"
    
    if (Test-Path "$TargetPath\nssm.exe") {
        Write-Log "NSSM already exists at: $TargetPath" "SUCCESS"
        exit 0
    }
    
    $tempZip = "$env:TEMP\nssm-download.zip"
    $downloaded = $false
    $retryCount = 0
    
    while (-not $downloaded -and $retryCount -lt $MaxRetries) {
        $retryCount++
        
        foreach ($url in $nssmUrls) {
            try {
                Write-Log "Attempt $retryCount/$MaxRetries - Downloading from: $url" "INFO"
                [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
                
                Invoke-WebRequest -Uri $url -OutFile $tempZip -UseBasicParsing -TimeoutSec 30 -ErrorAction Stop
                
                if (Test-Path $tempZip) {
                    Write-Log "Download successful" "SUCCESS"
                    $downloaded = $true
                    break
                }
            }
            catch {
                Write-Log "Failed: $_" "WARNING"
                Start-Sleep -Seconds 2
            }
        }
        
        if (-not $downloaded -and $retryCount -lt $MaxRetries) {
            Write-Log "Retry in 5 seconds..." "WARNING"
            Start-Sleep -Seconds 5
        }
    }
    
    if (-not $downloaded) {
        throw "Failed to download NSSM after $MaxRetries attempts"
    }
    
    Write-Log "Extracting NSSM..."
    $extractPath = "$env:TEMP\nssm-extract"
    
    if (Test-Path $extractPath) {
        Remove-Item $extractPath -Recurse -Force
    }
    
    Expand-Archive -Path $tempZip -DestinationPath $extractPath -Force
    
    Write-Log "Finding nssm.exe in archive..."
    $nssmExe = Get-ChildItem $extractPath -Recurse -Filter "nssm.exe" -ErrorAction Stop
    
    if (-not $nssmExe) {
        throw "nssm.exe not found in downloaded archive"
    }
    
    Write-Log "Installing to: $TargetPath"
    
    if (Test-Path $TargetPath) {
        Remove-Item $TargetPath -Recurse -Force
    }
    
    New-Item -ItemType Directory -Path $TargetPath -Force | Out-Null
    Copy-Item -Path $nssmExe.Directory -Destination $TargetPath -Recurse -Force
    
    Write-Log "Verifying installation..."
    $verify = Get-ChildItem "$TargetPath\nssm.exe" -ErrorAction Stop
    Write-Log "NSSM installed successfully at: $TargetPath" "SUCCESS"
    Write-Log "Version: $(& "$TargetPath\nssm.exe" --version 2>&1)" "INFO"
    
    # Cleanup
    Remove-Item $tempZip, $extractPath -Recurse -Force -ErrorAction SilentlyContinue
    
    Write-Log "NSSM is ready for use" "SUCCESS"
}
catch {
    Write-Log "Error: $_" "ERROR"
    exit 1
}
