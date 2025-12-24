# AMD AI Max+ 395 ROCm Test Execution Guide

This guide provides comprehensive instructions for running the AMD AI Max+ 395 ROCm testing framework and interpreting the results.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Test Categories](#test-categories)
4. [Running Tests](#running-tests)
5. [Result Interpretation](#result-interpretation)
6. [Performance Benchmarks](#performance-benchmarks)
7. [Troubleshooting](#troubleshooting)
8. [Advanced Usage](#advanced-usage)

## Prerequisites

### Hardware Requirements
- AMD AI Max+ 395 GPU with 128GB VRAM
- Windows 11 Pro or Enterprise
- Minimum 16GB system RAM
- SSD storage with at least 100GB free space

### Software Requirements
- Python 3.10-3.13
- AMD ROCm 7.1.1+ drivers
- Lemonade Server v9.1.1+ with ROCm backend support
- Git for version control

### Environment Setup

1. **Install Python Dependencies:**
   ```bash
   cd tests/rocm_max395
   pip install -r requirements.txt
   ```

2. **Verify ROCm Installation:**
   ```bash
   rocminfo
   # Should show AMD GPU information
   ```

3. **Start Lemonade Server:**
   ```bash
   lemonade --llamacpp rocm --model llama-3.2-1b-instruct-gguf
   # Server should start on http://localhost:8000
   ```

## Quick Start

### Run All Tests
```bash
cd tests/rocm_max395
pytest
```

### Run Specific Test Categories
```bash
# Basic inference tests
pytest -m "not (performance or rag or multi_model)"

# Performance benchmarks only
pytest -m performance

# Multi-model tests
pytest -m multi_model

# RAG integration tests
pytest -m rag
```

### Generate Test Report
```bash
pytest --html=report.html --self-contained-html
```

## Test Categories

### 1. Basic Inference Tests (`test_basic_inference.py`)
**Purpose**: Validate fundamental LLM inference capabilities on AMD AI Max+ 395

**Test Methods:**
- `test_model_loading_rocm()`: Verifies model loading with ROCm backend
- `test_api_inference_basic()`: Tests OpenAI-compatible API responses
- `test_large_model_vram()`: Validates 30B+ model loading and VRAM utilization
- `test_prompt_variation()`: Ensures diverse prompt handling

**Expected Runtime**: 5-15 minutes
**Success Criteria**: All tests pass with coherent model outputs

### 2. Performance Benchmarking (`test_performance.py`)
**Purpose**: Measure inference performance and scaling characteristics

**Test Methods:**
- `test_perplexity_benchmark()`: Measures tokens/second and latency
- `test_model_size_scaling()`: Compares 7B, 13B, 30B+ model performance
- `test_backend_comparison()`: Validates ROCm vs CPU performance advantage
- `test_stability_extended()`: Tests sustained performance over time

**Expected Runtime**: 30-60 minutes
**Success Criteria**: Performance metrics meet or exceed targets

### 3. RAG Integration Tests (`test_rag_integration.py`)
**Purpose**: Validate retrieval-augmented generation capabilities

**Test Methods:**
- `test_context_incorporation()`: Tests context-aware response generation
- `test_document_qa_pipeline()`: Validates document-based Q&A
- `test_variable_context_windows()`: Tests different context sizes (1K-16K tokens)
- `test_rag_streaming()`: Validates streaming responses with context

**Expected Runtime**: 15-30 minutes
**Success Criteria**: Accurate responses with proper context utilization

### 4. Multi-Model Tests (`test_multi_model.py`)
**Purpose**: Validate concurrent model loading and management

**Test Methods:**
- `test_concurrent_model_loading()`: Tests loading 2-3 models simultaneously
- `test_model_routing()`: Validates request routing to correct models
- `test_specialized_model_types()`: Tests generation vs instruction-tuned models
- `test_vram_exhaustion_handling()`: Tests graceful VRAM limit handling

**Expected Runtime**: 20-45 minutes
**Success Criteria**: Successful concurrent loading without interference

## Running Tests

### Command Line Options

```bash
# Run with verbose output
pytest -v

# Run specific test file
pytest test_basic_inference.py

# Run specific test method
pytest test_performance.py::TestPerformance::test_perplexity_benchmark

# Run with custom markers
pytest -m "rocm and not slow"

# Generate HTML report
pytest --html=results/report.html

# Run with coverage
pytest --cov=tests.rocm_max395 --cov-report=html

# Parallel execution (if available)
pytest -n auto
```

### Environment Variables

```bash
# Override server URL
export LEMONADE_SERVER_URL="http://localhost:8000/api/v1"

# Set test timeout
export TEST_TIMEOUT=600

# Enable debug logging
export DEBUG=1

# Set results directory
export RESULTS_DIR="/path/to/custom/results"
```

### Continuous Integration

For CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Run ROCm Tests
  run: |
    cd tests/rocm_max395
    pytest --tb=short --junitxml=results/junit.xml
```

## Result Interpretation

### Test Status Indicators

- **PASSED** (✓): Test completed successfully
- **FAILED** (✗): Test failed with assertion error
- **ERROR** (⚠): Test failed with unexpected exception
- **SKIPPED**: Test skipped due to missing dependencies or conditions

### Performance Metrics

#### Key Performance Indicators (KPIs)

| Metric | Target | Description |
|--------|--------|-------------|
| Tokens/sec | >50 | Inference throughput |
| Latency (ms) | <500 | Time to first token |
| VRAM Usage | <100GB | Memory utilization |
| Model Load Time | <300s | Time to load large models |

#### Interpreting Benchmark Results

**Tokens per Second:**
- 50+ tokens/sec: Excellent performance
- 20-50 tokens/sec: Good performance
- <20 tokens/sec: Performance needs investigation

**Latency Percentiles:**
- P50 < 200ms: Excellent responsiveness
- P95 < 1000ms: Good responsiveness
- P99 < 2000ms: Acceptable for most use cases

**VRAM Utilization:**
- <80GB for large models: Efficient memory usage
- 80-100GB: Acceptable for maximum performance
- >100GB: Potential memory issues

### Result Files

Test results are stored in `tests/rocm_max395/results/`:

```
results/
├── benchmark_20241223_143000.json    # Detailed benchmark data
├── test_summary_20241223_143000.md   # Human-readable summary
├── performance_metrics.json          # Aggregated performance data
└── error_logs/                        # Error details and stack traces
```

## Performance Benchmarks

### Baseline Performance Targets

Based on AMD AI Max+ 395 specifications:

#### Llama-3.2-1B Model
- **Expected Tokens/sec**: 80-120
- **Expected Latency**: 100-200ms
- **VRAM Usage**: 2-4GB

#### Llama-3.2-7B Model
- **Expected Tokens/sec**: 40-70
- **Expected Latency**: 200-400ms
- **VRAM Usage**: 8-12GB

#### Llama-3.2-13B Model
- **Expected Tokens/sec**: 25-45
- **Expected Latency**: 300-600ms
- **VRAM Usage**: 15-20GB

#### Llama-3.2-30B Model
- **Expected Tokens/sec**: 10-25
- **Expected Latency**: 500-1000ms
- **VRAM Usage**: 35-45GB

### Comparative Analysis

The framework automatically compares results against:
- Historical performance data
- Expected performance targets
- Cross-model scaling patterns
- ROCm vs CPU performance ratios

## Troubleshooting

### Common Issues

#### 1. ROCm Driver Issues
**Symptoms**: Tests fail with GPU-related errors
**Solutions**:
- Verify ROCm installation: `rocminfo`
- Check driver version: `rocm-smi`
- Restart ROCm services
- Reinstall drivers if necessary

#### 2. Model Loading Failures
**Symptoms**: "Model not found" or "Loading failed" errors
**Solutions**:
- Verify model file paths
- Check file permissions
- Ensure sufficient disk space
- Validate model file integrity

#### 3. VRAM Exhaustion
**Symptoms**: "Out of memory" or "VRAM exhausted" errors
**Solutions**:
- Reduce concurrent model count
- Use smaller model variants
- Close other GPU applications
- Check system memory usage

#### 4. Network/Connection Issues
**Symptoms**: Connection refused or timeout errors
**Solutions**:
- Verify Lemonade Server is running
- Check server URL configuration
- Test API connectivity manually
- Review firewall settings

### Debug Mode

Enable detailed logging for troubleshooting:

```bash
export DEBUG=1
pytest -v -s --tb=long
```

### Log Files

Check these locations for diagnostic information:
- `tests/rocm_max395/results/error_logs/`
- Lemonade Server logs
- System event logs
- ROCm debug logs: `/var/log/rocm/`

## Advanced Usage

### Custom Test Configuration

Create custom test configurations:

```python
# custom_config.json
{
  "models": {
    "custom_model": {
      "name": "custom-llama-3.2-7b-gguf",
      "size": "7B",
      "quantization": "Q4_K_M",
      "context_length": 4096
    }
  },
  "test_scenarios": [
    {
      "name": "custom_benchmark",
      "model": "custom_model",
      "prompts": ["Custom test prompt..."],
      "iterations": 10
    }
  ]
}
```

### Performance Profiling

Enable detailed performance profiling:

```bash
pytest --profile --profile-svg
# Generates performance profiles in prof/
```

### Custom Result Analysis

Use the ReportGenerator for custom analysis:

```python
from utils.report_generator import ReportGenerator

generator = ReportGenerator()
results = generator.load_results("results/benchmark_*.json")
analysis = generator.generate_analysis(results)
generator.save_report(analysis, "custom_report.md")
```

### Integration Testing

For continuous integration:

```bash
# Run smoke tests (fast validation)
pytest -m "not (slow or performance)"

# Run full regression suite
pytest --durations=10

# Generate compliance report
pytest --junitxml=compliance.xml --tb=no
```

## Support and Resources

### Documentation
- [AMD ROCm Documentation](https://docs.amd.com/)
- [Lemonade Server Documentation](https://lemonade.example.com/docs)
- [PyTorch ROCm Guide](https://pytorch.org/docs/stable/notes/rocm.html)

### Community Resources
- AMD ROCm Forums
- Lemonade Discord/Community
- GitHub Issues for bug reports

### Getting Help
1. Check this guide first
2. Review troubleshooting.md for specific issues
3. Check GitHub issues for similar problems
4. Create detailed bug reports with:
   - Full error logs
   - System information
   - Test configuration
   - Steps to reproduce

---

*Last updated: December 23, 2025*
*Test Framework Version: 1.0.0*