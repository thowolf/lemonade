# Research: W&B Weave Integration for LLM Model Comparison

**Feature**: `003-wandb-model-comparison`
**Date**: 2025-12-24
**Status**: Phase 0 Complete
**Research Focus**: W&B Weave integration patterns for Python evaluation workflows with LLM model comparison

---

## Executive Summary

This research document addresses the integration of Weights & Biases (W&B) Weave into the Lemonade SDK's evaluation workflows for LLM model comparison on AMD Ryzen AI hardware. Based on analysis of existing Lemonade metrics collection patterns, industry best practices, and W&B Weave capabilities, this document provides technical recommendations for initialization patterns, logging strategies, offline mode support, and dashboard customization.

**Key Findings**:
- **Initialization Pattern**: One-time project initialization with per-evaluation-run tracking using W&B Weave's decorator-based approach
- **Offline Support**: W&B supports offline mode with sync-later capability through environment variables and CLI commands
- **Logging Pattern**: Structured metric logging using W&B's `weave.log()` and automatic versioning for model configurations
- **Dashboard Strategy**: Custom W&B dashboard panels with grouping by model family, quantization level, and benchmark suite
- **Integration Architecture**: Extend existing `MetricsCollector` class with W&B Weave logger as pluggable backend

---

## 1. W&B Weave Initialization Patterns

### Research Question
How should W&B Weave be initialized in evaluation workflows? One-time setup vs per-evaluation-run setup?

### Findings

#### Recommended Pattern: Hybrid Initialization

**One-Time Project Initialization** (at application startup or first use):
```python
import weave

# Initialize Weave project once
# This creates/connects to a W&B project for organizing all evaluation runs
weave.init(project_name="lemonade-ryzenai-evals")
```

**Per-Evaluation-Run Tracking** (for each model comparison run):
```python
# Use decorators to automatically track function calls
@weave.op()
def evaluate_model(model_config, benchmark_suite):
    """
    Weave automatically tracks:
    - Input parameters (model_config, benchmark_suite)
    - Output results
    - Execution time
    - Versioning of code and data
    """
    # Evaluation logic here
    results = run_benchmarks(model_config, benchmark_suite)

    # Log additional metrics
    weave.log({
        "tokens_per_second": results.tps,
        "latency_ms": results.latency,
        "memory_gb": results.peak_memory,
        "accuracy": results.accuracy_score
    })

    return results
```

#### Integration with Existing Lemonade Architecture

Based on the existing `MetricsCollector` class in `tests/rocm_max395/utils/metrics_collector.py`, we should extend it to support W&B Weave as a logging backend:

```python
class WandbWeaveLogger:
    """W&B Weave integration for evaluation metrics logging."""

    def __init__(self, project_name: str, entity: str = None):
        """
        Initialize Weave project.

        Args:
            project_name: W&B project name (e.g., "lemonade-ryzenai-evals")
            entity: W&B team/organization name (optional)
        """
        import weave

        # One-time initialization
        self.project_name = project_name
        self.entity = entity
        weave.init(f"{entity}/{project_name}" if entity else project_name)

    @weave.op()
    def log_evaluation_run(self,
                          test_name: str,
                          model_config: dict,
                          metrics: PerformanceMetrics,
                          environment: dict) -> None:
        """
        Log a single evaluation run to W&B Weave.

        Args:
            test_name: Name of the benchmark test
            model_config: Model configuration (name, quantization, MoE settings)
            metrics: Performance metrics from evaluation
            environment: System environment info (hardware, OS, etc.)
        """
        # Weave automatically tracks this function call
        # Additional custom logging
        weave.log({
            "test_name": test_name,
            "model_name": model_config.get("name"),
            "quantization": model_config.get("quantization"),
            "moe_config": model_config.get("moe_config"),
            "tokens_per_second": metrics.tokens_per_second,
            "latency_ms": metrics.latency_ms,
            "ttft_ms": metrics.time_to_first_token_ms,
            "peak_memory_mb": metrics.peak_memory_mb,
            "cpu_utilization": metrics.cpu_utilization_percent,
            "gpu_utilization": metrics.gpu_utilization_percent,
            "hardware": environment.get("hardware"),
            "backend": environment.get("backend")
        })
```

