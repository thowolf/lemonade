#!/usr/bin/env python3
"""
Mock evaluation demonstration for W&B dashboard.

This script demonstrates the evaluation system by creating mock evaluation
results and logging them to W&B to show the dashboard functionality.
"""

import sys
import time
import random
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def create_mock_evaluation_data():
    """Create mock evaluation data for demonstration."""
    models = [
        {"name": "Qwen3-4B", "family": "qwen", "size": 7.5},
        {"name": "Llama3-8B", "family": "llama", "size": 15.0},
        {"name": "Mixtral-8x7B", "family": "mistral", "size": 46.7}
    ]

    quantizations = ["fp16", "int8", "int4"]
    benchmarks = ["mmlu", "hellaswag", "arc"]

    evaluations = []

    for model in models:
        for quant in quantizations:
            for benchmark in benchmarks:
                # Create mock results
                accuracy = random.uniform(0.3, 0.8)  # Random accuracy between 30-80%
                tokens_per_sec = random.uniform(50, 200)  # Random throughput
                latency = random.uniform(20, 100)  # Random latency in ms

                evaluation = {
                    "model_name": f"{model['name']}-{quant}",
                    "model_family": model["family"],
                    "quantization": quant,
                    "benchmark": benchmark,
                    "accuracy": accuracy,
                    "tokens_per_second": tokens_per_sec,
                    "latency_ms": latency,
                    "model_size_gb": model["size"],
                    "hardware": "AMD Ryzen AI Max+ 395",
                    "timestamp": datetime.now().isoformat()
                }
                evaluations.append(evaluation)

    return evaluations

def demonstrate_wandb_logging(evaluations):
    """Demonstrate W&B logging with mock data."""
    print("🚀 Demonstrating W&B Evaluation Logging")
    print("=" * 50)

    try:
        from lemonade.evaluation.wandb_logger import WandbMetricsCollector

        # Initialize W&B collector
        print("📊 Initializing W&B Metrics Collector...")
        wandb_collector = WandbMetricsCollector(
            project_name="lemonade-ryzenai-evals-demo",
            offline=True  # Use offline mode for demo
        )
        print("✅ W&B Collector initialized (offline mode)")

        # Log mock evaluations
        print(f"\n📈 Logging {len(evaluations)} mock evaluations...")

        for i, eval_data in enumerate(evaluations):
            print(f"  Logging evaluation {i+1}/{len(evaluations)}: {eval_data['model_name']} on {eval_data['benchmark']}")

            # Create mock evaluation run
            from lemonade.evaluation.models import (
                EvaluationRun, ModelConfiguration, HardwarePlatform,
                RunStatus, PerformanceMetrics, AccuracyMetrics
            )

            # Create model config
            model_config = ModelConfiguration(
                model_name=eval_data["model_name"],
                model_family=eval_data["model_family"],
                quantization=eval_data["quantization"],
                checkpoint=f"{eval_data['model_family']}/{eval_data['model_name']}:model",
                size_gb=eval_data["model_size_gb"],
                context_length=8192
            )

            # Create hardware platform
            hw_platform = HardwarePlatform(
                platform_name="AMD Ryzen AI Max+ 395",
                cpu="AMD Ryzen AI 9 395",
                gpu=None,
                npu="AMD Ryzen AI NPU",
                architecture="Zen 4c",
                total_vram_gb=32,
                system_ram_gb=32,
                os="Windows 11",
                driver_version=None
            )

            # Create evaluation run
            from uuid import uuid4
            run_id = str(uuid4())
            evaluation_run = EvaluationRun(
                run_id=run_id,
                name=f"Demo: {eval_data['model_name']} on {eval_data['benchmark']}",
                benchmark_suite=eval_data["benchmark"],
                backend="oga",
                hardware_platform=hw_platform,
                model_config_id=model_config.config_id,
                status=RunStatus.RUNNING  # Start as RUNNING
            )

            # Start evaluation run
            wandb_collector.start_evaluation_run(evaluation_run, model_config)

            # Log metrics using BenchmarkResult
            from lemonade.evaluation.models import BenchmarkResult, ResourceMetrics
            
            accuracy_metrics = AccuracyMetrics(
                acc=eval_data["accuracy"],
                acc_stderr=0.02
            )

            performance_metrics = PerformanceMetrics(
                tokens_per_second=eval_data["tokens_per_second"],
                latency_ms=eval_data["latency_ms"],
                total_tokens=1000,
                prompt_tokens=500,
                completion_tokens=500
            )

            resource_metrics = ResourceMetrics(
                peak_memory_mb=random.uniform(1000, 8000),
                cpu_utilization_percent=random.uniform(10, 40),
                vram_usage_mb=eval_data["model_size_gb"] * 1024 * 0.8  # Convert GB to MB
            )

            benchmark_result = BenchmarkResult(
                run_id=evaluation_run.run_id,
                task_name=eval_data["benchmark"],
                accuracy_metrics=accuracy_metrics,
                performance_metrics=performance_metrics,
                resource_metrics=resource_metrics,
                sample_count=100
            )

            # Log to W&B
            wandb_collector.log_benchmark_result(benchmark_result)

            # Complete the run
            from datetime import datetime
            evaluation_run.completed_at = datetime.datetime.now(datetime.timezone.utc)
            wandb_collector.update_run_status(RunStatus.COMPLETED, "Demo evaluation completed")
            wandb_collector.finish_evaluation_run()

            # Small delay to avoid overwhelming W&B
            time.sleep(0.1)

        print("✅ All evaluations logged successfully!")

        # Show summary
        print("\n📊 Evaluation Summary:")
        print(f"  • Models evaluated: {len(set([e['model_name'] for e in evaluations]))}")
        print(f"  • Total evaluations: {len(evaluations)}")
        print(f"  • Benchmarks: {', '.join(set([e['benchmark'] for e in evaluations]))}")
        print(f"  • Hardware: AMD Ryzen AI Max+ 395")

        print("\n🎯 W&B Dashboard Features Demonstrated:")
        print("  • Hierarchical grouping by model family → quantization → benchmark")
        print("  • Accuracy metrics comparison across models")
        print("  • Performance metrics (tokens/sec, latency)")
        print("  • Hardware utilization tracking")
        print("  • Model size and quantization impact analysis")

        print("\n🔗 To view the dashboard:")
        print("  1. Run 'wandb login' (if not already logged in)")
        print("  2. Visit https://wandb.ai")
        print("  3. Find project 'lemonade-ryzenai-evals-demo'")
        print("  4. Explore the hierarchical evaluation results!")

        return True

    except Exception as e:
        print(f"❌ W&B logging demonstration failed: {e}")
        return False

def main():
    """Main demonstration function."""
    print("🎬 Lemonade SDK Evaluation System - W&B Dashboard Demo")
    print("=" * 60)

    # Create mock data
    print("📋 Creating mock evaluation data...")
    evaluations = create_mock_evaluation_data()
    print(f"✅ Created {len(evaluations)} mock evaluations")

    # Demonstrate W&B logging
    success = demonstrate_wandb_logging(evaluations)

    print("\n" + "=" * 60)
    if success:
        print("🎉 W&B Dashboard Demo completed successfully!")
        print("💡 The evaluation system is ready for production use.")
    else:
        print("❌ Demo encountered issues. Check the error messages above.")

    print("\n🚀 Next Steps:")
    print("  1. Start Lemonade server: lemonade-server-dev serve")
    print("  2. Run real evaluations: lemonade -i <model> model-evaluation [options]")
    print("  3. View results at https://wandb.ai")

if __name__ == "__main__":
    main()