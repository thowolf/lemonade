# Data Model: LLM Model Comparison Dashboard

**Feature**: `003-wandb-model-comparison`
**Date**: 2025-12-24
**Status**: Phase 1 Design
**Related**: [spec.md](./spec.md) | [plan.md](./plan.md) | [research.md](./research.md)

---

## Overview

This document defines the data entities for the LLM Model Comparison Dashboard feature. These entities represent the domain model for evaluation runs, model configurations, benchmark results, and comparison sets. The design is technology-agnostic at the conceptual level, with implementation details deferred to the code phase.

---

## Core Entities

### 1. Evaluation Run

**Description**: Represents a single benchmark execution session for a specific model configuration.

**Attributes**:

| Attribute | Type | Required | Description | Validation |
|-----------|------|----------|-------------|------------|
| `run_id` | String (UUID) | Yes | Unique identifier for the evaluation run | UUID v4 format |
| `name` | String | Yes | Human-readable name for the run | Max 255 chars |
| `model_config_id` | String (UUID) | Yes | Reference to ModelConfiguration | Must exist |
| `benchmark_suite` | String | Yes | Benchmark suite name (e.g., "mmlu", "hellaswag") | From predefined list |
| `status` | Enum | Yes | Run status: pending, running, completed, failed | One of enum values |
| `created_at` | DateTime | Yes | Timestamp when run was created | ISO 8601 format |
| `started_at` | DateTime | No | Timestamp when execution started | ISO 8601 format |
| `completed_at` | DateTime | No | Timestamp when execution finished | ISO 8601 format |
| `hardware_platform` | Object | Yes | Hardware details (CPU, GPU, NPU, VRAM) | See HardwarePlatform |
| `backend` | String | Yes | Inference backend used (e.g., "oga-npu", "llamacpp-cpu") | Max 50 chars |
| `error_message` | String | No | Error details if run failed | Max 1000 chars |
| `wandb_run_url` | String (URL) | No | Link to W&B dashboard run | Valid URL |
| `tags` | Array[String] | No | User-defined tags for filtering | Max 20 tags |

**Relationships**:
- `model_config_id` → Many-to-One → ModelConfiguration
- `run_id` → One-to-Many → BenchmarkResult

**State Transitions**:
```
pending → running → completed
               ↓
            failed
```

**Invariants**:
- `started_at` must be >= `created_at`
- `completed_at` must be >= `started_at`
- `status = "completed"` requires `completed_at` is not null
- `status = "failed"` requires `error_message` is not null

---

### 2. Model Configuration

**Description**: Represents a specific combination of model architecture, quantization level, and MoE settings that can be evaluated.

**Attributes**:

| Attribute | Type | Required | Description | Validation |
|-----------|------|----------|-------------|------------|
| `config_id` | String (UUID) | Yes | Unique identifier for the configuration | UUID v4 format |
| `model_name` | String | Yes | Model identifier (e.g., "Llama-3.1-8B-Instruct") | Max 255 chars |
| `model_family` | String | Yes | Model family (e.g., "llama", "qwen", "phi") | Lowercase, max 50 chars |
| `checkpoint` | String | Yes | Model checkpoint path (HF format: org/repo:file) | Must contain ":" |
| `quantization` | String | Yes | Quantization method (e.g., "int4", "int8", "fp16") | From predefined list |
| `moe_config` | Object | No | MoE configuration details | See MoEConfig |
| `size_gb` | Float | Yes | Model size in gigabytes | > 0 |
| `context_length` | Integer | Yes | Maximum context window size | > 0 |
| `version` | String | No | Configuration version (e.g., "1.0.0") | Semantic versioning |
| `created_at` | DateTime | Yes | Timestamp when config was created | ISO 8601 format |
| `metadata` | Object | No | Additional metadata (key-value pairs) | Max 10 keys |

**Nested Objects**:

**MoEConfig**:
- `num_experts`: Integer (required) - Total number of experts
- `experts_per_token`: Integer (required) - Active experts per token
- `expert_capacity`: Integer (optional) - Capacity factor for load balancing

**Relationships**:
- `config_id` → One-to-Many → EvaluationRun

**Invariants**:
- `checkpoint` must match pattern: `<org>/<repo>:<file>` or `<org>/<repo>:<quant>`
- If `moe_config` is present, both `num_experts` and `experts_per_token` are required
- `experts_per_token` <= `num_experts`

