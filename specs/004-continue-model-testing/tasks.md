# Tasks: Continue Extension Model Testing Framework

**Input**: Design documents from `/specs/004-continue-model-testing/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Unit tests included for critical components. Integration tests will be manual per the hybrid testing approach.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**Best Practices Applied** (December 2025):
- **pytest** for testing framework ([GeeksforGeeks](https://www.geeksforgeeks.org/python/best-python-testing-frameworks/), [BrowserStack](https://www.browserstack.com/guide/top-python-testing-frameworks))
- **psutil 7.2.0** for system monitoring ([PyPI](https://pypi.org/project/psutil/))
- **Yamale/jsonschema** for YAML validation ([MoldStud](https://moldstud.com/articles/p-yaml-file-validation-best-practices-to-ensure-configuration-accuracy))

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- Project root: `scripts/benchmarks/continue-testing/`
- Tests: `tests/` at repository root
- Config: `scripts/benchmarks/continue-testing/config/`
- Results: `scripts/benchmarks/continue-testing/results/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create directory structure at scripts/benchmarks/continue-testing/ per plan.md
- [x] T002 Create config subdirectories: scripts/benchmarks/continue-testing/config/, scripts/benchmarks/continue-testing/utils/, scripts/benchmarks/continue-testing/results/
- [x] T003 [P] Create results subdirectories: scripts/benchmarks/continue-testing/results/test_runs/, scripts/benchmarks/continue-testing/results/freeze_events/, scripts/benchmarks/continue-testing/results/reports/
- [x] T004 [P] Add pyadl to setup.py extras_require['continue_testing'] for AMD GPU monitoring
- [x] T005 [P] Add yamale to setup.py extras_require['continue_testing'] for YAML schema validation
- [x] T006 [P] Create README.md at scripts/benchmarks/continue-testing/README.md with quickstart reference

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Data Model Foundation

- [x] T007 [P] Create SystemMetrics dataclass in scripts/benchmarks/continue-testing/metrics_collector.py following data-model.md
- [x] T008 [P] Create HardwareConfiguration dataclass in scripts/benchmarks/continue-testing/model_manager.py
- [x] T009 [P] Create TestRun dataclass in scripts/benchmarks/continue-testing/model_manager.py
- [x] T010 [P] Create TestInteraction dataclass in scripts/benchmarks/continue-testing/model_manager.py
- [x] T011 [P] Create FreezeEvent dataclass in scripts/benchmarks/continue-testing/freeze_detector.py
- [x] T012 [P] Create PerformanceMetrics dataclass in scripts/benchmarks/continue-testing/report_generator.py
- [x] T013 [P] Create CompatibilityResult dataclass in scripts/benchmarks/continue-testing/report_generator.py

### Configuration Infrastructure

- [x] T014 Create models.yaml schema at scripts/benchmarks/continue-testing/config/models.yaml with 3 example models (Qwen, DeepSeek, Llama)
- [x] T015 [P] Create test_scenarios.yaml schema at scripts/benchmarks/continue-testing/config/test_scenarios.yaml with P1 scenarios
- [x] T016 [P] Create hardware.yaml template at scripts/benchmarks/continue-testing/config/hardware.yaml
- [x] T017 Implement YAML config validator using yamale in scripts/benchmarks/continue-testing/model_manager.py:validate_config()
- [x] T018 [P] Create ConfigLoader class in scripts/benchmarks/continue-testing/model_manager.py with load_models(), load_scenarios(), load_hardware()

### Monitoring Infrastructure

- [x] T019 Implement SystemMonitor class in scripts/benchmarks/continue-testing/metrics_collector.py based on ryzen_benchmark_with_metrics.py patterns
- [x] T020 Implement SystemMonitor.sample() method using psutil for CPU/RAM metrics
- [x] T021 [P] Implement SystemMonitor._sample_npu() method using xrt-smi subprocess with JSON parsing (from research.md)
- [x] T022 [P] Implement SystemMonitor._sample_amd_gpu() method using pyadl if available
- [x] T023 Implement SystemMonitor.sample_continuous() for background monitoring with threading
- [x] T024 [P] Add unit tests for SystemMonitor in tests/unit/test_metrics_collector.py using pytest

