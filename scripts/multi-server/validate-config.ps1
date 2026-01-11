<#
.SYNOPSIS
    Validate configuration file and check port availability.

.DESCRIPTION
    This script validates the JSON configuration file structure and checks
    if the specified ports are available before attempting to start servers.

.PARAMETER ConfigFile
    Path to the JSON configuration file to validate.

.PARAMETER SkipPortCheck
    Skip port availability checks (only validate JSON structure).

.EXAMPLE
    .\validate-config.ps1
    .\validate-config.ps1 -ConfigFile config\my-config.json
    .\validate-config.ps1 -SkipPortCheck

.NOTES
    Author: Lemonade Server Team
    Version: 1.0.0
#>

[CmdletBinding()]
param(
    [Parameter(Position=0)]
    [string]$ConfigFile = 'config\example-config.json',
    
    [Parameter()]
    [switch]$SkipPortCheck
)

$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = 'Reset'
    )
    switch ($Color) {
        'Green' { Write-Host $Message -ForegroundColor Green }
        'Red'   { Write-Host $Message -ForegroundColor Red }
        'Yellow'{ Write-Host $Message -ForegroundColor Yellow }
        'Blue'  { Write-Host $Message -ForegroundColor Cyan }
        default { Write-Host $Message }
    }
}

function Test-PortAvailable {
    param([int]$Port)
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $Port)
        $listener.Start()
        $listener.Stop()
        return $true
    } catch {
        return $false
    }
}

Write-ColorOutput '=== Configuration Validator ===' 'Blue'

# Resolve config file path
$ConfigPath = Join-Path $ScriptDir $ConfigFile
Write-ColorOutput "Validating: $ConfigPath" 'Blue'

if (-not (Test-Path $ConfigPath)) {
    Write-ColorOutput "Configuration file not found: $ConfigPath" 'Red'
    exit 1
}

try {
    $config = Get-Content $ConfigPath -Raw | ConvertFrom-Json
} catch {
    Write-ColorOutput "Invalid JSON format: $($_.Exception.Message)" 'Red'
    exit 1
}

if (-not $config.servers -or $config.servers.Count -eq 0) {
    Write-ColorOutput "No servers defined in 'servers' array" 'Red'
    exit 1
}

Write-ColorOutput "Configuration loaded. $($config.servers.Count) server(s) found." 'Blue'

$errors = @()
$warnings = @()
$portsSeen = @{}
$namesSeen = @{}

for ($i = 0; $i -lt $config.servers.Count; $i++) {
    $server = $config.servers[$i]
    $serverNum = $i + 1
    Write-ColorOutput "Server $($serverNum):" 'Blue'

    if (-not $server.name) {
        $errors += "Server $($serverNum): Missing required field 'name'"
        continue
    }
    if ($namesSeen.ContainsKey($server.name)) {
        $errors += "Server $($serverNum): Duplicate server name '$($server.name)'"
    } else {
        $namesSeen[$server.name] = $serverNum
    }

    if (-not $server.port) {
        $errors += "Server $($serverNum): Missing required field 'port'"
        continue
    }
    if ($portsSeen.ContainsKey($server.port)) {
        $errors += "Server $($serverNum): Duplicate port $($server.port)"
    } else {
        $portsSeen[$server.port] = $serverNum
    }

    if ($server.port -lt 1024 -or $server.port -gt 65535) {
        $errors += "Server $($serverNum): Port $($server.port) out of valid range (1024-65535)"
    }

    if (-not $SkipPortCheck) {
        if (Test-PortAvailable -Port $server.port) {
            Write-ColorOutput "  Port $($server.port): [OK] Available" 'Green'
        } else {
            Write-ColorOutput "  Port $($server.port): [WARN] In use" 'Yellow'
            $warnings += "Server $($serverNum): Port $($server.port) is currently in use"
        }
    }

    if (-not $server.model) {
        $errors += "Server $($serverNum): Missing required field 'model'"
    }

    if ($server.llamacpp_backend -and $server.llamacpp_backend -notin @('vulkan','rocm','cpu')) {
        $warnings += "Server $($serverNum): Unknown llamacpp_backend '$($server.llamacpp_backend)'"
    }
    if ($server.log_level -and $server.log_level -notin @('debug','info','warning','error')) {
        $warnings += "Server $($serverNum): Unknown log_level '$($server.log_level)'"
    }
    if ($server.ctx_size) {
        if ($server.ctx_size -lt 512) { $warnings += "Server $($serverNum): ctx_size $($server.ctx_size) is very small" }
        if ($server.ctx_size -gt 32768) { $warnings += "Server $($serverNum): ctx_size $($server.ctx_size) is very large" }
    }
}

Write-ColorOutput ''
if ($errors.Count -gt 0) {
    Write-ColorOutput "[ERROR] Found $($errors.Count) error(s):" 'Red'
    foreach ($e in $errors) { Write-ColorOutput "  - $e" 'Red' }
    Write-ColorOutput ''
    Write-ColorOutput 'Fix errors before starting servers.' 'Red'
    exit 1
}

if ($warnings.Count -gt 0) {
    Write-ColorOutput "[WARN] Found $($warnings.Count) warning(s):" 'Yellow'
    foreach ($w in $warnings) { Write-ColorOutput "  - $w" 'Yellow' }
    Write-ColorOutput ''
    Write-ColorOutput 'Configuration has warnings but is valid. Proceed with caution.' 'Yellow'
    exit 0
}

Write-ColorOutput '[OK] Configuration is valid!' 'Green'
exit 0
