# Data Model: Continue Extension Model Testing Framework

**Feature**: 004-continue-model-testing
**Date**: 2025-12-25

## Overview

This document defines the data entities, their attributes, relationships, and validation rules for the Continue model testing framework. The data model supports test configuration, metrics collection, freeze event tracking, and compatibility reporting.

---

## Core Entities

### 1. CoderModel

**Description**: Represents a specific LLM variant that can be tested with the Continue extension.

**Attributes**:
| Attribute | Type | Required | Description | Validation |
|-----------|------|----------|-------------|------------|
| name | string | Yes | Model identifier (e.g., "qwen2.5-coder-7b") | Non-empty, alphanumeric + hyphens |
| display_name | string | Yes | Human-readable name | Non-empty |
| source | enum | Yes | Model source: "ollama", "lmstudio", "huggingface" | Valid enum value |
| quantization | string | Yes | Quantization level (e.g., "q4_0", "bf16", "int8") | Non-empty |
| size_gb | float | No | Model size in gigabytes | > 0 |
| expected_tokens_per_second | float | No | Expected performance baseline | > 0 |
| tolerance_percent | float | No | Acceptable performance variance | 0-100 |
| max_stable_interactions | int | No | Expected freeze-free interaction count | > 0 |

**Example**:
```json
{
    "name": "qwen2.5-coder-7b-q4",
    "display_name": "Qwen 2.5 Coder 7B (Q4_0)",
    "source": "ollama",
    "quantization": "q4_0",
    "size_gb": 4.2,
    "expected_tokens_per_second": 25.0,
    "tolerance_percent": 20.0,
    "max_stable_interactions": 20
}
```

**Relationships**:
- One CoderModel → Many TestRun
- One CoderModel → Many CompatibilityResult

---

### 2. TestRun

**Description**: Represents a single execution of the testing framework against a specific model.

**Attributes**:
| Attribute | Type | Required | Description | Validation |
|-----------|------|----------|-------------|------------|
| run_id | string | Yes | Unique run identifier (UUID) | UUID format |
| model_name | string | Yes | Foreign key to CoderModel | Must exist in models config |
| start_time | datetime | Yes | Test start timestamp (ISO 8601) | Valid datetime |
| end_time | datetime | No | Test end timestamp | After start_time |
| status | enum | Yes | "running", "completed", "failed", "aborted" | Valid enum value |
| hardware_config | HardwareConfiguration | Yes | Hardware environment snapshot | Valid HardwareConfiguration |
| test_scenario | string | No | Name of test scenario used | Must exist in scenarios config |
| num_interactions_planned | int | Yes | Total interactions to execute | > 0 |
| num_interactions_completed | int | Yes | Interactions completed | 0 to num_interactions_planned |
| freeze_detected | bool | Yes | Whether a freeze occurred | Boolean |
| freeze_after_interaction | int | No | Interaction number where freeze occurred | 1 to num_interactions_completed |
| metrics_collected | int | Yes | Number of metric samples collected | >= 0 |

**Example**:
```json
{
    "run_id": "550e8400-e29b-41d4-a716-446655440000",
    "model_name": "qwen2.5-coder-7b-q4",
    "start_time": "2025-12-25T14:30:00Z",
    "end_time": "2025-12-25T14:45:00Z",
    "status": "completed",
    "hardware_config": {...},
    "test_scenario": "code_explanation",
    "num_interactions_planned": 10,
    "num_interactions_completed": 10,
    "freeze_detected": false,
    "freeze_after_interaction": null,
    "metrics_collected": 900
}
```

**Relationships**:
- Many TestRun → One CoderModel
- One TestRun → Many TestInteraction
- One TestRun → Many SystemMetrics
- One TestRun → Zero or More FreezeEvent

---

### 3. TestInteraction

**Description**: Represents a single chat request/response cycle with the Continue extension.

**Attributes**:
| Attribute | Type | Required | Description | Validation |
|-----------|------|----------|-------------|------------|
| interaction_id | string | Yes | Unique interaction identifier | UUID format |
| run_id | string | Yes | Foreign key to TestRun | Must exist |
| sequence_number | int | Yes | Interaction number in test sequence | > 0 |
| request_timestamp | datetime | Yes | When request was sent | Valid datetime |
| request_text | string | Yes | Prompt sent to Continue | Non-empty |
| context_provided | bool | Yes | Whether code context was selected | Boolean |
| response_timestamp | datetime | No | When response completed | After request_timestamp |
| response_text | string | No | Model response (may be truncated) | Any string |
| response_tokens | int | No | Number of tokens in response | >= 0 |
| duration_ms | float | No | Total request-to-response time | >= 0 |
| tokens_per_second | float | No | Token generation rate | >= 0 |
| success | bool | Yes | Whether interaction completed | Boolean |
| error_message | string | No | Error if success=false | Any string |

