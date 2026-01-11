"""System metrics collection for the Continue testing framework.

This module provides the :class:`SystemMetrics` dataclass and :class:`SystemMonitor` class
used to sample CPU, memory, process, NPU and GPU metrics. Sampling is safe on systems
without NPU or AMD-specific libraries (it falls back gracefully).
"""
from __future__ import annotations

import dataclasses
import datetime
import json
import threading
import time
import uuid
from dataclasses import dataclass
from typing import List, Optional

import psutil


@dataclass
class SystemMetrics:
    """Snapshot of system-level metrics captured during a test run.

    Follows the data-model.md specification with comprehensive system monitoring.
    Instances are immutable dataclasses (by convention) and provide helpers to
    convert to `dict`/`json` for reporting or serialization.
    """

    metric_id: str
    run_id: str
    timestamp: str
    cpu_percent: float
    cpu_freq_mhz: Optional[float]
    memory_total_gb: float
    memory_used_gb: float
    memory_percent: float
    proc_cpu_percent: Optional[float]
    proc_memory_rss_mb: Optional[float]
    proc_memory_vms_mb: Optional[float]
    npu_device_count: Optional[int]
    npu_gops: Optional[float]
    npu_command_submissions: Optional[int]
    npu_command_completions: Optional[int]
    npu_utilization_percent: Optional[float]
    amd_gpu_utilization_percent: Optional[float]
    amd_gpu_temperature_c: Optional[float]
    amd_gpu_core_clock_mhz: Optional[int]

    def to_dict(self) -> dict:
        """Return the metrics as a plain dict suitable for JSON serialization."""
        return dataclasses.asdict(self)

    def to_json(self) -> str:
        """Return a JSON string representation of the metrics."""
        return json.dumps(self.to_dict(), default=str)

    @staticmethod
    def now_iso() -> str:
        """Return current time as an ISO 8601 string with UTC timezone."""
        return datetime.datetime.now(datetime.timezone.utc).isoformat()

    @classmethod
    def create_now(cls, run_id: str, track_proc: Optional[psutil.Process] = None) -> "SystemMetrics":
        """Collect a fresh snapshot of system metrics and return a SystemMetrics instance.

        Args:
            run_id: Identifier for the current test run (required).
            track_proc: Optional psutil.Process to collect per-process metrics.
        """
        # Generate unique metric ID
        metric_id = str(uuid.uuid4())

        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=None)
        try:
            cpu_freq = psutil.cpu_freq()
            cpu_freq_mhz = cpu_freq.current if cpu_freq else None
        except Exception:
            cpu_freq_mhz = None

        # Memory metrics
        mem = psutil.virtual_memory()
        memory_total_gb = round(mem.total / (1024 ** 3), 2)
        memory_used_gb = round(mem.used / (1024 ** 3), 2)
        memory_percent = mem.percent

        # Process metrics
        proc_cpu_percent = None
        proc_memory_rss_mb = None
        proc_memory_vms_mb = None
        if track_proc:
            try:
                proc_cpu_percent = track_proc.cpu_percent(interval=None)
                mem_info = track_proc.memory_info()
                proc_memory_rss_mb = round(mem_info.rss / (1024 ** 2), 2)
                proc_memory_vms_mb = round(mem_info.vms / (1024 ** 2), 2)
            except Exception:
                pass

        # NPU metrics
        monitor = SystemMonitor()
        npu_data = monitor._sample_npu()
        npu_device_count = npu_data.get("device_count")
        npu_gops = npu_data.get("gops")
        npu_command_submissions = npu_data.get("command_submissions")
        npu_command_completions = npu_data.get("command_completions")
        npu_utilization_percent = npu_data.get("utilization_percent")

        # AMD GPU metrics
        amd_gpu_data = monitor._sample_amd_gpu()
        amd_gpu_utilization_percent = amd_gpu_data.get("utilization_percent")
        amd_gpu_temperature_c = amd_gpu_data.get("temperature_c")
        amd_gpu_core_clock_mhz = amd_gpu_data.get("core_clock_mhz")

        return cls(
            metric_id=metric_id,
            run_id=run_id,
            timestamp=cls.now_iso(),
            cpu_percent=cpu_percent,
            cpu_freq_mhz=cpu_freq_mhz,
            memory_total_gb=memory_total_gb,
            memory_used_gb=memory_used_gb,
            memory_percent=memory_percent,
            proc_cpu_percent=proc_cpu_percent,
            proc_memory_rss_mb=proc_memory_rss_mb,
            proc_memory_vms_mb=proc_memory_vms_mb,
            npu_device_count=npu_device_count,
            npu_gops=npu_gops,
            npu_command_submissions=npu_command_submissions,
            npu_command_completions=npu_command_completions,
            npu_utilization_percent=npu_utilization_percent,
            amd_gpu_utilization_percent=amd_gpu_utilization_percent,
            amd_gpu_temperature_c=amd_gpu_temperature_c,
            amd_gpu_core_clock_mhz=amd_gpu_core_clock_mhz,
        )


