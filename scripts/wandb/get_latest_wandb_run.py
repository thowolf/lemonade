#!/usr/bin/env python3
import wandb
api = wandb.Api()
project='tom-rally/lemonade-ryzenai-evals-demo'
runs = api.runs(project)
print('Found runs:', len(runs))
if not runs:
    raise SystemExit('No runs found')
# sort by created_at if available
runs_sorted = sorted(runs, key=lambda r: getattr(r, 'created_at', r._attrs.get('createdAt', 0)), reverse=True)
run = runs_sorted[0]
print('Latest run URL:', run.url)
print('Weave URL:', f'https://wandb.ai/{run.entity}/{run.project}/weave')
