# ROCm Max395 Testing Suite

**Feature**: AMD AI Max+ 395 ROCm Testing (001-max-395-rocm-test)
**Purpose**: Comprehensive validation of LLM inference and RAG capabilities on AMD AI Max+ 395 hardware

## Overview

This test suite validates Lemonade Server's ROCm backend performance on AMD AI Max+ 395 (128GB VRAM, gfx1151) running Windows 11. Tests cover basic inference, performance benchmarking, RAG integration, and multi-model scenarios.

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run basic inference tests**:
   ```bash
   pytest test_basic_inference.py -v
   ```

3. **Run all tests**:
   ```bash
   pytest -v
   ```

## Test Structure

- `test_basic_inference.py`: P1 - Basic LLM inference validation
- `test_performance.py`: P2 - Performance benchmarking
- `test_rag_integration.py`: P3 - RAG pipeline testing
- `test_multi_model.py`: P4 - Multi-model loading and concurrency

## Fixtures

- `fixtures/prompts.json`: Test prompts covering diverse topics
- `fixtures/models_config.json`: Model configurations and quantization levels

## Utils

- `utils/lemonade_client.py`: OpenAI SDK wrapper for Lemonade Server
- `utils/metrics_collector.py`: Performance metrics collection
- `utils/rocm_monitor.py`: VRAM and GPU utilization tracking
- `utils/report_generator.py`: Test result formatting and visualization

## Results

Test results are stored in `results/` directory as JSON files. See `results/README.md` for interpretation guidelines.

## Prerequisites

- Windows 11 (22H2+) with AMD AI Max+ 395 GPU
- AMD ROCm drivers 7.1.1+ for Windows
- Lemonade Server 9.1.1+ with ROCm backend
- Python 3.10-3.13
- 200GB+ disk space for model files

## Configuration

Tests use environment variables and configuration files. See `conftest.py` for pytest configuration and shared fixtures.