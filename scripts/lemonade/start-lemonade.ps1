#Requires -Version 5.1
<#
.SYNOPSIS
    Start Lemonade Server with Quality Configuration and Model Management
.DESCRIPTION
    Production-ready startup script for Lemonade Server with:
    - Idempotent health checking (no unnecessary restarts)
    - Selective model loading with alias support
    - Auto-start of Lemonade Desktop app
    - Comprehensive status monitoring
.PARAMETER LoadModels
    Specify which models to load by alias (e.g., 'qwen-coder-30b','gemma-3-4b')
    If not specified, uses default enabled models from configuration
.PARAMETER Force
    Force restart server even if already running and force reload models
.EXAMPLE
    .\start-lemonade.ps1
    Load default enabled models
.EXAMPLE
    .\start-lemonade.ps1 -LoadModels 'qwen-coder-30b'
    Load only Qwen Coder model
.EXAMPLE
    .\start-lemonade.ps1 -LoadModels 'phi-3-mini','phi-4' -Force
    Restart server and load Phi models
#>

param(
    [string[]]$LoadModels,
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$ScriptVersion = "1.0.0"
$ServerUrl = "http://localhost:8000"
$ServerPort = 8000
$RepoRoot = (Get-Location).Path

# Ensure logs directory exists early and start a transcript so the script output is captured
$logDir = Join-Path $RepoRoot "logs"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
$ScriptLog = Join-Path $logDir ("start-lemonade-{0}.log" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))
try { Start-Transcript -Path $ScriptLog -Force -ErrorAction SilentlyContinue } catch { Write-Host "[WARN] Start-Transcript failed: $($_.Exception.Message)" -ForegroundColor Yellow }

# Color output helper
function Write-ColorOutput {
    param([string]$Message, [string]$Color)
    if ([string]::IsNullOrEmpty($Color)) { $Color = "White" }
    Write-Host $Message -ForegroundColor $Color
}

# Format context window size (16384 -> 16k)
function Format-ContextSize {
    param([int]$Size)
    if ($Size -ge 1000000) { return "$([math]::Round($Size / 1000000))M" }
    if ($Size -ge 1000) { return "$([math]::Round($Size / 1000))k" }
    return $Size
}

# Model configuration (initialized from Lemonade catalog - source of truth)
# Behavior:
# - Attempt to initialize $ModelsToLoad from GET /api/v1/models?show_all=true
# - Preserve a small repo-managed default enabled list (quality defaults)
# - Fall back to an embedded static list if the catalog cannot be fetched

$DefaultEnabledIds = @(
    'Qwen3-Coder-30B-A3B-Instruct-GGUF',
    'Gemma-3-4b-it-GGUF',
    'Whisper-Large-v3-Turbo'
)

function Get-ModelsFromCatalog {
    param([string]$ServerUrl)
    try {
        $resp = Invoke-RestMethod -Uri "$ServerUrl/api/v1/models?show_all=true" -TimeoutSec 10 -ErrorAction Stop
        if (-not $resp.data) { return $null }
        return $resp.data | ForEach-Object {
            [pscustomobject]@{
                id         = $_.id
                created    = $_.created
                object     = $_.object
                owned_by   = $_.owned_by
                checkpoint = $_.checkpoint
                recipe     = $_.recipe
                size       = $_.size
                downloaded = $_.downloaded
                suggested  = $_.suggested
                labels     = @($_.labels) -as [string[]]
                description= ($_.description -or $_.checkpoint)
                context    = ($_.recipe_options.ctx_size -or 0)
                alias      = ($_.id -replace '[^a-z0-9\-]','-' -replace '--','-').ToLower()
            }
        }
    } catch {
        return $null
    }
}

