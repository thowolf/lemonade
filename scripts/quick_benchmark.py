#!/usr/bin/env python3
"""Quick benchmark: send 3 prompts to server and measure latency/tokens."""
import requests
import time
from statistics import mean

BASE = "http://localhost:8000/api/v1"
MODEL = None

# Choose prompts
PROMPTS = [
    "Translate to French: 'Hello, how are you?'",
    "Summarize: 'Lemonade SDK provides easy local LLM serving on AMD hardware.'",
    "Answer concisely: 'What is the capital of France?'"
]


def get_model_from_health():
    r = requests.get(f"{BASE}/health", timeout=5)
    r.raise_for_status()
    data = r.json()
    models = data.get("all_models_loaded") or []
    if not models:
        raise RuntimeError("No models loaded on server")
    # Pick first checkpoint field or model_name
    first = models[0]
    return first.get('model_name') or first.get('checkpoint') or 'lemonade-model'


def run():
    global MODEL
    MODEL = get_model_from_health()
    print(f"Running quick benchmark against model: {MODEL}")

    results = []
    for i, prompt in enumerate(PROMPTS, 1):
        payload = {"model": MODEL, "messages": [{"role": "user", "content": prompt}], "max_tokens": 32}
        t0 = time.time()
        resp = requests.post(f"{BASE}/chat/completions", json=payload, timeout=60)
        t1 = time.time()
        latency_ms = (t1 - t0) * 1000
        try:
            data = resp.json()
        except Exception:
            data = {"error": resp.text}

        usage = data.get('usage', {})
        completion_tokens = usage.get('completion_tokens') or 0
        prompt_tokens = usage.get('prompt_tokens') or 0
        total_tokens = usage.get('total_tokens') or 0
        text = ''
        try:
            choices = data.get('choices', [])
            if choices:
                text = choices[0].get('message', {}).get('content', '')
        except Exception:
            text = ''

        results.append({
            'prompt': prompt,
            'status': resp.status_code,
            'latency_ms': latency_ms,
            'completion_tokens': completion_tokens,
            'prompt_tokens': prompt_tokens,
            'total_tokens': total_tokens,
            'reply_snippet': (text[:200] + '...') if len(text) > 200 else text
        })
        print(f"[{i}/{len(PROMPTS)}] {resp.status_code} latency={latency_ms:.1f}ms tokens={total_tokens}")

    # Summary
    latencies = [r['latency_ms'] for r in results]
    totals = [r['total_tokens'] for r in results]
    print("\nBenchmark summary:")
    print(f"  samples: {len(results)}")
    print(f"  latency_ms: mean={mean(latencies):.1f} min={min(latencies):.1f} max={max(latencies):.1f}")
    print(f"  tokens: total={sum(totals)} mean={mean(totals):.1f}")
    print("\nPer-sample details:")
    for r in results:
        print(f" - {r['prompt']!r} -> status={r['status']} latency={r['latency_ms']:.1f}ms tokens={r['total_tokens']} reply='{r['reply_snippet']}'")

    return results


if __name__ == '__main__':
    run()