### Logging and Error Handling

- [x] T025 Setup structured logging configuration in scripts/benchmarks/continue-testing/test_runner.py using Python logging module
- [x] T026 [P] Implement error handling base classes in scripts/benchmarks/continue-testing/utils/__init__.py (ConfigError, MonitoringError, FreezeDetectionError)
- [x] T027 [P] Create diagnostic data collection helper in scripts/benchmarks/continue-testing/utils/diagnostics.py:collect_system_snapshot()

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Model Compatibility Validation (Priority: P1) 🎯 MVP

**Goal**: Identify which coder models work reliably with AMD Ryzen AI hardware without freezing

**Independent Test**: Run test_runner.py with a single model for 10 interactions and verify:
1. Test completes without freezing
2. Compatibility result JSON is generated
3. Results contain model name, test count, freeze status

**Acceptance Criteria** (from spec.md):
- Test 3 models (Qwen 2.5 Coder, DeepSeek Coder v2, Llama 3.2) on AMD Ryzen AI hardware
- 10 consecutive interactions complete without freezing for compatible models
- Compatibility matrix generated showing which models work

### Unit Tests for US1

- [x] T028 [P] [US1] Create pytest tests for ModelManager in tests/unit/test_model_manager.py (config loading, validation)
- [x] T029 [P] [US1] Create pytest tests for TestRunner basic orchestration in tests/unit/test_runner_basic.py

### Implementation for US1

- [x] T030 [P] [US1] Implement ModelManager class in scripts/benchmarks/continue-testing/model_manager.py
- [x] T031 [US1] Implement ModelManager.load_model_config() to parse models.yaml
- [x] T032 [US1] Implement ModelManager.get_model_by_name() lookup method
- [x] T033 [P] [US1] Implement InteractiveTestRunner class in scripts/benchmarks/continue-testing/test_runner.py
- [x] T034 [US1] Implement InteractiveTestRunner.run_interactive_test_session() with CLI prompts (from quickstart.md)
- [x] T035 [US1] Implement InteractiveTestRunner._prompt_for_interaction() to guide user through manual testing
- [x] T036 [US1] Implement InteractiveTestRunner._record_interaction() to log TestInteraction data
- [x] T037 [US1] Implement TestResultWriter class in scripts/benchmarks/continue-testing/utils/result_writer.py
- [x] T038 [US1] Implement TestResultWriter.save_test_run() to write JSON results to results/test_runs/
- [x] T039 [US1] Add argparse CLI in scripts/benchmarks/continue-testing/test_runner.py with --model, --interactions, --interactive flags
- [x] T040 [US1] Add hardware auto-detection on first run using SystemMonitor and save to hardware.yaml
- [x] T041 [US1] Implement basic compatibility assessment in scripts/benchmarks/continue-testing/report_generator.py:assess_compatibility()
- [x] T042 [US1] Generate compatibility matrix JSON in scripts/benchmarks/continue-testing/report_generator.py:generate_matrix()

**Checkpoint**: At this point, User Story 1 should allow manual testing of models and generate compatibility results

---

## Phase 4: User Story 2 - Freeze Detection and Diagnosis (Priority: P1)

**Goal**: Detect when Continue freezes and collect comprehensive diagnostic data

**Independent Test**: Trigger a freeze scenario (or simulate timeout), verify:
1. Freeze is detected within 30 seconds
2. FreezeEvent JSON created with full diagnostics
3. System metrics captured at freeze time

**Acceptance Criteria** (from spec.md):
- Log all responses and identify freeze request number
- Capture memory, NPU/GPU utilization, error logs at freeze
- Identify common freeze patterns across multiple runs

