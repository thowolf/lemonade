# Validate start-lemonade.ps1 parses with the PowerShell parser
# Exit 0 on success, non-zero on parse error

$scriptPath = Join-Path $PSScriptRoot "..\scripts\lemonade\start-lemonade.ps1"
if (-not (Test-Path $scriptPath)) {
    Write-Error "start-lemonade.ps1 not found at $scriptPath"
    exit 2
}

try {
    $tokens = $null; $errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile($scriptPath, [ref]$tokens, [ref]$errors) | Out-Null
    if ($errors -and $errors.Count -gt 0) {
        $errors | ForEach-Object {
            Write-Error "Line:$($_.Extent.StartLineNumber) Col:$($_.Extent.StartColumn) - $($_.Message)"
        }
        exit 1
    }
    Write-Host "OK: start-lemonade.ps1 parsed successfully" -ForegroundColor Green
    exit 0
} catch {
    Write-Error "Exception while parsing: $($_.Exception.Message)"
    exit 3
}