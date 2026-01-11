# Research: Continue Extension Model Testing Framework

**Date**: 2025-12-25
**Phase**: 0 - Research & Technical Decisions
**Branch**: `004-continue-model-testing`

## Research Questions Addressed

1. How to automate and programmatically interact with Continue VSCode extension?
2. What Python libraries should be used for system resource monitoring on Windows 11?
3. What patterns and utilities from existing RyzenAI-SW benchmarks can be leveraged?

---

## Decision 1: Continue Extension Automation Approach

### Context
Need to programmatically send chat messages to Continue, monitor for freezes, and collect diagnostic data during testing.

### Options Evaluated

| Option | Pros | Cons | Feasibility |
|--------|------|------|-------------|
| VSCode Extension API (@vscode/test-electron) | Official testing framework, access to VSCode commands | Requires Node.js/TypeScript setup, complex for Python project | Medium |
| Playwright for VSCode | Powerful UI automation, freeze detection via timeouts | Heavy dependency, slow execution, UI-focused | Low |
| VSCode CLI Commands | Simple subprocess calls, Python-friendly | Limited Continue command exposure, no direct API | Medium |
| Continue Configuration + Log Monitoring | No automation dependency, monitors actual behavior | Indirect - can't trigger tests, only observe | High |
| Python + vscode-python bridge | Integrates with Python codebase | No established Continue automation patterns | Low |

### Decision

**Adopt Hybrid Approach**: Configuration Monitoring + Manual Testing Protocol

**Rationale**:
- Continue extension doesn't expose public automation API
- VSCode extension testing frameworks add significant complexity for marginal benefit
- Primary goal is **detecting existing freeze behavior**, not triggering artificial test scenarios
- Real-world usage monitoring is more valuable than synthetic test automation

**Implementation Strategy**:

1. **Manual Test Protocol** with structured logging:
   ```python
   # Test runner coordinates manual testing with automated monitoring
   class ContinueTestRunner:
       def run_interactive_test_session(self, model_config):
           """
           Guide user through manual test interactions while collecting metrics
           """
           print(f"Starting test for model: {model_config['name']}")
           print("Please perform the following interactions in Continue:")
           print("  1. Send message: 'Explain this code' (point to a function)")
           print("  2. Send message: 'Add error handling'")
           print("  3-10. Continue with coding tasks...")

           # Monitor in background while user interacts
           monitor = SystemMonitor()
           samples = monitor.sample_continuous(interval=1.0, duration=300)

           # Detect freeze via user input
           freeze_occurred = input("Did Continue freeze? (y/n): ").lower() == 'y'
           if freeze_occurred:
               freeze_after_msg = int(input("After which message number? "))
               self.record_freeze_event(freeze_after_msg, samples)
   ```

2. **Continue Log Monitoring** for automatic freeze detection:
   ```python
   class ContinueLogMonitor:
       """Monitor Continue extension logs for errors and hangs"""

       CONTINUE_LOG_PATHS = [
           os.path.expanduser("~/.continue/continue.log"),
           os.path.expanduser("~/.vscode/extensions/Continue.continue-*/logs"),
       ]

       def detect_freeze_from_logs(self, samples: List[SystemMetrics]) -> Optional[int]:
           """
           Analyze logs to detect when Continue stopped responding
           Returns: Message number where freeze occurred, or None
           """
           # Parse logs for timestamps and errors
           # Correlate with metric samples showing NPU/CPU drop-off
   ```

3. **Process Monitoring** for Continue extension host:
   ```python
   def find_continue_process() -> Optional[psutil.Process]:
       """Find VSCode extension host process running Continue"""
       for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
           if 'extensionHost' in ' '.join(proc.info['cmdline'] or []):
               return psutil.Process(proc.info['pid'])
       return None

   # Track Continue process metrics during testing
   monitor = SystemMonitor(track_process=find_continue_process())
   ```

**Alternatives Considered and Rejected**:
- **Full VSCode automation**: Too complex, fragile, doesn't match real-world usage
- **Continue API mocking**: Doesn't test actual freeze behavior in production extension
- **Browser automation (if Continue had web UI)**: Continue is VSCode-native

---

## Decision 2: System Monitoring Libraries

### Context
Need to collect CPU, RAM, NPU, GPU metrics on Windows 11 with AMD Ryzen AI hardware with <5% performance overhead.

### Decision

**Core Stack** (Already in use - Continue using):
- **psutil** (>=6.1.1): CPU, RAM, process monitoring
- **WMI** (Windows-only): Hardware enumeration, GPU detection
- **xrt-smi** (subprocess): AMD NPU monitoring via JSON output

