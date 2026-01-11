import sys
import types
import os
from scripts.benchmarks.continue_testing.model_manager import ConfigLoader


def make_fake_yamale(ok=True):
    fake = types.SimpleNamespace()

    class FakeSchema: pass

    def make_schema(p):
        return FakeSchema()

    def make_data(p):
        # return a placeholder; Yamale expects list-like
        return ['data']

    def validate(schema, data):
        if not ok:
            raise Exception('invalid config')
        return None

    fake.make_schema = make_schema
    fake.make_data = make_data
    fake.validate = validate
    return fake


def test_validate_config_uses_yamale_success(monkeypatch, tmp_path):
    cfg_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'benchmarks', 'continue-testing', 'config')
    cfg_dir = os.path.normpath(cfg_dir)
    loader = ConfigLoader(cfg_dir)

    fake = make_fake_yamale(ok=True)
    monkeypatch.setitem(sys.modules, 'yamale', fake)

    assert loader.validate_config('models') is True
    assert loader.validate_config('scenarios') is True
    assert loader.validate_config('hardware') is True


def test_validate_config_raises_on_invalid(monkeypatch):
    cfg_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'benchmarks', 'continue-testing', 'config')
    cfg_dir = os.path.normpath(cfg_dir)
    loader = ConfigLoader(cfg_dir)

    fake = make_fake_yamale(ok=False)
    monkeypatch.setitem(sys.modules, 'yamale', fake)

    import pytest
    with pytest.raises(ValueError):
        loader.validate_config('models')


def test_validate_config_no_yamale(monkeypatch):
    cfg_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'benchmarks', 'continue-testing', 'config')
    cfg_dir = os.path.normpath(cfg_dir)
    loader = ConfigLoader(cfg_dir)

    if 'yamale' in sys.modules:
        monkeypatch.delitem(sys.modules, 'yamale', raising=False)

    import pytest
    with pytest.raises(RuntimeError):
        loader.validate_config('models')
