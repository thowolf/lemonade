"""Diagnostics helpers for collecting system snapshots and logs."""
from __future__ import annotations

import os
import psutil
import shutil
import tarfile
import time
from typing import List

from scripts.benchmarks.continue_testing.metrics_collector import SystemMonitor


def collect_system_snapshot(output_path: str, run_id: str, extra_paths: List[str] = None) -> str:
    """Collect a snapshot of system state: process list, metrics, and provided paths (logs). Returns path to tarball."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    staging_dir = os.path.join(os.path.dirname(output_path), f"snapshot_{run_id}_{int(time.time())}")
    os.makedirs(staging_dir, exist_ok=True)

    # Write process list
    proc_file = os.path.join(staging_dir, "processes.txt")
    with open(proc_file, "w", encoding="utf-8") as f:
        for p in psutil.process_iter(['pid', 'name', 'cmdline', 'status']):
            try:
                f.write(repr(p.info) + "\n")
            except Exception:
                continue

    # Collect a small set of metrics
    monitor = SystemMonitor()
    metrics = monitor.sample(run_id=run_id)
    with open(os.path.join(staging_dir, "metrics.json"), "w", encoding="utf-8") as f:
        f.write(metrics.to_json())

    # Copy extra paths (logs) if provided
    if extra_paths:
        logs_dir = os.path.join(staging_dir, "logs")
        os.makedirs(logs_dir, exist_ok=True)
        for p in extra_paths:
            try:
                if os.path.isdir(p):
                    shutil.copytree(p, os.path.join(logs_dir, os.path.basename(p)))
                elif os.path.isfile(p):
                    shutil.copy2(p, logs_dir)
            except Exception:
                continue

    # Create tar.gz
    tar_path = output_path
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(staging_dir, arcname=os.path.basename(staging_dir))

    # Cleanup staging
    shutil.rmtree(staging_dir, ignore_errors=True)
    return tar_path
