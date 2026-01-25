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

# Runtime sanity checks ----------------------------------------------------
if (-not $PSVersionTable) {
    Write-Host "This script must be run under PowerShell." -ForegroundColor Red
    exit 2
}
if ($PSVersionTable.PSVersion.Major -lt 5) {
    Write-Host "PowerShell 5.1+ is required. Detected: $($PSVersionTable.PSVersion)" -ForegroundColor Red
    exit 2
}
# Self-parse the file at runtime to catch environments that mangle line-continuations
# Use a cross-version-safe approach: compile the script text into a ScriptBlock.
try {
    $scriptText = Get-Content -LiteralPath $MyInvocation.MyCommand.Path -Raw
    try {
        [scriptblock]::Create($scriptText) > $null
    } catch {
        Write-Host ("SYNTAX ERROR: $($_.Exception.Message)") -ForegroundColor Red
        exit 2
    }
} catch {
    Write-Host "Runtime parser check failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 2
}

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

# Normalize recipe_options.json (idempotent, safe) -------------------------------------------------
function Get-RecipeOptionsPaths {
    param([string]$ExplicitPath)
    if ($ExplicitPath) { return @($ExplicitPath) }

    $candidates = @()
    if ($env:USERPROFILE) { $candidates += Join-Path $env:USERPROFILE ".cache\lemonade\recipe_options.json" }
    if ($env:LOCALAPPDATA)  { $candidates += Join-Path $env:LOCALAPPDATA "lemonade\recipe_options.json" }
    if ($env:APPDATA)       { $candidates += Join-Path $env:APPDATA "lemonade\recipe_options.json" }
    if ($env:USERPROFILE) { $candidates += Join-Path $env:USERPROFILE "AppData\Local\lemonade\recipe_options.json" }

    return $candidates | Select-Object -Unique | Where-Object { Test-Path $_ }
}

