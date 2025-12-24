# Quickstart: LLM Model Comparison with W&B Weave

**Feature**: `003-wandb-model-comparison`
**Version**: 1.0.0
**Last Updated**: 2025-12-24

---

## Overview

This guide walks you through running your first LLM model comparison evaluation using the Lemonade SDK with Weights & Biases (W&B) Weave integration. You'll evaluate multiple model configurations on AMD Ryzen AI hardware and visualize results in a centralized dashboard.

**Time to complete**: ~30 minutes (setup) + evaluation runtime

---

## Prerequisites

### System Requirements
- **Hardware**: AMD Ryzen AI Max+ 395 (or compatible Ryzen AI hardware)
- **OS**: Windows 11 or Ubuntu 24.04/25.04
- **RAM**: 32GB minimum (128GB recommended)
- **VRAM**: 96GB+ for large models

### Software Requirements
- **Lemonade SDK**: Version 9.0.0 or later
- **Python**: 3.10-3.13
- **ROCm**: 7.11.0 or later (for AMD GPU acceleration)

### Accounts
- **Weights & Biases**: Free account at [wandb.ai](https://wandb.ai)
- **HuggingFace**: Account for model downloads (optional for public models)

---

## Step 1: Install Dependencies

### Install W&B Weave SDK

```bash
pip install wandb weave lm-eval
```

### Verify Installation

```python
import weave
import wandb
import lm_eval

print(f"Weave version: {weave.__version__}")
print(f"W&B version: {wandb.__version__}")
print(f"lm-eval version: {lm_eval.__version__}")
```

Expected output:
```
Weave version: 0.51.0+
W&B version: 0.18.0+
lm-eval version: 0.4.0+
```

---

## Step 2: Configure W&B Authentication

### Login to W&B

```bash
wandb login
```

Enter your API key when prompted (find it at https://wandb.ai/authorize).

### Verify Authentication

```python
import wandb

# Test connection
wandb.init(project="test-project", mode="offline")
wandb.finish()
```

---

## Step 3: Create Your First Evaluation Configuration

Create a file `evaluation_config.yaml`:

```yaml
metadata:
  name: "my-first-evaluation"
  version: "1.0.0"
  created: "2025-12-24T10:00:00Z"
  description: "First model evaluation with W&B Weave"

model:
  identifier: "Qwen3-4B-GGUF"
  checkpoint: "unsloth/Qwen3-4B-GGUF:Q4_0"
  recipe: "llamacpp-rocm"
  quantization:
    method: "Q4_0"
    bits: 4
  size_gb: 2.38
  context_length: 32768

hardware:
  backend: "rocm"
  device: "igpu"
  platform: "AMD Ryzen AI Max+ 395"
  architecture: "gfx1151"
  vram_limit_gb: 96

benchmarks:
  performance:
    enabled: true
    iterations: 3
    prompts_per_iteration: 5
    metrics:
      - tokens_per_second
      - latency_ms
      - vram_usage_gb

  accuracy:
    enabled: true
    suites:
      - name: "mmlu_abstract_algebra"
        limit: 10  # Use 10 samples for quick test
        num_fewshot: 0

targets:
  tokens_per_second: 15
  time_to_first_token_ms: 1000

wandb:
  enabled: true
  project: "lemonade-quickstart"
  offline: false  # Set to true for offline mode
```

---

## Step 4: Run Your First Evaluation

### Option A: Using Python API (Recommended)

Create `run_evaluation.py`:

```python
#!/usr/bin/env python3
"""
Run LLM model evaluation with W&B Weave logging.
"""

import yaml
import weave
from lemonade.state import State
from lemonade.tools.accuracy import LMEvalHarness
from lemonade.evaluation.wandb_logger import WandbMetricsCollector

def load_config(config_path: str) -> dict:
    """Load evaluation configuration from YAML."""
    with open(config_path) as f:
        return yaml.safe_load(f)

def run_evaluation(config: dict):
    """Execute evaluation workflow."""

    # Initialize W&B Weave
    wandb_config = config.get("wandb", {})
    weave.init(wandb_config.get("project", "lemonade-ryzenai-evals"))

    # Create metrics collector with W&B logging
    collector = WandbMetricsCollector(
        project_name=wandb_config["project"],
        offline=wandb_config.get("offline", False)
    )

    # Initialize Lemonade state and load model
    state = State()
    # Load model according to config (implementation depends on Lemonade SDK)

    # Run performance benchmarks
    if config["benchmarks"]["performance"]["enabled"]:
        print("Running performance benchmarks...")
        perf_config = config["benchmarks"]["performance"]

        for i in range(perf_config["iterations"]):
            # Run benchmark iteration
            # (Implementation using Lemonade profilers)
            print(f"  Iteration {i+1}/{perf_config['iterations']}")

    # Run accuracy benchmarks
    if config["benchmarks"]["accuracy"]["enabled"]:
        print("Running accuracy benchmarks...")
        eval_tool = LMEvalHarness()

        for suite in config["benchmarks"]["accuracy"]["suites"]:
            print(f"  Running {suite['name']}...")
            state = eval_tool.run(
                state=state,
                task=suite["name"],
                limit=suite.get("limit"),
                num_fewshot=suite.get("num_fewshot", 0)
            )

    print(f"\\nEvaluation complete!")
    print(f"View results at: https://wandb.ai/{wandb_config['project']}")

if __name__ == "__main__":
    config = load_config("evaluation_config.yaml")
    run_evaluation(config)
```

Run the evaluation:

```bash
python run_evaluation.py
```

### Option B: Using CLI (Coming Soon)

```bash
lemonade evaluate \
  --config evaluation_config.yaml \
  --wandb-project lemonade-quickstart
```

---

## Step 5: View Results in W&B Dashboard

After the evaluation completes:

1. Open your browser to https://wandb.ai
2. Navigate to your project (`lemonade-quickstart`)
3. Click on the latest run
4. Explore metrics, charts, and logs

### Key Metrics to Review

**Performance Metrics**:
- `perf/tokens_per_second` - Throughput
- `perf/latency_ms` - Mean latency
- `perf/latency_p95_ms` - 95th percentile latency
- `resources/vram_usage_mb` - VRAM consumption

**Accuracy Metrics** (for accuracy benchmarks):
- `accuracy/acc` - Overall accuracy
- `accuracy/exact_match` - Exact match score

---

## Step 6: Compare Multiple Models

To compare different model configurations, create multiple evaluation configs and run them sequentially.

### Example: INT4 vs INT8 Comparison

**config_int4.yaml**:
```yaml
metadata:
  name: "llama-int4"
  version: "1.0.0"
  created: "2025-12-24T10:00:00Z"

model:
  identifier: "Llama-3.1-8B-INT4"
  checkpoint: "meta-llama/Llama-3.1-8B-Instruct:Q4_K_M"
  recipe: "oga-hybrid"
  quantization:
    method: "Q4_K_M"
    bits: 4
  # ... rest of config
```

**config_int8.yaml**:
```yaml
metadata:
  name: "llama-int8"
  version: "1.0.0"
  created: "2025-12-24T10:00:00Z"

model:
  identifier: "Llama-3.1-8B-INT8"
  checkpoint: "meta-llama/Llama-3.1-8B-Instruct:Q8_0"
  recipe: "oga-hybrid"
  quantization:
    method: "Q8_0"
    bits: 8
  # ... rest of config
```

Run both evaluations:

```bash
python run_evaluation.py config_int4.yaml
python run_evaluation.py config_int8.yaml
```

### Create Comparison Dashboard

In W&B web interface:
1. Go to your project
2. Click "Create Report"
3. Add "Run Comparer" panel
4. Select the two runs to compare
5. Choose metrics: `tokens_per_second`, `latency_ms`, `accuracy/acc`
6. Save the report

---

## Step 7: Offline Mode (Optional)

For hardware testing without internet connectivity:

### Enable Offline Mode

In your config file:
```yaml
wandb:
  enabled: true
  project: "lemonade-quickstart"
  offline: true  # Enable offline mode
```

Or via environment variable:
```bash
export WANDB_MODE=offline
python run_evaluation.py
```

### Sync Results Later

When back online:
```bash
wandb sync --sync-all ./wandb/
```

---

## Common Use Cases

### Use Case 1: Quick Performance Check

Minimal config for fast performance validation:

```yaml
benchmarks:
  performance:
    enabled: true
    iterations: 1
    prompts_per_iteration: 5
    metrics: [tokens_per_second, latency_ms]
  accuracy:
    enabled: false
```

Runtime: ~2-5 minutes

### Use Case 2: Comprehensive Accuracy Evaluation

Full accuracy benchmark on multiple suites:

```yaml
benchmarks:
  performance:
    enabled: false
  accuracy:
    enabled: true
    suites:
      - name: "mmlu"
        limit: null  # Full dataset
      - name: "hellaswag"
        limit: null
      - name: "gsm8k"
        limit: null
```

Runtime: ~4-8 hours (depending on model size)

### Use Case 3: Quantization Comparison

Compare 3-4 quantization levels for same model:

```bash
# Run sequentially with different configs
for quant in Q4_0 Q4_K_M Q8_0; do
  python run_evaluation.py config_${quant}.yaml
done
```

Create comparison report in W&B to visualize trade-offs.

---

## Troubleshooting

### Issue: "W&B login failed"

**Solution**: Ensure you have valid API key
```bash
wandb login --relogin
```

### Issue: "Out of VRAM"

**Solutions**:
- Reduce model size or use more aggressive quantization
- Set `vram_limit_gb` in hardware config
- Use CPU fallback: `device: "cpu"`

### Issue: "Evaluation runs very slowly"

**Solutions**:
- Check backend is using GPU/NPU: `backend: "hybrid"`
- Verify ROCm installation: `rocm-smi`
- Reduce `iterations` and `prompts_per_iteration` for testing

### Issue: "Offline sync fails"

**Solution**: Check wandb directory path
```bash
wandb sync --sync-all $(pwd)/wandb/
```

---

## Next Steps

### Learn More
- **Full Documentation**: See [plan.md](./plan.md) for implementation details
- **Data Model**: Review [data-model.md](./data-model.md) for entity definitions
- **W&B Schema**: Check [contracts/wandb-schema.yaml](./contracts/wandb-schema.yaml)

### Advanced Topics
- Custom benchmark definitions
- Multi-GPU evaluation
- Automated report generation
- Integration with CI/CD pipelines

### Example Notebooks
- `examples/evaluation/compare_quantizations.py` - Quantization comparison
- `examples/evaluation/compare_moe_configs.py` - MoE configuration tuning
- `examples/evaluation/notebooks/dashboard_analysis.ipynb` - Analysis workflow

---

## Support

- **GitHub Issues**: https://github.com/lemonade-sdk/lemonade/issues
- **Discord**: https://discord.gg/5xXzkMu8Zk
- **Email**: lemonade@amd.com

---

**Congratulations!** You've successfully run your first model comparison evaluation. Check the W&B dashboard to explore your results and start comparing model performance across different configurations.
