#!/usr/bin/env python3
"""Large benchmark: run N prompts to measure latency and tokens/sec, save results."""
import requests
import time
import json
import os
from statistics import mean

BASE = "http://localhost:8000/api/v1"

PROMPT_TEMPLATES = [
    "Translate to French: 'Hello, how are you?'",
    "Summarize: 'Lemonade SDK provides easy local LLM serving on AMD hardware.'",
    "Answer concisely: 'What is the capital of France?'",
    "Explain briefly: 'How does a neural network learn?'",
    "List three benefits of using local LLM serving for privacy-sensitive apps."
]

N = 50
OUTPUT_DIR = "evaluation_results_large"


def get_model_from_health():
    r = requests.get(f"{BASE}/health", timeout=5)
    r.raise_for_status()
    data = r.json()
    models = data.get("all_models_loaded") or []
    if not models:
        raise RuntimeError("No models loaded on server")
    first = models[0]
    return first.get('model_name') or first.get('checkpoint') or 'lemonade-model'


def run(n=N):
    model = get_model_from_health()
    print(f"Running large benchmark against model: {model} (samples={n})")

    results = []
    total_tokens = 0
    start_all = time.time()

    for i in range(n):
        prompt = PROMPT_TEMPLATES[i % len(PROMPT_TEMPLATES)]
        payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 64}
        t0 = time.time()
        resp = requests.post(f"{BASE}/chat/completions", json=payload, timeout=120)
        t1 = time.time()
        latency = t1 - t0
        latency_ms = latency * 1000
        try:
            data = resp.json()
        except Exception:
            data = {"error": resp.text}

        usage = data.get('usage', {})
        completion_tokens = usage.get('completion_tokens') or 0
        prompt_tokens = usage.get('prompt_tokens') or 0
        total = usage.get('total_tokens') or (completion_tokens + prompt_tokens)
        total_tokens += total

        tps = total / latency if latency > 0 else 0.0
        text = ''
        try:
            choices = data.get('choices', [])
            if choices:
                text = choices[0].get('message', {}).get('content', '')
        except Exception:
            text = ''

        results.append({
            'index': i+1,
            'prompt': prompt,
            'status': resp.status_code,
            'latency_ms': latency_ms,
            'completion_tokens': completion_tokens,
            'prompt_tokens': prompt_tokens,
            'total_tokens': total,
            'tokens_per_second': tps,
            'reply_snippet': (text[:300] + '...') if len(text) > 300 else text
        })

        if (i+1) % 10 == 0:
            print(f"  completed {i+1}/{n}")

    end_all = time.time()
    elapsed = end_all - start_all
    avg_latency = mean([r['latency_ms'] for r in results])
    p95_latency = sorted([r['latency_ms'] for r in results])[int(len(results)*0.95)-1]
    mean_tps = mean([r['tokens_per_second'] for r in results])

    summary = {
        'model': model,
        'samples': n,
        'elapsed_seconds': elapsed,
        'total_tokens': total_tokens,
        'mean_latency_ms': avg_latency,
        'p95_latency_ms': p95_latency,
        'mean_tokens_per_second': mean_tps
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    outpath = os.path.join(OUTPUT_DIR, f'large_benchmark_{int(time.time())}.json')
    with open(outpath, 'w', encoding='utf-8') as f:
        json.dump({'summary': summary, 'results': results}, f, indent=2)

    print('\nBenchmark summary:')
    print(f"  samples: {n}")
    print(f"  elapsed: {elapsed:.1f}s")
    print(f"  mean latency: {avg_latency:.1f}ms  p95 latency: {p95_latency:.1f}ms")
    print(f"  total tokens: {total_tokens}  mean TPS (per-request): {mean_tps:.2f}")
    print(f"  results saved to: {outpath}")

    return summary, results


if __name__ == '__main__':
    run()
