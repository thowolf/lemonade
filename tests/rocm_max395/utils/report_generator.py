"""
Test result reporting and visualization utilities.

Generates formatted reports, charts, and summaries from test results.
"""

import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import asdict
from pathlib import Path
from datetime import datetime

try:
    from tabulate import tabulate
    TABULATE_AVAILABLE = True
except ImportError:
    TABULATE_AVAILABLE = False

class ReportGenerator:
    """Generate formatted reports from test results and benchmarks."""

    def __init__(self, output_dir: Path):
        """
        Initialize report generator.

        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_test_summary_report(self, test_results: List[Dict[str, Any]],
                                   environment: Dict[str, Any]) -> str:
        """
        Generate a summary report of test execution.

        Args:
            test_results: List of test result dictionaries
            environment: Environment information

        Returns:
            Formatted summary report as string
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        report = []
        report.append("=" * 80)
        report.append("ROCm Max395 Testing Summary Report")
        report.append("=" * 80)
        report.append(f"Generated: {timestamp}")
        report.append("")

        # Environment section
        report.append("Environment Information:")
        report.append("-" * 25)
        for key, value in environment.items():
            report.append(f"  {key}: {value}")
        report.append("")

        # Test results summary
        total_tests = len(test_results)
        passed_tests = sum(1 for r in test_results if r.get("status") == "passed")
        failed_tests = total_tests - passed_tests

        report.append("Test Results Summary:")
        report.append("-" * 22)
        report.append(f"  Total Tests: {total_tests}")
        report.append(f"  Passed: {passed_tests}")
        report.append(f"  Failed: {failed_tests}")
        report.append(".1f")
        report.append("")

        # Individual test results
        if test_results:
            report.append("Individual Test Results:")
            report.append("-" * 25)

            table_data = []
            for result in test_results:
                status_icon = "✓" if result.get("status") == "passed" else "✗"
                duration = result.get("duration", 0)
                table_data.append([
                    status_icon,
                    result.get("test_name", "Unknown"),
                    f"{duration:.2f}s",
                    result.get("model", "N/A")
                ])

            if TABULATE_AVAILABLE:
                table = tabulate(table_data, headers=["Status", "Test", "Duration", "Model"],
                               tablefmt="grid")
                report.append(table)
            else:
                # Fallback to simple text table
                report.append("Status | Test | Duration | Model")
                report.append("-------|------|----------|-------")
                for row in table_data:
                    report.append(" | ".join(str(cell) for cell in row))

        report.append("")
        report.append("=" * 80)

        return "\n".join(report)

    def generate_performance_report(self, benchmark_results: List[Dict[str, Any]]) -> str:
        """
        Generate a performance benchmarking report.

        Args:
            benchmark_results: List of benchmark result dictionaries

        Returns:
            Formatted performance report as string
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        report = []
        report.append("=" * 80)
        report.append("ROCm Max395 Performance Benchmark Report")
        report.append("=" * 80)
        report.append(f"Generated: {timestamp}")
        report.append("")

        if not benchmark_results:
            report.append("No benchmark results available.")
            return "\n".join(report)

        # Performance summary table
        report.append("Performance Summary:")
        report.append("-" * 20)

        table_data = []
        for result in benchmark_results:
            summary = result.get("summary", {})
            tokens_per_sec = summary.get("tokens_per_second", {})
            latency = summary.get("latency_ms", {})

            table_data.append([
                result.get("model_name", "Unknown"),
                result.get("model_size", "Unknown"),
                ".1f",
                ".0f",
                ".0f"
            ])

        if TABULATE_AVAILABLE:
            table = tabulate(table_data,
                           headers=["Model", "Size", "Tokens/sec", "Latency (ms)", "P95 Latency (ms)"],
                           tablefmt="grid")
            report.append(table)
        else:
            # Fallback to simple text table
            report.append("Model | Size | Tokens/sec | Latency (ms) | P95 Latency (ms)")
            report.append("-------|------|------------|--------------|----------------")
            for row in table_data:
                report.append(" | ".join(str(cell) for cell in row))

        report.append("")

        # Detailed results
        report.append("Detailed Results:")
        report.append("-" * 17)

        for result in benchmark_results:
            report.append(f"\nModel: {result.get('model_name', 'Unknown')} ({result.get('model_size', 'Unknown')})")
            report.append(f"Backend: {result.get('backend', 'Unknown')}")
            report.append(f"Test: {result.get('test_name', 'Unknown')}")

            summary = result.get("summary", {})
            tokens_per_sec = summary.get("tokens_per_second", {})
            latency = summary.get("latency_ms", {})

            report.append("  Tokens/second:")
            report.append(".2f")
            report.append(".2f")
            report.append(".2f")

            report.append("  Latency (ms):")
            report.append(".2f")
            report.append(".2f")
            report.append(".2f")
            report.append(".2f")

            report.append(f"  Sample count: {summary.get('count', 0)}")

        report.append("")
        report.append("=" * 80)

        return "\n".join(report)

    def generate_comparison_report(self, results_a: List[Dict[str, Any]],
                                 results_b: List[Dict[str, Any]],
                                 label_a: str, label_b: str) -> str:
        """
        Generate a comparison report between two sets of results.

        Args:
            results_a: First set of benchmark results
            results_b: Second set of benchmark results
            label_a: Label for first set
            label_b: Label for second set

        Returns:
            Formatted comparison report as string
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        report = []
        report.append("=" * 80)
        report.append(f"ROCm Max395 Comparison Report: {label_a} vs {label_b}")
        report.append("=" * 80)
        report.append(f"Generated: {timestamp}")
        report.append("")

        # Create lookup dictionaries
        lookup_a = {r.get("model_name", "Unknown"): r for r in results_a}
        lookup_b = {r.get("model_name", "Unknown"): r for r in results_b}

        # Find common models
        common_models = set(lookup_a.keys()) & set(lookup_b.keys())

        if not common_models:
            report.append("No common models found for comparison.")
            return "\n".join(report)

        report.append("Performance Comparison:")
        report.append("-" * 22)

        table_data = []
        for model in sorted(common_models):
            result_a = lookup_a[model]
            result_b = lookup_b[model]

            tokens_a = result_a.get("summary", {}).get("tokens_per_second", {}).get("mean", 0)
            tokens_b = result_b.get("summary", {}).get("tokens_per_second", {}).get("mean", 0)

            latency_a = result_a.get("summary", {}).get("latency_ms", {}).get("mean", 0)
            latency_b = result_b.get("summary", {}).get("latency_ms", {}).get("mean", 0)

            # Calculate ratios (avoid division by zero)
            tokens_ratio = tokens_a / tokens_b if tokens_b > 0 else 0
            latency_ratio = latency_b / latency_a if latency_a > 0 else 0  # Inverted for better readability

            table_data.append([
                model,
                ".1f",
                ".1f",
                ".2f",
                ".1f",
                ".1f",
                ".2f"
            ])

        if TABULATE_AVAILABLE:
            table = tabulate(table_data,
                           headers=[f"Model", f"{label_a} T/s", f"{label_b} T/s", "Ratio",
                                   f"{label_a} Lat", f"{label_b} Lat", "Ratio"],
                           tablefmt="grid")
            report.append(table)
        else:
            # Fallback to simple text table
            headers = [f"Model", f"{label_a} T/s", f"{label_b} T/s", "Ratio",
                      f"{label_a} Lat", f"{label_b} Lat", "Ratio"]
            report.append(" | ".join(headers))
            report.append(" | ".join("-" * len(h) for h in headers))
            for row in table_data:
                report.append(" | ".join(str(cell) for cell in row))

        report.append("")
        report.append("Ratio > 1.0 means A performs better than B")
        report.append("=" * 80)

        return "\n".join(report)

    def save_report(self, report_content: str, filename: str) -> Path:
        """
        Save a report to file.

        Args:
            report_content: Report content as string
            filename: Filename for the report

        Returns:
            Path to saved report file
        """
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_content)
        return filepath

    def save_json_results(self, results: List[Dict[str, Any]], filename: str) -> Path:
        """
        Save results as JSON file.

        Args:
            results: Results to save
            filename: Filename for JSON file

        Returns:
            Path to saved JSON file
        """
        filepath = self.output_dir / filename
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        return filepath

    def generate_html_report(self, test_results: List[Dict[str, Any]],
                           benchmark_results: List[Dict[str, Any]],
                           environment: Dict[str, Any]) -> str:
        """
        Generate an HTML report with charts and tables.

        Args:
            test_results: Test execution results
            benchmark_results: Performance benchmark results
            environment: Environment information

        Returns:
            HTML report as string
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        html = ".1f"".1f"".1f"f"""
<!DOCTYPE html>
<html>
<head>
    <title>ROCm Max395 Testing Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .section {{ margin: 20px 0; }}
        .metric {{ display: inline-block; margin: 10px; padding: 10px; background: #e8f4f8; border-radius: 3px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .pass {{ color: green; }}
        .fail {{ color: red; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>ROCm Max395 Testing Report</h1>
        <p>Generated: {timestamp}</p>
        <p>Environment: {environment.get('platform', 'Unknown')}</p>
    </div>

    <div class="section">
        <h2>Test Summary</h2>
        <div class="metric">Total Tests: {len(test_results)}</div>
        <div class="metric">Passed: {sum(1 for r in test_results if r.get('status') == 'passed')}</div>
        <div class="metric">Failed: {sum(1 for r in test_results if r.get('status') != 'passed')}</div>
    </div>

    <div class="section">
        <h2>Performance Results</h2>
        <table>
            <tr>
                <th>Model</th>
                <th>Size</th>
                <th>Tokens/sec</th>
                <th>Latency (ms)</th>
                <th>P95 Latency (ms)</th>
            </tr>
"""

        for result in benchmark_results:
            summary = result.get("summary", {})
            tokens_per_sec = summary.get("tokens_per_second", {})
            latency = summary.get("latency_ms", {})

            html += ".1f"".0f"".0f"f"""
            <tr>
                <td>{result.get('model_name', 'Unknown')}</td>
                <td>{result.get('model_size', 'Unknown')}</td>
                <td>{tokens_per_sec.get('mean', 0):.1f}</td>
                <td>{latency.get('mean', 0):.0f}</td>
                <td>{latency.get('p95', 0):.0f}</td>
            </tr>
"""

        html += """
        </table>
    </div>
</body>
</html>
"""

        return html

# Convenience functions
def create_report_generator(output_dir: Path) -> ReportGenerator:
    """Create and return a report generator instance."""
    return ReportGenerator(output_dir)

def generate_summary_report(test_results: List[Dict[str, Any]],
                          environment: Dict[str, Any],
                          output_dir: Path) -> Path:
    """Generate and save a summary report."""
    generator = ReportGenerator(output_dir)
    report = generator.generate_test_summary_report(test_results, environment)
    return generator.save_report(report, "test_summary.txt")