> **Note:** `xrt-smi` is a critical dependency for NPU telemetry on AMD Ryzen AI test systems—install AMD XRT / RyzenAI drivers to enable it. When present, the SystemMonitor collects robust NPU Gops/utilization and context metrics; when missing the code falls back gracefully but with reduced visibility.

**Recommended Additions**:
- **pyadl** (AMD Display Library): Real-time AMD GPU utilization and temperature
- **pynvml** (NVIDIA Management Library): NVIDIA GPU monitoring (optional, if present)

### Rationale

| Library | Purpose | Overhead | Latency/Sample | Already Using |
|---------|---------|----------|----------------|---------------|
| psutil | CPU, RAM, process | <1% | <1ms | ✅ Yes |
| WMI | Device enumeration | <1% | 10-50ms | ✅ Yes |
| xrt-smi (subprocess) | NPU metrics (JSON) | 2-3% | 200-500ms | ✅ Yes |
| pyadl | AMD GPU real-time | <2% | 5-10ms | ❌ Add |
| pynvml | NVIDIA GPU (if present) | <1% | 1-5ms | ❌ Add (optional) |

**Total Overhead**: 3-5% at 1-second sampling interval (within <5% constraint)

### Implementation Pattern

Adopt SystemMonitor abstraction (based on existing patterns in `ryzen_benchmark_with_metrics.py`):

```python
@dataclass
class SystemMetrics:
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    proc_cpu_percent: Optional[float]  # For Continue process
    proc_memory_rss_mb: Optional[float]
    npu_gops: Optional[float]
    npu_utilization_percent: Optional[float]
    amd_gpu_utilization_percent: Optional[float]
    amd_gpu_temperature_c: Optional[float]

class SystemMonitor:
    def __init__(self, track_process: Optional[psutil.Process] = None):
        self.track_process = track_process
        # Initialize NPU, GPU monitoring

    def sample(self) -> SystemMetrics:
        # Collect all metrics in single call
        # Use existing xrt-smi pattern from ryzen_benchmark_with_metrics.py

    def sample_continuous(self, interval: float, duration: float) -> List[SystemMetrics]:
        # Background sampling (pattern from memory_tracker.py)
```

**Key Files Referenced**:
- `scripts/benchmarks/ryzen_benchmark_with_metrics.py`: xrt-smi JSON parsing, metric aggregation
- `src/lemonade/profilers/memory_tracker.py`: Threading pattern for continuous monitoring
- `src/lemonade/common/system_info.py`: WMI-based GPU detection

**Alternatives Rejected**:
- **GPUtil**: Limited to NVIDIA, less capable than pynvml
- **nvidia-smi subprocess**: Higher overhead than pynvml, harder parsing
- **py-cpuinfo**: Only for static info, not monitoring
- **Custom AMD NPU Python bindings**: xrt-smi subprocess is official/stable approach

---

## Decision 3: Leverage RyzenAI-SW Benchmark Patterns

### Context
Existing benchmarks at `scripts/benchmarks/RyzenAI-SW` contain proven patterns for metrics collection, configuration, and reporting.

### Reusable Patterns Identified

#### 1. Measurement Dictionary Structure

**Source**: `RyzenAI-SW/onnx-benchmark/utilities.py` (meas_init function)

**Pattern**: Hierarchical JSON for complete test context:
```python
measurement = {
    "run": {
        "command": test_cmd,
        "model": model_name,
        "backend": execution_provider,
    },
    "results": {
        "performance": {
            "throughput_fps": float,
            "average_latency_ms": float,
        },
        "efficiency_perf_per_watt": float,
        "energy_mj_per_frame": {
            "apu": float, "cpu": float, "npu": float, "mem": float
        }
    },
    "system": {
        "frequency": {"MPNPUCLK": int, "NPUHCLK": int},
        "resources": {"CPU_usage": float, "Memory": float},
        "hw": {"processor": str, "num_cores": int},
        "driver": {"npu_version": str},
    },
    "environment": {
        "packages": {...},
        "xclbin_config": str,
    }
}
```

**Adoption**: Use for Continue test results - captures complete reproducibility context

#### 2. Power Monitoring Approach

**Source**: `RyzenAI-SW/onnx-benchmark/utilities.py` (PowerMeter class)

**Pattern**: Two-tool strategy with CSV output:
- **AGM** (AMD Graphics Manager): Socket power, NPU clock frequencies
- **HWInfo**: CPU package power, SoC power, NPU metrics

