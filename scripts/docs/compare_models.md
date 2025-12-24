# compare_models.py

This helper compares two models either from offline JSON results or by running a small live benchmark against a local Lemonade server.

Usage examples:

- Offline (compare results from `tests/data`):

```bash
python scripts/benchmarks/compare_models.py --mode offline --models qwen,Llama-3.1-8B-Instruct-Hybrid --results-dir tests/data --out-dir reports
```

- Live (run small online benchmark against local server):

```bash
python scripts/benchmarks/compare_models.py --mode live --models qwen,Llama-3.1-8B-Instruct-Hybrid --server http://localhost:8000 --samples 10 --out-dir reports
```

Output: an HTML report `reports/compare_<models>.html` with a comparison table, latency histogram and tokens/sec charts.

Optional W&B upload:

- Add `--wandb` to upload metrics and images to Weights & Biases and store the HTML report in the run directory. You can specify `--project` to change the W&B project name (defaults to `lemonade-ryzenai-evals-demo`).

Reference:

- W&B Model Track docs: https://docs.wandb.ai/models/track