**Examples**:
```json
{
  "config_id": "cfg-123e4567-e89b-12d3-a456-426614174000",
  "model_name": "Llama-3.1-8B-Instruct",
  "model_family": "llama",
  "checkpoint": "meta-llama/Llama-3.1-8B-Instruct:Q4_0",
  "quantization": "int4",
  "moe_config": null,
  "size_gb": 4.8,
  "context_length": 8192,
  "version": "1.0.0"
}
```

---

### 3. Benchmark Result

**Description**: Contains performance metrics from a single benchmark test within an evaluation run.

**Attributes**:

| Attribute | Type | Required | Description | Validation |
|-----------|------|----------|-------------|------------|
| `result_id` | String (UUID) | Yes | Unique identifier for the result | UUID v4 format |
| `run_id` | String (UUID) | Yes | Reference to parent EvaluationRun | Must exist |
| `task_name` | String | Yes | Specific benchmark task (e.g., "mmlu_abstract_algebra") | Max 255 chars |
| `accuracy_metrics` | Object | No | Accuracy scores (acc, exact_match, f1, etc.) | See AccuracyMetrics |
| `performance_metrics` | Object | Yes | Performance measurements | See PerformanceMetrics |
| `resource_metrics` | Object | Yes | Resource utilization data | See ResourceMetrics |
| `iteration` | Integer | No | Iteration number if multiple runs | >= 0 |
| `timestamp` | DateTime | Yes | When the benchmark was executed | ISO 8601 format |
| `sample_count` | Integer | No | Number of samples evaluated | > 0 |

**Nested Objects**:

**AccuracyMetrics**:
- `acc`: Float (0-1 range) - Overall accuracy
- `acc_stderr`: Float - Standard error of accuracy
- `exact_match`: Float (0-1 range) - Exact match score
- `f1`: Float (0-1 range) - F1 score
- `custom_metrics`: Object - Additional task-specific metrics

**PerformanceMetrics**:
- `tokens_per_second`: Float (required) - Throughput
- `latency_ms`: Float (required) - Mean latency in milliseconds
- `latency_p50_ms`: Float - Median latency
- `latency_p95_ms`: Float - 95th percentile latency
- `latency_p99_ms`: Float - 99th percentile latency
- `time_to_first_token_ms`: Float - TTFT measurement
- `total_tokens`: Integer - Total tokens processed
- `prompt_tokens`: Integer - Input tokens
- `completion_tokens`: Integer - Generated tokens

**ResourceMetrics**:
- `peak_memory_mb`: Float (required) - Peak memory usage
- `avg_memory_mb`: Float - Average memory usage
- `vram_usage_mb`: Float - GPU/NPU VRAM usage
- `cpu_utilization_percent`: Float (0-100) - CPU usage
- `gpu_utilization_percent`: Float (0-100) - GPU/NPU usage
- `power_consumption_watts`: Float - Power draw (if available)

**Relationships**:
- `run_id` → Many-to-One → EvaluationRun

**Invariants**:
- All percentage metrics must be in range [0, 100]
- All accuracy metrics must be in range [0, 1]
- `prompt_tokens` + `completion_tokens` = `total_tokens`
- `latency_p50_ms` <= `latency_p95_ms` <= `latency_p99_ms`

---

### 4. Comparison Set

**Description**: A user-defined grouping of evaluation runs selected for side-by-side analysis.

**Attributes**:

| Attribute | Type | Required | Description | Validation |
|-----------|------|----------|-------------|------------|
| `set_id` | String (UUID) | Yes | Unique identifier for the comparison set | UUID v4 format |
| `name` | String | Yes | Name of the comparison set | Max 255 chars |
| `description` | String | No | Purpose and context of comparison | Max 1000 chars |
| `run_ids` | Array[String (UUID)] | Yes | List of evaluation runs to compare | Min 2, max 50 |
| `created_by` | String | No | User who created the set | Max 100 chars |
| `created_at` | DateTime | Yes | Timestamp when set was created | ISO 8601 format |
| `filters` | Object | No | Applied filters (model_family, quantization, etc.) | See Filters |
| `visualization_config` | Object | No | Dashboard layout preferences | See VisualizationConfig |
| `shared` | Boolean | No | Whether set is shared with team | Default: false |
| `wandb_report_url` | String (URL) | No | Link to W&B report if generated | Valid URL |

**Nested Objects**:

**Filters**:
- `model_families`: Array[String] - Filter by model families
- `quantizations`: Array[String] - Filter by quantization levels
- `benchmarks`: Array[String] - Filter by benchmark suites
- `min_accuracy`: Float - Minimum accuracy threshold
- `max_latency_ms`: Float - Maximum latency threshold

