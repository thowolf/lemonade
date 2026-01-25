# Smoke: pull, load and poll until selected models are loaded (for local dev)
# Usage: pwsh -NoProfile -File tests\smoke_load_models_locally.ps1

$ErrorActionPreference = 'Stop'
$Server = 'http://localhost:8000'
$modelsToPull = @('GLM-4.7-Flash-GGUF','Phi-4-mini-instruct-GGUF','Gemma-3-4b-it-GGUF')
$aliasesToLoad = @('phi-4','glm-4.7','gemma-3-4b')

Write-Host "Running parser check..."
& pwsh -NoProfile -File tests\verify_start_lemonade_syntax.ps1

foreach ($m in $modelsToPull) {
    Write-Host "\n--- Pulling: $m ---"
    try {
        Invoke-RestMethod -Uri "$Server/api/v1/pull" -Method Post -ContentType 'application/json' -Body (@{ model_name=$m } | ConvertTo-Json) -TimeoutSec 120 -ErrorAction Stop
        Write-Host "pulled: $m" -ForegroundColor Green
    } catch {
        Write-Warning ("pull failed for {0}: {1}" -f $m, $_.Exception.Message)
    }
}

Write-Host "\nRequesting loads..."
foreach ($a in $aliasesToLoad) {
    Write-Host "Loading alias: $a"
    try {
        Invoke-RestMethod -Uri "$Server/api/v1/load" -Method Post -ContentType 'application/json' -Body (@{ model_name=$a } | ConvertTo-Json) -TimeoutSec 120 -ErrorAction Stop
        Write-Host "load request accepted: $a" -ForegroundColor Green
    } catch {
        Write-Warning ("load request failed for {0}: {1}" -f $a, $_.Exception.Message)
    }
}

Write-Host "\nPolling /api/v1/health for model load status (5m timeout)"
$deadline = (Get-Date).AddMinutes(5)
$loaded = @()
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 5
    try { $h = Invoke-RestMethod -Uri "$Server/api/v1/health" -TimeoutSec 5 -ErrorAction Stop } catch { $h = $null }
    if ($h -and $h.all_models_loaded) { $loaded = $h.all_models_loaded | ForEach-Object { $_.model_name } }
    Write-Host "Loaded models: $($loaded -join ', ')"
    if (($loaded -contains 'Phi-4-mini-instruct-GGUF') -and ($loaded -contains 'Gemma-3-4b-it-GGUF')) {
        Write-Host "\nSUCCESS: requested models are loaded" -ForegroundColor Green
        exit 0
    }
}

Write-Host "\nFAILED: models did not reach loaded state within timeout — dumping last 400 lines of logs" -ForegroundColor Red
Get-Content logs\lemonade-server.log -Tail 400 -ErrorAction SilentlyContinue
exit 2
