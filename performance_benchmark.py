#!/usr/bin/env python3
"""
Performance Benchmarking Script for Continue Extension Models

Tests 3 selected models and generates comparative performance analysis.
"""

import sys
import os
import time
import json
import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add the continue-testing directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts', 'benchmarks', 'continue-testing'))

from report_generator import ReportGenerator, PerformanceAnalyzer

def run_model_benchmark(model_name: str, duration: int = 60) -> Dict[str, Any]:
    """Run benchmark for a single model using subprocess."""
    print(f"\n{'='*60}")
    print(f"🚀 BENCHMARKING: {model_name}")
    print(f"{'='*60}")

    try:
        import subprocess
        import sys
        import os

        # Path to test_runner.py
        test_runner_path = os.path.join(os.path.dirname(__file__), 'scripts', 'benchmarks', 'continue-testing', 'test_runner.py')

        # Build command
        cmd = [
            sys.executable, '-m', 'scripts.benchmarks.continue-testing.test_runner',
            '--monitor-only',
            '--model', model_name,
            '--duration', str(duration),
            '--config-dir', os.path.join(os.path.dirname(__file__), 'scripts', 'benchmarks', 'continue-testing', 'config'),
            '--results-dir', os.path.join(os.path.dirname(__file__), 'scripts', 'benchmarks', 'continue-testing', 'results'),
            '--no-wandb'  # Disable W&B to avoid logging issues
        ]

        # Run the command
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(__file__))

        if result.returncode == 0:
            print(f"✅ {model_name} benchmark completed successfully")
            # Try to find the latest result file
            results_dir = Path(__file__).parent / "scripts" / "benchmarks" / "continue-testing" / "results" / "test_runs"
            if results_dir.exists():
                result_files = list(results_dir.glob("run_*.json"))
                if result_files:
                    latest_file = max(result_files, key=lambda x: x.stat().st_mtime)
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        return {"run": json.load(f)}
            return {"success": True, "model": model_name}
        else:
            print(f"❌ {model_name} benchmark failed: {result.stderr}")
            return {"error": result.stderr, "model": model_name}

    except Exception as e:
        print(f"❌ {model_name} benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e), "model": model_name}

def analyze_performance_comparison(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze and compare performance across all models."""
    print(f"\n{'='*60}")
    print("📊 PERFORMANCE ANALYSIS")
    print(f"{'='*60}")

    # Filter successful results
    successful_results = [r for r in results if "error" not in r]

    if not successful_results:
        return {"error": "No successful benchmark results to analyze"}

    # Extract test runs for analysis
    test_runs = [r["run"] for r in successful_results]

    # Generate performance analysis
    analysis = ReportGenerator.analyze_model_performance(test_runs)

    # Generate compatibility matrix
    compatibility_matrix = ReportGenerator.generate_compatibility_matrix(test_runs)

    return {
        "analysis": analysis,
        "compatibility_matrix": compatibility_matrix,
        "benchmark_results": successful_results,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

def save_benchmark_report(analysis_result: Dict[str, Any], models_tested: List[str]):
    """Save comprehensive benchmark report."""
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    reports_dir = Path(__file__).parent / "scripts" / "benchmarks" / "continue-testing" / "results" / "reports"

    # Create reports directory
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Save JSON report
    json_report = reports_dir / f"performance_comparison_{timestamp}.json"
    with open(json_report, 'w', encoding='utf-8') as f:
        json.dump(analysis_result, f, indent=2, default=str)

    # Generate and save markdown report
    md_report = None
    if "compatibility_matrix" in analysis_result:
        md_content = ReportGenerator.generate_markdown(analysis_result["compatibility_matrix"])
        md_report = reports_dir / f"performance_comparison_{timestamp}.md"
        with open(md_report, 'w', encoding='utf-8') as f:
            f.write(md_content)

    print(f"\n📄 Reports saved to: {reports_dir}")
    print(f"   - JSON: {json_report.name}")
    if md_report:
        print(f"   - Markdown: {md_report.name}")

    return str(json_report)

def main():
    """Main benchmarking function."""
    print("🎯 Continue Extension Model Performance Benchmarking")
    print("Testing 3 models for comparative analysis\n")

    # Selected models for benchmarking
    models_to_test = [
        "Qwen 2.5 Coder 7B",      # Medium model (14GB)
        "DeepSeek Coder v2 16B",  # Large model (16GB)
        "Llama 3.2 3B Instruct"   # Small model (3GB)
    ]

    print("📋 Models to benchmark:")
    for i, model in enumerate(models_to_test, 1):
        print(f"   {i}. {model}")
    print()

    # Benchmark duration per model (seconds)
    benchmark_duration = 30  # Shorter for quick comparison
    print(f"⏱️  Benchmark duration per model: {benchmark_duration} seconds")
    print("⚡ Starting benchmarks...\n")

    # Run benchmarks for all models
    results = []
    start_time = time.time()

    for model in models_to_test:
        result = run_model_benchmark(model, benchmark_duration)
        results.append(result)

        # Brief pause between models
        if model != models_to_test[-1]:
            print("⏳ Cooling down for 5 seconds...")
            time.sleep(5)

    total_time = time.time() - start_time
    print(f"⏱️  Total benchmarking time: {total_time:.1f} seconds")
    # Analyze results
    analysis_result = analyze_performance_comparison(results)

    # Save reports
    report_path = save_benchmark_report(analysis_result, models_to_test)

    # Summary
    print(f"\n{'='*60}")
    print("🏆 BENCHMARK SUMMARY")
    print(f"{'='*60}")

    successful = len([r for r in results if "error" not in r])
    print(f"✅ Successful benchmarks: {successful}/{len(models_to_test)}")
    print(f"📊 Performance analysis: {'Generated' if 'analysis' in analysis_result else 'Failed'}")
    print(f"📄 Full report: {report_path}")

    if "compatibility_matrix" in analysis_result:
        matrix = analysis_result["compatibility_matrix"]
        print("\n🎯 Model Compatibility:")
        for model, data in matrix.items():
            status = "✅ Compatible" if data.get("compatible") else "❌ Incompatible"
            rating = data.get("performance_rating", "unknown")
            print(f"   • {model}: {status} ({rating})")

    print("\n🎉 Benchmarking complete!")
    return 0

if __name__ == "__main__":
    sys.exit(main())