function Normalize-RecipeOptions {
    [CmdletBinding()]
    param(
        [string]$Path,
        [switch]$DryRun
    )

    $paths = Get-RecipeOptionsPaths -ExplicitPath $Path
    if (-not $paths -or $paths.Count -eq 0) {
        Write-ColorOutput "  No recipe_options.json found to normalize" "Gray"
        return $false
    }

    $anyChanged = $false
    foreach ($p in $paths) {
        try {
            $text = Get-Content -LiteralPath $p -Raw -ErrorAction Stop
            try {
                $json = ConvertFrom-Json $text -ErrorAction Stop
            } catch {
                Write-ColorOutput "  Could not parse recipe_options.json at $p - skipping" "Yellow"
                continue
            }

            $changed = $false
            foreach ($prop in $json.PSObject.Properties.Name) {
                $entry = $json.$prop
                if ($null -ne $entry.llamacpp_args) {
                    $orig = [string]$entry.llamacpp_args

                    # Normalization rules (idempotent):
                    #  - bare "--flash-attn" -> "--flash-attn=auto"
                    #  - "--flash-attn on" -> "--flash-attn=on" (and likewise for off)
                    # normalize explicit forms first ("--flash-attn on"/"off")
                    $normalized = $orig -replace '(?i)\s--flash-attn\s+on', ' --flash-attn=on'
                    $normalized = $normalized -replace '(?i)\s--flash-attn\s+off', ' --flash-attn=off'
                    # then convert bare flag to =auto (idempotent)
                    $normalized = $normalized -replace '(?i)(^|\s)--flash-attn($|\s)', ' --flash-attn=auto'
                    $normalized = $normalized -replace '\s{2,}', ' '
                    $normalized = $normalized.Trim()

                    if ($normalized -ne $orig) {
                        Write-ColorOutput "    Normalizing recipe_options for '$prop': '$orig' -> '$normalized'" "Gray"
                        $entry.llamacpp_args = $normalized
                        $json.$prop = $entry
                        $changed = $true
                        $anyChanged = $true
                    }
                }
            }

            if ($changed) {
                if ($DryRun) {
                    Write-ColorOutput "    DRY-RUN: would write changes to $p" "Yellow"
                } else {
                    $bak = "$p.bak.$((Get-Date).ToString('yyyyMMdd-HHmmss'))"
                    Copy-Item -LiteralPath $p -Destination $bak -ErrorAction SilentlyContinue
                    $json | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $p -Encoding UTF8
                    Write-ColorOutput "    Wrote normalized recipe_options.json to $p (backup: $bak)" "Green"
                }
            } else {
                Write-ColorOutput "    No changes required in $p" "Gray"
            }
        } catch {
            Write-ColorOutput ("    Error normalizing {0}: {1}" -f $p, $_.Exception.Message) "Yellow"
        }
    }

    return $anyChanged
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

# Backward-compatible structured defaults. Prefer values here when present.
# Non-breaking: keep $DefaultEnabledIds for simple lists; structured entries win when both present.
$DefaultEnabledModels = @(
    @{ id = 'Qwen3-Coder-30B-A3B-Instruct-GGUF'; ctx_size = 16384; llamacpp_backend = 'vulkan' },
    @{ id = 'Gemma-3-4b-it-GGUF';                    ctx_size = 16384; llamacpp_backend = 'vulkan' }
)
# Note: operators may override via -LoadModels or per-model recipe_options.json (highest precedence).

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
        # Resolve structured default (if any) without error when variable missing
        $defaultModelConfig = $null
        if (Get-Variable -Name DefaultEnabledModels -Scope Script -ErrorAction SilentlyContinue) {
            $defaultModelConfig = $DefaultEnabledModels | Where-Object { $_.id -eq $m.id } | Select-Object -First 1
        }

        # enabled: legacy ID list OR structured defaults
        $enabledFromDefaults = ($DefaultEnabledIds -contains $m.id) -or ($null -ne $defaultModelConfig)

        # context precedence: server catalog recipe_options -> DefaultEnabledModels -> catalog.context -> 0 (handled later)
        $resolvedContext = if ($m.recipe_options -and $m.recipe_options.ctx_size) {
            $m.recipe_options.ctx_size
        } elseif ($defaultModelConfig -and $defaultModelConfig.ctx_size) {
            $defaultModelConfig.ctx_size
        } else {
            ($m.context -as [int])
        }

        # backend precedence: recipe_options -> DefaultEnabledModels -> $null
        $resolvedBackend = if ($m.recipe_options -and $m.recipe_options.llamacpp_backend) {
            $m.recipe_options.llamacpp_backend
        } elseif ($defaultModelConfig -and $defaultModelConfig.llamacpp_backend) {
            $defaultModelConfig.llamacpp_backend
        } else {
            $null
        }

        $mps = [pscustomobject]@{
            name        = $m.id
            alias       = $m.alias
            enabled     = $enabledFromDefaults
            size        = ($m.size -as [string])
            context     = ($resolvedContext -as [int])
            description = $m.description
            checkpoint  = $m.checkpoint
            recipe      = $m.recipe
            downloaded  = $m.downloaded
            suggested   = $m.suggested
            labels      = $m.labels
            recipe_options = @{ ctx_size = ($resolvedContext -as [int]); llamacpp_backend = $resolvedBackend }
        }
        $ModelsToLoad += $mps
    }
} else {
    Write-ColorOutput "  WARNING: could not fetch model catalog from server - falling back to embedded defaults" "Yellow"
    # fallback static minimal list (kept for offline/dev scenarios)
    $ModelsToLoad = @(
        [pscustomobject]@{ name = 'Qwen3-Coder-30B-A3B-Instruct-GGUF'; alias='qwen-coder-30b'; enabled=$false;  context=32768; description='Coding/Tools' },
        [pscustomobject]@{ name = 'Gemma-3-4b-it-GGUF';                    alias='gemma-3-4b';    enabled=$true;  context=16384; description='Fast Responses' },
        [pscustomobject]@{ name = 'Whisper-Large-v3-Turbo';               alias='whisper';       enabled=$true;  context=8192;  description='Audio Transcription' },
        [pscustomobject]@{ name = 'Phi-4-mini-instruct-GGUF';              alias='phi-4';         enabled=$true; context=16384; description='Latest Phi (Compact)' },
        [pscustomobject]@{ name = 'GLM-4.7-GGUF';                         alias='glm-4.7';       enabled=$false; context=8192;  description='GLM 4.7 — compact instruction model (add to catalog when available)' }
    )
}


