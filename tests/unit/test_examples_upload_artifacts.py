import sys
from types import SimpleNamespace
from pathlib import Path

from scripts.benchmarks.continue_testing.examples import upload_artifacts_to_wandb


def test_upload_artifacts_to_wandb(monkeypatch, tmp_path):
    # create fake files
    csv = tmp_path / "r.csv"
    csv.write_text("a,b\n1,2")
    png = tmp_path / "plot.png"
    png.write_bytes(b"PNGDATA")

    artifacts = {"csv": str(csv), "plots": {"bar": str(png)}}

    calls = []

    class FakeArtifact:
        def __init__(self, name=None, type=None):
            self.name = name
            self.type = type
            self.files = []
        def add_file(self, p):
            self.files.append(str(p))

    class FakeRun:
        def __init__(self):
            self.logged = []
        def log_artifact(self, art):
            calls.append(("log_artifact", art.files))

    fake_wandb = SimpleNamespace(
        Artifact=FakeArtifact,
        init=lambda **kw: FakeRun(),
        finish=lambda: calls.append(("finish", None)),
        save=None,
    )

    monkeypatch.setitem(sys.modules, "wandb", fake_wandb)

    res = upload_artifacts_to_wandb(artifacts, project="org/proj", wandb_module=fake_wandb)
    assert res["uploaded"] is True
    assert len(res["details"]) == 2
    assert any(c[0] == "log_artifact" for c in calls)
    assert ("finish", None) in calls
