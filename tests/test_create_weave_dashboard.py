import subprocess
import sys
from pathlib import Path
import tempfile


def test_create_report_from_sample(tmp_path):
    repo = Path(__file__).resolve().parents[1]
    script = repo / 'scripts' / 'create_weave_dashboard.py'
    data_dir = repo / 'tests' / 'data'
    out_dir = tmp_path / 'reports'

    cmd = [sys.executable, str(script), '--results-dir', str(data_dir), '--out-dir', str(out_dir)]
    res = subprocess.run(cmd, cwd=str(repo))
    assert res.returncode == 0

    report = out_dir / 'lemonade_quick_benchmark_overview.html'
    assert report.exists()

    txt = report.read_text(encoding='utf-8')
    # check basic contents
    assert '<h1>Lemonade' in txt
    assert 'Latency Histogram' in txt
    assert 'Tokens/sec per Sample' in txt
    # check that there is an embedded PNG (base64) or an <img> tag present
    assert 'data:image/png;base64,' in txt
