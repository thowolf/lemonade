"""
ROCm Max395 testing utilities.

This package provides utilities for testing Lemonade Server with ROCm backend
on AMD AI Max+ 395 hardware.
"""

from .lemonade_client import LemonadeClient, InferenceRequest, InferenceResponse, create_client, simple_inference
from .metrics_collector import MetricsCollector, PerformanceMetrics, BenchmarkResult, create_benchmark_result
from .rocm_monitor import ROCmMonitor, GPUInfo, ROCmMetrics, get_rocm_monitor, quick_health_check
from .report_generator import ReportGenerator, create_report_generator, generate_summary_report

__all__ = [
    # Lemonade client
    "LemonadeClient",
    "InferenceRequest",
    "InferenceResponse",
    "create_client",
    "simple_inference",

    # Metrics collection
    "MetricsCollector",
    "PerformanceMetrics",
    "BenchmarkResult",
    "create_benchmark_result",

    # ROCm monitoring
    "ROCmMonitor",
    "GPUInfo",
    "ROCmMetrics",
    "get_rocm_monitor",
    "quick_health_check",

    # Report generation
    "ReportGenerator",
    "create_report_generator",
    "generate_summary_report"
]

__version__ = "1.0.0"