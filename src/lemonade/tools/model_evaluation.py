"""
Evaluation tool for LLM model comparison using W&B Weave.

This tool provides CLI commands for running comprehensive LLM evaluations
with W&B logging and dashboard visualization.
"""

import argparse
import json
import os
import sys
import time
from typing import List, Optional, Dict, Any
from pathlib import Path

from lemonade.state import State
from lemonade.tools import Tool, FirstTool
import lemonade.common.printing as printing
import lemonade.common.build as build

try:
    from lemonade.evaluation.runners import EvaluationRunner
    from lemonade.evaluation.wandb_logger import WandbMetricsCollector
    from lemonade.evaluation.harness import LMEvalHarness
    from lemonade.evaluation.config import EvaluationConfig
    from lemonade.evaluation.models import (
        EvaluationRun, ModelConfiguration, HardwarePlatform,
        RunStatus, MoEConfig
    )
    EVALUATION_AVAILABLE = True
except ImportError:
    EVALUATION_AVAILABLE = False


class ModelEvaluation(FirstTool):
    """
    Tool for comprehensive LLM model evaluation and comparison.

    Runs standardized benchmarks across different model configurations
    with W&B Weave logging for dashboard visualization and analysis.
    """

    unique_name = "model-evaluation"

    def __init__(self):
        super().__init__(
            monitor_message="Run comprehensive LLM model evaluation with W&B logging"
        )

        if not EVALUATION_AVAILABLE:
            raise ImportError(
                "Evaluation module not available. "
                "Install with: pip install lemonade-sdk[evaluation]"
            )

        self.evaluation_runner = None
        self.wandb_collector = None
        self.lm_harness = None

    @staticmethod
    def parser(add_help: bool = True) -> argparse.ArgumentParser:
        parser = __class__.helpful_parser(
            short_description="Run LLM model evaluation with W&B dashboard",
            add_help=add_help,
        )

        parser.add_argument(
            "--config",
            type=str,
            help="Path to evaluation configuration JSON file",
        )

        parser.add_argument(
            "--model-name",
            type=str,
            required=True,
            help="Name of the model to evaluate",
        )

        parser.add_argument(
            "--model-family",
            type=str,
            required=True,
            help="Model family (e.g., 'llama', 'qwen', 'mistral')",
        )

        parser.add_argument(
            "--checkpoint",
            type=str,
            help="Model checkpoint or path",
        )

        parser.add_argument(
            "--quantization",
            type=str,
            default="fp16",
            choices=["fp16", "int8", "int4", "gptq", "awq"],
            help="Quantization method used",
        )

        parser.add_argument(
            "--moe-config",
            type=str,
            help="JSON string with MoE configuration (experts, top_k, etc.)",
        )

        parser.add_argument(
            "--backend",
            type=str,
            default="oga",
            choices=["oga", "llamacpp", "transformers", "vllm"],
            help="Inference backend used",
        )

        parser.add_argument(
            "--benchmark-suite",
            type=str,
            default="mmlu",
            choices=["mmlu", "hellaswag", "arc", "gsm8k", "all"],
            help="Benchmark suite to run",
        )

        parser.add_argument(
            "--server-url",
            type=str,
            default="http://localhost:8000",
            help="Lemonade server URL for evaluation",
        )

        parser.add_argument(
            "--wandb-project",
            type=str,
            default="lemonade-ryzenai-evals",
            help="W&B project name",
        )

        parser.add_argument(
            "--wandb-entity",
            type=str,
            help="W&B team/organization name",
        )

        parser.add_argument(
            "--offline",
            action="store_true",
            help="Run W&B in offline mode",
        )

        parser.add_argument(
            "--output-dir",
            type=str,
            help="Directory to save evaluation results",
        )

        parser.add_argument(
            "--max-concurrent",
            type=int,
            default=1,
            help="Maximum concurrent benchmark executions",
        )

        parser.add_argument(
            "--limit",
            type=int,
            help="Limit number of samples per benchmark",
        )

        parser.add_argument(
            "--num-fewshot",
            type=int,
            default=0,
            help="Number of few-shot examples to use",
        )

        return parser

    def run(self, state: State, input: str = "", **kwargs) -> State:
        """Run the model evaluation."""

        # Load or create evaluation configuration
        if kwargs.get('config'):
            config = self._load_config(kwargs['config'])
        else:
            config = self._create_config_from_args(kwargs)

        # Validate configuration
        try:
            validated_config = EvaluationConfig(**config)
        except Exception as e:
            printing.log_error(f"Configuration validation failed: {e}")
            sys.exit(1)

        # Initialize components
        self._initialize_components(validated_config, kwargs)

        # Create evaluation run
        evaluation_run = self._create_evaluation_run(validated_config, kwargs)

        # Create model configuration
        model_config = self._create_model_config(kwargs)

        # Get benchmark tasks
        benchmark_tasks = self._get_benchmark_tasks(kwargs.get('benchmark_suite', 'mmlu'))

        try:
            # Run evaluation
            printing.info(f"Starting evaluation run: {evaluation_run.run_id}")
            printing.info(f"Model: {model_config.model_name} ({model_config.quantization})")
            printing.info(f"Benchmarks: {', '.join(benchmark_tasks)}")

            results = self.evaluation_runner.run_evaluation(
                evaluation_run=evaluation_run,
                model_config=model_config,
                benchmark_tasks=benchmark_tasks
            )

            # Save results if output directory specified
            if kwargs.get('output_dir'):
                self._save_results(results, kwargs['output_dir'], evaluation_run.run_id)

            # Print summary
            self._print_summary(results)

            printing.success(f"Evaluation completed successfully")

            return state

        except Exception as e:
            printing.error(f"Evaluation failed: {e}")
            if self.wandb_collector:
                self.wandb_collector.update_run_status(RunStatus.FAILED, str(e))
                self.wandb_collector.finish_evaluation_run()
            sys.exit(1)

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load evaluation configuration from file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            raise ValueError(f"Failed to load config from {config_path}: {e}")

    def _create_config_from_args(self, args) -> Dict[str, Any]:
        """Create configuration from command line arguments."""
        from datetime import datetime
        
        # Create benchmark suite config
        benchmark_suite = args.get('benchmark_suite', 'mmlu')
        accuracy_suites = []
        if benchmark_suite == 'mmlu':
            accuracy_suites = [{"name": "mmlu", "limit": 100, "num_fewshot": args.get('num_fewshot', 0)}]
        elif benchmark_suite == 'hellaswag':
            accuracy_suites = [{"name": "hellaswag", "limit": 100, "num_fewshot": args.get('num_fewshot', 0)}]
        else:
            accuracy_suites = [{"name": benchmark_suite, "limit": 100, "num_fewshot": args.get('num_fewshot', 0)}]
        
        config = {
            "metadata": {
                "name": f"{args.get('model_family')} {args.get('quantization')} Evaluation",
                "version": "1.0.0",
                "created": datetime.utcnow().isoformat(),
                "description": f"Evaluation of {args.get('model_name')} on {benchmark_suite}",
                "author": "lemonade-sdk"
            },
            "model": {
                "identifier": args.get('model_name'),
                "checkpoint": args.get('checkpoint') or f"{args.get('model_family')}/{args.get('model_name')}",
                "recipe": args.get('backend', 'oga'),
                "quantization": {
                    "method": args.get('quantization', 'fp16'),
                    "bits": 16 if args.get('quantization') == 'fp16' else (8 if args.get('quantization') == 'int8' else 4)
                },
                "size_gb": 7.5,  # Would be detected in real implementation
                "context_length": 8192
            },
            "hardware": {
                "backend": "ryzenai",
                "device": "npu",
                "platform": "AMD Ryzen AI Max+ 395",
                "architecture": "gfx1103",
                "vram_limit_gb": 32,
                "system_ram_gb": 32,
                "flags": ["directml"]
            },
            "benchmarks": {
                "accuracy": {
                    "enabled": True,
                    "suites": accuracy_suites
                }
            },
            "wandb": {
                "enabled": not args.get('offline', False),
                "project": args.get('wandb_project', 'lemonade-ryzenai-evals'),
                "entity": args.get('wandb_entity'),
                "offline": args.get('offline', False)
            }
        }
        
        return config

    def _initialize_components(self, config: EvaluationConfig, args: argparse.Namespace) -> None:
        """Initialize evaluation components."""
        # Initialize W&B collector
        self.wandb_collector = WandbMetricsCollector(
            project_name=config.wandb_project,
            entity=config.wandb_entity,
            offline=config.offline
        )

        # Initialize LM Eval Harness
        self.lm_harness = LMEvalHarness(
            server_url=config.server_url,
            timeout=config.timeout,
            max_concurrent=config.max_concurrent
        )

        # Initialize evaluation runner
        self.evaluation_runner = EvaluationRunner(
            wandb_collector=self.wandb_collector,
            lm_harness=self.lm_harness,
            max_concurrent=config.max_concurrent
        )

    def _create_evaluation_run(self, config: EvaluationConfig, args: argparse.Namespace) -> EvaluationRun:
        """Create evaluation run entity."""
        run_id = f"eval_{args.model_family}_{args.quantization}_{args.backend}_{int(time.time())}"

        return EvaluationRun(
            run_id=run_id,
            name=f"{args.get('model_family')} {args.get('quantization')} Evaluation",
            benchmark_suite=args.get('benchmark_suite', 'mmlu'),
            backend=args.get('backend', 'oga'),
            hardware_platform=HardwarePlatform(**config.hardware_platform),
            status=RunStatus.PENDING,
            config=config.dict()
        )

    def _create_model_config(self, args: argparse.Namespace) -> ModelConfiguration:
        """Create model configuration entity."""
        # Parse MoE config if provided
        moe_config = None
        if args.get('moe_config'):
            try:
                moe_data = json.loads(args['moe_config'])
                moe_config = MoEConfig(**moe_data)
            except Exception as e:
                printing.warning(f"Failed to parse MoE config: {e}")

        return ModelConfiguration(
            model_name=args.get('model_name'),
            model_family=args.get('model_family'),
            checkpoint=args.get('checkpoint') or f"{args.get('model_family')}/{args.get('model_name')}",
            quantization=args.get('quantization'),
            moe_config=moe_config
        )

    def _get_benchmark_tasks(self, benchmark_suite: str) -> List[str]:
        """Get benchmark tasks for the specified suite."""
        if benchmark_suite == "mmlu":
            return ["mmlu_abstract_algebra", "mmlu_anatomy", "mmlu_astronomy"]
        elif benchmark_suite == "hellaswag":
            return ["hellaswag"]
        elif benchmark_suite == "arc":
            return ["arc_easy", "arc_challenge"]
        elif benchmark_suite == "gsm8k":
            return ["gsm8k"]
        elif benchmark_suite == "all":
            return ["mmlu_abstract_algebra", "hellaswag", "arc_easy", "gsm8k"]
        else:
            return [benchmark_suite]

    def _save_results(self, results: List, output_dir: str, run_id: str) -> None:
        """Save evaluation results to file."""
        output_path = Path(output_dir) / f"{run_id}_results.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "run_id": run_id,
            "timestamp": time.time(),
            "results": [result.dict() for result in results]
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        printing.info(f"Results saved to: {output_path}")

    def _print_summary(self, results: List) -> None:
        """Print evaluation summary."""
        printing.info("\n" + "="*50)
        printing.info("EVALUATION SUMMARY")
        printing.info("="*50)

        successful = 0
        total_accuracy = 0.0
        accuracy_count = 0

        for result in results:
            if result.accuracy_metrics and result.accuracy_metrics.acc is not None:
                successful += 1
                total_accuracy += result.accuracy_metrics.acc
                accuracy_count += 1

                printing.info(f"✓ {result.task_name}: {result.accuracy_metrics.acc:.3f} accuracy")
            else:
                printing.info(f"✗ {result.task_name}: Failed or no accuracy metrics")

        if accuracy_count > 0:
            avg_accuracy = total_accuracy / accuracy_count
            printing.info(f"Average accuracy: {avg_accuracy:.3f}")
        else:
            printing.warning("No accuracy metrics available")

        printing.info(f"Successful benchmarks: {successful}/{len(results)}")
        printing.info("="*50)