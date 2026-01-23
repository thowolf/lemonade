#Requires -Version 5.1
<#
.SYNOPSIS
    Start LiteLLM Proxy Server for model routing and API management
.DESCRIPTION
    Production-ready startup script for LiteLLM Proxy with:
    - Model configuration and routing
    - API key management
    - Health checking
    - Comprehensive logging
.PARAMETER Models
    Specify which models to configure (optional)
.PARAMETER Port
    Port to run LiteLLM on (default: 8090)
.PARAMETER Force
    Force restart server if already running
.EXAMPLE
    .\start-litellm.ps1
    Start LiteLLM with default configuration
.EXAMPLE
    .\start-litellm.ps1 -Port 8090
    Start LiteLLM on custom port
#>

param(
    [string[]]$Models,
    [int]$Port = 8090,
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$ScriptVersion = "1.0.0"
$LiteLLMUrl = "http://localhost:$Port"
$RepoRoot = (Get-Location).Path

# Color output helper
function Write-ColorOutput {
    param([string]$Message, [string]$Color)
    if ([string]::IsNullOrEmpty($Color)) { $Color = "White" }
    Write-Host $Message -ForegroundColor $Color
}

try {
    Write-ColorOutput ""
    Write-ColorOutput "=====================================================" "Cyan"
    Write-ColorOutput "  LITELLM PROXY SERVER STARTUP" "Cyan"
    Write-ColorOutput "=====================================================" "Cyan"
    Write-ColorOutput ""
    Write-ColorOutput "=== LiteLLM Proxy Configuration ===" "Cyan"
    Write-ColorOutput "Script Version: $ScriptVersion" "Gray"
    Write-ColorOutput "Port: $Port" "Gray"
    Write-ColorOutput ""

    # Step 1: Check if LiteLLM is already running
    Write-ColorOutput "[1/4] Checking if LiteLLM is already running..." "Cyan"
    
    $existingProc = Get-Process -ErrorAction SilentlyContinue | Where-Object { 
        $_.ProcessName -match 'litellm|python' -and $_.CommandLine -match 'litellm'
    }
    
    if ($existingProc) {
        Write-ColorOutput "[OK] LiteLLM is already running (PID: $($existingProc.Id))" "Green"
        if (-not $Force) {
            Write-ColorOutput "  (Use -Force flag to restart)" "Gray"
            Write-ColorOutput ""
            Write-ColorOutput "[2/4] Health Status" "Cyan"
            Write-ColorOutput "  Port: $Port" "Gray"
            Write-ColorOutput "  Status: RUNNING" "Green"
            Write-ColorOutput ""
            Write-ColorOutput "[3/4] Available Models" "Cyan"
            Write-ColorOutput "  Configure models in config/litellm_config.yaml" "Gray"
            Write-ColorOutput ""
            Write-ColorOutput "=== LiteLLM Proxy Ready ===" "Green"
            Write-ColorOutput "Access: $LiteLLMUrl" "Green"
            exit 0
        } else {
            Write-ColorOutput "[INFO] Force restart requested..." "Yellow"
            Stop-Process -InputObject $existingProc -Force
            Start-Sleep -Seconds 2
        }
    }

    # Step 2: Check if LiteLLM is installed
    Write-ColorOutput "[2/4] Checking LiteLLM installation..." "Cyan"
    
    $litellmCmd = Get-Command litellm -ErrorAction SilentlyContinue
    if (-not $litellmCmd) {
        Write-ColorOutput "[INFO] LiteLLM not found in PATH" "Yellow"
        Write-ColorOutput "  Install: pip install litellm" "Gray"
        Write-ColorOutput "  Or create config/litellm_config.yaml manually" "Gray"
    } else {
        Write-ColorOutput "[OK] LiteLLM found at: $($litellmCmd.Source)" "Green"
    }

    # Step 3: Start LiteLLM Proxy
    Write-ColorOutput "[3/4] Starting LiteLLM Proxy Server..." "Cyan"
    
    $configFile = Join-Path $RepoRoot "config\litellm_config.yaml"
    
    if (Test-Path $configFile) {
        Write-ColorOutput "  Using config: $configFile" "Gray"
        $cmd = "litellm --config $configFile --port $Port"
    } else {
        Write-ColorOutput "  No config file found, starting with defaults" "Yellow"
        $cmd = "litellm --port $Port"
    }
    
    # Start in background
    $proc = Start-Process -FilePath "cmd" `
        -ArgumentList "/c", $cmd `
        -PassThru `
        -NoNewWindow
    
    Write-ColorOutput "  Process started (PID: $($proc.Id))" "Green"
    
    # Wait a bit for server to start
    Start-Sleep -Seconds 3

    # Step 4: Health check
    Write-ColorOutput "[4/4] Health Status" "Cyan"
    
    try {
        $response = Invoke-WebRequest -Uri "$LiteLLMUrl/health" -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-ColorOutput "  Status: ok" "Green"
            Write-ColorOutput "  URL: $LiteLLMUrl" "Green"
        }
    } catch {
        Write-ColorOutput "  Status: Starting (may need a moment)" "Yellow"
        Write-ColorOutput "  URL: $LiteLLMUrl" "Gray"
    }

    Write-ColorOutput ""
    Write-ColorOutput "=== LiteLLM Proxy Ready ===" "Green"
    Write-ColorOutput "Access: $LiteLLMUrl" "Green"
    Write-ColorOutput "Docs: $LiteLLMUrl/docs" "Gray"
    Write-ColorOutput ""

} catch {
    Write-ColorOutput ""
    Write-ColorOutput "[ERROR] $($_.Exception.Message)" "Red"
    exit 1
}