**Example**:
```json
{
    "interaction_id": "660e8400-e29b-41d4-a716-446655440001",
    "run_id": "550e8400-e29b-41d4-a716-446655440000",
    "sequence_number": 3,
    "request_timestamp": "2025-12-25T14:33:15Z",
    "request_text": "Add error handling to this function",
    "context_provided": true,
    "response_timestamp": "2025-12-25T14:33:28Z",
    "response_text": "Here's the function with added error handling...",
    "response_tokens": 247,
    "duration_ms": 13200.5,
    "tokens_per_second": 18.7,
    "success": true,
    "error_message": null
}
```

**Relationships**:
- Many TestInteraction → One TestRun
- One TestInteraction → Zero or One FreezeEvent (if freeze occurs during this interaction)

---

### 4. FreezeEvent

**Description**: Represents a detected unresponsive state of the Continue extension.

**Attributes**:
| Attribute | Type | Required | Description | Validation |
|-----------|------|----------|-------------|------------|
| freeze_id | string | Yes | Unique freeze event identifier | UUID format |
| run_id | string | Yes | Foreign key to TestRun | Must exist |
| interaction_id | string | No | Interaction during which freeze occurred | Must exist if provided |
| detected_timestamp | datetime | Yes | When freeze was detected | Valid datetime |
| detection_method | enum | Yes | "timeout", "user_report", "log_analysis", "process_monitor" | Valid enum value |
| last_response_timestamp | datetime | No | Timestamp of last successful response | Before detected_timestamp |
| time_since_last_response_s | float | No | Seconds since last activity | >= 0 |
| metrics_at_freeze | SystemMetrics | Yes | System state when freeze detected | Valid SystemMetrics |
| continue_process_state | string | No | Process state (running/not responding/terminated) | Any string |
| diagnostic_logs_path | string | No | Path to collected diagnostic data | Valid file path |
| user_notes | string | No | Additional context from tester | Any string |

**Example**:
```json
{
    "freeze_id": "770e8400-e29b-41d4-a716-446655440002",
    "run_id": "550e8400-e29b-41d4-a716-446655440000",
    "interaction_id": "660e8400-e29b-41d4-a716-446655440001",
    "detected_timestamp": "2025-12-25T14:35:45Z",
    "detection_method": "user_report",
    "last_response_timestamp": "2025-12-25T14:33:28Z",
    "time_since_last_response_s": 137.0,
    "metrics_at_freeze": {...},
    "continue_process_state": "not_responding",
    "diagnostic_logs_path": "./results/freeze_events/freeze_770e8400.json",
    "user_notes": "UI became completely unresponsive, spinner still animating but no response generated"
}
```

**Relationships**:
- Many FreezeEvent → One TestRun
- One FreezeEvent → Zero or One TestInteraction

---

### 5. HardwareConfiguration

**Description**: Represents the test environment hardware and software configuration.

**Attributes**:
| Attribute | Type | Required | Description | Validation |
|-----------|------|----------|-------------|------------|
| cpu_model | string | Yes | CPU identifier (e.g., "AMD Ryzen AI Max+ 395") | Non-empty |
| ram_total_gb | float | Yes | Total system RAM | > 0 |
| npu_available | bool | Yes | Whether NPU is detected | Boolean |
| npu_driver_version | string | No | NPU driver version | Any string |
| gpu_model | string | No | GPU identifier | Any string |
| gpu_vram_gb | float | No | GPU VRAM capacity | > 0 |
| gpu_driver_version | string | No | GPU driver version | Any string |
| os_version | string | Yes | Operating system version | Non-empty |
| python_version | string | Yes | Python interpreter version | Valid version format (X.Y.Z) |
| anaconda_env | string | No | Anaconda environment name | Any string |
| vscode_version | string | No | VSCode version | Version format |
| continue_version | string | No | Continue extension version | Version format |

**Example**:
```json
{
    "cpu_model": "AMD Ryzen AI Max+ 395",
    "ram_total_gb": 128.0,
    "npu_available": true,
    "npu_driver_version": "1.4.0",
    "gpu_model": "AMD Radeon 8060S",
    "gpu_vram_gb": 96.0,
    "gpu_driver_version": "31.0.24033.1003",
    "os_version": "Windows 11 Pro 23H2",
    "python_version": "3.13.1",
    "anaconda_env": "lemonade-amd",
    "vscode_version": "1.85.2",
    "continue_version": "0.8.45"
}
```

**Relationships**:
- One HardwareConfiguration → Many TestRun (captured as snapshot)

---

### 6. SystemMetrics

**Description**: Represents a timestamped snapshot of system resource utilization.

