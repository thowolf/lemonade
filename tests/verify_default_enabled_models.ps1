# Verify that $DefaultEnabledModels (structured) sets enabled + ctx_size on $ModelsToLoad
# This test mocks the catalog API and runs start-lemonade in library mode (no external services).
$env:LEMONADE_LIB = '1'

# Provide structured defaults for the test
$DefaultEnabledModels = @(
    @{ id = 'Gemma-3-4b-it-GGUF'; ctx_size = 16384; llamacpp_backend = 'vulkan' },
    @{ id = 'Qwen3-Coder-30B-A3B-Instruct-GGUF'; ctx_size = 16384; llamacpp_backend = 'vulkan' }
)

# Mock a minimal catalog response so dot-sourcing doesn't call the real server
$mockCatalog = @{ data = @(
    @{ id = 'Gemma-3-4b-it-GGUF'; recipe_options = @{ ctx_size = 0 }; recipe = 'llamacpp'; size = 3.61; downloaded = $true; labels = @('hot') ; checkpoint = 'ggml-org/gemma-3-4b-it-GGUF:Q4_K_M' },
    @{ id = 'Qwen3-Coder-30B-A3B-Instruct-GGUF'; recipe_options = @{ ctx_size = 0 }; recipe = 'llamacpp'; size = 18.6; downloaded = $true; labels = @('hot'); checkpoint = 'unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF:Qwen3-Coder-30B-A3B-Instruct-Q4_K_M.gguf' }
) }

# Backup any existing function and create a temporary mock for Invoke-RestMethod
$origInvoke = Get-Command Invoke-RestMethod -ErrorAction SilentlyContinue
function Invoke-RestMethod { param(
    [string]$Uri
) ; if ($Uri -match '/api/v1/models') { return $mockCatalog } ; return @{ data = @() } }

# Dot-source the script (runs in current scope when LEMONADE_LIB is set)
. "$PSScriptRoot/../scripts/lemonade/start-lemonade.ps1"

# Restore original cmdlet if it existed
if ($origInvoke) { Remove-Item Function:Invoke-RestMethod -ErrorAction SilentlyContinue }

# Assertions (deterministic)
$gem = $ModelsToLoad | Where-Object { $_.name -eq 'Gemma-3-4b-it-GGUF' }
$qwen = $ModelsToLoad | Where-Object { $_.name -eq 'Qwen3-Coder-30B-A3B-Instruct-GGUF' }

if (-not $gem -or -not $qwen) {
    Write-Host 'FAIL: expected models present in $ModelsToLoad' -ForegroundColor Red
    exit 1
}
if (-not $gem.enabled -or $gem.context -ne 16384) {
    Write-Host "FAIL: Gemma enabled=$($gem.enabled) context=$($gem.context)" -ForegroundColor Red
    exit 2
}
if (-not $qwen.enabled -or $qwen.context -ne 16384) {
    Write-Host "FAIL: Qwen enabled=$($qwen.enabled) context=$($qwen.context)" -ForegroundColor Red
    exit 3
}
Write-Host 'PASS' -ForegroundColor Green
exit 0
