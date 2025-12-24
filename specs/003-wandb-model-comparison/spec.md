# Feature Specification: LLM Model Comparison Dashboard

**Feature Branch**: `003-wandb-model-comparison`
**Created**: 2025-12-24
**Status**: Draft
**Input**: User description: "Workflow („verschiedene Modelle / Quant‑Stufen / MoE‑Configs auf Ryzen AI vergleichen"): W&B als Haupt‑Dashboard . später vielleicht zeno"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Compare Model Performance Across Configurations (Priority: P1)

A machine learning engineer wants to evaluate multiple LLM models with different quantization levels and MoE (Mixture of Experts) configurations running on Ryzen AI hardware. They need to see performance metrics, accuracy scores, and resource utilization in a centralized dashboard to make informed decisions about which model configuration to deploy.

**Why this priority**: This is the core value proposition - enabling systematic comparison of model variants to identify the optimal configuration for production deployment. Without this, users cannot make data-driven model selection decisions.

**Independent Test**: Can be fully tested by running evaluation benchmarks on at least two different model configurations and verifying that comparative metrics appear in the dashboard. Delivers immediate value by showing which model performs better.

**Acceptance Scenarios**:

1. **Given** multiple LLM models are available for testing, **When** the user runs evaluation workflows on each model with different quantization settings, **Then** all evaluation results are collected and displayed in a unified dashboard view
2. **Given** evaluation results exist for multiple configurations, **When** the user views the dashboard, **Then** they can see side-by-side comparisons of accuracy, inference speed, memory usage, and other key metrics
3. **Given** a model is evaluated with different MoE configurations, **When** the results are logged, **Then** the dashboard clearly distinguishes between different MoE settings and their impact on performance

---

### User Story 2 - Track Evaluation Progress and History (Priority: P2)

A researcher wants to monitor long-running evaluation tasks and review historical comparison data to understand how different model architectures perform over time and across different benchmark suites.

**Why this priority**: Evaluation runs can take hours or days. Users need visibility into progress and the ability to analyze trends. This builds on P1 by adding temporal context and run management.

**Independent Test**: Can be tested independently by starting an evaluation run and verifying that progress indicators update in real-time, and that completed runs remain accessible in the dashboard history.

**Acceptance Scenarios**:

1. **Given** an evaluation workflow is in progress, **When** the user checks the dashboard, **Then** they see real-time progress indicators showing which benchmarks are complete and which are running
2. **Given** multiple evaluation runs have been completed over time, **When** the user accesses the dashboard, **Then** they can view and compare results from previous runs
3. **Given** an evaluation fails or encounters errors, **When** the user views the dashboard, **Then** error information is clearly displayed with enough detail to diagnose issues

---

### User Story 3 - Export and Share Comparison Reports (Priority: P3)

A team lead wants to export comparison data and generate reports to share findings with stakeholders who may not have direct dashboard access, or to document model selection decisions for compliance purposes.

**Why this priority**: While viewing data in the dashboard is essential (P1, P2), sharing and exporting enables collaboration and documentation. This is valuable but not required for the core comparison workflow.

**Independent Test**: Can be tested by generating an export from existing dashboard data and verifying that the exported format contains all relevant metrics and is readable by stakeholders.

**Acceptance Scenarios**:

1. **Given** evaluation results exist in the dashboard, **When** the user requests an export, **Then** a structured report is generated containing all comparison metrics and visualizations
2. **Given** a comparison report has been exported, **When** stakeholders review it, **Then** they can understand model performance differences without needing dashboard access
3. **Given** multiple model configurations have been evaluated, **When** generating a report, **Then** the user can select which configurations to include in the comparison

---

### Edge Cases

