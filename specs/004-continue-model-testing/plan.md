# Implementation Plan: Continue Extension Model Testing Framework

**Branch**: `004-continue-model-testing` | **Date**: 2025-12-25 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-continue-model-testing/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build an automated testing framework to validate compatibility and performance of local coder models (Qwen 2.5 Coder, DeepSeek Coder v2, Llama 3.2) running on AMD Ryzen AI hardware through the Continue VSCode extension. The framework will detect chat freezes that occur after 2-5 interactions, collect diagnostic data, measure NPU utilization, and produce compatibility/performance reports to identify stable models for daily development use.

## Technical Context

**Language/Version**: Python 3.10-3.13 (aligns with Lemonade SDK requirements)
**Primary Dependencies**: psutil (>=6.1.1), wmi, pyadl, pyyaml, xrt-smi (subprocess), wandb (optional)
**Storage**: JSON/YAML files for test results, logs, and configuration; CSV for metrics export
**Testing**: pytest for unit tests, manual test protocol with automated monitoring for integration testing
**Target Platform**: Windows 11 with AMD Ryzen AI hardware (NPU support), Anaconda AMD distribution
**Project Type**: Single project - testing/benchmarking framework with CLI
**Performance Goals**: Complete model testing in <30 minutes per model, detect freezes within 30 seconds, collect metrics with <5% overhead
**Constraints**: Must not interfere with existing Continue extension functionality, must work with Anaconda AMD environment, must integrate with existing RyzenAI-SW benchmarks at `C:\Users\tomwo\git\lemonade\scripts\benchmarks\RyzenAI-SW`
**Scale/Scope**: 3-5 coder models, 10-20 test interactions per model, multi-run stability testing, compatibility matrix generation

**Automation Approach**: Hybrid manual testing with automated monitoring (see research.md for rationale)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Applicable Constitution Principles

**III. Hardware-Optimized Performance** ✅
- **Status**: PASS
- **Application**: This feature validates model performance on AMD Ryzen AI hardware (NPU) and ensures proper hardware utilization through monitoring
- **Requirement Met**: Framework will test and validate models on AMD hardware, monitor NPU utilization, and leverage existing RyzenAI-SW benchmarks
- **Notes**: Aligns with constitution's emphasis on AMD hardware optimization

**V. Developer Experience First** ✅
- **Status**: PASS
- **Application**: Framework aims to reduce model selection from hours of trial-and-error to <30 minutes of automated testing
- **Requirement Met**: Provides practical examples, clear reports, and actionable recommendations for model selection
- **Notes**: Directly improves developer experience by solving the "which model works reliably" problem

**VI. Production-Ready Quality** ✅
- **Status**: PASS
- **Application**: Framework includes comprehensive testing, error detection, and diagnostic data collection
- **Requirement Met**: pytest-based testing, detailed logging, actionable error messages, compatibility validation
- **Notes**: Ensures developers can rely on test results for production model selection

**VII. Cross-Platform Support** ⚠️
- **Status**: CONDITIONAL PASS
- **Application**: Framework targets Windows 11 with AMD Ryzen AI hardware
- **Requirement Met**: Platform-specific feature (NPU testing) with strong justification
- **Justification**: NPU support is currently Windows-only for AMD Ryzen AI hardware. Framework addresses specific hardware configuration. Future expansion to Linux (when NPU drivers available) would follow same patterns.
- **Complexity Justification**: See Complexity Tracking section below

**VIII. Observability & Debugging** ✅
- **Status**: PASS
- **Application**: Framework provides structured logging, performance profiling, and diagnostic data collection
- **Requirement Met**: Logs all test interactions, captures system metrics, provides clear error traceability
- **Notes**: Core feature requirement - freeze detection and diagnosis require observability

### Non-Applicable Principles

