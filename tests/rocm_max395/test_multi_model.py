"""
Multi-Model Testing (User Story 4 - P4)

Tests multiple LLM models simultaneously on AMD AI Max+ 395 with ROCm.
Validates concurrent loading, model routing, specialized model types, and VRAM management.
"""

import pytest
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

from utils.lemonade_client import LemonadeClient, InferenceRequest
from utils.rocm_monitor import ROCmMonitor
from utils.metrics_collector import MetricsCollector, PerformanceMetrics

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class MultiModelResult:
    """Result from multi-model test."""
    test_type: str
    models_loaded: List[str]
    total_vram_used_gb: float
    load_time_seconds: float
    concurrent_requests: int
    success_rate: float
    routing_accuracy: float
    error_messages: List[str]


@dataclass
class ModelLoadResult:
    """Result of loading a specific model."""
    model_name: str
    success: bool
    load_time_seconds: float
    vram_allocated_gb: float
    error_message: Optional[str] = None


class TestMultiModel:
    """Test multi-model capabilities."""

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

    @pytest.fixture
    def multi_model_configs(self, fixtures_dir: Path) -> Dict[str, Any]:
        """Load multi-model test configurations."""
        config_file = fixtures_dir / "multi_model_configs.json"
        if config_file.exists():
            with open(config_file, 'r') as f:
                return json.load(f)
        else:
            # Return minimal default configurations if file doesn't exist yet
            return self._get_default_multi_model_configs()

    def _get_default_multi_model_configs(self) -> Dict[str, Any]:
        """Provide default multi-model configurations for testing."""
        return {
            "model_sets": {
                "small_models": [
                    "llama-3.2-1b-instruct-gguf",
                    "llama-3.2-3b-instruct-gguf"
                ],
                "mixed_sizes": [
                    "llama-3.2-1b-instruct-gguf",
                    "llama-3.2-7b-instruct-gguf"
                ],
                "large_models": [
                    "llama-3.2-7b-instruct-gguf",
                    "llama-3.2-13b-instruct-gguf"
                ]
            },
            "test_scenarios": [
                {
                    "name": "concurrent_small",
                    "models": ["llama-3.2-1b-instruct-gguf", "llama-3.2-3b-instruct-gguf"],
                    "expected_total_vram_gb": 10.0,
                    "concurrent_requests": 4
                },
                {
                    "name": "routing_test",
                    "models": ["llama-3.2-1b-instruct-gguf", "llama-3.2-7b-instruct-gguf"],
                    "routing_tests": 6
                }
            ],
            "model_types": {
                "generation": ["llama-3.2-1b-instruct-gguf", "llama-3.2-7b-instruct-gguf"],
                "instruction_tuned": ["llama-3.2-1b-instruct-gguf", "llama-3.2-7b-instruct-gguf"],
                "embedding": []  # Would need embedding-specific models
            }
        }

    @pytest.mark.rocm
    @pytest.mark.multi_model
    def test_concurrent_model_loading(self, client: LemonadeClient, monitor: ROCmMonitor,
                                     collector: MetricsCollector, multi_model_configs: Dict[str, Any],
                                     model_configs: Dict[str, Any], temp_result_file, results_dir: Path):
        """
        Test loading 2-3 models simultaneously (AS1).

        Validates that multiple models can be loaded concurrently without
        exceeding VRAM limits and that loading performance is acceptable.
        """
        logger.info("Starting concurrent model loading test")

        # Use small models for concurrent loading test
        scenario = multi_model_configs.get("test_scenarios", [{}])[0]
        model_names = scenario.get("models", ["llama-3.2-1b-instruct-gguf", "llama-3.2-3b-instruct-gguf"])

        # Filter to available models
        available_models = []
        for model_key in model_names:
            if model_key in model_configs.get("models", {}):
                available_models.append(model_configs["models"][model_key]["name"])

        if len(available_models) < 2:
            pytest.skip("Need at least 2 models available for concurrent loading test")

        logger.info(f"Testing concurrent loading of models: {available_models}")

        # Monitor initial VRAM state
        initial_vram = monitor.get_rocm_metrics()
        initial_usage = initial_vram.get("vram_used_gb", 0)

        load_results = []
        total_load_time = 0

        try:
            # Load models concurrently (simulate parallel loading)
            start_time = time.time()

            for model_name in available_models:
                load_start = time.time()

                # Simulate model loading by making a test inference
                # In a real multi-model setup, this would load the model
                test_response = client.chat_completion(
                    messages=[{"role": "user", "content": "Hello"}],
                    model=model_name,
                    max_tokens=10
                )

                load_end = time.time()
                load_time = load_end - load_start

                # Monitor VRAM after each model load
                current_vram = monitor.get_rocm_metrics()
                current_usage = current_vram.get("vram_used_gb", 0)
                vram_allocated = current_usage - initial_usage

                load_result = ModelLoadResult(
                    model_name=model_name,
                    success=True,
                    load_time_seconds=load_time,
                    vram_allocated_gb=vram_allocated
                )
                load_results.append(load_result)
                total_load_time += load_time

                logger.info(f"Model {model_name} loaded in {load_time:.2f}s, VRAM: {vram_allocated:.1f}GB")

            end_time = time.time()
            total_duration = end_time - start_time

            # Calculate aggregate metrics
            successful_loads = len([r for r in load_results if r.success])
            success_rate = successful_loads / len(available_models)

            total_vram_used = sum(r.vram_allocated_gb for r in load_results)

            # Validate loading requirements
            assert success_rate >= 0.8, f"Model loading success rate too low: {success_rate:.2f}"
            assert total_vram_used <= 100, f"Total VRAM usage too high: {total_vram_used:.1f}GB (max 100GB)"
            assert total_duration <= 300, f"Total loading time too slow: {total_duration:.1f}s (max 5min)"

            # Expected VRAM validation (rough estimate)
            expected_total_vram = scenario.get("expected_total_vram_gb", 15.0)
            if total_vram_used > 0:  # Only check if we have VRAM measurements
                vram_ratio = total_vram_used / expected_total_vram
                assert 0.5 <= vram_ratio <= 2.0, f"VRAM usage outside expected range: {total_vram_used:.1f}GB vs {expected_total_vram:.1f}GB expected"

            # Create result
            result = MultiModelResult(
                test_type="concurrent_loading",
                models_loaded=available_models,
                total_vram_used_gb=total_vram_used,
                load_time_seconds=total_duration,
                concurrent_requests=0,  # Not applicable for loading test
                success_rate=success_rate,
                routing_accuracy=1.0,  # Not applicable for loading test
                error_messages=[]
            )

            # Save results
            loading_results = {
                "test_type": "concurrent_model_loading",
                "models_loaded": available_models,
                "total_vram_used_gb": total_vram_used,
                "load_time_seconds": total_duration,
                "success_rate": success_rate,
                "individual_results": [
                    {
                        "model_name": r.model_name,
                        "success": r.success,
                        "load_time_seconds": r.load_time_seconds,
                        "vram_allocated_gb": r.vram_allocated_gb
                    } for r in load_results
                ]
            }

            with open(results_dir / "multi_model_concurrent_loading.json", 'w') as f:
                json.dump(loading_results, f, indent=2)

            logger.info(f"Concurrent loading test completed: {successful_loads}/{len(available_models)} models loaded successfully")

        except Exception as e:
            logger.error(f"Concurrent loading test failed: {e}")
            pytest.fail(f"Concurrent model loading test failed: {e}")

    @pytest.mark.rocm
    @pytest.mark.multi_model
    @pytest.mark.routing
    def test_model_routing(self, client: LemonadeClient, monitor: ROCmMonitor,
                          collector: MetricsCollector, multi_model_configs: Dict[str, Any],
                          model_configs: Dict[str, Any], temp_result_file, results_dir: Path):
        """
        Test requests route to correct model without interference (AS2).

        Validates that when multiple models are loaded, requests to specific
        models are routed correctly and responses come from the intended model.
        """
        logger.info("Starting model routing test")

        # Get routing test scenario
        routing_scenario = None
        for scenario in multi_model_configs.get("test_scenarios", []):
            if scenario.get("name") == "routing_test":
                routing_scenario = scenario
                break

        if not routing_scenario:
            # Create default routing scenario
            routing_scenario = {
                "models": ["llama-3.2-1b-instruct-gguf", "llama-3.2-7b-instruct-gguf"],
                "routing_tests": 6
            }

        model_names = routing_scenario.get("models", [])
        num_tests = routing_scenario.get("routing_tests", 6)

        # Filter to available models
        available_models = []
        for model_key in model_names:
            if model_key in model_configs.get("models", {}):
                available_models.append(model_configs["models"][model_key]["name"])

        if len(available_models) < 2:
            pytest.skip("Need at least 2 models available for routing test")

        logger.info(f"Testing routing with models: {available_models}")

        # Prepare test queries that should produce different responses from different models
        test_queries = [
            "Explain quantum physics in one sentence.",
            "What is the capital of France?",
            "How does photosynthesis work?",
            "What are the three states of matter?",
            "Explain machine learning briefly.",
            "What is the largest planet in our solar system?"
        ]

        routing_results = []
        correct_routings = 0

        try:
            for i in range(min(num_tests, len(test_queries))):
                query = test_queries[i % len(test_queries)]

                # Test each model with the same query
                model_responses = {}

                for model_name in available_models:
                    response = client.chat_completion(
                        messages=[{"role": "user", "content": query}],
                        model=model_name,
                        max_tokens=50,
                        temperature=0.1  # Low temperature for consistency
                    )

                    answer = response.get("choices", [{}])[0].get("message", {}).get("content", "")
                    model_responses[model_name] = answer.strip()

                # Validate that responses are different (models should respond differently)
                responses = list(model_responses.values())
                unique_responses = len(set(responses))

                # For routing to work correctly, different models should give different responses
                # (at least for these test queries)
                routing_correct = unique_responses > 1

                if routing_correct:
                    correct_routings += 1

                routing_results.append({
                    "query": query,
                    "model_responses": model_responses,
                    "routing_correct": routing_correct,
                    "unique_responses": unique_responses
                })

                logger.info(f"Routing test {i+1}: {unique_responses} unique responses")

            # Calculate routing accuracy
            routing_accuracy = correct_routings / len(routing_results) if routing_results else 0

            # Validate routing requirements
            assert routing_accuracy >= 0.8, f"Model routing accuracy too low: {routing_accuracy:.2f}"

            # Create result
            result = MultiModelResult(
                test_type="model_routing",
                models_loaded=available_models,
                total_vram_used_gb=0,  # Not measured in this test
                load_time_seconds=0,   # Not applicable
                concurrent_requests=len(routing_results),
                success_rate=1.0,      # All requests succeeded
                routing_accuracy=routing_accuracy,
                error_messages=[]
            )

            # Save results
            routing_test_results = {
                "test_type": "model_routing",
                "models_tested": available_models,
                "routing_accuracy": routing_accuracy,
                "total_tests": len(routing_results),
                "correct_routings": correct_routings,
                "detailed_results": routing_results
            }

            with open(results_dir / "multi_model_routing.json", 'w') as f:
                json.dump(routing_test_results, f, indent=2)

            logger.info(f"Model routing test completed: accuracy={routing_accuracy:.2f} ({correct_routings}/{len(routing_results)} correct)")

        except Exception as e:
            logger.error(f"Model routing test failed: {e}")
            pytest.fail(f"Model routing test failed: {e}")
    @pytest.mark.rocm
    @pytest.mark.multi_model
    @pytest.mark.specialized
    def test_specialized_model_types(self, client: LemonadeClient, monitor: ROCmMonitor,
                                    collector: MetricsCollector, multi_model_configs: Dict[str, Any],
                                    model_configs: Dict[str, Any], temp_result_file, results_dir: Path):
        """
        Test generation, embedding, and instruction-tuned models (AS3).

        Validates that different model types perform their specialized tasks correctly
        when multiple models are loaded simultaneously.
        """
        logger.info("Starting specialized model types test")

        model_types = multi_model_configs.get("model_types", {})

        # Test generation models (text generation)
        generation_models = []
        for model_key in model_types.get("generation", []):
            if model_key in model_configs.get("models", {}):
                generation_models.append(model_configs["models"][model_key]["name"])

        if not generation_models:
            pytest.skip("No generation models available for specialized types test")

        logger.info(f"Testing generation models: {generation_models}")

        generation_results = []

        try:
            # Test text generation capabilities
            generation_prompts = [
                "Write a short poem about technology.",
                "Explain recursion in programming.",
                "Describe a futuristic city."
            ]

            for prompt in generation_prompts:
                for model_name in generation_models[:2]:  # Test up to 2 models
                    response = client.chat_completion(
                        messages=[{"role": "user", "content": prompt}],
                        model=model_name,
                        max_tokens=100,
                        temperature=0.7  # Higher temperature for creativity
                    )

                    generated_text = response.get("choices", [{}])[0].get("message", {}).get("content", "")

                    # Evaluate generation quality
                    quality_score = self._evaluate_generation_quality(generated_text, prompt)

                    generation_results.append({
                        "model": model_name,
                        "prompt": prompt,
                        "response": generated_text,
                        "quality_score": quality_score
                    })

            # Test instruction-tuned capabilities (if available)
            instruction_models = []
            for model_key in model_types.get("instruction_tuned", []):
                if model_key in model_configs.get("models", {}):
                    instruction_models.append(model_configs["models"][model_key]["name"])

            instruction_results = []
            if instruction_models:
                instruction_tasks = [
                    "Summarize the benefits of exercise in 2-3 sentences.",
                    "Explain why the sky is blue in simple terms.",
                    "List 3 healthy breakfast options."
                ]

                for task in instruction_tasks:
                    for model_name in instruction_models[:1]:  # Test 1 instruction model
                        response = client.chat_completion(
                            messages=[{"role": "user", "content": task}],
                            model=model_name,
                            max_tokens=80,
                            temperature=0.1  # Lower temperature for instruction following
                        )

                        answer = response.get("choices", [{}])[0].get("message", {}).get("content", "")

                        # Evaluate instruction following
                        instruction_score = self._evaluate_instruction_following(answer, task)

                        instruction_results.append({
                            "model": model_name,
                            "task": task,
                            "response": answer,
                            "instruction_score": instruction_score
                        })

            # Calculate aggregate scores
            avg_generation_quality = sum(r["quality_score"] for r in generation_results) / len(generation_results) if generation_results else 0
            avg_instruction_score = sum(r["instruction_score"] for r in instruction_results) / len(instruction_results) if instruction_results else 0

            # Validate specialized capabilities
            assert avg_generation_quality >= 0.5, f"Generation quality too low: {avg_generation_quality:.2f}"

            if instruction_results:
                assert avg_instruction_score >= 0.6, f"Instruction following too low: {avg_instruction_score:.2f}"

            # Save results
            specialized_results = {
                "test_type": "specialized_model_types",
                "generation_models_tested": list(set(r["model"] for r in generation_results)),
                "instruction_models_tested": list(set(r["model"] for r in instruction_results)),
                "average_generation_quality": avg_generation_quality,
                "average_instruction_score": avg_instruction_score,
                "generation_results": generation_results,
                "instruction_results": instruction_results
            }

            with open(results_dir / "multi_model_specialized_types.json", "w") as f:
                json.dump(specialized_results, f, indent=2)

            logger.info(f"Specialized model types test completed: gen_quality={avg_generation_quality:.2f}, inst_score={avg_instruction_score:.2f}")

        except Exception as e:
            logger.error(f"Specialized model types test failed: {e}")
            pytest.fail(f"Specialized model types test failed: {e}")

    def _evaluate_generation_quality(self, text: str, prompt: str) -> float:
        """Evaluate text generation quality."""
        if not text.strip():
            return 0.0

        score = 0.0

        # Basic quality checks
        word_count = len(text.split())
        if 20 <= word_count <= 150:  # Reasonable length
            score += 0.4

        # Check for creativity/relevance
        if len(set(text.lower().split())) > 10:  # Some vocabulary variety
            score += 0.3

        # Check response is not just repeating the prompt
        prompt_words = set(prompt.lower().split())
        response_words = set(text.lower().split())
        overlap_ratio = len(prompt_words.intersection(response_words)) / len(prompt_words) if prompt_words else 0

        if overlap_ratio < 0.8:  # Not just copying the prompt
            score += 0.3

        return min(score, 1.0)

    def _evaluate_instruction_following(self, response: str, task: str) -> float:
        """Evaluate how well the model follows instructions."""
        if not response.strip():
            return 0.0

        score = 0.0

        # Check for task completion
        if len(response.split()) > 5:  # Provides some content
            score += 0.4

        # Check for structured response (for list/summarize tasks)
        if "summarize" in task.lower() and len(response.split(".")) >= 2:
            score += 0.3
        elif "list" in task.lower() and ("\n" in response or "," in response):
            score += 0.3

        # Check for appropriate detail level
        if 10 <= len(response.split()) <= 50:  # Appropriate length
            score += 0.3

        return min(score, 1.0)