- What happens when evaluation runs are interrupted or the Ryzen AI hardware becomes unavailable mid-benchmark?
- How does the system handle cases where different models use incompatible evaluation metrics or benchmark suites?
- What happens when the dashboard receives results faster than they can be processed and displayed?
- How are extremely large result datasets handled without degrading dashboard performance?
- What occurs when users try to compare models evaluated with significantly different benchmark configurations?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST collect evaluation metrics from LLM benchmark runs including accuracy scores, inference latency, throughput, and resource utilization
- **FR-002**: System MUST support comparison of models with different quantization levels (e.g., INT8, INT4, FP16, FP32)
- **FR-003**: System MUST distinguish between different MoE (Mixture of Experts) configurations in evaluation results
- **FR-004**: System MUST provide a centralized dashboard interface for viewing all evaluation results
- **FR-005**: System MUST enable side-by-side comparison of multiple model configurations simultaneously
- **FR-006**: System MUST display real-time progress updates for ongoing evaluation runs
- **FR-007**: System MUST retain historical evaluation data for trend analysis
- **FR-008**: System MUST integrate with Weights & Biases (W&B) as the primary dashboard platform
- **FR-009**: System MUST support evaluation workflows specifically designed for Ryzen AI hardware
- **FR-010**: System MUST handle evaluation runs using LM Evaluation Harness or equivalent benchmarking tools
- **FR-011**: System MUST allow users to filter and group results by model type, quantization level, MoE configuration, or custom tags
- **FR-012**: System MUST provide export functionality for evaluation results and comparison reports
- **FR-013**: System MUST capture and display error information when evaluation runs fail
- **FR-014**: System MUST support MMLU and HellaSwag benchmarks by default, with other benchmark suites available as optional configurations
- **FR-015**: System MUST limit initial release to predefined standard evaluation metrics, with custom metrics support planned for a future phase

### Key Entities

- **Evaluation Run**: Represents a single benchmark execution session, including model identifier, configuration parameters (quantization, MoE settings), hardware details, timestamp, status, and associated metrics
- **Model Configuration**: Represents a specific combination of model architecture, quantization level, and MoE settings that can be evaluated and compared
- **Benchmark Result**: Contains performance metrics from a single benchmark test within an evaluation run, including accuracy scores, latency measurements, resource utilization data
- **Comparison Set**: A user-defined grouping of evaluation runs selected for side-by-side analysis, enabling targeted comparisons of specific configurations

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can identify the best-performing model configuration within 5 minutes of all evaluation runs completing
- **SC-002**: The dashboard displays results from at least 10 concurrent model evaluation runs without performance degradation
- **SC-003**: 90% of evaluation metrics are updated in the dashboard within 30 seconds of being logged
- **SC-004**: Users can compare results across at least 20 different model configurations in a single dashboard view
- **SC-005**: Historical evaluation data remains accessible and searchable for at least 6 months
- **SC-006**: Exported comparison reports contain all relevant metrics and are comprehensible to stakeholders without additional explanation in 95% of cases
- **SC-007**: The time to set up and run a new model comparison is reduced by 60% compared to manual benchmarking and result aggregation

## Technology Context (2025)

### Weights & Biases (W&B)
- **W&B Weave**: Visual and interactive toolkit for evaluating, monitoring, and iterating on AI applications with one-line code integration
- **Evaluation Framework**: Supports scoring across multiple dimensions including accuracy, latency, cost, and user experience
- **Automatic Versioning**: Tracks changes between experiments, enabling reproducibility and collaboration
- **Industry-Standard Scorers**: Comes with built-in scorers and supports custom scorer definitions
- **LLM-as-a-Judge**: Recent feature enabling automated evaluation feedback loops

### LM Evaluation Harness (2025)
- **Latest Features**: SGLang support (Feb 2025), HF model steering (Mar 2025), CoT reasoning trace support via `think_end_token` (Jul 2025)
- **Multimodal Support**: Text+image multimodal input tasks with hf-multimodal and vllm-vlm model types
- **Chat Template Improvements**: Enhanced handling for likelihood and multiple-choice tasks
- **API Model Support**: Batched and async requests with easier customization
- **Backend**: Powers Hugging Face's Open LLM Leaderboard and used by NVIDIA, Cohere, BigScience, and others

### AMD Ryzen AI (2025)
- **Ryzen AI Max+ 395**: Delivers up to 61 TPS on Phi-3.5, up to 12.2x faster than competitors on 14B parameter models
- **Hybrid Architecture**: Combines NPU (50+ TOPS) for compute-intensive prefill phase with iGPU for bandwidth-sensitive decode phase
- **Large Model Support**: Variable Graphics Memory upgrade enables up to 128B parameter models with 96GB VGM on Windows
- **MLPerf Client Benchmarks**: Sub-second TTFT for most workloads, competitive LLM inference performance
- **AMD Quark**: Quantization toolkit for inference acceleration on Ryzen AI NPU

### Zeno Platform
- **Interactive Evaluation**: General-purpose framework combining Python API with interactive UI
- **Modular Views**: Supports diverse use cases from object detection to chatbot conversations
- **Error Discovery**: Advanced techniques like slice finder to automatically surface systematic failures
- **Rich Reporting**: Create visualizations and reports from exploration to presentation
- **Open Source**: Developed by CMU researchers, available at zenoml.com

