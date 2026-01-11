import pytest
from scripts.benchmarks.continue_testing.metrics_collector import SystemMonitor, SystemMetrics


def test_systemmetrics_create_now_basic():
    m = SystemMetrics.create_now("test-run-123")
    assert isinstance(m.metric_id, str)
    assert m.run_id == "test-run-123"
    assert isinstance(m.timestamp, str)
    assert isinstance(m.cpu_percent, float)
    assert isinstance(m.memory_total_gb, float)
    assert isinstance(m.memory_used_gb, float)
    assert isinstance(m.memory_percent, float)
    assert 0.0 <= m.cpu_percent <= 100.0
    assert m.memory_total_gb > 0
    assert m.memory_used_gb >= 0
    assert 0.0 <= m.memory_percent <= 100.0


def test_systemmonitor_sample_returns_metrics():
    monitor = SystemMonitor()
    sample = monitor.sample("test-run-456")
    assert isinstance(sample, SystemMetrics)
    assert sample.run_id == "test-run-456"
    assert 0.0 <= sample.cpu_percent <= 100.0
    assert sample.memory_total_gb > 0
    assert sample.memory_used_gb >= 0
    assert 0.0 <= sample.memory_percent <= 100.0


def test_sample_npu_fallback():
    monitor = SystemMonitor()
    npu = monitor._sample_npu()
    # In CI or on machines without xrt-smi, we expect an empty dict rather than exception
    assert isinstance(npu, dict)


def test_sample_amd_gpu_fallback():
    monitor = SystemMonitor()
    gpu = monitor._sample_amd_gpu()
    # Should return empty dict if pyadl not available
    assert isinstance(gpu, dict)


def test_sample_continuous():
    monitor = SystemMonitor()
    samples = monitor.sample_continuous("test-run-789", interval=0.1, duration=0.2)
    assert len(samples) >= 1  # At least one sample
    for sample in samples:
        assert isinstance(sample, SystemMetrics)
        assert sample.run_id == "test-run-789"


def test_systemmonitor_with_process_tracking():
    monitor = SystemMonitor(track_process_name="python")
    # Should not crash even if process not found
    sample = monitor.sample("test-run-999")
    assert isinstance(sample, SystemMetrics)


def test_systemmetrics_to_dict():
    m = SystemMetrics.create_now("test-run-000")
    d = m.to_dict()
    assert isinstance(d, dict)
    assert "metric_id" in d
    assert "run_id" in d
    assert d["run_id"] == "test-run-000"


def test_systemmetrics_to_json():
    m = SystemMetrics.create_now("test-run-111")
    json_str = m.to_json()
    assert isinstance(json_str, str)
    # Should be valid JSON
    import json
    parsed = json.loads(json_str)
    assert parsed["run_id"] == "test-run-111"
