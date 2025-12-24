# Quickstart: AMD AI Max+ 395 ROCm Testing

**Goal**: Run your first LLM inference test on AMD AI Max+ 395 with ROCm backend in under 30 minutes

**Prerequisites**: Windows 11, AMD AI Max+ 395 hardware, administrator access

## Step 1: Install AMD ROCm Drivers (10 minutes)

### Download and Install HIP SDK

1. **Download** AMD HIP SDK for Windows:
   - Visit: https://rocm.docs.amd.com/projects/install-on-windows/en/latest/
   - Download latest HIP SDK installer (7.1.1 or newer)
   - Size: ~2-3 GB

2. **Install** with administrator privileges:
   ```powershell
   # Run installer as Administrator
   # Accept license, choose default installation path
   # Installation path typically: C:\Program Files\AMD\ROCm\
   ```

3. **Verify** installation:
   ```powershell
   # Open PowerShell as Administrator
   rocminfo
   # Should display: AMD AI Max+ 395, gfx1151 architecture, 128 GB VRAM
   
   hipinfo
   # Should show HIP version and device information
   ```

**Troubleshooting**:
- If `rocminfo` not found: Add `C:\Program Files\AMD\ROCm\bin` to PATH
- If GPU not detected: Update AMD graphics drivers from AMD.com
- If architecture mismatch: Set environment variable `HSA_OVERRIDE_GFX_VERSION=11.5.1`

## Step 2: Install Lemonade Server (5 minutes)

### Option A: Windows MSI Installer (Recommended)

1. **Download** Lemonade Server installer:
   ```powershell
   # Visit: https://github.com/lemonade-sdk/lemonade/releases/latest
   # Download: lemonade-server-minimal.msi
   ```

2. **Install**:
   - Run MSI installer
   - Accept defaults
   - Installation adds Lemonade to PATH automatically

3. **Verify**:
   ```powershell
   lemonade-server --version
   # Should show: 9.1.1 or newer
   ```

### Option B: From Source (Advanced)

```powershell
git clone https://github.com/lemonade-sdk/lemonade.git
cd lemonade
python -m pip install -e .
```

## Step 3: Install Python Dependencies (3 minutes)

### Create Testing Environment

```powershell
# Navigate to repository root
cd C:\path\to\lemonade

# Create virtual environment (optional but recommended)
python -m venv venv-rocm-test
.\venv-rocm-test\Scripts\Activate.ps1

# Install test dependencies
cd tests\rocm_max395
pip install -r requirements.txt
# Installs: pytest, openai, psutil, tabulate
```

**Verify Python version**:
```powershell
python --version
# Should be: Python 3.10.x, 3.11.x, 3.12.x, or 3.13.x
```

## Step 4: Download Test Model (5 minutes)

### Pull Llama 3.2 1B Model

```powershell
# Use Lemonade Model Manager to download small test model
lemonade-server pull Llama-3.2-1B-Instruct-GGUF

# Wait for download to complete (~700 MB)
# Model saved to: %USERPROFILE%\.lemonade\models\
```

**Verify model download**:
```powershell
lemonade-server list
# Should show: Llama-3.2-1B-Instruct-GGUF [downloaded]
```

## Step 5: Run Your First Test (5 minutes)

### Start Lemonade Server with ROCm Backend

```powershell
# Terminal 1: Start Lemonade Server
lemonade-server run Llama-3.2-1B-Instruct-GGUF --llamacpp rocm

# Expected output:
# [INFO] Loading model: Llama-3.2-1B-Instruct-GGUF
# [INFO] Using backend: ROCm (gfx1151)
# [INFO] Model loaded (VRAM: 2.3 GB)
# [INFO] Server running at http://localhost:8000
```

### Execute Basic Inference Test

```powershell
# Terminal 2: Run pytest (keep server running in Terminal 1)
cd tests\rocm_max395
pytest test_basic_inference.py::test_single_prompt_generation -v

# Expected output:
# test_basic_inference.py::test_single_prompt_generation PASSED [100%]
# ===== 1 passed in 5.32s =====
```

### View Test Results

```powershell
# Results saved to: tests/rocm_max395/results/tests/
# Open JSON result file:
notepad results\tests\P1-basic-1b-001.json

# Key metrics to check:
# - "status": "passed"
# - "tokens_per_second": > 40 (1B models are fast)
# - "vram_usage_gb": ~2-3 GB
```

## Step 6: Verify Success

### Check Test Output

Your test passed if:
- ✅ Server started with ROCm backend (check Terminal 1 logs)
- ✅ pytest reports "PASSED" status
- ✅ Result JSON shows `"status": "passed"`
- ✅ Response text is coherent (not gibberish)
- ✅ VRAM usage reported (check `vram_usage_gb`)