### Unit Tests for US2

- [x] T043 [P] [US2] Create pytest tests for FreezeDetector in tests/unit/test_freeze_detector.py (timeout detection, log analysis)

### Implementation for US2

- [X] T044 [P] [US2] Implement FreezeDetector class in scripts/benchmarks/continue-testing/freeze_detector.py
- [X] T045 [US2] Implement FreezeDetector.monitor_interaction() with timeout tracking
- [X] T046 [US2] Implement FreezeDetector.detect_from_timeout() method
- [X] T047 [P] [US2] Implement FreezeDetector.detect_from_logs() to parse Continue logs for errors
- [X] T048 [US2] Implement find_continue_process() in scripts/benchmarks/continue-testing/utils/vscode_bridge.py using psutil.process_iter()
- [X] T049 [US2] Implement ContinueLogMonitor class in scripts/benchmarks/continue-testing/utils/vscode_bridge.py
- [X] T050 [US2] Implement ContinueLogMonitor.get_log_paths() to find Continue extension logs
- [X] T051 [US2] Implement ContinueLogMonitor.parse_logs() to extract errors and timestamps
- [X] T052 [US2] Implement collect_freeze_diagnostics() in scripts/benchmarks/continue-testing/freeze_detector.py
- [X] T053 [US2] Collect system snapshot (metrics, process state, logs) in FreezeEvent
- [X] T054 [US2] Save FreezeEvent to results/freeze_events/freeze_{id}.json
- [X] T055 [US2] Integrate FreezeDetector into InteractiveTestRunner
- [X] T056 [US2] Add freeze detection to TestRunner.run_interactive_test_session()
- [X] T057 [US2] Display freeze diagnostics in CLI when detected
- [X] T058 [US2] Implement freeze pattern analysis in scripts/benchmarks/continue-testing/report_generator.py:analyze_freeze_patterns()
- [X] T059 [US2] Add freeze correlation analysis (message length, model type, resource usage)

**Checkpoint**: Freeze detection is fully functional, diagnostics captured automatically

---

## Phase 5: User Story 3 - RyzenAI Hardware Optimization (Priority: P2)

**Goal**: Verify models properly utilize NPU hardware acceleration

**Independent Test**: Run model test with NPU monitoring, verify:
1. NPU utilization metrics are non-zero during inference
2. Metrics logged to test run results
3. NPU metrics displayed in reports

**Acceptance Criteria** (from spec.md):
- NPU utilization metrics show hardware acceleration is active
- Models run with comparable performance to RyzenAI-SW benchmarks
- Resource usage stays within acceptable bounds

### Unit Tests for US3

- [x] T060 [P] [US3] Create pytest tests for NPUMonitor in tests/unit/test_npu_monitor.py (xrt-smi parsing, metric aggregation)

### Implementation for US3

- [X] T061 [P] [US3] Implement NPUMonitor class in scripts/benchmarks/continue-testing/utils/npu_monitor.py
- [X] T062 [US3] Implement NPUMonitor.sample_npu() using xrt-smi subprocess with temp file approach (from research.md)
- [X] T063 [US3] Implement NPUMonitor.parse_xrt_json() with numeric string handling
- [X] T064 [US3] Implement NPUMonitor.aggregate_metrics() using walk pattern from ryzen_benchmark_with_metrics.py
- [X] T065 [US3] Integrate NPUMonitor into SystemMonitor._sample_npu()
- [X] T066 [US3] Add NPU metrics to SystemMetrics dataclass (gops, command_submissions, utilization_percent)
- [X] T067 [US3] Display NPU utilization in real-time during test run
- [X] T068 [US3] Add NPU metrics to performance reports
- [X] T069 [US3] Implement NPU utilization validation in scripts/benchmarks/continue-testing/report_generator.py:validate_npu_usage()
- [X] T070 [US3] Compare NPU metrics against RyzenAI-SW benchmark baselines
- [X] T071 [US3] Add warning if NPU utilization is 0% (model not using acceleration)

