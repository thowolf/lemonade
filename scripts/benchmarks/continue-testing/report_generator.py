"""Report generation: performance metrics, compatibility analysis, and trend detection.

This module provides tools to compute aggregated performance metrics, generate
compatibility matrices (JSON/Markdown/CSV), and run simple trend analysis
across historical test runs.
"""
from __future__ import annotations

import argparse
import csv
import dataclasses
import datetime
import json
import os
import statistics
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .utils import sanitize_path_for_logging


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
    def save_json(path: str, data: Any) -> None:
        """Save data to JSON file."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

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

    @staticmethod
    def generate_recommendations(model_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate recommendations based on performance analysis."""
        recommendations = {}
        
        for model, metrics in model_metrics.items():
            recs = []
            
            # Performance recommendations
            rt_mean = metrics.get("response_time_ms", {}).get("mean")
            if rt_mean and rt_mean > 30000:  # > 30 seconds
                recs.append("Consider model optimization or hardware acceleration")
            elif rt_mean and rt_mean > 15000:  # > 15 seconds
                recs.append("Response time is acceptable but could be improved")
            
            # NPU utilization recommendations
            npu_mean = metrics.get("npu_utilization_percent", {}).get("mean")
            if npu_mean is None:
                recs.append("NPU monitoring not available - check driver installation")
            elif npu_mean < 10:
                recs.append("Low NPU utilization - verify model compatibility")
            elif npu_mean > 80:
                recs.append("High NPU utilization - monitor for thermal issues")
            
            # Freeze rate recommendations
            freeze_rate = metrics.get("freeze_rate_percent", 0)
            if freeze_rate > 50:
                recs.append("High freeze rate - investigate stability issues")
            elif freeze_rate > 10:
                recs.append("Moderate freeze rate - monitor for patterns")
            
            recommendations[model] = recs
        
        return recommendations

    @staticmethod
    def save_performance_comparison(model_metrics: Dict[str, Any], recommendations: Dict[str, Any], output_path: str) -> None:
        """Save performance comparison to JSON file."""
        data = {
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "model_metrics": model_metrics,
            "recommendations": recommendations
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def generate_comparison_markdown(model_metrics: Dict[str, Any], recommendations: Dict[str, Any]) -> str:
        """Generate markdown report for performance comparison."""
        lines = [
            "# Performance Comparison Report",
            "",
            f"Generated: {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
            "",
            "| Model | Avg Response Time | Tokens/sec | NPU Util % | Freeze Rate |",
            "|-------|------------------|------------|------------|-------------|"
        ]
        
        for model, metrics in sorted(model_metrics.items()):
            rt_mean = metrics.get("response_time_ms", {}).get("mean")
            tps_mean = metrics.get("tokens_per_second", {}).get("mean")
            npu_mean = metrics.get("npu_utilization_percent", {}).get("mean")
            freeze_rate = metrics.get("freeze_rate_percent", 0)
            
            rt_str = f"{rt_mean:.1f}ms" if rt_mean else "N/A"
            tps_str = f"{tps_mean:.1f}" if tps_mean else "N/A"
            npu_str = f"{npu_mean:.1f}" if npu_mean else "N/A"
            freeze_str = f"{freeze_rate:.1f}%"
            
            lines.append(f"| {model} | {rt_str} | {tps_str} | {npu_str} | {freeze_str} |")
        
        lines.append("")
        lines.append("## Recommendations")
        lines.append("")
        
        for model, recs in recommendations.items():
            if recs:
                lines.append(f"### {model}")
                for rec in recs:
                    lines.append(f"- {rec}")
                lines.append("")
        
        return "\n".join(lines)

    @staticmethod
    def generate_comparison_csv(model_metrics: Dict[str, Any], recommendations: Dict[str, Any]) -> str:
        """Generate CSV report for performance comparison."""
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(["Model", "Avg Response Time (ms)", "Tokens/sec", "NPU Util %", "Freeze Rate %", "Recommendations"])
        
        for model, metrics in sorted(model_metrics.items()):
            rt_mean = metrics.get("response_time_ms", {}).get("mean") or ""
            tps_mean = metrics.get("tokens_per_second", {}).get("mean") or ""
            npu_mean = metrics.get("npu_utilization_percent", {}).get("mean") or ""
            freeze_rate = metrics.get("freeze_rate_percent", 0)
            recs = "; ".join(recommendations.get(model, []))
            
            writer.writerow([model, rt_mean, tps_mean, npu_mean, freeze_rate, recs])
        
        return output.getvalue()


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
    def save_json(data: Any, output_path: str) -> None:
        """Save data to JSON file."""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

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
                "freeze_rate_percent": (model_stats["freeze_count"] / len(runs)) * 100 if runs else 0,
                "freeze_count": model_stats["freeze_count"]
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

    @staticmethod
    def analyze_historical_runs(runs: List[Dict[str, Any]], days_back: int = 30) -> Dict[str, Any]:
        """Analyze historical test runs to identify trends and patterns."""
        if not runs:
            return {"error": "No test runs found"}

        # Filter runs by date
        cutoff_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days_back)
        recent_runs = []
        for run in runs:
            try:
                run_date = None
                if 'start_time' in run:
                    if isinstance(run['start_time'], str):
                        run_date = datetime.datetime.fromisoformat(run['start_time'].replace('Z', '+00:00'))
                    else:
                        run_date = run['start_time']
                elif 'timestamp' in run:
                    run_date = datetime.datetime.fromisoformat(run['timestamp'].replace('Z', '+00:00'))

                if run_date and run_date >= cutoff_date:
                    recent_runs.append(run)
            except Exception:
                continue

        if not recent_runs:
            return {"error": f"No runs found in the last {days_back} days"}

        # Group by model
        by_model = {}
        for run in recent_runs:
            model = run.get("model_name", "unknown")
            by_model.setdefault(model, []).append(run)

        analysis = {
            "total_runs_analyzed": len(recent_runs),
            "date_range_days": days_back,
            "models_analyzed": len(by_model),
            "model_trends": {},
            "overall_trends": {}
        }

        # Analyze each model
        for model, model_runs in by_model.items():
            analysis["model_trends"][model] = TrendAnalyzer._analyze_model_trends(model_runs)

        # Overall trends
        analysis["overall_trends"] = TrendAnalyzer._analyze_overall_trends(recent_runs)

        return analysis

    @staticmethod
    def _analyze_model_trends(model_runs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trends for a specific model."""
        # Sort by date
        sorted_runs = sorted(model_runs, key=lambda x: x.get('start_time', ''))

        # Extract metrics over time
        timestamps = []
        response_times = []
        freeze_rates = []
        npu_utils = []

        for run in sorted_runs:
            try:
                # Timestamp
                if 'start_time' in run and isinstance(run['start_time'], str):
                    ts = datetime.datetime.fromisoformat(run['start_time'].replace('Z', '+00:00'))
                    timestamps.append(ts)

                # Response time (simplified - would need to aggregate interactions)
                interactions = run.get('interactions', [])
                if interactions:
                    rt = statistics.mean([i.get('duration_ms', 0) for i in interactions if i.get('duration_ms')])
                    response_times.append(rt)

                # Freeze rate
                total_interactions = len(interactions)
                freeze_count = sum(1 for i in interactions if i.get('freeze_detected'))
                if total_interactions > 0:
                    freeze_rates.append((freeze_count / total_interactions) * 100)

                # NPU utilization (simplified)
                for interaction in interactions:
                    pre_metrics = interaction.get('pre_metrics', {})
                    npu_data = pre_metrics.get('npu_metrics', {})
                    util = npu_data.get('utilization_percent')
                    if util is not None:
                        npu_utils.append(util)

            except Exception:
                continue

        return {
            "run_count": len(sorted_runs),
            "response_time_trend": TrendAnalyzer._detect_trend(response_times),
            "freeze_rate_trend": TrendAnalyzer._detect_trend(freeze_rates),
            "npu_utilization_trend": TrendAnalyzer._detect_trend(npu_utils),
            "avg_response_time": statistics.mean(response_times) if response_times else None,
            "avg_freeze_rate": statistics.mean(freeze_rates) if freeze_rates else None,
            "avg_npu_utilization": statistics.mean(npu_utils) if npu_utils else None
        }

    @staticmethod
    def _analyze_overall_trends(all_runs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze overall trends across all models."""
        # Group by day
        daily_stats = {}
        for run in all_runs:
            try:
                if 'start_time' in run and isinstance(run['start_time'], str):
                    date = datetime.datetime.fromisoformat(run['start_time'].replace('Z', '+00:00')).date()
                    daily_stats.setdefault(date, []).append(run)
            except Exception:
                continue

        # Calculate daily aggregates
        daily_success_rates = []
        daily_response_times = []

        for date, runs in daily_stats.items():
            total_runs = len(runs)
            successful_runs = sum(1 for r in runs if r.get('status') == 'completed')
            success_rate = (successful_runs / total_runs) * 100 if total_runs > 0 else 0
            daily_success_rates.append(success_rate)

            # Average response time across all runs that day
            day_response_times = []
            for run in runs:
                interactions = run.get('interactions', [])
                for interaction in interactions:
                    rt = interaction.get('duration_ms')
                    if rt:
                        day_response_times.append(rt)
            if day_response_times:
                daily_response_times.append(statistics.mean(day_response_times))

        return {
            "daily_success_rate_trend": TrendAnalyzer._detect_trend(daily_success_rates),
            "daily_response_time_trend": TrendAnalyzer._detect_trend(daily_response_times),
            "avg_daily_success_rate": statistics.mean(daily_success_rates) if daily_success_rates else None,
            "avg_daily_response_time": statistics.mean(daily_response_times) if daily_response_times else None
        }

    @staticmethod
    def detect_improvements(runs: List[Dict[str, Any]], window: int = 5, threshold_percent: float = 15.0) -> Dict[str, Any]:
        """Detect performance improvements by comparing recent runs to historical baseline."""
        if len(runs) < window * 2:
            return {"improved": False, "message": "Insufficient data for improvement detection"}

        # Sort runs by date
        sorted_runs = sorted(runs, key=lambda x: x.get('start_time', ''))

        # Calculate baseline (older runs) and recent
        baseline_runs = sorted_runs[:-window]
        recent_runs = sorted_runs[-window:]

        if not baseline_runs:
            return {"improved": False, "message": "No baseline data available"}

        # Calculate metrics
        baseline_metrics = TrendAnalyzer._calculate_run_metrics(baseline_runs)
        recent_metrics = TrendAnalyzer._calculate_run_metrics(recent_runs)

        # Check for improvements (positive changes)
        improvement_detected = False
        improvement_details = []

        # Lower response time = better
        baseline_rt = baseline_metrics.get('avg_response_time')
        recent_rt = recent_metrics.get('avg_response_time')
        if baseline_rt and recent_rt and recent_rt < baseline_rt:
            improvement = ((baseline_rt - recent_rt) / baseline_rt) * 100
            if improvement > threshold_percent:
                improvement_detected = True
                improvement_details.append(f"response time improved by {improvement:.1f}%")

        # Lower freeze rate = better
        baseline_fr = baseline_metrics.get('freeze_rate')
        recent_fr = recent_metrics.get('freeze_rate')
        if baseline_fr and recent_fr and recent_fr < baseline_fr:
            improvement = ((baseline_fr - recent_fr) / baseline_fr) * 100
            if improvement > threshold_percent:
                improvement_detected = True
                improvement_details.append(f"freeze rate improved by {improvement:.1f}%")

        # Higher NPU utilization = better
        baseline_npu = baseline_metrics.get('npu_utilization')
        recent_npu = recent_metrics.get('npu_utilization')
        if baseline_npu and recent_npu and recent_npu > baseline_npu:
            improvement = ((recent_npu - baseline_npu) / baseline_npu) * 100
            if improvement > threshold_percent:
                improvement_detected = True
                improvement_details.append(f"NPU utilization improved by {improvement:.1f}%")

        return {
            "improved": improvement_detected,
            "details": improvement_details,
            "baseline_period_runs": len(baseline_runs),
            "recent_period_runs": len(recent_runs),
            "baseline_metrics": baseline_metrics,
            "recent_metrics": recent_metrics
        }

    @staticmethod
    def _calculate_run_metrics(runs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate average metrics across a set of runs."""
        response_times = []
        freeze_rates = []
        npu_utils = []

        for run in runs:
            interactions = run.get('interactions', [])
            if interactions:
                # Response times
                rts = [i.get('duration_ms') for i in interactions if i.get('duration_ms')]
                if rts:
                    response_times.append(statistics.mean(rts))

                # Freeze rate
                total_interactions = len(interactions)
                freeze_count = sum(1 for i in interactions if i.get('freeze_detected'))
                if total_interactions > 0:
                    freeze_rates.append((freeze_count / total_interactions) * 100)

                # NPU utilization
                for interaction in interactions:
                    pre_metrics = interaction.get('pre_metrics', {})
                    npu_data = pre_metrics.get('npu_metrics', {})
                    util = npu_data.get('utilization_percent')
                    if util is not None:
                        npu_utils.append(util)

        return {
            "avg_response_time": statistics.mean(response_times) if response_times else None,
            "freeze_rate": statistics.mean(freeze_rates) if freeze_rates else None,
            "npu_utilization": statistics.mean(npu_utils) if npu_utils else None
        }

    @staticmethod
    def _detect_trend(values: List[float], min_points: int = 3) -> Dict[str, Any]:
        """Detect trend direction in a series of values."""
        if len(values) < min_points:
            return {"trend": "insufficient_data", "direction": None, "magnitude": None}

        if len(values) < 2:
            return {"trend": "stable", "direction": "stable", "magnitude": 0}

        # Simple linear trend detection
        try:
            # Calculate slope using simple linear regression
            n = len(values)
            x = list(range(n))
            x_mean = sum(x) / n
            y_mean = sum(values) / n

            numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, values))
            denominator = sum((xi - x_mean) ** 2 for xi in x)

            if denominator == 0:
                slope = 0
            else:
                slope = numerator / denominator

            # Determine trend
            if abs(slope) < 0.01:  # Very small slope = stable
                trend = "stable"
                direction = "stable"
            elif slope > 0:
                trend = "increasing"
                direction = "worse" if values[0] < values[-1] else "better"  # Context dependent
            else:
                trend = "decreasing"
                direction = "better" if values[0] > values[-1] else "worse"  # Context dependent

            # Magnitude as percentage change
            if values[0] != 0:
                magnitude = ((values[-1] - values[0]) / values[0]) * 100
            else:
                magnitude = 0

            return {
                "trend": trend,
                "direction": direction,
                "magnitude": magnitude,
                "slope": slope,
                "data_points": len(values)
            }

        except Exception:
            return {"trend": "error", "direction": None, "magnitude": None}

    @staticmethod
    def generate_trend_report_markdown(trend_analysis: Dict[str, Any], degradation_results: Dict[str, Any], improvement_results: Dict[str, Any]) -> str:
        """Generate markdown report for trend analysis."""
        lines = [
            "# Trend Analysis Report",
            "",
            f"Generated: {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
            "",
            "## Summary",
            "",
            f"- Total runs analyzed: {trend_analysis.get('total_runs_analyzed', 0)}",
            f"- Date range: {trend_analysis.get('date_range_days', 0)} days",
            f"- Models analyzed: {trend_analysis.get('models_analyzed', 0)}",
            f"- Degradation alerts: {len(degradation_results)}",
            f"- Improvement alerts: {len(improvement_results)}",
            ""
        ]

        # Overall trends
        overall = trend_analysis.get("overall_trends", {})
        lines.extend([
            "## Overall Trends",
            "",
            "### Success Rate Trend",
            f"- **Trend**: {overall.get('daily_success_rate_trend', {}).get('trend', 'N/A')}",
            f"- **Direction**: {overall.get('daily_success_rate_trend', {}).get('direction', 'N/A')}",
            f"- **Average**: {overall.get('avg_daily_success_rate', 'N/A'):.1f}%" if overall.get('avg_daily_success_rate') else "- **Average**: N/A",
            "",
            "### Response Time Trend",
            f"- **Trend**: {overall.get('daily_response_time_trend', {}).get('trend', 'N/A')}",
            f"- **Direction**: {overall.get('daily_response_time_trend', {}).get('direction', 'N/A')}",
            f"- **Average**: {overall.get('avg_daily_response_time', 'N/A'):.1f}ms" if overall.get('avg_daily_response_time') else "- **Average**: N/A",
            ""
        ])

        # Model-specific trends
        lines.extend([
            "## Model-Specific Trends",
            "",
            "| Model | Run Count | Response Time Trend | Freeze Rate Trend | NPU Utilization Trend | Avg Response Time | Avg Freeze Rate | Avg NPU Util |",
            "|-------|-----------|-------------------|------------------|----------------------|------------------|----------------|-------------|"
        ])

        for model, trends in trend_analysis.get("model_trends", {}).items():
            rt_trend = trends.get("response_time_trend", {})
            fr_trend = trends.get("freeze_rate_trend", {})
            npu_trend = trends.get("npu_utilization_trend", {})

            lines.append(
                f"| {model} | {trends.get('run_count', 0)} | "
                f"{rt_trend.get('trend', 'N/A')} | "
                f"{fr_trend.get('trend', 'N/A')} | "
                f"{npu_trend.get('trend', 'N/A')} | "
                f"{trends.get('avg_response_time', 'N/A') or 'N/A':.1f}ms | "
                f"{trends.get('avg_freeze_rate', 'N/A') or 'N/A':.1f}% | "
                f"{trends.get('avg_npu_utilization', 'N/A') or 'N/A':.1f}% |"
            )

        lines.append("")

        # Degradation alerts
        if degradation_results:
            lines.extend([
                "## ⚠️ Degradation Alerts",
                "",
                "The following models show signs of performance degradation:",
                ""
            ])

            for model, degradation in degradation_results.items():
                lines.extend([
                    f"### {model}",
                    f"- **Increase**: {degradation.get('pct_increase', 0):.1f}%",
                    f"- **Previous mean**: {degradation.get('prev_mean', 0):.1f}ms",
                    f"- **Current mean**: {degradation.get('last_mean', 0):.1f}ms",
                    ""
                ])

        # Improvement alerts
        if improvement_results:
            lines.extend([
                "## ✅ Improvement Alerts",
                "",
                "The following models show performance improvements:",
                ""
            ])

            for model, improvement in improvement_results.items():
                lines.extend([
                    f"### {model}",
                    "Improvements detected:",
                ])

                for detail in improvement.get("details", []):
                    lines.append(f"- {detail}")

                lines.append("")

        # Recommendations
        lines.extend([
            "## Recommendations",
            "",
            "Based on the trend analysis:",
            "",
            "- Monitor models with degradation alerts closely",
            "- Investigate root causes for performance declines",
            "- Consider model retraining or hardware optimization",
            "- Review system logs for correlated events",
            "- Schedule regular trend analysis to catch issues early",
            ""
        ])

        return "\n".join(lines)


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

def load_test_runs(results_dir: str) -> List[Dict[str, Any]]:
    """Load test run data from results directory."""
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
    """Load freeze event data from results directory."""
    freeze_events = []
    freeze_dir = os.path.join(results_dir, "freeze_events")
    
    if not os.path.exists(freeze_dir):
        return freeze_events
    
    for filename in os.listdir(freeze_dir):
        if filename.endswith(".json"):
            try:
                with open(os.path.join(freeze_dir, filename), "r", encoding="utf-8") as f:
                    event = json.load(f)
                    freeze_events.append(event)
            except Exception:
                continue
    
    return freeze_events

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

def main() -> int:
    """Main CLI entry point."""
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
    
    # Compatibility subcommand
    compat_parser = subparsers.add_parser("compatibility", help="Generate model compatibility matrix")
    compat_parser.add_argument("--models", nargs="*", help="Specific models to analyze")
    
    # Performance subcommand
    perf_parser = subparsers.add_parser("performance", help="Generate performance comparison report")
    perf_parser.add_argument("--models", nargs="*", help="Specific models to analyze")
    
    # Freeze analysis subcommand
    freeze_parser = subparsers.add_parser("freeze-analysis", help="Analyze freeze patterns across test runs")
    
    # Trend analysis subcommand
    trend_parser = subparsers.add_parser("trends", help="Analyze historical trends and detect degradation/improvement")
    trend_parser.add_argument("--days-back", type=int, default=30, help="Number of days to analyze (default: 30)")
    trend_parser.add_argument("--models", nargs="*", help="Specific models to analyze")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Set output directory
    output_dir = args.output_dir or args.results_dir
    
    try:
        if args.command == "compatibility":
            # Load test runs
            test_runs = load_test_runs(args.results_dir)
            
            if not test_runs:
                print("No test runs found")
                return 1
            
            # Filter models if specified
            if hasattr(args, 'models') and args.models:
                test_runs = [run for run in test_runs if run.get("model_name") in args.models]
            
            # Generate compatibility matrix
            matrix = ReportGenerator.generate_compatibility_matrix(test_runs)
            
            if not matrix:
                print("No compatibility data available")
                return 1
            
            # Output based on format
            if args.format == "json":
                output_path = os.path.join(output_dir, "compatibility_matrix.json")
                ReportGenerator.save_json(matrix, output_path)
                print(f"Compatibility matrix saved to: {sanitize_path_for_logging(output_path)}")
            
            elif args.format == "markdown":
                output_path = os.path.join(output_dir, "compatibility_matrix.md")
                md_content = ReportGenerator.generate_markdown(matrix)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(md_content)
                print(f"Compatibility report saved to: {sanitize_path_for_logging(output_path)}")
            
            elif args.format == "csv":
                output_path = os.path.join(output_dir, "compatibility_matrix.csv")
                csv_content = ReportGenerator.generate_csv(matrix)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(csv_content)
                print(f"Compatibility CSV saved to: {sanitize_path_for_logging(output_path)}")
            
            if args.verbose:
                print(f"Analyzed {matrix['total_test_runs']} test runs across {matrix['models_assessed']} models")
        
        elif args.command == "performance":
            # Load test runs and calculate performance metrics
            test_runs = load_test_runs(args.results_dir)
            
            if not test_runs:
                print("No test runs found")
                return 1
            
            # Filter models if specified
            if hasattr(args, 'models') and args.models:
                test_runs = [run for run in test_runs if run.get("model_name") in args.models]
            
            # Group by model and calculate metrics
            model_metrics = ReportGenerator.analyze_model_performance(test_runs)
            
            if not model_metrics:
                print("No performance data available")
                return 1
            
            # Generate recommendations
            recommendations = PerformanceAnalyzer.generate_recommendations(model_metrics.get("performance_by_model", {}))
            
            # Output based on format
            if args.format == "json":
                output_path = os.path.join(output_dir, "performance_comparison.json")
                PerformanceAnalyzer.save_performance_comparison(model_metrics, recommendations, output_path)
                print(f"Performance comparison saved to: {sanitize_path_for_logging(output_path)}")
            
            elif args.format == "markdown":
                output_path = os.path.join(output_dir, "performance_comparison.md")
                md_content = PerformanceAnalyzer.generate_comparison_markdown(model_metrics.get("performance_by_model", {}), recommendations)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(md_content)
                print(f"Performance report saved to: {sanitize_path_for_logging(output_path)}")
            
            elif args.format == "csv":
                output_path = os.path.join(output_dir, "performance_comparison.csv")
                csv_content = PerformanceAnalyzer.generate_comparison_csv(model_metrics.get("performance_by_model", {}), recommendations)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(csv_content)
                print(f"Performance CSV saved to: {sanitize_path_for_logging(output_path)}")
            
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
            analysis = ReportGenerator.analyze_freeze_patterns(test_runs)
            
            # Output based on format
            if args.format == "json":
                output_path = os.path.join(output_dir, "freeze_analysis.json")
                ReportGenerator.save_json(analysis, output_path)
                print(f"Freeze analysis saved to: {sanitize_path_for_logging(output_path)}")
            
            elif args.format == "markdown":
                output_path = os.path.join(output_dir, "freeze_analysis.md")
                md_content = generate_freeze_analysis_markdown(analysis)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(md_content)
                print(f"Freeze analysis report saved to: {sanitize_path_for_logging(output_path)}")
            
            elif args.format == "csv":
                output_path = os.path.join(output_dir, "freeze_analysis.csv")
                # Generate CSV for freeze analysis
                csv_content = f"Pattern,{analysis.get('pattern', 'N/A')}\nMessage,{analysis.get('message', 'N/A')}\nRecommendation,{analysis.get('recommendation', 'N/A')}\nTotal Freezes,{analysis.get('total_freezes', 0)}\nModels Affected,{len(analysis.get('models_affected', []))}\n"
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(csv_content)
                print(f"Freeze analysis CSV saved to: {sanitize_path_for_logging(output_path)}")
            
            if args.verbose:
                print(f"Analyzed freeze patterns across {len(test_runs)} test runs")
        
        elif args.command == "trends":
            # Load test runs
            test_runs = load_test_runs(args.results_dir)
            
            if not test_runs:
                print("No test runs found")
                return 1
            
            # Filter models if specified
            if hasattr(args, 'models') and args.models:
                test_runs = [run for run in test_runs if run.get("model_name") in args.models]
            
            # Analyze historical trends
            trend_analysis = TrendAnalyzer.analyze_historical_runs(test_runs, days_back=args.days_back)
            
            if "error" in trend_analysis:
                print(f"Trend analysis failed: {trend_analysis['error']}")
                return 1
            
            # Check for degradation and improvements
            degradation_results = {}
            improvement_results = {}
            
            for model in trend_analysis.get("model_trends", {}):
                model_runs = [run for run in test_runs if run.get("model_name") == model]
                if len(model_runs) >= 10:  # Need minimum data for meaningful analysis
                    degradation = TrendAnalyzer.detect_degradation(model_runs)
                    if degradation.get("degraded"):
                        degradation_results[model] = degradation
                    
                    improvement = TrendAnalyzer.detect_improvements(model_runs)
                    if improvement.get("improved"):
                        improvement_results[model] = improvement
            
            # Output based on format
            if args.format == "json":
                output_path = os.path.join(output_dir, "trend_analysis.json")
                result = {
                    "trend_analysis": trend_analysis,
                    "degradation_alerts": degradation_results,
                    "improvement_alerts": improvement_results,
                    "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
                }
                ReportGenerator.save_json(result, output_path)
                print(f"Trend analysis saved to: {sanitize_path_for_logging(output_path)}")
            
            elif args.format == "markdown":
                output_path = os.path.join(output_dir, "trend_analysis.md")
                md_content = TrendAnalyzer.generate_trend_report_markdown(trend_analysis, degradation_results, improvement_results)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(md_content)
                print(f"Trend analysis report saved to: {sanitize_path_for_logging(output_path)}")
            
            if args.verbose:
                print(f"Analyzed trends across {trend_analysis.get('total_runs_analyzed', 0)} test runs")
                print(f"Models analyzed: {trend_analysis.get('models_analyzed', 0)}")
                if degradation_results:
                    print(f"⚠️  Degradation detected in {len(degradation_results)} models")
                if improvement_results:
                    print(f"✅ Improvements detected in {len(improvement_results)} models")
    
    except Exception as e:
        print(f"Error generating report: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    return 0


class NotificationHandler:
    """Handle notifications for automated testing framework."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize notification handler with configuration."""
        self.config = config or {}
        self.notification_methods = []

        # Initialize notification methods based on config
        if self.config.get("email_enabled", False):
            self.notification_methods.append("email")
        if self.config.get("slack_enabled", False):
            self.notification_methods.append("slack")
        if self.config.get("webhook_enabled", False):
            self.notification_methods.append("webhook")

    @staticmethod
    def create_default_config() -> Dict[str, Any]:
        """Create default notification configuration."""
        return {
            "email_enabled": False,
            "email_smtp_server": "",
            "email_smtp_port": 587,
            "email_username": "",
            "email_password": "",
            "email_from": "",
            "email_to": [],
            "slack_enabled": False,
            "slack_webhook_url": "",
            "slack_channel": "",
            "webhook_enabled": False,
            "webhook_url": "",
            "webhook_headers": {},
            "notify_on_degradation": True,
            "notify_on_improvement": True,
            "notify_on_freeze": True,
            "notify_on_completion": False
        }

    def notify_degradation(self, model_name: str, degradation_info: Dict[str, Any]) -> bool:
        """Send notification about performance degradation."""
        if not self.config.get("notify_on_degradation", True):
            return True

        title = f"🚨 Performance Degradation Detected: {model_name}"
        message = self._format_degradation_message(model_name, degradation_info)

        return self._send_notifications(title, message, "degradation")

    def notify_improvement(self, model_name: str, improvement_info: Dict[str, Any]) -> bool:
        """Send notification about performance improvement."""
        if not self.config.get("notify_on_improvement", True):
            return True

        title = f"✅ Performance Improvement Detected: {model_name}"
        message = self._format_improvement_message(model_name, improvement_info)

        return self._send_notifications(title, message, "improvement")

    def notify_freeze_detected(self, model_name: str, freeze_info: Dict[str, Any]) -> bool:
        """Send notification about freeze detection."""
        if not self.config.get("notify_on_freeze", True):
            return True

        title = f"❄️ Freeze Detected: {model_name}"
        message = self._format_freeze_message(model_name, freeze_info)

        return self._send_notifications(title, message, "freeze")

    def notify_test_completion(self, summary: Dict[str, Any]) -> bool:
        """Send notification about test completion."""
        if not self.config.get("notify_on_completion", False):
            return True

        title = "✅ Automated Testing Complete"
        message = self._format_completion_message(summary)

        return self._send_notifications(title, message, "completion")

    def _format_degradation_message(self, model_name: str, degradation_info: Dict[str, Any]) -> str:
        """Format degradation notification message."""
        pct_increase = degradation_info.get('pct_increase', 0)
        prev_mean = degradation_info.get('prev_mean', 0)
        last_mean = degradation_info.get('last_mean', 0)

        return f"""
Performance degradation detected for model: {model_name}

📈 Response time increased by {pct_increase:.1f}%
   Previous average: {prev_mean:.1f}ms
   Current average: {last_mean:.1f}ms

This may indicate:
- Hardware issues
- Driver problems
- Memory leaks
- Model instability

Please investigate and consider:
- Restarting services
- Checking hardware health
- Updating drivers
- Re-evaluating model compatibility
"""

    def _format_improvement_message(self, model_name: str, improvement_info: Dict[str, Any]) -> str:
        """Format improvement notification message."""
        details = improvement_info.get('details', [])

        message = f"""
Performance improvement detected for model: {model_name}

🎉 Improvements:
"""

        for detail in details:
            message += f"   • {detail}\n"

        message += "\nThis indicates positive changes in model performance or system optimization."

        return message

    def _format_freeze_message(self, model_name: str, freeze_info: Dict[str, Any]) -> str:
        """Format freeze notification message."""
        freeze_count = freeze_info.get('freeze_count', 0)
        total_runs = freeze_info.get('total_runs', 0)
        freeze_rate = (freeze_count / total_runs * 100) if total_runs > 0 else 0

        return f"""
Freeze event detected for model: {model_name}

❄️ Freeze Statistics:
   Freezes: {freeze_count}
   Total runs: {total_runs}
   Freeze rate: {freeze_rate:.1f}%

This may indicate:
- Model instability
- Hardware issues
- Memory constraints
- Driver problems

Recommended actions:
- Monitor system resources
- Check NPU utilization
- Consider model retraining
- Review hardware compatibility
"""

    def _format_completion_message(self, summary: Dict[str, Any]) -> str:
        """Format test completion notification message."""
        total_runs = summary.get('total_runs', 0)
        successful_runs = summary.get('successful_runs', 0)
        failed_runs = summary.get('failed_runs', 0)
        duration = summary.get('duration_minutes', 0)

        success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0

        return f"""
Automated testing cycle completed

📊 Summary:
   Total runs: {total_runs}
   Successful: {successful_runs}
   Failed: {failed_runs}
   Success rate: {success_rate:.1f}%
   Duration: {duration:.1f} minutes

The next automated testing cycle will run according to schedule.
"""

    def _send_notifications(self, title: str, message: str, notification_type: str) -> bool:
        """Send notification through all configured methods."""
        success = True

        for method in self.notification_methods:
            try:
                if method == "email":
                    self._send_email(title, message)
                elif method == "slack":
                    self._send_slack(title, message)
                elif method == "webhook":
                    self._send_webhook(title, message, notification_type)
            except Exception as e:
                print(f"Failed to send {method} notification: {e}")
                success = False

        return success

    def _send_email(self, subject: str, body: str) -> None:
        """Send email notification."""
        # Note: In a real implementation, you would use smtplib or similar
        # For now, just print to console
        print(f"EMAIL NOTIFICATION: {subject}")
        print(f"Body: {body[:200]}...")

        # TODO: Implement actual email sending
        # import smtplib
        # from email.mime.text import MIMEText
        #
        # msg = MIMEText(body)
        # msg['Subject'] = subject
        # msg['From'] = self.config['email_from']
        # msg['To'] = ', '.join(self.config['email_to'])
        #
        # server = smtplib.SMTP(self.config['email_smtp_server'], self.config['email_smtp_port'])
        # server.starttls()
        # server.login(self.config['email_username'], self.config['email_password'])
        # server.sendmail(self.config['email_from'], self.config['email_to'], msg.as_string())
        # server.quit()

    def _send_slack(self, title: str, message: str) -> None:
        """Send Slack notification."""
        # Note: In a real implementation, you would use slack-sdk or requests
        # For now, just print to console
        print(f"SLACK NOTIFICATION: {title}")
        print(f"Message: {message[:200]}...")

        # TODO: Implement actual Slack webhook
        # import requests
        # payload = {
        #     "channel": self.config['slack_channel'],
        #     "username": "Continue Testing Bot",
        #     "text": f"*{title}*\n{message}",
        #     "icon_emoji": ":robot_face:"
        # }
        # requests.post(self.config['slack_webhook_url'], json=payload)

    def _send_webhook(self, title: str, message: str, notification_type: str) -> None:
        """Send webhook notification."""
        # Note: In a real implementation, you would use requests
        # For now, just print to console
        print(f"WEBHOOK NOTIFICATION ({notification_type}): {title}")
        print(f"Message: {message[:200]}...")

        # TODO: Implement actual webhook
        # import requests
        # payload = {
        #     "title": title,
        #     "message": message,
        #     "type": notification_type,
        #     "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        # }
        # headers = self.config.get('webhook_headers', {})
        # requests.post(self.config['webhook_url'], json=payload, headers=headers)


if __name__ == "__main__":
    import sys
    sys.exit(main())
