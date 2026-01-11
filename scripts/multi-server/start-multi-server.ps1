<#
.SYNOPSIS
    Start multiple Lemonade Server instances based on JSON configuration.

.DESCRIPTION
    This script reads a configuration file and starts multiple lemonade-server
    processes on different ports. Each server runs as a background process with
    its own log file and PID tracking.

.PARAMETER ConfigFile
    Path to the JSON configuration file. Defaults to config/example-config.json

.PARAMETER Force
    Skip port availability checks and start servers anyway

.EXAMPLE
    .\start-multi-server.ps1
    .\start-multi-server.ps1 -ConfigFile config/my-config.json
    .\start-multi-server.ps1 -Force

.NOTES
    Author: Lemonade Server Team
    Version: 1.0.0
#>

[CmdletBinding()]
param(
    [Parameter(Position=0)]
    [string]$ConfigFile = "config\example-config.json",
    
    [Parameter()]
    [switch]$Force
)

# Script configuration
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogDir = Join-Path $ScriptDir "logs"
$PidDir = Join-Path $ScriptDir "pids"

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = 'Reset',
        [switch]$NoNewline
    )
    $fg = switch ($Color) {
        'Green' { 'Green' }
        'Red' { 'Red' }
        'Yellow' { 'Yellow' }
        'Blue' { 'Cyan' }
        default { $null }
    }
    if ($NoNewline) {
        if ($fg) { Write-Host $Message -ForegroundColor $fg -NoNewline } else { Write-Host $Message -NoNewline }
    } else {
        if ($fg) { Write-Host $Message -ForegroundColor $fg } else { Write-Host $Message }
    }
}

function Test-PortAvailable {
    param([int]$Port)
    
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $Port)
        $listener.Start()
        $listener.Stop()
        return $true
    } catch {
        return $false
    }
}

function Get-LemonadeServerPath {
    # Check common installation paths
    $paths = @(
        "$env:LOCALAPPDATA\lemonade_server\bin\lemonade-router.exe",
        "$env:USERPROFILE\.lemonade\bin\lemonade-router.exe",
        "C:\Program Files\lemonade_server\bin\lemonade-router.exe"
    )
    
    foreach ($path in $paths) {
        if (Test-Path $path) {
            return $path
        }
    }
    
    # Check if it's in PATH
    $pathEnv = Get-Command "lemonade-router" -ErrorAction SilentlyContinue
    if ($pathEnv) {
        return $pathEnv.Source
    }
    
    throw "lemonade-router.exe not found. Please ensure Lemonade Server is installed."
}

