#!/usr/bin/env python3
"""
Ryzen Hybrid Benchmark with System & Process Metrics

Sends concurrent completion requests to a local RyzenAI-backed Lemonade Server
while sampling system and process-level metrics (CPU, memory) and recent server log lines.
Saves a JSON report with summary and time-series metrics.

Usage:
    python scripts/ryzen_benchmark_with_metrics.py --concurrency 4 --requests 10 --model Llama-3.2-3B-Instruct-Hybrid

Outputs:
    results/ryzen_benchmark_metrics_<timestamp>.json

Notes:
- Requires `requests` and `psutil` packages on the target system.
- On Windows, will attempt to read the server log at $env:TEMP\\lemonade-server.log
"""

import argparse
import json
import os
import socket
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from statistics import mean
from pathlib import Path
import threading

try:
    import requests
    import psutil
except Exception as e:
    print("Missing dependency:", e)
    print("Install requirements: pip install requests psutil")
    raise SystemExit(1)

DEFAULT_URL = "http://127.0.0.1:8001/v1/completions"
RESULTS_DIR = Path("tests/rocm_max395/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def find_process_by_name(name: str):
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] and name.lower() in proc.info['name'].lower():
                return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None


def find_process_by_port(port: int):
    for conn in psutil.net_connections(kind='inet'):
        if conn.laddr and conn.laddr.port == port and conn.pid:
            try:
                return psutil.Process(conn.pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    return None


def do_request(url: str, model: str, prompt: str, max_tokens: int, timeout: int = 30) -> dict:
    payload = {"model": model, "prompt": prompt, "max_tokens": max_tokens}
    start = time.time()
    try:
        r = requests.post(url, json=payload, timeout=timeout)
        elapsed = time.time() - start
        response_json = None
        try:
            response_json = r.json()
        except Exception:
            response_json = None
        return {"status_code": r.status_code, "elapsed": elapsed, "text_len": len(r.text), "response": response_json}
    except Exception as e:
        return {"status_code": None, "elapsed": None, "error": str(e)}


class Monitor(threading.Thread):
    def __init__(self, stop_event, pid_proc, sample_interval=1.0, log_path=None):
        super().__init__(daemon=True)
        self.stop_event = stop_event
        self.pid_proc = pid_proc
        self.sample_interval = sample_interval
        self.log_path = log_path
        self.samples = []

    def sample_once(self):
        ts = time.time()
        sample = {
            'ts': ts,
            'cpu_percent': psutil.cpu_percent(interval=None),
            'memory_percent': psutil.virtual_memory().percent,
        }
        if self.pid_proc:
            try:
                sample['proc_cpu_percent'] = self.pid_proc.cpu_percent(interval=None)
                mem = self.pid_proc.memory_info()
                sample['proc_rss_mb'] = mem.rss / (1024**2)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                sample['proc_cpu_percent'] = None
                sample['proc_rss_mb'] = None
        else:
            sample['proc_cpu_percent'] = None
            sample['proc_rss_mb'] = None

        # Read last few lines of log if present
        if self.log_path and os.path.exists(self.log_path):
            try:
                with open(self.log_path, 'rb') as f:
                    f.seek(0, os.SEEK_END)
                    size = f.tell()
                    read_size = min(8192, size)
                    f.seek(max(0, size - read_size))
                    data = f.read().decode(errors='ignore')
                    sample['log_tail'] = data.splitlines()[-10:]
            except Exception as e:
                sample['log_tail'] = [f"log read error: {e}"]
        else:
            sample['log_tail'] = []

        self.samples.append(sample)

    def run(self):
        # Initialize per-process cpu_percent counters
        if self.pid_proc:
            try:
                self.pid_proc.cpu_percent(interval=None)
            except Exception:
                pass
        while not self.stop_event.is_set():
            self.sample_once()
            self.stop_event.wait(self.sample_interval)


def run_benchmark(url: str, model: str, concurrency: int, requests_per_worker: int, prompt: str, max_tokens: int, sample_interval: float):
    tasks = []
    latencies = []
    successes = 0

    # Identify process to monitor (prefer process by name, fallback to port)
    proc = find_process_by_name('ryzenai-server') or find_process_by_port(8001)
    log_path = None
    tmp_log = os.environ.get('TEMP') or os.environ.get('TMP')
    if tmp_log:
        candidate = os.path.join(tmp_log, 'lemonade-server.log')
        if os.path.exists(candidate):
            log_path = candidate

    stop_event = threading.Event()
    monitor = Monitor(stop_event, proc, sample_interval=sample_interval, log_path=log_path)
    monitor.start()

    def worker_job(i):
        try:
            res = do_request(url, model, prompt, max_tokens)
            return res
        except Exception as e:
            return {"status_code": None, "elapsed": None, "error": str(e)}

    start_all = time.time()
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        futures = [ex.submit(worker_job, i) for i in range(concurrency * requests_per_worker)]
        for fut in as_completed(futures):
            r = fut.result()
            if r.get("status_code") == 200 and r.get('elapsed') is not None:
                successes += 1
                latencies.append(r['elapsed'])

    total_time = time.time() - start_all
    stop_event.set()
    monitor.join(timeout=5)

    summary = {
        "concurrency": concurrency,
        "requests": concurrency * requests_per_worker,
        "successes": successes,
        "failures": concurrency * requests_per_worker - successes,
        "mean_latency_s": mean(latencies) if latencies else None,
        "p50_latency_s": sorted(latencies)[len(latencies) // 2] if latencies else None,
        "total_time_s": total_time,
        "throughput_req_per_s": (successes / total_time) if total_time > 0 else None,
        "samples": monitor.samples,
    }

    timestamp = time.strftime('%Y%m%d_%H%M%S')
    out_file = RESULTS_DIR / f"ryzen_benchmark_metrics_{timestamp}.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, default=str)

    return summary, out_file


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--model", default="Llama-3.2-3B-Instruct-Hybrid")
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--requests", type=int, default=5, help="requests per worker (total requests = concurrency * requests)")
    parser.add_argument("--prompt", type=str, default="Hello, how are you?",)
    parser.add_argument("--max-tokens", type=int, default=10)
    parser.add_argument("--interval", type=float, default=1.0, help="metrics sample interval (seconds)")

    args = parser.parse_args()

    try:
        summary, out_file = run_benchmark(args.url, args.model, args.concurrency, args.requests, args.prompt, args.max_tokens, args.interval)
    except requests.exceptions.ConnectionError as e:
        print("Connection error: could not reach server at", args.url)
        raise SystemExit(1)

    print(json.dumps({k: summary[k] for k in summary if k != 'samples'}, indent=2))
    print("Metrics saved to:", out_file)


if __name__ == '__main__':
    main()