#### Decision: Hybrid Initialization

**Rationale**:
1. **One-time project init** reduces overhead and maintains consistent project context across multiple evaluation runs
2. **Per-run tracking** via decorators (`@weave.op()`) provides automatic versioning, input/output capture, and execution tracking
3. **Explicit logging** via `weave.log()` allows custom metrics and metadata to be recorded
4. **Compatibility** with existing Lemonade `MetricsCollector` patterns - can extend without breaking changes

---

## 2. Offline Mode Support

### Research Question
Does W&B Weave support offline logging with sync-later capability, or is cloud connectivity required?

### Findings

#### W&B Offline Mode Capabilities

**Yes**, W&B supports offline mode with sync-later capability through multiple mechanisms:

##### Option 1: Environment Variable (Recommended)
```bash
# Set offline mode before running evaluation
export WANDB_MODE=offline

# Run evaluation workflow
python evaluate_models.py

# Later, sync when online
wandb sync <run_directory>
```

##### Option 2: Programmatic Offline Mode
```python
import wandb
import os

# Enable offline mode programmatically
os.environ["WANDB_MODE"] = "offline"

# Initialize W&B (will cache locally)
wandb.init(project="lemonade-ryzenai-evals")

# Log metrics as normal - stored locally
wandb.log({"tokens_per_second": 125.3, "latency_ms": 45.2})

# Finish run
wandb.finish()

# Later, sync all offline runs
# From command line: wandb sync --sync-all
```

##### Option 3: Configuration File
Create `~/.config/wandb/settings` or project-level `.wandb/settings`:
```ini
[default]
mode = offline
```

#### Offline Data Storage

When in offline mode, W&B stores run data in:
- **Default location**: `./wandb/` directory in current working directory
- **Custom location**: Set via `WANDB_DIR` environment variable

**Directory structure**:
```
./wandb/
├── offline-run-<timestamp>-<run_id>/
│   ├── files/
│   │   ├── config.yaml
│   │   ├── wandb-metadata.json
│   │   └── wandb-summary.json
│   └── run-<run_id>.wandb
```

#### Syncing Offline Runs

Multiple sync strategies available:

```bash
# Sync a specific run
wandb sync ./wandb/offline-run-20251224_123456-abc123/

# Sync all offline runs in current directory
wandb sync --sync-all

# Sync from custom directory
wandb sync --sync-all /path/to/wandb/runs/
```

#### Integration Recommendation for Lemonade

**Offline-First Design**:
```python
class WandbWeaveLogger:
    """W&B Weave logger with offline-first support."""

    def __init__(self,
                 project_name: str,
                 offline: bool = False,
                 wandb_dir: str = None):
        """
        Initialize with optional offline mode.

        Args:
            project_name: W&B project name
            offline: If True, run in offline mode
            wandb_dir: Custom directory for offline runs
        """
        import os
        import weave

        if offline:
            os.environ["WANDB_MODE"] = "offline"

        if wandb_dir:
            os.environ["WANDB_DIR"] = wandb_dir

        weave.init(project_name)
        self.offline = offline
        self.wandb_dir = wandb_dir or "./wandb"

    def sync_offline_runs(self):
        """Sync all offline runs to W&B cloud."""
        if not self.offline:
            print("Not in offline mode, nothing to sync")
            return

        import subprocess
        result = subprocess.run(
            ["wandb", "sync", "--sync-all", self.wandb_dir],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"Successfully synced offline runs from {self.wandb_dir}")
        else:
            print(f"Sync failed: {result.stderr}")
```

#### Decision: Support Both Online and Offline Modes

**Rationale**:
1. **AMD Ryzen AI use case** may involve hardware testing without internet connectivity
2. **Development workflow** benefits from offline mode for rapid iteration
3. **Production deployment** can sync results periodically when online
4. **Minimal code changes** - W&B handles offline mode transparently
5. **Data safety** - offline runs are preserved locally and can be synced later

---

## 3. Logging Patterns for Evaluation Metrics

### Research Question
What are the best practices for logging evaluation metrics, model configurations, and benchmark results to W&B Weave?

### Findings

