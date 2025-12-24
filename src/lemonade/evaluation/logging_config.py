"""
Logging configuration for evaluation workflows.

This module provides logging setup and configuration for the evaluation
system, ensuring consistent logging across all evaluation components.
"""

import logging
import sys
from typing import Optional, Dict, Any
from pathlib import Path


class EvaluationLogger:
    """
    Configured logger for evaluation workflows.

    Provides structured logging with appropriate levels and formatting
    for evaluation operations, errors, and metrics.
    """

    def __init__(self,
                 name: str = "lemonade.evaluation",
                 level: int = logging.INFO,
                 log_file: Optional[Path] = None,
                 console: bool = True):
        """
        Initialize evaluation logger.

        Args:
            name: Logger name
            level: Logging level
            log_file: Optional file to log to
            console: Whether to log to console
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.propagate = False  # Don't propagate to root logger

        # Clear existing handlers
        self.logger.handlers.clear()

        # Create formatter
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Add console handler
        if console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        # Add file handler
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def get_logger(self) -> logging.Logger:
        """Get the configured logger instance."""
        return self.logger


# Global logger instance
_default_logger: Optional[EvaluationLogger] = None


def get_evaluation_logger() -> logging.Logger:
    """
    Get the default evaluation logger.

    Returns:
        Configured logger instance
    """
    global _default_logger
    if _default_logger is None:
        _default_logger = EvaluationLogger()
    return _default_logger.get_logger()


def setup_evaluation_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    console: bool = True
) -> logging.Logger:
    """
    Setup evaluation logging with specified configuration.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        console: Whether to enable console logging

    Returns:
        Configured logger instance
    """
    # Convert string level to logging constant
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }

    log_level = level_map.get(level.upper(), logging.INFO)
    log_path = Path(log_file) if log_file else None

    global _default_logger
    _default_logger = EvaluationLogger(
        level=log_level,
        log_file=log_path,
        console=console
    )

    logger = _default_logger.get_logger()
    logger.info(f"Evaluation logging configured: level={level}, file={log_file}, console={console}")

    return logger


def log_evaluation_event(
    event_type: str,
    message: str,
    extra: Optional[Dict[str, Any]] = None,
    level: str = "INFO"
) -> None:
    """
    Log a structured evaluation event.

    Args:
        event_type: Type of event (e.g., 'evaluation_start', 'benchmark_complete')
        message: Event message
        extra: Additional structured data
        level: Logging level
    """
    logger = get_evaluation_logger()

    # Create structured log message
    log_data = {
        "event_type": event_type,
        "message": message
    }

    if extra:
        log_data.update(extra)

    # Log with appropriate level
    if level.upper() == "DEBUG":
        logger.debug(f"EVALUATION_EVENT: {log_data}")
    elif level.upper() == "INFO":
        logger.info(f"EVALUATION_EVENT: {log_data}")
    elif level.upper() == "WARNING":
        logger.warning(f"EVALUATION_EVENT: {log_data}")
    elif level.upper() == "ERROR":
        logger.error(f"EVALUATION_EVENT: {log_data}")
    elif level.upper() == "CRITICAL":
        logger.critical(f"EVALUATION_EVENT: {log_data}")


# Convenience functions for common evaluation events
def log_evaluation_start(run_id: str, model_name: str, benchmark: str) -> None:
    """Log evaluation run start."""
    log_evaluation_event(
        "evaluation_start",
        f"Starting evaluation run {run_id}",
        {"run_id": run_id, "model_name": model_name, "benchmark": benchmark}
    )


def log_evaluation_complete(run_id: str, status: str, duration: float) -> None:
    """Log evaluation run completion."""
    log_evaluation_event(
        "evaluation_complete",
        f"Evaluation run {run_id} completed with status {status}",
        {"run_id": run_id, "status": status, "duration_seconds": duration}
    )


def log_benchmark_start(run_id: str, task_name: str) -> None:
    """Log benchmark task start."""
    log_evaluation_event(
        "benchmark_start",
        f"Starting benchmark {task_name} for run {run_id}",
        {"run_id": run_id, "task_name": task_name}
    )


def log_benchmark_complete(run_id: str, task_name: str, metrics: Dict[str, Any]) -> None:
    """Log benchmark task completion."""
    log_evaluation_event(
        "benchmark_complete",
        f"Benchmark {task_name} completed for run {run_id}",
        {"run_id": run_id, "task_name": task_name, "metrics": metrics}
    )


def log_error(run_id: str, error_type: str, error_message: str, recoverable: bool = False) -> None:
    """Log evaluation error."""
    log_evaluation_event(
        "evaluation_error",
        f"Error in run {run_id}: {error_message}",
        {"run_id": run_id, "error_type": error_type, "recoverable": recoverable},
        level="ERROR"
    )