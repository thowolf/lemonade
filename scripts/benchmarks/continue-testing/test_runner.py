"""Minimal test runner CLI for Continue testing framework.

Supports `--monitor-only` and `--interactive` (guided) modes.
"""
from __future__ import annotations

import argparse
import datetime
import json
import logging
import os
import uuid
import time
import threading
import schedule
from typing import Any, Dict, List, Optional, Callable

import yaml

from .model_manager import ConfigLoader, TestRun
from .metrics_collector import SystemMonitor, SystemMetrics
from .freeze_detector import FreezeDetector
from .report_generator import ReportGenerator, PerformanceAnalyzer
from .utils import sanitize_path_for_logging

# Setup structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'test_runner.log'))
    ]
)
logger = logging.getLogger(__name__)

RESULTS_DIR_DEFAULT = os.path.join(os.path.dirname(__file__), "results")


def check_dependencies() -> None:
    """Check that required dependencies meet minimum version requirements."""
    import platform
    issues = []

    # Check psutil version
    try:
        import psutil
        if psutil.version_info < (6, 1, 1):
            issues.append(f"psutil {psutil.__version__} is too old. Required: >= 6.1.1")
    except ImportError:
        issues.append("psutil is not installed")

    # Check pyadl availability (no version check needed)
    try:
        import pyadl
    except ImportError:
        pass  # pyadl is optional

    # Check yamale availability (no version check needed)
    try:
        import yamale
    except ImportError:
        pass  # yamale is optional for basic functionality

    if issues:
        print("Warning: Dependency issues detected:")
        for issue in issues:
            print(f"  - {issue}")
        print("Some features may not work correctly.")


def setup_common_args_and_logging(parser: argparse.ArgumentParser, args: argparse.Namespace) -> Optional['WandbLogger']:
    """Setup common logging configuration and W&B logger initialization.

    Returns:
        WandbLogger instance if W&B is enabled and available, None otherwise.
    """
    # Setup logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.verbose:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.WARNING)

    # Initialize W&B logger if requested
    wandb_logger = None
    if getattr(args, 'wandb', False) and not getattr(args, 'no_wandb', False):
        try:
            from .utils.wandb_logger import WandbLogger
            run_name = getattr(args, 'model', f"test_run_{int(time.time())}")
            wandb_logger = WandbLogger(run_name=run_name, offline=getattr(args, 'offline_wandb', False))
            if args.verbose or args.debug:
                print(f"W&B logger initialized: {wandb_logger.is_available()}{(' (offline mode)' if getattr(args, 'offline_wandb', False) else '')}")
        except Exception as e:
            if args.verbose or args.debug:
                print(f"W&B logger not available: {e}")
    elif getattr(args, 'no_wandb', False) and (args.verbose or args.debug):
        print("W&B logging disabled by --no-wandb flag")

    return wandb_logger


