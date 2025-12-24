<!--
  SYNC IMPACT REPORT
  ==================
  Version: 1.0.0 → 1.0.1
  Date: 2025-12-24
  
  Changes:
  - Added explicit health and readiness endpoint requirement under OpenAI API Compatibility
  - Clarified observability requirements for server health endpoints
  
  Principles Affected:
  - I. OpenAI API Compatibility (clarification)
  
  Follow-up Actions:
  - Add tests and documentation references for `/api/v1/health` and `/api/v1/ready`
-->

# Lemonade SDK Constitution

## Core Principles

### I. OpenAI API Compatibility

All server endpoints MUST maintain OpenAI API compatibility to ensure seamless integration with existing LLM applications. The base URL `http://localhost:8000/api/v1` MUST support standard OpenAI client libraries across all languages (Python, C++, Java, C#, Node.js, Go, Ruby, Rust, PHP).

**Rationale**: Enables immediate adoption by existing AI applications without code changes, maximizing ecosystem integration and reducing friction for developers.

**Requirements**:
- Implement `/chat/completions` endpoint following OpenAI specification
- Support streaming and non-streaming responses
- Accept standard message formats and parameters
- Return OpenAI-compatible response structures
- Expose health and readiness endpoints: `/api/v1/health` (returns server status and loaded models) and `/api/v1/ready` (returns readiness state). These endpoints MUST be accessible at the base URL and included in tests, monitoring, and documentation.

### II. Multi-Backend Architecture

The system MUST support multiple inference backends (ONNX Runtime GenAI, llama.cpp, FLM) with runtime selection capability. Users MUST be able to switch backends without changing application code.

**Rationale**: Different models and hardware configurations perform optimally with different backends. Providing choice maximizes performance across diverse deployment scenarios.

**Requirements**:
- Support GGUF models via llama.cpp with Vulkan/Metal backends
- Support ONNX models via ONNX Runtime GenAI for CPU/GPU/NPU
- Support FLM models for AMD Ryzen AI NPU acceleration
- Enable runtime backend selection via CLI flags

### III. Hardware-Optimized Performance

All supported configurations MUST be optimized for AMD hardware platforms, with explicit support for Ryzen AI NPUs (300 series), RDNA GPUs (gfx110X, gfx120X, gfx1151), and CPU execution.

**Rationale**: Lemonade SDK is sponsored by AMD to showcase optimal local LLM performance on AMD hardware. Performance optimization is a core differentiator.

**Requirements**:
- Test and validate on Ryzen AI Max+ 395 with **96 GB VRAM** (system RAM: 128 GB)
- Support Vulkan for cross-platform GPU execution
- Provide clear performance expectations per hardware configuration
- Document supported AMD platforms in README with architecture details

### IV. Open Source Collaboration

Development MUST be conducted in public with transparent roadmaps, comprehensive contribution guidelines, and responsive maintainer engagement. The project stands on shoulders of giants (llama.cpp, ONNX Runtime GenAI, Hugging Face Hub) and MUST contribute back.

**Rationale**: Open source collaboration drives innovation, quality, and adoption. Community contributions expand capabilities faster than any single organization.

**Requirements**:
- Maintain Apache 2.0 licensing with proper attribution (see NOTICE.md)
- Publish roadmap updates regularly
- Label good first issues for new contributors
- Respond to issues and PRs within reasonable timeframes
- Document all dependencies and their licenses
- Support contributor workflow via Discord, GitHub Issues, and email

### V. Developer Experience First

APIs, CLIs, and integrations MUST prioritize simplicity and clarity. Installation MUST work in under 10 minutes. Documentation MUST be practical and example-driven.

**Rationale**: Complex tools are abandoned. Lemonade succeeds when developers can integrate LLMs effortlessly and focus on building applications, not fighting infrastructure.

**Requirements**:
- Provide one-line installation commands per platform (Windows MSI, Ubuntu packages, source)
- Include working examples for all major use cases (examples/ directory)
- Offer both high-level Python API and low-level CLI tools
- Support common workflows: model download, chat, server launch, integration testing
- Maintain clear documentation at lemonade-server.ai
- Test installation procedures on clean systems regularly

### VI. Production-Ready Quality

Code MUST be tested, benchmarked, and validated before release. Breaking changes MUST follow semantic versioning. Error messages MUST be actionable.

**Rationale**: Developers deploy Lemonade in production applications. Instability, silent failures, or unclear errors erode trust and adoption.

**Requirements**:
- Maintain comprehensive test suite (test/ directory with unit, integration, contract tests)
- Run automated CI/CD workflows for all PRs (GitHub Actions)
- Use semantic versioning (MAJOR.MINOR.PATCH)
- Provide detailed error messages with troubleshooting guidance
- Test on supported platforms before release (Windows 11, Ubuntu 24.04/25.04)
- Include model validation notebooks (examples/notebooks/)

### VII. Cross-Platform Support

Lemonade MUST run on Windows (11+) and Linux (Ubuntu 24.04/25.04) with consistent functionality. Platform-specific optimizations are allowed; platform-exclusive features require strong justification.

**Rationale**: Developers use diverse environments. Cross-platform support maximizes addressable user base and prevents ecosystem fragmentation.

**Requirements**:
- Test all releases on Windows and Linux before publishing
- Provide native installers per platform (MSI for Windows, apt/source for Linux)
- Document platform-specific features clearly (e.g., NPU support Windows-only currently)
- Ensure CLI commands work identically across platforms
- Use cross-platform dependencies where possible

### VIII. Observability & Debugging

All operations MUST produce clear, structured logs. Performance profiling tools MUST be included. Errors MUST be traceable to root causes.

**Rationale**: When things fail (and they will), developers need visibility into what happened and why. Black-box failures lead to frustration and abandonment.

**Requirements**:
- Implement structured logging for server operations
- Provide CLI tools for benchmarking (lemonade CLI: accuracy, perplexity, power profiling)
- Include performance profiling capabilities (src/lemonade/profilers/)
- Log all model loading, inference requests, and errors with context
- Support debug modes with increased verbosity
- Document troubleshooting procedures in FAQ

## Technology Stack Requirements

**Languages**: Python 3.10-3.13, C++ (server and tray components)

**Core Dependencies**:
- FastAPI + Uvicorn (server framework)
- ONNX Runtime GenAI (ONNX backend)
- llama.cpp (GGUF backend)
- Hugging Face Hub (model downloads)
- OpenAI Python SDK (API compatibility)
- Transformers (model utilities)

**Build Tools**: CMake (C++ components), setuptools (Python packaging), webpack (Electron app)

**Development Tools**: pytest (testing), black (code formatting), GitHub Actions (CI/CD)

**Platforms**: Windows 11, Ubuntu 24.04/25.04, dev container (Debian GNU/Linux 12)

## External Documentation & Resources

**Lemonade SDK**:
- Official Documentation: https://lemonade-server.ai
- Public Repository: https://github.com/lemonade-sdk/lemonade
- Discord Community: https://discord.gg/5xXzkMu8Zk
- Support Email: lemonade@amd.com

**AMD Hardware Documentation**:
- Ryzen AI (NPU): https://ryzenai.docs.amd.com
- AMD Graphics Drivers: https://www.amd.com/en/support
- Radeon RX 9100 Support: https://www.amd.com/en/support/graphics/radeon-9000-series/radeon-rx-9000-series/amd-radeon-rx-9100

**Third-Party Dependencies**:
- llama.cpp: https://github.com/ggerganov/llama.cpp
- ONNX Runtime GenAI: https://github.com/microsoft/onnxruntime-genai
- Hugging Face Hub: https://huggingface.co/docs

## Test Environment Configuration

**Lemonade Server Installation**:
- **Executable Path**: `C:\Users\tomwo\AppData\Local\lemonade_server\bin\`
- **Router Binary**: `lemonade-router.exe`
- **Server Binary**: `lemonade-server.exe`

**Model Storage Locations**:
- **Huggingface Models**: `C:\Users\tomwo\.cache\huggingface\hub`
- **FLM Models**: `C:\Users\tomwo\Documents\flm\models`

**Standard Launch Commands**:
```powershell
# Router (OpenAI-compatible API endpoint)
"C:\Users\tomwo\AppData\Local\lemonade_server\bin\lemonade-router.exe" --port 8000 --host 0.0.0.0 --ctx-size 4096 --llamacpp vulkan --log-level debug --max-loaded-models 1 1 1 1

# Server (Background service)
"C:\Users\tomwo\AppData\Local\lemonade_server\bin\lemonade-server.exe" serve
```

**Test Hardware**: AMD AI Max+ 395 with **96GB VRAM** (gfx1151), ROCm-enabled Windows 11 system — system RAM: 128 GB

**Verified Software Stack**:
- **Python**: 3.13.11 (3.10-3.13 supported)
- **GPU Architecture**: gfx1151 (AMD Radeon 8060S / AI Max+ 395)
- **Total VRAM**: ~110 GB available for inference

**Performance Optimizations**:
- Follow platform-specific best practices for GPU/NPU drivers and backend libraries (Vulkan/ONNX/FLM) as documented in the README and platform pages.

**Additional Test Hardware**:
- AMD Radeon 8060S (gfx1151): 110457 MB VRAM - Verified compatible with same architecture as Max+ 395
- System RAM: 32 GB minimum recommended
- Pinned Memory: ~14.5 GB enabled for faster transfers

## Development Workflow

**Issue-First Development**: All contributions start with an Issue describing the proposal, use case, and maintainer approval. Exceptions: typo fixes, documentation clarifications.

**UI Development Policy**: UI and frontend development handled exclusively by core maintainers due to complexity of AI-assisted UI review. Community can propose UI/UX ideas via Issues or Discord.

**Script Organization Policy**: All executable scripts MUST be placed inside a subdirectory of the top-level `scripts/` folder (for example: `scripts/benchmarks/`, `scripts/wandb/`, `scripts/playground/`). Avoid leaving scripts directly under `scripts/`. Prefer one folder per spec/feature (exceptions allowed with justification documented in the implementation plan). Maintainers and reviewers will enforce this rule during PR review; follow-up migration steps should be included when a policy change affects existing files.

**Testing Requirements**: New features MUST include tests. Tests are OPTIONAL for specs but REQUIRED before merging implementation. Contract tests for API changes, integration tests for multi-component features, unit tests for isolated logic.

- CI Enforcement: Pull requests that add ROCm-specific tests, specs, or installation guides are blocked by a dedicated CI check (see `.github/workflows/block-rocm.yml`) unless the change is approved by maintainers via an Issue and review. This prevents accidental reintroductions of platform-specific ROCm content into the main branch.

**Upstream File Protection**: Files from the original public repository MUST NOT be overwritten in private fork operations. This includes but is not limited to:
- `docs/contribute.md` (upstream contribution guidelines)
- Core documentation from public repository
- Upstream configuration files

Private fork customizations should be maintained in separate files or clearly marked sections to avoid conflicts during upstream synchronization.

### Git Workflow

**Public Repository**: `https://github.com/lemonade-sdk/lemonade`

**Feature Branches**: `feature/description` or `###-feature-name`

#### Private Fork Mirror Workflow

Policy note: use a mirror workflow for private forks; the full step-by-step procedure is maintained in `docs/git-workflow.md` (see repository `docs/` directory). The Constitution retains policy-level guidance; operational details live in the docs file to keep the Constitution concise and maintainable.

**Code Review**: Maintainers (@danielholanda, @jeremyfowers, @ramkrishna, @vgodsoe) review all PRs. Reviews verify constitution compliance, test coverage, documentation updates, and platform compatibility.

**Release Process**: Semantic versioning. MAJOR = breaking API changes, MINOR = new features, PATCH = bug fixes. Tag releases with version number. Update version.py, CHANGELOG, documentation before release.

## Governance

This constitution supersedes all other development practices and guidelines. All PRs and code reviews MUST verify compliance with stated principles.

**Amendment Procedure**:
1. Propose amendment via Issue with rationale and impact analysis
2. Obtain maintainer approval
3. Update constitution.md with version bump following semantic versioning:
   - MAJOR: Backward incompatible principle removals or redefinitions
   - MINOR: New principle or materially expanded guidance
   - PATCH: Clarifications, wording fixes, non-semantic refinements
4. Update dependent templates and documentation
5. Document changes in Sync Impact Report (HTML comment at file top)

**Version Bumping**:
- Version increments MUST be justified in Sync Impact Report
- All placeholder tokens MUST be resolved or explicitly marked TODO with explanation
- Dates MUST follow ISO format (YYYY-MM-DD)

**Complexity Justification**: Features violating constitution principles (e.g., adding complexity, non-portable code) MUST document justification in implementation plan and obtain maintainer approval.

**Compliance Review**: Maintainers review constitution compliance quarterly. Violations trigger corrective action plans. Repeated violations may result in principle amendments or enforcement policy updates.

**Runtime Guidance**: For agent-specific development guidance, refer to `.github/prompts/` directory. Constitution provides project-wide principles; runtime guidance provides tactical execution details.

**Version**: 1.0.1 | **Ratified**: 2025-12-23 | **Last Amended**: 2025-12-24