# Main execution
try {
    Write-ColorOutput "=== Lemonade Multi-Server Starter ===" "Blue"
    Write-ColorOutput ""
    
    # Resolve config file path
    $ConfigPath = Join-Path $ScriptDir $ConfigFile
    if (-not (Test-Path $ConfigPath)) {
        throw "Configuration file not found: $ConfigPath"
    }
    
    Write-ColorOutput "Loading configuration: $ConfigPath" "Blue"
    $config = Get-Content $ConfigPath -Raw | ConvertFrom-Json
    
    if (-not $config.servers -or $config.servers.Count -eq 0) {
        throw "No servers defined in configuration file"
    }
    
    Write-ColorOutput "Found $($config.servers.Count) server(s) to start" "Blue"
    Write-ColorOutput ""
    
    # Find lemonade-server executable
    $lemonadeExe = Get-LemonadeServerPath
    Write-ColorOutput "Using: $lemonadeExe" "Blue"
    Write-ColorOutput ""
    
    # Ensure directories exist
    if (-not (Test-Path $LogDir)) {
        New-Item -ItemType Directory -Path $LogDir | Out-Null
    }
    if (-not (Test-Path $PidDir)) {
        New-Item -ItemType Directory -Path $PidDir | Out-Null
    }
    
    # Check for port conflicts
    $portConflicts = @()
    foreach ($server in $config.servers) {
        $pidFile = Join-Path $PidDir "server-$($server.port).pid"
        
        # Check if already running
        if (Test-Path $pidFile) {
            $existingPid = Get-Content $pidFile -Raw
            $process = Get-Process -Id $existingPid -ErrorAction SilentlyContinue
            if ($process) {
                Write-ColorOutput "[WARN] Server '$($server.name)' already running (PID: $existingPid, Port: $($server.port))" "Yellow"
                $portConflicts += $server
                continue
            }
        }
        
        # Check if port is available
        if (-not $Force -and -not (Test-PortAvailable -Port $server.port)) {
            Write-ColorOutput "[ERR] Port $($server.port) is already in use (server: $($server.name))" "Red"
            $portConflicts += $server
        }
    }
    
    if ($portConflicts.Count -gt 0 -and -not $Force) {
        Write-ColorOutput ""
        Write-ColorOutput "[ERR] Cannot start servers due to port conflicts or already running instances." "Red"
        Write-ColorOutput "   Use -Force to skip checks, or stop conflicting servers first." "Yellow"
        exit 1
    }
    
    # Start each server
    $startedServers = @()
    foreach ($server in $config.servers) {
        $pidFile = Join-Path $PidDir "server-$($server.port).pid"
        
        # Skip if already running
        if ($portConflicts -contains $server) {
            continue
        }
        
        Write-ColorOutput "Starting '$($server.name)' on port $($server.port)..." "Green"
        
        # Build command arguments
        $argList = @(
            "serve",
            "--host", ($server.host -or 'localhost'),
            "--port", $server.port,
            "--log-level", ($server.log_level -or 'info'),
            "--max-loaded-models", ($server.max_loaded_models -or '1 1 1 1')
        )
        
        if ($server.llamacpp_backend) {
            $argList += "--llamacpp-backend"
            $argList += $server.llamacpp_backend
        }
        
        if ($server.extra_args) {
            $argList += $server.extra_args.Split(" ")
        }
        
        # Prepare log files
        $logFile = Join-Path $LogDir "server-$($server.port).log"
        $errFile = Join-Path $LogDir "server-$($server.port).err.log"
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        "=== Server started at $timestamp ===" | Out-File -FilePath $logFile -Append
        "Model: $($server.model)" | Out-File -FilePath $logFile -Append
        "Port: $($server.port)" | Out-File -FilePath $logFile -Append
        "Backend: $($server.llamacpp_backend)" | Out-File -FilePath $logFile -Append
        "" | Out-File -FilePath $logFile -Append
        "=== Error log started at $timestamp ===" | Out-File -FilePath $errFile -Append
        "" | Out-File -FilePath $errFile -Append
        
        # Start the process (send stdout to general log, stderr to separate error log)
        $process = Start-Process -FilePath $lemonadeExe `
                                 -ArgumentList $argList `
                                 -WindowStyle Hidden `
                                 -PassThru `
                                 -RedirectStandardOutput $logFile `
                                 -RedirectStandardError $errFile
        
        # Save PID
        $process.Id | Out-File -FilePath $pidFile -NoNewline
        
        # Small delay and quick health of process
        Start-Sleep -Seconds 1
        $process.Refresh()
        if ($process.HasExited) {
            # Process exited early - read error log for details
            $errContent = Get-Content $errFile -Raw -ErrorAction SilentlyContinue
            if ($errContent -match "Another instance of lemonade-router") {
                Write-ColorOutput "[ERR] lemonade-router enforces a single instance on the host." "Red"
                Write-ColorOutput "Consider using Docker containers (see docker-compose.yml) or rebuild the server with single-instance check disabled." "Yellow"
            } else {
                Write-ColorOutput "[ERR] Server process exited early. Error log:" "Red"
                Write-ColorOutput "$errContent" "Red"
            }
            # Remove PID if created
            if (Test-Path $pidFile) { Remove-Item $pidFile -Force }
            continue
        }
        
        Write-ColorOutput "  [OK] Started with PID $($process.Id)" "Green"
        Write-ColorOutput "  Log: $logFile" "Blue"
        Write-ColorOutput "  Endpoint: http://$($server.host):$($server.port)" "Blue"
        Write-ColorOutput ""
        
        $startedServers += @{
            Name = $server.name
            Port = $server.port
            PID = $process.Id
            Model = $server.model
        }
        
        # Small delay between starts
        Start-Sleep -Milliseconds 500
    }
    
    # Summary
    Write-ColorOutput "=== Summary ===" "Blue"
    Write-ColorOutput "Started $($startedServers.Count) server(s) successfully" "Green"
    Write-ColorOutput ""
    
    foreach ($server in $startedServers) {
        Write-ColorOutput "- $($server.Name) - Port $($server.Port) - PID $($server.PID)" "Green"
    }
    
    if ($portConflicts.Count -gt 0) {
        Write-ColorOutput ""
        Write-ColorOutput "Skipped $($portConflicts.Count) server(s) due to conflicts:" "Yellow"
        foreach ($server in $portConflicts) {
            Write-ColorOutput "- $($server.name) - Port $($server.port)" "Yellow"
        }
    }
    
    Write-ColorOutput ""
    Write-ColorOutput "Use '.\stop-multi-server.ps1' to stop all servers" "Blue"
    Write-ColorOutput "Use '.\status-multi-server.ps1' to check server status" "Blue"
    
} catch {
    Write-ColorOutput ""
    Write-ColorOutput "[ERR] Error: $($_.Exception.Message)" "Red"
    exit 1
}
