<#
.SYNOPSIS
    Stop all running Lemonade Server instances.

.DESCRIPTION
    This script stops all lemonade-server processes that were started
    by the start-multi-server.ps1 script by reading PID files.

.PARAMETER Port
    Stop only the server on the specified port. If not specified, stops all servers.

.PARAMETER Force
    Force kill processes if graceful shutdown fails

.EXAMPLE
    .\stop-multi-server.ps1
    .\stop-multi-server.ps1 -Port 8000
    .\stop-multi-server.ps1 -Force

.NOTES
    Author: Lemonade Server Team
    Version: 1.0.0
#>

[CmdletBinding()]
param(
    [Parameter()]
    [int]$Port,
    
    [Parameter()]
    [switch]$Force
)

# Script configuration
$ErrorActionPreference = "Continue"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PidDir = Join-Path $ScriptDir "pids"

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

function Stop-LemonadeServer {
    param(
        [string]$PidFile,
        [int]$ServerPort
    )
    
    if (-not (Test-Path $PidFile)) {
        Write-ColorOutput "⚠️  No PID file found for port $ServerPort" "Yellow"
        return $false
    }
    
    $pid = Get-Content $PidFile -Raw
    $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
    
    if (-not $process) {
        Write-ColorOutput "⚠️  Server on port $ServerPort not running (PID: $pid)" "Yellow"
        Remove-Item $PidFile -Force
        return $false
    }
    
    Write-ColorOutput "Stopping server on port $ServerPort (PID: $pid)..." "Blue"
    
    try {
        # Try graceful shutdown first
        $process.CloseMainWindow() | Out-Null
        
        # Wait up to 5 seconds for graceful shutdown
        $waited = 0
        while (-not $process.HasExited -and $waited -lt 5000) {
            Start-Sleep -Milliseconds 100
            $waited += 100
            $process.Refresh()
        }
        
        # Force kill if still running
        if (-not $process.HasExited) {
            if ($Force) {
                Write-ColorOutput "  Force killing process..." "Yellow"
                Stop-Process -Id $pid -Force
            } else {
                Write-ColorOutput "  ⚠️  Process still running after graceful shutdown. Use -Force to kill." "Yellow"
                return $false
            }
        }
        
        # Remove PID file
        Remove-Item $PidFile -Force
        Write-ColorOutput "  ✓ Stopped successfully" "Green"
        return $true
        
    } catch {
        Write-ColorOutput "  ❌ Error stopping process: $($_.Exception.Message)" "Red"
        return $false
    }
}

# Main execution
try {
    Write-ColorOutput "=== Lemonade Multi-Server Stopper ===" "Blue"
    Write-ColorOutput ""
    
    if (-not (Test-Path $PidDir)) {
        Write-ColorOutput "No PID directory found. No servers to stop." "Yellow"
        exit 0
    }
    
    # Get all PID files
    $pidFiles = Get-ChildItem -Path $PidDir -Filter "server-*.pid"
    
    if ($pidFiles.Count -eq 0) {
        Write-ColorOutput "No running servers found." "Yellow"
        exit 0
    }
    
    # Filter by port if specified
    if ($Port) {
        $pidFiles = $pidFiles | Where-Object { $_.Name -eq "server-$Port.pid" }
        if ($pidFiles.Count -eq 0) {
            Write-ColorOutput "No server found on port $Port" "Yellow"
            exit 0
        }
    }
    
    Write-ColorOutput "Found $($pidFiles.Count) server(s) to stop" "Blue"
    Write-ColorOutput ""
    
    # Stop each server
    $stoppedCount = 0
    foreach ($pidFile in $pidFiles) {
        $serverPort = [regex]::Match($pidFile.Name, 'server-(\d+)\.pid').Groups[1].Value
        if (Stop-LemonadeServer -PidFile $pidFile.FullName -ServerPort $serverPort) {
            $stoppedCount++
        }
        Write-ColorOutput ""
    }
    
    # Summary
    Write-ColorOutput "=== Summary ===" "Blue"
    Write-ColorOutput "Stopped $stoppedCount of $($pidFiles.Count) server(s)" "Green"
    
} catch {
    Write-ColorOutput ""
    Write-ColorOutput "❌ Error: $($_.Exception.Message)" "Red"
    exit 1
}
