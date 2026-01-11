# Data Model: Multi-LLM Concurrent Execution

**Feature**: 005-multi-llm-execution  
**Status**: Feature Already Implemented  
**Date**: 2026-01-09

## Overview

This document describes the data entities and relationships in the multi-LLM concurrent execution feature. The implementation uses C++ classes with clear separation of concerns.

## Entities

### 1. WrappedServer

Represents a single loaded model instance with its backend server.

**Purpose**: Encapsulates a model's runtime state and provides uniform interface to different backend implementations (llama.cpp, ONNX Runtime, FLM).

**Attributes**:
| Field | Type | Description | Validation Rules |
|-------|------|-------------|------------------|
| model_name | string | User-facing model identifier | Non-empty, must match registry |
| checkpoint | string | HuggingFace checkpoint path | Format: "org/model:variant" or file path |
| type | ModelType enum | LLM, EMBEDDING, RERANKING, or AUDIO | Set based on model labels |
| device | Device enum (bitmask) | CPU, GPU, NPU (can be multiple) | Based on recipe |
| last_access_time | steady_clock::time_point | Timestamp of last inference or load | Updated on access |
| is_busy | atomic<bool> | True when processing inference | Protected from eviction when true |
| backend_port | int | Port of wrapped backend server | Auto-assigned from pool |

**Lifecycle**:
1. Created → `load_model()` called
2. Loading → Backend server starting (30-60s)
3. Loaded → Ready for inference
4. Processing → `is_busy = true` during inference
5. Idle → `is_busy = false` after inference complete
6. Evicted → Destructor called, backend stopped

**Implementation**: `src/cpp/include/lemon/wrapped_server.h`

---

### 2. Router

Central orchestrator managing multiple WrappedServer instances and enforcing capacity limits.

**Purpose**: Coordinates model loading/unloading, routes inference requests, enforces LRU eviction policy.

**Attributes**:
| Field | Type | Description | Validation Rules |
|-------|------|-------------|------------------|
| loaded_servers_ | vector<unique_ptr<WrappedServer>> | All currently loaded models | Size ≤ sum of capacity limits |
| max_llm_models_ | int | Maximum LLM slots | ≥ 1, set via CLI |
| max_embedding_models_ | int | Maximum embedding slots | ≥ 1, set via CLI |
| max_reranking_models_ | int | Maximum reranking slots | ≥ 1, set via CLI |
| max_audio_models_ | int | Maximum audio slots | ≥ 1, set via CLI |
| load_mutex_ | mutex | Protects load operations | Ensures serialization |
| is_loading_ | bool | True during active load | Only one load at a time |
| load_cv_ | condition_variable | Signals load completion | Wakes queued loads |
| ctx_size_ | int | Default context size | Overridable per model |
| llamacpp_backend_ | string | Default llama.cpp backend | "vulkan", "rocm", "cpu" |
| llamacpp_args_ | string | Default llama-server arguments | Overridable per model |

**Operations**:
- `load_model(name, info)` → Loads new model, triggers eviction if needed
- `unload_model(name)` → Unloads specific model or all models
- `find_server_by_model_name(name)` → Lookup for request routing
- `find_lru_server_by_type(type)` → Identifies eviction candidate
- `evict_server(server)` → Removes and destroys WrappedServer
- `execute_inference(request, func)` → Routes request with busy protection

**Implementation**: `src/cpp/include/lemon/router.h`, `src/cpp/server/router.cpp`

---

### 3. ModelInfo

Static metadata about a model from the registry.

**Purpose**: Describes model properties before loading (used for discovery and validation).

**Attributes**:
| Field | Type | Description | Source |
|-------|------|-------------|--------|
| checkpoint | string | HuggingFace checkpoint or file path | server_models.json or user_models.json |
| recipe | string | Inference backend to use | "llamacpp", "oga-cpu", "oga-hybrid", "oga-npu", "flm" |
| labels | vector<string> | Model capabilities | "reasoning", "vision", "embedding", "reranking", "audio" |
| mmproj | string (optional) | Multimodal projector file for vision models | Specified during pull |
| ctx_size | int (optional) | Per-model context size override | From previous saves or load request |

**Derived Properties**:
- **type**: Determined from labels (embedding → EMBEDDING, reranking → RERANKING, audio → AUDIO, else → LLM)
- **device**: Determined from recipe (flm/oga-npu → NPU, oga-hybrid → GPU+NPU, llamacpp → GPU, oga-cpu → CPU)

**Implementation**: `src/cpp/include/lemon/model_manager.h`

---

### 4. InferenceRequest

Represents an incoming API request for model inference.

**Purpose**: Encapsulates user request parameters for routing and execution.

