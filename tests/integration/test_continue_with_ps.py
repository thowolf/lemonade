import os
import sys
import time
import json
import glob
import shutil
import subprocess
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
PS_SCRIPT = os.path.join(ROOT, 'scripts', 'benchmarks', 'continue-testing', 'Test-ContinueModels.ps1')
CONFIG_DIR = os.path.join(ROOT, 'scripts', 'benchmarks', 'continue-testing', 'config')
RESULTS_DIR = os.path.join(ROOT, 'scripts', 'benchmarks', 'continue-testing', 'results')
MODEL_ID = os.getenv('LEMONADE_MODEL_ID', 'qwen3-coder:30b')


def powershell_available():
    # Prefer pwsh if available
    return shutil.which('pwsh') or shutil.which('powershell')


@pytest.mark.skipif(not powershell_available(), reason='PowerShell not available')
def test_continue_powerShell_runner():
    # Ensure Lemonade API available
    base = os.getenv('LEMONADE_BASE_URL', 'http://127.0.0.1:8000')
    try:
        import requests
        r = requests.get(base + '/api/v1/models?show_all=true', timeout=5)
        r.raise_for_status()
    except Exception as e:
        pytest.skip(f'Lemonade server not reachable: {e}')

    # (cleanup will be performed after we determine the exact model id to test)

    # Determine model id to test: env override or pick a server-loaded Qwen 30B candidate
    model_env = os.getenv('LEMONADE_MODEL_ID')
    selected_model = model_env
    if not selected_model:
        try:
            import requests
            r = requests.get(base + '/api/v1/models?show_all=true', timeout=5)
            r.raise_for_status()
            data = r.json().get('data', [])
            candidates = [m.get('id') for m in data if m.get('id') and 'qwen' in m.get('id').lower() and ('30' in m.get('id') or '30b' in m.get('id').lower())]
            if candidates:
                selected_model = candidates[0]
                print(f"Auto-selected model from server: {selected_model}")
        except Exception as e:
            print(f"Warning: could not query server for models: {e}")

    # Build PowerShell command
    pw = shutil.which('pwsh') or shutil.which('powershell')
    cmd = [pw, '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', PS_SCRIPT,
           '-MaxInteractions', '3', '-TimeoutSeconds', '600',
           '-ConfigPath', CONFIG_DIR, '-ResultsPath', RESULTS_DIR]

    if selected_model:
        cmd.extend(['-ModelId', selected_model])

        # Verify model is loaded on the server before attempting the test
        try:
            r2 = requests.get(base + '/api/v1/models?show_all=true', timeout=5)
            r2.raise_for_status()
            model_data = r2.json().get('data', [])
            server_model = next((m for m in model_data if m.get('id') == selected_model), None)
            if server_model:
                state = server_model.get('state') or server_model.get('status') or server_model.get('loaded')
                if state and str(state).lower() not in ('ready', 'loaded', 'available', 'true'):
                    pytest.skip(f"Selected model '{selected_model}' is not in a ready state on the server: {state}")
        except Exception as e:
            print(f"Warning: could not verify model state on server: {e}")

    # cleanup old files for the selected model
    model_to_use = selected_model or MODEL_ID
    import re
    safe_model = re.sub(r'[^0-9A-Za-z]', '_', model_to_use)
    pattern = os.path.join(RESULTS_DIR, f"result_{safe_model}_*.json")
    for f in glob.glob(pattern):
        try:
            os.remove(f)
        except Exception:
            pass

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=1200)
    sys.stderr.write(proc.stderr)
    sys.stdout.write(proc.stdout)

    assert proc.returncode == 0, f'PowerShell runner failed (rc={proc.returncode})'

    # Find latest result file
    files = glob.glob(pattern)
    assert files, 'No result files produced'

    latest = sorted(files, key=os.path.getmtime)[-1]
    # Read JSON using utf-8-sig to handle possible BOM written by PowerShell
    with open(latest, 'r', encoding='utf-8-sig') as f:
        res = json.load(f)

    # Assert freeze not detected
    assert 'freeze_detected' in res, 'Result missing freeze_detected'
    if res['freeze_detected']:
        # Retry once with a longer timeout to account for slow cold-starts
        print(f"Freeze detected in run {latest}, retrying with longer timeout...")
        retry_cmd = list(cmd)
        try:
            # replace timeout value (assumes pattern '-TimeoutSeconds', '600' exists)
            ti = retry_cmd.index('-TimeoutSeconds')
            retry_cmd[ti+1] = '1800'
        except ValueError:
            pass

        proc2 = subprocess.run(retry_cmd, capture_output=True, text=True, timeout=3600)
        sys.stderr.write(proc2.stderr)
        sys.stdout.write(proc2.stdout)
        assert proc2.returncode == 0, f'Retry PowerShell runner failed (rc={proc2.returncode})'

        # Find latest result file again
        files2 = glob.glob(pattern)
        assert files2, 'No result files produced on retry'
        latest2 = sorted(files2, key=os.path.getmtime)[-1]
        with open(latest2, 'r', encoding='utf-8-sig') as f:
            res2 = json.load(f)
        assert 'freeze_detected' in res2, 'Result missing freeze_detected (retry)'
        assert res2['freeze_detected'] is False, (
            f"Model froze during retry: {res2.get('freeze_at_interaction')}. "
            f"See result file: {latest2}. Check server logs, model resources, and consider increasing timeouts or reducing prompt size."
        )
    else:
        assert res['freeze_detected'] is False, f"Model froze during test: {res.get('freeze_at_interaction')}"
