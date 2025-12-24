"""
Lemonade Server API client wrapper.

Provides OpenAI-compatible API integration for testing Lemonade Server
with ROCm backend on AMD AI Max+ 395 hardware.
"""

import time
import json
import requests
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from pathlib import Path

@dataclass
class InferenceRequest:
    """Represents an inference request to Lemonade Server."""
    prompt: str
    model: str = "default"
    temperature: float = 0.7
    max_tokens: int = 512
    top_p: float = 0.9
    stream: bool = False
    stop: Optional[List[str]] = None

@dataclass
class InferenceResponse:
    """Represents an inference response from Lemonade Server."""
    text: str
    model: str
    tokens_used: int
    tokens_per_second: float
    latency_ms: float
    finish_reason: str
    raw_response: Dict[str, Any]

class LemonadeClient:
    """OpenAI-compatible client for Lemonade Server API."""

    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        """
        Initialize Lemonade client.

        Args:
            base_url: Base URL for Lemonade Server API
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 300  # 5 minute timeout

    def _make_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to Lemonade Server."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"API request failed: {e}") from e

    def chat_completion(self, request: InferenceRequest) -> InferenceResponse:
        """
        Perform chat completion using OpenAI-compatible API.

        Args:
            request: Inference request parameters

        Returns:
            Inference response with metrics
        """
        start_time = time.time()

        payload = {
            "model": request.model,
            "messages": [{"role": "user", "content": request.prompt}],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p,
            "stream": request.stream,
            "stop": request.stop or []
        }

        raw_response = self._make_request("chat/completions", payload)

        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000

        # Extract response data
        choice = raw_response["choices"][0]
        message = choice["message"]
        usage = raw_response.get("usage", {})

        # Calculate tokens per second (approximate)
        tokens_used = usage.get("completion_tokens", len(message["content"].split()))
        tokens_per_second = tokens_used / ((end_time - start_time) or 0.001)

        return InferenceResponse(
            text=message["content"],
            model=raw_response.get("model", request.model),
            tokens_used=tokens_used,
            tokens_per_second=tokens_per_second,
            latency_ms=latency_ms,
            finish_reason=choice.get("finish_reason", "completed"),
            raw_response=raw_response
        )

    def list_models(self) -> List[Dict[str, Any]]:
        """List available models on Lemonade Server."""
        try:
            response = self.session.get(f"{self.base_url}/models")
            response.raise_for_status()
            return response.json().get("data", [])
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to list models: {e}") from e

    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get information about a specific model."""
        models = self.list_models()
        for model in models:
            if model.get("id") == model_name:
                return model
        raise ValueError(f"Model '{model_name}' not found")

    def health_check(self) -> bool:
        """Check if Lemonade Server is healthy and responding."""
        try:
            response = self.session.get(f"{self.base_url}/health")
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def wait_for_server(self, timeout: int = 60) -> bool:
        """
        Wait for Lemonade Server to become available.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if server becomes available, False otherwise
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.health_check():
                return True
            time.sleep(2)
        return False

    def save_response(self, response: InferenceResponse, filepath: Path) -> None:
        """Save inference response to JSON file."""
        data = {
            "timestamp": time.time(),
            "model": response.model,
            "prompt_length": len(response.text.split()),  # Approximate
            "response_length": len(response.text.split()),
            "tokens_used": response.tokens_used,
            "tokens_per_second": response.tokens_per_second,
            "latency_ms": response.latency_ms,
            "finish_reason": response.finish_reason,
            "text": response.text[:500] + "..." if len(response.text) > 500 else response.text
        }

        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

# Convenience functions for testing
def create_client(base_url: str = "http://localhost:8000/api/v1") -> LemonadeClient:
    """Create and return a Lemonade client instance."""
    return LemonadeClient(base_url)

def simple_inference(prompt: str, model: str = "default",
                    base_url: str = "http://localhost:8000/api/v1") -> InferenceResponse:
    """
    Perform simple inference with default parameters.

    Args:
        prompt: Input prompt
        model: Model name
        base_url: Lemonade Server URL

    Returns:
        Inference response
    """
    client = LemonadeClient(base_url)
    request = InferenceRequest(prompt=prompt, model=model)
    return client.chat_completion(request)