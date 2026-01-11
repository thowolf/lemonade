"""W&B logger integration (lightweight wrapper)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional


class WandbLogger:
    """Lightweight W&B integration wrapper with explicit run lifecycle.

    This wrapper is defensive: it tolerates partial/mocked W&B implementations by
    checking callable attributes before calling them, and provides helpers for
    logging time-series metrics and grouping runs.
    """

    def __init__(self, project: str = "lemonade-continue-testing", run_name: str | None = None, group: Optional[str] = None, offline: bool = False):
        self.project = project
        self.run_name = run_name
        self.group = group
        self.offline = offline
        self._wandb = None
        self._run = None
        try:
            import wandb  # type: ignore
            self._wandb = wandb
            # Set offline mode if requested
            if self.offline:
                import os
                os.environ["WANDB_MODE"] = "offline"
        except Exception:
            self._wandb = None

    def is_available(self) -> bool:
        return self._wandb is not None

    def start_run(self, config: Dict[str, Any] | None = None, group: Optional[str] = None) -> bool:
        """Start a W&B run.

        Args:
            config: Optional configuration dict to attach to the run.
            group: Optional run group name to associate related runs together.

        Returns:
            True if a run was successfully started (or the underlying `init` callable exists), False otherwise.
        """
        if not self._wandb:
            return False
        
        # Check if run is already active
        if self._run is not None:
            # Update config if provided
            if config is not None and hasattr(self._run, 'config'):
                try:
                    for key, value in config.items():
                        self._run.config[key] = value
                except Exception:
                    pass
            return True
            
        try:
            # pass group/run_name/config if the underlying wandb supports them
            args = {
                "project": self.project,
                "name": self.run_name,
            }
            if config is not None:
                args["config"] = config
            if group is not None:
                args["group"] = group
            elif self.group is not None:
                args["group"] = self.group

            # Defensive call
            init = getattr(self._wandb, "init", None)
            if callable(init):
                self._run = init(**args)
                return True
            return False
        except Exception:
            return False

    def finish_run(self) -> bool:
        """Finish the active W&B run and clear the local run handle.

        Returns True if the finish operation was invoked, False otherwise.
        """
        if not self._wandb or not self._run:
            return False
        try:
            finish = getattr(self._wandb, "finish", None)
            if callable(finish):
                finish()
        finally:
            self._run = None
        return True

    def log_test_run(self, data: Dict[str, Any]) -> bool:
        """Write a run summary to W&B if available.

        The method attempts to update the underlying `wandb.run.summary` dictionary
        with the provided test run data and is resilient to partial/mock implementations.
        """
        if not self._wandb:
            return False
        if not self._run:
            self.start_run()
        try:
            # Summary storage if available
            wb_run = getattr(self._wandb, "run", None)
            if wb_run is not None and getattr(wb_run, "summary", None) is not None:
                update = getattr(wb_run.summary, "update", None)
                if callable(update):
                    update({"test_run": data})
            return True
        except Exception:
            return False

    def log_metrics(self, series: Dict[str, Any]) -> bool:
        """Log a single metrics dict to W&B."""
        if not self._wandb:
            return False
        try:
            log = getattr(self._wandb, "log", None)
            if callable(log):
                log(series)
                return True
            return False
        except Exception:
            return False

    def log_metrics_series(self, series_list: List[Dict[str, Any]], step_key: Optional[str] = None) -> bool:
        """Log a sequence of metric dicts to W&B (useful for time series).

        Adds an incremental step or timestamp field when `step_key` is provided
        (e.g., step_key="step" will add {'step': 0}, {'step': 1}, ... to logs).
        """
        if not self._wandb:
            return False
        try:
            log = getattr(self._wandb, "log", None)
            if not callable(log):
                return False
            for i, s in enumerate(series_list):
                payload = dict(s)
                if step_key:
                    payload[step_key] = i
                log(payload)
            return True
        except Exception:
            return False

    def set_group(self, group: str):
        """Set a run group to be used for subsequent `start_run` calls."""
        self.group = group

    def log_freeze_event(self, data: Dict[str, Any]) -> bool:
        if not self._wandb:
            return False
        try:
            log = getattr(self._wandb, "log", None)
            if callable(log):
                log({"freeze_event": data})
                return True
            return False
        except Exception:
            return False

    def log_performance_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Log performance comparison metrics to W&B.

        Args:
            metrics: Performance metrics dict from PerformanceAnalyzer

        Returns:
            True if logging was successful, False otherwise
        """
        if not self._wandb:
            return False
        if not self._run:
            self.start_run()
        try:
            log = getattr(self._wandb, "log", None)
            if callable(log):
                # Flatten nested metrics for W&B logging
                flattened = self._flatten_performance_metrics(metrics)
                log({"performance_metrics": flattened})
                return True
            return False
        except Exception:
            return False

    def _flatten_performance_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten nested performance metrics for W&B logging."""
        flattened = {}

        # Handle performance_by_model structure
        if "performance_by_model" in metrics:
            for model_name, model_metrics in metrics["performance_by_model"].items():
                prefix = f"model_{model_name.replace(':', '_').replace('.', '_')}_"

                # Response time metrics
                if "response_time_ms" in model_metrics:
                    rt = model_metrics["response_time_ms"]
                    if isinstance(rt, dict):
                        flattened[f"{prefix}response_time_mean"] = rt.get("mean")
                        flattened[f"{prefix}response_time_p50"] = rt.get("p50")
                        flattened[f"{prefix}response_time_p95"] = rt.get("p95")
                        flattened[f"{prefix}response_time_p99"] = rt.get("p99")

                # Tokens per second
                if "tokens_per_second" in model_metrics:
                    tps = model_metrics["tokens_per_second"]
                    if isinstance(tps, dict):
                        flattened[f"{prefix}tokens_per_second_mean"] = tps.get("mean")
                        flattened[f"{prefix}tokens_per_second_p50"] = tps.get("p50")

                # NPU utilization
                if "npu_utilization_percent" in model_metrics:
                    npu = model_metrics["npu_utilization_percent"]
                    if isinstance(npu, dict):
                        flattened[f"{prefix}npu_utilization_mean"] = npu.get("mean")
                        flattened[f"{prefix}npu_utilization_max"] = npu.get("max")

                # Memory usage
                if "memory_peak_gb" in model_metrics:
                    flattened[f"{prefix}memory_peak_gb"] = model_metrics["memory_peak_gb"]

                # Test run count
                if "test_runs_count" in model_metrics:
                    flattened[f"{prefix}test_runs_count"] = model_metrics["test_runs_count"]

        # Handle overall stats
        if "overall_stats" in metrics:
            overall = metrics["overall_stats"]
            flattened["overall_models_tested"] = overall.get("models_tested", 0)
            flattened["overall_total_runs"] = overall.get("total_runs", 0)
            flattened["overall_avg_response_time"] = overall.get("avg_response_time_ms", 0)
            flattened["overall_avg_tokens_per_second"] = overall.get("avg_tokens_per_second", 0)

        return flattened

    def sync_offline_data(self) -> bool:
        """Sync offline W&B data to server if in offline mode.

        Returns:
            True if sync was attempted (regardless of success), False if not in offline mode or W&B unavailable.
        """
        if not self.offline or not self._wandb:
            return False
        try:
            # Try to sync offline data
            sync = getattr(self._wandb, "sync", None)
            if callable(sync):
                sync()
                return True
            return False
        except Exception:
            return False
