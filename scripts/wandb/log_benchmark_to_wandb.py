#!/usr/bin/env python3
"""Log a benchmark results JSON file to W&B (offline) and create a basic Weave/W&B view."""
import json
import os
from pathlib import Path
from datetime import datetime

from lemonade.evaluation.wandb_logger import WandbMetricsCollector
from lemonade.evaluation.models import (
    EvaluationRun, ModelConfiguration, HardwarePlatform,
    BenchmarkResult, PerformanceMetrics, ResourceMetrics, AccuracyMetrics
)

INPUT_DIR = Path("evaluation_results_large")
# pick the most recent file
files = sorted(INPUT_DIR.glob('large_benchmark_*.json'))
if not files:
    raise SystemExit("No benchmark result files found in evaluation_results_large/")

filepath = files[-1]
with open(filepath, 'r', encoding='utf-8') as f:
    data = json.load(f)

summary = data.get('summary', {})
results = data.get('results', [])

# Create evaluation run and model config
from uuid import uuid4

run_id = str(uuid4())
eval_name = summary.get('model', 'model') + " - quick large benchmark"

hardware = HardwarePlatform(
    platform_name="AMD Ryzen AI Max+ 395",
    cpu="AMD Ryzen AI 9 395",
    gpu=None,
    npu="AMD Ryzen AI NPU",
    architecture="gfx1151",
    total_vram_gb=32,
    system_ram_gb=128,
    os="Windows 11",
    driver_version="ROCm"
)

model_name_val = summary.get('model', 'unknown')
model_config = ModelConfiguration(
    model_name=model_name_val,
    model_family="llama",
    checkpoint=f"llama/{model_name_val}:model",
    quantization="fp16",
    size_gb=15.0,
    context_length=8192
)

evaluation_run = EvaluationRun(
    run_id=run_id,
    name=eval_name,
    benchmark_suite="custom_quick",
    backend="oga",
    hardware_platform=hardware,
    model_config_id=str(model_config.config_id),
)

# Initialize W&B collector in offline mode
wandb_collector = WandbMetricsCollector(project_name="lemonade-ryzenai-evals-demo", offline=True)
wandb_collector.start_evaluation_run(evaluation_run, model_config)

# Collect benchmark results and log
br_list = []
for idx, r in enumerate(results, 1):
    perf = PerformanceMetrics(
        tokens_per_second=r.get('tokens_per_second', r.get('total_tokens', 0) / (r.get('latency_ms', 1)/1000.0) if r.get('latency_ms') else 0.0),
        latency_ms=r.get('latency_ms', 0.0),
        latency_p50_ms=None,
        latency_p95_ms=None,
        latency_p99_ms=None,
        time_to_first_token_ms=None,
        total_tokens=r.get('total_tokens', 0),
        prompt_tokens=r.get('prompt_tokens', 0),
        completion_tokens=r.get('completion_tokens', 0)
    )

    resm = ResourceMetrics(
        peak_memory_mb=1.0,
        avg_memory_mb=1.0,
        vram_usage_mb=1.0,
        cpu_utilization_percent=0.0,
        gpu_utilization_percent=0.0,
        power_consumption_watts=1.0
    )

    from uuid import uuid4
    bm = BenchmarkResult(
        result_id=str(uuid4()),
        run_id=run_id,
        task_name=r.get('prompt')[:120],
        benchmark_suite="custom_quick",
        accuracy_metrics=None,
        performance_metrics=perf,
        resource_metrics=resm,
        sample_count=1,
        timestamp=datetime.utcnow().timestamp()
    )

    wandb_collector.log_benchmark_result(bm)
    br_list.append(bm)

# Log summary
wandb_collector.log_evaluation_summary(evaluation_run, br_list)

# Also log raw results as an artifact/table if wandb run exists
if wandb_collector.wandb_run:
    try:
        import wandb
        # Create a simple table
        table = wandb.Table(columns=["index", "prompt", "status", "latency_ms", "total_tokens", "tps"])
        for r in results:
            table.add_data(r.get('index'), r.get('prompt')[:200], r.get('status'), r.get('latency_ms'), r.get('total_tokens'), r.get('tokens_per_second'))
        wandb_collector.wandb_run.log({"benchmark_table": table})
    except Exception as e:
        print(f"Warning: failed to log table to wandb: {e}")

# Finish run
wandb_collector.finish_evaluation_run()
print(f"Logged {len(br_list)} benchmark samples to W&B offline run. W&B files saved under ./wandb/.")
print(f"Local results file: {filepath}")
print("You can run `wandb sync` to upload offline runs to the cloud if desired.")
