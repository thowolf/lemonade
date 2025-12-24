"""
Data models for LLM evaluation workflows.

This module defines Pydantic models for evaluation entities based on the
data model specification in specs/003-wandb-model-comparison/data-model.md
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field, UUID4, validator
from uuid import uuid4


class RunStatus(str, Enum):
    """Evaluation run status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class MoEConfig(BaseModel):
    """Mixture of Experts configuration."""
    num_experts: int = Field(gt=0, description="Total number of experts")
    experts_per_token: int = Field(gt=0, description="Active experts per token")
    expert_capacity: Optional[float] = Field(None, ge=0.1, le=2.0, description="Capacity factor for load balancing")


class HardwarePlatform(BaseModel):
    """Hardware platform specification."""
    platform_name: str = Field(max_length=100, description="Hardware platform identifier")
    cpu: str = Field(max_length=100, description="CPU model")
    gpu: Optional[str] = Field(None, max_length=100, description="GPU model")
    npu: Optional[str] = Field(None, max_length=100, description="NPU model")
    architecture: Optional[str] = Field(None, max_length=50, description="GPU/NPU architecture")
    total_vram_gb: Optional[float] = Field(None, gt=0, description="Total VRAM available")
    system_ram_gb: float = Field(gt=0, description="System RAM")
    os: str = Field(max_length=50, description="Operating system")
    driver_version: Optional[str] = Field(None, max_length=50, description="GPU/NPU driver version")


class ModelConfiguration(BaseModel):
    """Model configuration entity."""
    config_id: UUID4 = Field(default_factory=uuid4, description="Unique configuration identifier")
    model_name: str = Field(max_length=255, description="Model identifier")
    model_family: str = Field(max_length=50, description="Model family for grouping")
    checkpoint: str = Field(description="HuggingFace checkpoint path (org/repo:file)")
    quantization: str = Field(description="Quantization method")
    moe_config: Optional[MoEConfig] = Field(None, description="MoE configuration if applicable")
    size_gb: float = Field(gt=0, description="Model size in gigabytes")
    context_length: int = Field(gt=0, description="Maximum context window size")
    version: Optional[str] = Field(None, pattern=r"^\d+\.\d+\.\d+$", description="Configuration version")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    metadata: Optional[Dict[str, Union[str, int, float, bool]]] = Field(None, description="Additional metadata")

    @validator('checkpoint')
    def validate_checkpoint(cls, v):
        """Validate checkpoint format: org/repo:file"""
        if ':' not in v or v.count(':') != 1:
            raise ValueError("Checkpoint must be in format 'org/repo:file'")
        return v

    @validator('moe_config')
    def validate_moe_config(cls, v):
        """Ensure MoE config has required fields if present."""
        if v and not (v.num_experts and v.experts_per_token):
            raise ValueError("MoE config requires num_experts and experts_per_token")
        if v and v.experts_per_token > v.num_experts:
            raise ValueError("experts_per_token cannot exceed num_experts")
        return v


class AccuracyMetrics(BaseModel):
    """Accuracy metrics from benchmark results."""
    acc: Optional[float] = Field(None, ge=0.0, le=1.0, description="Overall accuracy")
    acc_stderr: Optional[float] = Field(None, ge=0.0, description="Standard error of accuracy")
    exact_match: Optional[float] = Field(None, ge=0.0, le=1.0, description="Exact match score")
    f1: Optional[float] = Field(None, ge=0.0, le=1.0, description="F1 score")
    custom_metrics: Optional[Dict[str, Union[int, float]]] = Field(None, description="Task-specific metrics")


class PerformanceMetrics(BaseModel):
    """Performance metrics from benchmark execution."""
    tokens_per_second: float = Field(gt=0.0, description="Throughput in tokens/second")
    latency_ms: float = Field(gt=0.0, description="Mean latency in milliseconds")
    latency_p50_ms: Optional[float] = Field(None, gt=0.0, description="Median latency")
    latency_p95_ms: Optional[float] = Field(None, gt=0.0, description="95th percentile latency")
    latency_p99_ms: Optional[float] = Field(None, gt=0.0, description="99th percentile latency")
    time_to_first_token_ms: Optional[float] = Field(None, gt=0.0, description="Time to first token")
    total_tokens: int = Field(ge=0, description="Total tokens processed")
    prompt_tokens: int = Field(ge=0, description="Input prompt tokens")
    completion_tokens: int = Field(ge=0, description="Generated completion tokens")

    @validator('latency_p50_ms', 'latency_p95_ms', 'latency_p99_ms')
    def validate_percentiles(cls, v, values):
        """Ensure latency percentiles are in ascending order."""
        if v is None:
            return v
        if 'latency_p50_ms' in values and values['latency_p50_ms'] and v < values['latency_p50_ms']:
            raise ValueError("Latency percentiles must be in ascending order")
        return v

    @validator('total_tokens')
    def validate_token_count(cls, v, values):
        """Ensure total tokens equals prompt + completion."""
        if 'prompt_tokens' in values and 'completion_tokens' in values:
            expected = values.get('prompt_tokens', 0) + values.get('completion_tokens', 0)
            if expected > 0 and v != expected:
                raise ValueError(f"Total tokens ({v}) should equal prompt + completion tokens ({expected})")
        return v


