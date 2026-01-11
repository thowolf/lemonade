"""VS Code and Continue extension bridge utilities.

Provides utilities to find Continue processes and monitor extension logs.
"""
from __future__ import annotations

import os
import psutil
from typing import List, Optional


def find_continue_process() -> Optional[psutil.Process]:
    """Find the Continue extension process using psutil.process_iter().

    Returns the first process whose command line contains 'continue' (case-insensitive).
    """
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            if proc.info and proc.info.get("cmdline"):
                cmdline = " ".join(proc.info["cmdline"]).lower()
                if "continue" in cmdline:
                    return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None


class ContinueLogMonitor:
    """Monitor Continue extension logs for errors and freeze indicators."""

    def __init__(self):
        self.log_paths = self.get_log_paths()

    def get_log_paths(self) -> List[str]:
        """Find Continue extension log paths in VS Code user data directory."""
        log_paths = []
        
        # Common VS Code log locations
        possible_paths = [
            os.path.expanduser("~/.vscode/extensions/continue.log"),
            os.path.expanduser("~/Library/Application Support/Code/logs/"),
            os.path.expanduser("~/AppData/Roaming/Code/logs/"),
            os.path.expanduser("~/.config/Code/logs/"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                if os.path.isfile(path):
                    log_paths.append(path)
                elif os.path.isdir(path):
                    # Look for Continue-related log files in directory
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            if "continue" in file.lower() or "log" in file.lower():
                                log_paths.append(os.path.join(root, file))
        
        return log_paths

    def parse_logs(self, since_timestamp: Optional[str] = None) -> List[dict]:
        """Parse logs for errors and return structured error events.
        
        Args:
            since_timestamp: ISO timestamp to filter logs after this time
            
        Returns:
            List of error events with timestamps, messages, and severity
        """
        errors = []
        
        for log_path in self.log_paths:
            try:
                with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        # Simple log parsing - look for ERROR, WARN, etc.
                        if any(keyword in line.upper() for keyword in ["ERROR", "WARN", "EXCEPTION", "TIMEOUT"]):
                            # Extract timestamp if present (basic parsing)
                            timestamp = None
                            message = line.strip()
                            
                            # Try to extract ISO timestamp from line
                            if "T" in line and "+" in line:
                                try:
                                    # Simple timestamp extraction
                                    parts = line.split()
                                    for part in parts:
                                        if "T" in part and "+" in part:
                                            timestamp = part
                                            break
                                except:
                                    pass
                            
                            errors.append({
                                "timestamp": timestamp,
                                "message": message,
                                "severity": "ERROR" if "ERROR" in line.upper() else "WARN",
                                "source": log_path
                            })
                            
            except Exception:
                # Skip files we can't read
                continue
                
        return errors