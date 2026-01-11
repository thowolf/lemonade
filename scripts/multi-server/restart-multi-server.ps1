<#
.SYNOPSIS
    Restart all or specific Lemonade Server instances.

.DESCRIPTION
    This script stops and then starts lemonade-server processes.
    Useful for applying configuration changes or recovering from errors.

.PARAMETER Port
    Restart only the server on the specified port. If not specified, restarts all servers.

.PARAMETER ConfigFile
    Path to the JSON configuration file. Defaults to config/example-config.json

.PARAMETER Force
    Force kill processes during stop if graceful shutdown fails

.EXAMPLE
    .\restart-multi-server.ps1
    .\restart-multi-server.ps1 -Port 8000
    .\restart-multi-server.ps1 -ConfigFile config/my-config.json -Force

.NOTES
    Author: Lemonade Server Team
    Version: 1.0.0
#>

[CmdletBinding()]
param(
    [Parameter()]
    [int]$Port,
    
    [Parameter()]
    [string]$ConfigFile = "config\example-config.json",
    
    [Parameter()]
    [switch]$Force
)

# Script configuration
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# ANSI colors
$Colors = @{
    Green = "`e[32m"
    Red = "`e[31m"
    Yellow = "`e[33m"
    Blue = "`e[34m"
    Reset = "`e[0m"
}

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "Reset"
    )
    Write-Host "$($Colors[$Color])$Message$($Colors.Reset)"
}

# Main execution
try {
    Write-ColorOutput "=== Lemonade Multi-Server Restart ===" "Blue"
    Write-ColorOutput ""
    
    # Step 1: Stop servers
    Write-ColorOutput "Step 1: Stopping servers..." "Blue"
    Write-ColorOutput ""
    
    $stopArgs = @()
    if ($Port) {
        $stopArgs += "-Port", $Port
    }
    if ($Force) {
        $stopArgs += "-Force"
    }
    
    $stopScript = Join-Path $ScriptDir "stop-multi-server.ps1"
    & $stopScript @stopArgs
    
    if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne $null) {
        throw "Failed to stop servers"
    }
    
    # Wait a moment for cleanup
    Start-Sleep -Seconds 2
    
    # Step 2: Start servers
    Write-ColorOutput ""
    Write-ColorOutput "Step 2: Starting servers..." "Blue"
    Write-ColorOutput ""
    
    $startArgs = @()
    if ($ConfigFile) {
        $startArgs += $ConfigFile
    }
    
    $startScript = Join-Path $ScriptDir "start-multi-server.ps1"
    & $startScript @startArgs
    
    if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne $null) {
        throw "Failed to start servers"
    }
    
    Write-ColorOutput ""
    Write-ColorOutput "=== Restart Complete ===" "Green"
    
} catch {
    Write-ColorOutput ""
    Write-ColorOutput "❌ Error during restart: $($_.Exception.Message)" "Red"
    exit 1
}