**VisualizationConfig**:
- `chart_types`: Array[String] - Preferred chart types (bar, scatter, table)
- `primary_metric`: String - Main metric to highlight
- `sort_by`: String - Sorting criterion
- `group_by`: String - Grouping dimension

**Relationships**:
- `run_ids` → Many-to-Many → EvaluationRun

**Invariants**:
- `run_ids` must contain at least 2 valid run identifiers
- All runs in `run_ids` must exist and be in "completed" status
- `filters` must not result in empty result set

**Examples**:
```json
{
  "set_id": "set-789a1234-e56b-78c9-d012-345678901234",
  "name": "INT4 vs INT8 Quantization Comparison",
  "description": "Compare Llama-3.1-8B with different quantization levels",
  "run_ids": ["run-001", "run-002", "run-003"],
  "filters": {
    "model_families": ["llama"],
    "quantizations": ["int4", "int8"],
    "benchmarks": ["mmlu", "hellaswag"]
  },
  "created_at": "2025-12-24T10:00:00Z"
}
```

---

### 5. Hardware Platform

**Description**: Embedded object representing hardware configuration for an evaluation run.

**Attributes**:

| Attribute | Type | Required | Description | Validation |
|-----------|------|----------|-------------|------------|
| `platform_name` | String | Yes | Hardware platform identifier | Max 100 chars |
| `cpu` | String | Yes | CPU model (e.g., "AMD Ryzen AI Max+ 395") | Max 100 chars |
| `gpu` | String | No | GPU model (e.g., "AMD Radeon 8060S") | Max 100 chars |
| `npu` | String | No | NPU model (e.g., "AMD Ryzen AI NPU") | Max 100 chars |
| `architecture` | String | No | GPU/NPU architecture (e.g., "gfx1151") | Max 50 chars |
| `total_vram_gb` | Float | No | Total VRAM available | > 0 |
| `system_ram_gb` | Float | Yes | System RAM | > 0 |
| `os` | String | Yes | Operating system (e.g., "Windows 11", "Ubuntu 24.04") | Max 50 chars |
| `driver_version` | String | No | GPU/NPU driver version | Max 50 chars |

**Invariants**:
- At least one of `gpu`, `npu`, or both must be present for GPU/NPU evaluations
- `total_vram_gb` is required if `gpu` or `npu` is present

---

## Entity Relationship Diagram

```
┌─────────────────────┐
│ ModelConfiguration  │
│ ─────────────────── │
│ config_id (PK)      │
│ model_name          │
│ checkpoint          │
│ quantization        │
│ moe_config          │
└──────────┬──────────┘
           │
           │ 1:N
           │
           ▼
┌─────────────────────┐        ┌─────────────────────┐
│  EvaluationRun      │        │  ComparisonSet      │
│ ─────────────────── │        │ ─────────────────── │
│ run_id (PK)         │◄───┐   │ set_id (PK)         │
│ model_config_id(FK) │    │   │ name                │
│ benchmark_suite     │    │   │ run_ids[] (FK)      │
│ status              │    │   │ filters             │
│ hardware_platform   │    │   └─────────────────────┘
│ backend             │    │
└──────────┬──────────┘    │
           │               │
           │ 1:N           │ M:N
           │               │
           ▼               │
┌─────────────────────┐    │
│  BenchmarkResult    │    │
│ ─────────────────── │    │
│ result_id (PK)      │    │
│ run_id (FK)         │────┘
│ task_name           │
│ accuracy_metrics    │
│ performance_metrics │
│ resource_metrics    │
└─────────────────────┘
```

---

## Data Access Patterns

### Primary Queries

1. **Get all runs for a model configuration**
   ```
   SELECT * FROM EvaluationRun
   WHERE model_config_id = :config_id
   ORDER BY created_at DESC
   ```

2. **Get benchmark results for a run**
   ```
   SELECT * FROM BenchmarkResult
   WHERE run_id = :run_id
   ORDER BY task_name
   ```

3. **Find best performing configuration for a benchmark**
   ```
   SELECT mc.*, AVG(br.accuracy_metrics.acc) as avg_accuracy
   FROM ModelConfiguration mc
   JOIN EvaluationRun er ON mc.config_id = er.model_config_id
   JOIN BenchmarkResult br ON er.run_id = br.run_id
   WHERE er.benchmark_suite = :suite_name
   GROUP BY mc.config_id
   ORDER BY avg_accuracy DESC
   LIMIT 10
   ```