#### Metric Logging Hierarchy

W&B Weave supports multiple logging patterns, each suited for different use cases:

##### Pattern 1: Automatic Function Tracking (Recommended for High-Level Operations)

```python
import weave

@weave.op()
def run_mmlu_benchmark(model_config: dict, benchmark_config: dict):
    """
    Weave automatically captures:
    - Input parameters (model_config, benchmark_config)
    - Return value
    - Execution time
    - Call stack and dependencies
    """
    # Run benchmark
    results = execute_mmlu(model_config, benchmark_config)

    return {
        "accuracy": results.accuracy,
        "total_questions": results.total,
        "correct_answers": results.correct
    }
```

##### Pattern 2: Explicit Metric Logging (Recommended for Fine-Grained Metrics)

```python
import weave

@weave.op()
def evaluate_model_performance(model_name: str, device: str):
    """Evaluate and log detailed performance metrics."""

    # Run benchmark iterations
    metrics_list = []
    for i in range(iterations):
        result = run_single_iteration(model_name, device)

        # Log individual iteration
        weave.log({
            "iteration": i,
            "tokens_per_second": result.tps,
            "latency_ms": result.latency,
            "memory_gb": result.memory
        })

        metrics_list.append(result)

    # Log summary statistics
    weave.log({
        "summary/mean_tps": statistics.mean([m.tps for m in metrics_list]),
        "summary/p95_latency": percentile(95, [m.latency for m in metrics_list]),
        "summary/max_memory": max([m.memory for m in metrics_list])
    })

    return metrics_list
```

##### Pattern 3: Model Configuration Versioning

```python
import weave

# Define model configuration as a Weave Model
class ModelConfig(weave.Model):
    """Versioned model configuration."""
    model_name: str
    quantization: str  # e.g., "int4", "int8", "fp16"
    moe_config: dict
    backend: str  # e.g., "oga", "llamacpp", "flm"
    device: str  # e.g., "npu", "igpu", "cpu"

    @weave.op()
    def evaluate(self, benchmark_suite: str):
        """Run evaluation with this configuration."""
        # Weave automatically versions this config
        # Each change creates a new version
        results = run_benchmark(self, benchmark_suite)
        return results

# Usage
config = ModelConfig(
    model_name="Llama-3.1-8B-Instruct",
    quantization="int4",
    moe_config={"num_experts": 8, "experts_per_token": 2},
    backend="oga",
    device="npu"
)

# This is automatically versioned and tracked
results = config.evaluate("mmlu")
```

#### Integration with Existing Lemonade Metrics

Based on `PerformanceMetrics` and `BenchmarkResult` dataclasses in `metrics_collector.py`:

```python
from dataclasses import dataclass, asdict
import weave

@dataclass
class PerformanceMetrics:
    """Existing Lemonade metrics structure."""
    tokens_per_second: float
    latency_ms: float
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    time_to_first_token_ms: Optional[float] = None
    peak_memory_mb: Optional[float] = None

    def log_to_weave(self, prefix: str = ""):
        """Log metrics to W&B Weave."""
        weave.log({
            f"{prefix}tokens_per_second": self.tokens_per_second,
            f"{prefix}latency_ms": self.latency_ms,
            f"{prefix}total_tokens": self.total_tokens,
            f"{prefix}prompt_tokens": self.prompt_tokens,
            f"{prefix}completion_tokens": self.completion_tokens,
            f"{prefix}ttft_ms": self.time_to_first_token_ms,
            f"{prefix}peak_memory_mb": self.peak_memory_mb
        })

@weave.op()
def log_benchmark_result(result: BenchmarkResult):
    """Log complete benchmark result to Weave."""

    # Log test metadata
    weave.log({
        "test/name": result.test_name,
        "model/name": result.model_name,
        "model/size": result.model_size,
        "model/backend": result.backend,
        "environment": result.environment
    })

    # Log summary statistics
    for metric_name, metric_stats in result.summary.items():
        if isinstance(metric_stats, dict):
            for stat_name, value in metric_stats.items():
                weave.log({f"summary/{metric_name}/{stat_name}": value})
        else:
            weave.log({f"summary/{metric_name}": metric_stats})

    # Log individual metrics
    for i, metric in enumerate(result.metrics):
        metric.log_to_weave(prefix=f"iteration_{i}/")
```

