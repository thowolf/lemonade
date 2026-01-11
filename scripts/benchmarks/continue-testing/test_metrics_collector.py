#!/usr/bin/env python3
"""Unit tests for metrics_collector.py"""

import pytest
from metrics_collector import SystemMetrics


def test_system_metrics_create_now():
    """Test that SystemMetrics.create_now() creates metrics with live data."""
    metrics = SystemMetrics.create_now()

    # Check that we have a SystemMetrics instance
    assert isinstance(metrics, SystemMetrics)

    # Check that CPU metrics are present
    assert hasattr(metrics, 'cpu_percent')
    assert isinstance(metrics.cpu_percent, (int, float))

    # Check that memory metrics are present
    assert hasattr(metrics, 'memory_total_mb')
    assert isinstance(metrics.memory_total_mb, (int, float))
    assert hasattr(metrics, 'memory_used_mb')
    assert isinstance(metrics.memory_used_mb, (int, float))

    # Check that NPU metrics are present (may be empty dict if no NPU)
    assert hasattr(metrics, 'npu_metrics')
    assert isinstance(metrics.npu_metrics, dict)

    # If NPU metrics are present, check structure
    if metrics.npu_metrics:
        # Should have device_count at minimum
        assert 'device_count' in metrics.npu_metrics
        assert isinstance(metrics.npu_metrics['device_count'], int)

    # Check that AMD GPU metrics are present (may be empty dict)
    assert hasattr(metrics, 'amd_gpu_metrics')
    assert isinstance(metrics.amd_gpu_metrics, dict)

    print(f"✓ SystemMetrics created successfully:")
    print(f"  CPU: {metrics.cpu_percent}%")
    print(f"  Memory: {metrics.memory_total_mb:.1f} MB total, {metrics.memory_used_mb:.1f} MB used")
    print(f"  NPU: {metrics.npu_metrics}")
    print(f"  AMD GPU: {metrics.amd_gpu_metrics}")


if __name__ == "__main__":
    test_system_metrics_create_now()