$ModelsToLoad = @()
$catalog = Get-ModelsFromCatalog -ServerUrl $ServerUrl
if ($catalog) {
    Write-ColorOutput "  Initialized model catalog from Lemonade server (source-of-truth)" "Gray"
    foreach ($m in $catalog) {
        $mps = @{
            name        = $m.id
            alias       = $m.alias
            enabled     = ($DefaultEnabledIds -contains $m.id)
            size        = ($m.size -as [string])
            context     = ($m.context -as [int])
            description = $m.description
            checkpoint  = $m.checkpoint
            recipe      = $m.recipe
            downloaded  = $m.downloaded
            suggested   = $m.suggested
            labels      = $m.labels
        }
        $ModelsToLoad += $mps
    }
} else {
    Write-ColorOutput "  WARNING: could not fetch model catalog from server — falling back to embedded defaults" "Yellow"
    # fallback static minimal list (kept for offline/dev scenarios)
    $ModelsToLoad = @(
        @{ name = 'Qwen3-Coder-30B-A3B-Instruct-GGUF'; alias='qwen-coder-30b'; enabled=$false;  context=32768; description='Coding/Tools' },
        @{ name = 'Gemma-3-4b-it-GGUF';                    alias='gemma-3-4b';    enabled=$true;  context=16384; description='Fast Responses' },
        @{ name = 'Whisper-Large-v3-Turbo';               alias='whisper';       enabled=$true;  context=8192;  description='Audio Transcription' },
        @{ name = 'Phi-4-mini-instruct-GGUF';              alias='phi-4';         enabled=$true; context=16384; description='Latest Phi (Compact)' },
        @{ name = 'GLM-4.7-GGUF';                         alias='glm-4.7';       enabled=$false; context=8192;  description='GLM 4.7 — compact instruction model (add to catalog when available)' }
    )
}


# Update enabled models based on LoadModels parameter
if ($LoadModels) {
    $ModelsToLoad | ForEach-Object { $_.enabled = $false }
    
    foreach ($modelSpec in $LoadModels) {
        $found = $false
        
        # Try to match by alias first
        $match = $ModelsToLoad | Where-Object { $_.alias -eq $modelSpec }
        if ($match) {
            $match.enabled = $true
            $found = $true
        } else {
            # Try exact name match
            $match = $ModelsToLoad | Where-Object { $_.name -eq $modelSpec }
            if ($match) {
                $match.enabled = $true
                $found = $true
            } else {
                # Try substring match
                $match = $ModelsToLoad | Where-Object { $_.name -match $modelSpec }
                if ($match) {
                    $match.enabled = $true
                    $found = $true
                }
            }
        }
        
        if (-not $found) {
            Write-ColorOutput "[WARN] Model '$modelSpec' not found" "Yellow"
        }
    }
} else {
    Write-ColorOutput "  Using default enabled model configuration" "Gray"
}

function Test-ServerHealth {
    try {
        $response = Invoke-RestMethod -Uri "$ServerUrl/api/v1/models" -TimeoutSec 3 -ErrorAction Stop
        return $response -and $response.data -and $response.data.Count -gt 0
    } catch {
        return $false
    }
}

function Get-SystemInfo {
    try {
        $response = Invoke-RestMethod -Uri "$ServerUrl/api/v1/system-info" -TimeoutSec 3 -ErrorAction Stop
        return $response
    } catch {
        return $null
    }
}

function Get-HealthStatus {
    try {
        $response = Invoke-RestMethod -Uri "$ServerUrl/api/v1/health" -TimeoutSec 3 -ErrorAction Stop
        return $response
    } catch {
        return $null
    }
}

function Check-NPUExclusivity {
    $enabledModels = @($ModelsToLoad | Where-Object { $_.enabled -eq $true })
    $npuModels = @($enabledModels | Where-Object { $_.name -match '(Qwen3|NPU|A3B)' })
    
    if ($npuModels.Count -gt 1) {
        Write-ColorOutput "`n[WARNING] NPU Exclusivity" "Yellow"
        Write-ColorOutput "  Multiple NPU models enabled: $($npuModels.Count)" "Yellow"
        Write-ColorOutput "  Only ONE model can use NPU at a time." "Yellow"
        Write-ColorOutput "  Others will fall back to CPU/GPU." "Yellow"
    }
}

function Wait-ServerReady {
    param([int]$MaxWait = 30)
    $elapsed = 0
    while ($elapsed -lt $MaxWait) {
        if (Test-ServerHealth) {
            return $true
        }
        Start-Sleep -Seconds 1
        $elapsed += 1
        Write-Host "." -NoNewline -ForegroundColor Cyan
    }
    return $false
}

