# MoE Validation Test Suite

Test suite for validating Mixture-of-Experts (MoE) models, specifically `qwen3-next-80b-q4_k_m.gguf`.

## Prerequisites

### Model Artifact
The test suite requires the `qwen3-next-80b-q4_k_m.gguf` model file to be available locally.

**Required Model:**
- Name: `qwen3-next-80b-q4_k_m.gguf`
- Format: GGUF (GPT-Generated Unified Format)
- Size: ~80B parameters, quantized to 4-bit (q4_k_m)

**Acquisition:**
1. Download the model from your model repository
2. Place it in an accessible location
3. Update the `MODEL_PATH` variable in the notebook or test scripts

**Verification:**
```bash
# Check model file exists and is readable
ls -lh /path/to/qwen3-next-80b-q4_k_m.gguf

# Optional: Verify checksum (if provided)
sha256sum /path/to/qwen3-next-80b-q4_k_m.gguf
```

### Dependencies
Install required Python packages:

```bash
# Core dependencies (should already be installed with Lemonade)
pip install lemonade-sdk[dev,oga-ryzenai] --extra-index-url=https://pypi.amd.com/simple

# GGUF loading support (llama.cpp Python bindings)
pip install llama-cpp-python

# LM Evaluation Harness for accuracy tests
pip install lm-eval

# Additional dependencies for stats and reporting
pip install pandas
```

### Hardware Requirements
- **CPU**: Any modern x86_64 processor
- **iGPU**: AMD integrated GPU (driver-dependent)
- **RAM**: Minimum 16GB recommended for quick-demo, 32GB+ for full runs
- **Storage**: ~50GB free space for model + cache

## Directory Structure

```
tests/moe_validation/
├── README.md              # This file
├── stats_schema.sql       # Database schema for test results
├── test_data/             # Sample datasets for MMLU/GSM8k
│   ├── mmlu/
│   └── gsm8k/
├── test_moe_benchmark.py  # Benchmark tests
├── test_moe_accuracy.py   # MMLU/GSM8k tests
└── test_moe_judgement.py  # LLM judge tests
```

## Running Tests

### Quick Demo (5-10 minutes)
```python
# In the notebook, set:
CONFIG = "quick-demo"  # limit=5, warmup=0, iterations=5
```

### Full Validation (1-2 hours)
```python
# In the notebook, set:
CONFIG = "full"  # limit=100, warmup=10, iterations=20
```

### Devices
```python
DEVICE = "cpu"   # For CPU-only testing
DEVICE = "igpu"  # For AMD iGPU (driver-dependent)
```

## Expected Outputs

### Performance Metrics
- **TTFT** (Time to First Token): < 5 seconds
- **TPS** (Tokens Per Second): > 10 tokens/sec
- **Memory**: < 16GB for quick-demo

### Accuracy Metrics
- **MMLU**: Aggregate accuracy scores per subject
- **GSM8k**: Math problem solving accuracy

### Judgement
- **LLM Judge**: 1-5 rating with explanation

### Results Files
- CSV report: `{cache_dir}/moe_validation_results.csv`
- Stats database: `{cache_dir}/stats.json` or `.sqlite`
- Benchmark logs: `{cache_dir}/builds/{build_id}/`

## Troubleshooting

### Model Loading Errors
**Error**: `FileNotFoundError: Model file not found`
- **Solution**: Update `MODEL_PATH` in the notebook to point to your actual model file

**Error**: `GGUF file corrupted or incompatible`
- **Solution**: Re-download the model and verify checksum

### Memory Issues
**Error**: `Out of memory (OOM)`
- **Solution**:
  - Reduce batch size or sequence length
  - Use `CONFIG = "quick-demo"` for lower memory usage
  - Close other applications
  - Switch to `DEVICE = "cpu"` if GPU memory is limited

### Dependency Errors
**Error**: `ModuleNotFoundError: No module named 'llama_cpp'`
- **Solution**: `pip install llama-cpp-python`

**Error**: `lm_eval command not found`
- **Solution**: `pip install lm-eval`

## CI/Automation

The standalone smoke test script can be run for quick validation:

```bash
python scripts/ci/smoke_test_moe.py \
    --model /path/to/qwen3-next-80b-q4_k_m.gguf \
    --device cpu
```

Expected exit codes:
- `0`: Success
- `1`: Model loading failed
- `2`: Smoke test failed (response generation error)

## References

- [Lemonade Documentation](https://lemonade-server.ai/)
- [LM Evaluation Harness](https://github.com/EleutherAI/lm-evaluation-harness)
- [GGUF Format Specification](https://github.com/ggerganov/llama.cpp/blob/master/gguf-py/README.md)
- [Feature Specification](../../specs/002-moe-qwen3-tests/spec.md)

## Support

For issues or questions:
1. Check this README and feature spec
2. Review notebook cell outputs for error messages
3. Consult Lemonade SDK documentation
4. Open an issue in the project repository
