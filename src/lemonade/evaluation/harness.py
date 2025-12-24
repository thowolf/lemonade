"""
LM Evaluation Harness wrapper for Lemonade SDK integration.

This module provides a wrapper around the LM Evaluation Harness library
for running accuracy benchmarks on LLM models served by Lemonade.
"""

import os
import json
import subprocess
import tempfile
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import time

try:
    import lm_eval
    LMEVAL_AVAILABLE = True
except ImportError:
    LMEVAL_AVAILABLE = False
    lm_eval = None

from .models import BenchmarkResult, AccuracyMetrics, PerformanceMetrics, ResourceMetrics


class LMEvalHarness:
    """
    Wrapper for LM Evaluation Harness integration with Lemonade Server.

    Provides methods to run standardized accuracy benchmarks against
    models served through Lemonade's API endpoints.
    """

    def __init__(self,
                 server_url: str = "http://localhost:8000",
                 timeout: int = 300,
                 max_concurrent: int = 1):
        """
        Initialize LM Eval Harness wrapper.

        Args:
            server_url: URL of the Lemonade server
            timeout: Timeout for evaluation requests (seconds)
            max_concurrent: Maximum concurrent evaluation requests
        """
        if not LMEVAL_AVAILABLE:
            raise ImportError("lm-eval package is required for LMEvalHarness")

        self.server_url = server_url.rstrip('/')
        self.timeout = timeout
        self.max_concurrent = max_concurrent

    def run_benchmark(self,
                     task_name: str,
                     model_name: str = "lemonade-model",
                     limit: Optional[int] = None,
                     num_fewshot: int = 0,
                     batch_size: int = 1) -> BenchmarkResult:
        """
        Run a single benchmark task.

        Args:
            task_name: Name of the benchmark task (e.g., 'mmlu', 'hellaswag')
            model_name: Name identifier for the model
            limit: Limit number of samples to evaluate
            num_fewshot: Number of few-shot examples to use
            batch_size: Batch size for evaluation

        Returns:
            BenchmarkResult with accuracy metrics
        """
        # Prepare LM Eval command
        cmd = [
            "lm_eval",
            "--model", "local-completions",
            "--model_args", f"url={self.server_url}/v1/completions,auth=none",
            "--tasks", task_name,
            "--batch_size", str(batch_size),
            "--output_path", "/tmp/lm_eval_results",  # Temporary output
            "--log_samples", "false",
            "--include_path", ".",  # Use current directory for custom tasks
        ]

        if limit:
            cmd.extend(["--limit", str(limit)])

        if num_fewshot > 0:
            cmd.extend(["--num_fewshot", str(num_fewshot)])

        # Run evaluation
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=os.getcwd()
            )

            if result.returncode != 0:
                raise RuntimeError(f"LM Eval failed: {result.stderr}")

            # Parse results
            return self._parse_lm_eval_output(result.stdout, task_name, model_name)

        except subprocess.TimeoutExpired:
            raise TimeoutError(f"Evaluation timed out after {self.timeout} seconds")
        except Exception as e:
            raise RuntimeError(f"Evaluation failed: {e}")

    def run_multiple_benchmarks(self,
                              task_names: List[str],
                              model_name: str = "lemonade-model",
                              limit: Optional[int] = None,
                              num_fewshot: int = 0) -> List[BenchmarkResult]:
        """
        Run multiple benchmark tasks.

        Args:
            task_names: List of benchmark task names
            model_name: Name identifier for the model
            limit: Limit number of samples per task
            num_fewshot: Number of few-shot examples to use

        Returns:
            List of BenchmarkResult objects
        """
        results = []

        for task_name in task_names:
            try:
                result = self.run_benchmark(
                    task_name=task_name,
                    model_name=model_name,
                    limit=limit,
                    num_fewshot=num_fewshot
                )
                results.append(result)
            except Exception as e:
                # Create failed result
                failed_result = BenchmarkResult(
                    result_id="",  # Will be set by caller
                    run_id="",     # Will be set by caller
                    task_name=task_name,
                    accuracy_metrics=None,
                    performance_metrics=PerformanceMetrics(
                        tokens_per_second=0.0,
                        latency_ms=0.0,
                        total_tokens=0,
                        prompt_tokens=0,
                        completion_tokens=0
                    ),
                    resource_metrics=ResourceMetrics(
                        peak_memory_mb=0.0,
                        cpu_utilization_percent=0.0
                    ),
                    timestamp=time.time()
                )
                results.append(failed_result)
                print(f"Warning: Benchmark {task_name} failed: {e}")

        return results

    def _parse_lm_eval_output(self, output: str, task_name: str, model_name: str) -> BenchmarkResult:
        """
        Parse LM Eval output and create BenchmarkResult.

        Args:
            output: Raw output from lm_eval command
            task_name: Name of the benchmark task
            model_name: Name identifier for the model

        Returns:
            BenchmarkResult with parsed metrics
        """
        # Parse JSON results from output
        # This is a simplified parser - real implementation would need to handle
        # the actual LM Eval JSON output format

        try:
            # Look for JSON in output (lm_eval typically outputs JSON results)
            lines = output.strip().split('\n')
            json_line = None

            for line in lines:
                if line.strip().startswith('{'):
                    json_line = line
                    break

            if json_line:
                results_data = json.loads(json_line)
            else:
                # Fallback: create minimal result if parsing fails
                results_data = {}

            # Extract accuracy metrics
            accuracy_metrics = self._extract_accuracy_metrics(results_data, task_name)

            # Create performance metrics (placeholder - would need actual measurement)
            performance_metrics = PerformanceMetrics(
                tokens_per_second=0.0,  # Would be measured separately
                latency_ms=0.0,         # Would be measured separately
                total_tokens=0,
                prompt_tokens=0,
                completion_tokens=0
            )

            # Create resource metrics (placeholder)
            resource_metrics = ResourceMetrics(
                peak_memory_mb=0.0,
                cpu_utilization_percent=0.0
            )

            return BenchmarkResult(
                result_id="",  # Will be set by caller
                run_id="",     # Will be set by caller
                task_name=task_name,
                accuracy_metrics=accuracy_metrics,
                performance_metrics=performance_metrics,
                resource_metrics=resource_metrics,
                timestamp=time.time()
            )

        except Exception as e:
            raise RuntimeError(f"Failed to parse LM Eval output: {e}")

    def _extract_accuracy_metrics(self, results_data: Dict[str, Any], task_name: str) -> Optional[AccuracyMetrics]:
        """
        Extract accuracy metrics from LM Eval results.

        Args:
            results_data: Parsed JSON results from LM Eval
            task_name: Name of the benchmark task

        Returns:
            AccuracyMetrics object or None if not available
        """
        try:
            # Navigate to task results (structure depends on LM Eval version)
            task_results = results_data.get("results", {}).get(task_name, {})

            if not task_results:
                return None

            return AccuracyMetrics(
                acc=task_results.get("acc"),
                acc_stderr=task_results.get("acc_stderr"),
                exact_match=task_results.get("exact_match"),
                f1=task_results.get("f1"),
                custom_metrics=task_results.get("custom_metrics", {})
            )

        except Exception:
            return None

    def list_available_tasks(self) -> List[str]:
        """
        List all available benchmark tasks.

        Returns:
            List of available task names
        """
        try:
            # Use lm_eval to list tasks
            result = subprocess.run(
                ["lm_eval", "--list_tasks"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                # Parse task list from output
                tasks = []
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('-'):
                        tasks.append(line)
                return tasks
            else:
                raise RuntimeError(f"Failed to list tasks: {result.stderr}")

        except Exception as e:
            print(f"Warning: Could not list available tasks: {e}")
            # Return common default tasks
            return [
                "mmlu", "hellaswag", "gsm8k", "truthfulqa",
                "arc_easy", "arc_challenge", "humaneval"
            ]

    def validate_server_connection(self) -> bool:
        """
        Validate connection to Lemonade server.

        Returns:
            True if server is accessible, False otherwise
        """
        try:
            import requests
            response = requests.get(f"{self.server_url}/health", timeout=10)
            return response.status_code == 200
        except Exception:
            return False