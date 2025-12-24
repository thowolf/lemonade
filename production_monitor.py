#!/usr/bin/env python3
"""
AMD AI Max+ 395 ROCm Production Monitoring Script

This script provides comprehensive monitoring for AMD AI Max+ 395 ROCm deployments,
including GPU metrics, system resources, Lemonade Server health, and performance
benchmarks.

Usage:
    python production_monitor.py [--interval SECONDS] [--alert-thresholds FILE] [--log-dir DIR]

Options:
    --interval SECONDS    Monitoring interval in seconds (default: 60)
    --alert-thresholds FILE  JSON file with alert thresholds
    --log-dir DIR         Directory for log files
    --daemon              Run in daemon mode (continuous monitoring)
    --once                Run single monitoring cycle and exit
"""

import argparse
import json
import subprocess
import sys
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import psutil
import requests
from dataclasses import dataclass, asdict

@dataclass
class SystemMetrics:
    """System resource metrics."""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_usage_percent: Dict[str, float]
    network_io: Dict[str, float]

@dataclass
class GPUMetrics:
    """ROCm GPU metrics."""
    timestamp: float
    gpu_utilization: float
    memory_used_mb: float
    memory_total_mb: float
    temperature_celsius: float
    power_consumption_watts: float
    fan_speed_percent: float

@dataclass
class LemonadeMetrics:
    """Lemonade Server metrics."""
    timestamp: float
    server_status: str
    loaded_models: int
    active_requests: int
    total_requests: int
    average_response_time_ms: float
    error_rate_percent: float

@dataclass
class Alert:
    """Monitoring alert."""
    timestamp: float
    level: str  # 'info', 'warning', 'error', 'critical'
    component: str
    message: str
    value: Any
    threshold: Any

