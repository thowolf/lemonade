"""Result writing utilities for the Continue testing framework."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from scripts.benchmarks.continue_testing.model_manager import TestRun


class TestResultWriter:
    """Handles writing test results to JSON files."""

    def __init__(self, results_dir: str):
        self.results_dir = results_dir
        os.makedirs(results_dir, exist_ok=True)

    def save_test_run(self, test_run: TestRun) -> str:
        """Save a TestRun to a JSON file and return the file path."""
        run_dir = os.path.join(self.results_dir, "test_runs")
        os.makedirs(run_dir, exist_ok=True)

        filename = f"{test_run.run_id}.json"
        filepath = os.path.join(run_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(test_run.to_dict(), f, indent=2, default=str)

        return filepath