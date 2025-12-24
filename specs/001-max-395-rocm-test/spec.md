# Feature Specification: AMD AI Max+ 395 ROCm Testing

**Feature Branch**: `001-max-395-rocm-test`  
**Created**: 2025-12-23  
**Status**: Draft  
**Input**: User description: "AMD AI Max+ 395, 128 GB VRAM für test mit llms/rag via Lemonade mit ROCm-Builds aus windows 11"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Basic LLM Inference Validation (Priority: P1) 🎯 MVP

A developer or researcher needs to validate that LLMs run correctly on AMD AI Max+ 395 hardware using ROCm backend on Windows 11, establishing baseline functionality before more complex testing.

**Why this priority**: This is the foundation for all other testing. Without basic inference working, no other scenarios are possible. Provides immediate value by confirming the hardware and software stack are properly configured.

**Independent Test**: Can be fully tested by loading a pre-configured GGUF model (e.g., Llama-3.2-1B-Instruct), running a single inference request via CLI or API, and verifying correct output. Delivers the core value of "LLMs work on this hardware."

**Acceptance Scenarios**:

1. **Given** Lemonade Server installed on Windows 11 with AMD AI Max+ 395 and ROCm drivers, **When** user runs `lemonade-server run Llama-3.2-1B-Instruct-GGUF --llamacpp rocm`, **Then** model loads successfully and generates coherent text response within expected timeframe
2. **Given** a running Lemonade Server with ROCm backend, **When** user sends OpenAI-compatible API request to `http://localhost:8000/api/v1/chat/completions`, **Then** server returns properly formatted response with generated text
3. **Given** AMD AI Max+ 395 with 128GB VRAM, **When** loading a large model (e.g., 30B+ parameters), **Then** system utilizes VRAM efficiently without crashes or memory errors
4. **Given** basic inference working, **When** user runs the same model with different prompts, **Then** outputs vary appropriately and maintain coherence

---

### User Story 2 - Performance Benchmarking (Priority: P2)

A developer needs to measure and validate inference performance (tokens/second, latency, throughput) on AMD AI Max+ 395 with ROCm to understand hardware capabilities and compare against other backends.

**Why this priority**: Performance validation is critical for production deployment decisions and hardware optimization. Builds on P1's basic functionality to provide quantitative metrics.

**Independent Test**: Can be tested independently by running the Lemonade CLI benchmarking tools (`lemonade` CLI with perplexity, power profiling) on a working Lemonade installation. Delivers performance insights without requiring RAG or multi-model features.

**Acceptance Scenarios**:

1. **Given** basic inference working (P1 complete), **When** user runs perplexity benchmark using `lemonade` CLI, **Then** system reports tokens/second, latency percentiles (p50, p95, p99), and VRAM utilization
2. **Given** multiple model sizes available, **When** benchmarking 7B, 13B, and 30B+ models, **Then** performance metrics scale predictably with model size
3. **Given** ROCm backend enabled, **When** comparing against CPU or Vulkan backends, **Then** ROCm shows measurable performance advantage for large models
4. **Given** continuous inference load, **When** running for extended periods (1+ hours), **Then** performance remains stable without degradation or thermal throttling

---

### User Story 3 - RAG Pipeline Integration (Priority: P3)

A developer needs to test Retrieval-Augmented Generation (RAG) workflows on AMD AI Max+ 395, validating that LLMs can effectively process retrieved context and generate accurate responses.

**Why this priority**: RAG represents a common production use case but builds on basic inference and performance validation. Lower priority because it requires external components (vector DB, embeddings) beyond core Lemonade functionality.

**Independent Test**: Can be tested by setting up a simple RAG pipeline (e.g., using Lemonade with local vector store), submitting queries that require context retrieval, and verifying response accuracy. Delivers RAG-specific validation without requiring multi-model or advanced features.

**Acceptance Scenarios**:

