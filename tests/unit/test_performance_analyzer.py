"""Unit tests for PerformanceAnalyzer class."""
import pytest
from scripts.benchmarks.continue_testing.report_generator import PerformanceAnalyzer, PerformanceMetrics


def test_calculate_aggregates():
    """Test PerformanceAnalyzer.calculate_aggregates()."""
    response_times = [100, 200, 150, 300, 250]
    tokens_per_second = [10, 20, 15, 5, 25]
    
    result = PerformanceAnalyzer.calculate_aggregates(response_times, tokens_per_second)
    
    assert result["mean"] == 200.0
    assert result["p50"] == 200.0  # median
    assert result["p95"] == 290.0  # 95th percentile
    assert result["p99"] == 298.0  # 99th percentile
    assert result["tps_mean"] == 15.0
    assert result["tps_p50"] == 15.0


def test_calculate_aggregates_empty():
    """Test PerformanceAnalyzer.calculate_aggregates() with empty data."""
    result = PerformanceAnalyzer.calculate_aggregates([])
    
    assert result["mean"] is None
    assert result["p50"] is None
    assert result["tps_mean"] is None


def test_calculate_performance_metrics():
    """Test PerformanceAnalyzer.calculate_performance_metrics()."""
    test_run = {
        "interactions": [
            {
                "duration_ms": 100.0,
                "tokens_per_second": 20.0,
                "pre_metrics": {
                    "memory_used_mb": 2048,
                    "npu_metrics": {"utilization_percent": 80.0}
                },
                "post_metrics": {
                    "memory_used_mb": 3072,
                    "npu_metrics": {"utilization_percent": 90.0}
                }
            },
            {
                "duration_ms": 150.0,
                "tokens_per_second": 15.0,
                "pre_metrics": {
                    "memory_used_mb": 2500,
                    "npu_metrics": {"utilization_percent": 85.0}
                },
                "post_metrics": {
                    "memory_used_mb": 3500,
                    "npu_metrics": {"utilization_percent": 95.0}
                }
            }
        ]
    }
    
    metrics = PerformanceAnalyzer.calculate_performance_metrics(test_run)
    
    assert isinstance(metrics, PerformanceMetrics)
    assert metrics.response_time_p50_ms == 125.0  # median of [100, 150]
    assert metrics.response_time_p95_ms == 147.5  # 95th percentile calculation
    assert metrics.tokens_per_second == 17.5  # mean of [20, 15]
    assert metrics.memory_peak_gb == 3500 / 1024  # max memory in GB
    assert metrics.npu_util_mean_percent == 87.5  # mean of all NPU utils


def test_calculate_npu_aggregates():
    """Test PerformanceAnalyzer.calculate_npu_aggregates()."""
    test_runs = [
        {
            "interactions": [
                {
                    "pre_metrics": {"npu_metrics": {"utilization_percent": 80.0}},
                    "post_metrics": {"npu_metrics": {"utilization_percent": 90.0}}
                }
            ]
        },
        {
            "interactions": [
                {
                    "pre_metrics": {"npu_metrics": {"utilization_percent": 70.0}},
                    "post_metrics": {"npu_metrics": {"utilization_percent": 85.0}}
                }
            ]
        }
    ]
    
    result = PerformanceAnalyzer.calculate_npu_aggregates(test_runs)
    
    assert result["mean"] == 81.25  # mean of [80, 90, 70, 85]
    assert result["max"] == 90.0
    assert result["min"] == 70.0


def test_save_performance_metrics(tmp_path):
    """Test PerformanceAnalyzer.save_performance_metrics()."""
    metrics = PerformanceMetrics(
        response_time_p50_ms=100.0,
        response_time_p95_ms=200.0,
        tokens_per_second=15.0,
        memory_peak_gb=2.5,
        npu_util_mean_percent=80.0
    )
    
    path = PerformanceAnalyzer.save_performance_metrics("test_run_123", metrics, str(tmp_path))
    
    assert "test_run_123_perf.json" in path
    assert tmp_path.joinpath("test_run_123_perf.json").exists()