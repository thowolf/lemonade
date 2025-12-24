# Implementation Plan: LLM Model Comparison Dashboard

**Branch**: `003-wandb-model-comparison` | **Date**: 2025-12-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-wandb-model-comparison/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Create a comprehensive evaluation workflow and dashboard for comparing LLM model performance across different quantization levels and MoE configurations on AMD Ryzen AI hardware. The system integrates W&B Weave as the primary dashboard platform, leverages LM Evaluation Harness for benchmarking, and provides side-by-side comparison of accuracy, latency, throughput, and resource utilization metrics to enable data-driven model selection decisions.

## Technical Context

**Language/Version**: Python 3.10-3.13 (aligns with Lemonade SDK requirements)
**Primary Dependencies**:
- W&B Weave SDK (evaluation tracking and dashboard)
- LM Evaluation Harness (benchmark execution framework)
- wandb Python SDK (metrics logging)
- lm-eval (evaluation harness CLI and library)
- NEEDS CLARIFICATION: Integration with existing Lemonade SDK server/router architecture

**Storage**:
- W&B cloud storage (evaluation results, metrics, artifacts)
- Local filesystem (temporary benchmark data, model outputs)
- NEEDS CLARIFICATION: Local database for offline/cache support or W&B-only

**Testing**: pytest (unit tests), contract tests (W&B API integration), integration tests (end-to-end evaluation workflows)

**Target Platform**:
- Windows 11 (primary - AMD Ryzen AI NPU support)
- Ubuntu 24.04/25.04 (secondary - cross-platform compatibility per constitution)
- AMD Ryzen AI Max+ 395 with 96GB VRAM (primary test hardware)
- AMD Radeon 8060S gfx1151 (secondary test hardware)

**Project Type**: Single project with CLI tools and evaluation orchestration

**Performance Goals**:
- Dashboard updates within 30 seconds of metric logging (SC-003: 90% compliance)
- Support 10+ concurrent evaluation runs without degradation (SC-002)
- Handle 20+ model configurations in single comparison view (SC-004)

**Constraints**:
- OpenAI API compatibility MUST be maintained (Constitution Principle I)
- Cross-platform support Windows + Linux (Constitution Principle VII)
- NEEDS CLARIFICATION: Maximum evaluation run duration before timeout
- NEEDS CLARIFICATION: Maximum result dataset size before pagination/aggregation

**Scale/Scope**:
- Support evaluation of 20+ model configurations simultaneously
- Retain 6 months of historical evaluation data (SC-005)
- MMLU and HellaSwag benchmarks by default (FR-014)
- NEEDS CLARIFICATION: Expected number of concurrent users accessing dashboard
- NEEDS CLARIFICATION: Maximum number of evaluation runs per day/week

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: OpenAI API Compatibility
**Status**: ✅ PASS - Feature extends existing Lemonade SDK evaluation capabilities without modifying core API endpoints. W&B integration is additive.

### Principle II: Multi-Backend Architecture
**Status**: ✅ PASS - Feature supports evaluation of models across all backends (ONNX Runtime GenAI, llama.cpp, FLM). Backend selection handled by existing Lemonade infrastructure.

### Principle III: Hardware-Optimized Performance
**Status**: ✅ PASS - Feature specifically targets AMD Ryzen AI hardware optimization. Evaluations will leverage NPU/GPU hybrid architecture for benchmark execution.

### Principle IV: Open Source Collaboration
**Status**: ✅ PASS - Uses open source tools (LM Evaluation Harness, W&B Weave). Results and configurations will be shareable via W&B public projects.

### Principle V: Developer Experience First
**Status**: ✅ PASS - Simplifies model comparison workflow from manual aggregation to automated dashboard. CLI-driven with clear examples.

### Principle VI: Production-Ready Quality
**Status**: ⚠️ CONDITIONAL PASS - Requires comprehensive testing of W&B integration, error handling for failed evaluations, and validation of metric accuracy. Tests MUST be added before implementation merge.

### Principle VII: Cross-Platform Support
**Status**: ⚠️ CONDITIONAL PASS - W&B Weave is cross-platform. LM Evaluation Harness supports Windows + Linux. MUST validate that all workflows function identically across platforms.

### Principle VIII: Observability & Debugging
**Status**: ✅ PASS - W&B Weave provides built-in logging and tracing. Evaluation progress visible in real-time. Error details captured in dashboard (FR-013).

**Overall Gate Status**: ✅ PASS with conditions - Proceed to Phase 0 research. Re-validate testing and cross-platform support after Phase 1 design.

## Project Structure

### Documentation (this feature)

