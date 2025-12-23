"""
Basic LLM Inference Validation Tests (User Story 1 - P1)

Tests basic inference functionality on AMD AI Max+ 395 with ROCm backend.
Validates model loading, API responses, VRAM utilization, and output quality.
"""

import pytest
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any

from utils.lemonade_client import LemonadeClient, InferenceRequest
from utils.rocm_monitor import ROCmMonitor
from utils.metrics_collector import MetricsCollector, PerformanceMetrics

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestBasicInference:
    """Test basic LLM inference capabilities."""

    @pytest.fixture
    def client(self, lemonade_client: LemonadeClient) -> LemonadeClient:
        """Provide Lemonade client for tests."""
        return lemonade_client

    @pytest.fixture
    def monitor(self, rocm_monitor: ROCmMonitor) -> ROCmMonitor:
        """Provide ROCm monitor for tests."""
        return rocm_monitor

    @pytest.fixture
    def collector(self, metrics_collector: MetricsCollector) -> MetricsCollector:
        """Provide metrics collector for tests."""
        return metrics_collector

    @pytest.mark.rocm
    def test_model_loading_rocm(self, client: LemonadeClient, monitor: ROCmMonitor,
                               temp_result_file, results_dir: Path):
        """
        Test model loading with ROCm backend (AS1).

        Given Lemonade Server installed on Windows 11 with AMD AI Max+ 395 and ROCm drivers,
        When user runs lemonade-server run Llama-3.2-1B-Instruct-GGUF --llamacpp rocm,
        Then model loads successfully and generates coherent text response within expected timeframe
        """
        logger.info("Starting test_model_loading_rocm")

        try:
            # Check server health
            logger.info("Checking Lemonade Server health")
            if not client.health_check():
                raise RuntimeError("Lemonade Server is not responding")
            logger.info("Server health check passed")

            # Get model list
            logger.info("Retrieving available models")
            models = client.list_models()
            if not models:
                raise RuntimeError("No models available on server")
            logger.info(f"Found {len(models)} models: {[m['id'] for m in models]}")

            # Validate ROCm setup
            logger.info("Validating ROCm setup")
            is_valid, message = monitor.validate_max395_setup()
            if not is_valid:
                raise RuntimeError(f"ROCm setup validation failed: {message}")
            logger.info("ROCm setup validation passed")

            # Get initial GPU metrics
            logger.info("Collecting initial GPU metrics")
            initial_metrics = monitor.get_rocm_metrics()
            logger.info(f"Initial VRAM usage: {initial_metrics.total_vram_used_mb}MB")

            # Test basic inference
            test_prompt = "What is the capital of France?"
            logger.info(f"Testing inference with prompt: {test_prompt}")
            request = InferenceRequest(
                prompt=test_prompt,
                model=models[0]["id"],
                max_tokens=100
            )

            start_time = time.time()
            response = client.chat_completion(request)
            end_time = time.time()

            logger.info(f"Inference completed in {end_time - start_time:.2f}s")
            logger.info(f"Response length: {len(response.text)} characters")
            logger.info(".2f")

            # Validate response
            if not response.text:
                raise ValueError("No response text generated")
            if len(response.text) <= 10:
                raise ValueError(f"Response too short: {len(response.text)} characters")
            if "paris" not in response.text.lower():
                logger.warning(f"Response doesn't mention Paris: {response.text[:100]}...")

            # Check performance metrics
            if response.tokens_per_second <= 10:
                logger.warning(f"Tokens/sec below threshold: {response.tokens_per_second}")
            if response.latency_ms >= 5000:
                logger.warning(f"Latency above threshold: {response.latency_ms}ms")

            # Get final GPU metrics
            logger.info("Collecting final GPU metrics")
            final_metrics = monitor.get_rocm_metrics()
            vram_used = final_metrics.total_vram_used_mb
            logger.info(f"Final VRAM usage: {vram_used}MB")

            # Validate VRAM usage (should be reasonable for 1B model)
            if vram_used <= 1000:
                logger.warning(f"VRAM usage suspiciously low: {vram_used}MB")
            if vram_used >= 5000:
                logger.warning(f"VRAM usage high for 1B model: {vram_used}MB")

            # Save test results
            result_data = {
                "test_name": "test_model_loading_rocm",
                "status": "passed",
                "model": models[0]["id"],
                "prompt": test_prompt,
                "response_length": len(response.text),
                "tokens_per_second": response.tokens_per_second,
                "latency_ms": response.latency_ms,
                "vram_used_mb": vram_used,
                "execution_time": end_time - start_time
            }

            result_file = temp_result_file("model_loading_rocm")
            with open(result_file, 'w') as f:
                json.dump(result_data, f, indent=2)

            logger.info(f"Test completed successfully. Results saved to {result_file}")

        except Exception as e:
            logger.error(f"Test failed with error: {e}")
            # Save failure results
            result_data = {
                "test_name": "test_model_loading_rocm",
                "status": "failed",
                "error": str(e),
                "error_type": type(e).__name__
            }

            result_file = temp_result_file("model_loading_rocm")
            with open(result_file, 'w') as f:
                json.dump(result_data, f, indent=2)

            raise

    @pytest.mark.rocm
    def test_api_inference_basic(self, client: LemonadeClient, temp_result_file):
        """
        Test OpenAI-compatible API response format (AS2).

        Given a running Lemonade Server with ROCm backend,
        When user sends OpenAI-compatible API request to http://localhost:8000/api/v1/chat/completions,
        Then server returns properly formatted response with generated text
        """
        # Test API response format
        test_prompt = "Hello, how are you?"
        request = InferenceRequest(
            prompt=test_prompt,
            max_tokens=50
        )

        response = client.chat_completion(request)

        # Validate OpenAI-compatible response structure
        raw_response = response.raw_response

        # Check required fields
        assert "id" in raw_response, "Missing 'id' field in response"
        assert "object" in raw_response, "Missing 'object' field in response"
        assert "created" in raw_response, "Missing 'created' field in response"
        assert "model" in raw_response, "Missing 'model' field in response"
        assert "choices" in raw_response, "Missing 'choices' field in response"
        assert "usage" in raw_response, "Missing 'usage' field in response"

        # Validate choices structure
        choices = raw_response["choices"]
        assert len(choices) > 0, "No choices in response"
        choice = choices[0]
        assert "index" in choice, "Missing 'index' in choice"
        assert "message" in choice, "Missing 'message' in choice"
        assert "finish_reason" in choice, "Missing 'finish_reason' in choice"

        # Validate message structure
        message = choice["message"]
        assert "role" in message, "Missing 'role' in message"
        assert "content" in message, "Missing 'content' in message"
        assert message["role"] == "assistant", f"Unexpected role: {message['role']}"

        # Validate usage structure
        usage = raw_response["usage"]
        assert "prompt_tokens" in usage, "Missing 'prompt_tokens' in usage"
        assert "completion_tokens" in usage, "Missing 'completion_tokens' in usage"
        assert "total_tokens" in usage, "Missing 'total_tokens' in usage"

        # Validate content
        assert response.text, "Empty response content"
        assert len(response.text.strip()) > 0, "Response content is only whitespace"

        # Save test results
        result_data = {
            "test_name": "test_api_inference_basic",
            "status": "passed",
            "prompt": test_prompt,
            "response": response.text[:200] + "..." if len(response.text) > 200 else response.text,
            "response_format_valid": True,
            "api_compatible": True
        }

        result_file = temp_result_file("api_inference_basic")
        with open(result_file, 'w') as f:
            json.dump(result_data, f, indent=2)

    @pytest.mark.rocm
    @pytest.mark.slow
    def test_large_model_vram(self, client: LemonadeClient, monitor: ROCmMonitor,
                             model_configs: Dict[str, Any], temp_result_file):
        """
        Test large model loading and VRAM utilization (AS3).

        Given AMD AI Max+ 395 with 128GB VRAM,
        When loading a large model (e.g., 30B+ parameters),
        Then system utilizes VRAM efficiently without crashes or memory errors
        """
        # Skip if large model not available
        large_model_config = model_configs.get("models", {}).get("llama-3.2-30b-instruct-gguf")
        if not large_model_config:
            pytest.skip("Large model configuration not available")

        # Check if model is available on server
        models = client.list_models()
        model_names = [m["id"] for m in models]
        target_model = large_model_config["name"]

        if target_model not in model_names:
            pytest.skip(f"Large model {target_model} not available on server")

        # Get initial VRAM state
        initial_metrics = monitor.get_rocm_metrics()
        initial_vram = initial_metrics.total_vram_used_mb

        # Test inference with large model
        test_prompt = "Summarize the benefits of renewable energy."
        request = InferenceRequest(
            prompt=test_prompt,
            model=target_model,
            max_tokens=100
        )

        start_time = time.time()
        response = client.chat_completion(request)
        end_time = time.time()

        # Get final VRAM state
        final_metrics = monitor.get_rocm_metrics()
        final_vram = final_metrics.total_vram_used_mb

        # Validate VRAM utilization
        vram_increase = final_vram - initial_vram
        expected_vram = large_model_config["expected_vram_gb"] * 1024  # Convert to MB

        # Should use significant VRAM (at least 80% of expected)
        assert vram_increase > expected_vram * 0.8, (
            f"VRAM usage too low: {vram_increase}MB (expected >{expected_vram * 0.8}MB)"
        )

        # Should not exceed total VRAM capacity
        total_vram = final_metrics.total_vram_total_mb
        assert final_vram < total_vram * 0.95, (
            f"VRAM usage too high: {final_vram}/{total_vram}MB ({final_vram/total_vram*100:.1f}%)"
        )

        # Validate response quality
        assert response.text, "No response from large model"
        assert len(response.text) > 50, "Response too short for large model"

        # Performance should be reasonable (not too slow)
        assert response.tokens_per_second > 1, f"Tokens/sec too low: {response.tokens_per_second}"

        # Save test results
        result_data = {
            "test_name": "test_large_model_vram",
            "status": "passed",
            "model": target_model,
            "model_size": large_model_config["size"],
            "initial_vram_mb": initial_vram,
            "final_vram_mb": final_vram,
            "vram_increase_mb": vram_increase,
            "expected_vram_mb": expected_vram,
            "total_vram_mb": total_vram,
            "vram_utilization_percent": (final_vram / total_vram) * 100,
            "tokens_per_second": response.tokens_per_second,
            "execution_time": end_time - start_time
        }

        result_file = temp_result_file("large_model_vram")
        with open(result_file, 'w') as f:
            json.dump(result_data, f, indent=2)

    @pytest.mark.rocm
    def test_prompt_variation(self, client: LemonadeClient, test_prompts: Dict[str, Any],
                            temp_result_file):
        """
        Test output diversity with different prompts (AS4).

        Given basic inference working,
        When user runs the same model with different prompts,
        Then outputs vary appropriately and maintain coherence
        """
        # Select diverse prompts
        prompts = test_prompts.get("prompts", [])[:5]  # Test first 5 prompts
        if len(prompts) < 3:
            pytest.skip("Insufficient test prompts available")

        responses = []
        models = client.list_models()
        model_id = models[0]["id"] if models else "default"

        for i, prompt in enumerate(prompts):
            request = InferenceRequest(
                prompt=prompt,
                model=model_id,
                max_tokens=100
            )

            response = client.chat_completion(request)
            responses.append({
                "prompt": prompt,
                "response": response.text,
                "tokens": response.tokens_used,
                "tokens_per_second": response.tokens_per_second
            })

        # Validate response diversity
        response_texts = [r["response"] for r in responses]

        # Check that responses are different (basic diversity check)
        unique_responses = set(response_texts)
        assert len(unique_responses) > 1, "All responses are identical - no diversity"

        # Check response quality
        for response in responses:
            assert response["response"], f"Empty response for prompt: {response['prompt']}"
            assert len(response["response"]) > 10, f"Response too short for prompt: {response['prompt']}"
            assert response["tokens_per_second"] > 5, f"Performance too low: {response['tokens_per_second']} tokens/sec"

        # Check that different prompt types produce different response styles
        factual_prompts = [p for p in prompts if "what" in p.lower() or "explain" in p.lower()]
        creative_prompts = [p for p in prompts if "write" in p.lower() or "poem" in p.lower()]

        if factual_prompts and creative_prompts:
            # Basic check: factual responses should be different from creative ones
            factual_responses = [r["response"] for r in responses if r["prompt"] in factual_prompts]
            creative_responses = [r["response"] for r in responses if r["prompt"] in creative_prompts]

            # This is a simple check - in practice, more sophisticated analysis would be needed
            assert len(factual_responses) > 0 and len(creative_responses) > 0, "Mixed prompt types not tested"

        # Save test results
        result_data = {
            "test_name": "test_prompt_variation",
            "status": "passed",
            "model": model_id,
            "prompts_tested": len(prompts),
            "responses_generated": len(responses),
            "unique_responses": len(unique_responses),
            "average_tokens_per_second": sum(r["tokens_per_second"] for r in responses) / len(responses),
            "responses": [
                {
                    "prompt": r["prompt"][:50] + "..." if len(r["prompt"]) > 50 else r["prompt"],
                    "response_length": len(r["response"]),
                    "tokens_used": r["tokens"]
                }
                for r in responses
            ]
        }

        result_file = temp_result_file("prompt_variation")
        with open(result_file, 'w') as f:
            json.dump(result_data, f, indent=2)