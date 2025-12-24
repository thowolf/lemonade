"""
Evaluation configuration management.

This module provides configuration classes and validation for LLM evaluation
workflows based on the JSON schema in contracts/evaluation-config.schema.json
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator, model_validator
import yaml


class Metadata(BaseModel):
    """Evaluation metadata."""
    name: str = Field(..., min_length=1, max_length=255, description="Human-readable evaluation name")
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$", description="Evaluation configuration version")
    created: datetime = Field(..., description="ISO 8601 timestamp when configuration was created")
    description: Optional[str] = Field(None, max_length=1000, description="Optional description")
    author: Optional[str] = Field(None, max_length=100, description="Author identifier")


class QuantizationConfig(BaseModel):
    """Quantization configuration."""
    method: str = Field(..., description="Quantization method")
    bits: Optional[int] = Field(None, ge=2, le=32, description="Number of bits for quantization")


class MoEConfig(BaseModel):
    """Mixture of Experts configuration."""
    num_experts: int = Field(..., gt=0, description="Total number of experts")
    experts_per_token: int = Field(..., gt=0, description="Number of active experts per token")
    expert_capacity: Optional[float] = Field(None, ge=0.1, le=2.0, description="Capacity factor")


class ModelConfig(BaseModel):
    """Model specification."""
    identifier: str = Field(..., min_length=1, max_length=255, description="Unique model identifier")
    checkpoint: str = Field(..., description="HuggingFace checkpoint path")
    recipe: str = Field(..., description="Execution backend/recipe")
    quantization: Optional[QuantizationConfig] = Field(None, description="Quantization configuration")
    moe: Optional[MoEConfig] = Field(None, description="MoE configuration if applicable")
    size_gb: Optional[float] = Field(None, gt=0.1, description="Model size in gigabytes")
    context_length: Optional[int] = Field(None, gt=512, description="Maximum context window size")

    @validator('checkpoint')
    def validate_checkpoint(cls, v):
        """Validate checkpoint format."""
        if ':' not in v or v.count(':') != 1:
            raise ValueError("Checkpoint must be in format 'org/repo:file'")
        return v


class HardwareConfig(BaseModel):
    """Hardware and execution configuration."""
    backend: str = Field(..., description="Hardware backend")
    device: str = Field(..., description="Target execution device")
    platform: Optional[str] = Field(None, description="Hardware platform identifier")
    architecture: Optional[str] = Field(None, pattern=r"^gfx\d+$", description="GPU/NPU architecture")
    vram_limit_gb: Optional[int] = Field(None, gt=0, description="VRAM limit in gigabytes")
    system_ram_gb: Optional[int] = Field(None, gt=4, description="System RAM in gigabytes")
    flags: Optional[List[str]] = Field(None, description="Additional backend flags")


class PerformanceBenchmarkConfig(BaseModel):
    """Performance benchmarking configuration."""
    enabled: bool = Field(True, description="Whether performance benchmarks are enabled")
    iterations: int = Field(5, ge=1, le=100, description="Number of benchmark iterations")
    prompts_per_iteration: int = Field(10, ge=1, le=1000, description="Number of prompts per iteration")
    metrics: List[str] = Field(..., min_items=1, description="Performance metrics to collect")
    warmup_iterations: int = Field(2, ge=0, description="Number of warmup iterations")

    @validator('metrics')
    def validate_metrics(cls, v):
        """Validate metric names."""
        valid_metrics = {
            "tokens_per_second", "latency_ms", "time_to_first_token_ms",
            "vram_usage_gb", "cpu_utilization", "gpu_utilization", "power_consumption"
        }
        invalid = set(v) - valid_metrics
        if invalid:
            raise ValueError(f"Invalid metrics: {invalid}")
        return v


class AccuracySuiteConfig(BaseModel):
    """Accuracy benchmark suite configuration."""
    name: str = Field(..., description="Benchmark suite name")
    limit: Optional[int] = Field(None, gt=0, description="Limit number of samples")
    num_fewshot: int = Field(0, ge=0, le=25, description="Number of few-shot examples")


class AccuracyBenchmarkConfig(BaseModel):
    """Accuracy benchmarking configuration."""
    enabled: bool = Field(True, description="Whether accuracy benchmarks are enabled")
    suites: List[AccuracySuiteConfig] = Field(..., min_items=1, description="Benchmark suites to run")


class BenchmarksConfig(BaseModel):
    """Benchmark suite configurations."""
    performance: Optional[PerformanceBenchmarkConfig] = Field(None, description="Performance benchmarking")
    accuracy: Optional[AccuracyBenchmarkConfig] = Field(None, description="Accuracy benchmarking")


class TargetsConfig(BaseModel):
    """Expected performance targets."""
    tokens_per_second: Optional[float] = Field(None, gt=0, description="Minimum expected tokens per second")
    time_to_first_token_ms: Optional[float] = Field(None, gt=0, description="Maximum acceptable TTFT")
    accuracy: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum expected accuracy")
    vram_efficiency_percent: Optional[float] = Field(None, ge=0.0, le=100.0, description="Minimum VRAM efficiency")
    max_latency_p95_ms: Optional[float] = Field(None, gt=0, description="Maximum acceptable P95 latency")


class WandbConfig(BaseModel):
    """Weights & Biases integration configuration."""
    enabled: bool = Field(True, description="Enable W&B logging")
    project: str = Field("lemonade-ryzenai-evals", description="W&B project name")
    entity: Optional[str] = Field(None, description="W&B team/entity name")
    offline: bool = Field(False, description="Run in offline mode")
    tags: Optional[List[str]] = Field(None, max_items=20, description="Additional custom tags")


class RetryConfig(BaseModel):
    """Retry configuration for failed evaluations."""
    max_retries: int = Field(3, ge=0, le=10, description="Maximum number of retry attempts")
    retry_delay_seconds: int = Field(30, ge=1, le=300, description="Delay between retry attempts")
    retry_on: List[str] = Field(
        ["timeout", "connection_error"],
        description="Error types to retry on"
    )

    @validator('retry_on')
    def validate_retry_on(cls, v):
        """Validate retry error types."""
        valid_errors = {"timeout", "connection_error", "oom", "all"}
        invalid = set(v) - valid_errors
        if invalid:
            raise ValueError(f"Invalid retry_on values: {invalid}")
        return v


class EvaluationConfig(BaseModel):
    """Main evaluation configuration class."""
    metadata: Metadata = Field(..., description="Evaluation metadata")
    model: ModelConfig = Field(..., description="Model specification")
    hardware: HardwareConfig = Field(..., description="Hardware configuration")
    benchmarks: BenchmarksConfig = Field(..., description="Benchmark configurations")
    targets: Optional[TargetsConfig] = Field(None, description="Performance targets")
    wandb: Optional[WandbConfig] = Field(None, description="W&B integration config")
    retry: Optional[RetryConfig] = Field(None, description="Retry configuration")

    @model_validator(mode='after')
    def validate_config(self) -> 'EvaluationConfig':
        """Cross-field validation."""
        # Ensure at least one benchmark type is enabled
        benchmarks = self.benchmarks
        if benchmarks:
            perf_enabled = benchmarks.performance and benchmarks.performance.enabled
            acc_enabled = benchmarks.accuracy and benchmarks.accuracy.enabled
            if not (perf_enabled or acc_enabled):
                raise ValueError("At least one benchmark type must be enabled")

        return self

    @classmethod
    def from_yaml(cls, path: Union[str, Path]) -> 'EvaluationConfig':
        """Load configuration from YAML file."""
        path = Path(path)
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return cls(**data)

    @classmethod
    def from_json(cls, path: Union[str, Path]) -> 'EvaluationConfig':
        """Load configuration from JSON file."""
        path = Path(path)
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(**data)

    def to_yaml(self, path: Union[str, Path]) -> None:
        """Save configuration to YAML file."""
        path = Path(path)
        data = self.dict()
        # Convert datetime to ISO string
        if 'metadata' in data and 'created' in data['metadata']:
            data['metadata']['created'] = data['metadata']['created'].isoformat()
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def to_json(self, path: Union[str, Path]) -> None:
        """Save configuration to JSON file."""
        path = Path(path)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.dict(), f, indent=2, default=str)

    def validate_against_schema(self, schema_path: Union[str, Path]) -> List[str]:
        """Validate configuration against JSON schema."""
        # This would implement full JSON schema validation
        # For now, return empty list (Pydantic handles most validation)
        return []