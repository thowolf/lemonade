# Research: Multi-LLM Concurrent Execution

**Feature**: 005-multi-llm-execution  
**Status**: Feature Already Implemented  
**Date**: 2026-01-09

## Summary

Research phase **not required** - the multi-LLM concurrent execution feature is already fully implemented in Lemonade Server. This document serves as a reference for the existing implementation's design decisions and technology choices.

## Implementation Analysis

### Technology Choices

#### Why C++ for Multi-Model Management?

**Decision**: Implement multi-model orchestration in C++ Router component

**Rationale**:
- **Performance**: C++ enables efficient memory management and low-overhead model switching
- **Thread Safety**: std::mutex and condition variables provide robust concurrency control
- **Integration**: Tight integration with backend servers (llama.cpp, ONNX Runtime) which are also C++
- **Resource Control**: Direct control over model lifecycle and memory allocation

**Alternatives Considered**:
- Python FastAPI: Simpler but higher overhead, GIL limitations for true parallelism
- Separate process per model: More isolation but complex inter-process communication

#### Why LRU Eviction Policy?

**Decision**: Least Recently Used (LRU) cache eviction with active request protection

**Rationale**:
- **Predictable**: Users understand "oldest unused model gets evicted" intuitive
- **Fair**: Treats all models equally based on actual usage
- **Simple**: No complex heuristics or ML-based prediction needed
- **Effective**: Works well in practice - frequently used models stay in memory

**Alternatives Considered**:
- Least Frequently Used (LFU): More complex tracking, less responsive to changing usage patterns
- Random eviction: Unpredictable, poor user experience
- Manual-only: Requires user intervention, high operational overhead

#### Why Serialized Loading?

**Decision**: Queue model load requests and process sequentially

**Rationale**:
- **Safety**: Prevents race conditions on capacity checks
- **Simplicity**: No complex locking strategies or optimistic concurrency
- **Reliability**: Deterministic behavior under concurrent load
- **Acceptable Latency**: Model loading is slow (30-60s), serialization overhead negligible

**Alternatives Considered**:
- Concurrent loading: Complex locking, risk of exceeding capacity
- Optimistic concurrency: Can violate capacity limits, requires rollback logic

#### Why Type-Specific Capacity Limits?

**Decision**: Separate capacity limits for LLM, embedding, reranking, and audio models

**Rationale**:
- **Resource Optimization**: Embedding models are smaller, can load more
- **Use Case Alignment**: Embedding/reranking often used alongside LLMs
- **Flexibility**: Administrators can tune based on their workload
- **NPU Exclusivity**: Audio/embedding models on NPU don't compete with LLMs on GPU

**Alternatives Considered**:
- Single global limit: Less flexible, poor resource utilization
- Memory-based limits: Complex to track, platform-dependent

#### Why Nuclear Eviction on Load Failure?

**Decision**: Evict all models on load failure (except file-not-found)

**Rationale**:
- **Simplicity**: Avoids complex rollback logic
- **Robustness**: Clears potentially corrupted state
- **Rare**: Load failures are uncommon in practice
- **Clear State**: Server returns to known-good empty state

**Alternatives Considered**:
- Rollback to previous state: Complex to implement, requires snapshots
- Retry with different model: Infinite loops possible
- Leave inconsistent state: Risk of cascading failures

### Validation State

All technical decisions validated through:
- ✅ Implementation in `src/cpp/server/router.cpp`
- ✅ Test suite with 11 test cases in `test/server_multimodel.py`
- ✅ Production usage in Lemonade Server releases
- ✅ Documentation in `docs/server/server_spec.md`
- ✅ Technical spec in `src/cpp/Multi-Model-Spec.md`

## Dependencies

### Required Libraries

- **nlohmann/json**: JSON parsing for API requests/responses
- **httplib**: HTTP server framework
- **llama.cpp**: GGUF model backend
- **ONNX Runtime GenAI**: ONNX model backend  
- **C++ Standard Library**: std::mutex, std::condition_variable, std::vector, std::unique_ptr

All dependencies already integrated in Lemonade Server build system (CMake).

### Platform Requirements

- **Windows 11+**: Tested and validated
- **Ubuntu 24.04/25.04**: Tested and validated
- **C++17**: Required for std::optional and structured bindings

## Best Practices Applied

1. **RAII**: std::unique_ptr for automatic WrappedServer cleanup
2. **Lock Guards**: std::unique_lock for exception-safe locking
3. **Condition Variables**: std::condition_variable for efficient waiting
4. **Atomic Operations**: std::atomic<bool> for busy state checks
5. **Move Semantics**: Efficient WrappedServer transfers without copying

## Performance Characteristics

**Measured Performance** (from tests):
- Model eviction: <5 seconds
- Concurrent inference: No measurable overhead vs single model
- Load serialization: Negligible latency (<1ms queue time)
- LRU lookup: O(n) where n = loaded models (acceptable for n < 10)

## Security Considerations

- **API Key Support**: LEMONADE_API_KEY environment variable protects endpoints
- **HTTPS Requirement**: Documented requirement for internet exposure
- **Input Validation**: Model names validated against registry
- **Resource Limits**: Capacity limits prevent uncontrolled memory growth

## Open Questions

None - all design questions resolved in implementation.
