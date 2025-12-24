#!/usr/bin/env python3
"""Compare two models either from offline JSON results or by running a live micro-benchmark against local server.

Usage examples:
  # Offline (use JSON files in a directory named by model)
  python scripts/benchmarks/compare_models.py --mode offline --models qwen,llama-3.1-8B --results-dir tests/data --out-dir reports

  # Live (run small benchmark against local server)
  python scripts/benchmarks/compare_models.py --mode live --models qwen,llama-3.1-8B --server http://localhost:8000 --samples 5 --out-dir reports

Generates an HTML comparison report under `--out-dir`.
"""
from __future__ import annotations
import argparse
import json
import math
import os
import time
from pathlib import Path
from statistics import mean
import base64
import io

try:
    import matplotlib.pyplot as plt
except Exception:
    raise SystemExit("matplotlib is required; pip install matplotlib")

import requests


def load_results_from_json(results_dir: Path, model: str) -> list[dict]:
    # Look for files like <model>_*.json or files under subdir named model
    files = list(results_dir.glob(f"{model}*.json"))
    files += list((results_dir / model).glob("*.json")) if (results_dir / model).exists() else []
    samples = []
    for f in files:
        data = json.loads(f.read_text())
        if isinstance(data, dict) and "results" in data:
            samples.extend(data["results"])
        elif isinstance(data, list):
            samples.extend(data)
        else:
            samples.append(data)
    return samples


def run_live_samples(server: str, model: str, prompts: list[str], samples: int = 5) -> list[dict]:
    samples_out = []
    url = server.rstrip("/") + "/chat/completions"
    headers = {"Content-Type": "application/json"}
    for i in range(samples):
        prompt = prompts[i % len(prompts)]
        body = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 100
        }
        start = time.time()
        r = requests.post(url, json=body, headers=headers, timeout=30)
        elapsed = (time.time() - start) * 1000.0
        try:
            j = r.json()
        except Exception:
            j = {"error": r.text}
        sample = {
            "index": i + 1,
            "prompt": prompt,
            "latency_ms": elapsed,
            "status": r.status_code,
            "response": j,
        }
        samples_out.append(sample)
    return samples_out


def extract_stats(samples: list[dict]) -> dict:
    latencies = [float(s.get("latency_ms", s.get("duration_ms", 0))) for s in samples if s.get("latency_ms") is not None or s.get("duration_ms") is not None]
    tokens = [int(s.get("total_tokens", s.get("tokens", 0))) for s in samples]
    stats = {}
    if latencies:
        lat_sorted = sorted(latencies)
        stats["mean_latency_ms"] = mean(lat_sorted)
        idx_p95 = int(math.ceil(0.95 * len(lat_sorted))) - 1
        stats["p95_latency_ms"] = lat_sorted[max(0, idx_p95)]
    else:
        stats["mean_latency_ms"] = 0.0
        stats["p95_latency_ms"] = 0.0

    stats["mean_tps"] = mean([ (t / (l/1000.0)) if l>0 else 0.0 for t, l in zip(tokens, latencies) ]) if latencies and any(tokens) else 0.0
    stats["samples"] = len(samples)
    stats["total_tokens"] = sum(tokens)
    return stats


def plot_comparison(model_stats: dict, out_dir: Path) -> tuple[str,str]:
    # model_stats: {model: {latencies:[], tps:[], stats:{}}}
    # Latency histogram overlay
    plt.figure(figsize=(8,4))
    for model, data in model_stats.items():
        plt.hist(data["latencies"], bins=30, alpha=0.5, label=model)
    plt.title("Latency Histogram (ms)")
    plt.xlabel("Latency (ms)")
    plt.ylabel("Count")
    plt.legend()
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)
    hist_b64 = base64.b64encode(buf.read()).decode("ascii")

    # Tokens/sec line
    plt.figure(figsize=(8,4))
    for model, data in model_stats.items():
        plt.plot(range(1, len(data["tps"])+1), data["tps"], marker='o', label=model)
    plt.title("Tokens/sec per sample")
    plt.xlabel("Sample #")
    plt.ylabel("Tokens/sec")
    plt.legend()
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)
    tps_b64 = base64.b64encode(buf.read()).decode("ascii")

    return hist_b64, tps_b64


def generate_html_report(model_stats: dict, hist_b64: str, tps_b64: str, out_path: Path) -> None:
    rows = []
    for model, data in model_stats.items():
        s = data["stats"]
        rows.append(f"<tr><td>{model}</td><td>{s['samples']}</td><td>{s['mean_latency_ms']:.2f}</td><td>{s['p95_latency_ms']:.2f}</td><td>{s['mean_tps']:.2f}</td><td>{s['total_tokens']}</td></tr>")

    html = f'''<!doctype html>
<html><head><meta charset="utf-8"><title>Model comparison</title></head><body>
<h1>Model comparison</h1>
<table border=1><tr><th>Model</th><th>Samples</th><th>Mean latency (ms)</th><th>P95 latency (ms)</th><th>Mean tokens/sec</th><th>Total tokens</th></tr>
{''.join(rows)}
</table>
<h2>Latency histogram</h2>
<img src="data:image/png;base64,{hist_b64}" style="max-width:100%;height:auto"/>
<h2>Tokens/sec per sample</h2>
<img src="data:image/png;base64,{tps_b64}" style="max-width:100%;height:auto"/>
</body></html>'''
    out_path.write_text(html, encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["offline","live"], default="offline")
    parser.add_argument("--models", required=True, help="Comma separated model names (e.g. qwen,llama-3.1-8B)")
    parser.add_argument("--results-dir", default="evaluation_results_large", help="Directory with offline results")
    parser.add_argument("--server", default="http://localhost:8000", help="Local server URL for live mode")
    parser.add_argument("--samples", type=int, default=10, help="Number of samples per model for live mode")
    parser.add_argument("--out-dir", default="reports", help="Output directory")
    args = parser.parse_args()

    models = [m.strip() for m in args.models.split(",")]
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    model_stats = {}

    prompts = [
        "Translate to French: 'Hello, how are you?'",
        "Summarize: 'Lemonade SDK provides easy local LLM serving on AMD hardware.'",
        "Answer concisely: 'What is the capital of France?'",
    ]

    for model in models:
        if args.mode == "offline":
            samples = load_results_from_json(Path(args.results_dir), model)
        else:
            samples = run_live_samples(args.server, model, prompts, samples=args.samples)
        lat = [float(s.get("latency_ms", 0)) for s in samples]
        tps = [float(s.get("tokens_per_second", s.get("tokens_per_sec", 0))) for s in samples]
        stats = extract_stats(samples)
        model_stats[model] = {"latencies": lat, "tps": tps, "stats": stats, "samples": samples}

    hist_b64, tps_b64 = plot_comparison({m: {"latencies": model_stats[m]["latencies"], "tps": model_stats[m]["tps"]} for m in model_stats}, out_dir)

    report_path = out_dir / f"compare_{'_'.join(m.replace('/','_') for m in models)}.html"
    generate_html_report({m: model_stats[m] for m in model_stats}, hist_b64, tps_b64, report_path)

    print("Report generated:", report_path)


if __name__ == "__main__":
    main()