#### Structured Logging for LM Evaluation Harness Results

Integration with existing `lm-eval` usage (see `docs/dev_cli/lm-eval.md`):

```python
import weave
import json

@weave.op()
def log_lm_eval_results(task_name: str,
                        results_file: str,
                        model_config: dict):
    """
    Log LM Evaluation Harness results to Weave.

    Args:
        task_name: Name of evaluation task (e.g., "mmlu", "gsm8k")
        results_file: Path to lm-eval results JSON
        model_config: Model configuration dict
    """
    # Load results
    with open(results_file, 'r') as f:
        results = json.load(f)

    # Extract metrics based on task type
    task_results = results.get("results", {}).get(task_name, {})

    # Log all metrics with proper namespacing
    weave.log({
        "accuracy/task": task_name,
        "accuracy/model": model_config["model_name"],
        "accuracy/quantization": model_config["quantization"],
        **{f"accuracy/{k}": v for k, v in task_results.items()}
    })

    # Log task-specific details
    if "exact_match" in task_results:
        weave.log({"accuracy/exact_match": task_results["exact_match"]})
    if "acc" in task_results:
        weave.log({"accuracy/acc": task_results["acc"]})
```

#### Decision: Multi-Level Logging Strategy

**Recommended Pattern**:
1. **High-level operations**: Use `@weave.op()` decorator for automatic tracking
2. **Detailed metrics**: Use `weave.log()` for fine-grained performance data
3. **Model configs**: Use `weave.Model` for versioned configuration management
4. **Integration**: Extend existing `PerformanceMetrics` and `BenchmarkResult` with `.log_to_weave()` methods

**Rationale**:
- Preserves existing Lemonade metrics collection patterns
- Adds W&B Weave as optional logging backend
- Automatic versioning for reproducibility
- Minimal code changes to existing evaluation workflows

---

## 4. Dashboard Customization for Model Comparison

### Research Question
How to create custom views for side-by-side model comparison in W&B Weave dashboards?

### Findings

#### W&B Dashboard Architecture

W&B provides multiple dashboard types:
1. **Runs Table**: Tabular view of all runs with sortable/filterable columns
2. **Charts Panel**: Time-series, scatter plots, bar charts for metric visualization
3. **Parallel Coordinates**: Multi-dimensional comparison view
4. **Reports**: Shareable narrative documents with embedded visualizations

#### Custom Dashboard for Model Comparison

##### Option 1: Programmatic Dashboard Creation

```python
import wandb

# Initialize run
run = wandb.init(project="lemonade-ryzenai-evals")

# Log comparison table
comparison_data = wandb.Table(
    columns=[
        "model_name", "quantization", "moe_config",
        "tokens_per_second", "latency_ms", "accuracy", "memory_gb"
    ],
    data=[
        ["Llama-3.1-8B", "int4", "8x2", 125.3, 45.2, 0.847, 12.3],
        ["Llama-3.1-8B", "int8", "8x2", 98.7, 58.1, 0.863, 18.7],
        ["Qwen3-80B", "int4", "16x2", 87.2, 68.4, 0.891, 24.5],
    ]
)

# Log table to dashboard
wandb.log({"model_comparison": comparison_data})

# Create custom charts
wandb.log({
    "charts/tps_vs_accuracy": wandb.plot.scatter(
        comparison_data,
        x="tokens_per_second",
        y="accuracy",
        title="TPS vs Accuracy Trade-off"
    ),
    "charts/memory_by_quantization": wandb.plot.bar(
        comparison_data,
        label="quantization",
        value="memory_gb",
        title="Memory Usage by Quantization Level"
    )
})
```

##### Option 2: Web UI Configuration

Dashboard panels can be configured via W&B web interface:
- **Grouped Bar Charts**: Compare metrics across model families
- **Scatter Plots**: Visualize trade-offs (e.g., latency vs accuracy)
- **Parallel Coordinates**: Multi-dimensional comparison of configurations
- **Run Comparer**: Side-by-side comparison of specific runs

