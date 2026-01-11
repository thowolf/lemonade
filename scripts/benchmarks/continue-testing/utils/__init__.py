"""Error handling base classes for the Continue testing framework."""

from typing import Optional
import os


class ConfigError(Exception):
    """Raised when configuration files are invalid or missing."""

    def __init__(self, message: str, config_file: Optional[str] = None):
        super().__init__(message)
        self.config_file = config_file


class MonitoringError(Exception):
    """Raised when system monitoring fails."""

    def __init__(self, message: str, metric_type: Optional[str] = None):
        super().__init__(message)
        self.metric_type = metric_type


class FreezeDetectionError(Exception):
    """Raised when freeze detection fails."""

    def __init__(self, message: str, detection_method: Optional[str] = None):
        super().__init__(message)
        self.detection_method = detection_method


def sanitize_path_for_logging(path: str) -> str:
    """Sanitize file paths for logging to avoid exposing sensitive information.

    Replaces user home directory with ~ and removes potentially sensitive path components.

    Args:
        path: The file path to sanitize

    Returns:
        Sanitized path safe for logging
    """
    if not path:
        return path

    # Normalize path separators for consistent comparison
    path = os.path.normpath(path)
    home = os.path.normpath(os.path.expanduser("~"))

    # Replace user home directory with ~
    if path.startswith(home):
        path = path.replace(home, "~", 1)
        return path  # If we replaced home, return the sanitized path

    # For paths that don't start with home, check for other sensitive patterns
    path_parts = path.split(os.sep)

    # If path contains sensitive keywords, truncate it
    sensitive_keywords = ['users', 'documents', 'desktop', 'downloads', 'temp', 'tmp', 'home']
    for i, part in enumerate(path_parts):
        if part.lower() in sensitive_keywords and i < len(path_parts) - 1:
            # Truncate after the sensitive directory
            truncated = os.sep.join(path_parts[:i+2]) + os.sep + "..."
            return truncated

    return path