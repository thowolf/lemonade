# Data Model: AMD AI Max+ 395 ROCm Testing

**Feature**: 001-max-395-rocm-test  
**Date**: 2025-12-23  
**Purpose**: Define data structures for test configurations, results, and performance metrics

## Overview

This document defines the data model for test execution, result storage, and performance analysis. All data structures use JSON for serialization, enabling easy integration with pytest, result archiving, and visualization tools.

## Core Entities

### 1. TestConfiguration

Represents the setup and parameters for a single test execution.

**Attributes**:
- `test_id` (string): Unique identifier (e.g., "P1-basic-7b-001")
- `test_name` (string): Human-readable name (e.g., "Basic Inference - Llama 3.2 7B")
- `user_story` (string): Priority level (e.g., "P1", "P2", "P3", "P4")
- `model_config` (ModelConfiguration): Model details
- `execution_config` (ExecutionConfiguration): Backend and runtime settings
- `test_prompts` (list[string]): Prompts to execute
- `expected_metrics` (ExpectedMetrics): Performance targets
- `timestamp` (ISO 8601 string): Test start time
- `environment` (EnvironmentInfo): System details

**Example**:
```json
{
  "test_id": "P1-basic-7b-001",
  "test_name": "Basic Inference - Llama 3.2 7B ROCm",
  "user_story": "P1",
  "model_config": { /* ModelConfiguration */ },
  "execution_config": { /* ExecutionConfiguration */ },
  "test_prompts": ["What is the capital of France?", "Explain quantum computing."],
  "expected_metrics": { /* ExpectedMetrics */ },
  "timestamp": "2025-12-23T14:30:00Z",
  "environment": { /* EnvironmentInfo */ }
}
```

### 2. ModelConfiguration

Describes the LLM model under test.

**Attributes**:
- `model_name` (string): Model identifier (e.g., "Llama-3.2-7B-Instruct-GGUF")
- `model_size` (string): Parameter count (e.g., "7B", "13B", "30B")
- `quantization` (string): Quantization level (e.g., "Q4_K_M", "Q8_0", "F16")
- `context_length` (integer): Maximum context window (e.g., 8192, 16384)
- `model_path` (string): Local filesystem path to model file
- `model_source` (string): Origin (e.g., "HuggingFace", "local")

**Example**:
```json
{
  "model_name": "Llama-3.2-7B-Instruct-GGUF",
  "model_size": "7B",
  "quantization": "Q4_K_M",
  "context_length": 8192,
  "model_path": "C:\\Users\\user\\.lemonade\\models\\llama-3.2-7b-instruct-q4.gguf",
  "model_source": "HuggingFace"
}
```

### 3. ExecutionConfiguration

Specifies runtime settings for test execution.

**Attributes**:
- `backend` (string): Inference backend (e.g., "rocm", "vulkan", "cpu")
- `temperature` (float): Sampling temperature (default: 0.7)
- `max_tokens` (integer): Maximum generated tokens (default: 512)
- `top_p` (float): Nucleus sampling parameter (default: 0.9)
- `streaming` (boolean): Enable streaming mode (default: false)
- `batch_size` (integer): Number of concurrent requests (default: 1)
- `num_iterations` (integer): Repeat count for averaging (default: 5)
- `api_base_url` (string): Lemonade Server endpoint (default: "http://localhost:8000/api/v1")

**Example**:
```json
{
  "backend": "rocm",
  "temperature": 0.7,
  "max_tokens": 512,
  "top_p": 0.9,
  "streaming": true,
  "batch_size": 1,
  "num_iterations": 5,
  "api_base_url": "http://localhost:8000/api/v1"
}
```

### 4. EnvironmentInfo

Captures system and hardware details for result reproducibility.