**Attributes**:
| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| model | string | Target model name | Must match loaded model |
| messages | vector<Message> | Chat history | Non-empty for chat endpoints |
| max_tokens | int | Max generation tokens | > 0 |
| temperature | float | Sampling temperature | 0.0 - 2.0 |
| stream | bool | Enable streaming response | true or false |
| [other params] | various | Standard OpenAI parameters | Per OpenAI spec |

**Flow**:
1. Request arrives at `/api/v1/chat/completions` or `/api/v1/completions`
2. Router extracts `model` field
3. `find_server_by_model_name()` locates WrappedServer
4. If not found, auto-load model (if allowed)
5. `execute_inference()` marks server busy, forwards request, waits for response
6. Server marked idle after response complete

**Implementation**: Handled in `src/cpp/server/server.cpp` endpoint handlers

---

## Relationships

```
                    ┌─────────────────┐
                    │     Router      │
                    │  (Orchestrator) │
                    └────────┬────────┘
                             │
                             │ manages
                             ▼
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
    ┌──────────────────┐         ┌──────────────────┐
    │  WrappedServer   │         │  WrappedServer   │
    │   (Model 1)      │         │   (Model 2)      │
    └──────────────────┘         └──────────────────┘
              │                             │
              │ references                  │ references
              ▼                             ▼
    ┌──────────────────┐         ┌──────────────────┐
    │   ModelInfo      │         │   ModelInfo      │
    │  (Metadata)      │         │  (Metadata)      │
    └──────────────────┘         └──────────────────┘
```

**Router → WrappedServer**: 1-to-many  
Router owns multiple WrappedServer instances via `unique_ptr`. When eviction occurs, Router removes from vector and destructor auto-cleans backend.

**WrappedServer → ModelInfo**: many-to-one (reference)  
Multiple WrappedServers can reference the same ModelInfo (if same model loaded multiple times with different settings - though rare in practice).

**InferenceRequest → WrappedServer**: many-to-one (routing)  
Many concurrent requests can target the same WrappedServer. Router queues them and WrappedServer's backend processes sequentially.

---

## State Transitions

### WrappedServer State Machine

```
     [Not Exist]
          │
          │ load_model()
          ▼
     [Creating]
          │
          │ backend starts
          ▼
      [Loaded]
          │
          ├─────┐ inference request
          │     ▼
          │  [Busy]
          │     │
          │     │ request completes
          │◄────┘
          │
          │ evict_server()
          ▼
     [Destroyed]
```

### Router Load State Machine

```
       [Idle]
          │
          │ load_model() called
          ▼
    [is_loading=true]
          │
          │ eviction if needed
          │ backend starts (30-60s)
          ▼
    [Model Loaded]
          │
          │ is_loading=false, load_cv.notify_all()
          ▼
       [Idle]
```

---

## Capacity Management

**Capacity Formula per Type**:
```
current_count = count_servers_by_type(type)
available_slots = max_models_by_type - current_count
```

**Eviction Decision**:
```
if (current_count >= max_models_by_type):
    lru = find_lru_server_by_type(type)  # Skips busy servers
    if lru:
        evict_server(lru)
        # Slot now available
```

**NPU Exclusivity Override**:
```
if (new_model.device & Device::NPU):
    npu_server = find_npu_server()  # Any type
    if npu_server:
        evict_server(npu_server)  # Evict regardless of type limits
```

---

## Data Persistence

**None**: All model state is in-memory. When server restarts, all models are unloaded. This is intentional - model selection is dynamic and user-driven.

**Exception**: Per-model settings (ctx_size, llamacpp_backend, llamacpp_args) CAN be saved to `user_models.json` via `lemonade-server run MODEL --save-options`. These become defaults for future loads but don't auto-load models.

---

## Concurrency Guarantees

1. **Load Serialization**: Only one `load_model()` executes at a time (protected by `load_mutex_` + `is_loading_` flag)
2. **Busy Protection**: WrappedServers with `is_busy=true` skipped during LRU eviction
3. **Atomic Busy Flag**: `std::atomic<bool>` ensures thread-safe busy state checks
4. **Lock Scope**: `load_mutex_` released before slow backend startup (prevents blocking inference)

---

## Implementation Notes

- **C++ Ownership**: `std::unique_ptr<WrappedServer>` ensures automatic cleanup, no manual memory management
- **Move Semantics**: WrappedServers moved into `loaded_servers_` vector (no copying)
- **RAII**: Mutex locks use `std::unique_lock` for exception safety
- **Type Safety**: Enums (`ModelType`, `Device`) prevent invalid states
- **Thread Safety**: All mutable Router state protected by `load_mutex_`

---

## References

- **Implementation**: `src/cpp/include/lemon/router.h`, `src/cpp/server/router.cpp`
- **Spec**: `src/cpp/Multi-Model-Spec.md`
- **Tests**: `test/server_multimodel.py`