**Already Integrated**: `src/lemonade/profilers/hwinfo_power.py` uses HWInfo

**Adoption**: Reuse hwinfo_power.py for power profiling during model testing (optional - P3 priority)

#### 3. W&B Integration Pattern

**Source**: `src/lemonade/evaluation/wandb_logger.py` (WandbMetricsCollector)

**Pattern**:
```python
# Hierarchical project structure
project = "lemonade-ryzenai-evals"
group = f"{model_family}/{quantization}/{benchmark_suite}"

# Consistent metric naming
metrics = {
    "test/name": task_name,
    "model/name": model_name,
    "model/backend": backend,
    "perf/tokens_per_second": float,
    "perf/latency_ms": float,
    "perf/latency_p95_ms": float,
    "resources/peak_memory_mb": float,
    "resources/cpu_utilization_percent": float,
    "resources/power_consumption_watts": float,
}
```

**Adoption**: Log Continue test metrics to W&B with schema:
```python
{
    "test/model": "qwen2.5-coder-7b",
    "test/quantization": "q4_0",
    "test/interaction_num": 5,
    "perf/response_time_ms": float,
    "perf/tokens_per_second": float,
    "resources/npu_utilization_percent": float,
    "resources/memory_used_gb": float,
    "event/freeze_detected": bool,
}
```

#### 4. Configuration File Format

**Source**: `RyzenAI-SW/onnx-benchmark/test/*.json`

**Pattern**: JSON with test parameters and expectations:
```json
{
    "model": "./models/resnet50/resnet50_fp32_XINT8.onnx",
    "num": 200,
    "timelimit": 20,
    "threads": 16,
    "check": {
        "results": {
            "performance": {
                "total_throughput": {"expectation": 632, "range": 10}
            }
        }
    }
}
```

**Adoption**: Create `config/models.yaml` for Continue test configurations:
```yaml
models:
  - name: "qwen2.5-coder-7b"
    source: "ollama"
    quantization: "q4_0"
    expected_tokens_per_second: 25
    tolerance_percent: 20
    max_stable_interactions: 20  # Pass if completes 20 without freeze

  - name: "deepseek-coder-v2-16b"
    source: "ollama"
    quantization: "q4_0"
    expected_tokens_per_second: 15
    tolerance_percent: 20
    max_stable_interactions: 20
```

#### 5. Profiler ABC Pattern

**Source**: `src/lemonade/profilers/profiler.py`

**Pattern**: Abstract base class for extensible profiling:
```python
class Profiler(ABC):
    def start(self, build_dir): pass
    def tool_starting(self, tool_name): pass
    def tool_stopping(self): pass
    def stop(self): pass
    def generate_results(self, state, timestamp, start_times): pass
```

**Adoption**: Create ContinueTestProfiler implementing Profiler ABC for consistency with Lemonade profiling infrastructure

#### 6. NPU Metrics Aggregation

**Source**: `scripts/benchmarks/ryzen_benchmark_with_metrics.py` (xrt-smi parsing)

**Pattern**: Recursive walk of xrt-smi JSON output, aggregate numeric values:
```python
def walk(o, acc):
    if isinstance(o, dict):
        for k, v in o.items():
            lk = str(k).lower()
            num = _try_number(v)
            if num is not None and any(x in lk for x in ('gops', 'command', 'util')):
                acc[lk] = acc.get(lk, 0) + num
            else:
                walk(v, acc)
```

**Adoption**: Use identical pattern for NPU monitoring in SystemMonitor class

---

## Decision 4: Test Scenario Definition

### Context
Need standardized, reproducible test interactions to detect freezes consistently.

### Decision

**YAML-based test scenarios** with prompt templates:

```yaml
# config/test_scenarios.yaml
scenarios:
  - name: "code_explanation"
    priority: "P1"
    description: "Request code explanations - common use case"
    interactions:
      - prompt: "Explain what this function does"
        context_required: true  # User must select code
        expected_response_tokens: 100-300

      - prompt: "What are the edge cases?"
        context_required: false
        expected_response_tokens: 50-150

  - name: "code_modification"
    priority: "P1"
    description: "Request code changes - resource-intensive"
    interactions:
      - prompt: "Add error handling to this function"
        context_required: true
        expected_response_tokens: 200-500

      - prompt: "Add type hints"
        context_required: true
        expected_response_tokens: 100-300

  - name: "debugging_assistance"
    priority: "P2"
    description: "Debug help - complex reasoning"
    interactions:
      - prompt: "Why might this code fail?"
        context_required: true
        expected_response_tokens: 150-400

      - prompt: "Suggest a fix"
        context_required: false
        expected_response_tokens: 100-300
```

