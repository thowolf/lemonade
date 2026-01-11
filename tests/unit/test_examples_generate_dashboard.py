import sys
from types import SimpleNamespace
from pathlib import Path

from scripts.benchmarks.continue_testing.examples import generate_dashboard


def test_generate_dashboard_creates_artifacts(tmp_path, monkeypatch):
    # Create fake wandb Api returning two runs
    class FakeApi:
        def runs(self, project=None):
            return [
                SimpleNamespace(name="r1", summary={"avg_cpu": 10}),
                SimpleNamespace(name="r2", summary={"avg_cpu": 20}),
            ]

    fake_wandb = SimpleNamespace(Api=lambda: FakeApi())
    monkeypatch.setitem(sys.modules, "wandb", fake_wandb)

    out = generate_dashboard("org/proj", out_dir=str(tmp_path / "artifacts"), wandb_module=fake_wandb)
    # Check CSV created
    assert Path(out["csv"]).exists()
    # Check at least one plot created
    assert "bar" in out["plots"] and Path(out["plots"]["bar"]).exists()
    assert "aggregates" in out["plots"] and Path(out["plots"]["aggregates"]).exists()
    assert out["aggregates"]["avg_cpu"] == 15.0
