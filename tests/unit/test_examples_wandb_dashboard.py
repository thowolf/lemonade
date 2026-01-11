import sys
from types import SimpleNamespace

from scripts.benchmarks.continue_testing.examples import fetch_project_run_stats


def test_fetch_project_run_stats(monkeypatch):
    # Create a fake wandb.Api that returns two runs with numeric summaries
    class FakeApi:
        def runs(self, project=None):
            return [
                SimpleNamespace(name="r1", summary={"avg_cpu": 10}, config={"model": "m1"}),
                SimpleNamespace(name="r2", summary={"avg_cpu": 20}, config={"model": "m1"}),
            ]

    fake_wandb = SimpleNamespace(Api=lambda: FakeApi())
    monkeypatch.setitem(sys.modules, "wandb", fake_wandb)

    stats = fetch_project_run_stats("org/proj", limit=10)
    assert stats["project"] == "org/proj"
    assert stats["count"] == 2
    assert stats["aggregates"]["avg_cpu"] == 15.0
