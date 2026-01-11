import datetime

from scripts.benchmarks.continue_testing.metrics_collector import SystemMonitor


def test_long_duration_monitoring_samples_and_timestamps():
    monitor = SystemMonitor()
    samples = monitor.sample_continuous(interval=0.1, duration=1.0, run_id="longtest")
    # Expect multiple samples
    assert len(samples) >= 5
    # Check timestamps are ISO and timezone-aware
    for s in samples:
        ts = datetime.datetime.fromisoformat(s.timestamp)
        assert ts.tzinfo is not None
        assert s.run_id == "longtest"
