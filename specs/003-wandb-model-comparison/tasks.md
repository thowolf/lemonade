# Tasks: LLM Model Comparison Dashboard

**Input**: Design documents from `/specs/003-wandb-model-comparison/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Single project structure extending Lemonade SDK at repository root with `src/`, `tests/` directories.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create evaluation module directory structure in src/lemonade/evaluation/
- [X] T002 [P] Add W&B dependencies (wandb, weave) to requirements.txt or pyproject.toml
- [X] T003 [P] Add lm-eval dependency to requirements.txt or pyproject.toml
- [X] T004 [P] Configure Python import paths for new evaluation module in src/lemonade/evaluation/__init__.py
- [X] T005 Create test directories for evaluation module: tests/unit/evaluation/, tests/integration/evaluation/, tests/contract/wandb/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 [P] Create EvaluationRun entity model in src/lemonade/evaluation/models.py based on data-model.md
- [X] T007 [P] Create ModelConfiguration entity model in src/lemonade/evaluation/models.py based on data-model.md
- [X] T008 [P] Create BenchmarkResult entity model in src/lemonade/evaluation/models.py based on data-model.md
- [X] T009 [P] Create ComparisonSet entity model in src/lemonade/evaluation/models.py based on data-model.md
- [X] T010 [P] Create HardwarePlatform entity model in src/lemonade/evaluation/models.py based on data-model.md
- [X] T011 Implement Pydantic validation schemas for evaluation configuration in src/lemonade/evaluation/config.py based on contracts/evaluation-config.schema.json
- [X] T012 Create WandbMetricsCollector base class extending existing MetricsCollector pattern in src/lemonade/evaluation/wandb_logger.py
- [X] T013 Implement W&B Weave initialization wrapper (one-time project init) in src/lemonade/evaluation/wandb_logger.py
- [X] T014 Create LMEvalHarness wrapper class for server-based integration in src/lemonade/evaluation/harness.py
- [X] T015 Implement error handling utilities for evaluation failures in src/lemonade/evaluation/errors.py
- [X] T016 Create logging configuration for evaluation workflows in src/lemonade/evaluation/logging_config.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compare Model Performance Across Configurations (Priority: P1) 🎯 MVP

**Goal**: Enable side-by-side comparison of multiple LLM models with different quantization levels and MoE configurations in a unified dashboard

**Independent Test**: Run evaluation benchmarks on at least two different model configurations (e.g., Qwen3-4B Q4_0 vs Q8_0) and verify comparative metrics appear in W&B dashboard

### Implementation for User Story 1

- [X] T017 [P] [US1] Implement metric collection for accuracy scores in src/lemonade/evaluation/wandb_logger.py following contracts/wandb-schema.yaml accuracy namespace
- [X] T018 [P] [US1] Implement metric collection for performance metrics (TPS, latency) in src/lemonade/evaluation/wandb_logger.py following contracts/wandb-schema.yaml perf namespace
- [X] T019 [P] [US1] Implement metric collection for resource utilization (VRAM, CPU, GPU) in src/lemonade/evaluation/wandb_logger.py following contracts/wandb-schema.yaml resources namespace
- [X] T020 [US1] Create evaluation runner orchestration in src/lemonade/evaluation/runners.py to coordinate benchmark execution
- [X] T021 [US1] Implement W&B run initialization with hierarchical grouping in src/lemonade/evaluation/wandb_logger.py following contracts/wandb-schema.yaml run_config
- [X] T022 [US1] Implement tag generation following prefix-based schema (model:, quant:, backend:, device:) in src/lemonade/evaluation/wandb_logger.py
- [X] T023 [US1] Integrate LM Eval Harness for MMLU benchmark execution in src/lemonade/evaluation/harness.py using existing ServerRunner pattern
- [X] T024 [US1] Integrate LM Eval Harness for HellaSwag benchmark execution in src/lemonade/evaluation/harness.py using existing ServerRunner pattern
- [X] T025 [US1] Implement @weave.op() decorators for evaluation functions to enable tracing in src/lemonade/evaluation/runners.py
- [X] T026 [US1] Create CLI command for running evaluations in src/lemonade/cli/evaluate.py with model config and benchmark suite parameters
- [ ] T027 [US1] Implement configuration loading from YAML files in src/lemonade/evaluation/config.py
- [ ] T028 [US1] Create example evaluation configuration files in examples/evaluation/config_qwen3_q4.yaml and examples/evaluation/config_qwen3_q8.yaml
- [ ] T029 [US1] Implement comparison dashboard grouping logic in src/lemonade/evaluation/wandb_logger.py using group_pattern from contracts/wandb-schema.yaml
- [ ] T030 [US1] Add validation for quantization level configurations in src/lemonade/evaluation/config.py
- [ ] T031 [US1] Add validation for MoE configurations in src/lemonade/evaluation/config.py
- [ ] T032 [US1] Implement sequential evaluation strategy for AMD Ryzen AI (one model at a time) in src/lemonade/evaluation/runners.py

**Checkpoint**: At this point, User Story 1 should be fully functional - users can evaluate 2+ models and see comparison in W&B dashboard

---

## Phase 4: User Story 2 - Track Evaluation Progress and History (Priority: P2)

**Goal**: Enable monitoring of long-running evaluation tasks and review of historical comparison data

**Independent Test**: Start an evaluation run, verify real-time progress updates appear in W&B dashboard, and confirm completed runs remain accessible in history

### Implementation for User Story 2

- [ ] T033 [P] [US2] Implement run status tracking (pending, running, completed, failed) in src/lemonade/evaluation/models.py for EvaluationRun entity
- [ ] T034 [P] [US2] Add timestamp tracking (created_at, started_at, completed_at) to EvaluationRun in src/lemonade/evaluation/models.py
- [ ] T035 [US2] Implement real-time progress logging with weave.log() in src/lemonade/evaluation/runners.py
- [ ] T036 [US2] Create progress indicator metrics (test/iteration, benchmark progress) in src/lemonade/evaluation/wandb_logger.py following contracts/wandb-schema.yaml metadata namespace
- [ ] T037 [US2] Implement error capture and logging for failed evaluations in src/lemonade/evaluation/runners.py
- [ ] T038 [US2] Add error details to W&B run summary in src/lemonade/evaluation/wandb_logger.py
- [ ] T039 [US2] Implement historical run retention logic (6 months minimum per SC-005) in src/lemonade/evaluation/wandb_logger.py
- [ ] T040 [US2] Create run filtering and querying utilities in src/lemonade/evaluation/query.py for accessing historical data
- [ ] T041 [US2] Add retry logic for transient failures (timeout, connection_error) in src/lemonade/evaluation/runners.py based on retry configuration from contracts/evaluation-config.schema.json
- [ ] T042 [US2] Implement partial result logging to enable saving progress even when evaluation fails mid-run in src/lemonade/evaluation/wandb_logger.py
- [ ] T043 [US2] Create summary statistics aggregation (mean, median, std, p95, p99) in src/lemonade/evaluation/wandb_logger.py following contracts/wandb-schema.yaml summary namespace
- [ ] T044 [US2] Add CLI command for listing historical evaluation runs in src/lemonade/cli/evaluate.py
- [ ] T045 [US2] Add CLI command for viewing run details and status in src/lemonade/cli/evaluate.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - users can track progress and access history

---

## Phase 5: User Story 3 - Export and Share Comparison Reports (Priority: P3)

**Goal**: Enable exporting comparison data and generating reports for stakeholders without dashboard access

**Independent Test**: Generate an export from existing dashboard data and verify exported format contains all relevant metrics

### Implementation for User Story 3

- [ ] T046 [P] [US3] Implement W&B report generation API integration in src/lemonade/evaluation/export.py
- [ ] T047 [P] [US3] Create CSV export formatter for evaluation results in src/lemonade/evaluation/export.py
- [ ] T048 [P] [US3] Create JSON export formatter for evaluation results in src/lemonade/evaluation/export.py
- [ ] T049 [US3] Implement comparison table panel data preparation in src/lemonade/evaluation/export.py following contracts/wandb-schema.yaml dashboard.recommended_panels
- [ ] T050 [US3] Implement chart data preparation for TPS comparison bar chart in src/lemonade/evaluation/export.py
- [ ] T051 [US3] Implement chart data preparation for latency vs accuracy scatter plot in src/lemonade/evaluation/export.py
- [ ] T052 [US3] Add configuration selection logic for multi-model export in src/lemonade/evaluation/export.py
- [ ] T053 [US3] Create CLI command for exporting evaluation results in src/lemonade/cli/evaluate.py with format selection (csv, json, report)
- [ ] T054 [US3] Implement automated report generation with markdown template in src/lemonade/evaluation/report_template.py
- [ ] T055 [US3] Add visualization embedding for exported reports in src/lemonade/evaluation/export.py
- [ ] T056 [US3] Create example export script in examples/evaluation/export_comparison.py

**Checkpoint**: All user stories should now be independently functional - complete workflow from evaluation to export

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T057 [P] Add offline mode support (WANDB_MODE=offline) with sync-later capability in src/lemonade/evaluation/wandb_logger.py
- [ ] T058 [P] Implement validation rules from contracts/wandb-schema.yaml (token_count_consistency, latency_percentile_order) in src/lemonade/evaluation/validators.py
- [ ] T059 [P] Add cross-platform path handling for Windows and Linux in src/lemonade/evaluation/config.py
- [ ] T060 Create quantization comparison example script in examples/evaluation/compare_quantizations.py following quickstart.md
- [ ] T061 Create MoE configuration comparison example script in examples/evaluation/compare_moe_configs.py
- [ ] T062 Create Jupyter notebook for dashboard analysis in examples/evaluation/notebooks/dashboard_analysis.ipynb
- [ ] T063 Update main CLI entry point in src/lemonade/cli.py to register evaluate subcommands
- [ ] T064 Add evaluation workflow documentation in docs/evaluation_guide.md
- [ ] T065 [P] Add unit tests for WandbMetricsCollector in tests/unit/evaluation/test_wandb_logger.py
- [ ] T066 [P] Add unit tests for configuration validation in tests/unit/evaluation/test_config.py
- [ ] T067 [P] Add unit tests for entity models in tests/unit/evaluation/test_models.py
- [ ] T068 [P] Add contract tests for W&B API integration in tests/contract/wandb/test_weave_integration.py
- [ ] T069 [P] Add integration test for end-to-end evaluation workflow in tests/integration/evaluation/test_evaluation_workflow.py
- [ ] T070 [P] Add integration test for multi-model comparison in tests/integration/evaluation/test_model_comparison.py
- [ ] T071 Run quickstart.md validation on both Windows 11 and Ubuntu 24.04
- [ ] T072 Performance optimization for dashboard updates to meet SC-003 (90% within 30 seconds)
- [ ] T073 Add logging for all critical evaluation operations
- [ ] T074 Security review for API key handling and W&B authentication

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independently testable (adds progress tracking to existing evaluation flow)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Independently testable (exports data from existing evaluations)

### Within Each User Story

**User Story 1 (Phase 3)**:
- T017-T019 (metric collection) can run in parallel
- T020 (evaluation runner) depends on T006-T010 (entity models)
- T021-T022 (W&B run init and tags) depends on T012-T013 (WandbMetricsCollector)
- T023-T024 (benchmark integration) depends on T014 (LMEvalHarness wrapper)
- T025 (weave decorators) depends on T020 (evaluation runner)
- T026-T028 (CLI and configs) depends on T011 (config validation) and T020 (runner)
- T029 (dashboard grouping) depends on T021 (run init)
- T030-T031 (validation) depends on T011 (config schema)
- T032 (sequential strategy) depends on T020 (runner orchestration)

**User Story 2 (Phase 4)**:
- T033-T034 (status and timestamp tracking) can run in parallel
- T035-T036 (progress logging) depends on T033 (status tracking)
- T037-T038 (error capture) can run in parallel
- T039-T040 (historical data) can run in parallel
- T041 (retry logic) depends on T037 (error capture)
- T042 (partial results) depends on T035 (progress logging)
- T043 (summary stats) depends on T012 (WandbMetricsCollector)
- T044-T045 (CLI commands) can run in parallel after T040 (query utils)

**User Story 3 (Phase 5)**:
- T046-T048 (export formatters) can run in parallel
- T049-T051 (chart data prep) can run in parallel after T046 (export API)
- T052 (config selection) depends on T046 (export API)
- T053 (CLI export) depends on T046-T048 (formatters)
- T054-T055 (report generation and viz) can run in parallel after T049-T051 (chart data)
- T056 (example script) depends on T053 (CLI export)

**Polish (Phase 6)**:
- T057-T059 (offline, validation, cross-platform) can run in parallel
- T060-T062 (example scripts and notebook) can run in parallel
- T063-T064 (CLI registration and docs) can run in parallel
- T065-T067 (unit tests) can run in parallel
- T068-T070 (contract and integration tests) can run in parallel
- T071-T074 (validation, optimization, logging, security) must run after all features complete

### Parallel Opportunities

**Phase 1 (Setup)**: T002-T004 can run in parallel

**Phase 2 (Foundational)**:
- T006-T010 (all entity models) can run in parallel
- T012-T014 (collectors and wrappers) can run in parallel after models
- T015-T016 (error handling and logging) can run in parallel

**Phase 3 (User Story 1)**:
- T017-T019 (metric collection types)
- T023-T024 (benchmark integrations)
- T030-T031 (validation rules)

**Phase 4 (User Story 2)**:
- T033-T034 (status tracking)
- T037-T038 (error logging)
- T039-T040 (historical data)
- T044-T045 (CLI commands)

**Phase 5 (User Story 3)**:
- T046-T048 (export formatters)
- T049-T051 (chart prep)
- T054-T055 (report and viz)

**Phase 6 (Polish)**:
- T057-T059 (cross-cutting features)
- T060-T062 (examples)
- T063-T064 (docs)
- T065-T067 (unit tests)
- T068-T070 (integration tests)

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (T017-T032)
4. **STOP and VALIDATE**: Test User Story 1 independently with quickstart.md
5. Deploy/demo basic comparison workflow

**MVP Deliverable**: Users can evaluate 2+ models with different quantization levels and see side-by-side comparison in W&B dashboard

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → **Deploy/Demo (MVP!)**
3. Add User Story 2 → Test independently → Deploy/Demo (MVP + Progress Tracking)
4. Add User Story 3 → Test independently → Deploy/Demo (Complete Feature)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (Phase 1-2)
2. Once Foundational is done (after T016):
   - Developer A: User Story 1 (T017-T032)
   - Developer B: User Story 2 (T033-T045)
   - Developer C: User Story 3 (T046-T056)
3. Stories complete and integrate independently
4. All developers: Polish phase together (T057-T074)

---

## Notes

- [P] tasks = different files, no dependencies within same phase
- [Story] label (US1, US2, US3) maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Constitution Principle VI requires comprehensive testing - Phase 6 tests are MANDATORY
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Align with existing Lemonade SDK patterns (ServerRunner, MetricsCollector, CLI structure)
- Follow contracts/wandb-schema.yaml and contracts/evaluation-config.schema.json strictly
- Validate cross-platform support on Windows 11 and Ubuntu 24.04 per Constitution Principle VII