# Update enabled models based on LoadModels parameter
if ($LoadModels) {
    # Accept several invocation styles:
    #  - -LoadModels phi-4,phi-3  (single comma-separated string)
    #  - -LoadModels 'phi-4','phi-3' (array)
    if (($LoadModels.Count -eq 1) -and ($LoadModels[0] -match ',')) {
        $LoadModels = ($LoadModels[0] -split '\s*,\s*')
    }

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
            
            # Ensure the server is *requested* to load the model with a sane ctx_size before probing it.
            $loadRequest = @{ model_name = $model.name }

            # Prefer per-model saved recipe_options when present (keeps behavior consistent with server)
            if ($model.recipe_options) {
                if ($model.recipe_options.ctx_size) { $loadRequest.ctx_size = $model.recipe_options.ctx_size }
                if ($model.recipe_options.llamacpp_backend) { $loadRequest.llamacpp_backend = $model.recipe_options.llamacpp_backend }
                if ($model.recipe_options.llamacpp_args) { $loadRequest.llamacpp_args = $model.recipe_options.llamacpp_args }
            }

            # If no ctx_size determined yet, use model.catalog value or a conservative default
            if (-not $loadRequest.ContainsKey('ctx_size')) {
                if ($model.context -and ($model.context -gt 0)) {
                    $loadRequest.ctx_size = $model.context
                } else {
                    # conservative default to avoid starting wrapped server with an empty/zero ctx
                    $loadRequest.ctx_size = 4096
                }
            }

            # Defensive normalization for known llama-server flags that REQUIRE a value.
            if ($loadRequest.llamacpp_args) {
                # normalize bare --flash-attn -> --flash-attn=auto (robust regex, cross-shell)
                if ($loadRequest.llamacpp_args -match '(?i)(^|\s)--flash-attn($|\s)') {
                    $loadRequest.llamacpp_args = '--flash-attn=auto'
                    Write-ColorOutput "    Normalized llamacpp_args to '--flash-attn=auto'" "Gray"
                }
            }

            # Helper to send load request and return tuple(success, response/error)
            function Send-LoadRequest($payload) {
                try {
                    $lrParams = @{
                        Method = 'Post'
                        Uri = "$ServerUrl/api/v1/load"
                        ContentType = 'application/json'
                        Body = ($payload | ConvertTo-Json)
                        TimeoutSec = 120
                        ErrorAction = 'Stop'
                    }
                    $r = Invoke-RestMethod @lrParams
                    return @{ ok = $true; resp = $r }
                } catch {
                    return @{ ok = $false; err = $_.Exception.Message }
                }
            }

            # First attempt: send normalized/sane request
            $sendResult = Send-LoadRequest $loadRequest
            if ($sendResult.ok) {
                Write-Host "    [load requested: ctx=$($loadRequest.ctx_size)]" -ForegroundColor Gray
            } else {
                Write-ColorOutput "    Warning: load request failed: $($sendResult.err)" "Yellow"
            }

            # If the initial probe later fails with a wrapped-server error that looks like
            # an argument parsing problem, perform automatic remediation attempts below
            $autoRemediated = $false
            $remediationAttempts = @()
            $remediationAttempts += @{ reason = 'explicit-flash-attn'; apply = { param($lr) ; $lr.llamacpp_args = '--flash-attn=auto'; $lr } }
            $remediationAttempts += @{ reason = 'force-cpu-backend'; apply = { param($lr) ; $lr.Remove('llamacpp_args') | Out-Null; $lr.llamacpp_backend = 'cpu'; $lr } }

            # remember the last probe exception message for remediation decisions
            $lastProbeError = $null

            try {
                Write-ColorOutput "    (probing server to confirm model start)" "Gray"
            } catch {
                # noop - keep script robust
            }

            # Probe the model via chat/completions (server will attempt to start the wrapped process)
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
                    $invokeParams = @{
                        Method = 'Post'
                        Uri = "$ServerUrl/api/v1/chat/completions"
                        Headers = @{ 'Content-Type' = 'application/json' }
                        Body = $payload
                        TimeoutSec = $attemptTimeout
                        ErrorAction = 'Stop'
                    }
                    $response = Invoke-RestMethod @invokeParams

                    Write-Host " [OK]" -ForegroundColor Green
                    $successCount++
                    $loaded = $true
                    break
                } catch {
                    # capture the probe error for remediation logic
                    $lastProbeError = $_.Exception.Message

                    if ($attempt -lt $maxAttempts) {
                        Write-Host " [retry $attempt]" -ForegroundColor Yellow -NoNewline
                        Start-Sleep -Seconds 5
                    }
                }
            }

            if (-not $loaded) {
                Write-Host " [FAIL]" -ForegroundColor Red
                Write-ColorOutput "    Error: $($lastProbeError -or 'unknown')" "Red"

                # Remediation: if the failure looks like an argument parse error, try automated fallbacks
                if ($lastProbeError -and $lastProbeError -match '(?i)flash-attn|expected value for argument|llama-server failed to start') {
                    foreach ($rem in $remediationAttempts) {
                        if ($autoRemediated) { break }
                        Write-ColorOutput "    Attempting remediation: $($rem.reason)" "Yellow"
                        $candidate = & $rem.apply $loadRequest.Clone()
                        $res = Send-LoadRequest $candidate
                        if ($res.ok) {
                            Write-ColorOutput "    Remediation request accepted (reason: $($rem.reason)), probing..." "Gray"

                            # quick probe
                            try {
                                $probe = Invoke-RestMethod -Method Post -Uri "$ServerUrl/api/v1/chat/completions" -Headers @{ 'Content-Type' = 'application/json' } -Body $payload -TimeoutSec 30 -ErrorAction Stop
                                Write-Host "    [OK after remediation]" -ForegroundColor Green
                                $successCount++
                                $loaded = $true
                                $autoRemediated = $true
                                break
                            } catch {
                                Write-ColorOutput "    Remediation probe failed: $($_.Exception.Message)" "Yellow"
                                # continue to next remediation
                            }
                        } else {
                            Write-ColorOutput "    Remediation request rejected: $($res.err)" "Yellow"
                        }
                    }
                }

                if (-not $loaded) {
                    $failCount++
                }
            }
        } catch {
            Write-Host " [FAIL]" -ForegroundColor Red
            Write-ColorOutput "    Error: $($_.Exception.Message)" "Red"
            $failCount++
        }
    }
    
    Write-ColorOutput ""
    $summaryColor = if ($failCount -gt 0) { "Red" } else { "Green" }
    Write-ColorOutput "Model loading summary: $successCount loaded, $failCount failed" $summaryColor
    
    return $failCount -eq 0
}

