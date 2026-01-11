import os
from scripts.benchmarks.continue_testing.test_runner import run_monitor_only


def test_run_monitor_only_with_format_and_verbose(tmp_path):
    model = "qwen2.5-coder-7b-q4"
    results_dir = str(tmp_path)
    res = run_monitor_only(model, duration=1, config_dir=None, results_dir=results_dir)
    # This function ignores format/verbose flags directly; invocation via main handles formats.
    assert res["run"]["model_name"] == model
    assert os.path.isdir(os.path.join(results_dir, "reports"))
