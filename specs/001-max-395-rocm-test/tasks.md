# Tasks: AMD AI Max+ 395 ROCm Testing

**Feature**: 001-max-395-rocm-test  
**Branch**: `001-max-395-rocm-test`  
**Input**: Design documents from [specs/001-max-395-rocm-test/](../001-max-395-rocm-test/)  
**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/)

## Format: `- [ ] [ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1=P1, US2=P2, US3=P3, US4=P4)
- **File paths**: Exact locations per [plan.md structure](plan.md#project-structure)

## Path Conventions

Based on plan.md project structure:
- **Tests**: `tests/rocm_max395/` (main test directory)
- **Documentation**: `docs/testing/` (setup guides, troubleshooting)
- **Fixtures**: `tests/rocm_max395/fixtures/` (prompts, model configs)
- **Utils**: `tests/rocm_max395/utils/` (helper modules)
- **Results**: `tests/rocm_max395/results/` (benchmark output)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and directory structure

- [x] T001 Create directory structure: tests/rocm_max395/{fixtures/,utils/,results/} and docs/testing/
- [x] T002 [P] Create tests/rocm_max395/requirements.txt with dependencies (pytest, openai, psutil, tabulate)
- [x] T003 [P] Create tests/rocm_max395/README.md with testing overview and quick start instructions
- [x] T004 [P] Create docs/testing/rocm_max395_setup.md from quickstart.md (driver installation, environment setup)
- [x] T005 [P] Create results/.gitignore to exclude result files but keep directory structure

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core test infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 Create tests/rocm_max395/conftest.py with pytest configuration and shared fixtures (model loading, API client)
- [x] T007 [P] Implement LemonadeClient wrapper in tests/rocm_max395/utils/lemonade_client.py (OpenAI SDK integration)
- [x] T008 [P] Implement MetricsCollector in tests/rocm_max395/utils/metrics_collector.py (performance data collection)
- [x] T009 [P] Implement ROCmMonitor in tests/rocm_max395/utils/rocm_monitor.py (VRAM/GPU utilization tracking)
- [x] T010 [P] Implement ReportGenerator in tests/rocm_max395/utils/report_generator.py (result formatting and visualization)
- [x] T011 Create tests/rocm_max395/fixtures/prompts.json with 50-100 test prompts covering diverse topics
- [x] T012 [P] Create tests/rocm_max395/fixtures/models_config.json with model configurations (sizes, quantization levels)
- [x] T013 [P] Create tests/rocm_max395/utils/__init__.py to expose utility modules
- [x] T014 Create tests/rocm_max395/results/benchmark_template.json based on contracts/benchmark_results.json schema
- [x] T015 [P] Create tests/rocm_max395/results/README.md with result interpretation guide

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Basic LLM Inference Validation (Priority: P1) 🎯 MVP

**Goal**: Validate that LLMs run correctly on AMD AI Max+ 395 with ROCm backend, establishing baseline functionality

**Independent Test**: Load Llama-3.2-1B-Instruct GGUF, run single inference request via API, verify correct output within expected timeframe

**Acceptance Scenarios** (from spec.md):
1. Model loads successfully with `--llamacpp rocm` and generates coherent text
2. OpenAI-compatible API returns properly formatted response
3. Large models (30B+) utilize 128GB VRAM efficiently without crashes
4. Different prompts produce varied, coherent outputs

### Implementation for User Story 1

- [x] T016 [P] [US1] Create tests/rocm_max395/test_basic_inference.py with pytest structure
- [x] T017 [US1] Implement test_model_loading_rocm() to validate model load with ROCm backend (AS1)
- [x] T018 [US1] Implement test_api_inference_basic() to validate OpenAI API response format (AS2)
- [x] T019 [US1] Implement test_large_model_vram() to validate 30B+ model loading and VRAM utilization (AS3)
- [x] T020 [US1] Implement test_prompt_variation() to validate output diversity with different prompts (AS4)
- [x] T021 [US1] Add error handling for ROCm driver issues and model loading failures
- [x] T022 [US1] Add logging for inference requests, model loading events, and VRAM usage

**Checkpoint**: At this point, User Story 1 should be fully functional - basic inference validated on AMD AI Max+ 395 with ROCm

---

## Phase 4: User Story 2 - Performance Benchmarking (Priority: P2)

**Goal**: Measure inference performance (tokens/second, latency, throughput) on AMD AI Max+ 395 with ROCm to understand hardware capabilities

**Independent Test**: Run Lemonade CLI benchmarking tools (perplexity, power profiling) on working installation, verify performance metrics collection

**Acceptance Scenarios** (from spec.md):
1. Perplexity benchmark reports tokens/sec, latency percentiles (p50, p95, p99), VRAM utilization
2. Performance metrics scale predictably with model size (7B, 13B, 30B+)
3. ROCm shows measurable performance advantage vs CPU/Vulkan for large models
4. Performance remains stable during extended testing (4+ hours)

### Implementation for User Story 2

- [ ] T023 [P] [US2] Create tests/rocm_max395/test_performance.py with pytest structure
- [ ] T024 [US2] Implement test_perplexity_benchmark() to run perplexity tests and collect metrics (AS1)
- [ ] T025 [US2] Implement test_model_size_scaling() to benchmark 7B, 13B, 30B+ models and validate scaling (AS2)
- [ ] T026 [US2] Implement test_backend_comparison() to compare ROCm vs CPU/Vulkan performance (AS3)
- [ ] T027 [US2] Implement test_stability_extended() to run continuous inference for 4+ hours and track performance (AS4)
- [ ] T028 [US2] Integrate with MetricsCollector to aggregate performance data
- [ ] T029 [US2] Add benchmark result storage to tests/rocm_max395/results/ directory

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - basic inference + performance benchmarking complete

---

## Phase 5: User Story 3 - RAG Pipeline Integration (Priority: P3)

**Goal**: Test Retrieval-Augmented Generation workflows on AMD AI Max+ 395, validating LLM processing of retrieved context

**Independent Test**: Setup simple RAG pipeline with local vector store, submit queries requiring context retrieval, verify response accuracy

**Acceptance Scenarios** (from spec.md):
1. LLM generates responses that accurately incorporate provided context chunks
2. RAG pipeline retrieves relevant chunks and LLM generates accurate answers from document corpus
3. System handles context windows of varying sizes (4K, 8K, 16K+ tokens) efficiently
4. Streaming enabled for RAG responses without blocking on context processing

### Implementation for User Story 3

- [ ] T030 [P] [US3] Create tests/rocm_max395/test_rag_integration.py with pytest structure
- [ ] T031 [US3] Implement test_context_incorporation() to validate LLM response accuracy with provided context (AS1)
- [ ] T032 [US3] Implement test_document_qa_pipeline() to test full RAG pipeline with vector store and document corpus (AS2)
- [ ] T033 [US3] Implement test_variable_context_windows() to validate handling of 4K, 8K, 16K+ token contexts (AS3)
- [ ] T034 [US3] Implement test_rag_streaming() to validate streaming responses with context processing (AS4)
- [ ] T035 [US3] Add fixtures for RAG test scenarios (sample documents, expected Q&A pairs) in tests/rocm_max395/fixtures/rag_scenarios.json
- [ ] T036 [US3] Add error handling for context truncation and oversized context windows

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently - basic inference + performance + RAG validated

---

## Phase 6: User Story 4 - Multi-Model Testing (Priority: P4)

**Goal**: Test multiple LLM models simultaneously or switch between models rapidly to compare outputs and validate consistency

**Independent Test**: Load 2-3 models via Lemonade multi-model support, send concurrent requests to different models, verify each returns correct responses

**Acceptance Scenarios** (from spec.md):
1. Multiple models (2-3 totaling <100GB) load successfully and respond concurrently
2. Requests to specific models via model name route correctly without cross-contamination
3. Different model types (generation, embedding, instruction-tuned) perform specialized tasks correctly
4. System provides clear error messages for VRAM exhaustion when loading too many models

### Implementation for User Story 4

- [ ] T037 [P] [US4] Create tests/rocm_max395/test_multi_model.py with pytest structure
- [ ] T038 [US4] Implement test_concurrent_model_loading() to validate loading 2-3 models simultaneously (AS1)
- [ ] T039 [US4] Implement test_model_routing() to validate requests route to correct model without interference (AS2)
- [ ] T040 [US4] Implement test_specialized_model_types() to validate generation, embedding, and instruction-tuned models (AS3)
- [ ] T041 [US4] Implement test_vram_exhaustion_handling() to validate error messages when exceeding VRAM capacity (AS4)
- [ ] T042 [US4] Add fixtures for multi-model test configurations in tests/rocm_max395/fixtures/multi_model_configs.json
- [ ] T043 [US4] Add VRAM monitoring and allocation tracking for concurrent model loading

**Checkpoint**: At this point, ALL User Stories (1-4) should work independently - complete feature validation

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, refactoring, and final validation

- [ ] T044 [P] Create docs/testing/test_execution_guide.md with detailed instructions for running tests and interpreting results
- [ ] T045 [P] Create docs/testing/troubleshooting.md with common issues and solutions (driver errors, VRAM issues, model loading failures)
- [ ] T046 Update tests/rocm_max395/README.md with complete feature documentation and examples
- [ ] T047 [P] Validate quickstart.md instructions by following setup guide on fresh Windows 11 system
- [ ] T048 [P] Add edge case tests for ROCm driver issues, VRAM exhaustion, model file corruption (from spec.md Edge Cases section)
- [ ] T049 Run full test suite (pytest tests/rocm_max395/) and validate all acceptance scenarios pass
- [ ] T050 Generate comprehensive benchmark report using ReportGenerator with results from all user stories

---

## Dependencies & Execution Strategy

### Phase Dependencies

```
Phase 1 (Setup) → Phase 2 (Foundational) → Phases 3-6 (User Stories in parallel) → Phase 7 (Polish)
                                          ↓
                                    US1 (P1) ← MVP
                                    US2 (P2)
                                    US3 (P3)
                                    US4 (P4)
```

**Critical Path**:
1. **Phases 1-2 MUST complete first** (Setup + Foundational infrastructure)
2. **User Stories (Phases 3-6) can run in parallel** after Phase 2 completes
3. **Phase 7 (Polish) requires all user stories complete**

### User Story Independence

Each user story (US1-US4) is **independently testable** after Phase 2:

- **US1 (Basic Inference)**: No dependencies on other stories
- **US2 (Performance)**: No dependencies on other stories (builds on US1 conceptually, but not technically)
- **US3 (RAG)**: No dependencies on other stories (uses same inference API as US1)
- **US4 (Multi-Model)**: No dependencies on other stories (extends model loading from US1)

### Parallel Execution Examples

**Scenario 1: Single Developer (Sequential)**
```
Week 1: Phases 1-2 (Setup + Foundation)
Week 2: Phase 3 (US1 - MVP delivery)
Week 3: Phase 4 (US2 - Performance)
Week 4: Phase 5 (US3 - RAG)
Week 5: Phase 6 (US4 - Multi-Model)
Week 6: Phase 7 (Polish)
```

**Scenario 2: Team of 4 (Parallel User Stories)**
```
Week 1: All devs → Phases 1-2 (pair programming)
Week 2-3: Dev1→US1, Dev2→US2, Dev3→US3, Dev4→US4 (parallel)
Week 4: All devs → Phase 7 (integration testing, documentation)
```

**Scenario 3: MVP First (Incremental)**
```
Sprint 1: Phases 1-2 + Phase 3 (US1 MVP) → Deploy to stakeholders for validation
Sprint 2: Phase 4 (US2) → Add performance benchmarking
Sprint 3: Phases 5-6 (US3, US4) → RAG and multi-model features
Sprint 4: Phase 7 → Polish and documentation
```

### Task Parallelization Opportunities

**Within Phases** (tasks marked `[P]` can run concurrently):

- **Phase 1**: T002-T005 (4 parallel tasks - documentation creation)
- **Phase 2**: T007-T010, T012-T013, T015 (8 parallel tasks - utility modules and fixtures)
- **Phase 3**: T016 (single initial file creation, then sequential tests)
- **Phase 4**: T023 (single initial file creation, then sequential tests)
- **Phase 5**: T030 (single initial file creation, then sequential tests)
- **Phase 6**: T037 (single initial file creation, then sequential tests)
- **Phase 7**: T044-T045, T047-T048 (4 parallel tasks - documentation and edge cases)

**Cross-Phase Parallelization**: After Phase 2 completes, Phases 3-6 (US1-US4) can ALL run in parallel if multiple developers are available.

---

## Implementation Strategy

### MVP Delivery (Minimum Viable Product)

**Recommendation**: Implement **Phase 1 → Phase 2 → Phase 3 (US1 only)** first

**Rationale**:
- US1 (Basic Inference) delivers core value: "LLMs work on AMD AI Max+ 395 with ROCm"
- Provides immediate feedback on hardware/software stack viability
- Enables stakeholder validation before investing in performance benchmarking, RAG, or multi-model features
- Estimated effort: ~40% of total project (20 tasks out of 50)

**MVP Deliverable**: Working test suite demonstrating basic LLM inference on ROCm backend with:
- Model loading validation
- API integration
- VRAM utilization verification
- Prompt variation testing

### Incremental Delivery

After MVP (US1), prioritize remaining user stories based on stakeholder needs:

1. **Performance-focused path**: US1 → US2 → US3 → US4
2. **Application-focused path**: US1 → US3 (RAG) → US2 → US4
3. **Comprehensive validation path**: US1 → US2 → US4 → US3

**Recommendation**: Follow priority order (US1 → US2 → US3 → US4) unless stakeholder requests differ.

### Parallel Implementation (Team of 2+)

If multiple developers available:

1. **Week 1**: All devs collaborate on Phases 1-2 (foundation must be solid)
2. **Week 2+**: Split user stories across developers
   - Developer 1: US1 (MVP, highest priority)
   - Developer 2: US2 (performance validation)
   - Developer 3: US3 (RAG integration)
   - Developer 4: US4 (multi-model testing)
3. **Final Week**: Reconvene for Phase 7 (polish, integration testing, documentation)

---

## Success Metrics

**Task Completion**:
- Total Tasks: 50
- Setup Phase: 5 tasks
- Foundational Phase: 10 tasks
- User Story Phases: 28 tasks (7 per story)
- Polish Phase: 7 tasks

**User Story Breakdown**:
- US1 (P1 - MVP): 7 tasks (T016-T022)
- US2 (P2): 7 tasks (T023-T029)
- US3 (P3): 7 tasks (T030-T036)
- US4 (P4): 7 tasks (T037-T043)

**Parallel Opportunities**:
- Within Phases: 16 tasks marked `[P]` (32% of total)
- Across Phases: Phases 3-6 (28 tasks) can run fully in parallel after Phase 2

**Independent Test Validation**:
- Each user story has clear "Independent Test" criteria (defined in spec.md)
- Checkpoints after each phase ensure incremental validation
- No user story depends on another for testing or functionality

**MVP Scope**:
- Phases 1-3 (US1 only): 22 tasks
- Estimated effort: 40% of total project
- Delivers core value: "LLMs work on ROCm with AMD AI Max+ 395"

---

## Format Validation

✅ **All tasks follow required checklist format**:
- Checkbox: `- [ ]` (markdown checkbox)
- Task ID: Sequential (T001-T050)
- [P] marker: Included for parallelizable tasks (16 tasks)
- [Story] label: Included for user story tasks (US1-US4, 28 tasks)
- Description: Clear action with exact file path
- Examples:
  - ✅ `- [ ] T001 Create directory structure: tests/rocm_max395/{fixtures/,utils/,results/} and docs/testing/`
  - ✅ `- [ ] T007 [P] Implement LemonadeClient wrapper in tests/rocm_max395/utils/lemonade_client.py`
  - ✅ `- [ ] T016 [P] [US1] Create tests/rocm_max395/test_basic_inference.py with pytest structure`

✅ **Organization by user story**: Tasks grouped by P1-P4 priorities with clear phases

✅ **Dependencies documented**: Critical path and phase dependencies clearly shown

✅ **Independent testing**: Each user story includes independent test criteria and checkpoints
