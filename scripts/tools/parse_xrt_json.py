#!/usr/bin/env python3
import json
from pathlib import Path
p = Path(r"C:\Users\tomwo\AppData\Local\Temp\xrt_out.json")
if not p.exists():
    print('No xrt JSON file at', p)
    raise SystemExit(1)
with p.open('r', encoding='utf-8') as f:
    j = json.load(f)
devices = j.get('devices', [])
if not devices:
    print('No devices in JSON')
else:
    for dev in devices:
        did = dev.get('device_id')
        name = dev.get('platforms',[{}])[0].get('static_region',{}).get('name') or dev.get('device_id')
        partitions = dev.get('aie_partitions',{}).get('partitions',[]) or []
        print(f"Device: {did} ({name})")
        for idx, part in enumerate(partitions):
            hws = part.get('hw_contexts', [])
            total_instr_kb = 0
            for ctx in hws:
                ib = ctx.get('instr_bo_mem', '0 KB')
                try:
                    ibnum = int(str(ib).strip().split()[0])
                except Exception:
                    ibnum = 0
                total_instr_kb += ibnum
            print(f"  Partition {idx}: contexts={len(hws)}, total_instr_bo_kb={total_instr_kb}")
            print('  Contexts:')
            for ctx in hws:
                print(f"    pid={ctx.get('pid')} ctx={ctx.get('context_id')} instr_bo={ctx.get('instr_bo_mem')} gops={ctx.get('gops')}")