**Attributes**:
- `os` (string): Operating system (e.g., "Windows 11")
- `os_version` (string): OS build (e.g., "22H2")
- `gpu_model` (string): GPU identifier (e.g., "AMD AI Max+ 395")
- `gpu_architecture` (string): Architecture code (e.g., "gfx1151")
- `vram_total_gb` (integer): Total VRAM in GB (e.g., 128)
- `rocm_version` (string): ROCm driver version (e.g., "7.1.1")
- `lemonade_version` (string): Lemonade Server version (e.g., "9.1.1")
- `python_version` (string): Python runtime (e.g., "3.11.5")
- `cpu_model` (string): CPU identifier (optional)
- `ram_total_gb` (integer): System RAM in GB (optional)

**Example**:
```json
{
  "os": "Windows 11",
  "os_version": "22H2",
  "gpu_model": "AMD AI Max+ 395",
  "gpu_architecture": "gfx1151",
  "vram_total_gb": 128,
  "rocm_version": "7.1.1",
  "lemonade_version": "9.1.1",
  "python_version": "3.11.5",
  "cpu_model": "AMD Ryzen 9 7945HX",
  "ram_total_gb": 64
}
```

### 5. ExpectedMetrics

Defines performance targets from success criteria (SC-001 through SC-010).

**Attributes**:
- `min_tokens_per_second` (float): Minimum throughput (e.g., 20.0 for 7B, 5.0 for 30B+)
- `max_time_to_first_token_ms` (integer): Maximum latency (e.g., 2000 ms)
- `min_vram_utilization_percent` (float): Minimum VRAM usage for large models (e.g., 80.0)
- `min_uptime_percent` (float): Minimum stability (e.g., 95.0)
- `min_response_accuracy_percent` (float): Minimum correctness (e.g., 90.0)

**Example**:
```json
{
  "min_tokens_per_second": 20.0,
  "max_time_to_first_token_ms": 2000,
  "min_vram_utilization_percent": 80.0,
  "min_uptime_percent": 95.0,
  "min_response_accuracy_percent": 90.0
}
```

## Result Entities

### 6. TestResult

Captures outcomes from a single test execution.

**Attributes**:
- `test_id` (string): Links to TestConfiguration
- `status` (string): "passed", "failed", "error", "skipped"
- `start_time` (ISO 8601 string): Test start timestamp
- `end_time` (ISO 8601 string): Test end timestamp
- `duration_seconds` (float): Total execution time
- `performance_metrics` (PerformanceMetrics): Measured performance
- `responses` (list[ResponseRecord]): Generated outputs
- `errors` (list[ErrorRecord]): Any errors encountered (empty if passed)
- `validation_results` (ValidationResults): Success criteria checks

**Example**:
```json
{
  "test_id": "P1-basic-7b-001",
  "status": "passed",
  "start_time": "2025-12-23T14:30:00Z",
  "end_time": "2025-12-23T14:35:30Z",
  "duration_seconds": 330.5,
  "performance_metrics": { /* PerformanceMetrics */ },
  "responses": [ /* list of ResponseRecord */ ],
  "errors": [],
  "validation_results": { /* ValidationResults */ }
}
```

### 7. PerformanceMetrics

Measured performance data for analysis.

**Attributes**:
- `tokens_per_second` (object): {"mean": float, "min": float, "max": float, "std_dev": float}
- `time_to_first_token_ms` (object): {"p50": float, "p95": float, "p99": float}
- `total_latency_ms` (object): {"p50": float, "p95": float, "p99": float}
- `vram_usage_gb` (object): {"peak": float, "average": float, "min": float}
- `vram_utilization_percent` (float): Peak VRAM / Total VRAM * 100
- `gpu_temperature_celsius` (object): {"peak": float, "average": float} (optional)
- `throughput_tokens_total` (integer): Total tokens generated across all prompts
- `error_rate_percent` (float): Percentage of failed requests (0.0 if all succeeded)

**Example**:
```json
{
  "tokens_per_second": {"mean": 22.5, "min": 18.3, "max": 25.1, "std_dev": 1.8},
  "time_to_first_token_ms": {"p50": 1200, "p95": 1850, "p99": 2050},
  "total_latency_ms": {"p50": 15000, "p95": 18000, "p99": 20000},
  "vram_usage_gb": {"peak": 12.5, "average": 11.8, "min": 10.2},
  "vram_utilization_percent": 9.8,
  "gpu_temperature_celsius": {"peak": 72, "average": 68},
  "throughput_tokens_total": 5120,
  "error_rate_percent": 0.0
}
```

