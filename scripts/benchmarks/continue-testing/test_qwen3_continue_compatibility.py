#!/usr/bin/env python3
"""
Integration test: qwen3-coder:30b compatibility with Lemonade/Continue (OpenAI-compatible API on port 8000)
Sends a set of Continue-like prompts to the server and saves a compatibility report to results/.
"""
from __future__ import annotations

import os
import time
import json
import requests
from typing import Dict, Any, List

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

DEFAULT_BASE_URL = os.getenv("LEMONADE_BASE_URL", "http://127.0.0.1:8000")
API_PATH = "/api/v1/chat/completions"

MODEL = os.getenv("LEMONADE_MODEL_ID", "Qwen3-Coder-30B-A3B-Instruct-GGUF")  # default to server's 30B coder id (override with LEMONADE_MODEL_ID)

# Prompts typical for Continue extension (coding assistance)
PROMPTS: List[str] = [
    "Write a Python function to implement binary search.",
    "Explain how to optimize this code for better performance:\n\ndef factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)",
    "Create a React component for a todo list with add/remove functionality.",
    "Debug this JavaScript code:\n\nfunction fetchData() {\n    return fetch('/api/data')\n        .then(response => response.json())\n        .catch(error => console.log(error));\n}",
    "Write a SQL query to find users who haven't logged in for 30 days."
]

# Default parameters tuned for stability
DEFAULT_PARAMS = {
    "max_tokens": 200,
    "temperature": 0.3,
    "top_p": 0.9,
}

TIMEOUT = 120  # seconds per request


def call_chat_completion(base_url: str, model: str, prompt: str, params: Dict[str, Any]) -> Dict[str, Any]:
    endpoint = f"{base_url.rstrip('/')}{API_PATH}"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": params.get("max_tokens"),
        "temperature": params.get("temperature"),
        "top_p": params.get("top_p"),
        "n": 1,
        "stream": False,
    }

    start = time.time()
    resp = requests.post(endpoint, json=payload, timeout=TIMEOUT)
    elapsed = time.time() - start

    if resp.status_code != 200:
        return {"success": False, "status_code": resp.status_code, "error": resp.text}

    j = resp.json()
    choices = j.get("choices", [])
    if not choices:
        return {"success": False, "status_code": resp.status_code, "error": "no choices in response"}

    first = choices[0]
    message = first.get("message") or {}
    text = message.get("content") or first.get("text", "")
    usage = j.get("usage", {})

    return {
        "success": True,
        "text": text,
        "tokens": usage.get("total_tokens", 0),
        "response_time": elapsed,
        "raw": j,
    }


def list_available_models(base_url: str = DEFAULT_BASE_URL) -> List[str]:
    try:
        resp = requests.get(f"{base_url.rstrip('/')}/api/v1/models?show_all=true", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return [m.get('id') for m in data.get('data', [])]
    except Exception:
        return []


def run_tests(base_url: str = DEFAULT_BASE_URL, model: str = MODEL, prompts: List[str] = PROMPTS, params: Dict[str, Any] = DEFAULT_PARAMS) -> Dict[str, Any]:
    # If model not available, try to find a best match on the server
    available = list_available_models(base_url)
    if model not in available:
        candidates = [m for m in available if 'qwen' in (m or '').lower() and '30' in (m or '').lower()]
        if candidates:
            print(f"Model '{model}' not found on server; using available candidate: {candidates[0]}")
            model = candidates[0]
        else:
            print(f"Model '{model}' not found on server and no 30B Qwen candidate available.")
            print("Available models (sample):", (available[:20]))
            return {
                "model": model,
                "total_tests": len(prompts),
                "successful_tests": 0,
                "success_rate_percent": 0.0,
                "average_response_time_s": None,
                "total_time": 0.0,
                "compatible_with_continue": False,
                "error": "model_not_found",
                "available_models_sample": available[:50],
            }

    results = []
    success_count = 0
    total_time = 0.0

    for i, p in enumerate(prompts, start=1):
        print(f"Test {i}/{len(prompts)}: {p[:60]}...")
        res = call_chat_completion(base_url, model, p, params)
        if res.get("success"):
            success_count += 1
            total_time += res["response_time"]
            print(f"  ✅ OK ({res['tokens']} tokens, {res['response_time']:.2f}s)")
        else:
            print(f"  ❌ FAIL: {res.get('error')}")

        results.append({"prompt": p, **res})

    success_rate = success_count / len(prompts) * 100
    avg_time = (total_time / success_count) if success_count else None

    summary = {
        "model": model,
        "base_url": base_url,
        "params": params,
        "total_tests": len(prompts),
        "successful_tests": success_count,
        "success_rate_percent": success_rate,
        "average_response_time_s": avg_time,
        "total_time": total_time,
        "compatible_with_continue": success_rate >= 80,
        "results": results,
    }

    return summary
    results = []
    success_count = 0
    total_time = 0.0

    for i, p in enumerate(prompts, start=1):
        print(f"Test {i}/{len(prompts)}: {p[:60]}...")
        res = call_chat_completion(base_url, model, p, params)
        if res.get("success"):
            success_count += 1
            total_time += res["response_time"]
            print(f"  ✅ OK ({res['tokens']} tokens, {res['response_time']:.2f}s)")
        else:
            print(f"  ❌ FAIL: {res.get('error')}")

        results.append({"prompt": p, **res})

    success_rate = success_count / len(prompts) * 100
    avg_time = (total_time / success_count) if success_count else None

    summary = {
        "model": model,
        "base_url": base_url,
        "params": params,
        "total_tests": len(prompts),
        "successful_tests": success_count,
        "success_rate_percent": success_rate,
        "average_response_time_s": avg_time,
        "results": results,
        "compatible_with_continue": success_rate >= 80,
    }

    return summary


def save_results(summary: Dict[str, Any]) -> None:
    ts = int(time.time())
    md_file = os.path.join(RESULTS_DIR, f"qwen3_continue_compatibility_{ts}.md")
    json_file = os.path.join(RESULTS_DIR, f"qwen3_continue_test_results_{ts}.json")

    # Simple markdown report
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(f"# Continue Extension Compatibility Report: {summary['model']}\n\n")
        f.write(f"- Base URL: {summary['base_url']}\n")
        f.write(f"- Success Rate: {summary['success_rate_percent']:.1f}%\n")
        f.write(f"- Average Response Time: {summary['average_response_time_s'] or 0:.2f}s\n\n")
        f.write("## Results\n")
        for r in summary['results']:
            f.write(f"- Prompt: {r['prompt'][:80]}... -> {'OK' if r.get('success') else 'FAIL'}\n")

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"Saved report to: {md_file}")
    print(f"Saved results to: {json_file}")


if __name__ == "__main__":
    base = os.getenv("LEMONADE_BASE_URL", DEFAULT_BASE_URL)
    summary = run_tests(base_url=base)
    save_results(summary)
    if summary["compatible_with_continue"]:
        print("\n🎉 qwen3-coder:30b is compatible with Continue")
        raise SystemExit(0)
    else:
        print("\n⚠️ qwen3-coder:30b may not be compatible with Continue")
        raise SystemExit(1)