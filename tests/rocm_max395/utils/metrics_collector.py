"""
Performance metrics collection and analysis for ROCm testing.

Collects and aggregates performance data from Lemonade Server,
system monitoring, and GPU utilization metrics.
"""

import time
import json
import psutil
import statistics
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import defaultdict

@dataclass
class PerformanceMetrics:
    """Container for performance measurement data."""
    tokens_per_second: float
    latency_ms: float
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    time_to_first_token_ms: Optional[float] = None
    peak_memory_mb: Optional[float] = None
    average_memory_mb: Optional[float] = None
    cpu_utilization_percent: Optional[float] = None
    gpu_utilization_percent: Optional[float] = None
    vram_usage_mb: Optional[float] = None
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

@dataclass
class BenchmarkResult:
    """Container for benchmark test results."""
    test_name: str
    model_name: str
    model_size: str
    backend: str
    metrics: List[PerformanceMetrics]
    summary: Dict[str, Any]
    environment: Dict[str, Any]
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

class MetricsCollector:
    """Collects and analyzes performance metrics during testing."""

    def __init__(self):
        self.system_metrics = []
        self.start_time = None
        self.end_time = None

    def start_collection(self) -> None:
        """Start collecting system metrics."""
        self.start_time = time.time()
        self.system_metrics = []

    def stop_collection(self) -> None:
        """Stop collecting system metrics."""
        self.end_time = time.time()

    def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect current system performance metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)

            # Memory metrics
            memory = psutil.virtual_memory()
            memory_mb = memory.used / (1024 * 1024)

            # GPU metrics (placeholder - would need ROCm-specific monitoring)
            gpu_metrics = self._collect_gpu_metrics()

            metrics = {
                "timestamp": time.time(),
                "cpu_utilization_percent": cpu_percent,
                "memory_usage_mb": memory_mb,
                "memory_percent": memory.percent,
                **gpu_metrics
            }

            self.system_metrics.append(metrics)
            return metrics

        except Exception as e:
            # Return minimal metrics if collection fails
            return {
                "timestamp": time.time(),
                "error": str(e),
                "cpu_utilization_percent": 0.0,
                "memory_usage_mb": 0.0
            }

    def _collect_gpu_metrics(self) -> Dict[str, Any]:
        """Collect GPU-specific metrics using ROCm tools."""
        # Placeholder for ROCm GPU monitoring
        # In a real implementation, this would use rocm-smi or similar
        try:
            # This is a simplified placeholder
            # Real implementation would parse rocm-smi output
            return {
                "gpu_utilization_percent": 0.0,  # Placeholder
                "vram_usage_mb": 0.0,  # Placeholder
                "gpu_temperature_c": 0.0  # Placeholder
            }
        except Exception:
            return {
                "gpu_utilization_percent": None,
                "vram_usage_mb": None,
                "gpu_temperature_c": None
            }

    def calculate_summary_stats(self, metrics_list: List[PerformanceMetrics]) -> Dict[str, Any]:
        """
        Calculate summary statistics from a list of performance metrics.

        Args:
            metrics_list: List of PerformanceMetrics objects

        Returns:
            Dictionary with summary statistics
        """
        if not metrics_list:
            return {}

        # Extract values for statistical calculations
        tokens_per_second_values = [m.tokens_per_second for m in metrics_list]
        latency_values = [m.latency_ms for m in metrics_list]
        total_tokens_values = [m.total_tokens for m in metrics_list]

        summary = {
            "count": len(metrics_list),
            "tokens_per_second": {
                "mean": statistics.mean(tokens_per_second_values),
                "median": statistics.median(tokens_per_second_values),
                "min": min(tokens_per_second_values),
                "max": max(tokens_per_second_values),
                "stdev": statistics.stdev(tokens_per_second_values) if len(tokens_per_second_values) > 1 else 0
            },
            "latency_ms": {
                "mean": statistics.mean(latency_values),
                "median": statistics.median(latency_values),
                "min": min(latency_values),
                "max": max(latency_values),
                "p50": statistics.median(latency_values),
                "p95": self._calculate_percentile(latency_values, 95),
                "p99": self._calculate_percentile(latency_values, 99),
                "stdev": statistics.stdev(latency_values) if len(latency_values) > 1 else 0
            },
            "total_tokens": {
                "mean": statistics.mean(total_tokens_values),
                "total": sum(total_tokens_values)
            }
        }

        # Add time-to-first-token stats if available
        ttft_values = [m.time_to_first_token_ms for m in metrics_list if m.time_to_first_token_ms is not None]
        if ttft_values:
            summary["time_to_first_token_ms"] = {
                "mean": statistics.mean(ttft_values),
                "median": statistics.median(ttft_values),
                "min": min(ttft_values),
                "max": max(ttft_values)
            }

        return summary

    def _calculate_percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile from a list of values."""
        if not values:
            return 0.0
        values_sorted = sorted(values)
        index = int(len(values_sorted) * percentile / 100)
        return values_sorted[min(index, len(values_sorted) - 1)]

    def create_benchmark_result(self, test_name: str, model_name: str, model_size: str,
                              backend: str, metrics: List[PerformanceMetrics],
                              environment: Dict[str, Any]) -> BenchmarkResult:
        """
        Create a benchmark result object with summary statistics.

        Args:
            test_name: Name of the test
            model_name: Name of the model tested
            model_size: Size of the model (e.g., "7B", "30B")
            backend: Backend used (e.g., "rocm", "vulkan")
            metrics: List of performance metrics
            environment: Environment information

        Returns:
            BenchmarkResult object
        """
        summary = self.calculate_summary_stats(metrics)

        return BenchmarkResult(
            test_name=test_name,
            model_name=model_name,
            model_size=model_size,
            backend=backend,
            metrics=metrics,
            summary=summary,
            environment=environment
        )

    def save_benchmark_result(self, result: BenchmarkResult, filepath: Path) -> None:
        """
        Save benchmark result to JSON file.

        Args:
            filepath: Path to save the result
        """
        # Convert dataclasses to dictionaries for JSON serialization
        data = {
            "test_name": result.test_name,
            "model_name": result.model_name,
            "model_size": result.model_size,
            "backend": result.backend,
            "timestamp": result.timestamp,
            "summary": result.summary,
            "environment": result.environment,
            "metrics": [asdict(m) for m in result.metrics]
        }

        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def load_benchmark_result(self, filepath: Path) -> BenchmarkResult:
        """
        Load benchmark result from JSON file.

        Args:
            filepath: Path to the result file

        Returns:
            BenchmarkResult object
        """
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Reconstruct PerformanceMetrics objects
        metrics = []
        for m_data in data.get("metrics", []):
            # Remove timestamp if it's a string (JSON serialization issue)
            if isinstance(m_data.get("timestamp"), str):
                m_data["timestamp"] = float(m_data["timestamp"])
            metrics.append(PerformanceMetrics(**m_data))

        return BenchmarkResult(
            test_name=data["test_name"],
            model_name=data["model_name"],
            model_size=data["model_size"],
            backend=data["backend"],
            metrics=metrics,
            summary=data.get("summary", {}),
            environment=data.get("environment", {}),
            timestamp=data.get("timestamp", time.time())
        )

    def compare_results(self, result1: BenchmarkResult, result2: BenchmarkResult) -> Dict[str, Any]:
        """
        Compare two benchmark results.

        Args:
            result1: First benchmark result
            result2: Second benchmark result

        Returns:
            Dictionary with comparison metrics
        """
        comparison = {
            "models": f"{result1.model_name} vs {result2.model_name}",
            "backends": f"{result1.backend} vs {result2.backend}",
            "tokens_per_second_ratio": (
                result1.summary.get("tokens_per_second", {}).get("mean", 0) /
                result2.summary.get("tokens_per_second", {}).get("mean", 1)  # Avoid division by zero
            ),
            "latency_ratio": (
                result1.summary.get("latency_ms", {}).get("mean", 1) /
                result2.summary.get("latency_ms", {}).get("mean", 1)
            )
        }

        return comparison


def create_benchmark_result(
    test_name: str,
    model_name: str,
    model_size: str,
    backend: str,
    metrics: List[PerformanceMetrics],
    environment: Dict[str, Any]
) -> BenchmarkResult:
    """
    Create a benchmark result from collected metrics.

    Args:
        test_name: Name of the test
        model_name: Name of the model used
        model_size: Size/category of the model
        backend: Backend used (e.g., 'rocm', 'cpu')
        metrics: List of performance metrics
        environment: Environment information

    Returns:
        BenchmarkResult object with computed summary statistics
    """
    if not metrics:
        raise ValueError("Cannot create benchmark result with empty metrics")

    # Calculate summary statistics
    tokens_per_second_values = [m.tokens_per_second for m in metrics]
    latency_values = [m.latency_ms for m in metrics]
    memory_values = [m.peak_memory_mb for m in metrics if m.peak_memory_mb is not None]

    summary = {
        "tokens_per_second": {
            "mean": statistics.mean(tokens_per_second_values),
            "median": statistics.median(tokens_per_second_values),
            "std_dev": statistics.stdev(tokens_per_second_values) if len(tokens_per_second_values) > 1 else 0,
            "min": min(tokens_per_second_values),
            "max": max(tokens_per_second_values)
        },
        "latency_ms": {
            "mean": statistics.mean(latency_values),
            "median": statistics.median(latency_values),
            "std_dev": statistics.stdev(latency_values) if len(latency_values) > 1 else 0,
            "min": min(latency_values),
            "max": max(latency_values),
            "p95": statistics.quantiles(latency_values, n=20)[18] if len(latency_values) >= 20 else max(latency_values),
            "p99": statistics.quantiles(latency_values, n=100)[98] if len(latency_values) >= 100 else max(latency_values)
        },
        "total_samples": len(metrics),
        "total_tokens": sum(m.total_tokens for m in metrics),
        "total_prompt_tokens": sum(m.prompt_tokens for m in metrics),
        "total_completion_tokens": sum(m.completion_tokens for m in metrics)
    }

    if memory_values:
        summary["peak_memory_mb"] = {
            "mean": statistics.mean(memory_values),
            "max": max(memory_values)
        }

    return BenchmarkResult(
        test_name=test_name,
        model_name=model_name,
        model_size=model_size,
        backend=backend,
        metrics=metrics,
        summary=summary,
        environment=environment
    )