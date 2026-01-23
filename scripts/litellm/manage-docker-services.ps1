#Requires -Version 5.1
<#
.SYNOPSIS
    Manage LiteLLM and OpenedAI Speech Docker containers
.DESCRIPTION
    Start, stop, restart, and monitor Docker containers for:
    - LiteLLM Proxy (port 4014)
    - OpenedAI Speech RoCm (port 8888)
.PARAMETER Action
    Action to perform: start, stop, restart, status, logs
.PARAMETER Service
    Service to manage: all, litellm, openedai-speech
.EXAMPLE
    .\manage-docker-services.ps1 -Action start -Service all
    Start all services
.EXAMPLE
    .\manage-docker-services.ps1 -Action logs -Service openedai-speech
    View OpenedAI Speech logs
#>

param(
    [ValidateSet("start", "stop", "restart", "status", "logs", "pull")]
    [string]$Action = "status",
    
    [ValidateSet("all", "litellm", "openedai-speech")]
    [string]$Service = "all",
    
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$ScriptVersion = "1.0.0"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Color output helper
function Write-ColorOutput {
    param([string]$Message, [string]$Color)
    if ([string]::IsNullOrEmpty($Color)) { $Color = "White" }
    Write-Host $Message -ForegroundColor $Color
}

function Test-DockerInstalled {
    $docker = Get-Command docker -ErrorAction SilentlyContinue
    if (-not $docker) {
        Write-ColorOutput "[ERROR] Docker is not installed or not in PATH" "Red"
        Write-ColorOutput "  Install Docker Desktop: https://www.docker.com/products/docker-desktop" "Gray"
        return $false
    }
    return $true
}

function Start-DockerServices {
    Write-ColorOutput "[1/3] Pulling latest images..." "Cyan"
    
    try {
        if ($Service -eq "all" -or $Service -eq "openedai-speech") {
            Write-ColorOutput "  Pulling OpenedAI Speech RoCm image..." "Gray"
            docker pull ghcr.io/matatonic/openedai-speech:rocm
        }
        
        if ($Service -eq "all" -or $Service -eq "litellm") {
            Write-ColorOutput "  Pulling LiteLLM image..." "Gray"
            docker pull ghcr.io/berriai/litellm:main
        }
    } catch {
        Write-ColorOutput "[WARN] Image pull failed, continuing with existing images" "Yellow"
    }
    
    Write-ColorOutput "[2/3] Starting Docker containers..." "Cyan"
    
    $composeFile = Join-Path $ScriptDir "docker-compose.yml"
    if (-not (Test-Path $composeFile)) {
        Write-ColorOutput "[ERROR] docker-compose.yml not found: $composeFile" "Red"
        return $false
    }
    
    try {
        if ($Service -eq "all") {
            docker compose -f $composeFile up -d
            Write-ColorOutput "  All services started" "Green"
        } elseif ($Service -eq "litellm") {
            docker compose -f $composeFile up -d litellm
            Write-ColorOutput "  LiteLLM started" "Green"
        } elseif ($Service -eq "openedai-speech") {
            docker compose -f $composeFile up -d openedai-speech
            Write-ColorOutput "  OpenedAI Speech started" "Green"
        }
    } catch {
        Write-ColorOutput "[ERROR] Failed to start services: $_" "Red"
        return $false
    }
    
    Write-ColorOutput "[3/3] Waiting for services to be healthy..." "Cyan"
    Start-Sleep -Seconds 5
    
    return $true
}

function Stop-DockerServices {
    Write-ColorOutput "Stopping Docker containers..." "Cyan"
    
    $composeFile = Join-Path $ScriptDir "docker-compose.yml"
    
    try {
        if ($Service -eq "all") {
            docker compose -f $composeFile down
            Write-ColorOutput "  All services stopped" "Green"
        } elseif ($Service -eq "litellm") {
            docker compose -f $composeFile stop litellm
            Write-ColorOutput "  LiteLLM stopped" "Green"
        } elseif ($Service -eq "openedai-speech") {
            docker compose -f $composeFile stop openedai-speech
            Write-ColorOutput "  OpenedAI Speech stopped" "Green"
        }
    } catch {
        Write-ColorOutput "[ERROR] Failed to stop services: $_" "Red"
        return $false
    }
    
    return $true
}

function Get-ServiceStatus {
    Write-ColorOutput "Docker Services Status:" "Cyan"
    Write-ColorOutput ""
    
    # Get running containers
    $containers = docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>$null
    
    $openedaiRunning = $false
    $litellmRunning = $false
    
    if ($containers) {
        $containers | ForEach-Object {
            if ($_ -match "openedai-speech-rocm") {
                $openedaiRunning = $true
                Write-ColorOutput "  ✓ OpenedAI Speech: RUNNING" "Green"
                Write-ColorOutput "    Port: 8888" "Gray"
            }
            if ($_ -match "litellm-proxy") {
                $litellmRunning = $true
                Write-ColorOutput "  ✓ LiteLLM Proxy: RUNNING" "Green"
                Write-ColorOutput "    Port: 4014" "Gray"
            }
        }
    }
    
    if (-not $openedaiRunning) {
        Write-ColorOutput "  ✗ OpenedAI Speech: NOT RUNNING" "Yellow"
    }
    if (-not $litellmRunning) {
        Write-ColorOutput "  ✗ LiteLLM Proxy: NOT RUNNING" "Yellow"
    }
    
    Write-ColorOutput ""
    Write-ColorOutput "Health Checks:" "Cyan"
    
    # Test OpenedAI Speech
    if ($openedaiRunning) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8888/health" -ErrorAction SilentlyContinue -TimeoutSec 2
            Write-ColorOutput "  ✓ OpenedAI Speech health: OK" "Green"
        } catch {
            Write-ColorOutput "  ✗ OpenedAI Speech health: FAILED" "Red"
        }
    }
    
    # Test LiteLLM
    if ($litellmRunning) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:4014/health" -ErrorAction SilentlyContinue -TimeoutSec 2
            Write-ColorOutput "  ✓ LiteLLM Proxy health: OK" "Green"
        } catch {
            Write-ColorOutput "  ✗ LiteLLM Proxy health: FAILED" "Red"
        }
    }
    
    Write-ColorOutput ""
}

