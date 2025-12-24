"""
Evaluation runners for orchestrating benchmark execution.

This module provides classes for running evaluation workflows,
coordinating between models, benchmarks, and metrics collection.
"""

import time
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from .models import EvaluationRun, ModelConfiguration, BenchmarkResult, RunStatus
from .wandb_logger import WandbMetricsCollector
from .harness import LMEvalHarness
from .logging_config import get_evaluation_logger, log_evaluation_start, log_evaluation_complete, log_benchmark_start, log_benchmark_complete, log_error

try:
    import weave
    WEAVE_AVAILABLE = True
except ImportError:
    WEAVE_AVAILABLE = False
    weave = None

# Conditional decorator
def weave_op(func):
    """Conditional weave.op() decorator."""
    if WEAVE_AVAILABLE:
        return weave.op()(func)
    return func


class EvaluationRunner:
    """
    Orchestrates evaluation workflow execution.

    Coordinates model loading, benchmark execution, metrics collection,
    and result logging for comprehensive LLM evaluation.
    """

    def __init__(self,
                 wandb_collector: Optional[WandbMetricsCollector] = None,
                 lm_harness: Optional[LMEvalHarness] = None,
                 max_concurrent: int = 1):
        """
        Initialize evaluation runner.

        Args:
            wandb_collector: W&B metrics collector (optional)
            lm_harness: LM Evaluation Harness wrapper (optional)
            max_concurrent: Maximum concurrent benchmark executions
        """
        self.wandb_collector = wandb_collector
        self.lm_harness = lm_harness
        self.max_concurrent = max_concurrent
        self.logger = get_evaluation_logger()

    @weave_op
    def run_evaluation(self,
                      evaluation_run: EvaluationRun,
                      model_config: ModelConfiguration,
                      benchmark_tasks: List[str] = None) -> List[BenchmarkResult]:
        """
        Run complete evaluation workflow.

        Args:
            evaluation_run: The evaluation run configuration
            model_config: Model configuration to evaluate
            benchmark_tasks: List of benchmark tasks to run (optional)

        Returns:
            List of benchmark results
        """
        start_time = time.time()
        log_evaluation_start(evaluation_run.run_id, model_config.model_name, evaluation_run.benchmark_suite)

        # Update run status to running
        evaluation_run.status = RunStatus.RUNNING
        evaluation_run.started_at = start_time
        if self.wandb_collector:
            self.wandb_collector.update_run_status(RunStatus.RUNNING)

        try:
            # Initialize W&B run if collector available
            if self.wandb_collector:
                self.wandb_collector.start_evaluation_run(evaluation_run, model_config)

            # Determine benchmark tasks to run
            if not benchmark_tasks:
                benchmark_tasks = self._get_default_benchmark_tasks(evaluation_run.benchmark_suite)

            # Run benchmarks
            results = self._run_benchmarks(evaluation_run, model_config, benchmark_tasks)

            # Log evaluation summary
            if self.wandb_collector and results:
                self.wandb_collector.log_evaluation_summary(evaluation_run, results)

            # Update run status to completed
            evaluation_run.status = RunStatus.COMPLETED
            evaluation_run.completed_at = time.time()
            if self.wandb_collector:
                self.wandb_collector.update_run_status(RunStatus.COMPLETED)

            duration = time.time() - start_time
            log_evaluation_complete(evaluation_run.run_id, "completed", duration)

            return results

        except Exception as e:
            # Update run status to failed
            evaluation_run.status = RunStatus.FAILED
            evaluation_run.error_message = str(e)
            evaluation_run.completed_at = time.time()
            if self.wandb_collector:
                self.wandb_collector.update_run_status(RunStatus.FAILED, str(e))

            duration = time.time() - start_time
            log_evaluation_complete(evaluation_run.run_id, "failed", duration)
            log_error(evaluation_run.run_id, "evaluation_failed", str(e))

            raise

        finally:
            # Finish W&B run
            if self.wandb_collector:
                self.wandb_collector.finish_evaluation_run()

    def _run_benchmarks(self,
                       evaluation_run: EvaluationRun,
                       model_config: ModelConfiguration,
                       benchmark_tasks: List[str]) -> List[BenchmarkResult]:
        """
        Run benchmark tasks for the evaluation.

        Args:
            evaluation_run: The evaluation run
            model_config: Model configuration
            benchmark_tasks: List of benchmark task names

        Returns:
            List of benchmark results
        """
        results = []

        if self.max_concurrent == 1:
            # Sequential execution
            for task in benchmark_tasks:
                result = self._run_single_benchmark(evaluation_run, model_config, task)
                if result:
                    results.append(result)
        else:
            # Parallel execution
            with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
                futures = [
                    executor.submit(self._run_single_benchmark, evaluation_run, model_config, task)
                    for task in benchmark_tasks
                ]

                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        results.append(result)

        return results

    @weave_op
    def _run_single_benchmark(self,
                             evaluation_run: EvaluationRun,
                             model_config: ModelConfiguration,
                             task_name: str) -> Optional[BenchmarkResult]:
        """
        Run a single benchmark task.

        Args:
            evaluation_run: The evaluation run
            model_config: Model configuration
            task_name: Name of the benchmark task

        Returns:
            Benchmark result or None if failed
        """
        log_benchmark_start(evaluation_run.run_id, task_name)

        try:
            if not self.lm_harness:
                raise RuntimeError("LM Evaluation Harness not configured")

            # Run the benchmark
            result = self.lm_harness.run_benchmark(
                task_name=task_name,
                model_name=model_config.model_name
            )

            # Set run and result IDs
            if result:
                result.run_id = evaluation_run.run_id
                result.result_id = f"{evaluation_run.run_id}_{task_name}"

                # Log to W&B if available
                if self.wandb_collector:
                    self.wandb_collector.log_benchmark_result(result, task_name)

                log_benchmark_complete(evaluation_run.run_id, task_name, {
                    "accuracy": result.accuracy_metrics.acc if result.accuracy_metrics else None,
                    "tokens_per_second": result.performance_metrics.tokens_per_second,
                    "latency_ms": result.performance_metrics.latency_ms
                })

            return result

        except Exception as e:
            log_error(evaluation_run.run_id, "benchmark_failed", f"{task_name}: {str(e)}")
            self.logger.error(f"Benchmark {task_name} failed: {e}")
            return None

    def _get_default_benchmark_tasks(self, benchmark_suite: str) -> List[str]:
        """
        Get default benchmark tasks for a suite.

        Args:
            benchmark_suite: Name of the benchmark suite

        Returns:
            List of task names
        """
        if benchmark_suite.lower() == "mmlu":
            return ["mmlu_abstract_algebra", "mmlu_anatomy", "mmlu_astronomy"]
        elif benchmark_suite.lower() == "hellaswag":
            return ["hellaswag"]
        else:
            return [benchmark_suite]

    def run_multiple_evaluations(self,
                                evaluations: List[tuple]) -> Dict[str, List[BenchmarkResult]]:
        """
        Run multiple evaluations sequentially.

        Args:
            evaluations: List of (evaluation_run, model_config, benchmark_tasks) tuples

        Returns:
            Dictionary mapping run IDs to results
        """
        results = {}

        for evaluation_run, model_config, benchmark_tasks in evaluations:
            try:
                run_results = self.run_evaluation(evaluation_run, model_config, benchmark_tasks)
                results[evaluation_run.run_id] = run_results
            except Exception as e:
                self.logger.error(f"Evaluation {evaluation_run.run_id} failed: {e}")
                results[evaluation_run.run_id] = []

        return results