**Checkpoint**: NPU monitoring integrated, hardware acceleration verified

---

## Phase 6: User Story 4 - Model Performance Benchmarking (Priority: P2)

**Goal**: Provide quantitative performance metrics for model comparison

**Independent Test**: Run 2 models through same test scenarios, verify:
1. Performance metrics calculated (response time p50/p95, tokens/sec)
2. Performance comparison report generated
3. Recommendations provided based on metrics

**Acceptance Criteria** (from spec.md):
- Metrics captured for response time, tokens/sec, task completion rate
- Performance comparison report generated
- Recommendations provided for optimal model selection

### Unit Tests for US4

- [x] T072 [P] [US4] Create pytest tests for PerformanceAnalyzer in tests/unit/test_performance_analyzer.py (metrics calculation, statistical aggregation)

### Implementation for US4

- [x] T073 [P] [US4] Implement PerformanceAnalyzer class in scripts/benchmarks/continue-testing/report_generator.py
- [x] T074 [US4] Implement PerformanceAnalyzer.calculate_aggregates() for mean, median, p95, p99
- [x] T075 [US4] Implement PerformanceAnalyzer.calculate_performance_metrics() for TestRun
- [x] T076 [US4] Calculate response_time_mean_ms, response_time_p50_ms, response_time_p95_ms, response_time_p99_ms
- [x] T077 [US4] Calculate tokens_per_second_mean, tokens_per_second_p50
- [x] T078 [US4] Calculate memory_peak_gb, npu_utilization_mean_percent, npu_utilization_max_percent
- [x] T079 [US4] Save PerformanceMetrics to results/performance/{run_id}_perf.json
- [x] T080 [US4] Implement ModelComparator class in scripts/benchmarks/continue-testing/report_generator.py
- [x] T081 [US4] Implement ModelComparator.compare_models() to aggregate metrics across runs
- [x] T082 [US4] Generate performance comparison table (model, tokens/sec, latency, NPU util)
- [x] T083 [US4] Implement ModelComparator.generate_recommendations() based on performance thresholds
- [x] T084 [US4] Add performance rating logic (excellent/good/fair/poor) per data-model.md
- [x] T085 [US4] Add stability rating logic (stable/mostly_stable/unstable)
- [x] T086 [US4] Generate performance_comparison.json in results/reports/
- [x] T087 [US4] Add --format option to report_generator.py CLI (json, markdown, csv)
- [x] T088 [US4] Implement markdown table output for performance reports

**Checkpoint**: Performance benchmarking complete, comparison reports generated

---

## Phase 7: User Story 5 - Automated Testing Framework (Priority: P3)

**Goal**: Enable scheduled/continuous model stability testing

**Independent Test**: Configure scheduled run, verify:
1. Test runs automatically at specified time/interval
2. Results logged with timestamps
3. Historical trends analyzed

**Acceptance Criteria** (from spec.md):
- Tests run on schedule with timestamps and config details
- Notifications generated on failures
- Degradation patterns identified over time

### Implementation for US5

- [x] T089 [P] [US5] Implement ScheduledTestRunner class in scripts/benchmarks/continue-testing/test_runner.py
- [x] T090 [US5] Add --schedule flag to test_runner.py CLI (cron-style syntax or interval)
- [x] T091 [US5] Implement ScheduledTestRunner.run_scheduled() with background loop
- [x] T092 [US5] Add timestamp-based result organization (results/continuous/{date}/)
- [x] T093 [P] [US5] Implement TrendAnalyzer class in scripts/benchmarks/continue-testing/report_generator.py
- [x] T094 [US5] Implement TrendAnalyzer.analyze_historical_runs() to load multiple test runs
- [x] T095 [US5] Implement TrendAnalyzer.detect_degradation() to find performance regressions
- [x] T096 [US5] Implement TrendAnalyzer.detect_improvements() to identify stability gains
- [x] T097 [US5] Generate trend analysis report in results/reports/trends_{date}.json
- [x] T098 [P] [US5] Implement NotificationHandler in scripts/benchmarks/continue-testing/report_generator.py
- [x] T099 [US5] Add email notification support for freeze events
- [x] T100 [US5] Add console notification for test failures
- [x] T101 [US5] Add Windows notification support (if available)
- [x] T102 [US5] Document scheduled testing setup in scripts/benchmarks/continue-testing/README.md

