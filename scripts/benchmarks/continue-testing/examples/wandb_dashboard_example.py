"""Example script demonstrating how to fetch run summaries from W&B and compute simple aggregates.

This example is intentionally lightweight and defensive: it will operate when a local
`wandb` installation is available and can be monkeypatched for tests.

Usage:
    python examples/wandb_dashboard_example.py --project my-org/my-project

The script exposes a testable function `fetch_project_run_stats` which returns an aggregated
summary dictionary that can be used to build dashboards or charts.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


def fetch_project_run_stats(project: str, limit: int = 20, wandb_module: Optional[Any] = None) -> Dict[str, Any]:
    """Fetch recent runs for `project` and compute aggregate metrics.

    Args:
        project: W&B project path (e.g., "org/project" or project name depending on API).
        limit: maximum number of runs to query.
        wandb_module: Optional wandb module to use (allows injection of test doubles).

    Returns:
        A dict with per-run info and aggregated statistics (mean of numeric summaries).
    """
    if wandb_module is None:
        try:
            import wandb as wandb_module  # type: ignore
        except Exception:
            raise RuntimeError("wandb is not available; install wandb or pass a wandb_module")

    api_cls = getattr(wandb_module, "Api", None)
    if api_cls is None:
        raise RuntimeError("wandb.Api is not available in provided module")

    api = api_cls()
    runs = api.runs(project=project)

    runs = list(runs)[:limit]

    per_run: List[Dict[str, Any]] = []
    numeric_values = {}
    for r in runs:
        name = getattr(r, "name", None) or getattr(r, "id", None)
        summary = getattr(r, "summary", {}) or {}
        config = getattr(r, "config", {}) or {}
        per_run.append({"name": name, "summary": dict(summary), "config": dict(config)})
        # Collect numeric summaries
        for k, v in summary.items():
            try:
                val = float(v)
            except Exception:
                continue
            numeric_values.setdefault(k, []).append(val)

    aggregates = {k: (sum(v) / len(v) if v else None) for k, v in numeric_values.items()}

    return {"project": project, "count": len(per_run), "per_run": per_run, "aggregates": aggregates}


def compute_avg_from_per_run(per_run: list) -> dict:
    """Compute simple numeric aggregates from a list of per-run dicts.

    Args:
        per_run: list of dicts each containing a 'summary' mapping of numeric metrics.

    Returns:
        Dict mapping metric name to mean value across runs.
    """
    numeric_values = {}
    for r in per_run:
        summary = r.get("summary", {}) or {}
        for k, v in summary.items():
            try:
                val = float(v)
            except Exception:
                continue
            numeric_values.setdefault(k, []).append(val)
    return {k: (sum(v) / len(v) if v else None) for k, v in numeric_values.items()}


def generate_dashboard(project: str, out_dir: str = "artifacts", limit: int = 50, wandb_module: Optional[Any] = None) -> dict:
    """Generate simple dashboard artifacts (CSV and PNG plots) for a W&B project.

    This function fetches runs via :func:`fetch_project_run_stats`, converts the
    results to a DataFrame, computes aggregates, creates two plots (bar chart
    with per-run numeric metric and a line chart of aggregates), and writes
    CSV/PNG artifacts into ``out_dir``.

    Args:
        project: W&B project path or identifier.
        out_dir: Directory to create artifacts in (will be created if missing).
        limit: Maximum number of runs to fetch.
        wandb_module: Optional wandb module to use (for testing/offline use).

    Returns:
        A dictionary with paths to generated artifacts and the computed aggregates.
    """
    import os
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns

    stats = fetch_project_run_stats(project, limit=limit, wandb_module=wandb_module)
    per_run = stats.get("per_run", [])
    df = pd.DataFrame([{"name": r.get("name"), **r.get("summary", {})} for r in per_run])

    os.makedirs(out_dir, exist_ok=True)
    csv_path = os.path.join(out_dir, f"{project.replace('/', '_')}_per_run.csv")
    df.to_csv(csv_path, index=False)

    # Bar plot of a common numeric metric (pick first numeric column)
    numeric_cols = [c for c in df.columns if c != "name"]
    plots = {}

    if numeric_cols:
        col = numeric_cols[0]
        plt.figure(figsize=(8, 4))
        sns.barplot(data=df, x="name", y=col, palette="viridis")
        plt.title(f"Per-run {col}")
        plt.xticks(rotation=45, ha='right')
        bar_path = os.path.join(out_dir, f"{project.replace('/', '_')}_per_run_{col}.png")
        plt.tight_layout()
        plt.savefig(bar_path, dpi=150)
        plt.close()
        plots["bar"] = bar_path

    # Aggregates line plot
    aggregates = compute_avg_from_per_run(per_run)
    if aggregates:
        keys = list(aggregates.keys())
        vals = [aggregates[k] for k in keys]
        plt.figure(figsize=(6, 3))
        sns.lineplot(x=keys, y=vals, marker="o")
        plt.title("Aggregates")
        plt.ylabel("value")
        agg_path = os.path.join(out_dir, f"{project.replace('/', '_')}_aggregates.png")
        plt.tight_layout()
        plt.savefig(agg_path, dpi=150)
        plt.close()
        plots["aggregates"] = agg_path

    return {"csv": csv_path, "plots": plots, "aggregates": aggregates}


def upload_artifacts_to_wandb(artifacts: dict | list, project: str, run_name: str | None = None, wandb_module: Optional[Any] = None) -> dict:
    """Upload generated artifacts (CSV/PNG) to Weights & Biases.

    The function is defensive: it accepts either a mapping produced by
    :func:`generate_dashboard` or a flat list of file paths, supports passing
    a `wandb_module` for offline testing, and tolerates environments where
    W&B is not installed.

    Returns a dict with keys: `uploaded` (bool), `details` (list of uploaded
    paths) and `error` (optional error message).
    """
    import os

    # Normalize files list
    files = []
    if isinstance(artifacts, dict):
        if "csv" in artifacts and artifacts["csv"]:
            files.append(artifacts["csv"])
        plots = artifacts.get("plots") or {}
        if isinstance(plots, dict):
            files.extend(list(plots.values()))
        elif isinstance(plots, list):
            files.extend(plots)
    elif isinstance(artifacts, list):
        files.extend(artifacts)

    files = [str(f) for f in files if f]

    # Resolve wandb module
    if wandb_module is None:
        try:
            import wandb as wandb_module  # type: ignore
        except Exception as e:
            return {"uploaded": False, "details": [], "error": f"wandb unavailable: {e}"}

    # Start a run if available
    init = getattr(wandb_module, "init", None)
    if not callable(init):
        return {"uploaded": False, "details": [], "error": "wandb.init not available"}

    try:
        run = init(project=project, name=run_name)
    except Exception as e:
        return {"uploaded": False, "details": [], "error": f"failed to init wandb run: {e}"}

    uploaded = []
    try:
        # Prefer artifact API if available
        Artifact = getattr(wandb_module, "Artifact", None)
        log_artifact = getattr(run, "log_artifact", None) or getattr(wandb_module, "log_artifact", None)
        if Artifact is not None and callable(Artifact) and callable(log_artifact):
            art = Artifact(name=f"{project.replace('/', '_')}_artifacts", type="dashboard")
            for p in files:
                if os.path.exists(p):
                    try:
                        art.add_file(p)
                        uploaded.append(p)
                    except Exception:
                        pass
            try:
                log_artifact(art)
            except Exception:
                pass
        else:
            # Fall back to wandb.save per-file
            save = getattr(wandb_module, "save", None)
            if callable(save):
                for p in files:
                    if os.path.exists(p):
                        try:
                            save(p)
                            uploaded.append(p)
                        except Exception:
                            pass
            else:
                # No supported upload method
                return {"uploaded": False, "details": [], "error": "no artifact or save API available in wandb module"}
    finally:
        finish = getattr(wandb_module, "finish", None)
        if callable(finish):
            try:
                finish()
            except Exception:
                pass

    return {"uploaded": bool(uploaded), "details": uploaded}



if __name__ == "__main__":
    import argparse
    import json

    p = argparse.ArgumentParser(prog="wandb_dashboard_example.py")
    p.add_argument("--project", required=True)
    p.add_argument("--limit", type=int, default=20)
    args = p.parse_args()

    stats = fetch_project_run_stats(args.project, limit=args.limit)
    print(json.dumps(stats, indent=2))
