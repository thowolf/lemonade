import json
import os
from types import SimpleNamespace
from scripts.benchmarks.continue_testing.test_runner import main


def test_main_monitor_wandb(monkeypatch, tmp_path):
    # Create fake WandbLogger with tracking
    class FakeWandb:
        def __init__(self, project='p', run_name=None):
            self.calls = {}
        def is_available(self):
            return True
        def log_test_run(self, data):
            self.calls['run'] = data
        def log_freeze_event(self, data):
            self.calls['freeze'] = data
    fake = FakeWandb()

    def fake_init(*args, **kwargs):
        return fake

    import sys
    monkeypatch.setitem(sys.modules, 'scripts.benchmarks.continue_testing.utils.wandb_logger', SimpleNamespace(WandbLogger=lambda run_name=None: fake))

    # Run main in monitor-only mode
    rc = main(['--model', 'm1', '--monitor-only', '--duration', '1', '--results-dir', str(tmp_path), '--wandb'])
    assert rc == 0
    # ensure fake logged run
    assert 'run' in fake.calls
