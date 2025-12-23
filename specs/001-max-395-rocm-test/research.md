# Research: AMD AI Max+ 395 ROCm Testing

**Feature**: 001-max-395-rocm-test  
**Date**: 2025-12-23  
**Purpose**: Resolve technical unknowns and establish best practices for testing LLMs with ROCm on Windows 11

## Research Areas

### 1. ROCm Setup and Configuration on Windows 11

**Decision**: Use AMD ROCm 7.1.1+ HIP SDK for Windows with gfx1151 architecture support

**Rationale**:
- ROCm 7.1.1 is current stable release per https://rocm.docs.amd.com/en/latest/
- AMD AI Max+ 395 uses gfx1151 architecture (STX Halo per Lemonade README)
- Windows 11 ROCm support added in recent versions (HIP SDK for Windows)
- llama.cpp ROCm backend requires HIP SDK installation on Windows

**Alternatives Considered**:
- **Vulkan backend**: More mature on Windows, but ROCm offers better performance for large models according to AMD documentation
- **CPU-only testing**: Doesn't validate GPU capabilities
- **WSL2 with Linux ROCm**: Adds complexity, potential driver passthrough issues

**Key Findings from https://rocm.docs.amd.com/en/latest/**:
- ROCm 7.1.1 documentation references Windows HIP SDK installation
- Documentation covers Linux extensively; Windows docs at https://rocm.docs.amd.com/projects/install-on-windows/en/latest/
- gfx1151 architecture requires driver support confirmation
- Environment variables may be needed (e.g., `HSA_OVERRIDE_GFX_VERSION` if driver mismatch)

**Implementation Notes**:
- Install AMD ROCm HIP SDK for Windows from AMD developer site
- Verify GPU detection: `rocminfo` or `hipinfo` command
- Set environment variables if needed for gfx1151 recognition
- Test basic HIP functionality before Lemonade integration

### 2. llama.cpp ROCm Backend Integration

**Decision**: Use llama.cpp's built-in ROCm support via `--llamacpp rocm` flag in Lemonade Server

**Rationale**:
- Lemonade Server already integrates llama.cpp with ROCm support
- CLI flag `--llamacpp rocm` documented in Lemonade constitution and README
- GGUF models are widely available and compatible with llama.cpp
- No custom build required - Lemonade releases include ROCm-enabled llama.cpp

**Alternatives Considered**:
- **ONNX Runtime GenAI with ROCm**: More complex setup, less mature for text generation LLMs
- **Custom llama.cpp build**: Unnecessary - Lemonade packages pre-built ROCm support
- **FLM backend**: Targets NPU, not GPU (out of scope)

**Key Findings**:
- Lemonade Server run command syntax: `lemonade-server run MODEL_NAME --llamacpp rocm`
- Backend selection is per-execution, allowing comparison (ROCm vs Vulkan vs CPU)
- llama.cpp ROCm backend compiled with HIP for AMD GPU acceleration
- VRAM allocation handled automatically by llama.cpp

**Implementation Notes**:
- Default backend varies by platform; explicit `--llamacpp rocm` ensures ROCm usage
- Monitor VRAM with `rocm-smi` or Windows Task Manager GPU view
- Compare performance: run same model with `--llamacpp vulkan` and `--llamacpp rocm`

### 3. Performance Benchmarking Methodology

**Decision**: Use Lemonade CLI's built-in perplexity tool + custom Python scripts for comprehensive metrics

**Rationale**:
- Lemonade CLI (`lemonade`) includes perplexity benchmarking per docs/dev_cli/perplexity.md
- Perplexity provides model quality + performance metrics (tokens/sec)
- Custom scripts add latency measurement, VRAM monitoring, sustained load testing
- Industry-standard metrics (tokens/sec, p50/p95/p99 latency) for comparison

**Alternatives Considered**:
- **llama-bench (llama.cpp tool)**: Lower-level, requires manual compilation
- **OpenAI API load testing tools**: Focused on API overhead, not raw inference
- **Manual timing only**: Insufficient for statistical significance

**Key Findings**:
- Lemonade CLI perplexity command: `lemonade perplexity --model path --prompt-file prompts.txt`
- Outputs tokens/second, perplexity score, resource utilization
- Python `psutil` library provides cross-platform GPU memory monitoring
- OpenAI Python SDK streaming mode enables time-to-first-token measurement

**Implementation Notes**:
- Create standardized prompt set (50-100 prompts, varying lengths)
- Run multiple iterations for statistical confidence (5-10 runs per configuration)
- Collect metrics: tokens/sec (average, min, max), latency (p50, p95, p99), VRAM peak/average
- Document ambient conditions: background processes, GPU clock speeds, temperature

### 4. RAG Testing Approach

**Decision**: External RAG framework (LangChain or simple custom) with Lemonade as LLM backend only

**Rationale**:
- Lemonade's role is LLM inference, not RAG orchestration (per feature spec out-of-scope)
- OpenAI API compatibility allows drop-in replacement in existing RAG pipelines
- Testing validates LLM context handling, not vector store performance
- Simple custom RAG (retrieve → concat → prompt) sufficient for validation

