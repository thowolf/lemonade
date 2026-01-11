"""Model and configuration management for the Continue testing framework.

Contains dataclasses for hardware and test run entities, and a :class:`ConfigLoader`
that reads YAML configuration files and validates them using Yamale (optional).
"""
from __future__ import annotations

import dataclasses
import datetime
import json
import os
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class HardwareConfiguration:
    """Hardware and software configuration snapshot for test environment."""
    
    cpu_model: str
    ram_total_gb: float
    npu_available: bool
    npu_driver_version: Optional[str]
    gpu_model: Optional[str]
    gpu_vram_gb: Optional[float]
    gpu_driver_version: Optional[str]
    os_version: str
    python_version: str
    anaconda_env: Optional[str]
    vscode_version: Optional[str]
    continue_version: Optional[str]

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclass
class TestRun:
    """Represents a single execution of the testing framework against a specific model."""
    
    run_id: str
    model_name: str
    start_time: str
    end_time: Optional[str]
    status: str  # "running", "completed", "failed", "aborted"
    hardware_config: HardwareConfiguration
    test_scenario: Optional[str]
    num_interactions_planned: int
    num_interactions_completed: int
    freeze_detected: bool
    freeze_after_interaction: Optional[int]
    metrics_collected: int

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclass
class TestInteraction:
    """Represents a single chat request/response cycle with the Continue extension."""
    
    interaction_id: str
    run_id: str
    sequence_number: int
    request_timestamp: str
    request_text: str
    context_provided: bool
    response_timestamp: Optional[str]
    response_text: Optional[str]
    response_tokens: Optional[int]
    duration_ms: Optional[float]
    tokens_per_second: Optional[float]
    success: bool
    error_message: Optional[str]

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


class ConfigLoader:
    def __init__(self, config_dir: str):
        self.config_dir = config_dir

    def load_models(self) -> List[Dict[str, Any]]:
        path = os.path.join(self.config_dir, "models.yaml")
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data.get("models", [])

    def load_models_config(self) -> Dict[str, Any]:
        """Load the complete models configuration file."""
        path = os.path.join(self.config_dir, "models.yaml")
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data

    def load_scenarios(self) -> List[Dict[str, Any]]:
        path = os.path.join(self.config_dir, "test_scenarios.yaml")
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data.get("scenarios", [])

    def load_hardware(self) -> Dict[str, Any]:
        path = os.path.join(self.config_dir, "hardware.yaml")
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data.get("hardware", {})

    def validate_config(self, config_type: str = "models") -> bool:
        """Validate configuration using Yamale schemas.

        config_type: one of "models", "scenarios", "hardware". Returns True if valid.
        Raises RuntimeError if Yamale is not installed. Raises ValueError on validation errors.
        """
        try:
            import yamale
        except Exception as e:
            raise RuntimeError("Yamale is required for config validation. Install with `pip install yamale`") from e

        schema_map = {
            "models": os.path.join(self.config_dir, "schemas", "models_schema.yaml"),
            "scenarios": os.path.join(self.config_dir, "schemas", "test_scenarios_schema.yaml"),
            "hardware": os.path.join(self.config_dir, "schemas", "hardware_schema.yaml"),
        }

        if config_type not in schema_map:
            raise ValueError(f"Unsupported config type for validation: {config_type}")

        schema_path = schema_map[config_type]
        if not os.path.exists(schema_path):
            raise FileNotFoundError(f"Schema not found: {schema_path}")

        # Use Yamale to load schema and data and validate
        schema = yamale.make_schema(schema_path)
        data_file = {
            "models": os.path.join(self.config_dir, "models.yaml"),
            "scenarios": os.path.join(self.config_dir, "test_scenarios.yaml"),
            "hardware": os.path.join(self.config_dir, "hardware.yaml"),
        }[config_type]

        if not os.path.exists(data_file):
            raise FileNotFoundError(f"Config file not found: {data_file}")

        data = yamale.make_data(data_file)
        try:
            yamale.validate(schema, data)
        except Exception as ex:
            # Yamale raises YamaleError typically; surface as ValueError for caller
            raise ValueError(f"Configuration validation failed: {ex}") from ex

        return True


class ModelManager:
    """Manages model configurations for the Continue testing framework."""

    def __init__(self, config_dir: str):
        self.config_dir = config_dir
        self._models = {}
        self._load_models()

    def _load_models(self):
        """Load models from config/models.yaml."""
        config_loader = ConfigLoader(self.config_dir)
        self._models = {model['name']: model for model in config_loader.load_models()}

    def get_model_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get model configuration by name."""
        return self._models.get(name)

    def load_model_config(self) -> Dict[str, Dict[str, Any]]:
        """Load and return all model configurations from models.yaml."""
        config_loader = ConfigLoader(self.config_dir)
        models = config_loader.load_models()
        return {model['name']: model for model in models}