1. **Given** Lemonade Server running with ROCm backend, **When** RAG application sends queries with retrieved context chunks, **Then** LLM generates responses that accurately incorporate the provided context
2. **Given** a document corpus indexed in vector store, **When** submitting queries requiring factual information from documents, **Then** RAG pipeline retrieves relevant chunks and LLM generates accurate answers
3. **Given** context windows of varying sizes (4K, 8K, 16K+ tokens), **When** passing retrieved context to LLM, **Then** system handles context efficiently without errors or truncation issues
4. **Given** streaming enabled for RAG responses, **When** user requests real-time output, **Then** tokens stream smoothly without blocking on context processing

---

### User Story 4 - Multi-Model Testing (Priority: P4)

A developer needs to test multiple LLM models simultaneously or switch between models rapidly to compare outputs, validate consistency, and test specialized models (e.g., embedding models alongside generation models).

**Why this priority**: Useful for advanced testing and comparison but not essential for basic ROCm validation. Lower priority because most users start with single-model testing.

**Independent Test**: Can be tested by loading multiple models via Lemonade's multi-model support, sending requests to different models concurrently, and verifying each returns correct responses without interference. Delivers multi-model capability validation independently.

**Acceptance Scenarios**:

1. **Given** AMD AI Max+ 395 with 128GB VRAM, **When** loading multiple models (e.g., 2-3 models totaling <100GB), **Then** all models load successfully and respond to requests concurrently
2. **Given** multiple models loaded, **When** sending requests to specific models via model name in API, **Then** correct model responds without cross-contamination
3. **Given** models of different types (generation, embedding, instruction-tuned), **When** routing requests appropriately, **Then** each model performs its specialized task correctly
4. **Given** limited VRAM scenarios, **When** attempting to load too many models, **Then** system provides clear error messages about VRAM exhaustion


### Edge Cases