#### Recommended Dashboard Layout for Lemonade

```
┌─────────────────────────────────────────────────────────────┐
│ Model Comparison Dashboard - Lemonade Ryzen AI Evaluations │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ FILTERS                                                       │
│ Model Family: [All | Llama | Qwen | Phi | ...]              │
│ Quantization: [All | INT4 | INT8 | FP16 | ...]              │
│ Device: [All | NPU | iGPU | CPU | Hybrid | ...]             │
│ Benchmark: [All | MMLU | GSM8K | HumanEval | ...]           │
└──────────────────────────────────────────────────────────────┘

┌────────────────────────┬─────────────────────────────────────┐
│ Performance Overview   │  Accuracy Overview                  │
│                        │                                     │
│ [Grouped Bar Chart]    │  [Grouped Bar Chart]                │
│ TPS by Model/Quant     │  MMLU/GSM8K Scores by Model         │
└────────────────────────┴─────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ Latency Distribution (Box Plot)                              │
│ [Shows P50, P95, P99 latency across configurations]         │
└──────────────────────────────────────────────────────────────┘

┌────────────────────────┬─────────────────────────────────────┐
│ TPS vs Accuracy        │  Memory vs Latency                  │
│                        │                                     │
│ [Scatter Plot]         │  [Scatter Plot]                     │
│ Color by quantization  │  Color by model family              │
└────────────────────────┴─────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ Detailed Results Table                                        │
│ [Sortable/Filterable Table with all metrics]                │
└──────────────────────────────────────────────────────────────┘
```

##### Implementation Pattern

```python
import weave
import wandb

class ModelComparisonDashboard:
    """Create and manage W&B dashboard for model comparisons."""

    def __init__(self, project_name: str):
        self.project_name = project_name
        weave.init(project_name)

    @weave.op()
    def create_comparison_table(self, results: List[BenchmarkResult]):
        """Create comparison table from benchmark results."""

        table_data = []
        for result in results:
            row = [
                result.model_name,
                result.model_size,
                result.backend,
                result.summary["tokens_per_second"]["mean"],
                result.summary["latency_ms"]["p95"],
                result.summary.get("accuracy", {}).get("mean", "N/A"),
                result.summary.get("peak_memory_mb", {}).get("max", "N/A")
            ]
            table_data.append(row)

        table = wandb.Table(
            columns=[
                "Model", "Size", "Backend",
                "TPS (mean)", "Latency P95 (ms)",
                "Accuracy", "Peak Memory (MB)"
            ],
            data=table_data
        )

        wandb.log({"model_comparison_table": table})
        return table

    @weave.op()
    def create_performance_charts(self, table: wandb.Table):
        """Create performance visualization charts."""

        # TPS comparison
        wandb.log({
            "charts/tps_by_model": wandb.plot.bar(
                table,
                label="Model",
                value="TPS (mean)",
                title="Tokens Per Second by Model"
            )
        })

        # Latency vs Accuracy scatter
        wandb.log({
            "charts/latency_vs_accuracy": wandb.plot.scatter(
                table,
                x="Latency P95 (ms)",
                y="Accuracy",
                title="Latency vs Accuracy Trade-off"
            )
        })

        # Memory usage
        wandb.log({
            "charts/memory_by_backend": wandb.plot.bar(
                table,
                label="Backend",
                value="Peak Memory (MB)",
                title="Peak Memory by Backend"
            )
        })
```

#### Decision: Hybrid Dashboard Approach

**Recommended Strategy**:
1. **Programmatic creation** of comparison tables and standard charts
2. **Web UI customization** for advanced visualizations and layout
3. **Report generation** for shareable comparison summaries

**Rationale**:
- Programmatic approach ensures reproducibility and automation
- Web UI provides flexibility for ad-hoc exploration
- Reports enable stakeholder sharing (addresses User Story 3 - P3)

---

## 5. Grouping and Tagging Strategies

### Research Question
What are effective strategies for organizing evaluation runs by model family, quantization level, benchmark suite, and other dimensions?

### Findings

#### W&B Grouping Mechanisms

W&B provides multiple ways to organize runs:

