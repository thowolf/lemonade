import pytest
import subprocess
import sys
import requests
import time

SERVER_URL = "http://127.0.0.1:8001/v1/completions"
MODEL = "Llama-3.2-3B-Instruct-Hybrid"


@pytest.mark.integration
def test_ryzen_benchmark_quick():
    """Quick benchmark smoke test: skip if server not available."""
    try:
        r = requests.get("http://127.0.0.1:8001/health", timeout=2)
        if r.status_code != 200:
            pytest.skip("RyzenAI server not healthy")
    except requests.exceptions.RequestException:
        pytest.skip("RyzenAI server not reachable")

    # Run a few serial requests as a quick smoke test
    latencies = []
    for i in range(3):
        payload = {"model": MODEL, "prompt": "Hello", "max_tokens": 8}
        start = time.time()
        r = requests.post(SERVER_URL, json=payload, timeout=30)
        assert r.status_code == 200
        latencies.append(time.time() - start)

    avg_latency = sum(latencies) / len(latencies)

    # Basic assertion: avg latency must be < 5s for a hybrid NPU setup (generous threshold)
    assert avg_latency < 5.0
