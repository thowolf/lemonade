# Implementation Plan: AMD AI Max+ 395 ROCm Testing

**Branch**: `001-max-395-rocm-test` | **Date**: 2025-12-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-max-395-rocm-test/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Create comprehensive testing infrastructure to validate LLM inference and RAG capabilities on AMD AI Max+ 395 (128GB VRAM, gfx1151) using Lemonade Server with ROCm backend on Windows 11. Testing will cover basic inference validation, performance benchmarking, RAG pipeline integration, and multi-model scenarios. Approach uses existing Lemonade CLI tools (`lemonade` for benchmarking, `lemonade-server` for model management) with Python test scripts for automation, ROCm-optimized llama.cpp backend for GGUF models, and structured result collection for performance analysis.

## Technical Context

**Language/Version**: Python 3.10-3.13 (per Lemonade SDK compatibility), Windows 11 (build 22H2+)  
**Primary Dependencies**: 
- Lemonade Server (latest stable, 9.1.1+) with llama.cpp ROCm backend
- AMD ROCm 7.1.1+ drivers for Windows with gfx1151 support
- pytest (test framework), OpenAI Python SDK (API client)
- psutil (system monitoring), tabulate (result formatting)
- Optional: chromadb/faiss (RAG vector stores), langchain (RAG orchestration)

**Storage**: 
- Local filesystem for model files (200GB+ disk space)
- JSON files for test results and benchmarks
- SQLite optional for test history tracking
- No external databases required

**Testing**: 
- pytest for test orchestration and assertion
- Existing Lemonade CLI tools (`lemonade` for perplexity/power profiling, `lemonade-server` for model management)
- Manual validation for response quality assessment
- Performance metrics collection via psutil and Lemonade built-in reporting

**Target Platform**: Windows 11 (22H2+) with AMD AI Max+ 395 GPU (gfx1151, 128GB VRAM)

**Project Type**: Single testing/validation project (test scripts + documentation)

**Performance Goals**: 
- Basic inference: 20+ tokens/sec for 7B models, 5+ tokens/sec for 30B+ models
- Latency: <2 seconds time-to-first-token for streaming
- VRAM efficiency: 80%+ utilization for large model loading
- Stability: 95%+ uptime over 4+ hour continuous testing sessions

**Constraints**: 
- ROCm backend availability on Windows 11 (driver maturity may vary)
- Single hardware platform testing (no NVIDIA comparison)
- GGUF models only (no ONNX/FLM for this feature)
- Manual response quality validation (no automated accuracy scoring yet)
- Testing scope: inference-only (no training/fine-tuning)

**Scale/Scope**: 
- 3-5 test model sizes (1B, 7B, 13B, 30B+, 70B optional)
- 4 user story priorities (P1-P4) with independent test validation
- 50-100 test prompts covering diverse topics
- 10-20 test scripts automating benchmarks and validations
- Single tester/researcher setup (not multi-user)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ Principle III: Hardware-Optimized Performance

**Status**: ALIGNED - Feature directly validates this principle

This feature tests and validates ROCm backend on AMD AI Max+ 395 (gfx1151, 128GB VRAM), directly supporting the constitution requirement: "Test and validate on Ryzen AI Max+ 395 with 128 GB VRAM" and "Support ROCm for AMD GPU acceleration (Windows and Linux)".

**Justification**: Testing validates constitution compliance and provides performance baseline data for documentation.

### ✅ Principle VI: Production-Ready Quality

**Status**: ALIGNED - Testing infrastructure supports quality goals

Comprehensive testing (basic inference → performance → RAG → multi-model) with measurable success criteria (20 tok/s for 7B, 95%+ uptime) ensures production-ready validation.

**Justification**: Test framework establishes quality gates and provides performance data for users.

### ✅ Principle VII: Cross-Platform Support

**Status**: ALIGNED WITH NOTE - Windows 11 focus with Linux roadmap

Feature focuses on Windows 11 ROCm testing. Constitution requires both Windows and Linux support. ROCm on Windows is newer technology requiring dedicated validation.

**Justification**: Windows 11 ROCm support is emerging technology. Separate Linux testing can follow same methodology. Test infrastructure is platform-agnostic (Python + pytest), easily portable to Linux.

### ✅ Principle VIII: Observability & Debugging

**Status**: ALIGNED - Comprehensive metrics and logging

Test framework collects structured performance metrics (tokens/sec, latency, VRAM), logs ROCm initialization, captures errors with context, and provides debugging visibility.

**Justification**: Testing validates observability capabilities and generates documentation of expected behavior.

### 🔵 Principle I-II, IV-V: Not Directly Applicable