1. **Tags**: Free-form labels for filtering
2. **Groups**: Hierarchical organization of related runs
3. **Job Types**: Categorical labels for different workflows
4. **Config Parameters**: Structured configuration data for filtering
5. **Custom Metadata**: Additional key-value pairs

#### Recommended Tagging Schema for Lemonade

```python
import weave
import wandb

@weave.op()
def log_evaluation_with_tags(
    model_config: dict,
    benchmark_suite: str,
    results: BenchmarkResult
):
    """
    Log evaluation with comprehensive tagging strategy.

    Tags organized by:
    - Model family (e.g., "llama", "qwen", "phi")
    - Quantization level (e.g., "int4", "int8", "fp16")
    - Backend (e.g., "oga-npu", "llamacpp-cpu")
    - Benchmark suite (e.g., "mmlu", "gsm8k")
    - Hardware platform (e.g., "ryzen-ai-max-395")
    """

    # Extract model family from model name
    model_family = extract_model_family(model_config["model_name"])

    # Create hierarchical group name
    group_name = f"{model_family}/{model_config['quantization']}/{benchmark_suite}"

    # Create job type
    job_type = f"{benchmark_suite}_evaluation"

    # Initialize run with metadata
    run = wandb.init(
        project="lemonade-ryzenai-evals",
        name=f"{model_config['model_name']}_{benchmark_suite}_{timestamp()}",
        group=group_name,
        job_type=job_type,
        tags=[
            f"model:{model_family}",
            f"quant:{model_config['quantization']}",
            f"backend:{model_config['backend']}",
            f"device:{model_config['device']}",
            f"benchmark:{benchmark_suite}",
            f"hardware:ryzen-ai",
        ],
        config={
            "model_name": model_config["model_name"],
            "model_family": model_family,
            "quantization": model_config["quantization"],
            "moe_config": model_config.get("moe_config"),
            "backend": model_config["backend"],
            "device": model_config["device"],
            "benchmark_suite": benchmark_suite,
            "hardware": {
                "cpu": "AMD Ryzen AI Max+ 395",
                "gpu": "AMD Radeon 8060S gfx1151",
                "vram_gb": 96
            }
        }
    )

    # Log metrics
    weave.log(asdict(results))

    wandb.finish()


def extract_model_family(model_name: str) -> str:
    """Extract model family from model name."""
    model_name_lower = model_name.lower()

    if "llama" in model_name_lower:
        return "llama"
    elif "qwen" in model_name_lower:
        return "qwen"
    elif "phi" in model_name_lower:
        return "phi"
    elif "mistral" in model_name_lower:
        return "mistral"
    else:
        return "other"
```

#### Filtering and Querying Patterns

```python
# Query runs programmatically via W&B API
import wandb

api = wandb.Api()

# Filter by tags
runs = api.runs(
    path="team/lemonade-ryzenai-evals",
    filters={
        "tags": {"$in": ["model:llama", "quant:int4"]},
        "state": "finished"
    }
)

# Filter by config parameters
runs = api.runs(
    path="team/lemonade-ryzenai-evals",
    filters={
        "config.quantization": "int4",
        "config.benchmark_suite": "mmlu"
    }
)

# Group comparison query
runs_by_group = {}
for run in runs:
    group = run.group
    if group not in runs_by_group:
        runs_by_group[group] = []
    runs_by_group[group].append(run)
```

#### Hierarchical Organization Schema

```
Project: lemonade-ryzenai-evals
│
├─ Group: llama/int4/mmlu
│  ├─ Run: Llama-3.1-8B_mmlu_20251224_120000
│  ├─ Run: Llama-3.1-70B_mmlu_20251224_120500
│  └─ ...
│
├─ Group: llama/int8/mmlu
│  ├─ Run: Llama-3.1-8B_mmlu_20251224_121000
│  └─ ...
│
├─ Group: qwen/int4/gsm8k
│  ├─ Run: Qwen3-80B_gsm8k_20251224_122000
│  └─ ...
│
└─ Group: phi/fp16/humaneval
   ├─ Run: Phi-3.5-mini_humaneval_20251224_123000
   └─ ...
```

#### Dashboard Filtering with Tags