### Example Successful Output

```json
{
  "test_id": "P1-basic-1b-001",
  "status": "passed",
  "performance_metrics": {
    "tokens_per_second": {"mean": 42.5},
    "time_to_first_token_ms": {"p50": 800},
    "vram_usage_gb": {"peak": 2.3}
  },
  "validation_results": {
    "overall_pass": true,
    "pass_count": 2,
    "fail_count": 0
  }
}
```

## Next Steps

### Run Additional Tests

```powershell
# P1: Full basic inference test suite
pytest test_basic_inference.py -v

# P2: Performance benchmarking
pytest test_performance.py::test_benchmark_7b_model -v

# All tests (takes 30+ minutes)
pytest tests/rocm_max395/ -v
```

### Download Larger Models

```powershell
# 7B model for performance testing
lemonade-server pull Llama-3.2-7B-Instruct-GGUF

# 13B model
lemonade-server pull Llama-2-13B-Chat-GGUF

# Large 30B+ models (requires sufficient disk space)
lemonade-server pull Llama-2-34B-Code-Instruct-GGUF
```

### Compare Backends

```powershell
# Test same model with Vulkan backend
lemonade-server run Llama-3.2-7B-Instruct-GGUF --llamacpp vulkan

# Run benchmark comparison test
pytest test_performance.py::test_backend_comparison -v
```

### Customize Test Configuration

Edit `fixtures/models_config.json`:
```json
{
  "custom_test": {
    "model_name": "Your-Model-Name-GGUF",
    "model_size": "7B",
    "quantization": "Q4_K_M",
    "expected_tokens_per_second": 25.0
  }
}
```

Then run:
```powershell
pytest test_basic_inference.py --model custom_test -v
```

## Troubleshooting

### Server Won't Start

**Problem**: "Failed to load model"
- **Solution**: Check ROCm drivers installed (`rocminfo`)
- **Solution**: Verify model downloaded (`lemonade-server list`)
- **Solution**: Try Vulkan backend first: `--llamacpp vulkan`

**Problem**: "Backend not supported"
- **Solution**: Reinstall Lemonade Server (ensure ROCm build included)
- **Solution**: Check HIP SDK installed and in PATH

### Test Fails

**Problem**: pytest reports "FAILED"
- **Solution**: Check server running in Terminal 1
- **Solution**: Verify API accessible: `curl http://localhost:8000/api/v1/models`
- **Solution**: Review error logs in `results/tests/*.json`

**Problem**: Low tokens/second (<5 for 7B model)
- **Solution**: Confirm ROCm backend active (check server logs for "Using backend: ROCm")
- **Solution**: Check GPU utilization: Task Manager > Performance > GPU
- **Solution**: Close background applications using GPU

### VRAM Issues

**Problem**: "Insufficient VRAM"
- **Solution**: Close other GPU applications
- **Solution**: Try smaller quantization (Q4_K_M instead of Q8_0)
- **Solution**: Use smaller model (1B or 3B for initial testing)

**Problem**: VRAM not detected
- **Solution**: Run `rocm-smi` to check GPU status
- **Solution**: Restart system if GPU not visible
- **Solution**: Update AMD graphics drivers

## Getting Help

### Documentation

- **Lemonade Docs**: https://lemonade-server.ai/docs/
- **ROCm Docs**: https://rocm.docs.amd.com/en/latest/
- **Test Spec**: [specs/001-max-395-rocm-test/spec.md](spec.md)
- **Research**: [specs/001-max-395-rocm-test/research.md](research.md)

### Support Channels

- **GitHub Issues**: https://github.com/lemonade-sdk/lemonade/issues
- **Discord**: https://discord.gg/5xXzkMu8Zk
- **Email**: lemonade@amd.com

### Useful Commands

```powershell
# Check ROCm status
rocminfo
rocm-smi

# Check Lemonade installation
lemonade-server --version
lemonade-server list

# Check Python environment
python --version
pip list | findstr "openai pytest"

# View server logs (if running as service)
Get-Content $env:TEMP\lemonade-server.log -Tail 50

# Kill stuck server process
taskkill /IM lemonade-server.exe /F
```

## Success Criteria

After completing this quickstart, you should have:
- ✅ ROCm 7.1.1+ drivers installed and verified
- ✅ Lemonade Server 9.1.1+ installed
- ✅ Python 3.10-3.13 environment with test dependencies
- ✅ At least one GGUF model downloaded (Llama 3.2 1B)
- ✅ Successfully run and passed first inference test
- ✅ Generated test result JSON with performance metrics
- ✅ Verified ROCm backend actively used (check VRAM usage)

**Total Time**: ~30 minutes for complete setup and first test

**Next**: Move to P2 performance benchmarking or P3 RAG testing
