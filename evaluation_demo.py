#!/usr/bin/env python3
"""
Demonstration script for LLM Model Comparison using Lemonade SDK Evaluation.

This script shows how to run evaluations with different quantization levels
and configurations for model comparison.
"""

import os
import sys
import time
from pathlib import Path

# Add src to path for local development
sys.path.insert(0, str(Path(__file__).parent / "src"))

def demonstrate_evaluation_cli():
    """Demonstrate the evaluation CLI commands."""

    print("🔬 Lemonade SDK - LLM Model Comparison Demo")
    print("=" * 50)

    # Example evaluation commands
    evaluations = [
        {
            "name": "Qwen3-4B FP16",
            "command": "lemonade -i qwen3-4b model-evaluation --model-name Qwen3-4B --model-family qwen --quantization fp16 --benchmark-suite mmlu --offline --output-dir ./evaluation_results"
        },
        {
            "name": "Qwen3-4B INT8",
            "command": "lemonade -i qwen3-4b-int8 model-evaluation --model-name Qwen3-4B --model-family qwen --quantization int8 --benchmark-suite mmlu --offline --output-dir ./evaluation_results"
        },
        {
            "name": "Qwen3-4B INT4",
            "command": "lemonade -i qwen3-4b-int4 model-evaluation --model-name Qwen3-4B --model-family qwen --quantization int4 --benchmark-suite mmlu --offline --output-dir ./evaluation_results"
        },
        {
            "name": "Llama3-8B FP16",
            "command": "lemonade -i llama3-8b model-evaluation --model-name Llama3-8B --model-family llama --quantization fp16 --benchmark-suite hellaswag --offline --output-dir ./evaluation_results"
        },
        {
            "name": "Llama3-8B GPTQ",
            "command": "lemonade -i llama3-8b-gptq model-evaluation --model-name Llama3-8B --model-family llama --quantization gptq --benchmark-suite hellaswag --offline --output-dir ./evaluation_results"
        }
    ]

    print("\n📊 Evaluation Commands for Model Comparison:")
    print("-" * 50)

    for i, eval_config in enumerate(evaluations, 1):
        print(f"\n{i}. {eval_config['name']}")
        print(f"   Command: {eval_config['command']}")

    print("\n🎯 Expected W&B Dashboard Results:")
    print("-" * 50)
    print("After running these evaluations, the W&B dashboard would show:")
    print("• Hierarchical grouping: qwen/fp16/mmlu, qwen/int8/mmlu, etc.")
    print("• Performance metrics: tokens/sec, latency, memory usage")
    print("• Accuracy metrics: MMLU scores, HellaSwag accuracy")
    print("• Hardware metrics: NPU utilization, power consumption")
    print("• Side-by-side comparison charts and tables")

    print("\n📈 Sample Comparison Output:")
    print("-" * 50)
    print("""
EVALUATION SUMMARY
==================================================
✓ mmlu_abstract_algebra: 0.750 accuracy
✓ mmlu_anatomy: 0.820 accuracy
✓ mmlu_astronomy: 0.780 accuracy
Average accuracy: 0.783

Performance Metrics:
• Tokens/second: 125.4
• Latency (P95): 45.2ms
• Peak memory: 3.2GB
• NPU utilization: 87%
    """)

    print("\n🔗 W&B Dashboard Features:")
    print("-" * 50)
    print("• Real-time evaluation progress tracking")
    print("• Interactive comparison charts")
    print("• Historical run retention (6+ months)")
    print("• Custom dashboard layouts")
    print("• Team collaboration and sharing")

def demonstrate_evaluation_api():
    """Demonstrate the evaluation API usage."""

    print("\n🔧 Evaluation API Usage:")
    print("-" * 50)

    api_code = '''
from lemonade.evaluation import WandbMetricsCollector, LMEvalHarness, EvaluationRunner
from lemonade.evaluation.models import EvaluationRun, ModelConfiguration

# Initialize components
wandb_collector = WandbMetricsCollector(
    project_name="lemonade-ryzenai-evals",
    offline=True  # For demo
)

lm_harness = LMEvalHarness(
    server_url="http://localhost:8000",
    timeout=300
)

evaluation_runner = EvaluationRunner(
    wandb_collector=wandb_collector,
    lm_harness=lm_harness
)

# Create evaluation run
evaluation_run = EvaluationRun(
    run_id="demo_eval_001",
    name="Qwen3-4B FP16 vs INT8 Comparison",
    benchmark_suite="mmlu",
    backend="oga",
    hardware_platform={...}  # Hardware specs
)

# Create model configurations
models = [
    ModelConfiguration(
        model_name="Qwen3-4B-FP16",
        model_family="qwen",
        quantization="fp16"
    ),
    ModelConfiguration(
        model_name="Qwen3-4B-INT8",
        model_family="qwen",
        quantization="int8"
    )
]

# Run evaluations
for model_config in models:
    results = evaluation_runner.run_evaluation(
        evaluation_run=evaluation_run,
        model_config=model_config,
        benchmark_tasks=["mmlu_abstract_algebra", "mmlu_anatomy"]
    )
    print(f"Completed evaluation for {model_config.model_name}")
'''

    print(api_code)

if __name__ == "__main__":
    demonstrate_evaluation_cli()
    demonstrate_evaluation_api()

    print("\n✅ Demo completed!")
    print("To run actual evaluations, ensure Lemonade server is running and W&B is configured.")