**Checkpoint**: Automated testing framework operational, continuous monitoring enabled

---

## Phase 8: W&B Integration (Optional Enhancement)

**Purpose**: Add Weights & Biases logging for metric visualization

- [x] T103 [P] Implement WandbLogger class in scripts/benchmarks/continue-testing/utils/wandb_logger.py based on evaluation/wandb_logger.py
- [x] T104 Create W&B project structure: lemonade-continue-testing/{model}/{quantization}
- [x] T105 Implement WandbLogger.log_test_run() to log TestRun data
- [x] T106 [P] Implement WandbLogger.log_metrics() to log SystemMetrics time series
- [x] T107 [P] Implement WandbLogger.log_freeze_event() with diagnostic data
- [x] T108 [P] Implement WandbLogger.log_performance_metrics() with comparison charts
- [x] T109 Add --wandb / --no-wandb flag to test_runner.py CLI
- [x] T110 Add offline W&B support for air-gapped environments
- [x] T111 Document W&B setup in quickstart.md

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T112 [P] Add docstrings to all classes and public methods following Google style
- [x] T113 [P] Add type hints to all function signatures (Python 3.10+ compatible)
- [x] T114 [P] Run pytest on all unit tests in tests/unit/ and verify >80% coverage
- [x] T115 Code cleanup and refactoring for DRY principles
- [x] T116 [P] Add input validation for all config files using yamale schemas
- [x] T117 [P] Add comprehensive error messages with troubleshooting hints
- [x] T118 Validate quickstart.md instructions with fresh environment test
- [x] T119 [P] Create example models.yaml with all 3 target models
- [x] T120 [P] Create example test_scenarios.yaml with P1 and P2 scenarios
- [x] T121 [P] Add logging level configuration (--verbose, --debug flags)
- [x] T122 Add progress bars for long-running operations using tqdm
- [x] T123 [P] Add graceful shutdown handling (Ctrl+C) with result preservation
- [X] T124 Performance optimization: reduce xrt-smi sampling overhead
- [X] T125 [P] Security: sanitize log output (no API keys, sensitive paths)
- [x] T126 Add version check for dependencies (psutil >= 6.1.1, pyadl, yamale)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - User Story 1 (P1): Can start after Foundational - No dependencies on other stories
  - User Story 2 (P1): Can start after Foundational - Integrates with US1 but independently testable
  - User Story 3 (P2): Can start after Foundational - Enhances US1 monitoring
  - User Story 4 (P2): Can start after Foundational - Requires US1 test data
  - User Story 5 (P3): Can start after US1 complete - Automates US1 testing
- **W&B Integration (Phase 8)**: Can start after US1 complete (optional)
- **Polish (Phase 9)**: Depends on desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Independent - can deliver as MVP
- **US2 (P1)**: Independent but integrates with US1 - can test separately
- **US3 (P2)**: Enhances US1 with NPU monitoring - independently testable
- **US4 (P2)**: Requires US1 test runs for comparison - independently testable
- **US5 (P3)**: Automates US1 - requires US1 complete

### Within Each User Story

- Unit tests → Models/dataclasses → Core logic → CLI integration → Reporting
- Foundation tasks complete before story-specific tasks
- [P] tasks within same phase can run in parallel

### Parallel Opportunities

**Phase 1 Setup**: T003, T004, T005, T006 can run in parallel