function Unload-Models {
    param(
        [int]$Parallelism = 6,
        [int]$PerRequestTimeout = 5
    )

    Write-ColorOutput "[Cleanup] Unloading disabled models to free memory... (parallel=$Parallelism, timeout=${PerRequestTimeout}s)" "Cyan"

    # Determine candidates (disabled in the catalog)
    $modelsToUnloadCandidates = @($ModelsToLoad | Where-Object { $_.enabled -eq $false })

    # Try to limit unload requests to models that are actually loaded on the server
    $health = Get-HealthStatus
    if ($null -eq $health -or -not $health.all_models_loaded) {
        Write-ColorOutput "  Could not query server health; falling back to attempting to unload disabled models (may include models that are not loaded)" "Yellow"
        $modelsToUnloadList = $modelsToUnloadCandidates
    } else {
        $loadedNames = @($health.all_models_loaded | ForEach-Object { $_.model_name })
        $modelsToUnloadList = $modelsToUnloadCandidates | Where-Object { $loadedNames -contains $_.name }
        $skipped = $modelsToUnloadCandidates.Count - $modelsToUnloadList.Count

        if ($modelsToUnloadList.Count -eq 0) {
            if ($skipped -gt 0) {
                Write-ColorOutput "  No loaded disabled models to unload (skipped $skipped not-loaded disabled model(s))" "Gray"
            } else {
                Write-ColorOutput "  No disabled models to unload" "Gray"
            }
            return $true
        }

        Write-ColorOutput "  Unloading $($modelsToUnloadList.Count) loaded disabled model(s); skipped $skipped not-loaded disabled model(s)" "Gray"
    }

    # Provide a default Send-UnloadRequest if caller/test hasn't supplied one (can be overridden in a child session)
    if (-not (Get-Command Send-UnloadRequest -ErrorAction SilentlyContinue)) {
        function Send-UnloadRequest {
            param([string]$ServerUrl, [string]$ModelName, [int]$TimeoutSec)
            try {
                $payload = @{ model_name = $ModelName } | ConvertTo-Json -Depth 3
                $r = Invoke-RestMethod -Method Post -Uri "$ServerUrl/api/v1/unload" -Headers @{ 'Content-Type' = 'application/json' } -Body $payload -TimeoutSec $TimeoutSec -ErrorAction Stop
                return @{ ok = $true; model = $ModelName; resp = $r }
            } catch {
                return @{ ok = $false; model = $ModelName; err = $_.Exception.Message }
            }
        }
    }

    $successCount = 0
    $failCount = 0
    $sw = [System.Diagnostics.Stopwatch]::StartNew()

    # Process in bounded concurrent batches (PowerShell 5.1 compatible)
    for ($i = 0; $i -lt $modelsToUnloadList.Count; $i += $Parallelism) {
        $end = [math]::Min($i + $Parallelism - 1, $modelsToUnloadList.Count - 1)
        $batch = $modelsToUnloadList[$i..$end]
        $jobs = @()

        foreach ($m in $batch) {
            $jobs += Start-Job -ArgumentList $ServerUrl, $m.name, $PerRequestTimeout -ScriptBlock {
                param($sv, $mn, $to)
                try {
                    $payload = @{ model_name = $mn } | ConvertTo-Json -Depth 3
                    $r = Invoke-RestMethod -Method Post -Uri "$sv/api/v1/unload" -Headers @{ 'Content-Type' = 'application/json' } -Body $payload -TimeoutSec $to -ErrorAction Stop
                    return @{ ok = $true; model = $mn }
                } catch {
                    return @{ ok = $false; model = $mn; err = $_.Exception.Message }
                }
            }
            Write-Host "  Unload queued: $($m.name)" -ForegroundColor Gray
        }

        # Wait bounded time for this batch (allow slight overhead)
        $waitTotal = $PerRequestTimeout + 3
        Wait-Job -Job $jobs -Timeout $waitTotal | Out-Null

        foreach ($j in $jobs) {
            if ($j.State -eq 'Completed') {
                $res = Receive-Job -Job $j -ErrorAction SilentlyContinue
                if ($res -and $res.ok) {
                    Write-Host "  $($res.model) [OK]" -ForegroundColor Green
                    $successCount++
                } else {
                    $err = $res.err -or 'unknown'
                    if ($err -match '404|Not Found|Model not loaded') {
                        Write-Host "  $($res.model) [SKIP] (not loaded)" -ForegroundColor Gray
                    } else {
                        Write-Host "  $($res.model) [WARN] $err" -ForegroundColor Yellow
                        $failCount++
                    }
                }
            } else {
                Write-Host "  Job timeout/failed for id=$($j.Id) (state=$($j.State))" -ForegroundColor Yellow
                $failCount++
            }
            try { Remove-Job -Job $j -Force -ErrorAction SilentlyContinue } catch { }
        }
    }

    $sw.Stop()
    Write-ColorOutput "Finished unload: $successCount succeeded, $failCount failed in $([math]::Round($sw.Elapsed.TotalSeconds,1))s" "Gray"

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
            "--max-loaded-models", "5", "2", "2", "2",
            "--log-level", "error"
            # Do NOT set global --llamacpp-args here - per-model recipe_options or explicit /api/v1/load
            # requests are safer. Passing unsupported args can cause wrapped servers to exit with code 1.
        )
        
        $logDir = Join-Path $RepoRoot "logs"
        if (-not (Test-Path $logDir)) {
            New-Item -ItemType Directory -Path $logDir | Out-Null
        }
        $logFile = Join-Path $logDir "lemonade-server.log"
        
        $spArgs = @{
            FilePath = 'lemonade-server'
            ArgumentList = $serverArgs
            NoNewWindow = $true
            RedirectStandardOutput = $logFile
            PassThru = $true
        }
        Start-Process @spArgs | Out-Null

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

} catch {
    Write-ColorOutput ("FATAL: {0}" -f $_.Exception.Message) "Red"
    if ($ScriptLog) { Write-ColorOutput "Script transcript: $ScriptLog" "Gray" }
    exit 3
} finally {
    try { Stop-Transcript -ErrorAction SilentlyContinue } catch { }
}
