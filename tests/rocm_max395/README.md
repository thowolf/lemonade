# AMD AI Max+ 395 ROCm Testing Framework

**Feature**: Comprehensive LLM Validation Suite (001-max-395-rocm-test)
**Purpose**: Complete validation of AMD AI Max+ 395 hardware capabilities for LLM inference, RAG, and multi-model workloads
**Version**: 1.0.0
**Last Updated**: December 23, 2025

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [Test Categories](#test-categories)
5. [Configuration](#configuration)
6. [Usage Examples](#usage-examples)
7. [Results & Reporting](#results--reporting)
8. [Troubleshooting](#troubleshooting)
9. [Contributing](#contributing)

## Overview

This testing framework provides comprehensive validation of AMD AI Max+ 395 GPU capabilities for large language model workloads. It validates:

- ✅ **Basic Inference**: Model loading, API compatibility, diverse prompt handling
- ✅ **Performance Benchmarking**: Throughput, latency, scaling, and stability metrics
- ✅ **RAG Integration**: Context incorporation, document Q&A, variable context windows
- ✅ **Multi-Model Support**: Concurrent loading, routing, VRAM management, error handling

### Key Features

- **Hardware-Specific**: Optimized for AMD AI Max+ 395 (128GB VRAM, gfx1151)
- **Production-Ready**: Comprehensive error handling and edge case coverage
- **Automated Reporting**: JSON results with human-readable summaries
- **CI/CD Integration**: JUnit XML output and parallel test execution
- **Extensible**: Modular design for adding new test scenarios

### Supported Models

| Model | Size | Quantization | Context | VRAM Usage |
|-------|------|--------------|---------|------------|
| Llama-3.2-1B-Instruct | 1B | Q4_K_M | 8K | ~2.5GB |
| Llama-3.2-3B-Instruct | 3B | Q4_K_M | 8K | ~5GB |
| Llama-3.2-7B-Instruct | 7B | Q4_K_M | 8K | ~8GB |
| Llama-3.2-13B-Instruct | 13B | Q4_K_M | 8K | ~15GB |
| Llama-3.2-30B-Instruct | 30B | Q4_K_M | 8K | ~35GB |

## Architecture

### Test Structure

```
tests/rocm_max395/
├── conftest.py                 # Pytest configuration & fixtures
├── test_basic_inference.py     # US1: Basic inference validation
├── test_performance.py         # US2: Performance benchmarking
├── test_rag_integration.py     # US3: RAG pipeline testing
├── test_multi_model.py         # US4: Multi-model concurrency
├── fixtures/                   # Test data & configurations
│   ├── models_config.json      # Model specifications
│   ├── prompts.json           # Test prompts (50+ diverse topics)
│   ├── rag_scenarios.json     # RAG test scenarios
│   └── multi_model_configs.json # Multi-model test configurations
├── utils/                     # Shared utilities
│   ├── lemonade_client.py     # OpenAI SDK wrapper
│   ├── metrics_collector.py   # Performance metrics
│   ├── rocm_monitor.py        # GPU monitoring
│   └── report_generator.py    # Result formatting
└── results/                   # Test outputs
    ├── benchmark_*.json       # Performance data
    ├── test_summary_*.md      # Human-readable reports
    └── error_logs/            # Debug information
```

### Dependencies

- **pytest>=7.0.0**: Test framework with custom markers
- **openai>=1.0.0**: API client for Lemonade Server
- **psutil>=5.9.0**: System resource monitoring
- **tabulate>=0.9.0**: Result table formatting
- **requests>=2.31.0**: HTTP client utilities

## Quick Start

### 1. Environment Setup

```bash
# Clone repository
git clone <repository-url>
cd lemonade/tests/rocm_max395

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Important Paths

**Lemonade Server Executables:**
```
C:\Users\tomwo\AppData\Local\lemonade_server\bin\
```

**Model Storage Locations:**
- **Huggingface Models**: `C:\Users\tomwo\.cache\huggingface\hub`
- **FLM Models**: `C:\Users\tomwo\Documents\flm\models`

**Running Commands:**
```powershell
# Router
"C:\Users\tomwo\AppData\Local\lemonade_server\bin\lemonade-router.exe" --port 8000 --host 0.0.0.0 --ctx-size 4096 --llamacpp vulkan --log-level debug --max-loaded-models 1 1 1 1

# Server
"C:\Users\tomwo\AppData\Local\lemonade_server\bin\lemonade-server.exe" serve
```

### 3. Verify Prerequisites

```bash
# Check ROCm installation
rocminfo | grep "AMD Radeon"

# Start Lemonade Server
lemonade --llamacpp rocm --model llama-3.2-1b-instruct-gguf

# Verify server connectivity
curl http://localhost:8000/api/v1/models
```

### 3. Run Basic Tests

```bash
# Run all tests
pytest -v

# Run specific category
pytest -m basic -v

# Generate HTML report
pytest --html=results/report.html --self-contained-html
```

## Test Categories

### 1. Basic Inference Tests (`test_basic_inference.py`)

**Priority**: P1 (MVP) - **User Story 1**
**Runtime**: 5-15 minutes
**Purpose**: Validate fundamental LLM capabilities on AMD AI Max+ 395

#### Test Methods
- `test_model_loading_rocm()`: ROCm backend model loading
- `test_api_inference_basic()`: OpenAI API compatibility
- `test_large_model_vram()`: 30B+ model VRAM utilization
- `test_prompt_variation()`: Diverse prompt handling

#### Success Criteria
- All models load successfully with ROCm backend
- API returns properly formatted responses
- Large models utilize VRAM efficiently (<100GB)
- Different prompts produce varied, coherent outputs

### 2. Performance Benchmarking (`test_performance.py`)

**Priority**: P2 - **User Story 2**
**Runtime**: 30-60 minutes
**Purpose**: Measure and validate inference performance metrics

#### Test Methods
- `test_perplexity_benchmark()`: Throughput and latency measurement
- `test_model_size_scaling()`: Performance scaling across model sizes
- `test_backend_comparison()`: ROCm vs CPU performance validation
- `test_stability_extended()`: Sustained performance over time

#### Key Metrics
- **Tokens/second**: >50 for optimal performance
- **Latency percentiles**: P95 <1000ms, P99 <2000ms
- **VRAM efficiency**: <80GB for large models
- **Stability**: <5% performance variation over 4+ hours

### 3. RAG Integration Tests (`test_rag_integration.py`)

**Priority**: P3 - **User Story 3**
**Runtime**: 15-30 minutes
**Purpose**: Validate retrieval-augmented generation capabilities

#### Test Methods
- `test_context_incorporation()`: Context-aware response generation
- `test_document_qa_pipeline()`: Document-based question answering
- `test_variable_context_windows()`: 1K-16K token context handling
- `test_rag_streaming()`: Streaming responses with context

#### Success Criteria
- Accurate responses using provided context
- Proper context window management
- Streaming compatibility with RAG
- Document chunking and retrieval accuracy

### 4. Multi-Model Tests (`test_multi_model.py`)

**Priority**: P4 - **User Story 4**
**Runtime**: 20-45 minutes
**Purpose**: Validate concurrent model loading and management

#### Test Methods
- `test_concurrent_model_loading()`: 2-3 simultaneous model loading
- `test_model_routing()`: Request routing without interference
- `test_specialized_model_types()`: Generation vs instruction-tuned models
- `test_vram_exhaustion_handling()`: Graceful VRAM limit handling

#### Success Criteria
- Successful concurrent loading without conflicts
- Accurate request routing to correct models
- Proper model type differentiation
- Graceful error handling for resource limits

## Configuration

### Environment Variables

```bash
# Server Configuration
export LEMONADE_SERVER_URL="http://localhost:8000/api/v1"
export TEST_TIMEOUT=300
export MODEL_LOAD_TIMEOUT=600

# Test Parameters
export DEFAULT_TEMPERATURE=0.7
export DEFAULT_MAX_TOKENS=512
export RESULTS_DIR="./results"

# Debug Settings
export DEBUG=1
export LOG_LEVEL=INFO
```

### Configuration Files

#### `fixtures/models_config.json`
```json
{
  "small": {
    "name": "Llama-3.2-1B-Instruct-GGUF",
    "size": "1B",
    "quantization": "Q4_K_M",
    "context_length": 8192,
    "expected_vram_gb": 2.5
  }
}
```

#### `fixtures/multi_model_configs.json`
```json
{
  "model_sets": {
    "concurrent_test": ["llama-3.2-1b-instruct-gguf", "llama-3.2-7b-instruct-gguf"]
  },
  "performance_targets": {
    "max_concurrent_models": 3,
    "max_total_vram_gb": 100,
    "min_routing_accuracy": 0.8
  }
}
```

## Usage Examples

### Basic Test Execution

```bash
# Run all tests with verbose output
pytest -v

# Run specific test category
pytest -m "performance" -v

# Run single test method
pytest test_basic_inference.py::TestBasicInference::test_model_loading_rocm -v

# Run with coverage report
pytest --cov=. --cov-report=html
```

### Custom Test Scenarios

```bash
# Test specific model
pytest -k "llama_3_2_7b" -v

# Run tests in parallel (if pytest-xdist installed)
pytest -n 4

# Generate JUnit XML for CI/CD
pytest --junitxml=results/junit.xml

# Run with custom configuration
TEST_TIMEOUT=600 pytest test_performance.py
```

### Performance Profiling

```bash
# Profile test execution
pytest --profile --profile-svg

# Monitor system resources during tests
pytest -s --log-cli-level=INFO

# Generate detailed performance report
python -c "
from utils.report_generator import ReportGenerator
gen = ReportGenerator()
results = gen.load_results('results/benchmark_*.json')
report = gen.generate_comprehensive_report(results)
print(report)
"
```

### CI/CD Integration

```yaml
# .github/workflows/rocm-tests.yml
name: ROCm Max395 Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: self-hosted  # Windows 11 with AMD AI Max+ 395
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd tests/rocm_max395
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd tests/rocm_max395
          pytest --junitxml=results/junit.xml --html=results/report.html
      - name: Upload results
        uses: actions/upload-artifact@v4
        with:
          name: test-results
          path: tests/rocm_max395/results/
```

## Results & Reporting

### Result Structure

```
results/
├── benchmark_20241223_143000.json    # Raw performance data
├── test_summary_20241223_143000.md   # Human-readable summary
├── performance_metrics.json          # Aggregated metrics
├── error_logs/                        # Debug information
│   ├── test_failures.log
│   └── system_errors.log
└── report.html                        # HTML test report
```

### Performance Metrics

#### Key Performance Indicators

| Metric | Excellent | Good | Needs Attention |
|--------|-----------|------|-----------------|
| Tokens/sec | >80 | 40-80 | <40 |
| Latency P95 | <500ms | 500-1000ms | >1000ms |
| VRAM Usage | <80GB | 80-100GB | >100GB |
| Load Time | <180s | 180-300s | >300s |

#### Benchmark Result Interpretation

```json
{
  "test_name": "perplexity_benchmark",
  "model_name": "Llama-3.2-7B-Instruct-GGUF",
  "metrics": {
    "tokens_per_second": {
      "mean": 65.4,
      "std_dev": 2.1,
      "min": 62.1,
      "max": 68.9
    },
    "latency_ms": {
      "p50": 245,
      "p95": 456,
      "p99": 723
    }
  },
  "environment": {
    "gpu": "AMD Radeon RX 9100",
    "vram_total": 128,
    "driver_version": "ROCm 7.1.1"
  }
}
```

### Automated Reporting

```python
from utils.report_generator import ReportGenerator

# Generate comprehensive report
generator = ReportGenerator()
results = generator.load_results("results/benchmark_*.json")
report = generator.generate_comprehensive_report(results)

# Save reports
generator.save_report(report, "results/final_report.md")
generator.save_json_report(report, "results/final_report.json")
```

## Troubleshooting

### Common Issues

#### ROCm Driver Problems
```bash
# Verify ROCm installation
rocminfo

# Check GPU status
rocm-smi --showproductname --showvramusage

# Restart ROCm services
sudo systemctl restart rocm
```

#### Model Loading Failures
```bash
# Check model file permissions
ls -la /path/to/model.gguf

# Verify model path in server config
lemonade --model /full/path/to/model.gguf --llamacpp rocm
```

#### Memory Issues
```bash
# Monitor VRAM usage
watch -n 1 rocm-smi --showvramusage

# Check system memory
free -h

# Clear GPU memory
sudo fuser -k /dev/kfd
```

#### Connectivity Problems
```bash
# Test server connectivity
curl http://localhost:8000/api/v1/models

# Check server logs
tail -f /var/log/lemonade/server.log
```

### Debug Mode

```bash
# Enable detailed logging
export DEBUG=1
export LOG_LEVEL=DEBUG

# Run tests with debug output
pytest -v -s --tb=long --log-cli-level=DEBUG
```

### Getting Help

- 📖 **[Test Execution Guide](test_execution_guide.md)**: Detailed usage instructions
- 🔧 **[Troubleshooting Guide](troubleshooting.md)**: Solutions for common issues
- 🐛 **[GitHub Issues](https://github.com/your-org/lemonade/issues)**: Bug reports and feature requests
- 💬 **Community Support**: Lemonade Discord/Forum

## Contributing

### Adding New Tests

1. **Create test file** in `tests/rocm_max395/`
2. **Add fixtures** to `fixtures/` if needed
3. **Update configuration** in `conftest.py`
4. **Add documentation** to this README

### Test Development Guidelines

```python
import pytest
from utils.lemonade_client import LemonadeClient

class TestNewFeature:
    """Test class for new feature validation."""

    @pytest.mark.rocm
    def test_feature_functionality(self, client: LemonadeClient):
        """Test specific functionality."""
        # Test implementation
        result = client.some_new_method()
        assert result.is_valid()
```

### Code Quality

- Follow PEP 8 style guidelines
- Add comprehensive docstrings
- Include type hints
- Write descriptive test names
- Add error handling for edge cases

### Performance Testing

- Use appropriate timeouts for long-running tests
- Include resource cleanup in teardown
- Monitor system resources during test execution
- Provide baseline performance expectations

---

## Prerequisites

### Hardware Requirements
- AMD AI Max+ 395 GPU (128GB VRAM, gfx1151)
- Windows 11 Pro/Enterprise (22H2+)
- 16GB+ system RAM
- 200GB+ SSD storage

### Software Requirements
- Python 3.10-3.13
- AMD ROCm drivers 7.1.1+ for Windows
- Lemonade Server 9.1.1+ with ROCm backend
- Git for version control

### Installation Verification

```bash
# Verify Python version
python --version  # Should be 3.10-3.13

# Verify ROCm installation
rocminfo | grep "AMD Radeon RX 9100"

# Verify Lemonade Server
curl -s http://localhost:8000/api/v1/models | jq .data[0].id
```

---

*AMD AI Max+ 395 ROCm Testing Framework v1.0.0*
*Comprehensive LLM validation for enterprise AI workloads*
*Built for Lemonade Server with ROCm backend*