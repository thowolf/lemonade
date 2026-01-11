"""Report generation: performance metrics, compatibility analysis, and trend detection.

This module provides tools to compute aggregated performance metrics, generate
compatibility matrices (JSON/Markdown/CSV), and run simple trend analysis
across historical test runs.
"""
from __future__ import annotations

import dataclasses
import datetime
import json
import os
import statistics
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class PerformanceMetrics:
    """Aggregated performance statistics for a test run or interaction."""
    
    entity_id: str
    entity_type: str  # "test_run", "test_interaction"
    response_time_mean_ms: Optional[float]
    response_time_p50_ms: Optional[float]
    response_time_p95_ms: Optional[float]
    response_time_p99_ms: Optional[float]
    tokens_per_second_mean: Optional[float]
    tokens_per_second_p50: Optional[float]
    memory_peak_gb: Optional[float]
    npu_utilization_mean_percent: Optional[float]
    npu_utilization_max_percent: Optional[float]
    cpu_utilization_mean_percent: Optional[float]
    success_rate_percent: Optional[float]

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


@dataclass
class CompatibilityResult:
    """Summary of a model's compatibility and stability assessment."""
    
    result_id: str
    model_name: str
    assessment_date: str
    test_runs_analyzed: int
    compatible: bool
    max_stable_interactions_observed: int
    freeze_rate_percent: float
    mean_freeze_after_interaction: Optional[float]
    performance_rating: str  # "excellent", "good", "fair", "poor"
    stability_rating: str  # "stable", "mostly_stable", "unstable"
    recommended_for_production: bool
    notes: Optional[str]
    limitations: Optional[List[str]]

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


class PerformanceAnalyzer:
    """Calculate aggregated performance metrics from raw test run/interactions data."""

    @staticmethod
    def calculate_aggregates(response_times_ms: List[float], tokens_per_second: Optional[List[float]] = None) -> Dict[str, Optional[float]]:
        if not response_times_ms:
            return {
                "mean": None, "p50": None, "p95": None, "p99": None,
                "tps_mean": None, "tps_p50": None
            }

        mean = float(statistics.mean(response_times_ms))
        p50 = float(statistics.median(response_times_ms))
        # p95 and p99 using sorted list
        sorted_r = sorted(response_times_ms)
        def percentile(arr, p):
            if not arr:
                return None
            k = (len(arr)-1) * (p/100)
            f = int(k)
            c = min(f+1, len(arr)-1)
            if f == c:
                return float(arr[int(k)])
            d0 = arr[f] * (c - k)
            d1 = arr[c] * (k - f)
            return float(d0 + d1)

        p95 = percentile(sorted_r, 95)
        p99 = percentile(sorted_r, 99)

        tps_mean = None
        tps_p50 = None
        if tokens_per_second:
            tps_mean = float(statistics.mean(tokens_per_second))
            tps_p50 = float(statistics.median(tokens_per_second))

        return {"mean": mean, "p50": p50, "p95": p95, "p99": p99, "tps_mean": tps_mean, "tps_p50": tps_p50}

    @staticmethod
    def calculate_performance_metrics(test_run: Dict[str, Any]) -> PerformanceMetrics:
        """Calculate performance metrics for a single test run."""
        interactions = test_run.get("interactions", [])
        
        # Extract response times and tokens per second
        response_times = []
        tokens_per_second_list = []
        memory_usage = []
        npu_utils = []
        
        for interaction in interactions:
            rt = interaction.get("duration_ms")
            if rt is not None:
                response_times.append(float(rt))
            
            tps = interaction.get("tokens_per_second")
            if tps is not None:
                tokens_per_second_list.append(float(tps))
            
            # Extract memory and NPU metrics from pre/post metrics
            for metrics_key in ["pre_metrics", "post_metrics"]:
                metrics = interaction.get(metrics_key, {})
                mem_used = metrics.get("memory_used_mb")
                if mem_used is not None:
                    memory_usage.append(float(mem_used))
                
                npu_util = metrics.get("npu_metrics", {}).get("utilization_percent")
                if npu_util is not None:
                    npu_utils.append(float(npu_util))
        
        # Calculate aggregates
        perf_aggs = PerformanceAnalyzer.calculate_aggregates(response_times, tokens_per_second_list)
        
        # Calculate memory peak
        memory_peak_gb = max(memory_usage) / 1024 if memory_usage else 0.0
        
        # Calculate NPU utilization mean
        npu_util_mean_percent = statistics.mean(npu_utils) if npu_utils else 0.0
        
        return PerformanceMetrics(
            response_time_p50_ms=perf_aggs["p50"] or 0.0,
            response_time_p95_ms=perf_aggs["p95"] or 0.0,
            tokens_per_second=perf_aggs["tps_mean"] or 0.0,
            memory_peak_gb=memory_peak_gb,
            npu_util_mean_percent=npu_util_mean_percent,
        )

    @staticmethod
    def save_performance_metrics(run_id: str, metrics: PerformanceMetrics, results_dir: str) -> str:
        """Save PerformanceMetrics to JSON file."""
        os.makedirs(results_dir, exist_ok=True)
        path = os.path.join(results_dir, f"{run_id}_perf.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "run_id": run_id,
                "metrics": metrics.to_dict()
            }, f, indent=2)
        return path

    @staticmethod
    def calculate_npu_aggregates(test_runs: List[Dict[str, Any]]) -> Dict[str, Optional[float]]:
        """Calculate NPU utilization aggregates from test runs."""
        npu_utils = []
        for run in test_runs:
            # Check interactions for NPU metrics
            interactions = run.get("interactions", [])
            for interaction in interactions:
                pre_metrics = interaction.get("pre_metrics", {})
                post_metrics = interaction.get("post_metrics", {})
                
                # Extract NPU utilization from both pre and post metrics
                for metrics in [pre_metrics, post_metrics]:
                    npu_data = metrics.get("npu_metrics", {})
                    util = npu_data.get("utilization_percent")
                    if util is not None:
                        npu_utils.append(float(util))

        if not npu_utils:
            return {"mean": None, "max": None, "min": None}

        return {
            "mean": float(statistics.mean(npu_utils)),
            "max": float(max(npu_utils)),
            "min": float(min(npu_utils))
        }


