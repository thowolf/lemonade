"""
Error handling utilities for evaluation workflows.

This module defines custom exceptions and error handling utilities
for the LLM evaluation system.
"""

from typing import Optional, Dict, Any
from enum import Enum


class EvaluationErrorCode(str, Enum):
    """Error codes for evaluation failures."""
    MODEL_LOAD_FAILED = "model_load_failed"
    SERVER_CONNECTION_FAILED = "server_connection_failed"
    BENCHMARK_EXECUTION_FAILED = "benchmark_execution_failed"
    METRICS_COLLECTION_FAILED = "metrics_collection_failed"
    WANDB_LOGGING_FAILED = "wandb_logging_failed"
    CONFIGURATION_ERROR = "configuration_error"
    RESOURCE_EXHAUSTED = "resource_exhausted"
    TIMEOUT_ERROR = "timeout_error"
    VALIDATION_ERROR = "validation_error"


class EvaluationError(Exception):
    """
    Base exception for evaluation-related errors.

    Provides structured error information for debugging and logging.
    """

    def __init__(self,
                 message: str,
                 error_code: EvaluationErrorCode,
                 details: Optional[Dict[str, Any]] = None,
                 recoverable: bool = False):
        """
        Initialize evaluation error.

        Args:
            message: Human-readable error message
            error_code: Structured error code
            details: Additional error details/context
            recoverable: Whether the error is recoverable (can retry)
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.recoverable = recoverable

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging/serialization."""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code.value,
            "message": self.message,
            "details": self.details,
            "recoverable": self.recoverable
        }


class ModelLoadError(EvaluationError):
    """Error loading or initializing a model."""

    def __init__(self,
                 model_name: str,
                 backend: str,
                 details: Optional[Dict[str, Any]] = None):
        message = f"Failed to load model '{model_name}' with backend '{backend}'"
        super().__init__(
            message=message,
            error_code=EvaluationErrorCode.MODEL_LOAD_FAILED,
            details=details,
            recoverable=True
        )


class ServerConnectionError(EvaluationError):
    """Error connecting to or communicating with evaluation server."""

    def __init__(self,
                 server_url: str,
                 operation: str,
                 details: Optional[Dict[str, Any]] = None):
        message = f"Failed to {operation} with server at {server_url}"
        super().__init__(
            message=message,
            error_code=EvaluationErrorCode.SERVER_CONNECTION_FAILED,
            details=details,
            recoverable=True
        )


class BenchmarkExecutionError(EvaluationError):
    """Error executing a benchmark task."""

    def __init__(self,
                 task_name: str,
                 model_name: str,
                 details: Optional[Dict[str, Any]] = None):
        message = f"Failed to execute benchmark '{task_name}' for model '{model_name}'"
        super().__init__(
            message=message,
            error_code=EvaluationErrorCode.BENCHMARK_EXECUTION_FAILED,
            details=details,
            recoverable=False
        )


class MetricsCollectionError(EvaluationError):
    """Error collecting performance or accuracy metrics."""

    def __init__(self,
                 metric_type: str,
                 details: Optional[Dict[str, Any]] = None):
        message = f"Failed to collect {metric_type} metrics"
        super().__init__(
            message=message,
            error_code=EvaluationErrorCode.METRICS_COLLECTION_FAILED,
            details=details,
            recoverable=True
        )


class WandbLoggingError(EvaluationError):
    """Error logging data to Weights & Biases."""

    def __init__(self,
                 operation: str,
                 details: Optional[Dict[str, Any]] = None):
        message = f"Failed to {operation} with W&B"
        super().__init__(
            message=message,
            error_code=EvaluationErrorCode.WANDB_LOGGING_FAILED,
            details=details,
            recoverable=True
        )


class ConfigurationError(EvaluationError):
    """Error in evaluation configuration."""

    def __init__(self,
                 config_field: str,
                 issue: str,
                 details: Optional[Dict[str, Any]] = None):
        message = f"Configuration error in '{config_field}': {issue}"
        super().__init__(
            message=message,
            error_code=EvaluationErrorCode.CONFIGURATION_ERROR,
            details=details,
            recoverable=False
        )


class ResourceExhaustedError(EvaluationError):
    """Error due to exhausted system resources."""

    def __init__(self,
                 resource_type: str,
                 requested: Any,
                 available: Any,
                 details: Optional[Dict[str, Any]] = None):
        message = f"Resource exhausted: {resource_type} (requested: {requested}, available: {available})"
        super().__init__(
            message=message,
            error_code=EvaluationErrorCode.RESOURCE_EXHAUSTED,
            details=details,
            recoverable=True
        )


class TimeoutError(EvaluationError):
    """Error due to operation timeout."""

    def __init__(self,
                 operation: str,
                 timeout_seconds: int,
                 details: Optional[Dict[str, Any]] = None):
        message = f"Operation '{operation}' timed out after {timeout_seconds} seconds"
        super().__init__(
            message=message,
            error_code=EvaluationErrorCode.TIMEOUT_ERROR,
            details=details,
            recoverable=True
        )


class ValidationError(EvaluationError):
    """Error in data validation."""

    def __init__(self,
                 data_type: str,
                 validation_issue: str,
                 details: Optional[Dict[str, Any]] = None):
        message = f"Validation error for {data_type}: {validation_issue}"
        super().__init__(
            message=message,
            error_code=EvaluationErrorCode.VALIDATION_ERROR,
            details=details,
            recoverable=False
        )


class ErrorHandler:
    """
    Utility class for handling and recovering from evaluation errors.
    """

    @staticmethod
    def is_recoverable(error: Exception) -> bool:
        """
        Check if an error is recoverable.

        Args:
            error: The exception to check

        Returns:
            True if the error can be recovered from
        """
        if isinstance(error, EvaluationError):
            return error.recoverable
        return False

    @staticmethod
    def get_retry_delay(error: Exception, attempt: int) -> Optional[float]:
        """
        Get recommended retry delay for an error.

        Args:
            error: The exception that occurred
            attempt: Current retry attempt number (0-based)

        Returns:
            Delay in seconds, or None if no retry recommended
        """
        if not ErrorHandler.is_recoverable(error):
            return None

        # Exponential backoff with jitter
        base_delay = 1.0
        max_delay = 60.0
        delay = min(base_delay * (2 ** attempt), max_delay)

        return delay

    @staticmethod
    def format_error_for_logging(error: Exception) -> Dict[str, Any]:
        """
        Format an error for structured logging.

        Args:
            error: The exception to format

        Returns:
            Dictionary with error information
        """
        if isinstance(error, EvaluationError):
            return error.to_dict()

        return {
            "error_type": error.__class__.__name__,
            "message": str(error),
            "recoverable": False
        }