4. **Compare runs in a comparison set**
   ```
   SELECT er.*, br.*
   FROM ComparisonSet cs
   JOIN EvaluationRun er ON er.run_id IN (cs.run_ids)
   JOIN BenchmarkResult br ON br.run_id = er.run_id
   WHERE cs.set_id = :set_id
   ```

### Filtering Patterns

- By model family: `WHERE model_family = 'llama'`
- By quantization: `WHERE quantization IN ('int4', 'int8')`
- By benchmark suite: `WHERE benchmark_suite = 'mmlu'`
- By hardware: `WHERE hardware_platform.platform_name = 'AMD Ryzen AI Max+ 395'`
- By status: `WHERE status = 'completed'`
- By date range: `WHERE created_at BETWEEN :start_date AND :end_date`

---

## Storage Considerations

### W&B Weave Integration

**Primary Storage**: W&B cloud
- `EvaluationRun` → W&B Run
- `BenchmarkResult` → W&B Metrics (logged via `weave.log()`)
- `ModelConfiguration` → W&B Config + Tags
- `ComparisonSet` → W&B Report + Custom dashboard

**Grouping Strategy**:
- W&B Group: `{model_family}/{quantization}/{benchmark_suite}`
- W&B Tags: `model:{family}`, `quant:{level}`, `benchmark:{suite}`

### Local Caching (Optional)

For offline support and faster queries:
- JSON files per evaluation run
- SQLite database for metadata indexing
- File structure:
  ```
  .wandb/
    evaluations/
      {run_id}/
        metadata.json
        results.json
        metrics.json
  ```

---

## Validation Rules

### Cross-Entity Validation

1. **Evaluation Run → Model Configuration**
   - `model_config_id` must reference existing configuration
   - Backend must be compatible with model format

2. **Benchmark Result → Evaluation Run**
   - `run_id` must reference existing run
   - `task_name` must be valid for `benchmark_suite`

3. **Comparison Set → Evaluation Runs**
   - All `run_ids` must exist
   - All runs must have status = "completed"
   - Runs should use same benchmark suite for meaningful comparison

### Data Integrity

1. **Referential Integrity**
   - Foreign key relationships must be maintained
   - Cascading deletes: Delete ModelConfiguration → Delete all EvaluationRuns

2. **Temporal Consistency**
   - Timestamps must follow logical order
   - `completed_at` - `started_at` = run duration (reasonable limits)

3. **Metric Constraints**
   - All metrics must be within valid ranges
   - Required metrics must not be null for completed runs

---

## Versioning and Migration

### Schema Versioning

- Current version: `1.0.0`
- Version stored in entity metadata
- Migration path for schema updates

### Backwards Compatibility

- New optional fields can be added without breaking changes
- Required field additions require migration scripts
- Deprecated fields marked with `@deprecated` annotation

---

## Implementation Notes

### Technology Mapping

| Concept | W&B Weave | Local Storage |
|---------|-----------|---------------|
| EvaluationRun | W&B Run | JSON file |
| BenchmarkResult | W&B Metrics | JSON array |
| ModelConfiguration | W&B Config | JSON file |
| ComparisonSet | W&B Report | SQLite table |

### Pydantic Model Example

```python
from pydantic import BaseModel, Field, UUID4
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class MoEConfig(BaseModel):
    num_experts: int = Field(gt=0)
    experts_per_token: int = Field(gt=0)
    expert_capacity: Optional[int] = None

class ModelConfiguration(BaseModel):
    config_id: UUID4
    model_name: str = Field(max_length=255)
    model_family: str = Field(max_length=50)
    checkpoint: str
    quantization: str
    moe_config: Optional[MoEConfig] = None
    size_gb: float = Field(gt=0)
    context_length: int = Field(gt=0)
    created_at: datetime

class EvaluationRun(BaseModel):
    run_id: UUID4
    name: str = Field(max_length=255)
    model_config_id: UUID4
    benchmark_suite: str
    status: RunStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    # ... other fields
```

---

## Next Steps

After data model approval:
1. Create Pydantic models in `src/lemonade/evaluation/models.py`
2. Implement W&B Weave logging schema in `contracts/wandb-schema.yaml`
3. Define JSON Schema for configs in `contracts/evaluation-config.schema.json`
4. Build data access layer with validation
5. Integrate with existing Lemonade `MetricsCollector`

---

**Status**: Ready for review and implementation
