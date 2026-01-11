#!/usr/bin/env python3
import os, json, glob
root = os.path.join(os.getcwd(), 'wandb')
entries = []
for d in glob.glob(os.path.join(root, '**', 'files', 'wandb-summary.json'), recursive=True):
    try:
        j = json.load(open(d))
        v = None
        # try a few keys
        if 'resources' in j and isinstance(j['resources'], dict):
            v = j['resources'].get('vram_usage_mb')
        if not v:
            for k in ('resources/vram_usage_mb','resources.vram_usage_mb','resources_vram_usage_mb','resources_vram_usage_mb'):
                if k in j:
                    v = j[k]
                    break
        if v is not None:
            entries.append((d, float(v), j.get('_timestamp',0)))
    except Exception:
        continue
if not entries:
    print('No wandb vram entries found')
else:
    entries_sorted = sorted(entries, key=lambda x: x[2], reverse=True)
    for p,v,t in entries_sorted[:5]:
        print(f"{p} -> {v:.2f} MB (ts={t})")
    print('Total matches:', len(entries))
