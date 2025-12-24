"""
W&B Weave integration for evaluation metrics logging.

This module provides W&B Weave integration extending the existing MetricsCollector
pattern for LLM model comparison on AMD Ryzen AI hardware.
"""

import os
import time
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import json

try:
    import weave
    WEAVE_AVAILABLE = True
except ImportError:
    WEAVE_AVAILABLE = False
    weave = None

try:
    import wandb
    WANDB_AVAILABLE = True
except ImportError:
    WANDB_AVAILABLE = False
    wandb = None

# Conditional decorator
def weave_op(func):
    """Conditional weave.op() decorator."""
    if WEAVE_AVAILABLE:
        return weave.op()(func)
    return func

from .models import (
    EvaluationRun, ModelConfiguration, BenchmarkResult,
    PerformanceMetrics, ResourceMetrics, AccuracyMetrics,
    HardwarePlatform, RunStatus
)


class WandbMetricsCollector:
    """
    W&B Weave integration for collecting and logging evaluation metrics.

    Extends the existing MetricsCollector pattern with W&B Weave logging
    capabilities for LLM model comparison workflows.
    """

    def __init__(self,
                 project_name: str = "lemonade-ryzenai-evals",
                 entity: Optional[str] = None,
                 offline: bool = False):
        """
        Initialize W&B Weave project.

        Args:
            project_name: W&B project name for organizing evaluations
            entity: W&B team/organization name (optional)
            offline: Whether to run in offline mode
        """
        if not WEAVE_AVAILABLE:
            raise ImportError("weave package is required for WandbMetricsCollector")

        self.project_name = project_name
        self.entity = entity
        self.offline = offline
        self.weave_client = None
        self.wandb_run = None
        self.current_evaluation_run = None

        # Initialize Weave project
        self._init_weave()

    def _init_weave(self) -> None:
        """Initialize W&B Weave project."""
        if self.offline:
            os.environ["WANDB_MODE"] = "offline"

        try:
            project_path = f"{self.entity}/{self.project_name}" if self.entity else self.project_name
            weave.init(project_path)
            self.weave_client = weave
        except Exception as e:
            raise RuntimeError(f"Failed to initialize W&B Weave: {e}")

    def start_evaluation_run(self,
                           evaluation_run: EvaluationRun,
                           model_config: ModelConfiguration) -> None:
        """
        Start a new evaluation run with W&B tracking.

        Args:
            evaluation_run: The evaluation run entity
            model_config: The model configuration being evaluated
        """
        if not WANDB_AVAILABLE:
            raise ImportError("wandb package is required for evaluation runs")

        self.current_evaluation_run = evaluation_run

        # Create W&B run with hierarchical grouping
        group = f"{model_config.model_family}/{model_config.quantization}/{evaluation_run.benchmark_suite}"
        job_type = f"{evaluation_run.benchmark_suite}_evaluation"

        # Generate tags following schema
        tags = [
            f"model:{model_config.model_family}",
            f"quant:{model_config.quantization}",
            f"backend:{evaluation_run.backend}",
            f"device:{evaluation_run.hardware_platform.npu or evaluation_run.hardware_platform.gpu or 'cpu'}",
            f"benchmark:{evaluation_run.benchmark_suite}",
            "hardware:ryzen-ai"
        ]

        # Config data for W&B
        config = {
            "model_name": model_config.model_name,
            "model_family": model_config.model_family,
            "checkpoint": model_config.checkpoint,
            "quantization": model_config.quantization,
            "moe_config": model_config.moe_config.dict() if model_config.moe_config else None,
            "backend": evaluation_run.backend,
            "benchmark_suite": evaluation_run.benchmark_suite,
            "hardware": {
                "cpu": evaluation_run.hardware_platform.cpu,
                "gpu": evaluation_run.hardware_platform.gpu,
                "npu": evaluation_run.hardware_platform.npu,
                "architecture": evaluation_run.hardware_platform.architecture,
                "vram_gb": evaluation_run.hardware_platform.total_vram_gb,
                "system_ram_gb": evaluation_run.hardware_platform.system_ram_gb,
                "os": evaluation_run.hardware_platform.os,
                "driver_version": evaluation_run.hardware_platform.driver_version,
            }
        }

        try:
            self.wandb_run = wandb.init(
                project=self.project_name,
                name=evaluation_run.name,
                group=group,
                job_type=job_type,
                tags=tags,
                config=config,
                entity=self.entity
            )

            # Update evaluation run with W&B URL
            if self.wandb_run.url:
                evaluation_run.wandb_run_url = self.wandb_run.url

        except Exception as e:
            # Continue without W&B if initialization fails
            print(f"Warning: Failed to initialize W&B run: {e}")
            self.wandb_run = None

    @weave_op
    def log_benchmark_result(self,
                           benchmark_result: BenchmarkResult,
                           task_name: str = None) -> None:
        """
        Log a benchmark result to W&B Weave.

        Args:
            benchmark_result: The benchmark result to log
            task_name: Specific task name (overrides benchmark_result.task_name)
        """
        if not self.weave_client:
            return

        task = task_name or benchmark_result.task_name

        # Prepare metrics for logging
        metrics = {
            "test/name": task,
            "model/name": self.current_evaluation_run.name if self.current_evaluation_run else "unknown",
            "model/size_gb": benchmark_result.performance_metrics.total_tokens / 1e9 if benchmark_result.performance_metrics.total_tokens else 0,
            "model/backend": self.current_evaluation_run.backend if self.current_evaluation_run else "unknown",
        }

        # Performance metrics
        perf = benchmark_result.performance_metrics
        metrics.update({
            "perf/tokens_per_second": perf.tokens_per_second,
            "perf/latency_ms": perf.latency_ms,
            "perf/latency_p50_ms": perf.latency_p50_ms,
            "perf/latency_p95_ms": perf.latency_p95_ms,
            "perf/latency_p99_ms": perf.latency_p99_ms,
            "perf/time_to_first_token_ms": perf.time_to_first_token_ms,
            "perf/total_tokens": perf.total_tokens,
            "perf/prompt_tokens": perf.prompt_tokens,
            "perf/completion_tokens": perf.completion_tokens,
        })

        # Resource metrics
        res = benchmark_result.resource_metrics
        metrics.update({
            "resources/peak_memory_mb": res.peak_memory_mb,
            "resources/avg_memory_mb": res.avg_memory_mb,
            "resources/vram_usage_mb": res.vram_usage_mb,
            "resources/cpu_utilization_percent": res.cpu_utilization_percent,
            "resources/gpu_utilization_percent": res.gpu_utilization_percent,
            "resources/power_consumption_watts": res.power_consumption_watts,
        })

        # Accuracy metrics (if available)
        if benchmark_result.accuracy_metrics:
            acc = benchmark_result.accuracy_metrics
            metrics.update({
                "accuracy/acc": acc.acc,
                "accuracy/acc_stderr": acc.acc_stderr,
                "accuracy/exact_match": acc.exact_match,
                "accuracy/f1": acc.f1,
            })

        # Log to W&B Weave
        try:
            if self.wandb_run:
                self.wandb_run.log(metrics)
        except Exception as e:
            print(f"Warning: Failed to log metrics to W&B: {e}")

    @weave_op
    def log_evaluation_summary(self,
                             evaluation_run: EvaluationRun,
                             benchmark_results: List[BenchmarkResult]) -> None:
        """
        Log evaluation summary statistics.

        Args:
            evaluation_run: The completed evaluation run
            benchmark_results: All benchmark results from the run
        """
        if not benchmark_results:
            return

        # Calculate summary statistics
        summary_metrics = self._calculate_summary_metrics(benchmark_results)

        # Log summary to W&B
        try:
            if self.wandb_run:
                self.wandb_run.log(summary_metrics)

            # Log to W&B run summary if available
            if self.wandb_run:
                self.wandb_run.summary.update(summary_metrics)

        except Exception as e:
            print(f"Warning: Failed to log summary to W&B: {e}")

    def _calculate_summary_metrics(self, results: List[BenchmarkResult]) -> Dict[str, Any]:
        """Calculate summary statistics across all benchmark results."""
        if not results:
            return {}

        # Aggregate performance metrics
        tokens_per_second_values = [r.performance_metrics.tokens_per_second for r in results]
        latency_values = [r.performance_metrics.latency_ms for r in results]

        summary = {
            "summary/tokens_per_second/mean": sum(tokens_per_second_values) / len(tokens_per_second_values),
            "summary/latency_ms/p95": sorted(latency_values)[int(len(latency_values) * 0.95)],
            "summary/accuracy/mean": None,  # Will be calculated if accuracy metrics exist
        }

        # Calculate accuracy summary if available
        accuracy_values = []
        for result in results:
            if result.accuracy_metrics and result.accuracy_metrics.acc is not None:
                accuracy_values.append(result.accuracy_metrics.acc)

        if accuracy_values:
            summary["summary/accuracy/mean"] = sum(accuracy_values) / len(accuracy_values)

        return summary

    def update_run_status(self, status: RunStatus, error_message: str = None) -> None:
        """
        Update the evaluation run status.

        Args:
            status: New run status
            error_message: Error message if status is FAILED
        """
        if self.current_evaluation_run:
            self.current_evaluation_run.status = status
            if error_message:
                self.current_evaluation_run.error_message = error_message

            # Update timestamps
            now = time.time()
            if status == RunStatus.RUNNING:
                self.current_evaluation_run.started_at = now
            elif status in [RunStatus.COMPLETED, RunStatus.FAILED]:
                self.current_evaluation_run.completed_at = now

    def finish_evaluation_run(self) -> None:
        """Finish the current evaluation run and clean up W&B resources."""
        if self.wandb_run:
            try:
                self.wandb_run.finish()
            except Exception as e:
                print(f"Warning: Failed to finish W&B run: {e}")
            finally:
                self.wandb_run = None

        self.current_evaluation_run = None

    def sync_offline_data(self) -> None:
        """Sync offline W&B data if in offline mode."""
        if self.offline and WANDB_AVAILABLE:
            try:
                os.system("wandb sync --sync-all")
            except Exception as e:
                print(f"Warning: Failed to sync offline data: {e}")

    def export_results(self, filepath: Path, format: str = "json") -> None:
        """
        Export evaluation results to file.

        Args:
            filepath: Path to export file
            format: Export format ('json' or 'yaml')
        """
        if not self.current_evaluation_run:
            raise ValueError("No active evaluation run to export")

        data = {
            "evaluation_run": self.current_evaluation_run.dict(),
            "export_timestamp": time.time(),
            "format": format
        }

        filepath.parent.mkdir(parents=True, exist_ok=True)

        if format == "json":
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        else:
            # YAML export would require pyyaml
            raise NotImplementedError("YAML export not yet implemented")