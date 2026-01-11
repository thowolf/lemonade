#Requires -Version 5.1

<#
.SYNOPSIS
    Tests coder models for Continue VSCode extension compatibility on AMD Ryzen AI hardware

.DESCRIPTION
    This script automates testing of local coder models (Qwen, DeepSeek, Llama) with the Continue extension.
    It sends chat requests, monitors for freezes, collects diagnostic data, and generates compatibility reports.

.PARAMETER ModelId
    Specific model ID to test (optional, tests all if not specified)

.PARAMETER MaxInteractions
    Maximum number of chat interactions per model (default: 10)

.PARAMETER TimeoutSeconds
    Timeout for each interaction in seconds (default: 30)

.PARAMETER ConfigPath
    Path to configuration directory (default: .\config)

.PARAMETER ResultsPath
    Path to results directory (default: .\results)

.EXAMPLE
    .\Test-ContinueModels.ps1 -ModelId "qwen2.5-coder:7b"

.EXAMPLE
    .\Test-ContinueModels.ps1 -MaxInteractions 20 -TimeoutSeconds 60
#>

param(
    [string]$ModelId,
    [int]$MaxInteractions = 10,
    [int]$TimeoutSeconds = 30,
    [string]$ConfigPath = ".\config",
    [string]$ResultsPath = ".\results"
)

# Configuration
$ContinueApiUrl = "http://127.0.0.1:8000"
$ScriptRoot = $PSScriptRoot

# Ensure results directory exists
if (!(Test-Path $ResultsPath)) {
    New-Item -ItemType Directory -Path $ResultsPath -Force | Out-Null
}

# Logging function
function Write-TestLog {
    param(
        [string]$Message,
        [string]$Level = "INFO",
        [string]$Model = "",
        [string]$TestRunId = ""
    )

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level]"

    if ($Model) { $logMessage += " [$Model]" }
    if ($TestRunId) { $logMessage += " [$TestRunId]" }

    $logMessage += " $Message"

    Write-Host $logMessage

    # Also log to file
    $logFile = Join-Path $ResultsPath "test_run_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
    [System.IO.File]::AppendAllText($logFile, $logMessage + [System.Environment]::NewLine, (New-Object System.Text.UTF8Encoding $false))
}

