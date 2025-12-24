# AMD AI Max+ 395 ROCm Troubleshooting Guide

This guide provides solutions for common issues encountered when running the AMD AI Max+ 395 ROCm testing framework.

## Table of Contents

1. [Quick Diagnosis](#quick-diagnosis)
2. [ROCm Driver Issues](#rocm-driver-issues)
3. [Model Loading Problems](#model-loading-problems)
4. [VRAM and Memory Issues](#vram-and-memory-issues)
5. [Performance Problems](#performance-problems)
6. [Network and Connectivity](#network-and-connectivity)
7. [Test Framework Issues](#test-framework-issues)
8. [System Configuration](#system-configuration)
9. [Advanced Debugging](#advanced-debugging)
10. [Getting Help](#getting-help)

## Quick Diagnosis

### Run Diagnostic Script

```bash
cd tests/rocm_max395
python -c "
import sys
import subprocess
import psutil
import platform

print('=== AMD AI Max+ 395 ROCm Diagnostics ===')
print(f'Python Version: {platform.python_version()}')
print(f'Platform: {platform.platform()}')

# Check ROCm
try:
    result = subprocess.run(['rocminfo'], capture_output=True, text=True, timeout=10)
    if result.returncode == 0:
        print('✓ ROCm drivers detected')
    else:
        print('✗ ROCm drivers not found or not working')
except:
    print('✗ ROCm verification failed')

# Check Lemonade Server
try:
    import requests
    response = requests.get('http://localhost:8000/api/v1/models', timeout=5)
    if response.status_code == 200:
        print('✓ Lemonade Server responding')
    else:
        print('✗ Lemonade Server not responding correctly')
except:
    print('✗ Cannot connect to Lemonade Server')

# Check system resources
memory = psutil.virtual_memory()
print(f'System Memory: {memory.total // (1024**3)}GB total, {memory.available // (1024**3)}GB available')

print('\\n=== End Diagnostics ===')
"
```

### Common Quick Fixes

1. **Restart Services:**
   ```bash
   # Restart ROCm services
   sudo systemctl restart rocm

   # Restart Lemonade Server
   pkill -f lemonade
   lemonade --llamacpp rocm --model llama-3.2-1b-instruct-gguf
   ```

2. **Clear Cache:**
   ```bash
   # Clear Python cache
   find . -name "__pycache__" -type d -exec rm -rf {} +

   # Clear test results
   rm -rf tests/rocm_max395/results/*
   ```

3. **Update Dependencies:**
   ```bash
   cd tests/rocm_max395
   pip install -r requirements.txt --upgrade
   ```

## ROCm Driver Issues

### Symptoms
- "ROCm not detected" errors
- GPU memory allocation failures
- Tests fail with CUDA/ROCm related exceptions
- `rocminfo` command not found

### Solutions

#### 1. Verify ROCm Installation
```bash
# Check if ROCm is installed
which rocminfo
which rocm-smi

# List available GPUs
rocminfo | grep -A 10 "Agent"

# Check GPU status
rocm-smi --showid --showproductname --showvramsize --showvramvendor
```

#### 2. Reinstall ROCm Drivers
```bash
# Download latest ROCm installer
wget https://repo.radeon.com/amdgpu-install/6.1.1/ubuntu/jammy/amdgpu-install_6.1.60101-1_all.deb

# Install ROCm
sudo dpkg -i amdgpu-install_*.deb
sudo amdgpu-install --usecase=rocm

# Reboot system
sudo reboot
```

#### 3. Update GPU Firmware
```bash
# Update AMD GPU firmware
sudo apt update
sudo apt install amdgpu-firmware
```

#### 4. Check Kernel Compatibility
```bash
# Verify kernel version
uname -r

# Check if kernel supports ROCm
ls /sys/module/amdgpu

# Rebuild kernel modules if needed
sudo dkms autoinstall
```

### Common ROCm Error Messages

**"hipError_t: hipErrorNoBinaryForGpu"**
- GPU architecture not supported
- Update ROCm to latest version
- Check GPU compatibility

**"CL_OUT_OF_RESOURCES"**
- Insufficient VRAM
- Close other GPU applications
- Reduce model size or batch size

**"hipErrorOutOfMemory"**
- System out of GPU memory
- Reduce concurrent models
- Check for memory leaks

## Model Loading Problems

### Symptoms
- "Model file not found" errors
- "Failed to load model" messages
- Timeout during model loading
- Corrupted model file errors

### Solutions

#### 1. Verify Model Files
```bash
# Check model file exists and is readable
ls -la /path/to/model.gguf

# Verify file integrity (if checksum available)
sha256sum /path/to/model.gguf

# Check file permissions
chmod 644 /path/to/model.gguf
```

#### 2. Model Path Configuration
```bash
# Set correct model path in Lemonade
lemonade --model /full/path/to/llama-3.2-1b-instruct-gguf --llamacpp rocm

# Or use relative path from working directory
cd /path/to/models
lemonade --model llama-3.2-1b-instruct-gguf --llamacpp rocm
```

#### 3. Model Format Issues
```bash
# Convert model if needed (GGUF format required)
# Use llama.cpp or similar tools to convert models
llama.cpp/convert.py --input /path/to/model.bin --output /path/to/model.gguf
```

#### 4. Loading Timeout Issues
```bash
# Increase loading timeout
export MODEL_LOAD_TIMEOUT=1200  # 20 minutes

# Check system resources during loading
htop  # Monitor CPU/memory usage
nvtop  # Monitor GPU usage (if available)
```

### Model-Specific Issues

**Llama-3.2 Models:**
- Ensure GGUF format (not GGML)
- Check quantization level compatibility
- Verify model architecture support

**Large Models (30B+):**
- Ensure sufficient system RAM (>64GB recommended)
- Check swap space configuration
- Monitor disk I/O during loading

## VRAM and Memory Issues

### Symptoms
- "Out of memory" errors
- GPU memory allocation failures
- System becomes unresponsive
- Tests crash with memory-related exceptions

### Solutions

#### 1. Monitor VRAM Usage
```bash
# Real-time VRAM monitoring
watch -n 1 rocm-smi --showvramusage

# Check process GPU memory usage
rocm-smi --showpidgpus

# Monitor with radeontop
sudo radeontop
```

#### 2. Reduce Memory Usage
```bash
# Use smaller models
lemonade --model llama-3.2-1b-instruct-gguf --llamacpp rocm

# Reduce context length
export DEFAULT_CONTEXT_LENGTH=2048

# Use lower precision
export USE_FP16=false
```

#### 3. Clear GPU Memory
```bash
# Kill GPU processes
sudo fuser -k /dev/kfd
sudo fuser -k /dev/dri/*

# Reset GPU
sudo modprobe -r amdgpu
sudo modprobe amdgpu
```

#### 4. System Memory Management
```bash
# Check swap space
free -h
swapon -s

# Add swap if needed
sudo fallocate -l 32G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Memory Leak Detection
```bash
# Monitor memory usage over time
python -c "
import psutil
import time
process = psutil.Process()
for i in range(60):
    mem = process.memory_info()
    print(f'{i}s: {mem.rss / 1024 / 1024:.1f}MB RSS, {mem.vms / 1024 / 1024:.1f}MB VMS')
    time.sleep(1)
"
```

## Performance Problems

### Symptoms
- Slower than expected inference
- High latency or low throughput
- Performance degrades over time
- Inconsistent benchmark results

### Solutions

#### 1. Performance Baseline Check
```bash
# Run simple performance test
cd tests/rocm_max395
python -c "
import time
from utils.lemonade_client import LemonadeClient

client = LemonadeClient()
start = time.time()
response = client.inference('What is 2+2?', max_tokens=10)
end = time.time()
print(f'Inference time: {end-start:.3f}s')
print(f'Response: {response}')
"
```

#### 2. Optimize ROCm Settings
```bash
# Set optimal GPU clock
sudo rocm-smi --setfan 100  # Maximum fan speed
sudo rocm-smi --setperflevel high

# Check power profile
sudo rocm-smi --setpoweroverdrive 0  # Disable power limits
```

#### 3. CPU and System Optimization
```bash
# Disable CPU frequency scaling
sudo cpupower frequency-set -g performance

# Optimize kernel parameters
sudo sysctl -w vm.swappiness=10
sudo sysctl -w vm.dirty_ratio=80
sudo sysctl -w vm.dirty_background_ratio=5
```

#### 4. Benchmark Comparison
```bash
# Compare with CPU-only performance
lemonade --model llama-3.2-1b-instruct-gguf  # CPU mode

# Test different batch sizes
export BATCH_SIZE=1  # Start small
export BATCH_SIZE=4  # Test larger batches
```

### Performance Degradation Issues

**Gradual Performance Loss:**
- Check for memory leaks
- Monitor GPU temperature
- Verify power supply stability

**Inconsistent Results:**
- Ensure stable system load
- Check for background processes
- Verify network stability for remote models

## Network and Connectivity

### Symptoms
- Connection refused errors
- Timeout errors
- API call failures
- Intermittent connectivity issues

### Solutions

#### 1. Test Basic Connectivity
```bash
# Test server availability
curl -X GET http://localhost:8000/api/v1/models

# Test API health
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "llama-3.2-1b-instruct-gguf", "messages": [{"role": "user", "content": "Hello"}]}'
```

#### 2. Firewall Configuration
```bash
# Check firewall status
sudo ufw status

# Allow Lemonade port
sudo ufw allow 8000

# Or disable firewall temporarily for testing
sudo ufw disable
```

#### 3. Network Configuration
```bash
# Check network interfaces
ip addr show

# Test local connectivity
telnet localhost 8000

# Check DNS resolution
nslookup localhost
```

#### 4. Server Configuration Issues
```bash
# Check server logs
tail -f /var/log/lemonade/server.log

# Verify server configuration
ps aux | grep lemonade

# Restart server with debug logging
lemonade --debug --llamacpp rocm --model llama-3.2-1b-instruct-gguf
```

## Test Framework Issues

### Symptoms
- Import errors
- Test discovery failures
- Fixture errors
- Configuration problems

### Solutions

#### 1. Environment Setup
```bash
# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
pip install -r tests/rocm_max395/requirements.txt

# Verify Python path
python -c "import sys; print(sys.path)"
```

#### 2. Test Discovery Issues
```bash
# List all discoverable tests
pytest --collect-only -q

# Check specific test file
pytest tests/rocm_max395/test_basic_inference.py --collect-only

# Debug import issues
python -c "import tests.rocm_max395.test_basic_inference"
```

#### 3. Configuration Problems
```bash
# Validate configuration files
python -c "
import json
with open('tests/rocm_max395/fixtures/models_config.json') as f:
    config = json.load(f)
    print('Config loaded successfully')
    print(f'Models: {list(config.keys())}')
"
```

#### 4. Fixture Errors
```bash
# Test fixture loading
pytest --setup-show tests/rocm_max395/test_basic_inference.py::TestBasicInference::test_model_loading_rocm

# Debug fixture issues
pytest -v -s --tb=long tests/rocm_max395/test_basic_inference.py::TestBasicInference::test_model_loading_rocm
```

## System Configuration

### BIOS Settings
- Enable Above 4G Decoding
- Enable Resizable BAR
- Set PCIe ASPM to Disabled
- Enable SR-IOV if available

### Windows-Specific Issues
```powershell
# Check Windows version
winver

# Verify WSL2 installation
wsl --list --verbose

# Update WSL kernel
wsl --update
```

### Power Management
```bash
# Disable power management for GPU
sudo rocm-smi --setpowerprofile 1  # Maximum performance

# Check power supply
sudo rocm-smi --showpower

# Monitor temperatures
sudo rocm-smi --showtemp
```

## Advanced Debugging

### Enable Debug Logging
```bash
# Set debug environment variables
export DEBUG=1
export LOG_LEVEL=DEBUG
export PYTEST_DEBUG=1

# Run tests with verbose output
pytest -v -s --tb=long --log-cli-level=DEBUG
```

### Core Dump Analysis
```bash
# Enable core dumps
ulimit -c unlimited
echo '/tmp/core.%e.%p.%t' | sudo tee /proc/sys/kernel/core_pattern

# Analyze core dump
gdb /path/to/lemonade /tmp/core.lemonade.12345.1678901234
```

### Performance Profiling
```bash
# Profile test execution
pytest --profile --profile-svg

# Use py-spy for live profiling
py-spy top --pid $(pgrep -f pytest)

# Memory profiling
python -m memory_profiler tests/rocm_max395/test_performance.py
```

### GPU Debugging
```bash
# Enable ROCm debugging
export AMD_LOG_LEVEL=3
export AMD_GPU_DEBUG=1

# Check GPU kernel execution
rocprof --stats --timestamp on lemonade --llamacpp rocm --model llama-3.2-1b-instruct-gguf
```

## Getting Help

### Information to Include in Bug Reports

When reporting issues, please include:

1. **System Information:**
   ```bash
   uname -a
   rocminfo | head -20
   python --version
   pip list | grep -E "(pytest|openai|psutil)"
   ```

2. **Error Logs:**
   ```bash
   # Test framework logs
   cat tests/rocm_max395/results/error_logs/*.log

   # Lemonade server logs
   tail -100 /var/log/lemonade/server.log
   ```

3. **Test Configuration:**
   ```bash
   # Show test configuration
   cat tests/rocm_max395/fixtures/models_config.json
   cat tests/rocm_max395/fixtures/multi_model_configs.json
   ```

4. **Reproduction Steps:**
   - Exact command used
   - Test environment setup
   - Expected vs actual behavior

### Support Channels

1. **GitHub Issues:** For bug reports and feature requests
2. **AMD ROCm Forums:** For ROCm-specific issues
3. **Lemonade Community:** For server-specific problems
4. **Stack Overflow:** For general Python/testing questions

### Emergency Contacts

For critical production issues:
- AMD Enterprise Support
- Lemonade Enterprise Support
- System Administrator

---

*Last updated: December 23, 2025*
*Test Framework Version: 1.0.0*