- What happens when ROCm drivers are outdated or misconfigured on Windows 11?
- How does system handle VRAM exhaustion when loading models that exceed 128GB?
- What occurs when switching between ROCm and other backends (Vulkan, CPU) mid-session?
- How does system behave with corrupted or incomplete model files?
- What happens during concurrent inference requests under heavy load?
- How does system handle Windows 11 system updates or driver updates while Lemonade Server is running?
- What occurs when network connections drop during model downloads from Hugging Face Hub?
- How does system respond to invalid or malformed OpenAI API requests?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST successfully install and run Lemonade Server on Windows 11 with AMD AI Max+ 395 hardware
- **FR-002**: System MUST support ROCm backend selection via CLI flag (`--llamacpp rocm`) for GGUF models
- **FR-003**: System MUST detect and utilize AMD AI Max+ 395's 128GB VRAM for model loading and inference
- **FR-004**: System MUST load GGUF models (minimum 1B parameters, recommended up to 70B parameters) using llama.cpp with ROCm
- **FR-005**: System MUST process inference requests via OpenAI-compatible API (`/chat/completions`) with ROCm backend
- **FR-006**: System MUST support both streaming and non-streaming inference modes with ROCm
- **FR-007**: System MUST provide CLI commands for model download (`lemonade-server pull`), execution (`lemonade-server run`), and listing (`lemonade-server list`)
- **FR-008**: System MUST report VRAM utilization, inference speed (tokens/second), and latency metrics during execution
- **FR-009**: System MUST handle graceful degradation when VRAM is insufficient for requested model size
- **FR-010**: System MUST maintain compatibility with Python 3.10-3.13 on Windows 11
- **FR-011**: System MUST support RAG workflows by accepting and processing extended context windows (up to model's maximum)
- **FR-012**: System MUST enable multi-model loading and concurrent inference when VRAM permits
- **FR-013**: System MUST log ROCm initialization, model loading events, inference requests, and errors with structured logging
- **FR-014**: System MUST provide clear error messages for ROCm driver issues, VRAM exhaustion, or model incompatibilities
- **FR-015**: System MUST persist model files locally to avoid repeated downloads across testing sessions

### Key Entities

- **Hardware Configuration**: AMD AI Max+ 395 GPU with 128GB VRAM, gfx1151 architecture, Windows 11 host system
- **Software Stack**: Lemonade Server, ROCm drivers (Windows 11 builds), llama.cpp with ROCm support, ONNX Runtime GenAI (optional)
- **Model Artifacts**: GGUF model files (quantized LLMs), ONNX model files (optional), model metadata (context length, parameter count, quantization level)
- **Inference Request**: User prompt/message, model selection, generation parameters (temperature, max tokens), streaming preference
- **Inference Response**: Generated tokens, metadata (tokens/second, latency), VRAM usage statistics, completion status
- **Performance Metrics**: Tokens per second (generation speed), latency (time to first token, total time), VRAM utilization, perplexity scores
- **RAG Context**: Retrieved document chunks, embeddings, vector store queries, context injection into prompts

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Successfully load and run at least 3 different GGUF models (small 1-3B, medium 7-13B, large 30B+) on AMD AI Max+ 395 with ROCm backend on Windows 11
- **SC-002**: Achieve inference performance of at least 20 tokens/second for 7B models and 5+ tokens/second for 30B+ models using ROCm
- **SC-003**: Utilize 80%+ of available 128GB VRAM when loading maximum model sizes without system instability
- **SC-004**: Complete RAG workflows with context windows of 8K+ tokens while maintaining coherent, accurate responses
- **SC-005**: Successfully run concurrent inference on 2+ models simultaneously without errors or response degradation
- **SC-006**: Achieve 95%+ uptime during extended testing sessions (4+ hours continuous inference)
- **SC-007**: Reduce time-to-first-token latency to under 2 seconds for streaming responses on 7B models
- **SC-008**: Generate accurate responses (manually validated) for at least 90% of test prompts across diverse topics
- **SC-009**: Successfully switch between ROCm, Vulkan, and CPU backends without requiring system restart or reconfiguration
- **SC-010**: Complete full testing cycle (installation, model download, inference, benchmarking, RAG validation) in under 2 hours for new setup

## Assumptions

- Windows 11 is fully updated with latest AMD ROCm drivers compatible with AI Max+ 395
- Network connectivity is available for initial model downloads from Hugging Face Hub
- User has administrator privileges on Windows 11 for driver installation and system configuration
- Testing focuses on text generation LLMs; multimodal models (image, audio) are out of scope
- ROCm performance will exceed CPU and potentially match or exceed Vulkan for large models on this hardware
- VRAM capacity (128GB) is sufficient for testing largest commonly available GGUF models (up to 70B parameters)
- RAG testing will use external vector store (not part of Lemonade); Lemonade's role is LLM inference only
- Performance benchmarks assume system is dedicated to Lemonade testing (minimal background processes)

## Dependencies

- AMD ROCm drivers for Windows 11 with gfx1151 support
- Lemonade Server installation package (latest stable version)
- Python 3.10-3.13 runtime on Windows 11
- GGUF model files (downloadable via Lemonade Model Manager or Hugging Face Hub)
- Network access to Hugging Face Hub for model downloads
- Sufficient disk space for model storage (200GB+ recommended for multiple large models)
- Optional: Vector database (for RAG testing) - Chroma, FAISS, or similar
- Optional: RAG framework integration - LangChain, LlamaIndex, or custom implementation

## Out of Scope

- ONNX model testing (focus is ROCm via llama.cpp for GGUF models)
- NPU testing (AMD AI Max+ 395's NPU is separate from GPU ROCm testing)
- Fine-tuning or training models (inference-only testing)
- Multimodal models (vision, audio) - text-only LLMs
- Production deployment configuration (focus is validation testing, not production hardening)
- Custom model quantization or conversion (use pre-quantized GGUF models)
- Comparison with NVIDIA hardware (focus is validating AMD hardware capabilities)
- UI/frontend testing (CLI and API testing only)
- Integration with specific applications beyond generic RAG validation