**Attributes**:
| Attribute | Type | Required | Description | Validation |
|-----------|------|----------|-------------|------------|
| metric_id | string | Yes | Unique metric sample identifier | UUID format |
| run_id | string | Yes | Foreign key to TestRun | Must exist |
| timestamp | datetime | Yes | Sample collection time | Valid datetime |
| cpu_percent | float | Yes | System-wide CPU utilization | 0-100 |
| cpu_freq_mhz | float | No | CPU frequency | > 0 |
| memory_total_gb | float | Yes | Total system RAM | > 0 |
| memory_used_gb | float | Yes | Used system RAM | 0 to memory_total_gb |
| memory_percent | float | Yes | RAM utilization percentage | 0-100 |
| proc_cpu_percent | float | No | Continue process CPU % | 0-100 |
| proc_memory_rss_mb | float | No | Continue process RSS memory | >= 0 |
| proc_memory_vms_mb | float | No | Continue process VMS memory | >= 0 |
| npu_device_count | int | No | Number of NPU devices | >= 0 |
| npu_gops | float | No | NPU compute throughput | >= 0 |
| npu_command_submissions | int | No | NPU command queue submissions | >= 0 |
| npu_command_completions | int | No | NPU command queue completions | >= 0 |
| npu_utilization_percent | float | No | NPU utilization | 0-100 |
| amd_gpu_utilization_percent | float | No | AMD GPU utilization | 0-100 |
| amd_gpu_temperature_c | float | No | AMD GPU temperature | 0-150 |
| amd_gpu_core_clock_mhz | int | No | AMD GPU core clock | > 0 |

**Example**:
```json
{
    "metric_id": "880e8400-e29b-41d4-a716-446655440003",
    "run_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2025-12-25T14:33:20Z",
    "cpu_percent": 45.2,
    "cpu_freq_mhz": 3800.0,
    "memory_total_gb": 128.0,
    "memory_used_gb": 54.3,
    "memory_percent": 42.4,
    "proc_cpu_percent": 12.5,
    "proc_memory_rss_mb": 2048.7,
    "npu_device_count": 1,
    "npu_gops": 12.4,
    "npu_utilization_percent": 78.3,
    "amd_gpu_utilization_percent": 15.2,
    "amd_gpu_temperature_c": 65.0,
    "amd_gpu_core_clock_mhz": 2100
}
```

**Relationships**:
- Many SystemMetrics → One TestRun

---

### 7. PerformanceMetrics

**Description**: Aggregated performance statistics for a test run or interaction.

**Attributes**:
| Attribute | Type | Required | Description | Validation |
|-----------|------|----------|-------------|------------|
| entity_id | string | Yes | TestRun or TestInteraction ID | UUID format |
| entity_type | enum | Yes | "test_run", "test_interaction" | Valid enum value |
| response_time_mean_ms | float | No | Mean response time | >= 0 |
| response_time_p50_ms | float | No | Median response time | >= 0 |
| response_time_p95_ms | float | No | 95th percentile response time | >= 0 |
| response_time_p99_ms | float | No | 99th percentile response time | >= 0 |
| tokens_per_second_mean | float | No | Mean token generation rate | >= 0 |
| tokens_per_second_p50 | float | No | Median token generation rate | >= 0 |
| memory_peak_gb | float | No | Peak memory usage | >= 0 |
| npu_utilization_mean_percent | float | No | Mean NPU utilization | 0-100 |
| npu_utilization_max_percent | float | No | Peak NPU utilization | 0-100 |
| cpu_utilization_mean_percent | float | No | Mean CPU utilization | 0-100 |
| success_rate_percent | float | No | Percentage of successful interactions | 0-100 |

**Example**:
```json
{
    "entity_id": "550e8400-e29b-41d4-a716-446655440000",
    "entity_type": "test_run",
    "response_time_mean_ms": 14200.5,
    "response_time_p50_ms": 13800.2,
    "response_time_p95_ms": 18500.8,
    "response_time_p99_ms": 22100.3,
    "tokens_per_second_mean": 19.3,
    "tokens_per_second_p50": 20.1,
    "memory_peak_gb": 58.2,
    "npu_utilization_mean_percent": 72.5,
    "npu_utilization_max_percent": 95.2,
    "cpu_utilization_mean_percent": 48.3,
    "success_rate_percent": 100.0
}
```

**Relationships**:
- One PerformanceMetrics → One TestRun or One TestInteraction

---

### 8. CompatibilityResult

**Description**: Summary of a model's compatibility and stability assessment.

