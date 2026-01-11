import os
import sys
import subprocess
import time
import signal
import requests
import pytest

EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts", "benchmarks", "continue-testing", "examples")
SERVE_SCRIPT = os.path.join(EXAMPLES_DIR, "serve_test_page.py")
PAGE_URL = 'http://127.0.0.1:8001/continue_test_page.html'
LEMONADE_BASE = os.getenv('LEMONADE_BASE_URL', 'http://127.0.0.1:8000')
MODEL_ID = os.getenv('LEMONADE_MODEL_ID', 'Qwen3-Coder-30B-A3B-Instruct-GGUF')

try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None


@pytest.mark.skipif(sync_playwright is None, reason='Playwright not installed')
def test_continue_e2e_playwright():
    # Start local static file server
    srv = subprocess.Popen([sys.executable, SERVE_SCRIPT], cwd=EXAMPLES_DIR)

    # wait for server to be ready
    for _ in range(30):
        try:
            r = requests.get(PAGE_URL, timeout=1)
            if r.status_code == 200:
                break
        except Exception:
            time.sleep(0.2)
    else:
        srv.terminate()
        pytest.skip('Could not start test page server')

    # Check Lemonade API reachable
    try:
        r = requests.get(f"{LEMONADE_BASE}/api/v1/models?show_all=true", timeout=5)
        r.raise_for_status()
    except Exception:
        srv.terminate()
        pytest.skip('Lemonade API not reachable')

    # Run Playwright test
    success = False
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(PAGE_URL + f'?base={LEMONADE_BASE}&model={MODEL_ID}')
            page.fill('#prompt', 'Write a Python function that returns the 42st fibonacci number.')
            page.click('#send')

            # wait for response text to update
            page.wait_for_selector('#response:not(:text("No response yet."))', timeout=120000)
            text = page.inner_text('#response')
            assert text and len(text) > 20
            success = True
            browser.close()
    finally:
        try:
            srv.terminate()
        except Exception:
            pass

    assert success, 'Playwright E2E did not succeed'