def detect_and_save_hardware_config(config_dir: str) -> None:
    """Auto-detect hardware configuration and save to hardware.yaml if not already configured."""
    hardware_path = os.path.join(config_dir, "hardware.yaml")
    
    # Check if hardware.yaml already exists and has real data (not template)
    if os.path.exists(hardware_path):
        try:
            with open(hardware_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            # If it has real CPU model (not template), assume it's configured
            if data and data.get("hardware", {}).get("cpu", {}).get("model") != "AMD Ryzen AI 9 365":
                return  # Already configured
        except Exception:
            pass  # File corrupted or invalid, re-detect
    
    print("Auto-detecting hardware configuration...")
    
    # Detect hardware
    monitor = SystemMonitor()
    sample = monitor.sample("hw-detect")
    
    # Get system info
    import platform
    system_info = {
        "cpu_model": platform.processor() or "Unknown",
        "ram_total_gb": sample.memory_total_gb,
        "os_version": f"{platform.system()} {platform.release()}",
        "python_version": f"{platform.python_version()}",
    }
    
    # NPU info
    npu_info = {}
    if sample.npu_metrics:
        npu_info = {
            "npu_available": True,
            "npu_driver_version": sample.npu_metrics.get("driver_version"),
        }
    else:
        npu_info = {"npu_available": False}
    
try:
    import GPUtil
    GPU_UTIL_AVAILABLE = True
except ImportError:
    GPU_UTIL_AVAILABLE = False


def detect_and_save_hardware_config(config_dir: str = "config") -> None:
    """Auto-detect hardware configuration and save to hardware.yaml."""
    import platform
    import psutil
    
    # System info using psutil and platform
    cpu_model = platform.processor() or "Unknown"
    ram_total_gb = round(psutil.virtual_memory().total / (1024 ** 3), 1)
    os_version = f"{platform.system()} {platform.release()}"
    python_version = platform.python_version()
    
    # NPU info - try to detect AMD Ryzen AI NPU
    npu_info = {"npu_available": False}
    try:
        # Check for AMD Ryzen AI NPU via xrt-smi or other indicators
        import subprocess
        result = subprocess.run(['xrt-smi', '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            npu_info = {
                "npu_available": True,
                "npu_driver_version": "AMD Ryzen AI",
            }
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
        pass
    
    # GPU info (basic detection)
    gpu_info = {}
    if GPU_UTIL_AVAILABLE:
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                gpu_info = {
                    "gpu_model": gpu.name,
                    "gpu_vram_gb": round(gpu.memoryTotal / 1024, 1),
                }
        except Exception:
            gpu_info = {"gpu_model": "Not detected"}
    else:
        gpu_info = {"gpu_model": "GPUtil not available"}
    
    # Create hardware config
    hardware_config = {
        "hardware": {
            "cpu": {
                "model": cpu_model,
            },
            "memory": {
                "total_gb": ram_total_gb,
            },
            "gpu": gpu_info,
            "npu": npu_info,
            "software": {
                "os_version": os_version,
                "python_version": python_version,
            }
        }
    }
    
    # Save to file
    hardware_path = os.path.join(config_dir, "hardware.yaml")
    os.makedirs(config_dir, exist_ok=True)
    with open(hardware_path, "w", encoding="utf-8") as f:
        yaml.dump(hardware_config, f, default_flow_style=False, sort_keys=False)
    
    print(f"Hardware configuration saved to: {sanitize_path_for_logging(hardware_path)}")
    print(f"Detected: CPU={cpu_model}, RAM={ram_total_gb}GB, NPU={'Yes' if npu_info.get('npu_available') else 'No'}")


def run_monitor_only(model_name: str, duration: float, config_dir: str, results_dir: str, wandb_logger: Optional[Any] = None) -> Dict[str, Any]:
    """Run background monitoring for `duration` seconds and optionally log to W&B.

    If `wandb_logger` is provided and available, the run will be started and aggregated
    metrics will be logged (average CPU/memory, sample count).
    """
    from .metrics_collector import SystemMonitor

    run_id = str(uuid.uuid4())
    start_time = datetime.datetime.now(datetime.timezone.utc).isoformat()

    print(f"Starting system monitoring for {duration} seconds...")
    monitor = SystemMonitor(track_process_name=None)

    # Simple progress indicator
    import time
    start_time_monitor = time.time()
    samples = []

    for i in range(int(duration)):
        remaining = int(duration) - i
        if remaining % 10 == 0 or i == 0:  # Update every 10 seconds or at start
            print(f"Monitoring progress: {i}/{int(duration)} seconds ({i/int(duration)*100:.1f}%) - {remaining} seconds remaining")
        sample = monitor.sample(run_id=run_id)
        samples.append(sample)
        time.sleep(1.0)

    print(f"Monitoring complete: collected {len(samples)} samples")

    # Create a minimal TestRun summary
    tr = {
        "run_id": run_id,
        "model_name": model_name,
        "start_time": start_time,
        "end_time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": "completed",
        "num_interactions_planned": 0,
        "num_interactions_completed": 0,
        "freeze_detected": False,
        "metrics_collected": len(samples),
    }

    # If a W&B logger is provided, log aggregated metrics
    if wandb_logger and getattr(wandb_logger, 'is_available', lambda: False)():
        # compute simple aggregates
        cpu_vals = [s.cpu_percent for s in samples if s.cpu_percent is not None]
        mem_vals = [s.memory_percent for s in samples if s.memory_percent is not None]
        agg = {
            'avg_cpu_percent': sum(cpu_vals) / len(cpu_vals) if cpu_vals else None,
            'avg_memory_percent': sum(mem_vals) / len(mem_vals) if mem_vals else None,
            'samples': len(samples),
        }
        try:
            # Call W&B methods only if they exist to support lightweight fakes/mocks
            start_run = getattr(wandb_logger, 'start_run', None)
            if callable(start_run):
                start_run(config={"model": model_name, "duration": duration})
            log_metrics = getattr(wandb_logger, 'log_metrics', None)
            if callable(log_metrics):
                log_metrics(agg)
            log_test_run = getattr(wandb_logger, 'log_test_run', None)
            if callable(log_test_run):
                # Convert datetime objects to strings for W&B serialization
                serializable_tr = json.loads(json.dumps(tr, default=str))
                log_test_run(serializable_tr)
            finish = getattr(wandb_logger, 'finish_run', None)
            if callable(finish):
                finish()
        except Exception:
            pass

    os.makedirs(os.path.join(results_dir, "test_runs"), exist_ok=True)
    out_path = os.path.join(results_dir, "test_runs", f"run_{run_id}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(tr, f, default=str, indent=2)

    # Generate compatibility report (single-run matrix)
    matrix = ReportGenerator.generate_compatibility_matrix([tr])
    reports_dir = os.path.join(results_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    json_path = os.path.join(reports_dir, f"compatibility_matrix_{timestamp}.json")
    PerformanceAnalyzer.save_json(json_path, matrix)

    md = ReportGenerator.generate_markdown(matrix)
    with open(os.path.join(reports_dir, f"compatibility_matrix_{timestamp}.md"), "w", encoding="utf-8") as f:
        f.write(md)

    return {"run": tr, "matrix": matrix}


def _input_yes_no(prompt: str, default: Optional[bool] = None) -> bool:
    """Parse a yes/no response from input with retries. Returns True for yes, False for no."""
    while True:
        val = input(prompt).strip().lower()
        if val in ("y", "yes"):
            return True
        if val in ("n", "no"):
            return False
        if val == "" and default is not None:
            return default
        print("Please answer 'y' or 'n'.")


def _input_float_optional(prompt: str) -> Optional[float]:
    """Read a float from input or return None if blank. Retries on invalid input."""
    while True:
        val = input(prompt).strip()
        if val == "":
            return None
        try:
            return float(val)
        except ValueError:
            print("Please enter a number (milliseconds) or leave blank.")


class InteractiveTestRunner:
    """Interactive test runner for manual Continue extension testing."""
    
    def __init__(self, model_name: str, config_dir: str = "config", results_dir: str = "results"):
        self.model_name = model_name
        self.config_dir = config_dir
        self.results_dir = results_dir
        self.monitor = SystemMonitor(track_process_name=None)
        self.freeze_detector = FreezeDetector()
    
    def run_interactive_test_session(self, num_interactions: int, verbose: bool = False) -> Dict[str, Any]:
        """Run an interactive test session with the specified number of interactions.
        
        Returns a dict with 'run' key containing TestRun data, or 'freeze_event' if freeze detected.
        """
        run_id = str(uuid.uuid4())
        start_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        # Start background monitoring
        stop_event = self.monitor.start_background_sampling(interval=1.0, run_id=run_id)
        
        interactions_record = []
        
        try:
            for i in range(1, num_interactions + 1):
                interaction_result = self._prompt_for_interaction(i, num_interactions)
                
                if interaction_result["success"]:
                    # Record successful interaction
                    self._record_interaction(interactions_record, i, interaction_result)
                    if verbose:
                        rt = interaction_result.get("response_time_ms")
                        print(f"  ✓ Recorded interaction {i} (rt={rt}ms)")
                else:
                    # Handle freeze detection
                    sample = self.monitor.sample(run_id=run_id)
                    fe = FreezeDetector.create_freeze_event(
                        run_id=run_id, 
                        interaction_id=str(i), 
                        metrics=sample, 
                        detection_method="user_report"
                    )
                    fe_path = fe.save(os.path.join(self.results_dir, "freeze_events"))
                    print(f"[!] FREEZE detected at interaction {i}. Diagnostics saved to: {sanitize_path_for_logging(fe_path)}")
                    stop_event.set()
                    return {"run": None, "freeze_event": fe.to_dict()}
        finally:
            stop_event.set()
        
        # Create TestRun result
        end_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
        tr = {
            "run_id": run_id,
            "model_name": self.model_name,
            "start_time": start_time,
            "end_time": end_time,
            "status": "completed",
            "num_interactions_planned": num_interactions,
            "num_interactions_completed": len(interactions_record),
            "freeze_detected": False,
            "metrics_collected": None,
            "interactions": interactions_record,
        }
        
        # Save test run
        os.makedirs(os.path.join(self.results_dir, "test_runs"), exist_ok=True)
        out_path = os.path.join(self.results_dir, "test_runs", f"run_{run_id}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(tr, f, default=str, indent=2)
        
        return {"run": tr}
    
    def _prompt_for_interaction(self, interaction_num: int, total_interactions: int) -> Dict[str, Any]:
        """Prompt user to perform an interaction and report the result.
        
        Returns a dict with 'success' boolean and optional 'response_time_ms'.
        """
        print(f"Interaction {interaction_num}/{total_interactions}: ")
        input("  - Send the message in Continue then press ENTER to continue...")
        
        success = _input_yes_no("  - Did Continue respond successfully? (y/n): ")
        
        result = {"success": success}
        
        if success:
            response_time = _input_float_optional("  - Response time in ms (approx, blank to skip): ")
            if response_time is not None:
                result["response_time_ms"] = response_time
        
        return result
    
    def _record_interaction(self, interactions_record: List[Dict[str, Any]], interaction_num: int, interaction_result: Dict[str, Any]) -> None:
        """Record a successful interaction in the interactions record list."""
        record = {
            "interaction_number": interaction_num,
            "success": True,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        
        if "response_time_ms" in interaction_result:
            record["duration_ms"] = interaction_result["response_time_ms"]
        
        interactions_record.append(record)


def run_interactive(model_name: str, interactions: int, config_dir: str, results_dir: str, verbose: bool = False, output_format: str = "json") -> Dict[str, Any]:
    run_id = str(uuid.uuid4())
    start_time = datetime.datetime.now(datetime.timezone.utc).isoformat()

    monitor = SystemMonitor(track_process_name=None)
    stop_event = monitor.start_background_sampling(interval=1.0, run_id=run_id)

    interactions_record: List[Dict[str, Any]] = []
    freeze_detector = FreezeDetector()

    try:
        for i in range(1, interactions + 1):
            print(f"Interaction {i}/{interactions}: ")
            input("  - Send the message in Continue then press ENTER to continue...")

            ok = _input_yes_no("  - Did Continue respond successfully? (y/n): ")
            if ok:
                rt_val = _input_float_optional("  - Response time in ms (approx, blank to skip): ")
                interactions_record.append({"interaction_number": i, "success": True, "response_time_ms": rt_val})
                if verbose:
                    print(f"  ✓ Recorded interaction {i} (rt={rt_val})")
            else:
                # create freeze event and stop
                sample = monitor.sample(run_id=run_id)
                fe = FreezeDetector.create_freeze_event(run_id=run_id, interaction_id=str(i), metrics=sample, detection_method="user_report")
                fe_path = fe.save(os.path.join(results_dir, "freeze_events"))
                print(f"[!] FREEZE detected at interaction {i}. Diagnostics saved to: {sanitize_path_for_logging(fe_path)}")
                stop_event.set()
                return {"run": None, "freeze_event": fe.to_dict()}
    finally:
        stop_event.set()

    end_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
    tr = {
        "run_id": run_id,
        "model_name": model_name,
        "start_time": start_time,
        "end_time": end_time,
        "status": "completed",
        "num_interactions_planned": interactions,
        "num_interactions_completed": len(interactions_record),
        "freeze_detected": False,
        "metrics_collected": None,
        "interactions": interactions_record,
    }

    os.makedirs(os.path.join(results_dir, "test_runs"), exist_ok=True)
    out_path = os.path.join(results_dir, "test_runs", f"run_{run_id}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(tr, f, default=str, indent=2)

    matrix = ReportGenerator.generate_compatibility_matrix([tr])
    reports_dir = os.path.join(results_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")

    if output_format in ("json", "all"):
        json_path = os.path.join(reports_dir, f"compatibility_matrix_{timestamp}.json")
        ReportGenerator.save_json(json_path, matrix)
    if output_format in ("md", "all", "markdown"):
        md = ReportGenerator.generate_markdown(matrix)
        with open(os.path.join(reports_dir, f"compatibility_matrix_{timestamp}.md"), "w", encoding="utf-8") as f:
            f.write(md)
    if output_format in ("csv", "all"):
        csv_out = ReportGenerator.generate_csv(matrix)
        with open(os.path.join(reports_dir, f"compatibility_matrix_{timestamp}.csv"), "w", encoding="utf-8") as f:
            f.write(csv_out)

    if verbose:
        print(f"Interactive run complete. Results saved to {reports_dir}")

    result_obj = {"run": tr, "matrix": matrix}
    if verbose:
        print("DEBUG: returning result_obj with keys:", list(result_obj.keys()))
    return result_obj




def main(argv: Optional[List[str]] = None) -> int:
    """CLI entrypoint for test_runner.

    Supported flags:
    - --model MODEL (required)
    - --monitor-only (run background monitor for --duration seconds)
    - --interactive (manual guided mode)
    - --duration N (seconds for monitor-only)
    - --format (json|md|csv|all)
    - --wandb (log results to Weights & Biases if available)
    - --verbose (enable verbose output)
    """
    # Check dependencies
    check_dependencies()
    p = argparse.ArgumentParser(prog="test_runner.py")
    p.add_argument("--model", required=True)
    p.add_argument("--interactions", type=int, default=10)
    p.add_argument("--interactive", action="store_true")
    p.add_argument("--monitor-only", action="store_true")
    p.add_argument("--duration", type=int, default=60, help="Duration in seconds for monitor-only mode")
    p.add_argument("--format", choices=["json", "md", "csv", "all"], default="json", help="Report output format")
    p.add_argument("--wandb", action="store_true", help="Log run to Weights & Biases if available")
    p.add_argument("--no-wandb", action="store_true", help="Disable Weights & Biases logging even if available")
    p.add_argument("--offline-wandb", action="store_true", help="Run W&B in offline mode (store data locally for later sync)")
    p.add_argument("--verbose", action="store_true", help="Verbose output")
    p.add_argument("--debug", action="store_true", help="Debug output (includes verbose)")
    p.add_argument("--config-dir", default=os.path.join(os.path.dirname(__file__), "config"))
    p.add_argument("--results-dir", default=os.path.join(os.path.dirname(__file__), "results"))

    args = p.parse_args(argv)

    # Setup logging and W&B logger
    wandb_logger = setup_common_args_and_logging(p, args)

    # Validate model exists in configuration
    try:
        config_loader = ConfigLoader(args.config_dir)
        models_config = config_loader.load_models_config()
        models_list = models_config.get("models", [])
        model_names = [model.get("name") for model in models_list if isinstance(model, dict)]
        if args.model not in model_names:
            logger.error(f"Model '{args.model}' not found in configuration")
            logger.error(f"Available models: {model_names}")
            logger.error("Check your models.yaml file or use --config-dir to specify the correct config directory")
            return 1
    except FileNotFoundError:
        config_path = os.path.join(args.config_dir, 'models.yaml')
        logger.error(f"Configuration file not found: {sanitize_path_for_logging(config_path)}")
        logger.error("Please ensure models.yaml exists in the config directory")
        return 1
    except Exception as e:
        logger.error(f"Failed to validate model configuration: {e}")
        return 1

    if args.monitor_only:
        result = run_monitor_only(args.model, args.duration, args.config_dir, args.results_dir, wandb_logger=wandb_logger)
        # run_monitor_only handles W&B logging if wandb_logger was provided
        if args.verbose:
            print("Monitor run complete. Summary:")
            print(json.dumps(result["run"], indent=2))
        return 0

    if args.interactive:
        result = run_interactive(args.model, args.interactions, args.config_dir, args.results_dir, verbose=args.verbose, output_format=args.format)
        if result.get("freeze_event"):
            # Optionally log freeze event
            if args.wandb and wandb_logger and getattr(wandb_logger, 'is_available', lambda: False)():
                log_freeze = getattr(wandb_logger, 'log_freeze_event', None)
                if callable(log_freeze):
                    try:
                        # Convert datetime objects to strings for W&B serialization
                        serializable_freeze = json.loads(json.dumps(result["freeze_event"], default=str))
                        log_freeze(serializable_freeze)
                    except Exception:
                        pass
            print("Freeze detected during interactive session. See diagnostics.")
            return 2
        if args.wandb and wandb_logger and getattr(wandb_logger, 'is_available', lambda: False)():
            log_test_run = getattr(wandb_logger, 'log_test_run', None)
            if callable(log_test_run):
                try:
                    # Convert datetime objects to strings for W&B serialization
                    serializable_run = json.loads(json.dumps(result["run"], default=str))
                    log_test_run(serializable_run)
                except Exception:
                    pass
        if args.verbose:
            print("Interactive run complete. Summary:")
            print(json.dumps(result["run"], indent=2))
        return 0

    p.print_help()
    return 1


class InteractiveTestRunner:
    """Interactive test runner for manual Continue compatibility testing."""

    def __init__(self, config_dir: str, results_dir: str):
        self.config_dir = config_dir
        self.results_dir = results_dir
        self.config_loader = ConfigLoader(config_dir)
        self.monitor = SystemMonitor()
        self.freeze_detector = FreezeDetector()

    def run_interactive_test_session(self, model_name: str, max_interactions: int = 10) -> Dict[str, Any]:
        """Run an interactive test session for the given model."""
        print(f"Starting interactive test for model: {model_name}")
        print(f"Max interactions: {max_interactions}")
        print("Follow the prompts to test Continue compatibility.")

        interactions = []
        for i in range(max_interactions):
            if not self._prompt_for_interaction(i + 1):
                break
            interaction = self._record_interaction(i + 1, f"Test interaction {i+1}")
            interactions.append(interaction)

        # Generate summary
        freeze_count = sum(1 for interaction in interactions if interaction.get("freeze_detected"))
        result = {
            "model_name": model_name,
            "interactions_completed": len(interactions),
            "freeze_detected": freeze_count > 0,
            "freeze_count": freeze_count,
            "summary": f"Completed {len(interactions)} interactions, {freeze_count} freezes detected"
        }
        return result

    def _prompt_for_interaction(self, interaction_num: int) -> bool:
        """Prompt user to perform an interaction."""
        response = input(f"\nInteraction {interaction_num}: Press Enter to start, or 'q' to quit: ")
        return response.lower() != 'q'

    def _record_interaction(self, interaction_num: int, description: str) -> Dict[str, Any]:
        """Record a test interaction."""
        # Sample metrics before interaction
        pre_metrics = self.monitor.sample_once()
        self._display_npu_metrics(pre_metrics, "Pre-interaction")

        start_time = time.time()
        # Simulate waiting for user
        input("Perform the interaction in Continue, then press Enter when done: ")
        end_time = time.time()

        # Sample metrics after interaction
        post_metrics = self.monitor.sample_once()
        self._display_npu_metrics(post_metrics, "Post-interaction")

        # Check for freezes
        freeze_event = self.freeze_detector.detect_from_timeout(start_time, 300, interaction_num)
        if freeze_event:
            print(f"⚠️  FREEZE DETECTED: {freeze_event.diagnostics.get('user_notes', 'Unknown')}")
            # Save freeze event
            freeze_dir = os.path.join(self.results_dir, "freeze_events")
            freeze_event.save(freeze_dir)
            print(f"Freeze event saved to: {sanitize_path_for_logging(freeze_event.saved_path)}")

        return {
            "interaction_num": interaction_num,
            "description": description,
            "duration_ms": (end_time - start_time) * 1000,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "pre_metrics": pre_metrics.to_dict(),
            "post_metrics": post_metrics.to_dict(),
            "freeze_detected": freeze_event is not None,
            "freeze_event_id": freeze_event.id if freeze_event else None
        }

    def _display_npu_metrics(self, metrics: SystemMetrics, label: str) -> None:
        """Display NPU metrics in a user-friendly format."""
        if not metrics.npu_metrics:
            print(f"{label} NPU: No NPU detected or monitoring unavailable")
            return

        npu = metrics.npu_metrics
        print(f"{label} NPU Metrics:")
        print(f"  Device count: {npu.get('device_count', 'N/A')}")
        print(f"  Utilization: {npu.get('utilization_percent', 'N/A')}%")
        print(f"  GOPS: {npu.get('gops', 'N/A')}")
        print(f"  Instruction buffer: {npu.get('instr_bo_kb', 'N/A')} KB")
        print(f"  Command submissions: {npu.get('command_submissions', 'N/A')}")
        print(f"  Active contexts: {len(npu.get('contexts', []))}")

        # Show warning if utilization is 0%
        if npu.get('utilization_percent') == 0:
            print("  ⚠️  WARNING: NPU utilization is 0% - model may not be using hardware acceleration!")


class ScheduledTestRunner:
    """Automated test runner for continuous model stability testing."""

    def __init__(self, config_loader: ConfigLoader, results_dir: str = RESULTS_DIR_DEFAULT, wandb_logger: Optional[Any] = None):
        self.config_loader = config_loader
        self.results_dir = results_dir
        self.continuous_dir = os.path.join(results_dir, "continuous")
        self.scheduler = schedule.Scheduler()
        self.running = False
        self.stop_event = threading.Event()
        self.wandb_logger = wandb_logger

        # Ensure continuous results directory exists
        os.makedirs(self.continuous_dir, exist_ok=True)

    def add_schedule(self, cron_expression: str, models: List[str] = None, scenarios: List[str] = None) -> None:
        """Add a scheduled test run.

        Args:
            cron_expression: Cron-style expression (e.g., "0 */4 * * *" for every 4 hours)
            models: List of model names to test (None = all models)
            scenarios: List of scenario names to test (None = all scenarios)
        """
        def job():
            try:
                self._run_scheduled_test(models, scenarios)
            except Exception as e:
                logger.error(f"Scheduled test failed: {e}")

        # Parse cron expression and schedule
        # For simplicity, support basic cron-like syntax
        parts = cron_expression.split()
        if len(parts) != 5:
            raise ValueError("Invalid cron expression. Expected 5 space-separated parts.")

        minute, hour, day, month, day_of_week = parts

        if minute == "*" and hour == "*" and day == "*" and month == "*" and day_of_week == "*":
            # Every minute - for testing
            self.scheduler.every().minute.do(job)
        elif minute == "0" and hour.startswith("*/"):
            # Every N hours
            hours = int(hour.split("/")[1])
            self.scheduler.every(hours).hours.do(job)
        elif minute == "0" and hour == "*" and day == "*" and month == "*" and day_of_week == "*":
            # Every hour
            self.scheduler.every().hour.do(job)
        elif minute == "0" and hour == "0" and day == "*" and month == "*" and day_of_week == "*":
            # Daily at midnight
            self.scheduler.every().day.at("00:00").do(job)
        else:
            raise ValueError(f"Unsupported cron expression: {cron_expression}")

        logger.info(f"Added scheduled test: {cron_expression}")

    def run_scheduled(self) -> None:
        """Run the scheduler in a loop until stopped."""
        self.running = True
        logger.info("Starting scheduled test runner...")

        try:
            while not self.stop_event.is_set():
                self.scheduler.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Scheduled test runner stopped by user")
        finally:
            self.running = False

    def stop(self) -> None:
        """Stop the scheduled test runner."""
        logger.info("Stopping scheduled test runner...")
        self.stop_event.set()

    def _run_scheduled_test(self, models: List[str] = None, scenarios: List[str] = None) -> None:
        """Execute a single scheduled test run."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        run_id = f"scheduled_{timestamp}_{uuid.uuid4().hex[:8]}"

        logger.info(f"Starting scheduled test run: {run_id}")

        # Create timestamp-based directory
        date_dir = datetime.datetime.now().strftime("%Y-%m-%d")
        run_dir = os.path.join(self.continuous_dir, date_dir, run_id)
        os.makedirs(run_dir, exist_ok=True)

        # Get models and scenarios to test
        if models is None:
            models = list(self.config_loader.models.keys())
        if scenarios is None:
            scenarios = list(self.config_loader.scenarios.keys())

        # Run tests for each model/scenario combination
        for model_name in models:
            for scenario_name in scenarios:
                try:
                    self._run_single_test(model_name, scenario_name, run_dir, run_id)
                except Exception as e:
                    logger.error(f"Test failed for {model_name}/{scenario_name}: {e}")

        logger.info(f"Completed scheduled test run: {run_id}")

    def _run_single_test(self, model_name: str, scenario_name: str, run_dir: str, run_id: str) -> None:
        """Run a single model/scenario test."""
        logger.info(f"Testing {model_name} with {scenario_name}")

        # Get model and scenario configs
        model_config = self.config_loader.get_model(model_name)
        scenario_config = self.config_loader.get_scenario(scenario_name)

        # Create test runner for this specific test
        runner = InteractiveTestRunner(self.config_loader, self.results_dir)

        # Create test run
        test_run = TestRun(
            id=f"{run_id}_{model_name}_{scenario_name}",
            model_name=model_name,
            scenario_name=scenario_name,
            start_time=datetime.datetime.now(datetime.timezone.utc),
            status="running"
        )

        # Run the test (simplified - would need to adapt based on scenario type)
        # For now, just run a basic interactive session
        try:
            # This would need to be adapted to run non-interactively
            # For now, we'll simulate a basic test
            test_run.end_time = datetime.datetime.now(datetime.timezone.utc)
            test_run.status = "completed"
            test_run.num_interactions_completed = scenario_config.get("interactions", 5)

            # Save results
            result_path = os.path.join(run_dir, f"{model_name}_{scenario_name}.json")
            with open(result_path, "w", encoding="utf-8") as f:
                json.dump({
                    "test_run": test_run.to_dict(),
                    "model_config": model_config,
                    "scenario_config": scenario_config,
                    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
                }, f, indent=2, default=str)

            # Log to W&B if available
            if self.wandb_logger:
                try:
                    log_test_run = getattr(self.wandb_logger, 'log_test_run', None)
                    if callable(log_test_run):
                        log_test_run({
                            "model_name": model_name,
                            "scenario_name": scenario_name,
                            "status": test_run.status,
                            "interactions_completed": test_run.num_interactions_completed,
                            "start_time": test_run.start_time.isoformat() if test_run.start_time else None,
                            "end_time": test_run.end_time.isoformat() if test_run.end_time else None,
                            "run_id": run_id
                        })
                except Exception as e:
                    logger.warning(f"Failed to log to W&B: {e}")

            logger.info(f"Saved test results to: {result_path}")

        except Exception as e:
            test_run.status = "failed"
            test_run.error_message = str(e)
            logger.error(f"Test failed: {e}")


class ScheduledTestRunner:
    """Automated test runner that executes tests on a schedule using cron expressions."""

    def __init__(self, config_loader: ConfigLoader, results_dir: str, wandb_logger: Optional[Any] = None):
        """Initialize the scheduled test runner."""
        self.config_loader = config_loader
        self.results_dir = results_dir
        self.schedule = schedule.Scheduler()
        self.running = False
        self.notification_handler = None
        self.wandb_logger = wandb_logger

        # Initialize notification handler if config exists
        notification_config_path = os.path.join(os.path.dirname(results_dir), "config", "notifications.yaml")
        if os.path.exists(notification_config_path):
            try:
                with open(notification_config_path, "r", encoding="utf-8") as f:
                    notification_config = yaml.safe_load(f)
                from .report_generator import NotificationHandler
                self.notification_handler = NotificationHandler(notification_config)
                logger.info("Notification handler initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize notification handler: {e}")

    def add_schedule(self, cron_expression: str) -> None:
        """Add a scheduled test run using cron expression."""
        try:
            # Parse cron expression (basic support for common patterns)
            self._parse_cron_expression(cron_expression)
            self.schedule.every().day.at("00:00").do(self._run_scheduled_test)  # Placeholder
            # TODO: Implement full cron parsing
            logger.info(f"Added schedule: {cron_expression}")
        except Exception as e:
            raise ValueError(f"Invalid cron expression '{cron_expression}': {e}")

    def _parse_cron_expression(self, cron: str) -> None:
        """Parse cron expression and configure schedule."""
        # Basic cron parsing - for now just support simple hourly/daily patterns
        parts = cron.strip().split()
        if len(parts) != 5:
            raise ValueError("Cron expression must have 5 parts: minute hour day month weekday")

        minute, hour, day, month, weekday = parts

        # Handle common patterns
        if minute == "0" and hour.startswith("*/"):
            # Every N hours
            hours = int(hour[2:])
            self.schedule.every(hours).hours.do(self._run_scheduled_test)
        elif minute == "0" and hour.isdigit():
            # Daily at specific hour
            self.schedule.every().day.at(f"{hour.zfill(2)}:00").do(self._run_scheduled_test)
        else:
            # For complex expressions, run daily at midnight as fallback
            logger.warning(f"Complex cron expression '{cron}' not fully supported, running daily at midnight")
            self.schedule.every().day.at("00:00").do(self._run_scheduled_test)

    def run_scheduled(self) -> None:
        """Run the scheduled test execution loop."""
        self.running = True
        logger.info("Starting scheduled test execution")

        try:
            while self.running:
                self.schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Scheduled execution interrupted")
        finally:
            self.running = False
            logger.info("Scheduled test execution stopped")

    def stop(self) -> None:
        """Stop the scheduled execution."""
        self.running = False
        logger.info("Stopping scheduled test execution")

    def _run_scheduled_test(self) -> None:
        """Execute a scheduled test run."""
        try:
            logger.info("Executing scheduled test run")

            # Get all configured models
            try:
                models_config = self.config_loader.load_models_config()
            except FileNotFoundError:
                logger.error("models.yaml configuration file not found")
                config_path = os.path.join(self.config_loader.config_dir, 'models.yaml')
                logger.error(f"Expected location: {sanitize_path_for_logging(config_path)}")
                logger.error("Please create the models.yaml file with your model configurations")
                return
            except Exception as e:
                logger.error(f"Failed to load models configuration: {e}")
                logger.error("Check that models.yaml exists and is properly formatted YAML")
                return

            models_list = models_config.get("models", [])
            if not models_list:
                logger.warning("No models configured for scheduled testing")
                logger.warning("Add model configurations to models.yaml to enable scheduled testing")
                return

            # Run tests for all models
            all_results = []
            for model in models_list:
                if not isinstance(model, dict) or "name" not in model:
                    logger.warning(f"Skipping invalid model configuration: {model}")
                    continue
                model_name = model["name"]
                try:
                    logger.info(f"Testing model: {model_name}")

                    # Run monitor-only test (automated)
                    result = run_monitor_only(
                        model_name=model_name,
                        duration=300,  # 5 minutes
                        config_dir=self.config_loader.config_dir,
                        results_dir=self.results_dir
                    )

                    if result:
                        all_results.append(result)

                        # Save result
                        result_path = os.path.join(self.results_dir, f"scheduled_{model_name}_{int(time.time())}.json")
                        with open(result_path, "w", encoding="utf-8") as f:
                            json.dump(result, f, indent=2)

                        # Log to W&B if available
                        if self.wandb_logger:
                            try:
                                log_test_run = getattr(self.wandb_logger, 'log_test_run', None)
                                if callable(log_test_run):
                                    log_test_run(result.get("run", {}))
                            except Exception as e:
                                logger.warning(f"Failed to log scheduled test to W&B: {e}")

                        logger.info(f"Scheduled test completed for {model_name}")

                except Exception as e:
                    logger.error(f"Scheduled test failed for {model_name}: {e}")

            # Analyze trends and send notifications
            if all_results and self.notification_handler:
                self._analyze_and_notify(all_results)

        except Exception as e:
            logger.error(f"Scheduled test execution failed: {e}")

    def _analyze_and_notify(self, test_results: List[Dict[str, Any]]) -> None:
        """Analyze test results and send notifications if needed."""
        try:
            from .report_generator import TrendAnalyzer, PerformanceAnalyzer

            # Load historical data
            historical_runs = TrendAnalyzer.load_runs_from_directory(self.results_dir)

            # Analyze trends
            trend_analysis = TrendAnalyzer.analyze_historical_runs(historical_runs, days_back=7)

            # Analyze performance metrics
            performance_analysis = PerformanceAnalyzer.analyze_model_performance(historical_runs + test_results)

            # Log performance metrics to W&B
            if self.wandb_logger:
                try:
                    log_performance = getattr(self.wandb_logger, 'log_performance_metrics', None)
                    if callable(log_performance):
                        log_performance(performance_analysis)
                except Exception as e:
                    logger.warning(f"Failed to log performance metrics to W&B: {e}")

            # Check for degradation
            degradation_alerts = {}
            for result in test_results:
                model_name = result.get("model_name", "unknown")
                model_runs = [r for r in historical_runs if r.get("model_name") == model_name]
                if len(model_runs) >= 5:
                    degradation = TrendAnalyzer.detect_degradation(model_runs)
                    if degradation.get("degraded"):
                        degradation_alerts[model_name] = degradation

            # Check for improvements
            improvement_alerts = {}
            for result in test_results:
                model_name = result.get("model_name", "unknown")
                model_runs = [r for r in historical_runs if r.get("model_name") == model_name]
                if len(model_runs) >= 5:
                    improvement = TrendAnalyzer.detect_improvements(model_runs)
                    if improvement.get("improved"):
                        improvement_alerts[model_name] = improvement

            # Send notifications
            for model, degradation in degradation_alerts.items():
                self.notification_handler.notify_degradation(model, degradation)

            for model, improvement in improvement_alerts.items():
                self.notification_handler.notify_improvement(model, improvement)

            # Send completion notification
            summary = {
                "total_runs": len(test_results),
                "successful_runs": len([r for r in test_results if r.get("status") == "completed"]),
                "failed_runs": len([r for r in test_results if r.get("status") != "completed"]),
                "duration_minutes": 5,  # Approximate
                "degradation_alerts": len(degradation_alerts),
                "improvement_alerts": len(improvement_alerts)
            }
            self.notification_handler.notify_test_completion(summary)

        except Exception as e:
            logger.error(f"Trend analysis and notification failed: {e}")


def main() -> int:
    """Main CLI entry point for test runner."""
    parser = argparse.ArgumentParser(
        description="Continue Extension Model Testing Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive testing
  python test_runner.py --model qwen3:0.6b --interactive

  # Scheduled testing (every 4 hours)
  python test_runner.py --schedule "0 */4 * * *"

  # Monitor-only mode
  python test_runner.py --monitor-only --duration 60
        """
    )

    parser.add_argument(
        "--model",
        help="Model name to test (from models.yaml)"
    )

    parser.add_argument(
        "--scenario",
        help="Test scenario name (from test_scenarios.yaml)"
    )

    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode (guided testing)"
    )

    parser.add_argument(
        "--monitor-only",
        action="store_true",
        help="Run system monitoring only (no model testing)"
    )

    parser.add_argument(
        "--schedule",
        help="Run scheduled tests with cron expression (e.g., '0 */4 * * *' for every 4 hours)"
    )

    parser.add_argument(
        "--duration",
        type=int,
        default=300,
        help="Test duration in seconds (default: 300)"
    )

    parser.add_argument(
        "--interactions",
        type=int,
        default=5,
        help="Number of interactions to test (default: 5)"
    )

    parser.add_argument(
        "--config-dir",
        default=os.path.join(os.path.dirname(__file__), "config"),
        help="Configuration directory"
    )

    parser.add_argument(
        "--results-dir",
        default=RESULTS_DIR_DEFAULT,
        help="Results directory"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Debug output (includes verbose)"
    )

    parser.add_argument(
        "--wandb",
        action="store_true",
        help="Log results to Weights & Biases if available"
    )

    parser.add_argument(
        "--no-wandb",
        action="store_true",
        help="Disable Weights & Biases logging even if available"
    )

    parser.add_argument(
        "--offline-wandb",
        action="store_true",
        help="Run W&B in offline mode (store data locally for later sync)"
    )

    args = parser.parse_args()

    # Check dependencies before proceeding
    check_dependencies()

    # Setup logging and W&B logger
    wandb_logger = setup_common_args_and_logging(parser, args)

    try:
        # Load configuration
        try:
            config_loader = ConfigLoader(args.config_dir)
        except FileNotFoundError as e:
            logger.error(f"Configuration directory not found: {sanitize_path_for_logging(args.config_dir)}")
            logger.error("Please ensure the config directory exists and contains required YAML files (models.yaml, test_scenarios.yaml, hardware.yaml)")
            logger.error(f"Expected config files in: {sanitize_path_for_logging(args.config_dir)}")
            return 1
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            logger.error("Check that YAML files are properly formatted and accessible")
            return 1

        # Validate model if specified
        if args.model:
            try:
                models_config = config_loader.load_models_config()
                models_list = models_config.get("models", [])
                model_names = [model.get("name") for model in models_list if isinstance(model, dict)]
                if args.model not in model_names:
                    logger.error(f"Model '{args.model}' not found in configuration")
                    logger.error(f"Available models: {model_names}")
                    logger.error("Check your models.yaml file or use --config-dir to specify the correct config directory")
                    return 1
            except Exception as e:
                logger.error(f"Failed to validate model configuration: {e}")
                return 1

        if args.schedule:
            # Scheduled mode
            logger.info(f"Starting scheduled test runner with schedule: {args.schedule}")

            scheduled_runner = ScheduledTestRunner(config_loader, args.results_dir, wandb_logger)
            scheduled_runner.add_schedule(args.schedule)

            # Handle graceful shutdown
            import signal
            def signal_handler(signum, frame):
                logger.info("Received shutdown signal")
                scheduled_runner.stop()

            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)

            try:
                scheduled_runner.run_scheduled()
            except KeyboardInterrupt:
                pass

            return 0

        elif args.monitor_only:
            # Monitor-only mode
            result = run_monitor_only(
                model_name="system_monitor_only",
                duration=args.duration,
                config_dir=args.config_dir,
                results_dir=args.results_dir,
                wandb_logger=wandb_logger
            )
            # Print summary
            if result.get("metrics_collected", 0) > 0:
                print(f"Collected {result['metrics_collected']} monitoring samples")
            return 0

        elif args.interactive or args.model:
            # Interactive testing mode
            if not args.model:
                print("Error: --model is required for interactive testing")
                return 1

            logger.info(f"Starting interactive test for model: {args.model}")

            runner = InteractiveTestRunner(args.model, args.config_dir, args.results_dir)
            return runner.run_interactive_test_session(
                num_interactions=args.interactions,
                verbose=args.verbose
            )

        else:
            parser.print_help()
            return 1

    except Exception as e:
        logger.error(f"Test runner failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    # Allow running from CLI
    raise SystemExit(main())

