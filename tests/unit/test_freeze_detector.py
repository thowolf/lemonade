from scripts.benchmarks.continue_testing.freeze_detector import FreezeDetector
from scripts.benchmarks.continue_testing.metrics_collector import SystemMetrics


def test_create_freeze_event_basic():
    metrics = SystemMetrics.create_now()
    fe = FreezeDetector.create_freeze_event(request_index=1, detection_method="timeout", metrics=metrics)
    assert fe.request_index == 1
    assert fe.diagnostics["detection_method"] == "timeout"
    assert isinstance(fe.id, str) and len(fe.id) > 0


def test_freeze_event_save(tmp_path):
    metrics = SystemMetrics.create_now()
    fe = FreezeDetector.create_freeze_event(request_index=2, detection_method="user_report", metrics=metrics)
    out = fe.save(str(tmp_path))
    assert out.endswith(".json")
    assert tmp_path.joinpath(out.split('/')[-1]).exists() or tmp_path.joinpath(out.split('\\')[-1]).exists()


def test_detect_from_timeout():
    detector = FreezeDetector()
    
    # Test timeout detection
    import time
    start_time = time.time() - 10  # 10 seconds ago
    fe = detector.detect_from_timeout(start_time, timeout_seconds=5, request_index=3)
    assert fe is not None
    assert fe.request_index == 3
    assert "timed out" in fe.diagnostics["user_notes"]
    
    # Test no timeout
    start_time = time.time()  # Just started
    fe = detector.detect_from_timeout(start_time, timeout_seconds=5, request_index=4)
    assert fe is None


def test_collect_freeze_diagnostics():
    detector = FreezeDetector()
    fe = detector.collect_freeze_diagnostics(request_index=5)
    assert fe.request_index == 5
    assert "comprehensive_snapshot" in fe.diagnostics["detection_method"]
    assert "system_metrics" in fe.diagnostics
    assert "recent_log_errors" in fe.diagnostics