## Assumptions

- Users have access to Weights & Biases accounts and appropriate API credentials, with W&B Weave available
- Ryzen AI hardware (preferably Ryzen AI Max+ or HX series) is properly configured and accessible for running evaluations
- LLM models to be evaluated are already available in compatible formats for LM Evaluation Harness
- Users have basic familiarity with LLM evaluation concepts and benchmark metrics
- Network connectivity is available for logging results to W&B dashboard
- MMLU and HellaSwag benchmarks are appropriate for the models being tested (default suite)
- Evaluation runs are automated workflows that can log results programmatically via W&B Weave
- Future integration with Zeno platform is desired but not required for initial release
- Users may leverage AMD Ryzen AI hybrid NPU+iGPU architecture for optimal inference performance
- Custom metrics support will be implemented in a future phase, not in the initial MVP

## Dependencies

- Weights & Biases platform availability and API stability
- LM Evaluation Harness or equivalent benchmarking framework compatibility
- Ryzen AI hardware drivers and runtime environment
- Access to model repositories and benchmark datasets

## Out of Scope

- Development or modification of LLM models themselves
- Creation of new benchmark suites or evaluation methodologies
- Hardware performance tuning or Ryzen AI optimization
- Model training workflows (focus is on evaluation only)
- Automated model deployment based on comparison results
- Real-time inference monitoring (focus is on benchmark evaluation, not production monitoring)
- Integration with platforms other than W&B in initial release (Zeno integration is future consideration)

## References

### Weights & Biases (W&B)
- [W&B Weave Platform](https://wandb.ai/site/weave/)
- [W&B Evaluations](https://wandb.ai/site/evaluations/)
- [Building Robust LLM Evaluation Frameworks](https://www.zenml.io/llmops-database/building-robust-llm-evaluation-frameworks-w-b-s-evaluation-driven-development-approach)
- [LLM Apps Evaluation Course](https://wandb.ai/site/courses/evals/)
- [W&B Documentation](https://docs.wandb.ai/)

### LM Evaluation Harness
- [GitHub Repository](https://github.com/EleutherAI/lm-evaluation-harness)
- [Release Notes](https://github.com/EleutherAI/lm-evaluation-harness/releases)
- [EleutherAI LLM Evaluation Project](https://www.eleuther.ai/projects/large-language-model-evaluation)
- [Evaluation Guide for Local Server (Medium)](https://medium.com/@kimdoil1211/evaluating-llm-accuracy-with-lm-evaluation-harness-for-local-server-a-comprehensive-guide-933df1361d1d)
- [PyPI Package](https://pypi.org/project/lm-eval/)

### AMD Ryzen AI
- [MLPerf Client Performance on Ryzen AI](https://www.amd.com/en/developer/resources/technical-articles/2025/unlocking-peak-ai-performance-with-mlperf-client-on-ryzen-ai-.html)
- [Ryzen AI Max+ 395 Announcement](https://www.amd.com/en/blogs/2025/amd-ryzen-ai-max-395-processor-breakthrough-ai-.html)
- [128B Parameter LLM Support with LM Studio](https://www.amd.com/en/blogs/2025/amd-ryzen-ai-max-upgraded-run-up-to-128-billion-parameter-llms-lm-studio.html)
- [AMD Quark Inference Acceleration](https://www.amd.com/en/developer/resources/technical-articles/2025/ai-inference-acceleration-on-ryzen-ai-with-quark.html)
- [RAG with Hybrid LLM on Ryzen AI](https://www.amd.com/en/developer/resources/technical-articles/2025/rag-with-hybrid-llm-on-amd-ryzen-ai-processors.html)
- [LLM Performance Comparison (Tom's Hardware)](https://www.tomshardware.com/pc-components/cpus/amd-ryzen-ai-9-hx-375-outperforms-intels-core-ultra-7-258v-in-llm-performance-team-red-provided-benchmarks-show-a-strong-lead-of-up-to-27-percent-in-lm-studio)

### Zeno Platform
- [Zeno AI Evaluation Platform](https://zenoml.com/)
- [Zeno Hub](https://hub.zenoml.com/home)
- [CMU FLAME Research Project](https://www.cmu.edu/flame/research/2024/zeno.html)
- [GitHub Repository](https://github.com/zeno-ml/zeno)
- [Mozilla Foundation Feature](https://www.mozillafoundation.org/en/blog/zeno-an-interactive-tool-for-ai-model-evaluation/)
