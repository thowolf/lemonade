#!/usr/bin/env python3
"""Quick server integration test: health + chat completion."""
import sys
import requests

BASE = "http://localhost:8000/api/v1"

try:
    r = requests.get(f"{BASE}/health", timeout=5)
    r.raise_for_status()
    health = r.json()
except Exception as e:
    print(f"Health check failed: {e}")
    sys.exit(2)

models = health.get("all_models_loaded") or []
if not models:
    print("No loaded models reported in /health; aborting test.")
    sys.exit(3)

# Choose first available model identifier
first = models[0]
model_name = first.get("model_name") or first.get("checkpoint")
print(f"Using model from health: {model_name}")

payload = {
    "model": model_name,
    "messages": [{"role": "user", "content": "Say hello and identify yourself briefly."}],
    "max_tokens": 32,
}

try:
    resp = requests.post(f"{BASE}/chat/completions", json=payload, timeout=20)
    print(f"Status: {resp.status_code}")
    try:
        print(resp.json())
    except Exception:
        print(resp.text)
except Exception as e:
    print(f"Completion request failed: {e}")
    sys.exit(4)

print("Test finished.")
