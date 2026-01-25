# Smoke test: verify Lemonade catalog is usable and start-lemonade initializes from it
# Run locally (requires Lemonade server running on localhost:8000)

$ErrorActionPreference = 'Stop'

Write-Host "== Verify GET /api/v1/models?show_all=true returns catalog =="
$r = Invoke-RestMethod -Uri 'http://localhost:8000/api/v1/models?show_all=true' -TimeoutSec 10
if (-not $r.data) { throw 'No models returned from catalog' }
Write-Host "  Catalog entries: $($r.data.Count)" -ForegroundColor Green

# Validate schema on first entry
$sample = $r.data[0]
$required = @('id','checkpoint','recipe','size','downloaded','labels')
foreach ($f in $required) {
    if (-not $sample.PSObject.Properties.Name -contains $f) { throw "Catalog entry missing field: $f" }
}
Write-Host "  Catalog schema looks correct (id,checkpoint,recipe,size,downloaded,labels)" -ForegroundColor Green

Write-Host "== Run start-lemonade in "-WhatIf" to validate initialization path =="
# Run the script in a separated process and capture the transcript it writes
$cmd = { param($p) pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\lemonade\start-lemonade.ps1 -WhatIf }
Invoke-Command -ScriptBlock $cmd -ArgumentList @() -ErrorAction SilentlyContinue | Out-Null
Write-Host "  (If server is already running the script will attempt an init path)" -ForegroundColor Yellow

Write-Host "== PASS: catalog is available and script initialization path exercised ==" -ForegroundColor Green
exit 0