"""
Lemonade SDK Evaluation Module

This module provides comprehensive evaluation workflows for LLM model comparison
on AMD Ryzen AI hardware using Weights & Biases (W&B) Weave integration.

Key Features:
- Model performance benchmarking across quantization levels and MoE configurations
- Accuracy evaluation using LM Evaluation Harness
- Real-time metrics collection and dashboard visualization
- Support for AMD Ryzen AI hybrid NPU+iGPU architecture

Example:
    from lemonade.evaluation import WandbMetricsCollector, LMEvalHarness

    # Initialize W&B logging
    collector = WandbMetricsCollector(project_name="my-evals")

    # Run evaluation
    results = collector.evaluate_model(model_config, benchmark_suite)
"""

__version__ = "1.0.0"
__author__ = "Lemonade SDK Team"

# Import main classes for easy access
from .wandb_logger import WandbMetricsCollector
from .harness import LMEvalHarness
from .runners import EvaluationRunner
from .config import EvaluationConfig
from .models import (
    EvaluationRun, ModelConfiguration, BenchmarkResult,
    PerformanceMetrics, ResourceMetrics, AccuracyMetrics,
    HardwarePlatform, RunStatus
)
from .errors import EvaluationError
from .logging_config import get_evaluation_logger

__all__ = [
    "WandbMetricsCollector",
    "LMEvalHarness",
    "EvaluationRunner",
    "EvaluationConfig",
    "EvaluationRun",
    "ModelConfiguration",
    "BenchmarkResult",
    "PerformanceMetrics",
    "ResourceMetrics",
    "AccuracyMetrics",
    "HardwarePlatform",
    "RunStatus",
    "EvaluationError",
    "get_evaluation_logger",
]