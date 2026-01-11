# Quickstart Guide: Continue Extension Model Testing

**Feature**: 004-continue-model-testing
**Date**: 2025-12-25

## Overview

This guide helps you quickly set up and run the Continue extension model testing framework to identify stable coder models for your AMD Ryzen AI hardware.

**Time to first test**: ~15 minutes
**Prerequisites**: VSCode, Continue extension, Anaconda AMD, Python 3.10-3.13

---

## Quick Start (5 Steps)

### 1. Install Dependencies

```bash
# Navigate to project root
cd C:\Users\tomwo\git\lemonade

# Install testing framework dependencies
pip install -e ".[continue_testing]"

# Verify xrt-smi is available (for NPU monitoring)
xrt-smi examine
```

> **Important:** `xrt-smi` is required for full NPU/GPU telemetry in the Continue testing framework. If `xrt-smi` is not found, install the AMD XRT / RyzenAI drivers (or follow your system vendor instructions). The framework will still run without `xrt-smi` but NPU metrics and some diagnostics will be unavailable.

**Expected output**: NPU device information or "command not found" (install AMD RyzenAI drivers if missing)

---

### 2. Configure Models to Test

Edit `scripts/benchmarks/continue-testing/config/models.yaml`:

```yaml
models:
  - name: "qwen2.5-coder-7b-q4"
    display_name: "Qwen 2.5 Coder 7B (Q4_0)"
    source: "ollama"
    quantization: "q4_0"
    expected_tokens_per_second: 25.0
    tolerance_percent: 20.0
    max_stable_interactions: 20

  - name: "deepseek-coder-v2-16b-q4"
    display_name: "DeepSeek Coder v2 16B (Q4_0)"
    source: "ollama"
    quantization: "q4_0"
    expected_tokens_per_second: 15.0
    tolerance_percent: 20.0
    max_stable_interactions: 20
```

**Note**: Ensure models are already downloaded in Ollama/LM Studio before testing.

---

### 3. Verify Continue Extension Setup

1. Open VSCode
2. Ensure Continue extension is installed and activated
3. Configure Continue to use local model (e.g., Ollama):
   - Open Continue settings (gear icon in Continue panel)
   - Set model to `ollama:qwen2.5-coder-7b-q4`
   - Test with a simple message: "Hello"

**Expected result**: Continue responds successfully

---

### 4. Run First Test

```bash
# Run interactive test for a single model
python scripts/benchmarks/continue-testing/test_runner.py \
    --model qwen2.5-coder-7b-q4 \
    --interactions 10 \
    --interactive

# Or run in background monitoring mode (manual testing)
python scripts/benchmarks/continue-testing/test_runner.py \
    --model qwen2.5-coder-7b-q4 \
    --monitor-only \
    --duration 600  # 10 minutes
```

**What happens**:
1. Test runner initializes system monitoring (CPU, RAM, NPU, GPU)
2. **Interactive mode**: CLI guides you through manual test interactions
3. **Monitor mode**: Runs in background while you use Continue normally
4. Metrics are collected every second
5. Results saved to `results/test_runs/{run_id}.json`

---

### 5. View Results

```bash
# Generate compatibility report
python scripts/benchmarks/continue-testing/report_generator.py \
    --output results/reports/compatibility_matrix.json

# View in terminal
cat results/reports/compatibility_matrix.json
```

**Sample output**:
```json
{
  "qwen2.5-coder-7b-q4": {
    "compatible": true,
    "max_stable_interactions": 20,
    "freeze_rate_percent": 0.0,
    "performance_rating": "good",
    "stability_rating": "stable",
    "recommended_for_production": true
  }
}
```

---

## Interactive Testing Workflow

When running with `--interactive`, the test runner guides you step-by-step:

### Example Session