**Alternatives Considered**:
- **Integrated RAG in Lemonade**: Out of scope, violates separation of concerns
- **No RAG testing**: Misses common production use case
- **Complex RAG framework**: Adds dependencies, testing complexity without benefit

**Key Findings**:
- RAG tests focus on: long context handling (8K+ tokens), factual accuracy with retrieved docs, streaming with context
- Vector store (chromadb, FAISS) optional - can use pre-retrieved fixed context for simplicity
- Test corpus: technical docs (e.g., Lemonade docs, ROCm docs) for ground-truth validation
- Success measured by response coherence and factual accuracy, not retrieval quality

**Implementation Notes**:
- Minimal RAG: Load document → split chunks → create 5-10 test queries → manually verify answers
- Use OpenAI SDK with `base_url="http://localhost:8000/api/v1"` for Lemonade integration
- Context window sizes: test 4K, 8K, 16K token contexts (model-dependent)
- Manual accuracy assessment: 3-point scale (correct, partial, wrong) for factual questions

### 5. Multi-Model Testing Strategy

**Decision**: Sequential loading and concurrent inference with VRAM budget management

**Rationale**:
- 128GB VRAM allows multiple models simultaneously (e.g., 2-3 large models)
- Test both scenarios: multiple loaded models + switching between single models
- Validates VRAM management, model routing, isolation
- Lemonade Server supports multi-model via model name in API request

**Alternatives Considered**:
- **Single model only**: Doesn't test VRAM management at scale
- **Maximum model count stress test**: Less practical, VRAM exhaustion expected behavior
- **Hot-swapping same model**: Doesn't test isolation

**Key Findings from Lemonade docs**:
- Multi-model support documented in docs/cpp/Multi-Model-Spec.md
- Model selection via `model` field in OpenAI API request
- VRAM allocation: models loaded independently, no automatic unloading
- Requires explicit model list at server start or dynamic loading API

**Implementation Notes**:
- Test combinations: 1x 30B + 1x 7B, 2x 13B + 1x 1B, 1x 70B solo
- Send concurrent requests to different models, verify correct routing
- Monitor VRAM per-model allocation (if tooling available)
- Test VRAM exhaustion scenario: attempt loading beyond 128GB, verify graceful error

### 6. Test Automation and CI/CD Considerations

**Decision**: pytest framework with manual execution initially, optional GitHub Actions CI later

**Rationale**:
- pytest is standard Python testing framework, well-documented
- Manual execution appropriate for hardware-specific testing (AMD AI Max+ 395)
- CI/CD requires self-hosted runner with identical hardware (complex setup)
- Focus on test reliability first, automation second

**Alternatives Considered**:
- **GitHub Actions**: Requires self-hosted runner with AMD AI Max+ 395 (infeasible for most)
- **No automation**: Manual testing error-prone, non-reproducible
- **Custom test runner**: Reinvents wheel, pytest sufficient

**Key Findings**:
- pytest fixtures enable shared Lemonade Server setup/teardown
- pytest markers (`@pytest.mark.slow`) allow selective test execution
- JSON output format (`--json-report`) enables result archiving
- Parallel execution (`pytest-xdist`) possible but VRAM contention risk

**Implementation Notes**:
- `conftest.py`: Server startup fixture, model download verification, result directory setup
- Test organization: one file per user story (P1-P4)
- Execution: `pytest tests/rocm_max395/test_basic_inference.py -v --json-report`
- CI/CD: Document setup for self-hosted runner, don't require it initially

## Summary of Decisions

| Decision Area | Choice | Key Reason |
|---------------|--------|------------|
| ROCm Version | 7.1.1+ HIP SDK | Current stable, Windows support |
| llama.cpp Integration | Built-in via `--llamacpp rocm` | Pre-packaged in Lemonade |
| Benchmarking | Lemonade CLI + custom scripts | Comprehensive metrics |
| RAG Approach | External minimal RAG | Focused on LLM validation |
| Multi-Model | Sequential + concurrent | VRAM management testing |
| Automation | pytest manual execution | Hardware-specific initially |

## Open Questions Resolved

✅ **ROCm driver installation process**: Use AMD HIP SDK for Windows installer  
✅ **Backend selection syntax**: `lemonade-server run MODEL --llamacpp rocm`  
✅ **Performance baseline expectations**: 20+ tok/s (7B), 5+ tok/s (30B+) per spec  
✅ **RAG framework choice**: Simple custom or LangChain, not Lemonade responsibility  
✅ **Multi-model API**: Use `model` field in OpenAI request, check Multi-Model-Spec.md  
✅ **Test automation platform**: pytest with optional CI/CD via self-hosted runner

## Next Steps (Phase 1)

With research complete, proceed to Phase 1:
1. **data-model.md**: Define schemas for test results, benchmarks, model configurations
2. **contracts/**: Create test execution and result reporting contracts
3. **quickstart.md**: Write setup guide for running first test
4. **Update agent context**: Add ROCm testing technology to Copilot context