**Phase 2 Foundational**:
- Data models (T007-T013) can all run in parallel
- Config files (T015, T016) in parallel
- Monitoring methods (T021, T022) in parallel
- Tests (T024) in parallel

**User Story 1**:
- Unit tests (T028, T029) in parallel
- ModelManager + InteractiveTestRunner (T030, T033) in parallel

**User Story 2**:
- Log monitoring + process finding (T047, T048) in parallel

**User Story 3**:
- NPUMonitor unit tests while implementing other components

**User Story 4**:
- Metrics calculation + comparison logic can be developed in parallel

**All User Stories**: Can be worked on by different team members in parallel after Foundational phase

---

## Parallel Example: User Story 1

```bash
# Launch all unit tests for User Story 1 together:
Task: "Create pytest tests for ModelManager in tests/unit/test_model_manager.py"
Task: "Create pytest tests for TestRunner basic orchestration in tests/unit/test_runner_basic.py"

# Launch all core classes for User Story 1 together:
Task: "Implement ModelManager class in scripts/benchmarks/continue-testing/model_manager.py"
Task: "Implement InteractiveTestRunner class in scripts/benchmarks/continue-testing/test_runner.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 & 2 Only)

1. Complete Phase 1: Setup (T001-T006)
2. Complete Phase 2: Foundational (T007-T027) - CRITICAL
3. Complete Phase 3: User Story 1 - Model Compatibility (T028-T042)
4. Complete Phase 4: User Story 2 - Freeze Detection (T043-T059)
5. **STOP and VALIDATE**:
   - Test 3 models interactively
   - Verify freeze detection works
   - Generate compatibility matrix
6. Deploy/demo if ready

**Estimated MVP: ~40-50 tasks (T001-T059)**

### Incremental Delivery

1. MVP (US1 + US2) → Test and validate → Usable for troubleshooting
2. Add US3 (NPU monitoring) → Verify hardware utilization → Enhanced diagnostics
3. Add US4 (Performance benchmarking) → Compare models → Data-driven selection
4. Add US5 (Automation) → Continuous monitoring → Long-term stability tracking
5. Add W&B (Optional) → Visual dashboards → Team collaboration

### Parallel Team Strategy

With multiple developers:

1. **Week 1**: Team completes Setup + Foundational together (T001-T027)
2. **Week 2-3**: Once Foundational is done:
   - Developer A: User Story 1 (T028-T042)
   - Developer B: User Story 2 (T043-T059)
   - Developer C: User Story 3 (T060-T071)
3. **Week 4**: Integration testing and validation
4. **Week 5**: User Stories 4 & 5 + Polish

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Best practice**: Use pytest with parametrize for testing multiple models
- **Best practice**: Use psutil non-blocking methods (interval=None) for low overhead monitoring
- **Best practice**: Validate YAML configs with yamale schemas before parsing
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

---

## Total Task Count

- **Setup**: 6 tasks
- **Foundational**: 21 tasks
- **User Story 1 (P1)**: 15 tasks
- **User Story 2 (P1)**: 17 tasks
- **User Story 3 (P2)**: 11 tasks
- **User Story 4 (P2)**: 16 tasks
- **User Story 5 (P3)**: 14 tasks
- **W&B Integration**: 9 tasks (optional)
- **Polish**: 15 tasks

**Total**: 124 tasks
**MVP**: ~50 tasks (Setup + Foundational + US1 + US2)
**Parallel**: ~40 tasks marked [P]

---

## Suggested MVP Scope

**Minimum Viable Product**: User Stories 1 & 2 (Model Compatibility + Freeze Detection)

This delivers:
- ✅ Test 3 coder models for compatibility
- ✅ Detect and diagnose freezes
- ✅ Generate compatibility matrix
- ✅ Collect diagnostic data
- ✅ Manual interactive testing workflow

**Value**: Solves the immediate problem (identifying which models work reliably) with full diagnostic capabilities.
