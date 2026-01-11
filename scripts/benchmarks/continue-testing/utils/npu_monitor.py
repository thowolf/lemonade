"""NPU monitoring utilities for AMD Ryzen AI hardware."""

from __future__ import annotations

import json
import subprocess
import tempfile
import time
from typing import Dict, Any, Optional


class NPUMonitor:
    """Monitor NPU metrics using xrt-smi."""

    def __init__(self):
        self.last_sample_time = 0
        self.sample_interval = 1.0  # Minimum interval between samples
        self._cached_result = None
        self._cache_timestamp = 0
        self._cache_ttl = 2.0  # Cache results for 2 seconds

    def sample_npu(self) -> Dict[str, Any]:
        """Sample current NPU metrics using xrt-smi.

        Returns dict with keys like:
        - device_count: int
        - gops: float
        - command_submissions: int
        - command_completions: int
        - utilization_percent: float
        - instr_bo_kb: int (total instruction buffer memory)
        - contexts: list of context details
        """
        # Check cache first
        now = time.time()
        if self._cached_result is not None and (now - self._cache_timestamp) < self._cache_ttl:
            return self._cached_result.copy()

        # Rate limit sampling
        if now - self.last_sample_time < self.sample_interval:
            return self._cached_result.copy() if self._cached_result else {}

        self.last_sample_time = now

        try:
            # Use more targeted xrt-smi command for better performance
            # Get only AIE partitions data which contains the metrics we need
            cmd = ['xrt-smi', 'examine', '--report', 'aie-partitions', '-f', 'JSON']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3)

            if result.returncode != 0:
                return self._cached_result.copy() if self._cached_result else {}

            # Parse JSON directly from stdout instead of using temp files
            data = json.loads(result.stdout)
            parsed_result = self.parse_xrt_json(data)

            # Cache the result
            self._cached_result = parsed_result
            self._cache_timestamp = now

            return parsed_result

        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError, KeyError, OSError):
            return self._cached_result.copy() if self._cached_result else {}

    def parse_xrt_json(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse xrt-smi JSON output into standardized metrics.

        Handles both 'examine -r all' and 'examine --report aie-partitions' formats.
        """
        metrics = {}

        # Handle different JSON structures
        if 'devices' in data:
            # Full examine -r all format
            devices = data.get('devices', [])
            metrics['device_count'] = len(devices)

            if not devices:
                return metrics

            # Use first device (typically NPU Strix Halo)
            device = devices[0]
            aie_data = device.get('aie_partitions', {})
            partitions = aie_data.get('partitions', [])

        elif 'aie-partitions' in data:
            # Targeted --report aie-partitions format
            aie_data = data.get('aie-partitions', {})
            partitions = aie_data.get('partitions', [])
            # Assume single device for targeted report
            metrics['device_count'] = 1 if partitions else 0
        else:
            # Unknown format
            return metrics

        # Aggregate AIE partition metrics
        total_instr_bo_kb = 0
        total_submissions = 0
        total_completions = 0
        contexts = []
        gops_values = []

        for partition in partitions:
            partition_id = partition.get('partition_index', 'unknown')
            hw_contexts = partition.get('hw_contexts', [])

            for ctx in hw_contexts:
                # Parse instr_bo_mem (e.g., "1344 KB" -> 1344)
                instr_bo_str = ctx.get('instr_bo_mem', '0 KB')
                instr_bo_kb = int(instr_bo_str.split()[0]) if instr_bo_str.split()[0].isdigit() else 0
                total_instr_bo_kb += instr_bo_kb

                submissions = int(ctx.get('command_submissions', 0))
                completions = int(ctx.get('command_completions', 0))
                total_submissions += submissions
                total_completions += completions

                gops_str = ctx.get('gops', 'N/A')
                gops = float(gops_str) if gops_str != 'N/A' and gops_str.replace('.', '').isdigit() else 0.0
                if gops > 0:
                    gops_values.append(gops)

                contexts.append({
                    'partition_id': partition_id,
                    'context_id': ctx.get('context_id'),
                    'pid': ctx.get('pid'),
                    'instr_bo_kb': instr_bo_kb,
                    'command_submissions': submissions,
                    'command_completions': completions,
                    'gops': gops,
                    'status': ctx.get('status')
                })

        metrics['instr_bo_kb'] = total_instr_bo_kb
        metrics['command_submissions'] = total_submissions
        metrics['command_completions'] = total_completions

        # Calculate utilization
        if total_submissions > 0:
            metrics['utilization_percent'] = min(100.0, (total_completions / total_submissions) * 100.0)
        else:
            metrics['utilization_percent'] = 0.0

        # Average GOPS
        metrics['gops'] = sum(gops_values) / len(gops_values) if gops_values else 0.0
        metrics['contexts'] = contexts

        return metrics

    def aggregate_metrics(self, samples: list) -> Dict[str, Any]:
        """Aggregate multiple NPU samples into summary statistics."""
        if not samples:
            return {}

        # Extract numeric metrics
        gops_values = [s.get('gops', 0) for s in samples if s.get('gops') is not None]
        util_values = [s.get('utilization_percent', 0) for s in samples if s.get('utilization_percent') is not None]
        instr_bo_values = [s.get('instr_bo_kb', 0) for s in samples if s.get('instr_bo_kb') is not None]

        aggregated = {
            'sample_count': len(samples),
            'gops_mean': sum(gops_values) / len(gops_values) if gops_values else 0.0,
            'gops_max': max(gops_values) if gops_values else 0.0,
            'utilization_mean_percent': sum(util_values) / len(util_values) if util_values else 0.0,
            'utilization_max_percent': max(util_values) if util_values else 0.0,
            'instr_bo_mean_kb': sum(instr_bo_values) / len(instr_bo_values) if instr_bo_values else 0.0,
            'instr_bo_max_kb': max(instr_bo_values) if instr_bo_values else 0.0,
        }

        return aggregated