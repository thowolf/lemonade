# Feature Specification: MoE tests for qwen3-next-80b-q4_k_m.gguf

**Feature Branch**: `002-moe-qwen3-tests`  
**Created**: 2025-12-24  
**Status**: Draft  
**Input**: User request: "MoE-Tests mit qwen3-next-80b-q4_k_m.gguf; orientiert an examples/notebooks/lemonade_model_validation.ipynb"

## Summary

Add an end-to-end test suite and example notebook cells that demonstrate how to run benchmarking, objective accuracy (MMLU/GSM8k), and subjective (LLM-judge) tests for the Mixture-of-Experts (MoE) model `qwen3-next-80b-q4_k_m.gguf`. The goal is a reproducible, testable workflow that mirrors the `examples/notebooks/lemonade_model_validation.ipynb` patterns and can be used as both a demonstration and a validation harness for this MoE model.

---

## Clarifications

### Session 2025-12-24
- Q: Which devices should we prioritize for the tests (options: `cpu`, `igpu`, `hybrid`, `npu`)? Default proposal: `cpu` and `igpu`. → A: cpu and igpu
- Q: Should the CI smoke job be submitted to public CI or only to self-hosted hardware runners? (Default: self-hosted runners only.) → A: Self-hosted runners only
- Q: Should the repository default to running `quick-demo` parameters in automated contexts (CI) and reserve `full` runs for manual/overnight experiments? (Default: quick-demo in CI.) → A: Yes - quick-demo in CI.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run full model validation (Priority: P1)

A user wants to validate `qwen3-next-80b-q4_k_m.gguf` by running the standard Lemonade benchmarking and accuracy tests from the notebook and collecting results.

**Why this priority**: This delivers core value — a validated method to benchmark MoE models and produce comparable metrics.

**Independent Test**: Run the notebook cells (or equivalent CLI commands) with a quick demo configuration (`limit=5`) and verify the final report CSV contains TTFT, TPS, memory usage, MMLU accuracy, and GSM8k accuracy.

**Acceptance Scenarios**:

1. **Given** a system with the model file accessible and Lemonade tools installed, **When** the user runs the provided notebook section titled "MoE validation - quick demo", **Then** the run completes and writes a CSV report to the cache directory with the expected metrics.
2. **Given** the same run repeated 3 times, **When** results are compared, **Then** model load and run succeed in at least 95% of attempts (to detect flaky loads/crashes).

---

### User Story 2 - Automated judgement & stats storage (Priority: P2)

A user wants the notebook to demonstrate automatic subjective scoring using a local LLM judge and persist judgement results back to the experiment stats.

**Why this priority**: Automates human-like evaluation at scale and stores results where they can be aggregated.

**Independent Test**: Run the "LLM judge" cell in the notebook against the model response; verify the stats database contains `llm_judgement` and `llm_judgement_reason` entries after the run.

**Acceptance Scenarios**:

1. **Given** Lemonade Server (or a compatible local judge) is available, **When** the judgement flow is executed, **Then** it returns a JSON judgement and the stats file contains the saved judgement values.

---

## Notes

- The notebook includes a compatibility check for `lm-eval` and `huggingface-hub`. If `huggingface-hub` >= 1.0 is present the notebook will skip the `lm-eval` steps and instruct users to run `lm-eval` in a separate venv with `huggingface-hub<1.0,>=0.30.0`.
- Use server-based tests for newer architectures (qwen3next) where the direct `llama.cpp` CLI may not support the model.

---

## Files

- `examples/notebooks/moe_qwen3_validation.ipynb` - Notebook demonstrating server-based flows and fallback checks
- `scripts/ci/smoke_test_moe_server.py` - Server-based smoke test script
- `scripts/ci/README.md` - CI guidance and dependency notes

---

*This spec was generated during the 002-moe-qwen3-tests workstream and is intentionally concise — expand sections into `plan.md` and `tasks.md` for execution details.*
