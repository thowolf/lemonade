# AMD AI Max+ 395 Quick Deployment Guide
## For Existing Lemonade Server Installation

**Date**: December 23, 2025
**Your Setup**: Lemonade Server at `C:\Users\tomwo\AppData\Local\lemonade_server\`
**Models Location**: `C:\Users\tomwo\.cache\huggingface\hub`

## Step 1: Transfer Deployment Files

The deployment package `amd_max395_deployment.zip` has been created in your workspace. Transfer this file to your Windows system and extract it to a directory (e.g., `C:\AMD_Max395_Deployment\`).

## Step 2: Verify Your Current Setup

You already have:
- ✅ Lemonade Server installed
- ✅ Models cached locally

## Step 3: Run Deployment Script

Since you have Lemonade Server installed, use these parameters:

```powershell
# Open PowerShell as Administrator
cd C:\AMD_Max395_Deployment

# Run deployment with existing Lemonade Server
.\deploy_amd_max395.ps1 -SkipLemonadeServer -Verbose
```

This will:
- ✅ Skip hardware check (optional)
- ✅ Install/Update ROCm drivers
- ✅ Setup Python environment
- ✅ **Skip Lemonade Server** (you already have it)
- ✅ Deploy testing framework
- ✅ Run validation

## Step 4: Configure Lemonade Server

Update your Lemonade Server configuration to use ROCm:

1. Open `C:\Users\tomwo\AppData\Local\lemonade_server\config.yaml`
2. Add ROCm configuration:

```yaml
rocm:
  enabled: true
  gpu_device: 0
  vram_budget: 120

models:
  - name: "llama-3.1-8b-instruct"
    path: "C:\Users\tomwo\.cache\huggingface\hub\models--meta-llama--Llama-3.1-8B-Instruct\gguf\llama-3.1-8b-instruct.gguf"
    type: "llama"
    context_length: 4096
    gpu_layers: 99
```

## Step 5: Run Validation

After deployment:

```powershell
# Run validation script
python deployment_validation.py --verbose

# Run test suite
cd tests\rocm_max395
python -m pytest --tb=short -v
```

## Benchmarking (optional)

For quick Ryzen hybrid throughput checks, a small benchmark script is included:

```powershell
# From repo root
python scripts/ryzen_benchmark.py --concurrency 4 --requests 5 --model Llama-3.2-3B-Instruct-Hybrid

# Or run the lightweight pytest-based smoke benchmark (skips if server not reachable)
python -m pytest tests/rocm_max395/test_benchmark_ryzen.py -q

# To capture system/process metrics alongside the benchmark, run:
python scripts/ryzen_benchmark_with_metrics.py --concurrency 4 --requests 5 --model Llama-3.2-3B-Instruct-Hybrid --interval 1.0
```

## Step 6: Start Monitoring

```powershell
# Start production monitoring
python production_monitor.py --daemon --interval 30
```

## Expected Results

- **28 tests** should pass
- **GPU utilization** should be visible in ROCm monitoring
- **Lemonade Server** should respond to API calls
- **Performance benchmarks** should show >50 tokens/sec

## Troubleshooting

If issues occur:
1. Check ROCm drivers: `rocm-smi`
2. Verify Python environment: `python --version`
3. Check Lemonade Server logs
4. Review deployment logs: `deployment_log_*.txt`

## Next Steps

1. Load models in Lemonade Server
2. Run performance benchmarks
3. Configure automated monitoring
4. Set up backup procedures

---

**Deployment Package**: `amd_max395_deployment.zip`
**Full Guide**: `docs/deployment/amd_max395_production_deployment.md`