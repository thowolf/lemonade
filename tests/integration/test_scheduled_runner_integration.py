import time
from types import SimpleNamespace
from pathlib import Path

from scripts.benchmarks.continue_testing.scheduled_runner import ScheduledTestRunner
from scripts.benchmarks.continue_testing.test_runner import run_monitor_only


def test_scheduled_runner_runs_task_and_wandb_logging(tmp_path):
    calls = []

    fake_wandb_logger = SimpleNamespace(
        is_available=lambda: True,
        start_run=lambda config=None: calls.append(("start", config)),
        log_metrics=lambda m: calls.append(("metrics", m)),
        log_test_run=lambda r: calls.append(("run", r)),
        finish_run=lambda: calls.append(("finish", None)),
    )

    results_dir = tmp_path / "results"
    results_dir.mkdir()

    def task():
        # short duration monitor-only run
        run_monitor_only("m1", duration=1, config_dir=".", results_dir=str(results_dir), wandb_logger=fake_wandb_logger)

    runner = ScheduledTestRunner(task=task, interval_seconds=1, max_runs=3)
    stop = runner.start()

    # Wait for expected runs to complete (with timeout)
    timeout = time.time() + 8
    while time.time() < timeout:
        run_files = list((results_dir / "test_runs").glob("run_*.json")) if (results_dir / "test_runs").exists() else []
        if len(run_files) >= 3:
            break
        time.sleep(0.2)

    # Ensure scheduled runs produced results and W&B calls were made
    run_files = list((results_dir / "test_runs").glob("run_*.json"))
    assert len(run_files) >= 3
    assert any(c[0] == "run" for c in calls)

    # Ensure we stop the runner
    stop()
