#!/usr/bin/env python3
"""Create an offline HTML dashboard from evaluation result JSON files.

- Generates a latency histogram and tokens/sec chart (PNG embedded in HTML)
- Saves report under `reports/` (self-contained HTML with base64 images)
- Optionally creates a Weave saved view linking to the report or project (requires `weave` and W&B login)

Usage:
  python scripts/create_weave_dashboard.py --results-dir evaluation_results_large --out-dir reports --weave
"""
from __future__ import annotations
import argparse
import base64
import io
import json
import os
from pathlib import Path
from statistics import mean
import math

try:
    import matplotlib.pyplot as plt
except Exception as e:
    raise SystemExit("matplotlib is required to run this script. Install it with `pip install matplotlib`")


def find_latest_json(results_dir: Path) -> Path | None:
    if not results_dir.exists():
        return None
    files = sorted(results_dir.rglob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def load_samples(path: Path) -> list[dict]:
    data = json.loads(path.read_text())
    # Support several common payload shapes: top-level list, dict with 'results' or 'samples',
    # or a simple mapping of id->sample.
    if isinstance(data, dict):
        if "results" in data and isinstance(data["results"], list):
            return data["results"]
        if "samples" in data and isinstance(data["samples"], list):
            return data["samples"]
        # If it's a dict mapping ids to samples (and not lists), return values
        if all(isinstance(v, dict) for v in data.values()) and not any(isinstance(v, list) for v in data.values()):
            return list(data.values())
        # Otherwise treat the entire dict as a single sample
        return [data]
    elif isinstance(data, list):
        return data
    else:
        return [data]


def extract_metrics(samples: list[dict]) -> tuple[list[float], list[int], list[float]]:
    latencies = []
    tokens = []
    tps = []
    for s in samples:
        # latency in ms: try many common names
        latency = None
        for key in ("latency_ms", "duration_ms", "latency", "duration"):
            if key in s:
                latency = s[key]
                break
        # nested structures
        if latency is None:
            metrics = s.get("metrics") or {}
            for key in ("latency_ms", "duration_ms", "latency", "duration"):
                if key in metrics:
                    latency = metrics[key]
                    break
        if latency is None and "start_time" in s and "end_time" in s:
            try:
                latency = (float(s["end_time"]) - float(s["start_time"])) * 1000.0
            except Exception:
                latency = None
        if latency is None:
            # fallback: if sample has a single 'elapsed_ms' variant
            latency = s.get("elapsed_ms")
        if latency is None:
            # skip if we cannot find latency
            continue
        latencies.append(float(latency))

        # tokens
        t = None
        for key in ("total_tokens", "tokens", "token_count"):
            if key in s:
                t = s[key]
                break
        if t is None and s.get("usage"):
            for key in ("total_tokens", "tokens"):
                if key in s["usage"]:
                    t = s["usage"][key]
                    break
        tokens.append(int(t) if t is not None else 0)

        # tokens/sec
        seconds = max(0.001, float(latency) / 1000.0)
        tps.append((int(t) if t is not None else 0) / seconds)

    return latencies, tokens, tps


def plot_histogram(latencies: list[float]) -> bytes:
    plt.figure(figsize=(8, 4))
    plt.hist(latencies, bins=40, color="#2c7fb8", edgecolor="black")
    plt.title("Latency Histogram (ms)")
    plt.xlabel("Latency (ms)")
    plt.ylabel("Count")
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)
    return buf.read()


def plot_tps_line(tps: list[float]) -> bytes:
    plt.figure(figsize=(8, 4))
    plt.plot(range(1, len(tps) + 1), tps, marker="o", linestyle="-", color="#2c7fb8")
    plt.title("Tokens/sec per Sample")
    plt.xlabel("Sample #")
    plt.ylabel("Tokens/sec")
    plt.grid(alpha=0.25)
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)
    return buf.read()