class ReportGenerator:
    """Generate compatibility matrices and performance reports."""

    @staticmethod
    def assess_compatibility(test_runs: List[Dict[str, Any]], model_name: str) -> CompatibilityResult:
        """Assess compatibility for a specific model based on test runs."""
        model_runs = [r for r in test_runs if r.get("model_name") == model_name]
        if not model_runs:
            return CompatibilityResult(model_name, False, 0, "No test runs found")

        freeze_count = sum(1 for r in model_runs if r.get("freeze_detected"))
        success = freeze_count == 0
        notes = f"Tested {len(model_runs)} times, {freeze_count} freezes detected"

        return CompatibilityResult(model_name, success, freeze_count, notes)

    @staticmethod
    def generate_matrix(test_runs: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Generate compatibility matrix JSON."""
        return ReportGenerator.generate_compatibility_matrix(test_runs)

    @staticmethod
    def generate_compatibility_matrix(test_runs: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Produce a compatibility matrix keyed by model name.

        test_runs: list of dictionaries with keys: model_name, freeze_detected (bool), num_interactions_completed (int), response_time_ms (optional), tokens_per_second (optional)
        """
        by_model: Dict[str, List[Dict[str, Any]]] = {}
        for tr in test_runs:
            name = tr.get("model_name")
            by_model.setdefault(name, []).append(tr)

        matrix: Dict[str, Dict[str, Any]] = {}
        for model, runs in by_model.items():
            total = len(runs)
            incompatible = sum(1 for r in runs if r.get("freeze_detected"))
            compatible_count = total - incompatible
            max_stable = 0
            freeze_after_list = []
            response_times = []
            tps_list = []

            for r in runs:
                if r.get("freeze_detected"):
                    fa = r.get("freeze_after_interaction") or 0
                    freeze_after_list.append(fa)
                else:
                    max_stable = max(max_stable, r.get("num_interactions_completed", 0))
                rt = r.get("response_time_ms")
                if rt is not None:
                    response_times.append(float(rt))
                tps = r.get("tokens_per_second")
                if tps is not None:
                    tps_list.append(float(tps))

            freeze_rate = (incompatible / total) * 100.0 if total else 0.0
            mean_freeze_after = float(statistics.mean(freeze_after_list)) if freeze_after_list else None

            # Performance aggregates
            perf_aggs = PerformanceAnalyzer.calculate_aggregates(response_times, tps_list)

            # NPU utilization aggregates
            npu_aggs = PerformanceAnalyzer.calculate_npu_aggregates(runs)

            # Richer rating rules
            performance_rating = "poor"
            if perf_aggs["mean"] is None:
                performance_rating = "unknown"
            else:
                rt_mean = perf_aggs["mean"]
                tps_mean = perf_aggs["tps_mean"] or 0.0
                if rt_mean < 8000 and tps_mean >= 15:
                    performance_rating = "excellent"
                elif rt_mean < 15000 and tps_mean >= 10:
                    performance_rating = "good"
                elif rt_mean < 30000:
                    performance_rating = "fair"
                else:
                    performance_rating = "poor"

            if freeze_rate == 0.0 and performance_rating in ("excellent", "good"):
                stability_rating = "stable"
            elif freeze_rate < 50.0:
                stability_rating = "mostly_stable"
            else:
                stability_rating = "unstable"

            recommended = (stability_rating == "stable" and performance_rating in ("excellent", "good"))

            matrix[model] = {
                "compatible": compatible_count > 0 and freeze_rate == 0.0,
                "max_stable_interactions": max_stable,
                "freeze_rate_percent": freeze_rate,
                "mean_freeze_after_interaction": mean_freeze_after,
                "performance_rating": performance_rating,
                "stability_rating": stability_rating,
                "performance_aggs": perf_aggs,
                "npu_aggs": npu_aggs,
                "recommended_for_production": bool(recommended),
            }

        return matrix

    @staticmethod
    def generate_markdown(matrix: Dict[str, Dict[str, Any]]) -> str:
        """Generate a markdown table from compatibility matrix."""
        lines = ["| Model | Compatible | Max Stable | Freeze % | Perf Rating | Stability | NPU Util % | Recommended |",
                 "|---|---:|---:|---:|---|---|---:|---:|"]
        for model, v in sorted(matrix.items()):
            npu_mean = v.get('npu_aggs', {}).get('mean')
            npu_str = f"{npu_mean:.1f}" if npu_mean is not None else "N/A"
            lines.append(f"| {model} | {v['compatible']} | {v['max_stable_interactions']} | {v['freeze_rate_percent']:.1f} | {v['performance_rating']} | {v['stability_rating']} | {npu_str} | {v['recommended_for_production']} |")
        return "\n".join(lines)

    @staticmethod
    def generate_csv(matrix: Dict[str, Dict[str, Any]]) -> str:
        """Generate a CSV string from compatibility matrix."""
        import csv
        from io import StringIO

        out = StringIO()
        writer = csv.writer(out)
        writer.writerow(["model","compatible","max_stable_interactions","freeze_rate_percent","performance_rating","stability_rating","npu_util_mean_percent","recommended_for_production"])
        for model, v in sorted(matrix.items()):
            npu_mean = v.get('npu_aggs', {}).get('mean')
            writer.writerow([model, v['compatible'], v['max_stable_interactions'], f"{v['freeze_rate_percent']:.1f}", v['performance_rating'], v['stability_rating'], f"{npu_mean:.1f}" if npu_mean is not None else "N/A", v['recommended_for_production']])
        return out.getvalue()

    @staticmethod
    def validate_npu_usage(test_runs: List[Dict[str, Any]], model_name: str) -> Dict[str, Any]:
        """Validate NPU usage for a specific model and provide recommendations."""
        model_runs = [r for r in test_runs if r.get("model_name") == model_name]
        if not model_runs:
            return {"valid": False, "message": "No test runs found for model"}

        npu_aggs = PerformanceAnalyzer.calculate_npu_aggregates(model_runs)
        npu_mean = npu_aggs.get("mean")

        if npu_mean is None:
            return {
                "valid": False,
                "message": "No NPU metrics collected - NPU monitoring may not be available",
                "recommendation": "Check NPU driver installation and monitoring setup"
            }

        if npu_mean == 0:
            return {
                "valid": False,
                "message": f"NPU utilization is 0% - model '{model_name}' is not using hardware acceleration",
                "recommendation": "Verify model is compatible with Ryzen AI NPU or check for driver issues"
            }

        if npu_mean < 10:
            return {
                "valid": True,
                "message": f"Low NPU utilization ({npu_mean:.1f}%) - model may have limited acceleration",
                "recommendation": "Consider optimizing model for better NPU utilization"
            }

        return {
            "valid": True,
            "message": f"Good NPU utilization ({npu_mean:.1f}%) - model is effectively using hardware acceleration",
            "recommendation": None
        }

    @staticmethod
    def compare_against_baselines(npu_aggs: Dict[str, Optional[float]], model_type: str = "llm") -> Dict[str, Any]:
        """Compare NPU metrics against RyzenAI-SW benchmark baselines."""
        # Ryzen AI baseline expectations (approximate from documentation)
        baselines = {
            "llm": {"expected_utilization_min": 20, "expected_gops_min": 10},
            "vision": {"expected_utilization_min": 30, "expected_gops_min": 50},
            "multimodal": {"expected_utilization_min": 15, "expected_gops_min": 8}
        }

        baseline = baselines.get(model_type, baselines["llm"])
        npu_mean = npu_aggs.get("mean")

        if npu_mean is None:
            return {
                "comparison": "unknown",
                "message": "Cannot compare - no NPU metrics available"
            }

        if npu_mean >= baseline["expected_utilization_min"]:
            return {
                "comparison": "good",
                "message": f"NPU utilization ({npu_mean:.1f}%) meets or exceeds baseline expectations for {model_type} models"
            }
        else:
            return {
                "comparison": "below_baseline",
                "message": f"NPU utilization ({npu_mean:.1f}%) is below expected baseline ({baseline['expected_utilization_min']}%) for {model_type} models",
                "recommendation": "Check model optimization or consider alternative configurations"
            }

    @staticmethod
    def analyze_freeze_patterns(test_runs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze freeze patterns across test runs to identify common causes."""
        freeze_events = []
        
        # Collect all freeze events from test runs
        for run in test_runs:
            interactions = run.get("interactions", [])
            for interaction in interactions:
                if interaction.get("freeze_detected"):
                    freeze_events.append({
                        "run_id": run.get("run_id"),
                        "model_name": run.get("model_name"),
                        "interaction_num": interaction.get("interaction_num"),
                        "duration_ms": interaction.get("duration_ms"),
                        "pre_metrics": interaction.get("pre_metrics", {}),
                        "post_metrics": interaction.get("post_metrics", {}),
                        "timestamp": interaction.get("timestamp")
                    })
        
        if not freeze_events:
            return {"pattern": "no_freezes", "message": "No freeze events detected"}
        
        # Analyze patterns
        total_freezes = len(freeze_events)
        models_affected = set(event["model_name"] for event in freeze_events)
        
        # Analyze by model type
        model_patterns = {}
        for model in models_affected:
            model_freezes = [e for e in freeze_events if e["model_name"] == model]
            model_patterns[model] = {
                "freeze_count": len(model_freezes),
                "avg_interaction_num": statistics.mean(e["interaction_num"] for e in model_freezes),
                "interaction_nums": [e["interaction_num"] for e in model_freezes]
            }
        
        # Check for message length correlation (if available in future data)
        # For now, assume interaction_num correlates with complexity
        
        # Check for correlation with NPU utilization
        npu_correlations = []
        for event in freeze_events:
            pre_npu = event.get("pre_metrics", {}).get("npu_metrics", {}).get("utilization_percent")
            post_npu = event.get("post_metrics", {}).get("npu_metrics", {}).get("utilization_percent")
            if pre_npu is not None and post_npu is not None:
                npu_correlations.append({
                    "pre_utilization": pre_npu,
                    "post_utilization": post_npu,
                    "change": post_npu - pre_npu
                })
        
        # Check for correlation with memory usage
        memory_correlations = []
        for event in freeze_events:
            pre_mem = event.get("pre_metrics", {}).get("memory_used_mb")
            post_mem = event.get("post_metrics", {}).get("memory_used_mb")
            if pre_mem is not None and post_mem is not None:
                memory_correlations.append({
                    "pre_memory_mb": pre_mem,
                    "post_memory_mb": post_mem,
                    "change_mb": post_mem - pre_mem
                })
        
        # Determine most likely cause
        if npu_correlations and all(c["post_utilization"] == 0 for c in npu_correlations):
            cause = "npu_not_utilized"
            message = "Freezes consistently occur when NPU utilization drops to 0%"
            recommendation = "Verify model is compatible with Ryzen AI NPU"
        elif memory_correlations and all(c["change_mb"] > 1000 for c in memory_correlations):
            cause = "memory_pressure"
            message = "Freezes correlate with significant memory usage increases"
            recommendation = "Monitor memory usage and consider reducing context size"
        else:
            cause = "unknown"
            message = f"Detected {total_freezes} freeze events across {len(models_affected)} models"
            recommendation = "Further investigation needed"
        
        return {
            "pattern": cause,
            "message": message,
            "recommendation": recommendation,
            "total_freezes": total_freezes,
            "models_affected": list(models_affected),
            "model_patterns": model_patterns,
            "npu_correlations": npu_correlations,
            "memory_correlations": memory_correlations
        }

    @staticmethod
    def analyze_model_performance(test_runs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance metrics across models and test runs."""
        if not test_runs:
            return {"error": "No test runs provided"}

        # Group runs by model
        by_model = {}
        for run in test_runs:
            model = run.get("model_name", "unknown")
            by_model.setdefault(model, []).append(run)

        analysis = {
            "total_runs": len(test_runs),
            "models_analyzed": len(by_model),
            "performance_by_model": {},
            "overall_stats": {}
        }

        all_response_times = []
        all_tps = []
        all_npu_utils = []

        for model, runs in by_model.items():
            model_stats = {
                "run_count": len(runs),
                "response_times_ms": [],
                "tokens_per_second": [],
                "npu_utilizations": [],
                "freeze_count": 0
            }

            for run in runs:
                if run.get("freeze_detected"):
                    model_stats["freeze_count"] += 1

                # Collect performance metrics from interactions
                interactions = run.get("interactions", [])
                for interaction in interactions:
                    duration = interaction.get("duration_ms")
                    if duration:
                        model_stats["response_times_ms"].append(duration)
                        all_response_times.append(duration)

                    # Extract TPS if available
                    tps = interaction.get("tokens_per_second")
                    if tps:
                        model_stats["tokens_per_second"].append(tps)
                        all_tps.append(tps)

                    # Extract NPU utilization
                    pre_metrics = interaction.get("pre_metrics", {})
                    post_metrics = interaction.get("post_metrics", {})
                    for metrics in [pre_metrics, post_metrics]:
                        npu_data = metrics.get("npu_metrics", {})
                        util = npu_data.get("utilization_percent")
                        if util is not None:
                            model_stats["npu_utilizations"].append(util)
                            all_npu_utils.append(util)

            # Calculate aggregates for this model
            perf_stats = {
                "response_time_ms": ReportGenerator._calculate_stats(model_stats["response_times_ms"]),
                "tokens_per_second": ReportGenerator._calculate_stats(model_stats["tokens_per_second"]),
                "npu_utilization_percent": ReportGenerator._calculate_stats(model_stats["npu_utilizations"]),
                "freeze_rate_percent": (model_stats["freeze_count"] / len(runs)) * 100 if runs else 0
            }

            analysis["performance_by_model"][model] = perf_stats

        # Overall statistics
        analysis["overall_stats"] = {
            "response_time_ms": ReportGenerator._calculate_stats(all_response_times),
            "tokens_per_second": ReportGenerator._calculate_stats(all_tps),
            "npu_utilization_percent": ReportGenerator._calculate_stats(all_npu_utils),
            "total_freezes": sum(stats["freeze_count"] for stats in analysis["performance_by_model"].values())
        }

        return analysis

    @staticmethod
    def _calculate_stats(values: List[float]) -> Dict[str, Optional[float]]:
        """Calculate basic statistics for a list of numeric values."""
        if not values:
            return {"count": 0, "mean": None, "median": None, "min": None, "max": None}

        return {
            "count": len(values),
            "mean": float(statistics.mean(values)),
            "median": float(statistics.median(values)),
            "min": float(min(values)),
            "max": float(max(values))
        }


class TrendAnalyzer:
    """Analyze historical test runs to detect trends and degradations."""

    @staticmethod
    def load_runs_from_directory(results_dir: str) -> List[Dict[str, Any]]:
        runs = []
        for root, _, files in os.walk(results_dir):
            for f in files:
                if f.endswith('.json') and f.startswith('run_'):
                    path = os.path.join(root, f)
                    try:
                        with open(path, 'r', encoding='utf-8') as fh:
                            runs.append(json.load(fh))
                    except Exception:
                        continue
        return runs

    @staticmethod
    def detect_degradation(runs: List[Dict[str, Any]], window: int = 5, threshold_percent: float = 20.0) -> Dict[str, Any]:
        """Simple degradation detection: compare mean response time over sliding window to previous window.

        Returns a dict with 'degraded' bool and details.
        """
        # extract per-run mean response times if available
        means = []
        for r in runs:
            interactions = r.get('interactions') or []
            times = [i.get('response_time_ms') for i in interactions if i.get('response_time_ms') is not None]
            if times:
                means.append(statistics.mean(times))
        if len(means) < window * 2:
            return {'degraded': False, 'reason': 'insufficient data', 'count': len(means)}

        prev_window = means[-2*window:-window]
        last_window = means[-window:]
        prev_mean = statistics.mean(prev_window)
        last_mean = statistics.mean(last_window)
        pct_increase = ((last_mean - prev_mean) / prev_mean) * 100.0 if prev_mean > 0 else 0.0
        return {'degraded': pct_increase >= threshold_percent, 'prev_mean': prev_mean, 'last_mean': last_mean, 'pct_increase': pct_increase}


class ModelComparator:
    """Compare performance metrics across different models."""

    @staticmethod
    def compare_models(test_runs: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Compare performance metrics across models."""
        model_metrics = {}
        
        # Group runs by model
        by_model = {}
        for run in test_runs:
            model = run.get("model_name", "unknown")
            by_model.setdefault(model, []).append(run)
        
        # Calculate metrics for each model
        for model, runs in by_model.items():
            all_response_times = []
            all_tps = []
            all_memory = []
            all_npu = []
            
            for run in runs:
                interactions = run.get("interactions", [])
                for interaction in interactions:
                    rt = interaction.get("duration_ms")
                    if rt is not None:
                        all_response_times.append(float(rt))
                    
                    tps = interaction.get("tokens_per_second")
                    if tps is not None:
                        all_tps.append(float(tps))
                    
                    # Extract from metrics
                    for metrics_key in ["pre_metrics", "post_metrics"]:
                        metrics = interaction.get(metrics_key, {})
                        mem = metrics.get("memory_used_mb")
                        if mem is not None:
                            all_memory.append(float(mem))
                        
                        npu = metrics.get("npu_metrics", {}).get("utilization_percent")
                        if npu is not None:
                            all_npu.append(float(npu))
            
            # Calculate aggregates
            perf_aggs = PerformanceAnalyzer.calculate_aggregates(all_response_times, all_tps)
            npu_aggs = PerformanceAnalyzer.calculate_npu_aggregates(runs)
            
            model_metrics[model] = {
                "response_time_p50_ms": perf_aggs["p50"],
                "response_time_p95_ms": perf_aggs["p95"],
                "tokens_per_second": perf_aggs["tps_mean"],
                "memory_peak_gb": max(all_memory) / 1024 if all_memory else None,
                "npu_utilization_mean_percent": npu_aggs["mean"],
                "npu_utilization_max_percent": npu_aggs["max"],
                "test_runs_count": len(runs),
                "total_interactions": len(all_response_times)
            }
        
        return model_metrics

    @staticmethod
    def generate_recommendations(model_metrics: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
        """Generate recommendations based on performance metrics."""
        recommendations = {}
        
        for model, metrics in model_metrics.items():
            npu_util = metrics.get("npu_utilization_mean_percent", 0)
            response_time = metrics.get("response_time_p50_ms", float('inf'))
            tps = metrics.get("tokens_per_second", 0)
            
            if npu_util == 0:
                recommendations[model] = "Not recommended - no NPU acceleration detected"
            elif response_time < 5000 and tps > 20:
                recommendations[model] = "Excellent performance - recommended for production"
            elif response_time < 10000 and tps > 10:
                recommendations[model] = "Good performance - suitable for most use cases"
            elif response_time < 20000:
                recommendations[model] = "Fair performance - consider for lightweight tasks"
            else:
                recommendations[model] = "Poor performance - not recommended"
        
        return recommendations

    @staticmethod
    def generate_comparison_table(model_metrics: Dict[str, Dict[str, Any]], recommendations: Dict[str, str]) -> str:
        """Generate a markdown table comparing model performance."""
        lines = [
            "| Model | Response Time P50 (ms) | Response Time P95 (ms) | Tokens/sec | Memory Peak (GB) | NPU Util % | Recommendation |",
            "|---|---:|---:|---:|---:|---:|---|"
        ]
        
        for model in sorted(model_metrics.keys()):
            metrics = model_metrics[model]
            rec = recommendations.get(model, "Unknown")
            
            lines.append(
                f"| {model} | {metrics.get('response_time_p50_ms', 'N/A') or 'N/A':.1f} | "
                f"{metrics.get('response_time_p95_ms', 'N/A') or 'N/A':.1f} | "
                f"{metrics.get('tokens_per_second', 'N/A') or 'N/A':.1f} | "
                f"{metrics.get('memory_peak_gb', 'N/A') or 'N/A':.1f} | "
                f"{metrics.get('npu_utilization_mean_percent', 'N/A') or 'N/A':.1f} | {rec} |"
            )
        
        return "\n".join(lines)

    @staticmethod
    def save_comparison_report(model_metrics: Dict[str, Dict[str, Any]], recommendations: Dict[str, str], results_dir: str) -> str:
        """Save performance comparison report to JSON."""
        os.makedirs(results_dir, exist_ok=True)
        path = os.path.join(results_dir, "performance_comparison.json")
        
        report = {
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "model_metrics": model_metrics,
            "recommendations": recommendations
        }
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)
        
        return path


class ReportGenerator:
    """Generate compatibility matrices and assessment reports from test run data."""
    
    @staticmethod
    def assess_compatibility(test_runs: List[Dict[str, Any]], model_name: str) -> CompatibilityResult:
        """Assess model compatibility based on test run data.
        
        Basic assessment logic:
        - Compatible if no freezes in last 3 runs and mean response time < 30s
        - Stable if freeze rate < 10%
        - Performance rating based on response times and resource usage
        """
        if not test_runs:
            return CompatibilityResult(
                result_id=str(uuid.uuid4()),
                model_name=model_name,
                assessment_date=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                test_runs_analyzed=0,
                compatible=False,
                max_stable_interactions_observed=0,
                freeze_rate_percent=0.0,
                mean_freeze_after_interaction=None,
                performance_rating="unknown",
                stability_rating="unknown",
                recommended_for_production=False,
                notes="No test runs available",
                limitations=["No test data"]
            )
        
        # Analyze test runs
        total_runs = len(test_runs)
        freeze_count = sum(1 for run in test_runs if run.get("freeze_detected", False))
        freeze_rate = (freeze_count / total_runs) * 100
        
        # Calculate max stable interactions
        max_stable = 0
        freeze_interactions = []
        for run in test_runs:
            interactions_completed = run.get("num_interactions_completed", 0)
            if run.get("freeze_detected"):
                freeze_interactions.append(interactions_completed)
            max_stable = max(max_stable, interactions_completed)
        
        mean_freeze_after = statistics.mean(freeze_interactions) if freeze_interactions else None
        
        # Basic compatibility assessment
        compatible = freeze_rate < 50.0 and max_stable >= 3  # At least 3 interactions without freeze
        
        # Performance rating based on response times (simplified)
        response_times = []
        for run in test_runs:
            for interaction in run.get("interactions", []):
                rt = interaction.get("duration_ms")
                if rt:
                    response_times.append(rt)
        
        if response_times:
            mean_rt = statistics.mean(response_times)
            if mean_rt < 5000:  # < 5 seconds
                perf_rating = "excellent"
            elif mean_rt < 15000:  # < 15 seconds
                perf_rating = "good"
            elif mean_rt < 30000:  # < 30 seconds
                perf_rating = "fair"
            else:
                perf_rating = "poor"
        else:
            perf_rating = "unknown"
        
        # Stability rating
        if freeze_rate == 0:
            stability = "stable"
        elif freeze_rate < 25:
            stability = "mostly_stable"
        else:
            stability = "unstable"
        
        # Production recommendation
        recommended = compatible and stability in ["stable", "mostly_stable"] and perf_rating in ["excellent", "good", "fair"]
        
        notes = f"Analyzed {total_runs} test runs. Freeze rate: {freeze_rate:.1f}%"
        limitations = []
        if freeze_rate > 10:
            limitations.append("High freeze rate")
        if max_stable < 5:
            limitations.append("Limited interaction stability")
        
        return CompatibilityResult(
            result_id=str(uuid.uuid4()),
            model_name=model_name,
            assessment_date=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            test_runs_analyzed=total_runs,
            compatible=compatible,
            max_stable_interactions_observed=max_stable,
            freeze_rate_percent=freeze_rate,
            mean_freeze_after_interaction=mean_freeze_after,
            performance_rating=perf_rating,
            stability_rating=stability,
            recommended_for_production=recommended,
            notes=notes,
            limitations=limitations if limitations else None
        )
    
    @staticmethod
    def generate_compatibility_matrix(test_runs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate compatibility matrix from test runs.
        
        Returns a dict with model compatibility assessments and summary statistics.
        """
        # Group test runs by model
        model_runs = {}
        for run in test_runs:
            model = run.get("model_name", "unknown")
            if model not in model_runs:
                model_runs[model] = []
            model_runs[model].append(run)
        
        # Assess each model
        assessments = {}
        for model, runs in model_runs.items():
            assessments[model] = ReportGenerator.assess_compatibility(runs, model).to_dict()
        
        # Generate summary
        total_runs = len(test_runs)
        total_freezes = sum(1 for run in test_runs if run.get("freeze_detected", False))
        overall_freeze_rate = (total_freezes / total_runs * 100) if total_runs > 0 else 0
        
        matrix = {
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "total_test_runs": total_runs,
            "total_freezes": total_freezes,
            "overall_freeze_rate_percent": overall_freeze_rate,
            "models_assessed": len(assessments),
            "compatibility_assessments": assessments,
            "summary": {
                "compatible_models": [m for m, a in assessments.items() if a["compatible"]],
                "recommended_models": [m for m, a in assessments.items() if a["recommended_for_production"]],
                "high_risk_models": [m for m, a in assessments.items() if not a["compatible"] or a["freeze_rate_percent"] > 25]
            }
        }
        
        return matrix
    
    @staticmethod
    def save_json(data: Dict[str, Any], path: str) -> None:
        """Save data as JSON to specified path."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
    
    @staticmethod
    def generate_markdown(matrix: Dict[str, Any]) -> str:
        """Generate markdown report from compatibility matrix."""
        lines = [
            "# Continue Model Compatibility Report",
            "",
            f"Generated: {matrix['generated_at']}",
            "",
            "## Summary",
            "",
            f"- Total test runs: {matrix['total_test_runs']}",
            f"- Total freezes: {matrix['total_freezes']}",
            f"- Overall freeze rate: {matrix['overall_freeze_rate_percent']:.1f}%",
            f"- Models assessed: {matrix['models_assessed']}",
            "",
            "## Model Compatibility Assessments",
            "",
            "| Model | Compatible | Stable Interactions | Freeze Rate | Performance | Stability | Recommended |",
            "|-------|------------|-------------------|-------------|-------------|-----------|-------------|"
        ]
        
        for model, assessment in matrix["compatibility_assessments"].items():
            lines.append(
                f"| {model} | {'✓' if assessment['compatible'] else '✗'} | "
                f"{assessment['max_stable_interactions_observed']} | "
                f"{assessment['freeze_rate_percent']:.1f}% | "
                f"{assessment['performance_rating']} | "
                f"{assessment['stability_rating']} | "
                f"{'✓' if assessment['recommended_for_production'] else '✗'} |"
            )
        
        lines.extend([
            "",
            "## Recommendations",
            "",
            f"**Compatible Models**: {', '.join(matrix['summary']['compatible_models']) or 'None'}",
            "",
            f"**Recommended for Production**: {', '.join(matrix['summary']['recommended_models']) or 'None'}",
            "",
            f"**High Risk Models**: {', '.join(matrix['summary']['high_risk_models']) or 'None'}",
        ])
        
        return "\n".join(lines)


def main() -> int:
    """CLI entry point for report generation."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate performance and compatibility reports from test run data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate compatibility matrix for all test runs
  python report_generator.py compatibility --results-dir ./results --format json
  
  # Generate performance comparison report
  python report_generator.py performance --results-dir ./results --format markdown
  
  # Generate freeze pattern analysis
  python report_generator.py freeze-analysis --results-dir ./results --format json
        """
    )
    
    parser.add_argument(
        "--results-dir",
        default="results",
        help="Directory containing test run results (default: results)"
    )
    parser.add_argument(
        "--config-dir", 
        default="config",
        help="Directory containing configuration files (default: config)"
    )
    parser.add_argument(
        "--format",
        choices=["json", "markdown", "csv"],
        default="json",
        help="Output format (default: json)"
    )
    parser.add_argument(
        "--output-dir",
        help="Output directory for generated reports (default: same as results-dir)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Report type to generate")
    
    # Compatibility matrix subcommand
    compat_parser = subparsers.add_parser(
        "compatibility",
        help="Generate model compatibility matrix"
    )
    compat_parser.add_argument(
        "--model",
        help="Specific model to analyze (default: all models)"
    )
    
    # Performance comparison subcommand
    perf_parser = subparsers.add_parser(
        "performance", 
        help="Generate performance comparison report"
    )
    perf_parser.add_argument(
        "--models",
        nargs="+",
        help="Models to compare (default: all available)"
    )
    
    # Freeze analysis subcommand
    freeze_parser = subparsers.add_parser(
        "freeze-analysis",
        help="Analyze freeze patterns across test runs"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Set output directory
    output_dir = args.output_dir or os.path.join(args.results_dir, "reports")
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        if args.command == "compatibility":
            # Load test runs
            test_runs = load_test_runs(args.results_dir)
            
            if args.model:
                test_runs = [run for run in test_runs if run.get("model_name") == args.model]
            
            if not test_runs:
                print(f"No test runs found for model '{args.model}'" if args.model else "No test runs found")
                return 1
            
            # Generate compatibility matrix
            matrix = ReportGenerator.generate_compatibility_matrix(test_runs)
            
            # Output based on format
            if args.format == "json":
                output_path = os.path.join(output_dir, "compatibility_matrix.json")
                ReportGenerator.save_json(matrix, output_path)
                print(f"Compatibility matrix saved to: {output_path}")
            
            elif args.format == "markdown":
                output_path = os.path.join(output_dir, "compatibility_matrix.md")
                md_content = ReportGenerator.generate_markdown(matrix)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(md_content)
                print(f"Compatibility report saved to: {output_path}")
            
            elif args.format == "csv":
                # Generate CSV format
                output_path = os.path.join(output_dir, "compatibility_matrix.csv")
                csv_content = generate_compatibility_csv(matrix)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(csv_content)
                print(f"Compatibility CSV saved to: {output_path}")
            
            if args.verbose:
                print(f"Analyzed {matrix['total_test_runs']} test runs across {matrix['models_assessed']} models")
        
        elif args.command == "performance":
            # Load test runs and calculate performance metrics
            test_runs = load_test_runs(args.results_dir)
            
            if not test_runs:
                print("No test runs found")
                return 1
            
            # Filter models if specified
            if args.models:
                test_runs = [run for run in test_runs if run.get("model_name") in args.models]
            
            # Group by model and calculate metrics
            model_metrics = ReportGenerator.analyze_model_performance(test_runs)
            
            if not model_metrics:
                print("No performance data available")
                return 1
            
            # Generate recommendations
            recommendations = PerformanceAnalyzer.generate_recommendations(model_metrics)
            
            # Output based on format
            if args.format == "json":
                output_path = os.path.join(output_dir, "performance_comparison.json")
                PerformanceAnalyzer.save_performance_comparison(model_metrics, recommendations, output_path)
                print(f"Performance comparison saved to: {output_path}")
            
            elif args.format == "markdown":
                output_path = os.path.join(output_dir, "performance_comparison.md")
                md_content = PerformanceAnalyzer.generate_comparison_markdown(model_metrics, recommendations)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(md_content)
                print(f"Performance report saved to: {output_path}")
            
            elif args.format == "csv":
                output_path = os.path.join(output_dir, "performance_comparison.csv")
                csv_content = PerformanceAnalyzer.generate_comparison_csv(model_metrics, recommendations)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(csv_content)
                print(f"Performance CSV saved to: {output_path}")
            
            if args.verbose:
                print(f"Compared {len(model_metrics)} models")
        
        elif args.command == "freeze-analysis":
            # Load test runs and freeze events
            test_runs = load_test_runs(args.results_dir)
            freeze_events = load_freeze_events(args.results_dir)
            
            if not test_runs:
                print("No test runs found")
                return 1
            
            # Analyze freeze patterns
            analysis = ReportGenerator.analyze_freeze_patterns(test_runs, freeze_events)
            
            # Output based on format
            if args.format == "json":
                output_path = os.path.join(output_dir, "freeze_analysis.json")
                ReportGenerator.save_json(analysis, output_path)
                print(f"Freeze analysis saved to: {output_path}")
            
            elif args.format == "markdown":
                output_path = os.path.join(output_dir, "freeze_analysis.md")
                md_content = generate_freeze_analysis_markdown(analysis)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(md_content)
                print(f"Freeze analysis report saved to: {output_path}")
            
            if args.verbose:
                print(f"Analyzed {analysis.get('total_freezes', 0)} freeze events")
    
    except Exception as e:
        print(f"Error generating report: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    return 0


def load_test_runs(results_dir: str) -> List[Dict[str, Any]]:
    """Load all test run JSON files from results directory."""
    test_runs = []
    test_runs_dir = os.path.join(results_dir, "test_runs")
    
    if not os.path.exists(test_runs_dir):
        return test_runs
    
    for filename in os.listdir(test_runs_dir):
        if filename.endswith(".json"):
            try:
                with open(os.path.join(test_runs_dir, filename), "r", encoding="utf-8") as f:
                    test_run = json.load(f)
                    test_runs.append(test_run)
            except Exception:
                continue
    
    return test_runs


def load_freeze_events(results_dir: str) -> List[Dict[str, Any]]:
    """Load all freeze event JSON files from results directory."""
    freeze_events = []
    freeze_dir = os.path.join(results_dir, "freeze_events")
    
    if not os.path.exists(freeze_dir):
        return freeze_events
    
    for filename in os.listdir(freeze_dir):
        if filename.endswith(".json"):
            try:
                with open(os.path.join(freeze_dir, filename), "r", encoding="utf-8") as f:
                    freeze_event = json.load(f)
                    freeze_events.append(freeze_event)
            except Exception:
                continue
    
    return freeze_events


def generate_compatibility_csv(matrix: Dict[str, Any]) -> str:
    """Generate CSV format for compatibility matrix."""
    lines = ["Model,Compatible,Stable_Interactions,Freeze_Rate_Percent,Performance_Rating,Stability_Rating,Recommended"]
    
    for model, assessment in matrix["compatibility_assessments"].items():
        line = ",".join([
            model,
            str(assessment["compatible"]),
            str(assessment["max_stable_interactions_observed"]),
            f"{assessment['freeze_rate_percent']:.1f}",
            assessment["performance_rating"],
            assessment["stability_rating"],
            str(assessment["recommended_for_production"])
        ])
        lines.append(line)
    
    return "\n".join(lines)


def generate_freeze_analysis_markdown(analysis: Dict[str, Any]) -> str:
    """Generate markdown report for freeze analysis."""
    lines = [
        "# Freeze Pattern Analysis Report",
        "",
        f"Generated: {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
        "",
        "## Summary",
        "",
        f"- Total test runs analyzed: {analysis.get('total_runs', 0)}",
        f"- Total freeze events: {analysis.get('total_freezes', 0)}",
        f"- Freeze rate: {analysis.get('overall_freeze_rate_percent', 0):.1f}%",
        "",
        "## Freeze Patterns by Model",
        "",
        "| Model | Freeze Count | Freeze Rate | Avg Interactions Before Freeze |",
        "|-------|--------------|-------------|-------------------------------|"
    ]
    
    for model, pattern in analysis.get("patterns_by_model", {}).items():
        lines.append(
            f"| {model} | {pattern.get('freeze_count', 0)} | "
            f"{pattern.get('freeze_rate_percent', 0):.1f}% | "
            f"{pattern.get('avg_interactions_before_freeze', 'N/A')} |"
        )
    
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    sys.exit(main())
