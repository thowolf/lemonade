#!/usr/bin/env python3
"""Sync offline W&B runs in ./wandb to the cloud project."""
import subprocess
import sys

cmd = [sys.executable, '-m', 'wandb', 'sync', './wandb', '--project', 'lemonade-ryzenai-evals-demo']
print('Running:', ' '.join(cmd))
res = subprocess.run(cmd, capture_output=True, text=True)
print('Return code:', res.returncode)
print(res.stdout)
print(res.stderr)
if res.returncode != 0:
    raise SystemExit('wandb sync failed')
print('W&B sync completed')
