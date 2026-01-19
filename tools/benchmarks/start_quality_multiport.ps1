#!/usr/bin/pwsh
# Lemonade Quality Config - Single Server with Multiple Loaded Models
# Uses --max-loaded-models to keep all 4 models in VRAM simultaneously
# This is the ONLY working approach (no true multi-port support in Lemonade)

param([switch]$Start, [switch]$Stop, [switch]$Load, [switch]$Test, [switch]$All)

$port = 8000

$models = @(
    "Qwen3-Next-80B-A3B-Instruct-GGUF",
    "Qwen3-Coder-30B-A3B-Instruct-GGUF",
    "Gemma-3-4b-it-GGUF",
    "Whisper-Large-v3-Turbo"
)

if ($Stop -or $All) {
    Write-Host "Stopping Lemonade server..."
    lemonade-server stop
    Start-Sleep -Seconds 2
}

if ($Start -or $All) {
    Write-Host "Starting Lemonade with 4 models loaded (76GB VRAM, Flash Attention ON)..."
    mkdir -Force reports > $null
    
    $serverArgs = @("serve", "--port", $port, "--max-loaded-models", "4", "1", "1", "1", "--log-level", "info", "--llamacpp-args", '"--flash-attn on"')
    Start-Process -FilePath "lemonade-server" -ArgumentList $serverArgs -RedirectStandardOutput "reports/server.log" -WindowStyle Hidden
    
    Write-Host "Waiting 10 seconds for server to initialize..."
    Start-Sleep -Seconds 10
}

if ($Load -or $All) {
    Write-Host ""
    Write-Host "Loading all 4 Quality Config models on port $port..."
    Write-Host ""
    
    $success = 0
    $failed = 0
    
    $ctxSizes = @{
        "Qwen3-Next-80B-A3B-Instruct-GGUF" = 32768
        "Qwen3-Coder-30B-A3B-Instruct-GGUF" = 65536
        "Gemma-3-4b-it-GGUF" = 16384
        "Whisper-Large-v3-Turbo" = 0
    }
    
    foreach ($model in $models) {
        Write-Host "Loading $model..."
        $ctx = $ctxSizes[$model]
        
        try {
            # Load model using POST /api/v1/load endpoint
            $body = @{ model_name = $model; ctx_size = $ctx } | ConvertTo-Json
            $response = Invoke-RestMethod -Uri "http://localhost:$port/api/v1/load" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 900 -ErrorAction Stop
            Write-Host "  $($response.message)"
            $success++
        }
        catch {
            Write-Host "  Error: $($_.Exception.Message)"
            $failed++
        }
        
        Start-Sleep -Seconds 3
    }
    
    Write-Host ""
    Write-Host "Summary: $success loaded, $failed failed"
}

if ($Test) {
    Write-Host ""
    Write-Host "Testing API..."
    
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:$port/api/v1/models" -Method Get -TimeoutSec 5 -ErrorAction Stop
        Write-Host "Server online with $($response.data.Count) models"
        
        $loaded = $response.data | Where-Object { $_.loaded -eq $true }
        Write-Host "Loaded models: $($loaded.Count)"
        $loaded | ForEach-Object { Write-Host "  - $($_.id)" }
    }
    catch {
        Write-Host "Server offline"
    }
}