```
╔══════════════════════════════════════════════════════════════╗
║   Continue Extension Model Testing - Interactive Mode        ║
╚══════════════════════════════════════════════════════════════╝

Model: Qwen 2.5 Coder 7B (Q4_0)
Planned interactions: 10
Background monitoring: ACTIVE (CPU, RAM, NPU, GPU)

═══════════════════════════════════════════════════════════════
Interaction 1/10: Code Explanation
═══════════════════════════════════════════════════════════════

[ACTION REQUIRED]
1. Open a code file in VSCode (e.g., a Python function)
2. Select 10-20 lines of code
3. Open Continue panel
4. Send this message:

   "Explain what this function does"

Press ENTER when you've sent the message...
```

**You do**:
1. Follow the instructions
2. Send the message in Continue
3. Press ENTER in terminal

**Test runner does**:
1. Records timestamp
2. Continues monitoring system metrics
3. Waits for you to confirm response

```
Did Continue respond successfully? (y/n): y
Response time (approximate seconds): 15

✓ Interaction 1 completed successfully
  Estimated tokens/second: ~18.5
  Continue process memory: 2048 MB
  NPU utilization: 75%

═══════════════════════════════════════════════════════════════
Interaction 2/10: Code Modification
═══════════════════════════════════════════════════════════════
...
```

### If Freeze Detected

```
Did Continue respond successfully? (y/n): n

[!] FREEZE DETECTED
    Collecting diagnostic data...
    ✓ System metrics captured
    ✓ Continue logs collected
    ✓ Process state recorded

    Freeze occurred after interaction 5/10

Test will terminate. View diagnostics at:
  results/freeze_events/freeze_{uuid}.json

Would you like to restart Continue and continue testing? (y/n):
```

---

## Monitor-Only Mode (Recommended for Real Usage)

For detecting freezes during normal development work:

```bash
# Start background monitoring
python scripts/benchmarks/continue-testing/test_runner.py \
    --model qwen2.5-coder-7b-q4 \
    --monitor-only \
    --duration 3600 \
    --wandb  # Optional: log to Weights & Biases

# Keep this terminal open
# Use Continue normally in VSCode
# Monitoring runs in background

# After 1 hour (or manual stop with Ctrl+C):
#   Results saved automatically
#   Freeze events logged if detected
```

**Advantages**:
- Tests real-world usage patterns
- No artificial test scenario constraints
- Captures actual developer workflow

---

## Configuration Files Reference

### models.yaml Structure

```yaml
models:
  - name: string                      # Unique identifier (required)
    display_name: string              # Human-readable name (required)
    source: enum                      # "ollama" | "lmstudio" | "huggingface" (required)
    quantization: string              # e.g., "q4_0", "bf16" (required)
    size_gb: float                    # Model size (optional)
    expected_tokens_per_second: float # Performance baseline (optional)
    tolerance_percent: float          # Acceptable variance (default: 20.0)
    max_stable_interactions: int      # Expected freeze-free count (default: 20)
```

### test_scenarios.yaml Structure

```yaml
scenarios:
  - name: string                      # Unique identifier (required)
    priority: enum                    # "P1" | "P2" | "P3" (required)
    description: string               # Human-readable description (required)
    interactions:                     # List of interactions (required)
      - prompt: string                # Prompt template (required)
        context_required: bool        # Code selection needed (required)
        expected_response_tokens_min: int    # Min tokens (optional)
        expected_response_tokens_max: int    # Max tokens (optional)
        timeout_seconds: int          # Timeout (default: 60)
```

### hardware.yaml Structure

```yaml
# Auto-detected on first run, can be overridden
hardware:
  cpu_model: string                   # e.g., "AMD Ryzen AI Max+ 395"
  ram_total_gb: float                 # e.g., 128.0
  npu_available: bool                 # Auto-detected
  gpu_model: string                   # Auto-detected
  monitoring:
    sample_interval_seconds: float    # Default: 1.0
    enable_npu: bool                  # Default: true
    enable_amd_gpu: bool              # Default: true
    enable_nvidia_gpu: bool           # Default: false
```