### 8. ResponseRecord

Details of a single LLM response.

**Attributes**:
- `prompt_index` (integer): Index in test_prompts list
- `prompt_text` (string): Input prompt
- `response_text` (string): Generated output
- `tokens_generated` (integer): Output token count
- `duration_ms` (float): Generation time
- `time_to_first_token_ms` (float): Streaming latency (null if non-streaming)
- `tokens_per_second` (float): Calculated throughput
- `model_used` (string): Model name (for multi-model tests)

**Example**:
```json
{
  "prompt_index": 0,
  "prompt_text": "What is the capital of France?",
  "response_text": "The capital of France is Paris. It is located in the north-central part...",
  "tokens_generated": 45,
  "duration_ms": 2000,
  "time_to_first_token_ms": 1200,
  "tokens_per_second": 22.5,
  "model_used": "Llama-3.2-7B-Instruct-GGUF"
}
```

### 9. ErrorRecord

Captures error details for debugging.

**Attributes**:
- `error_type` (string): Error category (e.g., "api_error", "timeout", "vram_exhaustion")
- `error_message` (string): Error description
- `timestamp` (ISO 8601 string): When error occurred
- `prompt_index` (integer): Which prompt failed (null if setup error)
- `stack_trace` (string): Full traceback (optional, for debugging)

**Example**:
```json
{
  "error_type": "vram_exhaustion",
  "error_message": "Failed to load model: Insufficient VRAM (required: 140GB, available: 128GB)",
  "timestamp": "2025-12-23T14:32:15Z",
  "prompt_index": null,
  "stack_trace": "Traceback (most recent call last):\\n  File..."
}
```

### 10. ValidationResults

Success criteria evaluation results.

**Attributes**:
- `criteria_checks` (list[CriteriaCheck]): Individual SC checks
- `overall_pass` (boolean): True if all checks passed
- `pass_count` (integer): Number of passed checks
- `fail_count` (integer): Number of failed checks
- `total_checks` (integer): Total criteria evaluated

**CriteriaCheck Attributes**:
- `criteria_id` (string): Success criteria identifier (e.g., "SC-002")
- `description` (string): What was checked
- `expected` (string): Expected value
- `actual` (string): Measured value
- `passed` (boolean): True if criteria met

**Example**:
```json
{
  "criteria_checks": [
    {
      "criteria_id": "SC-002",
      "description": "Tokens per second >= 20.0 for 7B model",
      "expected": ">=20.0",
      "actual": "22.5",
      "passed": true
    },
    {
      "criteria_id": "SC-007",
      "description": "Time to first token <= 2000ms",
      "expected": "<=2000",
      "actual": "1200",
      "passed": true
    }
  ],
  "overall_pass": true,
  "pass_count": 2,
  "fail_count": 0,
  "total_checks": 2
}
```

## Aggregate Entities

### 11. BenchmarkSummary

Aggregates multiple test results for comparison and reporting.

**Attributes**:
- `summary_id` (string): Unique identifier
- `summary_name` (string): Description (e.g., "ROCm vs Vulkan Comparison - 7B Models")
- `test_ids` (list[string]): Included test IDs
- `timestamp` (ISO 8601 string): Summary generation time
- `aggregate_metrics` (AggregateMetrics): Cross-test statistics
- `comparison_table` (list[ComparisonRow]): Side-by-side results

**Example**:
```json
{
  "summary_id": "benchmark-001",
  "summary_name": "ROCm vs Vulkan Comparison - Llama 3.2 7B",
  "test_ids": ["P1-basic-7b-001", "P1-basic-7b-002"],
  "timestamp": "2025-12-23T15:00:00Z",
  "aggregate_metrics": { /* AggregateMetrics */ },
  "comparison_table": [ /* list of ComparisonRow */ ]
}
```

### 12. AggregateMetrics

Statistical summaries across multiple tests.

