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


def plot_comparison(model_stats: dict, out_dir: Path) -> tuple[bytes, bytes]:
    """Return raw PNG bytes for histogram and tokens/sec chart.

    Returning raw bytes allows optional upload to W&B or other services without
    needing to re-encode from base64 later.
    """
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
    hist_bytes = buf.getvalue()

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
    tps_bytes = buf.getvalue()

    return hist_bytes, tps_bytes


def generate_html_report(model_stats: dict, hist_bytes: bytes, tps_bytes: bytes, out_path: Path) -> None:
    rows = []
    for model, data in model_stats.items():
        s = data["stats"]
        rows.append(f"<tr><td>{model}</td><td>{s['samples']}</td><td>{s['mean_latency_ms']:.2f}</td><td>{s['p95_latency_ms']:.2f}</td><td>{s['mean_tps']:.2f}</td><td>{s['total_tokens']}</td></tr>")

    hist_b64 = base64.b64encode(hist_bytes).decode("ascii")
    tps_b64 = base64.b64encode(tps_bytes).decode("ascii")

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
<hr/>
<p style="font-size:0.9em;color:#666">Charts generated with Weights & Biases — <a href="https://docs.wandb.ai/models/track" target="_blank" rel="noopener">W&B Model Track docs</a></p>
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
    parser.add_argument("--wandb", action="store_true", help="Upload report and charts to W&B and create a Weave view if available")
    parser.add_argument("--project", default="lemonade-ryzenai-evals-demo", help="W&B project name")
    args = parser.parse_args()

    models = [m.strip() for m in args.models.split(",")]
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    def log_to_wandb(project_name: str, model_stats: dict, hist_bytes: bytes, tps_bytes: bytes, report_path: Path) -> None:
        try:
            import wandb
        except Exception:
            print("wandb not installed or available; skipping W&B upload")
            return

        # Add tags indicating this is a comparison run and which models are included
        tags = ["compare"]
        try:
            tags.extend([f"model:{m}" for m in model_stats.keys()])
        except Exception:
            pass

        try:
            run = wandb.init(project=project_name or "lemonade-ryzenai-evals", job_type="model_comparison", tags=tags, reinit=True)
        except Exception as e:
            print(f"Warning: Failed to initialize W&B run: {e}")
            return

        # Log metrics per model
        for model, data in model_stats.items():
            s = data["stats"]
            try:
                run.log({
                    f"{model}/mean_latency_ms": s["mean_latency_ms"],
                    f"{model}/p95_latency_ms": s["p95_latency_ms"],
                    f"{model}/mean_tps": s["mean_tps"],
                    f"{model}/total_tokens": s["total_tokens"],
                })
            except Exception as e:
                print(f"Warning: Failed to log metrics for {model}: {e}")
        # Attach images
        try:
            from PIL import Image
            import io as _io
            img1 = Image.open(_io.BytesIO(hist_bytes))
            img2 = Image.open(_io.BytesIO(tps_bytes))
            run.log({
                "charts/latency_histogram": wandb.Image(img1, caption="Latency histogram"),
                "charts/tokens_per_sec": wandb.Image(img2, caption="Tokens/sec per sample"),
            })
        except Exception as e:
            # Fallback: write files and attach
            try:
                tmp_hist = report_path.parent / "latency_hist.png"
                tmp_tps = report_path.parent / "tokens_per_sec.png"
                tmp_hist.write_bytes(hist_bytes)
                tmp_tps.write_bytes(tps_bytes)
                run.log({
                    "charts/latency_histogram": wandb.Image(str(tmp_hist)),
                    "charts/tokens_per_sec": wandb.Image(str(tmp_tps)),
                })
            except Exception as e2:
                print(f"Warning: Failed to attach images to W&B run: {e2}")

        try:
            wandb.save(str(report_path))
        except Exception as e:
            print(f"Warning: failed to save report to wandb: {e}")

        try:
            print("W&B run URL:", run.url)
        except Exception:
            pass

        try:
            run.finish()
        except Exception:
            pass

    def create_weave_savedview_from_wandb(project_name: str | None = None, models: list[str] | None = None) -> None:
        """Create an enhanced Weave SavedView after uploading a comparison run to W&B.

        This finds the most recent W&B run in the project (preferably the comparison run),
        and creates:
         - a Markdown SavedView embedding the uploaded histogram/tps images and run link
         - a runs SavedView with preconfigured charts (p95 latency, mean tokens/sec)
        """
        try:
            import wandb
            import weave
        except Exception:
            print("wandb or weave not available; skipping Weave SavedView creation")
            return

        api = wandb.Api()
        proj = project_name or "tom-rally-/lemonade-ryzenai-evals-demo"
        runs = api.runs(proj, order='-created_at')
        if not runs:
            print("No runs found for project; skipping Weave SavedView creation")
            return
        run = runs[0]

        # Find image file URLs in the run
        files = list(run.files())
        img_files = [f for f in files if f.name and "media/images/charts" in f.name]
        histogram_url = None
        tps_url = None
        for f in img_files:
            if "latency_histogram" in f.name:
                histogram_url = f.url
            if "tokens_per_sec" in f.name:
                tps_url = f.url

        # Build a Markdown view embedding images and basic stats
        summary = run.summary or {}
        mean_latency = summary.get("summary/mean_latency_ms")
        p95_latency = summary.get("summary/p95_latency_ms")
        mean_tps = summary.get("summary/mean_tps")

        md = f"""# Model Comparison — Quick Overview

Project: [{proj}](https://wandb.ai/{proj})  
Run: [{run.name}]({run.url})

"""
        if models:
            md += "**Models compared:** " + ", ".join(models) + "\n\n"

        md += f"- Mean latency: **{mean_latency or 'N/A'} ms**  \n- P95 latency: **{p95_latency or 'N/A'} ms**  \n- Mean tokens/sec: **{mean_tps or 'N/A'}**\n\n"
        if histogram_url:
            md += f"### Latency Histogram\n\n![latency histogram]({histogram_url})\n\n"
        if tps_url:
            md += f"### Tokens/sec per sample\n\n![tokens/sec]({tps_url})\n\n"

        # Add reference to W&B Model Track docs
        md += "Learn more: [W&B Model Track docs](https://docs.wandb.ai/models/track)\n"

        # Publish Markdown view
        weave.init(project_name=project_name or proj)

        @weave.op
        def add_markdown_view():
            weave.set_view('compare_models_overview', md, extension='md', mimetype='text/markdown', metadata={'project': project_name or proj})
            return 'ok'

        try:
            add_markdown_view()
            print('Created Markdown Weave view for comparison run')
        except Exception as e:
            print(f'Warning: failed to create markdown view: {e}')

        # Create runs view with charts
        try:
            runs_view = weave.SavedView(view_type='runs', label='comparison_runs')
            runs_view.base.definition.charts = [
                { 'title': 'P95 latency (runs)', 'type': 'line', 'metric': 'summary/p95_latency_ms' },
                { 'title': 'Mean tokens/sec', 'type': 'line', 'metric': 'summary/mean_tps' }
            ]
            runs_view.save()
            print('Saved runs view with charts:', runs_view.ui_url())
        except Exception as e:
            print(f'Warning: failed to create runs SavedView: {e}')
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

    hist_bytes, tps_bytes = plot_comparison({m: {"latencies": model_stats[m]["latencies"], "tps": model_stats[m]["tps"]} for m in model_stats}, out_dir)

    report_path = out_dir / f"compare_{'_'.join(m.replace('/','_') for m in models)}.html"
    generate_html_report({m: model_stats[m] for m in model_stats}, hist_bytes, tps_bytes, report_path)

    # Optional: upload to W&B and create a Weave view if requested
    if getattr(args, 'wandb', False):
        log_to_wandb(args.project or None, {m: model_stats[m] for m in model_stats}, hist_bytes, tps_bytes, report_path)
        # After successful W&B upload, create an interactive Weave SavedView for quick inspection
        try:
            create_weave_savedview_from_wandb(args.project or None, models)
        except Exception as e:
            print(f"Warning: failed to create Weave SavedView: {e}")

    print("Report generated:", report_path)


if __name__ == "__main__":
    main()
