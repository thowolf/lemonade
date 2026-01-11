import os
import json
from scripts.benchmarks.continue_testing.report_generator import TrendAnalyzer


def test_detect_degradation_insufficient_data(tmp_path):
    runs_dir = tmp_path
    # write only 3 runs with interactions -> insufficient for window 2
    for i in range(3):
        r = {"run_id": f"r{i}", "interactions": [{"response_time_ms": 1000.0+i*10} for _ in range(2)]}
        with open(os.path.join(runs_dir, f"run_{i}.json"), 'w', encoding='utf-8') as fh:
            json.dump(r, fh)
    runs = TrendAnalyzer.load_runs_from_directory(str(runs_dir))
    out = TrendAnalyzer.detect_degradation(runs, window=2, threshold_percent=10.0)
    assert out['degraded'] is False


def test_detect_degradation_positive(tmp_path):
    runs_dir = tmp_path
    # create 6 runs: first 3 low mean, last 3 high mean
    for i in range(6):
        base = 1000.0 if i < 3 else 3000.0
        r = {"run_id": f"r{i}", "interactions": [{"response_time_ms": base + j*10} for j in range(3)]}
        with open(os.path.join(runs_dir, f"run_{i}.json"), 'w', encoding='utf-8') as fh:
            json.dump(r, fh)
    runs = TrendAnalyzer.load_runs_from_directory(str(runs_dir))
    out = TrendAnalyzer.detect_degradation(runs, window=2, threshold_percent=20.0)
    assert out['degraded'] is True
