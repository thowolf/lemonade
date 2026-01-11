"""Scheduled test runner for periodic execution of Continue testing runs."""
from __future__ import annotations

import threading
import time
from typing import Callable, Optional


class ScheduledTestRunner:
    """Run a provided `task` function at fixed intervals (seconds).

    Usage:
        runner = ScheduledTestRunner(task=my_task, interval_seconds=300)
        stop = runner.start()
        # ... stop when desired
        stop()
    """

    def __init__(self, task: Callable[[], None], interval_seconds: int = 300, max_runs: Optional[int] = None):
        self.task = task
        self.interval_seconds = interval_seconds
        self.max_runs = max_runs
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def _worker(self):
        runs = 0
        while not self._stop_event.is_set():
            self.task()
            runs += 1
            if self.max_runs and runs >= self.max_runs:
                break
            # Wait with early exit
            for _ in range(self.interval_seconds):
                if self._stop_event.is_set():
                    break
                time.sleep(1)

    def start(self) -> Callable[[], None]:
        """Start the scheduled runner thread and return a callable to stop it.

        If the runner is already active this method returns the current stop callable.
        """
        if self._thread and self._thread.is_alive():
            return self.stop
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()
        return self.stop

    def stop(self):
        """Stop the scheduled runner and wait briefly for the worker thread to exit."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1)