class ResourceMetrics(BaseModel):
    """Resource utilization metrics."""
    peak_memory_mb: float = Field(gt=0.0, description="Peak memory usage in MB")
    avg_memory_mb: Optional[float] = Field(None, gt=0.0, description="Average memory usage in MB")
    vram_usage_mb: Optional[float] = Field(None, gt=0.0, description="GPU/NPU VRAM usage in MB")
    cpu_utilization_percent: float = Field(ge=0.0, le=100.0, description="CPU utilization percentage")
    gpu_utilization_percent: Optional[float] = Field(None, ge=0.0, le=100.0, description="GPU/NPU utilization percentage")
    power_consumption_watts: Optional[float] = Field(None, gt=0.0, description="Power consumption")


class BenchmarkResult(BaseModel):
    """Benchmark result entity."""
    result_id: UUID4 = Field(default_factory=uuid4, description="Unique result identifier")
    run_id: UUID4 = Field(description="Reference to parent evaluation run")
    task_name: str = Field(max_length=255, description="Specific benchmark task")
    accuracy_metrics: Optional[AccuracyMetrics] = Field(None, description="Accuracy scores")
    performance_metrics: PerformanceMetrics = Field(description="Performance measurements")
    resource_metrics: ResourceMetrics = Field(description="Resource utilization data")
    iteration: Optional[int] = Field(None, ge=0, description="Iteration number for multi-run tests")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Execution timestamp")
    sample_count: Optional[int] = Field(None, gt=0, description="Number of samples evaluated")


class EvaluationRun(BaseModel):
    """Evaluation run entity."""
    run_id: UUID4 = Field(default_factory=uuid4, description="Unique run identifier")
    name: str = Field(max_length=255, description="Human-readable run name")
    model_config_id: UUID4 = Field(description="Reference to model configuration")
    benchmark_suite: str = Field(description="Benchmark suite name")
    status: RunStatus = Field(default=RunStatus.PENDING, description="Run status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Execution start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Execution completion timestamp")
    hardware_platform: HardwarePlatform = Field(description="Hardware details")
    backend: str = Field(max_length=50, description="Inference backend used")
    error_message: Optional[str] = Field(None, max_length=1000, description="Error details if failed")
    wandb_run_url: Optional[str] = Field(None, description="Link to W&B dashboard run")
    tags: Optional[List[str]] = Field(None, max_length=20, description="User-defined tags")

    @validator('started_at')
    def validate_started_at(cls, v, values):
        """Ensure started_at is after created_at."""
        if v and 'created_at' in values and values['created_at'] and v < values['created_at']:
            raise ValueError("started_at must be after created_at")
        return v

    @validator('completed_at')
    def validate_completed_at(cls, v, values):
        """Ensure completed_at is after started_at."""
        if v and 'started_at' in values and values['started_at'] and v < values['started_at']:
            raise ValueError("completed_at must be after started_at")
        return v

    @validator('status')
    def validate_status_fields(cls, v, values):
        """Validate required fields based on status."""
        if v == RunStatus.COMPLETED and not values.get('completed_at'):
            raise ValueError("completed_at required for COMPLETED status")
        if v == RunStatus.FAILED and not values.get('error_message'):
            raise ValueError("error_message required for FAILED status")
        return v


class Filters(BaseModel):
    """Filter criteria for comparison sets."""
    model_families: Optional[List[str]] = Field(None, description="Filter by model families")
    quantizations: Optional[List[str]] = Field(None, description="Filter by quantization levels")
    benchmarks: Optional[List[str]] = Field(None, description="Filter by benchmark suites")
    min_accuracy: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum accuracy threshold")
    max_latency_ms: Optional[float] = Field(None, gt=0.0, description="Maximum latency threshold")


class VisualizationConfig(BaseModel):
    """Dashboard visualization preferences."""
    chart_types: Optional[List[str]] = Field(None, description="Preferred chart types")
    primary_metric: Optional[str] = Field(None, description="Main metric to highlight")
    sort_by: Optional[str] = Field(None, description="Sorting criterion")
    group_by: Optional[str] = Field(None, description="Grouping dimension")


class ComparisonSet(BaseModel):
    """Comparison set entity for side-by-side analysis."""
    set_id: UUID4 = Field(default_factory=uuid4, description="Unique set identifier")
    name: str = Field(max_length=255, description="Comparison set name")
    description: Optional[str] = Field(None, max_length=1000, description="Purpose and context")
    run_ids: List[UUID4] = Field(min_items=2, max_items=50, description="Evaluation runs to compare")
    created_by: Optional[str] = Field(None, max_length=100, description="Creator identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    filters: Optional[Filters] = Field(None, description="Applied filters")
    visualization_config: Optional[VisualizationConfig] = Field(None, description="Dashboard layout preferences")
    shared: bool = Field(default=False, description="Whether set is shared")
    wandb_report_url: Optional[str] = Field(None, description="Link to W&B report")