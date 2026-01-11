from scripts.benchmarks.continue_testing.utils.wandb_logger import WandbLogger


def test_wandb_logger_handles_missing_wandb(monkeypatch):
    # Simulate ImportError when importing wandb
    import builtins
    real_import = builtins.__import__
    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == 'wandb':
            raise ImportError('no wandb')
        return real_import(name, globals, locals, fromlist, level)
    monkeypatch.setattr(builtins, '__import__', fake_import)

    wl = WandbLogger()
    assert wl.is_available() is False
    assert wl.log_test_run({'a':1}) is False
    assert wl.log_metrics({'m':2}) is False
    assert wl.log_freeze_event({'f':3}) is False
