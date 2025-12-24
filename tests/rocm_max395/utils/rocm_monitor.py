"""
ROCm GPU monitoring utilities for AMD AI Max+ 395 testing.

Provides GPU utilization, VRAM usage, and ROCm-specific metrics collection.
"""

import time
import subprocess
import re
from typing import Dict, Optional, List, Any, Tuple
from dataclasses import dataclass
from pathlib import Path

@dataclass
class GPUInfo:
    """Information about GPU device."""
    device_id: int
    name: str
    architecture: str
    vram_total_mb: float
    vram_used_mb: float
    utilization_percent: float
    temperature_c: float
    power_watts: Optional[float] = None
    memory_clock_mhz: Optional[float] = None
    graphics_clock_mhz: Optional[float] = None

@dataclass
class ROCmMetrics:
    """ROCm-specific performance metrics."""
    timestamp: float
    gpu_info: List[GPUInfo]
    total_vram_used_mb: float
    total_vram_total_mb: float
    average_utilization_percent: float
    max_temperature_c: float

class ROCmMonitor:
    """Monitor ROCm GPU metrics and AMD AI Max+ 395 performance."""

    def __init__(self):
        self.rocm_smi_available = self._check_rocm_smi()
        self.rocminfo_available = self._check_rocminfo()

    def _check_rocm_smi(self) -> bool:
        """Check if rocm-smi is available."""
        try:
            result = subprocess.run(['rocm-smi'], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _check_rocminfo(self) -> bool:
        """Check if rocminfo is available."""
        try:
            result = subprocess.run(['rocminfo'], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def get_gpu_info(self) -> List[GPUInfo]:
        """
        Get detailed information about all GPUs.

        Returns:
            List of GPUInfo objects for each GPU
        """
        if not self.rocm_smi_available:
            return [self._get_mock_gpu_info()]

        try:
            # Run rocm-smi to get GPU information
            cmd = ['rocm-smi', '--showid', '--showproductname', '--showvram', '--showpower',
                   '--showuse', '--showtemp', '--showclocks']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode != 0:
                return [self._get_mock_gpu_info()]

            return self._parse_rocm_smi_output(result.stdout)

        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return [self._get_mock_gpu_info()]

    def _parse_rocm_smi_output(self, output: str) -> List[GPUInfo]:
        """Parse rocm-smi output to extract GPU information."""
        gpus = []

        # Split output into lines
        lines = output.strip().split('\n')

        # Find GPU entries (simplified parsing)
        gpu_pattern = r'(\d+)\s+(.+?)\s+(\d+|\w+)\s+(\d+|\w+)\s+(\d+|\w+)\s+(\d+|\w+)\s+(\d+|\w+)'

        for line in lines:
            match = re.search(gpu_pattern, line)
            if match:
                try:
                    device_id = int(match.group(1))
                    name = match.group(2).strip()

                    # Parse VRAM (convert to MB)
                    vram_used = self._parse_memory_value(match.group(3))
                    vram_total = self._parse_memory_value(match.group(4))

                    utilization = float(match.group(5).rstrip('%'))
                    temperature = float(match.group(6).rstrip('cC'))
                    power = float(match.group(7).rstrip('wW'))

                    gpu = GPUInfo(
                        device_id=device_id,
                        name=name,
                        architecture="gfx1151",  # Assume Max+ 395
                        vram_total_mb=vram_total,
                        vram_used_mb=vram_used,
                        utilization_percent=utilization,
                        temperature_c=temperature,
                        power_watts=power
                    )
                    gpus.append(gpu)

                except (ValueError, IndexError):
                    continue

        return gpus if gpus else [self._get_mock_gpu_info()]

    def _parse_memory_value(self, value: str) -> float:
        """Parse memory value from rocm-smi output."""
        value = value.strip().upper()
        if 'G' in value:
            return float(value.rstrip('G')) * 1024
        elif 'M' in value:
            return float(value.rstrip('M'))
        else:
            try:
                return float(value)
            except ValueError:
                return 0.0

    def _get_mock_gpu_info(self) -> GPUInfo:
        """Return mock GPU info when ROCm tools are not available."""
        return GPUInfo(
            device_id=0,
            name="AMD AI Max+ 395 (Mock)",
            architecture="gfx1151",
            vram_total_mb=131072,  # 128GB
            vram_used_mb=0.0,
            utilization_percent=0.0,
            temperature_c=30.0
        )

    def get_rocm_metrics(self) -> ROCmMetrics:
        """
        Get comprehensive ROCm metrics.

        Returns:
            ROCmMetrics object with current GPU state
        """
        gpu_info = self.get_gpu_info()

        total_vram_used = sum(gpu.vram_used_mb for gpu in gpu_info)
        total_vram_total = sum(gpu.vram_total_mb for gpu in gpu_info)
        avg_utilization = sum(gpu.utilization_percent for gpu in gpu_info) / len(gpu_info)
        max_temp = max(gpu.temperature_c for gpu in gpu_info)

        return ROCmMetrics(
            timestamp=time.time(),
            gpu_info=gpu_info,
            total_vram_used_mb=total_vram_used,
            total_vram_total_mb=total_vram_total,
            average_utilization_percent=avg_utilization,
            max_temperature_c=max_temp
        )

    def monitor_performance(self, duration_seconds: int = 60,
                          interval_seconds: float = 1.0) -> List[ROCmMetrics]:
        """
        Monitor ROCm performance over a time period.

        Args:
            duration_seconds: How long to monitor
            interval_seconds: Interval between measurements

        Returns:
            List of ROCmMetrics over the monitoring period
        """
        metrics = []
        start_time = time.time()
        end_time = start_time + duration_seconds

        while time.time() < end_time:
            metrics.append(self.get_rocm_metrics())
            time.sleep(interval_seconds)

        return metrics

    def check_rocm_health(self) -> Dict[str, Any]:
        """
        Check ROCm installation health and capabilities.

        Returns:
            Dictionary with health check results
        """
        health = {
            "rocm_smi_available": self.rocm_smi_available,
            "rocminfo_available": self.rocminfo_available,
            "gpus_detected": 0,
            "total_vram_gb": 0.0,
            "architecture_supported": False,
            "errors": []
        }

        try:
            if self.rocminfo_available:
                result = subprocess.run(['rocminfo'], capture_output=True, text=True, timeout=10)
                if "gfx1151" in result.stdout:
                    health["architecture_supported"] = True

            gpu_info = self.get_gpu_info()
            health["gpus_detected"] = len(gpu_info)
            health["total_vram_gb"] = sum(gpu.vram_total_mb for gpu in gpu_info) / 1024

        except Exception as e:
            health["errors"].append(str(e))

        return health

    def validate_max395_setup(self) -> Tuple[bool, str]:
        """
        Validate that the system is properly set up for AMD AI Max+ 395.

        Returns:
            Tuple of (is_valid, message)
        """
        health = self.check_rocm_health()

        if not health["rocm_smi_available"]:
            return False, "rocm-smi not available. Install AMD ROCm drivers."

        if not health["rocminfo_available"]:
            return False, "rocminfo not available. Install AMD ROCm drivers."

        if health["gpus_detected"] == 0:
            return False, "No GPUs detected. Check hardware and drivers."

        if not health["architecture_supported"]:
            return False, "AMD AI Max+ 395 (gfx1151) not detected. Check hardware."

        if health["total_vram_gb"] < 100:
            return False, f"Insufficient VRAM detected: {health['total_vram_gb']:.1f}GB. Expected ~128GB for Max+ 395."

        return True, f"AMD AI Max+ 395 setup validated. {health['gpus_detected']} GPU(s), {health['total_vram_gb']:.1f}GB VRAM."

    def save_metrics_to_file(self, metrics: ROCmMetrics, filepath: Path) -> None:
        """
        Save ROCm metrics to JSON file.

        Args:
            metrics: ROCmMetrics object to save
            filepath: Path to save file
        """
        data = {
            "timestamp": metrics.timestamp,
            "total_vram_used_mb": metrics.total_vram_used_mb,
            "total_vram_total_mb": metrics.total_vram_total_mb,
            "average_utilization_percent": metrics.average_utilization_percent,
            "max_temperature_c": metrics.max_temperature_c,
            "gpu_info": [
                {
                    "device_id": gpu.device_id,
                    "name": gpu.name,
                    "architecture": gpu.architecture,
                    "vram_total_mb": gpu.vram_total_mb,
                    "vram_used_mb": gpu.vram_used_mb,
                    "utilization_percent": gpu.utilization_percent,
                    "temperature_c": gpu.temperature_c,
                    "power_watts": gpu.power_watts
                }
                for gpu in metrics.gpu_info
            ]
        }

        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            import json
            json.dump(data, f, indent=2)

# Convenience functions
def get_rocm_monitor() -> ROCmMonitor:
    """Create and return a ROCm monitor instance."""
    return ROCmMonitor()

def quick_health_check() -> str:
    """Perform a quick ROCm health check and return status message."""
    monitor = ROCmMonitor()
    is_valid, message = monitor.validate_max395_setup()
    status = "✓ PASS" if is_valid else "✗ FAIL"
    return f"ROCm Health Check: {status} - {message}"