<#
.SYNOPSIS
    Check health status of all running Lemonade Server instances.

.DESCRIPTION
    This script checks if servers are running and queries their /api/v1/health
    endpoint to verify they are responding correctly.

.PARAMETER Port
    Check only the server on the specified port. If not specified, checks all servers.

.PARAMETER Verbose
    Show detailed health information including loaded models

.EXAMPLE
    .\status-multi-server.ps1
    .\status-multi-server.ps1 -Port 8000
    .\status-multi-server.ps1 -Verbose

.NOTES
    Author: Lemonade Server Team
    Version: 1.0.0
#>

[CmdletBinding()]
param(
    [Parameter()]
    [int]$Port
)

# Script configuration
$ErrorActionPreference = "Continue"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PidDir = Join-Path $ScriptDir "pids"
$LogDir = Join-Path $ScriptDir "logs"

# ANSI colors
$Colors = @{
    Green = "`e[32m"
    Red = "`e[31m"
    Yellow = "`e[33m"
    Blue = "`e[34m"
    Cyan = "`e[36m"
    Reset = "`e[0m"
}

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "Reset",
        [switch]$NoNewline
    )
    $fg = switch ($Color) {
        'Green' { 'Green' }
        'Red' { 'Red' }
        'Yellow' { 'Yellow' }
        'Blue' { 'Cyan' }
        'Cyan' { 'Cyan' }
        default { $null }
    }
    if ($NoNewline) {
        if ($fg) { Write-Host $Message -ForegroundColor $fg -NoNewline } else { Write-Host $Message -NoNewline }
    } else {
        if ($fg) { Write-Host $Message -ForegroundColor $fg } else { Write-Host $Message }
    }
}

function Test-ServerHealth {
    param(
        [int]$ServerPort
    )
    
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:$ServerPort/api/v1/health" -TimeoutSec 5 -ErrorAction Stop
        return @{
            Success = $true
            Status = $response.status
            Response = $response
        }
    } catch {
        return @{
            Success = $false
            Error = $_.Exception.Message
        }
    }
}

function Get-ProcessUptime {
    param($Process)
    
    $uptime = (Get-Date) - $Process.StartTime
    
    if ($uptime.Days -gt 0) {
        return "$($uptime.Days)d $($uptime.Hours)h"
    } elseif ($uptime.Hours -gt 0) {
        return "$($uptime.Hours)h $($uptime.Minutes)m"
    } elseif ($uptime.Minutes -gt 0) {
        return "$($uptime.Minutes)m $($uptime.Seconds)s"
    } else {
        return "$($uptime.Seconds)s"
    }
}

# Main execution
Write-ColorOutput "=== Lemonade Multi-Server Status ===" "Blue"
Write-ColorOutput ""

if (-not (Test-Path $PidDir)) {
    Write-ColorOutput "No PID directory found. No servers configured." "Yellow"
    exit 0
}

# Get all PID files
$pidFiles = Get-ChildItem -Path $PidDir -Filter "server-*.pid"

if ($Port) {
    $pidFiles = $pidFiles | Where-Object { $_.Name -eq "server-$Port.pid" }
}

if ($pidFiles.Count -eq 0) {
    Write-ColorOutput "No servers found." "Yellow"
    exit 0
}

Write-ColorOutput "Checking $($pidFiles.Count) server(s)..." "Blue"
Write-ColorOutput ""

# Check each server
$runningCount = 0
$healthyCount = 0

foreach ($pidFile in $pidFiles) {
    $serverPort = [regex]::Match($pidFile.Name, 'server-(\d+)\.pid').Groups[1].Value
    
    Write-ColorOutput "--- Server on Port $serverPort ---" "Cyan"
    
    # Check if process is running
    if (-not (Test-Path $pidFile.FullName)) {
        Write-ColorOutput "  Status: [ERR] Not configured" "Red"
        Write-ColorOutput ""
        continue
    }
    
    $serverPid = Get-Content $pidFile.FullName -Raw
    $process = Get-Process -Id $serverPid -ErrorAction SilentlyContinue
    
    if (-not $process) {
        Write-ColorOutput "  Status: [ERR] Not running (PID: $serverPid)" "Red"
        Write-ColorOutput "  Hint: Process may have crashed. Check logs:" "Yellow"
        
        $logFile = Join-Path $LogDir "server-$serverPort.log"
        if (Test-Path $logFile) {
            Write-ColorOutput "        $logFile" "Yellow"
        }
        
        Write-ColorOutput ""
        continue
    }
    
    $runningCount++
    
    # Process info
    $uptime = Get-ProcessUptime -Process $process
    $memoryMB = [math]::Round($process.WorkingSet64 / 1MB, 2)
    
    Write-ColorOutput "  Status: [OK] Running" "Green"
    Write-ColorOutput "  PID: $serverPid" "Blue"
    Write-ColorOutput "  Uptime: $uptime" "Blue"
    Write-ColorOutput "  Memory: ${memoryMB} MB" "Blue"
    
    # Check health endpoint
    Write-ColorOutput "  Health Check: " "Blue" -NoNewline
    $health = Test-ServerHealth -ServerPort $serverPort
    
    if ($health.Success) {
        Write-ColorOutput "[OK] Healthy ($($health.Status))" "Green"
        $healthyCount++
        
        if ($PSBoundParameters.ContainsKey('Verbose') -and $health.Response) {
            Write-ColorOutput ""
            Write-ColorOutput "  Loaded Models:" "Cyan"
            
            if ($health.Response.loaded_models) {
                foreach ($model in $health.Response.loaded_models) {
                    Write-ColorOutput "    - $model" "Blue"
                }
            } else {
                Write-ColorOutput "    (none)" "Yellow"
            }
        }
    } else {
        Write-ColorOutput "[ERR] Unhealthy" "Red"
        Write-ColorOutput "  Error: $($health.Error)" "Red"
    }
    
    Write-ColorOutput ""
}

# Summary
Write-ColorOutput "=== Summary ===" "Blue"
Write-ColorOutput "Total servers: $($pidFiles.Count)" "Blue"
$runningColor = if ($runningCount -eq $pidFiles.Count) { "Green" } else { "Yellow" }
$healthyColor = if ($healthyCount -eq $runningCount) { "Green" } else { "Yellow" }
Write-ColorOutput "Running: $runningCount" $runningColor
Write-ColorOutput "Healthy: $healthyCount" $healthyColor

if ($healthyCount -lt $pidFiles.Count) {
    Write-ColorOutput ""
    Write-ColorOutput "Use '.\restart-multi-server.ps1' to restart failed servers" "Yellow"
    Write-ColorOutput "Use '.\stop-multi-server.ps1' and '.\start-multi-server.ps1' for full restart" "Yellow"
}
