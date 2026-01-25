<#
.SYNOPSIS
    Fixes missing Prisma runtime for the LiteLLM Windows service, restarts the service,
    and tails migration/DB log lines for verification.

.DESCRIPTION
    - Detects which Python executable the LiteLLM service will use (via NSSM or installed
      `litellm.exe` location).
    - Installs `prisma` into that Python environment (pip install prisma).
    - Optionally clears `DATABASE_URL` in the service environment if `prisma` cannot be
      installed and `-AllowFallback` is supplied.
    - Restarts the NSSM-managed service `LiteLLM-Proxy` and streams log lines that match
      migration/DB success patterns.

.PARAMETER AllowFallback
    If set, the script will clear the service `DATABASE_URL` (NSSM AppEnvironmentExtra)
    when `prisma` cannot be installed so the service can start without DB features.

.PARAMETER TailLines
    Number of log lines to tail when streaming verification output. Default: 200

.EXAMPLE
    # dry-run: show detected Python and what would be done
    .\fix-prisma-and-restart.ps1 -WhatIf

    # install prisma, restart service and tail logs
    .\fix-prisma-and-restart.ps1

    # allow fallback (clear DATABASE_URL) if prisma install/verification fails
    .\fix-prisma-and-restart.ps1 -AllowFallback
#>
[CmdletBinding(SupportsShouldProcess=$true)]
param(
    [switch]$AllowFallback,
    [int]$TailLines = 200
)

function Write-Note($m) { Write-Host "[INFO]    $m" -ForegroundColor Cyan }
function Write-Warn($m) { Write-Host "[WARN]    $m" -ForegroundColor Yellow }
function Write-Err($m)  { Write-Host "[ERROR]   $m" -ForegroundColor Red }
function Write-OK($m)   { Write-Host "[SUCCESS] $m" -ForegroundColor Green }

if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Err 'This script must be run as Administrator. Open PowerShell "Run as administrator" and retry.'
    exit 2
}

$serviceName = 'LiteLLM-Proxy'
$logPath = Join-Path $PSScriptRoot 'logs\litellm-service.log'

function Get-NssmValue($name, $key) {
    try {
        $out = & nssm get $name $key 2>$null
        if ($LASTEXITCODE -eq 0) { return $out.Trim() }
    } catch {}
    return $null
}

function Get-ServicePython() {
    # 1) Prefer NSSM Application (if available)
    $app = Get-NssmValue -name $serviceName -key Application
    $appDir = Get-NssmValue -name $serviceName -key AppDirectory

    if ($app) {
        # If the NSSM Application is a Python-based wrapper or litellm.exe, try to infer python
        if ($app -match '\\Scripts\\litellm\.exe$') {
            $litellmExe = $app
            $pythonCandidate = (Split-Path $litellmExe -Parent) -Replace '\\Scripts$', '\\python.exe'
            if (Test-Path $pythonCandidate) { return (Resolve-Path $pythonCandidate).Path }
        }

        if ($app -match '\.bat$' -and (Test-Path $app)) {
            # inspect wrapper for an explicit python path
            $txt = Get-Content $app -Raw -ErrorAction SilentlyContinue
            # capture a Windows-style python.exe path (e.g. C:\Users\...\python.exe)
            if ($txt -match '([A-Za-z]:\\\S+python\.exe)') { return $matches[1] }
        }

        # fallback: if AppDirectory looks like a conda prefix, use its python
        if ($appDir -and (Test-Path (Join-Path $appDir 'python.exe'))) {
            return (Join-Path $appDir 'python.exe')
        }
    }

    # 2) Fallback: try to resolve installed `litellm.exe` and infer python from its parent folder
    try {
        $cmd = Get-Command litellm.exe -ErrorAction SilentlyContinue
        if ($cmd) {
            $litPath = $cmd.Source
            if ($litPath -match '\\Scripts\\litellm\.exe$') {
                $py = (Split-Path $litPath -Parent) -Replace '\\Scripts$', '\\python.exe'
                if (Test-Path $py) { return (Resolve-Path $py).Path }
            }
        }
    } catch {}

    # 3) Last resort: common Miniconda path used on this machine
    $default = 'C:\\Users\\tomwo\\miniconda3\\python.exe'
    if (Test-Path $default) { Write-Warn "Could not auto-detect exact service Python; falling back to $default"; return $default }

    Write-Err 'Unable to determine the Python executable used by the service. Use -WhatIf to inspect or set up prisma manually.'
    return $null
}

function Install-And-Verify-Prisma($pythonExe) {
    if (-not (Test-Path $pythonExe)) { Write-Err "python not found at $pythonExe"; return $false }

    Write-Note "Installing prisma into: $pythonExe"
    if ($PSCmdlet.ShouldProcess("pip install prisma in $pythonExe")) {
        & $pythonExe -m pip install prisma --disable-pip-version-check | ForEach-Object { Write-Note $_ }
    }

    Write-Note 'Verifying prisma import...'
    try {
        $ver = & $pythonExe -c "import prisma; print(prisma.__version__)" 2>&1
        if ($LASTEXITCODE -eq 0) { Write-OK "prisma ok: $ver"; return $true }
        Write-Warn "prisma import returned: $ver"
    } catch {
        Write-Warn "prisma import failed: $_"
    }
    return $false
}

# === main ===
$python = Get-ServicePython
if (-not $python) { exit 3 }
Write-Note "Detected service Python: $python"

if (-not $PSCmdlet.ShouldProcess('install-prisma','will attempt to install and verify prisma')) { Write-Note 'WhatIf only -- no changes made.'; exit 0 }

$ok = Install-And-Verify-Prisma -pythonExe $python

if (-not $ok) {
    Write-Warn "prisma installation/verification failed.";
    if ($AllowFallback) {
        Write-Warn 'AllowFallback set — clearing DATABASE_URL in NSSM so service can start without DB.'
        & nssm set $serviceName AppEnvironmentExtra "DATABASE_URL=" 2>$null
    } else {
        Write-Err 'Run again with -AllowFallback to clear DATABASE_URL and allow the service to start without DB, or install prisma manually into the service Python.'
        exit 4
    }
}

Write-Note 'Restarting service via NSSM...'
& nssm restart $serviceName 2>&1 | ForEach-Object { Write-Note $_ }
Start-Sleep -Seconds 2

if (-not (Test-Path $logPath)) { Write-Warn "Log file not found: $logPath"; exit 0 }

Write-Note ("Tailing log (" + $TailLines + ") lines. Press Ctrl+C to stop.")
Get-Content $logPath -Tail $TailLines -Wait | Select-String -Pattern 'alembic|Running upgrade|prisma|Connected to DB|Unable to connect to DB' | ForEach-Object { Write-Host $_ }
