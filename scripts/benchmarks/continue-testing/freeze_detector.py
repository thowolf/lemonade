"""Freeze detection utilities.

Defines :class:`FreezeEvent` and helpers to create and persist freeze diagnostics.
The FreezeDetector class contains convenience methods used by the interactive test runner
and by automated monitors.
"""
from __future__ import annotations

import dataclasses
import datetime
import json
import os
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .metrics_collector import SystemMetrics, SystemMonitor
from .utils.vscode_bridge import ContinueLogMonitor


@dataclass
class FreezeEvent:
    """Represents a detected unresponsive state of the Continue extension."""
    
    freeze_id: str
    run_id: str
    interaction_id: Optional[str]
    detected_timestamp: str
    detection_method: str  # "timeout", "user_report", "log_analysis", "process_monitor"
    last_response_timestamp: Optional[str]
    time_since_last_response_s: Optional[float]
    metrics_at_freeze: SystemMetrics
    continue_process_state: Optional[str]
    diagnostic_logs_path: Optional[str]
    user_notes: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)

    def save(self, results_dir: str) -> str:
        os.makedirs(results_dir, exist_ok=True)
        path = os.path.join(results_dir, f"freeze_{self.freeze_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json())
        return path


class FreezeDetector:
    """Basic freeze detector that can be expanded.

    For now provides helper to create FreezeEvent from a timestamp and SystemMetrics snapshot.
    """

    @staticmethod
    def create_freeze_event(request_index: int, detection_method: str = "timeout", metrics: Optional[SystemMetrics] = None, user_notes: Optional[str] = None) -> FreezeEvent:
        """Create a FreezeEvent with current timestamp and diagnostics."""
        ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        diagnostics = {
            "detection_method": detection_method,
            "user_notes": user_notes,
            "timestamp": ts
        }
        
        if metrics:
            diagnostics["metrics"] = metrics.to_dict()
            # Calculate time since last metrics if available
            try:
                last_dt = datetime.datetime.fromisoformat(metrics.timestamp)
                time_since = (datetime.datetime.now(datetime.timezone.utc) - last_dt).total_seconds()
                diagnostics["time_since_last_metrics_s"] = time_since
            except Exception:
                pass

        return FreezeEvent(
            id=str(uuid.uuid4()),
            detected_at=ts,
            request_index=request_index,
            diagnostics=diagnostics,
            saved_path=""  # Will be set when saved
        )

    def monitor_interaction(self, request_index: int, timeout_seconds: int = 300) -> Optional[FreezeEvent]:
        """Monitor an interaction for freezes using timeout detection.
        
        Returns a FreezeEvent if a freeze is detected, None otherwise.
        """
        import time
        start_time = time.time()
        
        # For now, this is a simple timeout monitor
        # In a real implementation, this would monitor the Continue process
        # and check for responsiveness
        
        return None

    def detect_from_timeout(self, start_time: float, timeout_seconds: int, request_index: int) -> Optional[FreezeEvent]:
        """Check if a timeout has occurred and create a freeze event if so."""
        import time
        elapsed = time.time() - start_time
        
        if elapsed >= timeout_seconds:
            return self.create_freeze_event(
                request_index=request_index,
                detection_method="timeout",
                user_notes=f"Operation timed out after {elapsed:.1f} seconds (limit: {timeout_seconds}s)"
            )
        
        return None

    def detect_from_logs(self, request_index: int, since_timestamp: Optional[str] = None) -> Optional[FreezeEvent]:
        """Check Continue logs for freeze indicators and create freeze event if found."""
        monitor = ContinueLogMonitor()
        errors = monitor.parse_logs(since_timestamp)
        
        # Look for critical errors that indicate freezes
        critical_errors = [e for e in errors if e["severity"] == "ERROR"]
        
        if critical_errors:
            # Create freeze event from the most recent critical error
            latest_error = max(critical_errors, key=lambda e: e.get("timestamp", ""))
            
            return self.create_freeze_event(
                request_index=request_index,
                detection_method="log_analysis",
                user_notes=f"Critical error detected in logs: {latest_error['message']}"
            )
        
        return None

    def collect_freeze_diagnostics(self, request_index: int) -> FreezeEvent:
        """Collect comprehensive freeze diagnostics including system snapshot."""
        from .utils.vscode_bridge import find_continue_process
        
        # Sample current system metrics
        monitor = SystemMonitor()
        metrics = monitor.sample_once()
        
        # Find Continue process
        continue_proc = find_continue_process()
        process_state = None
        if continue_proc:
            try:
                process_state = {
                    "pid": continue_proc.pid,
                    "name": continue_proc.info.get("name"),
                    "cpu_percent": continue_proc.cpu_percent(),
                    "memory_percent": continue_proc.memory_percent(),
                    "status": continue_proc.status(),
                    "cmdline": continue_proc.info.get("cmdline")
                }
            except Exception:
                process_state = {"error": "Could not read process state"}
        
        # Collect recent log errors
        log_monitor = ContinueLogMonitor()
        recent_errors = log_monitor.parse_logs()
        
        # Create comprehensive diagnostics
        diagnostics = {
            "detection_method": "comprehensive_snapshot",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "system_metrics": metrics.to_dict() if metrics else None,
            "continue_process": process_state,
            "recent_log_errors": recent_errors[-10:],  # Last 10 errors
            "request_index": request_index
        }
        
        return FreezeEvent(
            id=str(uuid.uuid4()),
            detected_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            request_index=request_index,
            diagnostics=diagnostics,
            saved_path=""
        )