**I. OpenAI API Compatibility**: N/A - Testing framework, not API server
**II. Multi-Backend Architecture**: N/A - Testing existing tools (Continue extension), not implementing backends
**IV. Open Source Collaboration**: N/A - Internal testing tool, not public contribution
**Development Workflow Policies**: Scripts will follow Script Organization Policy (placed in `scripts/benchmarks/continue-testing/`)

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
scripts/benchmarks/continue-testing/
├── test_runner.py           # Main test orchestration
├── freeze_detector.py       # Monitors Continue extension for freeze events
├── metrics_collector.py     # Collects NPU/GPU/memory metrics
├── model_manager.py         # Manages model configurations and loading
├── report_generator.py      # Generates compatibility matrix and performance reports
├── config/
│   ├── models.yaml          # Model configurations (names, sources, quantization)
│   ├── test_scenarios.yaml  # Test prompts and interaction sequences
│   └── hardware.yaml        # Hardware configuration and monitoring settings
├── utils/
│   ├── continue_api.py      # Continue extension automation/interaction
│   ├── npu_monitor.py       # NPU utilization monitoring (xrt-smi integration)
│   ├── vscode_bridge.py     # VSCode automation helpers
│   └── wandb_logger.py      # W&B integration for metrics logging (optional)
└── results/
    ├── test_runs/           # Individual test run logs
    ├── freeze_events/       # Diagnostic data from freeze events
    └── reports/             # Generated compatibility and performance reports

tests/
├── integration/
│   ├── test_freeze_detection.py
│   ├── test_model_compatibility.py
│   └── test_metrics_collection.py
└── unit/
    ├── test_report_generator.py
    ├── test_model_manager.py
    └── test_npu_monitor.py
```

**Structure Decision**: Single project structure under `scripts/benchmarks/continue-testing/` following the Script Organization Policy. This placement keeps the testing framework co-located with existing RyzenAI-SW benchmarks and clearly separates it from the main Lemonade SDK codebase. The framework is self-contained with its own configuration, utilities, and test results storage.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Windows-only (VII. Cross-Platform Support) | AMD Ryzen AI NPU support currently Windows-only | Linux NPU drivers not yet available. Testing CPU/GPU-only on Linux provides no value - purpose is validating NPU acceleration. Framework designed to extend to Linux when drivers release. |


---

## Post-Design Constitution Re-Evaluation

*Re-evaluated after Phase 1 design completion (2025-12-25)*

### Changes from Initial Check

**No violations introduced** - Design adheres to all applicable constitution principles.

### Principle Compliance Confirmation

**III. Hardware-Optimized Performance** ✅ CONFIRMED
- SystemMonitor class leverages existing xrt-smi patterns from RyzenAI-SW benchmarks
- NPU monitoring integrated via proven subprocess approach
- Reuses profiler patterns from src/lemonade/profilers/

**V. Developer Experience First** ✅ CONFIRMED
- quickstart.md provides 15-minute setup guide
- Interactive mode guides users through testing step-by-step
- Clear error messages and diagnostic data collection

**VI. Production-Ready Quality** ✅ CONFIRMED
- JSON Schema contracts define configuration validation
- data-model.md documents complete data structures
- Measurement dictionary pattern ensures reproducibility

**VII. Cross-Platform Support** ⚠️ JUSTIFIED (No Change)
- Windows-only design justified by NPU availability
- Framework structure allows Linux extension when drivers available

**VIII. Observability & Debugging** ✅ CONFIRMED
- SystemMetrics dataclass with comprehensive attributes
- FreezeEvent entity captures complete diagnostic context
- W&B integration for metrics visualization

### Design Decisions Aligned with Constitution

1. **Reuses existing patterns** (II, VI): SystemMonitor based on ryzen_benchmark_with_metrics.py
2. **Following Script Organization Policy**: Placed in scripts/benchmarks/continue-testing/
3. **Leverages Lemonade profiler infrastructure**: ContinueTestProfiler implements Profiler ABC
4. **W&B integration pattern**: Reuses WandbMetricsCollector approach from evaluation/wandb_logger.py

### Final Gate Assessment: **PASS** ✅

All constitution principles satisfied. No additional complexity violations introduced during design phase.
