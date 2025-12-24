#!/usr/bin/env python3
"""
AMD AI Max+ 395 ROCm Production Deployment Validation Script

This script validates a complete production deployment of the AMD AI Max+ 395
ROCm testing framework, ensuring all components are properly installed and
functioning correctly.

Usage:
    python deployment_validation.py [--verbose] [--quick] [--report-dir DIR]

Options:
    --verbose, -v    Enable verbose output
    --quick, -q      Run only critical validation checks
    --report-dir DIR Save validation report to specified directory
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import requests
import psutil

class DeploymentValidator:
    """Validates AMD AI Max+ 395 ROCm production deployment."""

    def __init__(self, verbose: bool = False, quick: bool = False):
        self.verbose = verbose
        self.quick = quick
        self.results = {
            "timestamp": time.time(),
            "hostname": self._get_hostname(),
            "validation_checks": [],
            "overall_status": "unknown",
            "summary": {}
        }

    def _get_hostname(self) -> str:
        """Get system hostname."""
        try:
            import platform
            return platform.node()
        except:
            return "unknown"

    def log(self, message: str, level: str = "info") -> None:
        """Log a message if verbose mode is enabled."""
        if self.verbose or level in ["error", "warning"]:
            timestamp = time.strftime("%H:%M:%S")
            print(f"[{timestamp}] {level.upper()}: {message}")

    def run_check(self, name: str, check_func, *args, **kwargs) -> Dict[str, Any]:
        """Run a validation check and record results."""
        self.log(f"Running check: {name}")

        check_result = {
            "name": name,
            "status": "unknown",
            "message": "",
            "details": {},
            "duration": 0
        }

        start_time = time.time()
        try:
            result = check_func(*args, **kwargs)
            check_result.update(result)
            check_result["status"] = result.get("status", "unknown")
            check_result["message"] = result.get("message", "")
            check_result["details"] = result.get("details", {})

        except Exception as e:
            check_result["status"] = "error"
            check_result["message"] = f"Check failed with exception: {str(e)}"
            self.log(f"Check '{name}' failed: {e}", "error")

        check_result["duration"] = time.time() - start_time
        self.results["validation_checks"].append(check_result)

        status_emoji = {"pass": "✅", "fail": "❌", "warning": "⚠️", "error": "💥", "unknown": "❓"}
        emoji = status_emoji.get(check_result["status"], "❓")
        self.log(f"Check '{name}': {emoji} {check_result['message']}")

        return check_result

    def check_hardware_requirements(self) -> Dict[str, Any]:
        """Check hardware requirements for AMD AI Max+ 395."""
        result = {"status": "pass", "message": "Hardware requirements met", "details": {}}

        try:
            # Check CPU
            cpu_count = psutil.cpu_count(logical=True)
            cpu_physical = psutil.cpu_count(logical=False)
            result["details"]["cpu_logical_cores"] = cpu_count
            result["details"]["cpu_physical_cores"] = cpu_physical

            if cpu_count < 16:
                result["status"] = "warning"
                result["message"] = f"CPU has {cpu_count} logical cores, recommend 16+"

            # Check RAM
            ram_gb = psutil.virtual_memory().total / (1024**3)
            result["details"]["ram_gb"] = round(ram_gb, 1)

            if ram_gb < 32:
                result["status"] = "fail"
                result["message"] = f"Insufficient RAM: {ram_gb:.1f}GB, require 32GB+"

            # Check GPU via ROCm
            try:
                gpu_result = subprocess.run(
                    ["rocm-smi", "--showproductname", "--showvram"],
                    capture_output=True, text=True, timeout=10
                )

                if gpu_result.returncode == 0:
                    gpu_output = gpu_result.stdout
                    result["details"]["rocm_output"] = gpu_output.strip()

                    # Check for AMD Radeon RX 9100
                    if "Radeon RX 9100" in gpu_output:
                        result["details"]["gpu_model"] = "AMD Radeon RX 9100 (AI Max+ 395)"
                    else:
                        result["status"] = "warning"
                        result["message"] = "AMD Radeon RX 9100 not detected"

                    # Check VRAM (look for 128GB)
                    if "128" in gpu_output and "GB" in gpu_output:
                        result["details"]["vram_detected"] = "128GB"
                    else:
                        result["status"] = "warning"
                        result["message"] = "128GB VRAM not confirmed"
                else:
                    result["status"] = "fail"
                    result["message"] = "ROCm GPU detection failed"

            except (subprocess.TimeoutExpired, FileNotFoundError):
                result["status"] = "fail"
                result["message"] = "ROCm tools not available"

        except Exception as e:
            result["status"] = "error"
            result["message"] = f"Hardware check failed: {str(e)}"

        return result

    def check_rocm_drivers(self) -> Dict[str, Any]:
        """Check ROCm driver installation and version."""
        result = {"status": "pass", "message": "ROCm drivers OK", "details": {}}

        try:
            # Check rocm-smi version
            version_result = subprocess.run(
                ["rocm-smi", "--version"],
                capture_output=True, text=True, timeout=5
            )

            if version_result.returncode == 0:
                version_output = version_result.stdout.strip()
                result["details"]["rocm_version"] = version_output

                # Check version is 7.1.1 or later
                if "7.1.1" in version_output or "7.2" in version_output or "8." in version_output:
                    result["message"] = f"ROCm version OK: {version_output}"
                else:
                    result["status"] = "warning"
                    result["message"] = f"ROCm version may be outdated: {version_output}"
            else:
                result["status"] = "fail"
                result["message"] = "rocm-smi command failed"

            # Test GPU communication
            gpu_test = subprocess.run(
                ["rocm-smi", "--showid"],
                capture_output=True, text=True, timeout=5
            )

            if gpu_test.returncode == 0:
                result["details"]["gpu_communication"] = "OK"
            else:
                result["status"] = "fail"
                result["message"] = "GPU communication failed"

        except (subprocess.TimeoutExpired, FileNotFoundError):
            result["status"] = "fail"
            result["message"] = "ROCm tools not found in PATH"

        return result

    def check_python_environment(self) -> Dict[str, Any]:
        """Check Python environment and dependencies."""
        result = {"status": "pass", "message": "Python environment OK", "details": {}}

        try:
            import platform
            python_version = platform.python_version_tuple()
            version_str = f"{python_version[0]}.{python_version[1]}.{python_version[2]}"
            result["details"]["python_version"] = version_str

            major, minor = int(python_version[0]), int(python_version[1])
            if not (3, 10) <= (major, minor) <= (3, 13):
                result["status"] = "fail"
                result["message"] = f"Python {version_str} not supported (require 3.10-3.13)"

            # Check required packages
            required_packages = ["pytest", "openai", "psutil", "requests"]
            missing_packages = []

            for package in required_packages:
                try:
                    __import__(package)
                    result["details"][f"{package}_installed"] = True
                except ImportError:
                    missing_packages.append(package)
                    result["details"][f"{package}_installed"] = False

            if missing_packages:
                result["status"] = "fail"
                result["message"] = f"Missing required packages: {', '.join(missing_packages)}"

        except Exception as e:
            result["status"] = "error"
            result["message"] = f"Python environment check failed: {str(e)}"

        return result

    def check_lemonade_server(self) -> Dict[str, Any]:
        """Check Lemonade Server installation and connectivity."""
        result = {"status": "pass", "message": "Lemonade Server OK", "details": {}}

        server_url = "http://localhost:8000/api/v1"

        try:
            # Test basic connectivity
            response = requests.get(f"{server_url}/models", timeout=10)

            if response.status_code == 200:
                result["details"]["server_response"] = "OK"
                result["details"]["response_code"] = response.status_code

                # Parse models response
                try:
                    models_data = response.json()
                    model_count = len(models_data.get("data", []))
                    result["details"]["loaded_models"] = model_count

                    if model_count == 0:
                        result["status"] = "warning"
                        result["message"] = "No models loaded in Lemonade Server"
                    else:
                        result["message"] = f"Lemonade Server OK with {model_count} model(s) loaded"

                except json.JSONDecodeError:
                    result["status"] = "warning"
                    result["message"] = "Server responded but returned invalid JSON"

            else:
                result["status"] = "fail"
                result["message"] = f"Server returned status code {response.status_code}"

        except requests.exceptions.ConnectionError:
            result["status"] = "fail"
            result["message"] = "Cannot connect to Lemonade Server"

        except requests.exceptions.Timeout:
            result["status"] = "fail"
            result["message"] = "Lemonade Server connection timeout"

        except Exception as e:
            result["status"] = "error"
            result["message"] = f"Server check failed: {str(e)}"

        return result

    def check_test_framework(self) -> Dict[str, Any]:
        """Check testing framework installation and basic functionality."""
        result = {"status": "pass", "message": "Test framework OK", "details": {}}

        try:
            # Check if we're in the right directory
            current_dir = Path.cwd()
            test_dir = current_dir / "tests" / "rocm_max395"

            if not test_dir.exists():
                result["status"] = "fail"
                result["message"] = f"Test directory not found: {test_dir}"
                return result

            result["details"]["test_directory"] = str(test_dir)

            # Check configuration files
            config_files = [
                "conftest.py",
                "fixtures/models_config.json",
                "fixtures/multi_model_configs.json",
                "fixtures/rag_scenarios.json"
            ]

            missing_configs = []
            for config_file in config_files:
                config_path = test_dir / config_file
                if config_path.exists():
                    result["details"][f"{config_file}_exists"] = True
                else:
                    missing_configs.append(config_file)
                    result["details"][f"{config_file}_exists"] = False

            if missing_configs:
                result["status"] = "fail"
                result["message"] = f"Missing configuration files: {', '.join(missing_configs)}"

            # Test framework imports
            try:
                sys.path.insert(0, str(current_dir))
                from utils.lemonade_client import LemonadeClient
                from utils.rocm_monitor import ROCmMonitor
                from utils.metrics_collector import MetricsCollector
                result["details"]["framework_imports"] = "OK"
            except ImportError as e:
                result["status"] = "fail"
                result["message"] = f"Framework import failed: {str(e)}"

        except Exception as e:
            result["status"] = "error"
            result["message"] = f"Framework check failed: {str(e)}"

        return result

    def check_inference_basic(self) -> Dict[str, Any]:
        """Check basic inference functionality."""
        result = {"status": "pass", "message": "Basic inference OK", "details": {}}

        if self.quick:
            result["status"] = "skipped"
            result["message"] = "Skipped in quick mode"
            return result

        try:
            sys.path.insert(0, str(Path.cwd()))
            from utils.lemonade_client import LemonadeClient

            client = LemonadeClient()

            # Test basic inference
            test_prompt = "What is the capital of France?"
            response = client.inference(test_prompt, max_tokens=10, timeout=30)

            if response and response.content:
                result["details"]["inference_response"] = "OK"
                result["details"]["response_length"] = len(response.content)
                result["message"] = f"Basic inference OK (response length: {len(response.content)})"
            else:
                result["status"] = "fail"
                result["message"] = "Basic inference failed - no response"

        except Exception as e:
            result["status"] = "fail"
            result["message"] = f"Basic inference check failed: {str(e)}"

        return result

    def run_all_checks(self) -> Dict[str, Any]:
        """Run all validation checks."""
        self.log("Starting AMD AI Max+ 395 ROCm deployment validation")

        checks = [
            ("Hardware Requirements", self.check_hardware_requirements),
            ("ROCm Drivers", self.check_rocm_drivers),
            ("Python Environment", self.check_python_environment),
            ("Lemonade Server", self.check_lemonade_server),
            ("Test Framework", self.check_test_framework),
            ("Basic Inference", self.check_inference_basic),
        ]

        for check_name, check_func in checks:
            self.run_check(check_name, check_func)

        # Calculate overall status
        statuses = [check["status"] for check in self.results["validation_checks"]]
        status_priority = {"pass": 0, "warning": 1, "fail": 2, "error": 3, "unknown": 4, "skipped": 5}

        overall_status = min(statuses, key=lambda s: status_priority.get(s, 5))
        self.results["overall_status"] = overall_status

        # Generate summary
        total_checks = len(self.results["validation_checks"])
        passed_checks = sum(1 for check in self.results["validation_checks"] if check["status"] == "pass")
        failed_checks = sum(1 for check in self.results["validation_checks"] if check["status"] in ["fail", "error"])

        self.results["summary"] = {
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": failed_checks,
            "pass_rate": round((passed_checks / total_checks) * 100, 1) if total_checks > 0 else 0,
            "validation_duration": sum(check["duration"] for check in self.results["validation_checks"])
        }

        self.log(f"Validation complete: {passed_checks}/{total_checks} checks passed")

        return self.results

    def save_report(self, report_dir: Optional[Path] = None) -> Path:
        """Save validation report to file."""
        if report_dir is None:
            report_dir = Path.cwd() / "deployment_validation_reports"
        else:
            report_dir = Path(report_dir)

        report_dir.mkdir(parents=True, exist_ok=True)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"deployment_validation_{timestamp}.json"

        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)

        self.log(f"Validation report saved to: {report_file}")
        return report_file

    def print_summary(self) -> None:
        """Print validation summary to console."""
        print("\n" + "="*80)
        print("AMD AI Max+ 395 ROCm Deployment Validation Summary")
        print("="*80)

        status_emoji = {"pass": "✅", "fail": "❌", "warning": "⚠️", "error": "💥", "skipped": "⏭️"}
        status_color = {"pass": "\033[92m", "fail": "\033[91m", "warning": "\033[93m", "error": "\033[91m", "skipped": "\033[90m"}

        for check in self.results["validation_checks"]:
            emoji = status_emoji.get(check["status"], "❓")
            color = status_color.get(check["status"], "")
            reset = "\033[0m" if color else ""

            duration = f"({check['duration']:.1f}s)"
            print(f"{emoji} {check['name']}: {color}{check['message']}{reset} {duration}")

        print("\n" + "-"*80)
        summary = self.results["summary"]
        overall_status = self.results["overall_status"]
        overall_emoji = status_emoji.get(overall_status, "❓")

        print(f"Overall Status: {overall_emoji} {overall_status.upper()}")
        print(f"Pass Rate: {summary['pass_rate']}% ({summary['passed_checks']}/{summary['total_checks']} checks)")
        print(f"Total Duration: {summary['validation_duration']:.1f}s")
        print(f"Report Timestamp: {time.ctime(self.results['timestamp'])}")

        print("\n" + "="*80)


def main():
    """Main entry point for deployment validation."""
    parser = argparse.ArgumentParser(
        description="AMD AI Max+ 395 ROCm Production Deployment Validation"
    )
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Enable verbose output")
    parser.add_argument("-q", "--quick", action="store_true",
                       help="Run only critical validation checks")
    parser.add_argument("--report-dir", type=str,
                       help="Directory to save validation report")

    args = parser.parse_args()

    # Initialize validator
    validator = DeploymentValidator(verbose=args.verbose, quick=args.quick)

    # Run all checks
    results = validator.run_all_checks()

    # Save report
    report_file = validator.save_report(Path(args.report_dir) if args.report_dir else None)

    # Print summary
    validator.print_summary()

    # Exit with appropriate code
    overall_status = results["overall_status"]
    exit_codes = {"pass": 0, "warning": 0, "fail": 1, "error": 2, "unknown": 3, "skipped": 0}
    sys.exit(exit_codes.get(overall_status, 1))


if __name__ == "__main__":
    main()