W&B dashboard UI supports tag-based filtering:
- Filter runs by multiple tags (AND/OR logic)
- Group visualization by tag category
- Create saved views for common filter combinations

Example saved views:
- "All INT4 Models" (tag: `quant:int4`)
- "NPU Benchmarks" (tag: `device:npu`)
- "MMLU Accuracy Comparison" (tag: `benchmark:mmlu`)
- "Llama Family Performance" (tag: `model:llama`)

#### Decision: Comprehensive Tagging with Hierarchical Groups

**Recommended Strategy**:
1. **Hierarchical groups**: `{model_family}/{quantization}/{benchmark_suite}`
2. **Tag schema**: Prefix-based tags for each dimension (e.g., `model:`, `quant:`, `device:`)
3. **Config parameters**: Store all configuration as structured data for programmatic filtering
4. **Job types**: Use benchmark suite name as job type

**Rationale**:
- Hierarchical groups enable drill-down navigation
- Prefix-based tags prevent tag namespace collision
- Config parameters support complex queries
- Multiple indexing dimensions support different comparison workflows

---

## 6. Integration Architecture

### Recommended Implementation Pattern

Based on existing Lemonade architecture analysis:

```
src/lemonade/
├── evaluation/              # NEW: Evaluation orchestration
│   ├── __init__.py
│   ├── config.py            # Evaluation configuration management
│   ├── runners.py           # Evaluation run orchestration
│   ├── wandb_logger.py      # W&B Weave integration (NEW)
│   └── harness.py           # LM Eval Harness wrapper
│
├── profilers/               # EXISTING: Extend with W&B support
│   ├── profiler.py
│   ├── memory_tracker.py
│   └── wandb_profiler.py    # NEW: W&B as profiler backend
│
└── cli/
    └── evaluate.py          # NEW: CLI commands for evaluations
```

#### Core Integration Points

##### 1. Extend MetricsCollector with W&B Backend

```python
# src/lemonade/evaluation/wandb_logger.py

from tests.rocm_max395.utils.metrics_collector import (
    MetricsCollector,
    PerformanceMetrics,
    BenchmarkResult
)
import weave
import wandb
from typing import Optional

class WandbMetricsCollector(MetricsCollector):
    """Metrics collector with W&B Weave logging."""

    def __init__(self,
                 project_name: str,
                 offline: bool = False,
                 entity: Optional[str] = None):
        super().__init__()

        # Initialize Weave
        self.project_name = project_name
        self.entity = entity
        self.offline = offline

        if offline:
            import os
            os.environ["WANDB_MODE"] = "offline"

        weave.init(f"{entity}/{project_name}" if entity else project_name)

    @weave.op()
    def create_benchmark_result(self, *args, **kwargs):
        """Override to add W&B logging."""
        result = super().create_benchmark_result(*args, **kwargs)
        self._log_to_weave(result)
        return result

    def _log_to_weave(self, result: BenchmarkResult):
        """Log benchmark result to W&B Weave."""
        # Log metadata
        weave.log({
            "test/name": result.test_name,
            "model/name": result.model_name,
            "model/size": result.model_size,
            "model/backend": result.backend
        })

        # Log summary statistics
        for metric_name, metric_stats in result.summary.items():
            if isinstance(metric_stats, dict):
                for stat_name, value in metric_stats.items():
                    weave.log({f"summary/{metric_name}/{stat_name}": value})
```

##### 2. CLI Integration

```python
# src/lemonade/cli/evaluate.py

import argparse
from lemonade.evaluation.wandb_logger import WandbMetricsCollector

def add_wandb_arguments(parser: argparse.ArgumentParser):
    """Add W&B-specific arguments to CLI parser."""
    wandb_group = parser.add_argument_group('W&B Weave Options')

    wandb_group.add_argument(
        '--wandb-project',
        type=str,
        default='lemonade-ryzenai-evals',
        help='W&B project name (default: lemonade-ryzenai-evals)'
    )

    wandb_group.add_argument(
        '--wandb-entity',
        type=str,
        default=None,
        help='W&B team/entity name (optional)'
    )

    wandb_group.add_argument(
        '--wandb-offline',
        action='store_true',
        help='Run W&B in offline mode (sync later)'
    )

    wandb_group.add_argument(
        '--wandb-tags',
        nargs='+',
        default=[],
        help='Additional tags for W&B run'
    )

# Usage in evaluation command
def evaluate_command(args):
    """Run evaluation with W&B logging."""

    # Create metrics collector with W&B backend
    collector = WandbMetricsCollector(
        project_name=args.wandb_project,
        entity=args.wandb_entity,
        offline=args.wandb_offline
    )

    # Run evaluation
    # ... existing evaluation logic ...
```

