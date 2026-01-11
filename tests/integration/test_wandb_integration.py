import sys
from types import SimpleNamespace

from scripts.benchmarks.continue_testing.utils.wandb_logger import WandbLogger


def test_wandb_logger_integration(monkeypatch):
    calls = []

    def fake_init(**kwargs):
        calls.append(("init", kwargs))
        return SimpleNamespace()

    def fake_log(data):
        calls.append(("log", dict(data)))

    def fake_finish():
        calls.append(("finish", None))

    def fake_summary_update(d):
        calls.append(("summary", d))

    fake_module = SimpleNamespace(
        init=fake_init, log=fake_log, finish=fake_finish, run=SimpleNamespace(summary=SimpleNamespace(update=fake_summary_update))
    )

    monkeypatch.setitem(sys.modules, "wandb", fake_module)

    wb = WandbLogger(run_name="r1", group="g1")
    assert wb.is_available()

    assert wb.start_run(config={"model": "m1"})
    # ensure init call included group and config
    assert any(c[0] == "init" and c[1].get("group") == "g1" and c[1].get("config", {}).get("model") == "m1" for c in calls)

    calls.clear()
    series = [{"cpu": 10}, {"cpu": 20}]
    assert wb.log_metrics_series(series, step_key="step")
    # two log calls with step keys
    assert any(c[0] == "log" and c[1].get("step") == 0 for c in calls)
    assert any(c[0] == "log" and c[1].get("step") == 1 for c in calls)

    calls.clear()
    assert wb.log_test_run({"run_id": "abc"})
    assert ("summary", {"test_run": {"run_id": "abc"}}) in calls

    calls.clear()
    assert wb.finish_run()
    assert ("finish", None) in calls
