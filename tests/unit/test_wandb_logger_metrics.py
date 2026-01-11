import sys
from types import SimpleNamespace
from scripts.benchmarks.continue_testing.utils.wandb_logger import WandbLogger


def test_wandb_logger_logs_metrics(monkeypatch):
    # Create a fake wandb module
    class FakeRun:
        def __init__(self):
            self.summary = {}
    class FakeWandbModule:
        def __init__(self):
            self.logged = []
            self.run = FakeRun()
        def init(self, project=None, name=None, config=None):
            self.run = FakeRun()
            return self.run
        def finish(self):
            pass
        def log(self, d):
            self.logged.append(d)
    fake = FakeWandbModule()
    monkeypatch.setitem(sys.modules, 'wandb', fake)

    wl = WandbLogger(run_name='t')
    assert wl.is_available()
    assert wl.start_run() is True
    assert wl.log_metrics({'a':1}) is True
    assert fake.logged[-1] == {'a':1}
    assert wl.log_metrics_series([{'x':1},{'x':2}]) is True
    assert fake.logged[-1] == {'x':2}
    assert wl.log_test_run({'model':'m'}) is True
    assert 'test_run' in fake.run.summary
    assert wl.finish_run() is True