**Principles I (OpenAI API), II (Multi-Backend), IV (Open Source), V (Developer Experience)**: Testing feature validates existing Lemonade capabilities rather than adding new features. Tests use existing OpenAI-compatible API, existing backend selection, contribute test methodology openly, and validate existing CLI/API experience.

**Justification**: Testing infrastructure supports rather than modifies these principles.

### Phase 1 Re-evaluation Notes

**Date**: 2025-12-23 (Post-Design)  
**Status**: ✅ ALL PRINCIPLES REMAIN ALIGNED

**Design Decisions Reviewed**:

1. **Test Structure** (`tests/rocm_max395/`): 
   - ✅ Follows existing Lemonade test patterns (pytest framework)
   - ✅ No new architectural complexity introduced
   - ✅ Isolated subdirectory prevents interference with existing tests

2. **Data Model** (JSON schemas):
   - ✅ Standard JSON format aligns with Constitution Principle V (Developer Experience)
   - ✅ Self-documenting with JSON Schema validation
   - ✅ No external database required (filesystem storage sufficient)

3. **Test Contracts** (test_execution.json, benchmark_results.json):
   - ✅ Clear interfaces support Constitution Principle VI (Production-Ready Quality)
   - ✅ Enables future automation and CI/CD integration
   - ✅ Validates against spec requirements

4. **Quickstart Guide** (quickstart.md):
   - ✅ 30-minute setup target aligns with Constitution Principle V (<10 min installation + 20 min first test)
   - ✅ Practical, example-driven documentation
   - ✅ Troubleshooting section supports debugging (Principle VIII)

**No Constitution Violations Detected**

All design decisions maintain alignment with constitution principles. Test infrastructure is:
- Platform-agnostic (portable to Linux per Principle VII)
- Observable (structured metrics per Principle VIII)  
- High-quality (comprehensive validation per Principle VI)
- Developer-friendly (clear setup, examples per Principle V)
- Hardware-optimized testing (validates Principle III)

**Recommendation**: ✅ Proceed to Phase 2 (tasks.md generation via `/speckit.tasks` command)

## Project Structure

### Documentation (this feature)

```text
specs/001-max-395-rocm-test/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output: ROCm setup, testing best practices
├── data-model.md        # Phase 1 output: Test result schemas, benchmark data structures
├── quickstart.md        # Phase 1 output: Setup and run first test guide
├── contracts/           # Phase 1 output: Test execution interfaces
│   ├── test_execution.json    # Test runner contract (input/output)
│   └── benchmark_results.json # Performance metrics schema
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
tests/rocm_max395/
├── README.md                    # Testing overview and setup instructions
├── requirements.txt             # Python dependencies (pytest, openai, psutil, tabulate)
├── conftest.py                  # pytest configuration and shared fixtures
├── test_basic_inference.py      # P1: Basic LLM inference validation tests
├── test_performance.py          # P2: Performance benchmarking tests
├── test_rag_integration.py      # P3: RAG pipeline validation tests
├── test_multi_model.py          # P4: Multi-model loading and concurrency tests
├── fixtures/
│   ├── prompts.json            # Test prompts covering diverse topics
│   └── models_config.json      # Model configurations (sizes, quantization)
├── utils/
│   ├── __init__.py
│   ├── lemonade_client.py      # Wrapper for Lemonade Server API interactions
│   ├── metrics_collector.py    # Performance metrics collection and formatting
│   ├── rocm_monitor.py         # VRAM and GPU utilization monitoring
│   └── report_generator.py     # Test result reporting and visualization
└── results/
    ├── .gitignore              # Ignore result files (keep structure)
    ├── README.md               # Result interpretation guide
    └── benchmark_template.json # Template for benchmark result storage

docs/testing/
├── rocm_max395_setup.md        # Driver installation, environment setup
├── test_execution_guide.md     # How to run tests, interpret results
└── troubleshooting.md          # Common issues and solutions
```

**Structure Decision**: Single project structure under `tests/rocm_max395/` subdirectory. This is a testing/validation feature, not a production feature, so tests live in the repository's test directory rather than `src/`. Documentation goes in `docs/testing/` for visibility. This structure:
- Keeps ROCm-specific tests isolated from general Lemonade tests
- Allows independent execution via pytest path: `pytest tests/rocm_max395/`
- Facilitates reuse for future AMD hardware testing (similar pattern for other GPUs)
- Aligns with constitution Principle V (Developer Experience) - clear separation of concerns

## Complexity Tracking

> **No constitution violations** - All checks passed. This section intentionally left minimal.

This testing feature directly supports Constitution Principle III (Hardware-Optimized Performance) without introducing complexity. Test structure follows existing Lemonade testing patterns (pytest framework, OpenAI SDK integration) and adds no new architectural components.