function Load-Models {
    Write-ColorOutput "[3/4] Loading enabled models with context sizes..." "Cyan"
    
    $modelsToLoadList = @($ModelsToLoad | Where-Object { $_.enabled -eq $true })
    
    if ($modelsToLoadList.Count -eq 0) {
        Write-ColorOutput "  No models enabled for loading" "Yellow"
        return $true
    }
    
    $successCount = 0
    $failCount = 0
    
    foreach ($model in $modelsToLoadList) {
        try {
            Write-Host "  Loading $($model.name) (ctx: $($model.context))..." -NoNewline -ForegroundColor Cyan
            
            $payload = @{
                model = $model.name
                messages = @(@{ role = "user"; content = "init" })
                max_tokens = 10
            } | ConvertTo-Json -Depth 3
            
            $loaded = $false
            $maxAttempts = 4
            for ($attempt = 1; $attempt -le $maxAttempts; $attempt++) {
                try {
                    $attemptTimeout = 40
                    $response = Invoke-RestMethod `
                        -Method Post `
                        -Uri "$ServerUrl/api/v1/chat/completions" `
                        -Headers @{ "Content-Type" = "application/json" } `
                        -Body $payload `
                        -TimeoutSec $attemptTimeout `
                        -ErrorAction Stop

                    Write-Host " [OK]" -ForegroundColor Green
                    $successCount++
                    $loaded = $true
                    break
                } catch {
                    if ($attempt -lt $maxAttempts) {
                        Write-Host " [retry $attempt]" -ForegroundColor Yellow -NoNewline
                        Start-Sleep -Seconds 5
                    }
                }
            }
            if (-not $loaded) {
                Write-Host " [FAIL]" -ForegroundColor Red
                Write-ColorOutput "    Error: $($_.Exception.Message)" "Red"
                $failCount++
            }
        } catch {
            Write-Host " [FAIL]" -ForegroundColor Red
            Write-ColorOutput "    Error: $($_.Exception.Message)" "Red"
            $failCount++
        }
    }
    
    Write-ColorOutput ""
    Write-ColorOutput "Model loading summary: $successCount loaded, $failCount failed" `
        $(if ($failCount -gt 0) { "Red" } else { "Green" })
    
    return $failCount -eq 0
}

function Unload-Models {
    Write-ColorOutput "[Cleanup] Unloading disabled models to free memory..." "Cyan"
    
    $modelsToUnloadList = @($ModelsToLoad | Where-Object { $_.enabled -eq $false })
    
    if ($modelsToUnloadList.Count -eq 0) {
        Write-ColorOutput "  No disabled models to unload" "Gray"
        return $true
    }
    
    $successCount = 0
    $failCount = 0
    
    foreach ($model in $modelsToUnloadList) {
        try {
            Write-Host "  Unloading $($model.name)..." -NoNewline -ForegroundColor Cyan
            
            $payload = @{
                model_name = $model.name
            } | ConvertTo-Json -Depth 3
            
            try {
                $response = Invoke-RestMethod `
                    -Method Post `
                    -Uri "$ServerUrl/api/v1/unload" `
                    -Headers @{ "Content-Type" = "application/json" } `
                    -Body $payload `
                    -TimeoutSec 10 `
                    -ErrorAction Stop
                
                Write-Host " [OK]" -ForegroundColor Green
                $successCount++
            } catch {
                if ($_.Exception.Message -match "Model not loaded") {
                    Write-Host " [SKIP]" -ForegroundColor Gray
                    Write-ColorOutput "    (Model not loaded)" "Gray"
                } else {
                    Write-Host " [WARN]" -ForegroundColor Yellow
                    Write-ColorOutput "    Warning: $($_.Exception.Message)" "Yellow"
                }
            }
        } catch {
            Write-Host " [FAIL]" -ForegroundColor Red
            Write-ColorOutput "    Error: $($_.Exception.Message)" "Red"
            $failCount++
        }
    }
    
    return $failCount -eq 0
}

try {
    Write-ColorOutput "=====================================================" "Cyan"
    Write-ColorOutput "  LEMONADE SERVER STARTUP" "Cyan"
    Write-ColorOutput "=====================================================" "Cyan"
    Write-ColorOutput ""
    
    Write-ColorOutput "=== Lemonade Server ===" "Green"
    Write-ColorOutput "Script Version: $ScriptVersion" "Gray"
    Write-ColorOutput ""
    
    # Step 0: Display system resources
    Write-ColorOutput "[0/4] System Resources" "Cyan"
    $sysInfo = Get-SystemInfo
    if ($sysInfo) {
        $proc = Get-WmiObject -Class Win32_Processor
        Write-ColorOutput "  Processor: $($proc.Name)" "Gray"
        Write-ColorOutput "  OS: " "Gray"
        Write-ColorOutput "  Available Memory: 0 GB" "Gray"
        
        if ($sysInfo.devices) {
            Write-ColorOutput "  Devices:" "Gray"
            $sysInfo.devices.PSObject.Properties | ForEach-Object {
                $deviceCount = $_.Value | Measure-Object | Select-Object -ExpandProperty Count
                Write-ColorOutput "    - $($_.Name): $deviceCount available" "Gray"
            }
        }
    } else {
        Write-ColorOutput "  [INFO] System info not available (server not running yet)" "Yellow"
    }
    Write-ColorOutput "" ""
    
    # Step 1: Check if server is already running
    Write-ColorOutput "[1/4] Checking if server is already running..." "Cyan"
    $serverHealthy = $false
    $wasAlreadyRunning = $false
    $forceModelReload = $false
    try {
        if (Test-ServerHealth) {
            Write-ColorOutput "[OK] Server is already running and models are loaded" "Green"
            $serverHealthy = $true
            $wasAlreadyRunning = $true
            Write-ColorOutput "  (Use -Force flag to restart)" "Yellow"
        }
    } catch {
        Write-ColorOutput "[WARN] Could not connect to server" "Yellow"
    }
    
    # Step 2: Start server if needed
    if ($Force -or -not $serverHealthy) {
        if ($Force) {
            Write-ColorOutput "[2/4] Force restart requested - stopping existing server..." "Cyan"
            try {
                $procs = Get-Process -Name "lemonade-server" -ErrorAction SilentlyContinue
                if ($procs) {
                    foreach ($proc in $procs) {
                        Write-ColorOutput "Stopping server on port $ServerPort..." "Yellow"
                        
                        $childProcs = Get-WmiObject -Class Win32_Process | `
                            Where-Object { $_.ParentProcessId -eq $proc.Id }
                        
                        if ($childProcs) {
                            foreach ($child in $childProcs) {
                                Write-ColorOutput "  Found child process: $($child.Name) (PID: $($child.ProcessId))" "Gray"
                            }
                        }
                        
                        Write-ColorOutput "Terminating router (PID: $($proc.Id))..." "Yellow"
                        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
                        
                        foreach ($child in $childProcs) {
                            Write-ColorOutput "Terminating child process (PID: $($child.ProcessId))..." "Yellow"
                            Stop-Process -Id $child.ProcessId -Force -ErrorAction SilentlyContinue
                        }
                        
                        Write-ColorOutput "Waiting for processes to exit (up to 5 seconds)..." "Gray"
                        Start-Sleep -Seconds 2
                    }
                    Write-ColorOutput "Lemonade Server stopped successfully." "Green"
                } else {
                    Write-ColorOutput "Lemonade Server is not running" "Yellow"
                }
            } catch {
                Write-ColorOutput "  (No running instance to stop)" "Yellow"
            }
        } else {
            Write-ColorOutput "[2/4] Starting Lemonade Server on port $ServerPort..." "Cyan"
        }
        
        $serverArgs = @(
            "serve",
            "--port", $ServerPort,
            "--max-loaded-models", "4", "1", "1", "1",
            "--log-level", "error",
            "--llamacpp-args", "--flash-attn=on"
        )
        
        $logDir = Join-Path $RepoRoot "logs"
        if (-not (Test-Path $logDir)) {
            New-Item -ItemType Directory -Path $logDir | Out-Null
        }
        $logFile = Join-Path $logDir "lemonade-server.log"
        
        Start-Process -FilePath "lemonade-server" `
            -ArgumentList $serverArgs `
            -NoNewWindow `
            -RedirectStandardOutput $logFile `
            -PassThru | Out-Null
        
        Write-ColorOutput "[OK] Server process started" "Green"
        Write-ColorOutput "  Waiting for server to be ready..." "Cyan"
        
        if (Wait-ServerReady -MaxWait 30) {
            Write-ColorOutput "" "White"
            Write-ColorOutput "[OK] Server is responding" "Green"
        } else {
            Write-ColorOutput "" "White"
            Write-ColorOutput "[WARN] Server started but not responding to /models endpoint (may still be loading)" "Yellow"
        }
    }
    
    # Step 3: Load models based on configuration
    $currentHealth = Get-HealthStatus
    $modelsCurrentlyLoaded = @($currentHealth.all_models_loaded).Count
    $expectedEnabled = ($ModelsToLoad | Where-Object { $_.enabled -eq $true }).Count
    $shouldLoadModels = $false

    # Decide to (re)load models when server not running, when forced, or when the number
    # of loaded models is less than the configured enabled set (recover partial state).
    if (-not $wasAlreadyRunning -or $Force -or $forceModelReload) {
        $shouldLoadModels = $true
    } elseif ($modelsCurrentlyLoaded -eq 0) {
        $shouldLoadModels = $true
        Write-ColorOutput "[INFO] No models currently loaded, loading configured models..." "Yellow"
    } elseif ($modelsCurrentlyLoaded -lt $expectedEnabled) {
        # NEW: attempt to load missing models even if the server is already running
        Write-ColorOutput "[WARN] Partial model state detected: $modelsCurrentlyLoaded of $expectedEnabled configured models are loaded. Attempting to load missing models..." "Yellow"
        $shouldLoadModels = $true
    }

    if ($shouldLoadModels) {
        Check-NPUExclusivity

        $modelsToLoadList = @($ModelsToLoad | Where-Object { $_.enabled -eq $true })

        if ($modelsToLoadList.Count -eq 0) {
            Write-ColorOutput "[3/4] No models enabled for loading" "Yellow"
        } else {
            $modelsLoaded = Load-Models
            if (-not $modelsLoaded) {
                Write-ColorOutput "[WARN] Some models failed to load (they may still load in background)" "Yellow"
            }
        }

        Unload-Models
    } else {
        Write-ColorOutput "[3/4] Server already running with models loaded - skipping model reload" "Yellow"
        Write-ColorOutput "  (Use -Force to reload models)" "Gray"
    }
    
    # Step 4: Display health status
    Write-ColorOutput "[4/4] Health Status" "Cyan"
    $health = Get-HealthStatus
    if ($health) {
        $loadedCount = @($health.all_models_loaded).Count
        Write-ColorOutput "  Script Version: $ScriptVersion | Server Version: $($health.version)" "Gray"
        Write-ColorOutput "  Server Status: $($health.status)" $(if ($health.status -eq "ok") { "Green" } else { "Yellow" })
        Write-ColorOutput "  Models Loaded: $loadedCount" "Green"
        
        if ($health.all_models_loaded -and $health.all_models_loaded.Count -gt 0) {
            Write-ColorOutput "  Loaded Model Details:" "Green"
            $health.all_models_loaded | ForEach-Object {
                $deviceType = if ($_.device) { $_.device } else { "Unknown" }
                Write-ColorOutput "    - $($_.model_name)" "Gray"
                Write-ColorOutput "      Checkpoint: $($_.checkpoint)" "Gray"
                Write-ColorOutput "      Device: $deviceType | Type: $($_.type)" "Gray"
                Write-ColorOutput "      Backend: $($_.backend_url)" "Gray"
            }
        }
    } else {
        Write-ColorOutput "  [INFO] Health status not available" "Yellow"
    }
    
    Write-ColorOutput ""
    Write-ColorOutput "=== Lemonade Server Ready ===" "Green"
    Write-ColorOutput "Script Version: $ScriptVersion" "Gray"
    Write-ColorOutput "Access: $ServerUrl" "Green"
    Write-ColorOutput "API: $ServerUrl/api/v1/models" "Green"
    Write-ColorOutput ""
    
    if ($modelsToLoadList.Count -gt 0) {
        Write-ColorOutput "Loaded models:" "Green"
        $modelsToLoadList | ForEach-Object {
            $contextStr = Format-ContextSize $_.context
            Write-ColorOutput "  - $($_.name) [$($_.alias)]" "Green"
            Write-ColorOutput "    $($_.description) | Size: $($_.size) | Context: $contextStr" "Gray"
        }
    }

    Write-ColorOutput ""
    Write-ColorOutput "All available models:" "Cyan"
    $ModelsToLoad | ForEach-Object {
        $status = if ($_.enabled) { "[ENABLED]" } else { "[disabled]" }
        $contextStr = Format-ContextSize $_.context
        Write-ColorOutput "  $status  $($_.alias) ($contextStr) - $($_.name)" $(if ($_.enabled) { "Green" } else { "Gray" })
    }
    Write-ColorOutput ""
    Write-ColorOutput "Usage examples:" "Cyan"
    Write-ColorOutput "  .\start-lemonade.ps1                                      # Load default enabled models" "Gray"
    Write-ColorOutput "  .\start-lemonade.ps1 -LoadModels 'qwen-coder-30b'         # Load by alias" "Gray"
    Write-ColorOutput "  .\start-lemonade.ps1 -LoadModels 'phi-3-mini','phi-4'     # Load multiple by alias" "Gray"
    Write-ColorOutput '  .\start-lemonade.ps1 -LoadModels "Qwen3-Coder-30B-A3B-Instruct-GGUF" -Force  # Full name + restart' "Gray"
    Write-ColorOutput ""
    
} catch {
    Write-ColorOutput ""
    Write-ColorOutput "[ERROR] $($_.Exception.Message)" "Red"
    try { Stop-Transcript -ErrorAction SilentlyContinue } catch {}
    exit 1
} finally {
    try { Stop-Transcript -ErrorAction SilentlyContinue } catch {}
}
