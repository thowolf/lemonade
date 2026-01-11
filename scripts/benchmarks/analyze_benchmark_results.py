#!/usr/bin/env python3
"""Summarize benchmark JSON results into a markdown table

Usage:
  python scripts/benchmarks/analyze_benchmark_results.py
"""
import glob
import json
from pathlib import Path
from datetime import datetime

RESULTS = Path('tests/results')
out = []
for p in sorted(RESULTS.glob('ryzen_benchmark_metrics_*.json')):
    try:
        j = json.loads(p.read_text())
    except Exception:
        continue
    # Try to detect model name from first sample log_tail
    model = None
    samples = j.get('samples', [])
    if samples:
        tail = samples[0].get('log_tail', [])
        for line in tail:
            if 'Auto-loading model:' in line:
                model = line.split('Auto-loading model:')[-1].strip()
                break
            if 'Auto-loading model' in line:
                model = line.split(':')[-1].strip()
                break
    out.append({
        'file': str(p),
        'model': model or 'unknown',
        'concurrency': j.get('concurrency'),
        'requests': j.get('requests'),
        'mean_latency_s': j.get('mean_latency_s'),
        'throughput_req_per_s': j.get('throughput_req_per_s'),
        'npu_device_count_max': j.get('npu_device_count_max'),
        'npu_command_avg_rate': (j.get('npu_metrics_agg', {}).get('command_submissions', {}).get('avg_rate_per_s')),
        'npu_gops_max': (j.get('npu_metrics_agg', {}).get('gops', {}).get('max')),
    })

# Write markdown summary
now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')
out_md = RESULTS / f'benchmark_summary_{now}.md'
with open(out_md, 'w', encoding='utf-8') as f:
    f.write('| model | concurrency | requests | mean_latency_s | throughput_req_per_s | npu_device_count_max | npu_command_avg_rate/s | npu_gops_max |\n')
    f.write('|---|---:|---:|---:|---:|---:|---:|---:|\n')
    for r in out:
        f.write(f"| {r['model']} | {r['concurrency']} | {r['requests']} | {r['mean_latency_s'] or ''} | {r['throughput_req_per_s'] or ''} | {r['npu_device_count_max'] or ''} | {r['npu_command_avg_rate'] or ''} | {r['npu_gops_max'] or ''} |\n")

print('Wrote summary to', out_md)
print('Rows:', len(out))