function Get-ServiceLogs {
    Write-ColorOutput "Showing logs for: $Service" "Cyan"
    Write-ColorOutput ""
    
    $composeFile = Join-Path $ScriptDir "docker-compose.yml"
    
    try {
        docker compose -f $composeFile logs --tail 50 $Service
    } catch {
        Write-ColorOutput "[ERROR] Failed to get logs: $_" "Red"
    }
}

# Main execution
try {
    Write-ColorOutput ""
    Write-ColorOutput "=====================================================" "Cyan"
    Write-ColorOutput "  Docker Services Manager v$ScriptVersion" "Cyan"
    Write-ColorOutput "=====================================================" "Cyan"
    Write-ColorOutput ""
    
    # Check if Docker is installed
    if (-not (Test-DockerInstalled)) {
        exit 1
    }
    
    # Execute action
    switch ($Action) {
        "start" {
            if (-not (Start-DockerServices)) {
                exit 1
            }
            Get-ServiceStatus
        }
        
        "stop" {
            if (-not (Stop-DockerServices)) {
                exit 1
            }
        }
        
        "restart" {
            Write-ColorOutput "Restarting services..." "Cyan"
            Stop-DockerServices | Out-Null
            Start-Sleep -Seconds 2
            Start-DockerServices | Out-Null
            Get-ServiceStatus
        }
        
        "status" {
            Get-ServiceStatus
        }
        
        "logs" {
            Get-ServiceLogs
        }
        
        "pull" {
            Write-ColorOutput "Pulling latest images..." "Cyan"
            docker pull ghcr.io/matatonic/openedai-speech:rocm
            docker pull ghcr.io/berriai/litellm:main
            Write-ColorOutput "  Images updated" "Green"
        }
    }
    
    Write-ColorOutput ""
    
} catch {
    Write-ColorOutput ""
    Write-ColorOutput "[ERROR] $($_.Exception.Message)" "Red"
    exit 1
}
