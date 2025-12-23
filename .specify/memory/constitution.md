<!--
  SYNC IMPACT REPORT
  ==================
  Version: 0.0.0 → 1.0.0
  Date: 2025-12-23
  
  Changes:
  - Initial constitution ratification
  - Established 8 core principles for Lemonade SDK development
  - Defined open source collaboration and AMD hardware optimization principles
  
  Principles Defined:
  1. OpenAI API Compatibility (NEW)
  2. Multi-Backend Architecture (NEW)
  3. Hardware-Optimized Performance (NEW)
  4. Open Source Collaboration (NEW)
  5. Developer Experience First (NEW)
  6. Production-Ready Quality (NEW)
  7. Cross-Platform Support (NEW)
  8. Observability & Debugging (NEW)
  
  Templates Status:
  ✅ plan-template.md - Reviewed, aligns with constitution
  ✅ spec-template.md - Reviewed, aligns with constitution
  ✅ tasks-template.md - Reviewed, aligns with constitution
  
  Follow-up Actions:
  - None required - initial constitution establishment
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

### II. Multi-Backend Architecture

The system MUST support multiple inference backends (ONNX Runtime GenAI, llama.cpp, FLM) with runtime selection capability. Users MUST be able to switch backends without changing application code.

**Rationale**: Different models and hardware configurations perform optimally with different backends. Providing choice maximizes performance across diverse deployment scenarios.

**Requirements**:
- Support GGUF models via llama.cpp with Vulkan/ROCm/Metal backends
- Support ONNX models via ONNX Runtime GenAI for CPU/GPU/NPU
- Support FLM models for AMD Ryzen AI NPU acceleration
- Enable runtime backend selection via CLI flags

### III. Hardware-Optimized Performance

All supported configurations MUST be optimized for AMD hardware platforms, with explicit support for Ryzen AI NPUs (300 series), RDNA GPUs (gfx110X, gfx120X, gfx1151), and CPU execution.

**Rationale**: Lemonade SDK is sponsored by AMD to showcase optimal local LLM performance on AMD hardware. Performance optimization is a core differentiator.

**Requirements**:
- Test and validate on Ryzen AI Max+ 395 with 128 GB VRAM
- Support ROCm for AMD GPU acceleration (Windows and Linux)
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

## Development Workflow

**Issue-First Development**: All contributions start with an Issue describing the proposal, use case, and maintainer approval. Exceptions: typo fixes, documentation clarifications.

**UI Development Policy**: UI and frontend development handled exclusively by core maintainers due to complexity of AI-assisted UI review. Community can propose UI/UX ideas via Issues or Discord.

**Testing Requirements**: New features MUST include tests. Tests are OPTIONAL for specs but REQUIRED before merging implementation. Contract tests for API changes, integration tests for multi-component features, unit tests for isolated logic.

**Git Workflow**:
- Public repository: `https://github.com/lemonade-sdk/lemonade`
- Private forks: Use mirror workflow (upstream = public, origin = private)
- Feature branches: `feature/description` or `###-feature-name`
- Update from upstream regularly: `git fetch upstream && git rebase upstream/main`

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

**Version**: 1.0.0 | **Ratified**: 2025-12-23 | **Last Amended**: 2025-12-23