class SystemMonitor:
    """Monitors system metrics. Intended to be extended with NPU/GPU sampling."""

    def __init__(self, track_process_name: Optional[str] = None):
        self.track_process_name = track_process_name
        self._track_proc: Optional[psutil.Process] = None
        if track_process_name:
            self._track_proc = self._find_process_by_name(track_process_name)

    def _find_process_by_name(self, name: str) -> Optional[psutil.Process]:
        """Find the first process whose command line contains ``name`` (case-insensitive).

        Returns a psutil.Process if found, otherwise None.
        """
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                if proc.info and name.lower() in (" ".join(proc.info.get("cmdline", [])).lower()):
                    return proc
            except Exception:
                continue
        return None

    def sample(self, run_id: str) -> SystemMetrics:
        """Take a single sample of system metrics."""
        return SystemMetrics.create_now(run_id=run_id, track_proc=self._track_proc)

    def _run_xrt_smi(self) -> dict:
        """Run `xrt-smi -j` (if available) and return parsed JSON. Returns empty dict on error or if not found."""
        import json
        import subprocess

        try:
            proc = subprocess.run(["xrt-smi", "-j"], capture_output=True, text=True, timeout=3)
            if proc.returncode != 0 or not proc.stdout:
                return {}
            data = json.loads(proc.stdout)
            return data
        except FileNotFoundError:
            # xrt-smi not installed
            return {}
        except Exception:
            return {}

    def _sample_npu(self) -> dict:
        """Sample NPU metrics using NPUMonitor."""
        try:
            from utils.npu_monitor import NPUMonitor
            monitor = NPUMonitor()
            return monitor.sample_npu()
        except Exception:
            return {}

    def _sample_amd_gpu(self) -> dict:
        """Attempt to sample AMD GPU metrics. If pyadl not installed or not available, return empty dict."""
        try:
            import pyadl
        except Exception:
            return {}

        try:
            # Example pyadl usage - may vary by version; use defensive access
            adapters = pyadl.get_adapters()
            if not adapters:
                return {}
            gpu = adapters[0]
            return {
                "utilization_percent": getattr(gpu, "utilization", None),
                "temperature_c": getattr(gpu, "temperature", None),
                "core_clock_mhz": getattr(gpu, "core_clock", None),
            }
        except Exception:
            return {}

    def sample_continuous(self, run_id: str, interval: float = 1.0, duration: Optional[float] = None) -> List[SystemMetrics]:
        """Sample continuously in current thread (blocking) for duration seconds. If duration is None, sample once and return.

        Returns list of SystemMetrics objects.
        """
        samples: List[SystemMetrics] = []
        if duration is None:
            samples.append(self.sample(run_id=run_id))
            return samples

        end_time = time.time() + duration
        while time.time() < end_time:
            samples.append(self.sample(run_id=run_id))
            time.sleep(interval)
        return samples

    # Background sampling helpers
    def start_background_sampling(self, run_id: str, interval: float, callback=None) -> threading.Event:
        """Start background sampling at `interval` seconds. If `callback` is provided it will be called with each sample.

        Returns a threading.Event that can be set to stop the background sampler.
        """
        stop_event = threading.Event()

        def _worker():
            while not stop_event.is_set():
                sample = self.sample(run_id=run_id)
                if callback:
                    try:
                        callback(sample)
                    except Exception:
                        pass
                time.sleep(interval)

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        return stop_event

    def stop_background_sampling(self, stop_event: threading.Event):
        """Signal a background sampling loop to stop by setting the provided event.

        This is a convenience wrapper around ``stop_event.set()`` to make intent explicit
        in calling code.
        """
        stop_event.set()