class ProductionMonitor:
    """Production monitoring system for AMD AI Max+ 395."""

    def __init__(self, alert_thresholds_file: Optional[str] = None, log_dir: Optional[str] = None):
        self.alert_thresholds_file = alert_thresholds_file or "alert_thresholds.json"
        self.log_dir = Path(log_dir) if log_dir else Path.cwd() / "monitoring_logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Default alert thresholds
        self.alert_thresholds = {
            "gpu": {
                "memory_percent": {"warning": 85, "critical": 95},
                "temperature_celsius": {"warning": 80, "critical": 90},
                "utilization_percent": {"warning": 95, "critical": 99}
            },
            "system": {
                "cpu_percent": {"warning": 85, "critical": 95},
                "memory_percent": {"warning": 85, "critical": 95},
                "disk_percent": {"warning": 85, "critical": 95}
            },
            "lemonade": {
                "response_time_ms": {"warning": 5000, "critical": 10000},
                "error_rate_percent": {"warning": 5, "critical": 10}
            }
        }

        # Load custom thresholds if provided
        self.load_alert_thresholds()

        # Monitoring state
        self.is_running = False
        self.monitoring_thread = None
        self.metrics_history: List[Dict[str, Any]] = []
        self.alerts: List[Alert] = []

        # Previous values for rate calculations
        self.prev_network_io = None
        self.prev_lemonade_stats = None

    def load_alert_thresholds(self) -> None:
        """Load custom alert thresholds from file."""
        thresholds_path = Path(self.alert_thresholds_file)
        if thresholds_path.exists():
            try:
                with open(thresholds_path, 'r') as f:
                    custom_thresholds = json.load(f)
                    self.alert_thresholds.update(custom_thresholds)
                print(f"Loaded custom alert thresholds from {thresholds_path}")
            except Exception as e:
                print(f"Failed to load alert thresholds: {e}")

    def collect_system_metrics(self) -> SystemMetrics:
        """Collect system resource metrics."""
        timestamp = time.time()

        # CPU and memory
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_gb = memory.used / (1024**3)
        memory_total_gb = memory.total / (1024**3)

        # Disk usage
        disk_usage = {}
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_usage[partition.mountpoint] = usage.percent
            except:
                pass

        # Network I/O
        network_io = psutil.net_io_counters()
        current_io = {
            'bytes_sent': network_io.bytes_sent,
            'bytes_recv': network_io.bytes_recv,
            'packets_sent': network_io.packets_sent,
            'packets_recv': network_io.packets_recv
        }

        # Calculate rates if we have previous values
        if self.prev_network_io:
            time_diff = timestamp - self.prev_network_io['timestamp']
            if time_diff > 0:
                current_io['bytes_sent_rate'] = (current_io['bytes_sent'] - self.prev_network_io['bytes_sent']) / time_diff
                current_io['bytes_recv_rate'] = (current_io['bytes_recv'] - self.prev_network_io['bytes_recv']) / time_diff

        self.prev_network_io = {'timestamp': timestamp, **current_io}

        return SystemMetrics(
            timestamp=timestamp,
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_gb=memory_used_gb,
            memory_total_gb=memory_total_gb,
            disk_usage_percent=disk_usage,
            network_io=current_io
        )

    def collect_gpu_metrics(self) -> Optional[GPUMetrics]:
        """Collect ROCm GPU metrics."""
        try:
            timestamp = time.time()

            # Use rocm-smi to get GPU metrics
            result = subprocess.run(
                ['rocm-smi', '--showuse', '--showmeminfo', 'vram', '--showtemp', '--showpower', '--showfan'],
                capture_output=True, text=True, timeout=10
            )

            if result.returncode != 0:
                print(f"ROCm command failed: {result.stderr}")
                return None

            output = result.stdout

            # Parse metrics (simplified parsing - adjust based on actual rocm-smi output format)
            gpu_utilization = 0.0
            memory_used_mb = 0.0
            memory_total_mb = 0.0
            temperature = 0.0
            power = 0.0
            fan_speed = 0.0

            lines = output.split('\n')
            for line in lines:
                line = line.lower()
                if 'gpu use' in line or 'utilization' in line:
                    # Extract percentage
                    import re
                    match = re.search(r'(\d+)%', line)
                    if match:
                        gpu_utilization = float(match.group(1))

                elif 'vram' in line and 'used' in line:
                    match = re.search(r'(\d+)[\s]*MB', line)
                    if match:
                        memory_used_mb = float(match.group(1))

                elif 'vram' in line and 'total' in line:
                    match = re.search(r'(\d+)[\s]*GB', line)
                    if match:
                        memory_total_mb = float(match.group(1)) * 1024  # Convert to MB

                elif 'temperature' in line or 'temp' in line:
                    match = re.search(r'(\d+)[\s]*c', line)
                    if match:
                        temperature = float(match.group(1))

                elif 'power' in line:
                    match = re.search(r'(\d+)[\s]*w', line)
                    if match:
                        power = float(match.group(1))

                elif 'fan' in line:
                    match = re.search(r'(\d+)%', line)
                    if match:
                        fan_speed = float(match.group(1))

            return GPUMetrics(
                timestamp=timestamp,
                gpu_utilization=gpu_utilization,
                memory_used_mb=memory_used_mb,
                memory_total_mb=memory_total_mb,
                temperature_celsius=temperature,
                power_consumption_watts=power,
                fan_speed_percent=fan_speed
            )

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            print(f"Failed to collect GPU metrics: {e}")
            return None

    def collect_lemonade_metrics(self) -> Optional[LemonadeMetrics]:
        """Collect Lemonade Server metrics."""
        try:
            timestamp = time.time()
            server_url = "http://localhost:8000"

            # Check server status
            try:
                response = requests.get(f"{server_url}/health", timeout=5)
                server_status = "healthy" if response.status_code == 200 else "unhealthy"
            except:
                server_status = "unreachable"

            # Get models
            loaded_models = 0
            try:
                response = requests.get(f"{server_url}/api/v1/models", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    loaded_models = len(data.get('data', []))
            except:
                pass

            # For demonstration, using placeholder values
            # In a real implementation, you'd need Lemonade Server to expose metrics endpoints
            active_requests = 0
            total_requests = getattr(self, '_total_requests', 0)
            average_response_time_ms = 0.0
            error_rate_percent = 0.0

            return LemonadeMetrics(
                timestamp=timestamp,
                server_status=server_status,
                loaded_models=loaded_models,
                active_requests=active_requests,
                total_requests=total_requests,
                average_response_time_ms=average_response_time_ms,
                error_rate_percent=error_rate_percent
            )

        except Exception as e:
            print(f"Failed to collect Lemonade metrics: {e}")
            return None

    def check_alerts(self, metrics: Dict[str, Any]) -> List[Alert]:
        """Check metrics against alert thresholds."""
        alerts = []
        timestamp = time.time()

        # GPU alerts
        gpu_metrics = metrics.get('gpu')
        if gpu_metrics:
            gpu_thresholds = self.alert_thresholds['gpu']

            # Memory usage
            memory_percent = (gpu_metrics.memory_used_mb / gpu_metrics.memory_total_mb) * 100
            if memory_percent >= gpu_thresholds['memory_percent']['critical']:
                alerts.append(Alert(timestamp, 'critical', 'gpu', 'GPU memory usage critical', memory_percent, gpu_thresholds['memory_percent']['critical']))
            elif memory_percent >= gpu_thresholds['memory_percent']['warning']:
                alerts.append(Alert(timestamp, 'warning', 'gpu', 'GPU memory usage high', memory_percent, gpu_thresholds['memory_percent']['warning']))

            # Temperature
            if gpu_metrics.temperature_celsius >= gpu_thresholds['temperature_celsius']['critical']:
                alerts.append(Alert(timestamp, 'critical', 'gpu', 'GPU temperature critical', gpu_metrics.temperature_celsius, gpu_thresholds['temperature_celsius']['critical']))
            elif gpu_metrics.temperature_celsius >= gpu_thresholds['temperature_celsius']['warning']:
                alerts.append(Alert(timestamp, 'warning', 'gpu', 'GPU temperature high', gpu_metrics.temperature_celsius, gpu_thresholds['temperature_celsius']['warning']))

            # Utilization
            if gpu_metrics.gpu_utilization >= gpu_thresholds['utilization_percent']['critical']:
                alerts.append(Alert(timestamp, 'critical', 'gpu', 'GPU utilization critical', gpu_metrics.gpu_utilization, gpu_thresholds['utilization_percent']['critical']))
            elif gpu_metrics.gpu_utilization >= gpu_thresholds['utilization_percent']['warning']:
                alerts.append(Alert(timestamp, 'warning', 'gpu', 'GPU utilization high', gpu_metrics.gpu_utilization, gpu_thresholds['utilization_percent']['warning']))

        # System alerts
        system_metrics = metrics.get('system')
        if system_metrics:
            system_thresholds = self.alert_thresholds['system']

            # CPU usage
            if system_metrics.cpu_percent >= system_thresholds['cpu_percent']['critical']:
                alerts.append(Alert(timestamp, 'critical', 'system', 'CPU usage critical', system_metrics.cpu_percent, system_thresholds['cpu_percent']['critical']))
            elif system_metrics.cpu_percent >= system_thresholds['cpu_percent']['warning']:
                alerts.append(Alert(timestamp, 'warning', 'system', 'CPU usage high', system_metrics.cpu_percent, system_thresholds['cpu_percent']['warning']))

            # Memory usage
            if system_metrics.memory_percent >= system_thresholds['memory_percent']['critical']:
                alerts.append(Alert(timestamp, 'critical', 'system', 'Memory usage critical', system_metrics.memory_percent, system_thresholds['memory_percent']['critical']))
            elif system_metrics.memory_percent >= system_thresholds['memory_percent']['warning']:
                alerts.append(Alert(timestamp, 'warning', 'system', 'Memory usage high', system_metrics.memory_percent, system_thresholds['memory_percent']['warning']))

            # Disk usage
            for mount, usage in system_metrics.disk_usage_percent.items():
                if usage >= system_thresholds['disk_percent']['critical']:
                    alerts.append(Alert(timestamp, 'critical', 'system', f'Disk usage critical on {mount}', usage, system_thresholds['disk_percent']['critical']))
                elif usage >= system_thresholds['disk_percent']['warning']:
                    alerts.append(Alert(timestamp, 'warning', 'system', f'Disk usage high on {mount}', usage, system_thresholds['disk_percent']['warning']))

        # Lemonade alerts
        lemonade_metrics = metrics.get('lemonade')
        if lemonade_metrics:
            lemonade_thresholds = self.alert_thresholds['lemonade']

            # Response time
            if lemonade_metrics.average_response_time_ms >= lemonade_thresholds['response_time_ms']['critical']:
                alerts.append(Alert(timestamp, 'critical', 'lemonade', 'Response time critical', lemonade_metrics.average_response_time_ms, lemonade_thresholds['response_time_ms']['critical']))
            elif lemonade_metrics.average_response_time_ms >= lemonade_thresholds['response_time_ms']['warning']:
                alerts.append(Alert(timestamp, 'warning', 'lemonade', 'Response time high', lemonade_metrics.average_response_time_ms, lemonade_thresholds['response_time_ms']['warning']))

            # Error rate
            if lemonade_metrics.error_rate_percent >= lemonade_thresholds['error_rate_percent']['critical']:
                alerts.append(Alert(timestamp, 'critical', 'lemonade', 'Error rate critical', lemonade_metrics.error_rate_percent, lemonade_thresholds['error_rate_percent']['critical']))
            elif lemonade_metrics.error_rate_percent >= lemonade_thresholds['error_rate_percent']['warning']:
                alerts.append(Alert(timestamp, 'warning', 'lemonade', 'Error rate high', lemonade_metrics.error_rate_percent, lemonade_thresholds['error_rate_percent']['warning']))

            # Server status
            if lemonade_metrics.server_status != 'healthy':
                alerts.append(Alert(timestamp, 'critical', 'lemonade', f'Server status: {lemonade_metrics.server_status}', lemonade_metrics.server_status, 'healthy'))

        return alerts

    def collect_all_metrics(self) -> Dict[str, Any]:
        """Collect all monitoring metrics."""
        metrics = {
            'timestamp': time.time(),
            'system': self.collect_system_metrics(),
            'gpu': self.collect_gpu_metrics(),
            'lemonade': self.collect_lemonade_metrics()
        }

        # Convert dataclasses to dictionaries for JSON serialization
        metrics_dict = {
            'timestamp': metrics['timestamp'],
            'system': asdict(metrics['system']) if metrics['system'] else None,
            'gpu': asdict(metrics['gpu']) if metrics['gpu'] else None,
            'lemonade': asdict(metrics['lemonade']) if metrics['lemonade'] else None
        }

        return metrics_dict

    def log_metrics(self, metrics: Dict[str, Any]) -> None:
        """Log metrics to file."""
        timestamp = datetime.fromtimestamp(metrics['timestamp'])
        log_file = self.log_dir / f"metrics_{timestamp.strftime('%Y%m%d')}.jsonl"

        with open(log_file, 'a') as f:
            json.dump(metrics, f, default=str)
            f.write('\n')

    def log_alerts(self, alerts: List[Alert]) -> None:
        """Log alerts to file and console."""
        if not alerts:
            return

        timestamp = datetime.now()
        alert_file = self.log_dir / f"alerts_{timestamp.strftime('%Y%m%d')}.jsonl"

        for alert in alerts:
            # Log to file
            with open(alert_file, 'a') as f:
                json.dump(asdict(alert), f, default=str)
                f.write('\n')

            # Print to console with color coding
            level_colors = {
                'info': '\033[94m',  # Blue
                'warning': '\033[93m',  # Yellow
                'error': '\033[91m',  # Red
                'critical': '\033[95m'  # Magenta
            }
            color = level_colors.get(alert.level, '\033[0m')
            reset = '\033[0m'

            print(f"{color}[{alert.level.upper()}] {alert.component}: {alert.message} "
                  f"(value: {alert.value}, threshold: {alert.threshold}){reset}")

    def monitoring_loop(self, interval: int = 60) -> None:
        """Main monitoring loop."""
        print(f"Starting production monitoring (interval: {interval}s)")
        print(f"Logs will be saved to: {self.log_dir}")

        while self.is_running:
            try:
                # Collect metrics
                metrics = self.collect_all_metrics()

                # Store in history (keep last 1000 entries)
                self.metrics_history.append(metrics)
                if len(self.metrics_history) > 1000:
                    self.metrics_history.pop(0)

                # Log metrics
                self.log_metrics(metrics)

                # Check for alerts
                alerts = self.check_alerts(metrics)
                if alerts:
                    self.alerts.extend(alerts)
                    self.log_alerts(alerts)

                # Wait for next interval
                time.sleep(interval)

            except KeyboardInterrupt:
                print("\nMonitoring stopped by user")
                break
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(interval)

    def start_monitoring(self, interval: int = 60, daemon: bool = True) -> None:
        """Start the monitoring system."""
        if self.is_running:
            print("Monitoring is already running")
            return

        self.is_running = True

        if daemon:
            self.monitoring_thread = threading.Thread(
                target=self.monitoring_loop,
                args=(interval,),
                daemon=True
            )
            self.monitoring_thread.start()
            print("Monitoring started in daemon mode")
        else:
            self.monitoring_loop(interval)

    def stop_monitoring(self) -> None:
        """Stop the monitoring system."""
        self.is_running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        print("Monitoring stopped")

    def get_status_report(self) -> Dict[str, Any]:
        """Generate a status report."""
        if not self.metrics_history:
            return {"error": "No metrics collected yet"}

        latest_metrics = self.metrics_history[-1]

        # Calculate averages over last hour (if available)
        one_hour_ago = time.time() - 3600
        recent_metrics = [m for m in self.metrics_history if m['timestamp'] >= one_hour_ago]

        report = {
            "timestamp": time.time(),
            "latest_metrics": latest_metrics,
            "alerts_last_24h": len([a for a in self.alerts if a.timestamp >= time.time() - 86400]),
            "system_status": "unknown",
            "gpu_status": "unknown",
            "lemonade_status": "unknown"
        }

        # Determine component status
        if latest_metrics.get('system'):
            system = latest_metrics['system']
            if system['cpu_percent'] < 85 and system['memory_percent'] < 85:
                report['system_status'] = "healthy"
            elif system['cpu_percent'] < 95 and system['memory_percent'] < 95:
                report['system_status'] = "warning"
            else:
                report['system_status'] = "critical"

        if latest_metrics.get('gpu'):
            gpu = latest_metrics['gpu']
            memory_percent = (gpu['memory_used_mb'] / gpu['memory_total_mb']) * 100 if gpu['memory_total_mb'] > 0 else 0
            if gpu['temperature_celsius'] < 80 and memory_percent < 85:
                report['gpu_status'] = "healthy"
            elif gpu['temperature_celsius'] < 90 and memory_percent < 95:
                report['gpu_status'] = "warning"
            else:
                report['gpu_status'] = "critical"

        if latest_metrics.get('lemonade'):
            lemonade = latest_metrics['lemonade']
            if lemonade['server_status'] == 'healthy':
                report['lemonade_status'] = "healthy"
            else:
                report['lemonade_status'] = "critical"

        return report

    def run_once(self) -> Dict[str, Any]:
        """Run a single monitoring cycle and return results."""
        metrics = self.collect_all_metrics()
        alerts = self.check_alerts(metrics)

        return {
            "metrics": metrics,
            "alerts": [asdict(alert) for alert in alerts],
            "timestamp": time.time()
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="AMD AI Max+ 395 ROCm Production Monitoring"
    )
    parser.add_argument("--interval", type=int, default=60,
                       help="Monitoring interval in seconds")
    parser.add_argument("--alert-thresholds", type=str,
                       help="JSON file with alert thresholds")
    parser.add_argument("--log-dir", type=str,
                       help="Directory for log files")
    parser.add_argument("--daemon", action="store_true",
                       help="Run in daemon mode")
    parser.add_argument("--once", action="store_true",
                       help="Run single monitoring cycle and exit")

    args = parser.parse_args()

    # Initialize monitor
    monitor = ProductionMonitor(
        alert_thresholds_file=args.alert_thresholds,
        log_dir=args.log_dir
    )

    if args.once:
        # Run single cycle
        result = monitor.run_once()
        print(json.dumps(result, indent=2, default=str))
        return

    # Start monitoring
    try:
        monitor.start_monitoring(interval=args.interval, daemon=args.daemon)

        if args.daemon:
            # Keep main thread alive
            print("Press Ctrl+C to stop monitoring")
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping monitoring...")
    finally:
        monitor.stop_monitoring()


if __name__ == "__main__":
    main()