**Attributes**:
| Attribute | Type | Required | Description | Validation |
|-----------|------|----------|-------------|------------|
| result_id | string | Yes | Unique result identifier | UUID format |
| model_name | string | Yes | Foreign key to CoderModel | Must exist |
| assessment_date | datetime | Yes | When assessment was performed | Valid datetime |
| test_runs_analyzed | int | Yes | Number of test runs included | > 0 |
| compatible | bool | Yes | Overall compatibility verdict | Boolean |
| max_stable_interactions_observed | int | Yes | Longest freeze-free run | >= 0 |
| freeze_rate_percent | float | Yes | Percentage of runs with freezes | 0-100 |
| mean_freeze_after_interaction | float | No | Average interaction where freezes occur | > 0 |
| performance_rating | enum | Yes | "excellent", "good", "fair", "poor" | Valid enum value |
| stability_rating | enum | Yes | "stable", "mostly_stable", "unstable" | Valid enum value |
| recommended_for_production | bool | Yes | Production readiness recommendation | Boolean |
| notes | string | No | Additional assessment notes | Any string |
| limitations | list[string] | No | Known limitations or issues | Array of strings |

**Example**:
```json
{
    "result_id": "990e8400-e29b-41d4-a716-446655440004",
    "model_name": "qwen2.5-coder-7b-q4",
    "assessment_date": "2025-12-25T15:00:00Z",
    "test_runs_analyzed": 5,
    "compatible": true,
    "max_stable_interactions_observed": 20,
    "freeze_rate_percent": 0.0,
    "mean_freeze_after_interaction": null,
    "performance_rating": "good",
    "stability_rating": "stable",
    "recommended_for_production": true,
    "notes": "Excellent stability across all test runs. Performance within expected range.",
    "limitations": ["Large code context (>5000 lines) may slow response times"]
}
```

**Relationships**:
- Many CompatibilityResult → One CoderModel

---

## Entity Relationship Diagram

```
CoderModel (1) ──────< (N) TestRun (1) ──────< (N) TestInteraction
    │                          │                          │
    │                          │                          │
    │                          ├──────< (N) SystemMetrics │
    │                          │                          │
    │                          ├──────< (0..N) FreezeEvent ├──── (0..1)
    │                          │
    │                          ├────── (1) HardwareConfiguration
    │                          │
    │                          └────── (0..1) PerformanceMetrics
    │
    └──────< (N) CompatibilityResult
```

---

## State Transitions

### TestRun Status State Machine

```
[Created] → running → completed ✓
                  ↘
                   failed ✗
                    ↘
                     aborted ⊗
```

**Valid Transitions**:
- `created` → `running`: Test execution starts
- `running` → `completed`: All interactions finish successfully
- `running` → `failed`: Error prevents test completion
- `running` → `aborted`: User cancels test
- No transitions allowed from terminal states (`completed`, `failed`, `aborted`)

---

## Validation Rules

### Cross-Entity Validation

1. **TestRun.num_interactions_completed <= TestRun.num_interactions_planned**
2. **If TestRun.freeze_detected == true, then FreezeEvent must exist with matching run_id**
3. **TestInteraction.response_timestamp > TestInteraction.request_timestamp** (if both present)
4. **SystemMetrics.timestamp must be between TestRun.start_time and TestRun.end_time**
5. **FreezeEvent.detected_timestamp >= TestRun.start_time**
6. **PerformanceMetrics.entity_id must exist in corresponding entity table**

### Data Consistency Rules

1. **Test run must have at least one SystemMetrics sample**
2. **Completed test run must have performance metrics calculated**
3. **Freeze event must have diagnostic logs path populated**
4. **Compatibility result must be based on at least 3 test runs**

---

## Storage Format

### File Structure

```
results/
├── test_runs/
│   └── {run_id}.json              # TestRun + TestInteractions
├── metrics/
│   └── {run_id}_metrics.json      # SystemMetrics samples (chunked)
├── freeze_events/
│   └── freeze_{freeze_id}.json    # FreezeEvent + diagnostics
├── performance/
│   └── {run_id}_perf.json         # PerformanceMetrics
└── reports/
    └── compatibility_matrix.json  # CompatibilityResults
```

### JSON Schema Example (TestRun)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["run_id", "model_name", "start_time", "status", "hardware_config"],
  "properties": {
    "run_id": {"type": "string", "format": "uuid"},
    "model_name": {"type": "string"},
    "start_time": {"type": "string", "format": "date-time"},
    "status": {"type": "string", "enum": ["running", "completed", "failed", "aborted"]},
    "freeze_detected": {"type": "boolean"},
    "interactions": {
      "type": "array",
      "items": {"$ref": "#/definitions/TestInteraction"}
    }
  }
}
```

---

## Migration and Versioning

**Schema Version**: 1.0.0
**Backward Compatibility**: Not required (initial implementation)
**Future Considerations**:
- Add `schema_version` field to all JSON output files
- Version changes follow semantic versioning (breaking changes = major bump)