---

## 7. Technology Decisions Summary

### Resolved Research Questions

| Research Question | Decision | Rationale |
|-------------------|----------|-----------|
| **Initialization Pattern** | Hybrid: One-time project init + per-run decorators | Balances overhead with granular tracking |
| **Offline Mode Support** | Support both online and offline via environment variables | Enables offline hardware testing with later sync |
| **Logging Pattern** | Multi-level: `@weave.op()` + `weave.log()` + `weave.Model` | Automatic versioning + explicit custom metrics |
| **Dashboard Strategy** | Programmatic + Web UI customization | Reproducibility + flexibility |
| **Grouping/Tagging** | Hierarchical groups + prefix-based tags + config params | Multiple filtering dimensions for complex queries |

### Key Dependencies

```txt
# requirements.txt additions
wandb>=0.18.0
weave>=0.51.0
lm-eval>=0.4.0
```

### Configuration File Schema

```yaml
# config/wandb_evaluation.yaml
wandb:
  project: "lemonade-ryzenai-evals"
  entity: null  # Optional team name
  offline: false
  sync_interval: 300  # seconds (for periodic sync in offline mode)

evaluation:
  benchmarks:
    - name: "mmlu"
      limit: null  # Full dataset
      tasks:
        - "mmlu_abstract_algebra"
        - "mmlu_anatomy"
        # ... more tasks
    - name: "gsm8k"
      limit: 100  # Quick test

  models:
    - name: "Llama-3.1-8B-Instruct"
      quantizations: ["int4", "int8", "fp16"]
      backends: ["oga"]
      devices: ["npu", "igpu", "cpu"]

    - name: "Qwen3-80B-A3B-Instruct"
      quantizations: ["int4"]
      backends: ["oga", "llamacpp"]
      devices: ["hybrid"]
      moe_config:
        num_experts: 16
        experts_per_token: 2
```

---

## 8. Next Steps

### Phase 1: Design Artifacts

Based on this research, proceed to create:

1. **data-model.md**: Define entities (EvaluationRun, ModelConfig, BenchmarkResult, ComparisonSet)
2. **contracts/wandb-schema.yaml**: W&B logging schema and tag conventions
3. **contracts/evaluation-config.schema.json**: JSON schema for evaluation configuration
4. **quickstart.md**: Getting started guide with examples

### Phase 2: Implementation Tasks

After Phase 1 design, use `/speckit.tasks` to generate:
- Implement `WandbMetricsCollector` class
- Create CLI commands for W&B-enabled evaluation
- Add offline mode support and sync utilities
- Create dashboard templates and visualization utilities
- Write integration tests for W&B logging
- Document W&B Weave setup and authentication

---

## References

### W&B Weave Documentation
- Weave Python SDK: https://wandb.github.io/weave/
- W&B Evaluations Guide: https://docs.wandb.ai/guides/evaluation
- Offline Mode Documentation: https://docs.wandb.ai/guides/track/tracking-faq#offline-mode
- Dashboard Customization: https://docs.wandb.ai/guides/app/features/custom-charts

### Existing Lemonade Patterns
- `tests/rocm_max395/utils/metrics_collector.py`: Metrics collection patterns
- `src/lemonade/tools/bench.py`: Benchmarking infrastructure
- `docs/dev_cli/lm-eval.md`: LM Evaluation Harness integration
- `src/lemonade/profilers/`: Profiler architecture patterns

### LM Evaluation Harness
- GitHub Repository: https://github.com/EleutherAI/lm-evaluation-harness
- Task Documentation: https://github.com/EleutherAI/lm-evaluation-harness/tree/main/docs

---

**Research Complete**: Ready to proceed to Phase 1 design artifacts.
