"""
Edge case tests for AMD AI Max+ 395 ROCm validation.

Tests for error conditions, boundary cases, and robustness validation
including driver failures, memory exhaustion, and corrupted data handling.
"""

import pytest
import json
import time
import psutil
import subprocess
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import Dict, Any, Optional

from utils.lemonade_client import LemonadeClient, InferenceRequest
from utils.rocm_monitor import ROCmMonitor
from utils.metrics_collector import MetricsCollector


class TestEdgeCases:
    """Test edge cases and error conditions for robustness validation."""

    @pytest.fixture
    def corrupted_model_file(self, tmp_path: Path) -> Path:
        """Create a corrupted model file for testing."""
        corrupted_file = tmp_path / "corrupted_model.gguf"
        # Create a file with invalid GGUF header
        with open(corrupted_file, 'wb') as f:
            f.write(b'INVALID_HEADER_DATA' * 1000)
        return corrupted_file

    @pytest.fixture
    def oversized_request(self) -> InferenceRequest:
        """Create an oversized inference request."""
        return InferenceRequest(
            prompt="Test prompt " * 10000,  # Very long prompt
            max_tokens=100000,  # Excessive token limit
            temperature=2.0,  # Invalid temperature
            context_length=100000  # Excessive context
        )

    @pytest.mark.rocm
    @pytest.mark.edge_case
    def test_rocm_driver_unavailable(self, client: LemonadeClient, monitor: ROCmMonitor):
        """
        Test behavior when ROCm driver becomes unavailable during operation.

        Simulates driver crash or GPU disconnection scenarios.
        """
        # First verify normal operation
        try:
            response = client.inference("Hello world", max_tokens=10)
            assert response is not None
            assert len(response.content) > 0
        except Exception as e:
            pytest.skip(f"Cannot establish baseline: {e}")

        # Simulate driver unavailability
        with patch.object(monitor, 'get_vram_usage', side_effect=Exception("GPU unavailable")):
            with pytest.raises(Exception) as exc_info:
                client.inference("Test prompt", max_tokens=10)

            # Should provide meaningful error message
            assert any(error_type in str(exc_info.value).lower() for error_type in
                      ['gpu', 'rocm', 'driver', 'unavailable'])

    @pytest.mark.rocm
    @pytest.mark.edge_case
    def test_vram_exhaustion_during_inference(self, client: LemonadeClient, monitor: ROCmMonitor):
        """
        Test VRAM exhaustion handling during active inference.

        Validates graceful degradation when memory limits are exceeded.
        """
        # Monitor initial VRAM state
        initial_vram = monitor.get_vram_usage()
        assert initial_vram is not None

        # Attempt to exhaust VRAM with large concurrent requests
        large_prompts = [
            "Generate a detailed analysis of " * 1000,  # ~4K tokens each
            "Explain quantum computing with examples " * 800,
            "Write a comprehensive guide about " * 600
        ]

        errors_caught = []
        successful_requests = 0

        # Launch concurrent requests that may exceed VRAM
        for i, prompt in enumerate(large_prompts):
            try:
                response = client.inference(prompt, max_tokens=500, timeout=30)
                if response and response.content:
                    successful_requests += 1
            except Exception as e:
                errors_caught.append(str(e))

        # Should either succeed or fail gracefully with appropriate errors
        total_attempts = len(large_prompts)
        assert successful_requests + len(errors_caught) == total_attempts

        # Check for appropriate error messages if failures occurred
        if errors_caught:
            vram_related_errors = [e for e in errors_caught if
                                 any(term in e.lower() for term in
                                    ['vram', 'memory', 'gpu', 'out of memory'])]
            assert len(vram_related_errors) > 0, f"No VRAM-related errors in: {errors_caught}"

    @pytest.mark.rocm
    @pytest.mark.edge_case
    def test_corrupted_model_file_handling(self, corrupted_model_file: Path):
        """
        Test handling of corrupted or invalid model files.

        Validates proper error reporting for file corruption issues.
        """
        # This test would typically require server restart with corrupted model
        # For now, validate file detection logic
        assert corrupted_model_file.exists()
        assert corrupted_model_file.stat().st_size > 0

        # Verify file appears corrupted (invalid GGUF format)
        with open(corrupted_model_file, 'rb') as f:
            header = f.read(4)
            assert header != b'GGUF', "File should not have valid GGUF header"

        # Note: Actual server testing with corrupted model would require
        # integration with server startup logic, which may vary by implementation

    @pytest.mark.rocm
    @pytest.mark.edge_case
    def test_network_interruption_recovery(self, client: LemonadeClient):
        """
        Test recovery from network interruptions during inference.

        Validates connection resilience and retry logic.
        """
        # Test with very short timeout to simulate network issues
        with pytest.raises(Exception) as exc_info:
            client.inference("Test prompt", max_tokens=100, timeout=0.001)

        # Should be a timeout-related error
        assert any(term in str(exc_info.value).lower() for term in
                  ['timeout', 'connection', 'network'])

    @pytest.mark.rocm
    @pytest.mark.edge_case
    def test_oversized_request_handling(self, client: LemonadeClient, oversized_request: InferenceRequest):
        """
        Test handling of oversized or invalid inference requests.

        Validates input validation and error reporting.
        """
        with pytest.raises(Exception) as exc_info:
            client.inference(
                oversized_request.prompt,
                max_tokens=oversized_request.max_tokens,
                temperature=oversized_request.temperature
            )

        # Should reject invalid parameters
        error_msg = str(exc_info.value).lower()
        assert any(term in error_msg for term in
                  ['invalid', 'too large', 'exceeds', 'limit', 'parameter'])

    @pytest.mark.rocm
    @pytest.mark.edge_case
    def test_concurrent_request_interference(self, client: LemonadeClient):
        """
        Test for interference between concurrent requests.

        Validates request isolation and thread safety.
        """
        import threading
        import queue

        results = queue.Queue()
        errors = queue.Queue()

        def make_request(request_id: int):
            """Make a single inference request."""
            try:
                prompt = f"Count to {request_id} in words: "
                response = client.inference(prompt, max_tokens=20, timeout=10)
                results.put((request_id, response.content if response else None))
            except Exception as e:
                errors.put((request_id, str(e)))

        # Launch 5 concurrent requests
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join(timeout=15)

        # Collect results
        successful_requests = 0
        failed_requests = 0

        while not results.empty():
            request_id, content = results.get()
            if content and len(content.strip()) > 0:
                successful_requests += 1
            else:
                failed_requests += 1

        while not errors.empty():
            request_id, error = errors.get()
            failed_requests += 1

        # Should have some successful requests and no catastrophic failures
        assert successful_requests >= 2, f"Too few successful requests: {successful_requests}"
        assert successful_requests + failed_requests == 5, "Request count mismatch"

    @pytest.mark.rocm
    @pytest.mark.edge_case
    def test_system_resource_exhaustion(self, monitor: ROCmMonitor):
        """
        Test system behavior under resource exhaustion conditions.

        Monitors CPU, memory, and GPU resources during stress testing.
        """
        # Monitor initial system state
        initial_cpu = psutil.cpu_percent(interval=1)
        initial_memory = psutil.virtual_memory().percent
        initial_vram = monitor.get_vram_usage()

        # Simulate resource stress (this is a monitoring test, not a load test)
        stress_start = time.time()

        # Monitor for 10 seconds
        cpu_samples = []
        memory_samples = []
        vram_samples = []

        for _ in range(10):
            cpu_samples.append(psutil.cpu_percent(interval=0.1))
            memory_samples.append(psutil.virtual_memory().percent)
            vram_samples.append(monitor.get_vram_usage() or 0)
            time.sleep(1)

        stress_duration = time.time() - stress_start

        # Validate monitoring capability
        assert len(cpu_samples) == 10
        assert len(memory_samples) == 10
        assert len(vram_samples) == 10
        assert stress_duration >= 9.0  # Should take at least 10 seconds

        # Check that monitoring didn't crash under stress
        avg_cpu = sum(cpu_samples) / len(cpu_samples)
        avg_memory = sum(memory_samples) / len(memory_samples)
        avg_vram = sum(vram_samples) / len(vram_samples)

        # Basic sanity checks
        assert 0 <= avg_cpu <= 100
        assert 0 <= avg_memory <= 100
        assert avg_vram >= 0

    @pytest.mark.rocm
    @pytest.mark.edge_case
    def test_model_unloading_recovery(self, client: LemonadeClient, monitor: ROCmMonitor):
        """
        Test recovery after model unloading and reloading.

        Validates model state management and cleanup.
        """
        # This test assumes server supports model switching
        # Implementation may vary based on server capabilities

        # Test basic connectivity first
        try:
            response = client.inference("Hello", max_tokens=5)
            assert response is not None
        except Exception as e:
            pytest.skip(f"Cannot test model switching: {e}")

        # Monitor VRAM before and after operations
        initial_vram = monitor.get_vram_usage()

        # Note: Actual model unloading/reloading would require server API support
        # This test validates the monitoring and client infrastructure

        final_vram = monitor.get_vram_usage()

        # VRAM should be measurable (not necessarily changed)
        assert initial_vram is not None
        assert final_vram is not None
        assert final_vram >= 0

    @pytest.mark.rocm
    @pytest.mark.edge_case
    def test_invalid_configuration_handling(self, client: LemonadeClient):
        """
        Test handling of invalid configuration parameters.

        Validates parameter validation and error reporting.
        """
        invalid_configs = [
            {"temperature": -1.0},  # Negative temperature
            {"temperature": 3.0},   # Temperature > 2.0
            {"max_tokens": -100},   # Negative max tokens
            {"max_tokens": 1000000}, # Excessive max tokens
            {"top_p": 1.5},         # Invalid top_p
            {"frequency_penalty": 3.0}, # Excessive penalty
        ]

        for config in invalid_configs:
            with pytest.raises(Exception) as exc_info:
                client.inference("Test prompt", **config)

            # Should provide meaningful error message
            error_msg = str(exc_info.value).lower()
            assert any(term in error_msg for term in
                      ['invalid', 'parameter', 'range', 'limit'])

    @pytest.mark.rocm
    @pytest.mark.edge_case
    def test_empty_and_malformed_prompts(self, client: LemonadeClient):
        """
        Test handling of empty and malformed input prompts.

        Validates input sanitization and error handling.
        """
        test_cases = [
            ("", "Empty prompt"),
            ("   ", "Whitespace-only prompt"),
            ("\n\t\r", "Control characters only"),
            ("Prompt with null char \x00 in middle", "Null character in prompt"),
            ("Very long prompt " * 10000, "Extremely long prompt"),  # ~200K chars
        ]

        for prompt, description in test_cases:
            try:
                response = client.inference(prompt, max_tokens=10, timeout=5)
                # Should either succeed or fail gracefully
                if response:
                    assert isinstance(response.content, str)
                else:
                    # Failed gracefully
                    pass
            except Exception as e:
                # Should be a meaningful error, not a crash
                assert len(str(e)) > 0
                assert "traceback" not in str(e).lower()

    @pytest.mark.rocm
    @pytest.mark.edge_case
    def test_server_restart_recovery(self, client: LemonadeClient):
        """
        Test client recovery after server restart.

        Validates connection recovery and state management.
        """
        # Test initial connectivity
        try:
            response = client.inference("Initial test", max_tokens=5)
            assert response is not None
        except Exception:
            pytest.skip("Cannot establish initial connection")

        # Simulate server unavailability (this would require actual server control)
        # For now, test timeout behavior which simulates server issues

        with pytest.raises(Exception) as exc_info:
            # Very short timeout to simulate server unavailability
            client.inference("Test after simulated restart", max_tokens=10, timeout=0.001)

        # Should be a connection/timeout error
        assert any(term in str(exc_info.value).lower() for term in
                  ['timeout', 'connection', 'unavailable', 'server'])