from scripts.benchmarks.continue_testing.scheduled_runner import ScheduledTestRunner
import time


def test_scheduled_runner_runs_task_once():
    called = {'n': 0}
    def task():
        called['n'] += 1
    runner = ScheduledTestRunner(task=task, interval_seconds=1, max_runs=1)
    stop = runner.start()
    # wait a bit for the run to execute
    time.sleep(2)
    assert called['n'] == 1
    stop()


def test_scheduled_runner_can_stop_early():
    called = {'n': 0}
    def task():
        called['n'] += 1
    runner = ScheduledTestRunner(task=task, interval_seconds=10, max_runs=5)
    stop = runner.start()
    time.sleep(1)
    stop()
    # may have run at least once or not; ensure stop returns without hanging
    assert True
