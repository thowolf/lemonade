#!/usr/bin/env python3
"""Sample xrt-smi JSON output repeatedly and produce a small time-series summary.

Usage:
    python scripts/tools/sample_xrt_time_series.py --duration 10 --interval 1

Requires: xrt-smi available on PATH.
"""
import argparse
import json
import subprocess
import tempfile
import time
import os
from datetime import datetime


def run_xrt_out(tmp_path):
    # Run examine with JSON output to file
    cmd = ['xrt-smi', 'examine', '-r', 'all', '-f', 'JSON', '-o', str(tmp_path)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        return {'error': proc.stderr.strip()}
    try:
        with open(tmp_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        return {'error': f'parse_error: {e}'}


def extract_metrics(j):
    # Extract some useful summary metrics: total instr_bo per partition, gops sums, device count
    out = {}
    devices = j.get('devices') if isinstance(j, dict) else None
    if not devices:
        return {'error': 'no_devices'}
    devs = []
    for dev in devices:
        d = {}
        d['device_id'] = dev.get('device_id')
        d['name'] = dev.get('platforms',[{}])[0].get('static_region',{}).get('name') if dev.get('platforms') else None
        parts = dev.get('aie_partitions',{}).get('partitions',[]) or []
        part_summaries = []
        for p in parts:
            hw = p.get('hw_contexts',[]) or []
            total_instr_kb = 0
            total_gops = 0
            for ctx in hw:
                ib = ctx.get('instr_bo_mem','0 KB')
                try:
                    ibnum = int(str(ib).strip().split()[0])
                except Exception:
                    ibnum = 0
                total_instr_kb += ibnum
                try:
                    g = int(str(ctx.get('gops') or 0))
                except Exception:
                    try:
                        g = int(float(str(ctx.get('gops') or 0)))
                    except Exception:
                        g = 0
                total_gops += g
            part_summaries.append({'contexts': len(hw), 'total_instr_bo_kb': total_instr_kb, 'total_gops': total_gops})
        d['partitions'] = part_summaries
        devs.append(d)
    out['devices'] = devs
    return out


def sample(duration, interval):
    tmp = os.path.join(tempfile.gettempdir(), f"xrt_sample_{int(time.time())}.json")
    samples = []
    end = time.time() + duration
    while time.time() < end:
        ts = datetime.utcnow().isoformat() + 'Z'
        j = run_xrt_out(tmp)
        metrics = extract_metrics(j) if isinstance(j, dict) else {'error': 'invalid_json'}
        samples.append({'ts': ts, 'metrics': metrics})
        # small sleep until next interval
        time.sleep(interval)
    # cleanup
    try:
        if os.path.exists(tmp):
            os.remove(tmp)
    except Exception:
        pass
    return samples


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--duration', type=int, default=10, help='Duration in seconds to sample')
    parser.add_argument('--interval', type=float, default=1.0, help='Sample interval in seconds')
    args = parser.parse_args()
    print(f"Sampling xrt-smi for {args.duration}s at {args.interval}s interval...")
    s = sample(args.duration, args.interval)
    print(json.dumps(s, indent=2))

if __name__ == '__main__':
    main()