```text
specs/003-wandb-model-comparison/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output - W&B Weave integration, LM Eval Harness patterns
├── data-model.md        # Phase 1 output - Evaluation Run, Model Configuration entities
├── quickstart.md        # Phase 1 output - Getting started guide for running comparisons
├── contracts/           # Phase 1 output - W&B logging schema, evaluation config schema
│   ├── wandb-schema.yaml
│   └── evaluation-config.schema.json
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
# Single project structure (aligned with existing Lemonade SDK)
src/lemonade/
├── evaluation/          # NEW: Evaluation orchestration
│   ├── __init__.py
│   ├── runners.py       # Evaluation run orchestration
│   ├── wandb_logger.py  # W&B Weave integration
│   ├── harness.py       # LM Eval Harness wrapper
│   └── config.py        # Evaluation configuration management
├── cli/
│   └── evaluate.py      # NEW: CLI commands for running evaluations
├── models/              # Existing - model management
└── profilers/           # Existing - may integrate with evaluation metrics

test/
├── unit/
│   └── evaluation/      # NEW: Unit tests for evaluation components
├── integration/
│   └── evaluation/      # NEW: End-to-end evaluation workflow tests
└── contract/
    └── wandb/           # NEW: W&B API contract tests

examples/
└── evaluation/          # NEW: Example evaluation configurations and notebooks
    ├── compare_quantizations.py
    ├── compare_moe_configs.py
    └── notebooks/
        └── dashboard_analysis.ipynb
```

**Structure Decision**: Single project structure selected. This feature extends the existing Lemonade SDK with new evaluation capabilities. Evaluation orchestration lives in `src/lemonade/evaluation/` with CLI entry points in `src/lemonade/cli/evaluate.py`. This maintains consistency with existing Lemonade architecture (profilers, CLI tools) while keeping evaluation code modular and testable.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations requiring justification. All conditional passes can be resolved through standard testing and validation procedures.

## Phase 0: Research & Technology Decisions

**Status**: PENDING - See [research.md](./research.md) after Phase 0 completion

### Research Questions to Resolve

1. **W&B Weave Integration Architecture**
   - Question: How to integrate W&B Weave logging into existing Lemonade evaluation workflows?
   - NEEDS CLARIFICATION: One-time initialization vs per-evaluation-run setup
   - NEEDS CLARIFICATION: Offline mode support or W&B cloud required

2. **LM Evaluation Harness Integration**
   - Question: How to programmatically invoke LM Eval Harness with Lemonade models?
   - NEEDS CLARIFICATION: Custom task definitions for Ryzen AI-specific metrics
   - NEEDS CLARIFICATION: Batch vs sequential evaluation strategy for multiple configs

3. **Evaluation Configuration Management**
   - Question: How to define and version evaluation configurations (models, quantizations, benchmarks)?
   - NEEDS CLARIFICATION: Configuration file format (YAML, JSON, Python)
   - NEEDS CLARIFICATION: Model specification format (Hugging Face IDs, local paths, both)

4. **Dashboard Customization and Views**
   - Question: What W&B dashboard views are needed for model comparison?
   - NEEDS CLARIFICATION: Custom panels vs standard W&B charts
   - NEEDS CLARIFICATION: Grouping strategy (by model family, by quantization, by benchmark)

5. **Error Handling and Recovery**
   - Question: How to handle partial evaluation failures (e.g., one benchmark fails out of ten)?
   - NEEDS CLARIFICATION: Retry strategy for transient failures
   - NEEDS CLARIFICATION: Partial result logging vs all-or-nothing

6. **Performance and Resource Management**
   - Question: How to manage VRAM/system memory during concurrent evaluations?
   - NEEDS CLARIFICATION: Model loading/unloading strategy
   - NEEDS CLARIFICATION: Queue management for evaluation runs

7. **Export and Reporting**
   - Question: What export formats are needed beyond W&B's built-in capabilities?
   - NEEDS CLARIFICATION: CSV, JSON, PDF report generation
   - NEEDS CLARIFICATION: Automated report generation triggers

## Phase 1: Design Artifacts

**Status**: PENDING - Will be generated after Phase 0 research completion

### Deliverables
- [data-model.md](./data-model.md) - Entity definitions (Evaluation Run, Model Configuration, Benchmark Result, Comparison Set)
- [contracts/](./contracts/) - API contracts for W&B logging schema and evaluation configurations
- [quickstart.md](./quickstart.md) - Getting started guide for running model comparisons

## Phase 2: Task Breakdown

**Status**: NOT STARTED - Use `/speckit.tasks` command after Phase 1 completion

Tasks will be generated in [tasks.md](./tasks.md) by the `/speckit.tasks` command, breaking down implementation into dependency-ordered, independently testable work items.

## Next Steps

1. Execute Phase 0 research to resolve all "NEEDS CLARIFICATION" items
2. Document research findings in research.md
3. Generate Phase 1 design artifacts (data-model.md, contracts/, quickstart.md)
4. Update agent context with new technologies
5. Re-run Constitution Check to verify design compliance
6. Proceed to `/speckit.tasks` for implementation task breakdown