**Rationale**:
- Reproducible across test runs
- Tracks expected response characteristics for anomaly detection
- Aligns with RyzenAI-SW configuration pattern
- Supports automated reporting (compatibility matrix generation)

---

## Technical Debt and Limitations

### Limitations Accepted

1. **No Full Automation**: Continue extension testing requires manual interaction
   - **Impact**: Higher time cost per test run (~30 min vs ~5 min if automated)
   - **Mitigation**: Structured protocol + background monitoring minimizes manual overhead
   - **Future**: If Continue exposes automation API, can refactor to full automation

2. **NPU Monitoring Overhead**: xrt-smi subprocess has 200-500ms latency
   - **Impact**: Can't sample faster than ~1 second intervals
   - **Mitigation**: 1-second interval sufficient for detecting multi-minute freezes
   - **Future**: AMD may release Python bindings for xrt-smi

3. **Process Tracking Fragility**: Finding Continue extension host process by cmdline matching
   - **Impact**: May fail if VSCode changes process structure
   - **Mitigation**: Fallback to system-wide monitoring if process not found
   - **Future**: More robust process identification if needed

### Technical Debt Created

None - reusing existing patterns and libraries from Lemonade SDK minimizes new code and dependencies.

---

## Dependencies and Prerequisites

### Python Packages (update setup.py)

```python
install_requires=[
    "psutil>=6.1.1",  # Already included
    "wmi; platform_system == 'Windows'",  # Already included
    # ... existing packages ...
],
extras_require={
    "continue_testing": [
        "pyadl>=0.1.0",  # AMD GPU monitoring
        "pyyaml>=6.0",  # Config file parsing
    ],
    # ... existing extras ...
}
```

### External Tools

- **xrt-smi**: Must be in PATH (installed with AMD RyzenAI drivers)
  - Location: `C:\Windows\System32\AMD\xrt-smi.exe`
- **VSCode**: With Continue extension installed
- **Ollama/LM Studio**: For hosting local models (user installs separately)

### Environment Requirements

- Windows 11 with AMD Ryzen AI hardware
- Anaconda AMD distribution (for Python environment)
- Git (for version control of test results)
- W&B account (optional, for metrics visualization)

---

## Implementation Priorities

Based on constitution principle alignment and spec priorities:

### Phase 1 (P1 - Must Have)
1. SystemMonitor class (CPU, RAM, NPU, GPU metrics)
2. Model configuration management (models.yaml)
3. Manual test protocol with structured logging
4. Freeze detection from logs and process monitoring
5. Basic compatibility matrix generation

### Phase 2 (P2 - Should Have)
6. W&B integration for metrics visualization
7. Test scenario definitions (test_scenarios.yaml)
8. Performance benchmarking and comparison reports
9. Metrics correlation and anomaly detection

### Phase 3 (P3 - Nice to Have)
10. Power profiling integration (hwinfo_power.py)
11. Automated scheduling for continuous monitoring
12. Historical trend analysis

---

## Verification Criteria

Research complete when:
- [x] Continue automation approach defined (hybrid: manual + monitoring)
- [x] System monitoring stack selected (psutil, wmi, xrt-smi, pyadl)
- [x] RyzenAI-SW patterns identified and adoption plan documented
- [x] Configuration file formats defined (models.yaml, test_scenarios.yaml)
- [x] Dependencies and prerequisites listed
- [x] Implementation priorities aligned with constitution and spec

---

## References

**Web Research Sources**:
- [Continue Extension Testing](https://docs.continue.dev/troubleshooting)
- [VSCode Extension Testing Guide](https://code.visualstudio.com/api/working-with-extensions/testing-extension)
- [psutil Documentation](https://psutil.readthedocs.io/)
- [AMD RyzenAI Documentation](https://ryzenai.docs.amd.com)

**Codebase Files Referenced**:
- `scripts/benchmarks/ryzen_benchmark_with_metrics.py` - NPU monitoring, metrics collection
- `scripts/benchmarks/RyzenAI-SW/onnx-benchmark/utilities.py` - Measurement patterns
- `src/lemonade/profilers/memory_tracker.py` - Threading patterns
- `src/lemonade/profilers/hwinfo_power.py` - Power monitoring
- `src/lemonade/evaluation/wandb_logger.py` - W&B integration
- `src/lemonade/common/system_info.py` - GPU detection