def to_base64_png(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def generate_html(out_path: Path, summary: dict, img_hist_b64: str, img_tps_b64: str, samples_count: int) -> None:
    html = f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Lemonade Quick Benchmark Overview</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 30px; }}
    .panel {{ margin-bottom: 24px; }}
    .metrics {{ display:flex; gap:24px; }}
    .metric {{ padding:12px; border:1px solid #ddd; border-radius:6px; min-width:140px; text-align:center; }}
  </style>
</head>
<body>
  <h1>Lemonade — Quick Benchmark Overview</h1>
  <p>Samples: {samples_count}</p>

  <div class="metrics">
    <div class="metric"><strong>Mean Latency</strong><div>{summary['mean_latency']:.2f} ms</div></div>
    <div class="metric"><strong>P95 Latency</strong><div>{summary['p95_latency']:.2f} ms</div></div>
    <div class="metric"><strong>Mean Tokens/sec</strong><div>{summary['mean_tps']:.2f}</div></div>
  </div>

  <div class="panel">
    <h2>Latency Histogram</h2>
    <img src="data:image/png;base64,{img_hist_b64}" alt="Latency histogram" style="max-width:100%; height:auto;" />
  </div>

  <div class="panel">
    <h2>Tokens/sec per Sample</h2>
    <img src="data:image/png;base64,{img_tps_b64}" alt="Tokens/sec chart" style="max-width:100%; height:auto;" />
  </div>

  <hr />
  <p>Generated by <code>scripts/create_weave_dashboard.py</code>.</p>
</body>
</html>
"""
    out_path.write_text(html, encoding="utf-8")


def summary_stats(latencies: list[float], tps: list[float]) -> dict:
    if not latencies:
        return {"mean_latency": 0.0, "p95_latency": 0.0, "mean_tps": 0.0}
    lat_sorted = sorted(latencies)
    mean_latency = mean(lat_sorted)
    idx_p95 = int(math.ceil(0.95 * len(lat_sorted))) - 1
    p95_latency = lat_sorted[max(0, idx_p95)]
    mean_tps = mean(tps) if tps else 0.0
    return {"mean_latency": mean_latency, "p95_latency": p95_latency, "mean_tps": mean_tps}


def create_weave_view(view_name: str, html_report_path: Path, project_name: str | None = None) -> None:
    try:
        import weave
    except Exception:
        print("weave is not installed or cannot be imported; skipping Weave view creation")
        return
    weave.init(project_name=project_name or "lemonade-views")

    md = f"""# Lemonade Quick Benchmark Overview

The offline report is available at: `{html_report_path}`

You can also explore the project in Weights & Biases.
"""

    @weave.op
    def add_view():
        weave.set_view(view_name, md, extension="md", mimetype="text/markdown", metadata={"project": project_name or "lemonade-views"})
        return "ok"

    print("Creating Weave view...")
    add_view()
    print("Weave view creation called (check your Weave workspace)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", default="evaluation_results_large", help="Directory containing evaluation JSON results")
    parser.add_argument("--out-dir", default="reports", help="Output directory for generated HTML report")
    parser.add_argument("--file", default=None, help="Specific JSON file to use (optional)")
    parser.add_argument("--weave", action="store_true", help="Also attempt to create a Weave saved view (requires weave/wandb login)")
    parser.add_argument("--project", default=None, help="Weave/W&B project name to associate with the view (optional)")
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = Path(args.file) if args.file else find_latest_json(results_dir)
    if not json_path or not json_path.exists():
        raise SystemExit(f"No JSON results found in {results_dir}; pass --file <path> to specify a file")

    print("Using results file:", json_path)
    samples = load_samples(json_path)
    latencies, tokens, tps = extract_metrics(samples)
    if not latencies:
        raise SystemExit("No latency metrics found in samples; cannot generate dashboard")

    img_hist = plot_histogram(latencies)
    img_tps = plot_tps_line(tps)

    b64_hist = to_base64_png(img_hist)
    b64_tps = to_base64_png(img_tps)

    stats = summary_stats(latencies, tps)
    out_html = out_dir / "lemonade_quick_benchmark_overview.html"
    generate_html(out_html, stats, b64_hist, b64_tps, samples_count=len(samples))

    print("Report generated:", out_html)

    def log_to_wandb(project_name: str, stats: dict, img_hist_bytes: bytes, img_tps_bytes: bytes, report_path: Path) -> None:
        try:
            import wandb
        except Exception:
            print("wandb is not installed or cannot be imported; skipping W&B logging")
            return

        # Initialize a short-lived W&B run to upload metrics and images
        try:
            run = wandb.init(project=project_name or "lemonade-ryzenai-evals", job_type="dashboard_report", reinit=True)
        except Exception as e:
            print(f"Warning: Failed to initialize W&B run: {e}")
            return

        # Log numeric summary metrics
        try:
            run.log({
                "summary/mean_latency_ms": stats["mean_latency"],
                "summary/p95_latency_ms": stats["p95_latency"],
                "summary/mean_tps": stats["mean_tps"],
            })
        except Exception as e:
            print(f"Warning: Failed to log numeric metrics to W&B: {e}")

        # Log images (try to use Pillow; fall back to temp files)
        try:
            from PIL import Image
            import io
            img1 = Image.open(io.BytesIO(img_hist_bytes))
            img2 = Image.open(io.BytesIO(img_tps_bytes))
            run.log({
                "charts/latency_histogram": wandb.Image(img1, caption="Latency histogram"),
                "charts/tokens_per_sec": wandb.Image(img2, caption="Tokens/sec per sample"),
            })
        except Exception as e:
            # Fallback: write images to temp files and upload
            try:
                tmp_hist = report_path.parent / "latency_hist.png"
                tmp_tps = report_path.parent / "tokens_per_sec.png"
                tmp_hist.write_bytes(img_hist_bytes)
                tmp_tps.write_bytes(img_tps_bytes)
                run.log({
                    "charts/latency_histogram": wandb.Image(str(tmp_hist)),
                    "charts/tokens_per_sec": wandb.Image(str(tmp_tps)),
                })
            except Exception as e2:
                print(f"Warning: Failed to attach images to W&B run: {e2}")

        # Save the HTML report into the run directory (so it appears as an artifact in the run)
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

    def create_enhanced_weave_view_from_wandb(project_name: str, view_name: str = "lemonade_quick_benchmark_overview") -> None:
        try:
            import wandb
            import weave
        except Exception:
            print("wandb or weave not available; cannot create enhanced view")
            return

        api = wandb.Api()
        proj = project_name or "tom-rally-/lemonade-ryzenai-evals-demo"
        runs = api.runs(proj, order='-created_at')
        if not runs:
            print("No runs found for project; skipping enhanced view creation")
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

        # Use run summary keys if available
        summary = run.summary or {}
        mean_latency = summary.get("summary/mean_latency_ms")
        p95_latency = summary.get("summary/p95_latency_ms")
        mean_tps = summary.get("summary/mean_tps")

        # Build a Markdown view embedding images and metrics
        md = f"""# Lemonade — Quick Benchmark Overview

**Project:** [{proj}](https://wandb.ai/{proj})  
**Latest run:** [{run.name}]({run.url})  

**Summary metrics**

- Mean latency: **{mean_latency:.2f} ms**  
- P95 latency: **{p95_latency:.2f} ms**  
- Mean tokens/sec: **{mean_tps:.2f}**

"""
        if histogram_url:
            md += f"### Latency Histogram\n\n![latency histogram]({histogram_url})\n\n"
        if tps_url:
            md += f"### Tokens/sec per sample\n\n![tokens/sec]({tps_url})\n\n"

        # Create the view inside an op context
        weave.init(project_name=project_name or "lemonade-views")

        @weave.op
        def add_view():
            weave.set_view(view_name, md, extension="md", mimetype="text/markdown", metadata={"project": project_name or proj})
            return "ok"

        print("Creating enhanced Weave view (with embedded images)...")
        try:
            add_view()
            print("Enhanced Weave view created.")
        except Exception as e:
            print(f"Failed to create enhanced view: {e}")

    if args.weave:
        # First try to log to W&B so metrics/charts are available in the project's runs
        log_to_wandb(args.project or "lemonade-ryzenai-evals", stats, img_hist, img_tps, out_html)

        # Then create an enhanced view that embeds the uploaded chart images and metrics
        create_enhanced_weave_view_from_wandb(args.project or "tom-rally-/lemonade-ryzenai-evals-demo")


if __name__ == "__main__":
    main()
