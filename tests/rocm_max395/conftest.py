"""
Pytest configuration and shared fixtures for ROCm Max395 testing.

This module provides:
- Pytest configuration for test discovery and execution
- Shared fixtures for model loading, API client setup, and test data
- Environment validation and setup
"""

import pytest
import json
import os
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

# Test configuration
TEST_CONFIG = {
    "lemonade_server_url": "http://localhost:8000/api/v1",
    "test_timeout": 300,  # 5 minutes
    "model_load_timeout": 600,  # 10 minutes for large models
    "default_temperature": 0.7,
    "default_max_tokens": 512,
    "results_dir": Path(__file__).parent / "results"
}

@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration to all tests."""
    return TEST_CONFIG.copy()

@pytest.fixture(scope="session")
def lemonade_server_url():
    """Lemonade Server API base URL."""
    return TEST_CONFIG["lemonade_server_url"]

@pytest.fixture(scope="session")
def results_dir():
    """Directory for storing test results."""
    results_dir = TEST_CONFIG["results_dir"]
    results_dir.mkdir(exist_ok=True)
    return results_dir

@pytest.fixture(scope="session")
def model_configs():
    """Load model configurations from fixtures."""
    config_file = Path(__file__).parent / "fixtures" / "models_config.json"
    if config_file.exists():
        with open(config_file, 'r') as f:
            return json.load(f)
    else:
        # Default configurations
        return {
            "small": {
                "name": "Llama-3.2-1B-Instruct-GGUF",
                "size": "1B",
                "quantization": "Q4_K_M",
                "context_length": 8192,
                "expected_vram_gb": 2.5
            },
            "medium": {
                "name": "Llama-3.2-7B-Instruct-GGUF",
                "size": "7B",
                "quantization": "Q4_K_M",
                "context_length": 8192,
                "expected_vram_gb": 8.0
            },
            "large": {
                "name": "Llama-3.2-30B-Instruct-GGUF",
                "size": "30B",
                "quantization": "Q4_K_M",
                "context_length": 8192,
                "expected_vram_gb": 25.0
            }
        }

@pytest.fixture(scope="session")
def test_prompts():
    """Load test prompts from fixtures."""
    prompts_file = Path(__file__).parent / "fixtures" / "prompts.json"
    if prompts_file.exists():
        with open(prompts_file, 'r') as f:
            return json.load(f)
    else:
        # Default test prompts
        return {
            "simple": "What is the capital of France?",
            "reasoning": "Explain quantum computing in simple terms.",
            "creative": "Write a short poem about artificial intelligence.",
            "factual": "What are the main differences between Python 2 and Python 3?",
            "multilingual": "こんにちは、世界！ (Hello, world!) Translate this to English and explain the programming significance."
        }

@pytest.fixture(scope="function")
def temp_result_file(results_dir):
    """Create a temporary result file for each test."""
    def _temp_result_file(test_name: str) -> Path:
        return results_dir / f"{test_name}.json"
    return _temp_result_file

@pytest.fixture(scope="session")
def environment_info():
    """Collect environment information for test results."""
    import platform
    import psutil

    return {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "cpu_count": os.cpu_count(),
        "memory_gb": round(psutil.virtual_memory().total / (1024**3), 1),
        "hostname": platform.node(),
        "user": os.environ.get("USERNAME", "unknown")
    }

@pytest.fixture(scope="session")
def multi_model_configs():
    """Load multi-model test configurations from fixtures."""
    config_file = Path(__file__).parent / "fixtures" / "multi_model_configs.json"
    if config_file.exists():
        with open(config_file, 'r') as f:
            return json.load(f)
    else:
        # Default multi-model configurations
        return {
            "model_sets": {
                "small_models": ["llama-3.2-1b-instruct-gguf", "llama-3.2-3b-instruct-gguf"],
                "mixed_sizes": ["llama-3.2-1b-instruct-gguf", "llama-3.2-7b-instruct-gguf"],
                "large_models": ["llama-3.2-7b-instruct-gguf", "llama-3.2-13b-instruct-gguf"]
            },
            "test_scenarios": [
                {
                    "name": "concurrent_small",
                    "models": ["llama-3.2-1b-instruct-gguf", "llama-3.2-3b-instruct-gguf"],
                    "expected_total_vram_gb": 10.0,
                    "concurrent_requests": 4
                }
            ],
            "performance_targets": {
                "max_concurrent_models": 3,
                "max_total_vram_gb": 100,
                "min_routing_accuracy": 0.8
            }
        }

@pytest.fixture(scope="session", autouse=True)
def validate_environment():
    """Validate test environment before running tests."""
    # Check Python version
    import sys
    python_version = sys.version_info
    if not (3, 10) <= python_version < (3, 14):
        pytest.skip(f"Python {python_version.major}.{python_version.minor} not supported. Use Python 3.10-3.13")

    # Check if we're on Windows
    if os.name != 'nt':
        pytest.skip("These tests are designed for Windows 11 with AMD ROCm")

    # Check for ROCm installation (optional - tests can still run)
    try:
        result = subprocess.run(['rocminfo'], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            pytest.warns(UserWarning, "ROCm not detected. Tests may fail without proper ROCm installation.")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pytest.warns(UserWarning, "ROCm verification failed. Ensure ROCm is properly installed.")

    yield

# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "rocm: marks tests that require ROCm backend")
    config.addinivalue_line("markers", "performance: marks performance benchmarking tests")
    config.addinivalue_line("markers", "rag: marks RAG integration tests")
    config.addinivalue_line("markers", "multi_model: marks multi-model tests")
    config.addinivalue_line("markers", "routing: marks model routing tests")
    config.addinivalue_line("markers", "specialized: marks specialized model type tests")
    config.addinivalue_line("markers", "edge_case: marks edge case and error condition tests")
    config.addinivalue_line("markers", "scaling: marks model scaling performance tests")
    config.addinivalue_line("markers", "comparison: marks backend comparison tests")
    config.addinivalue_line("markers", "stability: marks stability and endurance tests")
    config.addinivalue_line("markers", "streaming: marks streaming response tests")
    config.addinivalue_line("markers", "slow: marks tests that take longer than 30 seconds")

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on file names."""
    for item in items:
        if "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        if "rag" in str(item.fspath):
            item.add_marker(pytest.mark.rag)
        if "multi_model" in str(item.fspath):
            item.add_marker(pytest.mark.multi_model)

        # Mark all tests as requiring ROCm by default
        item.add_marker(pytest.mark.rocm)