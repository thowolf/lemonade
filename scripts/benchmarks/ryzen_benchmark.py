#!/usr/bin/env python3
"""
Ryzen Hybrid Benchmark

Sends concurrent completion requests to a local RyzenAI-backed Lemonade Server
and reports latency and throughput (tokens/sec).

Usage:
    python scripts/ryzen_benchmark.py --concurrency 4 --requests 20 --model Llama-3.2-3B-Instruct-Hybrid

Note: Defaults target http://127.0.0.1:8001 (ryzenai-server).
"""

import argparse
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from statistics import mean
import requests

DEFAULT_URL = "http://127.0.0.1:8001/v1/completions"


def do_request(url: str, model: str, prompt: str, max_tokens: int, timeout: int = 30) -> dict:
    payload = {
        "model": model,
        "prompt": prompt,
        "max_tokens": max_tokens
    }
    start = time.time()
    r = requests.post(url, json=payload, timeout=timeout)
    elapsed = time.time() - start
    return {"status_code": r.status_code, "elapsed": elapsed, "text_len": len(r.text), "response": r.json() if r.headers.get('content-type','').startswith('application/json') else None}


def run_benchmark(url: str, model: str, concurrency: int, requests_per_worker: int, prompt: str, max_tokens: int):
    tasks = []
    latencies = []
    successes = 0
    total_tokens_out = 0

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
            if r.get("status_code") == 200:
                successes += 1
                if r.get("elapsed"):
                    latencies.append(r["elapsed"])
                # try to extract token counts if present
                resp = r.get("response")
                if resp and isinstance(resp, dict):
                    # try known shapes
                    # many servers return choices or data with tokens; we try a few heuristics
                    if "choices" in resp:
                        # assume text length as proxy
                        total_tokens_out += 1
                    elif "data" in resp and isinstance(resp["data"], dict):
                        total_tokens_out += 1
            else:
                # treat as failure; try to capture error
                pass

    total_time = time.time() - start_all
    summary = {
        "concurrency": concurrency,
        "requests": concurrency * requests_per_worker,
        "successes": successes,
        "failures": concurrency * requests_per_worker - successes,
        "mean_latency_s": mean(latencies) if latencies else None,
        "p50_latency_s": sorted(latencies)[len(latencies) // 2] if latencies else None,
        "total_time_s": total_time,
        "throughput_req_per_s": (successes / total_time) if total_time > 0 else None,
        "tokens_out": total_tokens_out,
    }
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--model", default="Llama-3.2-3B-Instruct-Hybrid")
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--requests", type=int, default=20, help="requests per worker (total requests = concurrency * requests)")
    parser.add_argument("--prompt", type=str, default="Hello, how are you?",)
    parser.add_argument("--max-tokens", type=int, default=10)

    args = parser.parse_args()

    try:
        summary = run_benchmark(args.url, args.model, args.concurrency, args.requests, args.prompt, args.max_tokens)
    except requests.exceptions.ConnectionError as e:
        print("Connection error: could not reach server at", args.url)
        raise SystemExit(1)

    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
