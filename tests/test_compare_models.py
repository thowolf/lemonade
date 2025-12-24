import subprocess
import sys
from pathlib import Path

def test_compare_models_offline(tmp_path):
    repo = Path(__file__).resolve().parents[1]
    script = repo / 'scripts' / 'benchmarks' / 'compare_models.py'
    data_dir = repo / 'tests' / 'data'
    out_dir = tmp_path / 'reports'
    cmd = [sys.executable, str(script), '--mode', 'offline', '--models', 'qwen,Llama-3.1-8B-Instruct-Hybrid', '--results-dir', str(data_dir), '--out-dir', str(out_dir)]
    res = subprocess.run(cmd, cwd=str(repo))
    assert res.returncode == 0
    report = out_dir / 'compare_qwen_Llama-3.1-8B-Instruct-Hybrid.html'
    assert report.exists()
    txt = report.read_text(encoding='utf-8')
    assert 'qwen' in txt.lower() and 'llama' in txt.lower()
    assert 'Latency histogram' in txt
    assert 'Tokens/sec per sample' in txt
