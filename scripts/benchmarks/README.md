# Benchmarks directory

This directory contains benchmarking scripts and helper assets used in the project.

Note: The repository `scripts/benchmarks/RyzenAI-SW` is a third-party clone of AMD's `RyzenAI-SW` project and is intentionally kept as an external, untracked vendor copy.

- Do **not** modify or commit changes inside `scripts/benchmarks/RyzenAI-SW/` here.
- If you need to propose changes for `RyzenAI-SW`, create a fork of the official upstream repository and submit a PR to `amd/RyzenAI-SW`.

The top-level `.gitignore` is configured to ignore the `RyzenAI-SW` folder to prevent accidental commits here.

## Benchmarks usage

We provide a small benchmark runner and an analyzer in this folder.

- Run a single benchmark:

```powershell
# Run a short benchmark for a model (use conda ryzen env)
conda run -n ryzen-ai-1.6.1 python scripts/benchmarks/ryzen_benchmark_with_metrics.py --url http://127.0.0.1:8000/api/v1/chat/completions --model "Phi-3-Mini-Instruct-Hybrid" --concurrency 1 --requests 5 --prompt "Test run" --max-tokens 32
```

- Run a sweep (multiple models/concurrency):

```powershell
conda run -n ryzen-ai-1.6.1 python scripts/benchmarks/ryzen_benchmark_with_metrics.py --sweep --models "Phi-3-Mini-Instruct-Hybrid,Qwen3-4B-Instruct-2507-GGUF,Llama-3.2-3B-Instruct-Hybrid" --concurrency-list "1,4" --requests-list "20"
```

- Analyze results and produce a markdown summary:

```powershell
python scripts/benchmarks/analyze_benchmark_results.py
```

Results and sweep JSONs are saved to `tests/results/` and W&B runs are recorded in `wandb/` (offline by default).