import os
import json
from scripts.benchmarks.continue_testing.test_runner import run_interactive


def test_run_interactive_all_yes(monkeypatch, tmp_path):
    # Simulate pressing ENTER, then 'y', then '100' for each interaction
    seq = []
    for _ in range(3):
        seq.extend(['', 'y', '100'])
    it = iter(seq)
    monkeypatch.setattr('builtins.input', lambda prompt='': next(it))

    results_dir = str(tmp_path)
    res = run_interactive('m1', interactions=3, config_dir=None, results_dir=results_dir, verbose=True, output_format='all')
    assert res['run'] is not None
    assert res['run']['num_interactions_completed'] == 3
    reports = os.listdir(os.path.join(results_dir, 'reports'))
    # Expect json, md, csv files
    assert any(f.endswith('.json') for f in reports)
    assert any(f.endswith('.md') for f in reports)
    assert any(f.endswith('.csv') for f in reports)