**Attributes**:
- `tests_count` (integer): Number of tests included
- `avg_tokens_per_second` (float): Mean throughput
- `avg_time_to_first_token_ms` (float): Mean latency
- `avg_vram_utilization_percent` (float): Mean VRAM usage
- `pass_rate_percent` (float): Percentage of passing tests
- `fastest_backend` (string): Best performing backend (e.g., "rocm")
- `slowest_backend` (string): Worst performing backend

**Example**:
```json
{
  "tests_count": 10,
  "avg_tokens_per_second": 21.8,
  "avg_time_to_first_token_ms": 1350,
  "avg_vram_utilization_percent": 11.2,
  "pass_rate_percent": 100.0,
  "fastest_backend": "rocm",
  "slowest_backend": "cpu"
}
```

### 13. ComparisonRow

Side-by-side comparison entry for benchmark summary table.

**Attributes**:
- `test_name` (string): Test identifier
- `backend` (string): Backend used
- `tokens_per_second` (float): Throughput
- `time_to_first_token_ms` (float): Latency
- `vram_usage_gb` (float): Memory consumption
- `status` (string): "passed" | "failed"

**Example**:
```json
{
  "test_name": "Llama 3.2 7B - ROCm",
  "backend": "rocm",
  "tokens_per_second": 22.5,
  "time_to_first_token_ms": 1200,
  "vram_usage_gb": 12.5,
  "status": "passed"
}
```

## Relationships

```
TestConfiguration --1:1--> TestResult
    |                          |
    |                          +--1:*--> ResponseRecord
    +--1:1--> ModelConfiguration
    +--1:1--> ExecutionConfiguration
    +--1:1--> EnvironmentInfo
    +--1:1--> ExpectedMetrics

TestResult --1:1--> PerformanceMetrics
           --1:1--> ValidationResults
           --0:*--> ErrorRecord

BenchmarkSummary --1:*--> TestResult
                 --1:1--> AggregateMetrics
                 --1:*--> ComparisonRow
```

## Storage Format

All entities serialize to JSON for storage in `tests/rocm_max395/results/` directory:

```
results/
├── tests/
│   ├── P1-basic-7b-001.json       # TestConfiguration + TestResult
│   ├── P1-basic-7b-002.json
│   ├── P2-perf-13b-001.json
│   └── ...
├── benchmarks/
│   ├── benchmark-001.json         # BenchmarkSummary
│   └── ...
└── archive/
    └── 2025-12-23/                # Date-based archiving
```

## Usage in Tests

**Test Script Example** (pytest):
```python
# tests/rocm_max395/test_basic_inference.py
from utils.metrics_collector import MetricsCollector
from utils.lemonade_client import LemonadeClient
import json

def test_basic_inference_7b(lemonade_server):
    # Load configuration
    config = TestConfiguration(
        test_id="P1-basic-7b-001",
        model_config=ModelConfiguration(model_name="Llama-3.2-7B-Instruct-GGUF", ...),
        execution_config=ExecutionConfiguration(backend="rocm", ...),
        ...
    )
    
    # Execute test
    client = LemonadeClient(config.execution_config.api_base_url)
    collector = MetricsCollector()
    
    result = TestResult(test_id=config.test_id, start_time=now())
    
    for prompt in config.test_prompts:
        response = client.generate(prompt, config.execution_config)
        result.responses.append(ResponseRecord(...))
        collector.record_metrics(response)
    
    result.performance_metrics = collector.aggregate()
    result.validation_results = validate_criteria(result, config.expected_metrics)
    result.status = "passed" if result.validation_results.overall_pass else "failed"
    
    # Save result
    with open(f"results/tests/{config.test_id}.json", "w") as f:
        json.dump(result.to_dict(), f, indent=2)
    
    assert result.validation_results.overall_pass
```

## Extensibility

Data model supports future extensions:
- Additional backends (ONNX, FLM) via ExecutionConfiguration.backend
- Multi-GPU testing via EnvironmentInfo.gpu_model (list)
- Advanced metrics (memory bandwidth, cache hit rate) via PerformanceMetrics custom fields
- Automated accuracy scoring via ValidationResults.criteria_checks