# Load YAML configuration
function Get-YamlConfig {
    param([string]$Path)

    if (!(Test-Path $Path)) {
        throw "Configuration file not found: $Path"
    }

    # Simple YAML parser (basic implementation)
    $content = Get-Content $Path -Raw
    $config = @{}

    # Parse basic YAML structure
    $currentSection = $null
    foreach ($line in ($content -split "`n")) {
        $line = $line.Trim()
        if ($line -match "^(\w+):$") {
            $currentSection = $matches[1]
            $config[$currentSection] = @()
        }
        elseif ($line -match "^\s*-\s*name:\s*`"([^`"]+)`"" -and $currentSection) {
            $item = @{}
            $item.name = $matches[1]
            # Parse additional properties
            $lines = $content -split "`n"
            $index = $lines.IndexOf($line) + 1
            while ($index -lt $lines.Length -and $lines[$index] -match "^\s+(\w+):\s*(.+)$") {
                $key = $matches[1]
                $value = $matches[2].Trim('"')
                $item[$key] = $value
                $index++
            }
            $config[$currentSection] += $item
        }
    }

    return $config
}

# Check if Continue API is available
function Test-ContinueApi {
    try {
        $response = Invoke-WebRequest -Uri "$ContinueApiUrl/api/v1/models" -Method GET -TimeoutSec 5 -ErrorAction Stop -UseBasicParsing
        return $true
    }
    catch {
        Write-TestLog "Continue API not available: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

# Get system metrics
function Get-SystemMetrics {
    $cpu = Get-WmiObject Win32_Processor | Select-Object -First 1
    $memory = Get-WmiObject Win32_OperatingSystem
    $gpu = Get-WmiObject Win32_VideoController | Where-Object { $_.Name -like "*AMD*" -or $_.Name -like "*Radeon*" }

    return @{
        cpu_usage = $cpu.LoadPercentage
        memory_total_gb = [math]::Round($memory.TotalVisibleMemorySize / 1MB, 2)
        memory_used_gb = [math]::Round(($memory.TotalVisibleMemorySize - $memory.FreePhysicalMemory) / 1MB, 2)
        gpu_name = if ($gpu) { $gpu.Name } else { "Not detected" }
        timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    }
}

# Send chat request to Continue
function Send-ContinueChat {
    param(
        [string]$Message,
        [int]$TimeoutSeconds = 30,
        [string]$ModelId = $null
    )

    $payload = @{
        messages = @(
            @{
                role = "user"
                content = $Message
            }
        )
        stream = $false
    }

    if ($ModelId) {
        $payload.model = $ModelId
    }

    $body = $payload | ConvertTo-Json

    try {
        $response = Invoke-WebRequest -Uri "$ContinueApiUrl/api/v1/chat/completions" -Method POST -Body $body -ContentType "application/json" -TimeoutSec $TimeoutSeconds -ErrorAction Stop -UseBasicParsing

        # Parse JSON defensively
        try {
            $json = $response.Content | ConvertFrom-Json -ErrorAction Stop
        }
        catch {
            $json = $null
        }

        if ($null -eq $json) {
            return @{
                success = $false
                error = "Invalid JSON response: $($response.Content)"
                duration_ms = 0
            }
        }

        # Check for error field
        if ($json.error) {
            return @{
                success = $false
                error = ($json.error | ConvertTo-Json -Compress)
                duration_ms = 0
            }
        }

        # Extract content safely
        $choices = $json.choices
        if (-not $choices -or $choices.Count -eq 0) {
            return @{
                success = $false
                error = "No choices in response"
                duration_ms = 0
            }
        }

        $first = $choices[0]
        $message = $null
        if ($first.message) { $message = $first.message }
        elseif ($first.text) { $message = @{ content = $first.text } }
        else { $message = @{ content = '' } }

        $content = $message.content
        $tokens = 0
        if ($json.usage -and $json.usage.total_tokens) { $tokens = $json.usage.total_tokens }

        return @{
            success = $true
            response = $content
            tokens = $tokens
            duration_ms = 0
        }
    }
    catch {
        return @{
            success = $false
            error = $_.Exception.Message
            duration_ms = 0
        }
    }
}

# Main test function
function Test-Model {
    param(
        [hashtable]$Model,
        [array]$Scenarios,
        [int]$MaxInteractions,
        [int]$TimeoutSeconds
    )

    $testRunId = "$($Model.id)_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Write-TestLog "Starting test run for model: $($Model.name)" "INFO" $Model.id $testRunId

    $results = @{
        model = $Model
        test_run_id = $testRunId
        start_time = Get-Date
        interactions = @()
        freeze_detected = $false
        freeze_at_interaction = 0
        system_metrics = @()
        end_time = $null
        status = "running"
    }

    # Check API availability
    if (!(Test-ContinueApi)) {
        Write-TestLog "Continue API not available, cannot test model" "ERROR" $Model.id $testRunId
        $results.status = "failed"
        $results.error = "Continue API not available"
        return $results
    }

    # Run test interactions
    for ($i = 1; $i -le $MaxInteractions; $i++) {
        Write-TestLog "Starting interaction $i/$MaxInteractions" "INFO" $Model.id $testRunId

        # Collect system metrics before interaction
        $metrics = Get-SystemMetrics
        $results.system_metrics += $metrics

        # Select test scenario
        $scenario = $Scenarios[($i - 1) % $Scenarios.Count]

        # Send chat request
        $startTime = Get-Date
        $chatResult = Send-ContinueChat -Message $scenario.prompt -TimeoutSeconds $TimeoutSeconds -ModelId $model.id
        $endTime = Get-Date
        $duration = ($endTime - $startTime).TotalMilliseconds

        $interaction = @{
            interaction_number = $i
            scenario = $scenario.name
            prompt = $scenario.prompt
            start_time = $startTime
            end_time = $endTime
            duration_ms = $duration
            success = $chatResult.success
            response = if ($chatResult.success) { $chatResult.response } else { $null }
            error = if (!$chatResult.success) { $chatResult.error } else { $null }
            tokens = if ($chatResult.success) { $chatResult.tokens } else { 0 }
        }

        $results.interactions += $interaction

        if ($chatResult.success) {
            Write-TestLog "Interaction $i completed successfully in $($duration)ms" "INFO" $Model.id $testRunId
        }
        else {
            Write-TestLog "Interaction $i failed: $($chatResult.error)" "ERROR" $Model.id $testRunId

            # Check if this is a freeze (timeout)
            if ($chatResult.error -like "*timeout*" -or $chatResult.error -like "*timed out*") {
                $results.freeze_detected = $true
                $results.freeze_at_interaction = $i
                Write-TestLog "Freeze detected at interaction $i" "ERROR" $Model.id $testRunId
                break
            }
        }

        # Small delay between interactions
        Start-Sleep -Seconds 1
    }

    $results.end_time = Get-Date
    $results.status = if ($results.freeze_detected) { "freeze_detected" } else { "completed" }

    Write-TestLog "Test run completed. Status: $($results.status)" "INFO" $Model.id $testRunId

    return $results
}

# Generate compatibility report
function New-CompatibilityReport {
    param([array]$TestResults)

    $report = @{
        generated_at = Get-Date
        summary = @{
            total_models_tested = $TestResults.Count
            compatible_models = ($TestResults | Where-Object { !$_.freeze_detected }).Count
            incompatible_models = ($TestResults | Where-Object { $_.freeze_detected }).Count
        }
        models = @()
    }

    foreach ($result in $TestResults) {
        $modelReport = @{
            name = $result.model.name
            id = $result.model.id
            compatible = !$result.freeze_detected
            max_stable_interactions = if ($result.freeze_detected) { $result.freeze_at_interaction - 1 } else { $result.interactions.Count }
            total_interactions_attempted = $result.interactions.Count
            freeze_detected = $result.freeze_detected
            freeze_at = $result.freeze_at_interaction
            average_response_time_ms = ($result.interactions | Where-Object { $_.success } | Measure-Object -Property duration_ms -Average).Average
            success_rate = ($result.interactions | Where-Object { $_.success }).Count / $result.interactions.Count
        }
        $report.models += $modelReport
    }

    return $report
}

# Main execution
try {
    Write-TestLog "Starting Continue Extension Model Testing Framework"

    # Load configurations
    $modelsConfig = Get-YamlConfig -Path (Join-Path $ConfigPath "models.yaml")
    $scenariosConfig = Get-YamlConfig -Path (Join-Path $ConfigPath "test_scenarios.yaml")

    $models = $modelsConfig.models
    $scenarios = $scenariosConfig.scenarios

    if ($ModelId) {
        $found = $models | Where-Object { $_.id -eq $ModelId }
        if ($found) {
            $models = $found
        }
        else {
            # If the model isn't present in the static config, still allow testing a server-loaded model id
            Write-TestLog "Model '$ModelId' not found in configuration; will test using server model id." "WARN"
            $models = @(@{ name = $ModelId; id = $ModelId })
        }
    }

    Write-TestLog "Loaded $($models.Count) models and $($scenarios.Count) test scenarios"

    # Run tests for each model
    $allResults = @()

    foreach ($model in $models) {
        $result = Test-Model -Model $model -Scenarios $scenarios -MaxInteractions $MaxInteractions -TimeoutSeconds $TimeoutSeconds
        $allResults += $result

        # Save individual result
        $resultFile = Join-Path $ResultsPath "result_$($model.id -replace '[^a-zA-Z0-9]', '_')_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
        [System.IO.File]::WriteAllText($resultFile, ($result | ConvertTo-Json -Depth 10), (New-Object System.Text.UTF8Encoding $false))
        Write-TestLog "Saved result to: $resultFile" "INFO" $model.id
    }

    # Generate compatibility report
    $report = New-CompatibilityReport -TestResults $allResults
    $reportFile = Join-Path $ResultsPath "compatibility_report_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
    [System.IO.File]::WriteAllText($reportFile, ($report | ConvertTo-Json -Depth 10), (New-Object System.Text.UTF8Encoding $false))

    Write-TestLog "Compatibility report saved to: $reportFile"

    # Display summary
    Write-TestLog "Testing completed. Summary:" "INFO"
    Write-TestLog "Total models tested: $($report.summary.total_models_tested)" "INFO"
    Write-TestLog "Compatible models: $($report.summary.compatible_models)" "INFO"
    Write-TestLog "Incompatible models: $($report.summary.incompatible_models)" "INFO"

    foreach ($model in $report.models) {
        $status = if ($model.compatible) { "COMPATIBLE" } else { "INCOMPATIBLE" }
        Write-TestLog "$($model.name): $status (max stable: $($model.max_stable_interactions) interactions)" "INFO"
    }

}
catch {
    Write-TestLog "Fatal error: $($_.Exception.Message)" "ERROR"
    Write-TestLog "Stack trace: $($_.ScriptStackTrace)" "ERROR"
    exit 1
}

Write-TestLog "Continue Extension Model Testing Framework completed"