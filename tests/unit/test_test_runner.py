import os
import json
from scripts.benchmarks.continue_testing.test_runner import run_monitor_only


def test_run_monitor_only_creates_results(tmp_path):
    model = "qwen2.5-coder-7b-q4"
    cfg_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'benchmarks', 'continue-testing', 'config'))
    results_dir = str(tmp_path)
    res = run_monitor_only(model, duration=1, config_dir=cfg_dir, results_dir=results_dir)
    # check run file exists
    assert res["run"]["model_name"] == model
    reports_dir = os.path.join(results_dir, "reports")
    assert os.path.isdir(reports_dir)
    # compatibility json should exist
    files = [f for f in os.listdir(reports_dir) if f.endswith('.json')]
    assert len(files) >= 1