---

## Command Line Reference

### test_runner.py

```bash
python scripts/benchmarks/continue-testing/test_runner.py [OPTIONS]

Options:
  --model TEXT              Model name from models.yaml (required)
  --scenario TEXT           Test scenario from test_scenarios.yaml (optional)
  --interactions INTEGER    Number of interactions to run (default: 10)
  --interactive / --no-interactive
                            Interactive mode vs automated (default: interactive)
  --monitor-only            Only monitor, no guided interactions
  --duration INTEGER        Monitoring duration in seconds (default: 600)
  --output-dir PATH         Results output directory (default: results/)
  --wandb / --no-wandb      Log to Weights & Biases (default: no-wandb)
  --verbose                 Verbose logging
  --help                    Show this message and exit
```

### report_generator.py

```bash
python scripts/benchmarks/continue-testing/report_generator.py [OPTIONS]

Options:
  --input-dir PATH          Test runs directory (default: results/test_runs/)
  --output PATH             Output file (default: results/reports/compatibility_matrix.json)
  --format TEXT             Output format: "json" | "markdown" | "csv" (default: json)
  --min-runs INTEGER        Minimum runs to include model (default: 3)
  --help                    Show this message and exit
```

---

## Troubleshooting

### "xrt-smi: command not found"

**Solution**: Install AMD RyzenAI drivers
```bash
# Download from: https://ryzenai.docs.amd.com/en/latest/inst.html
# Or disable NPU monitoring:
export ENABLE_NPU_MONITORING=false
```

### "pyadl not found"

**Solution**: Install AMD GPU monitoring library
```bash
pip install pyadl
```

### "Continue process not found"

**Cause**: VSCode extension host process not detected
**Solution**: Test runner falls back to system-wide monitoring (works but less precise)

### Metrics show 0% NPU utilization

**Possible causes**:
1. Model not configured to use NPU
2. Continue using CPU/GPU backend instead
3. NPU driver issues

**Diagnosis**:
```bash
# Check NPU availability
xrt-smi examine

# Check Continue model configuration
# Ensure Continue is configured to use Ollama/LM Studio with NPU support
```

---

## Next Steps

### After First Successful Test

1. **Test more models**: Add models to `models.yaml` and repeat
2. **Run longer tests**: Increase `--interactions` to 20+ for stability testing
3. **Enable W&B logging**: Add `--wandb` flag for visualization
4. **Create test scenarios**: Define custom scenarios in `test_scenarios.yaml`

### Analyzing Results

```python
# Load and analyze test results
import json

with open('results/test_runs/{run_id}.json') as f:
    run = json.load(f)

print(f"Model: {run['model_name']}")
print(f"Interactions completed: {run['num_interactions_completed']}")
print(f"Freeze detected: {run['freeze_detected']}")
print(f"Metrics collected: {run['metrics_collected']} samples")

# Load performance metrics
with open(f"results/performance/{run['run_id']}_perf.json") as f:
    perf = json.load(f)

print(f"Mean response time: {perf['response_time_mean_ms']:.1f} ms")
print(f"Tokens/second: {perf['tokens_per_second_mean']:.1f}")
print(f"NPU utilization: {perf['npu_utilization_mean_percent']:.1f}%")
```

### Continuous Monitoring Setup

For ongoing stability monitoring:

```bash
# Create scheduled task (Windows Task Scheduler)
# Or cron job (Linux) to run daily:

python scripts/benchmarks/continue-testing/test_runner.py \
    --model qwen2.5-coder-7b-q4 \
    --monitor-only \
    --duration 3600 \
    --wandb \
    --output-dir results/continuous/$(date +%Y%m%d)
```

---

## Support

**Issues**: https://github.com/lemonade-sdk/lemonade/issues
**Documentation**: [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md)
**Questions**: Discord community or lemonade@amd.com
