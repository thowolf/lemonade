# Implementation Tasks: On-Premise AI Infrastructure with Nextcloud, LiteLLM, and Lemonade Server

**Feature**: `006-nextcloud-litellm-infra`
**Date Generated**: 2026-01-20
**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)
**Total Tasks**: 16 tasks across 4 phases

---

## Task Summary

| Phase | Title | Tasks | Duration | MVP |
|-------|-------|-------|----------|-----|
| Phase 1 | Setup & Infrastructure | T001-T003 | 30 min | ✓ |
| Phase 2 | Foundational Services | T004-T006 | 45 min | ✓ |
| Phase 3 | User Story 1 - Text Generation | T007-T010 | 60 min | ✓ |
| Phase 4 | User Story 2 - Secure API Gateway | T011-T013 | 45 min | ✓ |
| Phase 5 | User Story 3-5 - Extended Features | T014-T016 | 90 min |  |

**MVP Scope (Recommended First Increment)**: Phases 1-4 (T001-T013) - Delivers complete text generation + API security

---

## Dependencies & Execution Order

```
Phase 1 (Setup)
  ├── T001: Create feature directory
  ├── T002: Prepare configuration templates
  └── T003: Validate network connectivity
         ↓
Phase 2 (Foundational)
  ├── T004: Deploy Lemonade Server
  ├── T005: [P] Deploy LiteLLM Proxy
  └── T006: [P] Verify API endpoints
         ↓
Phase 3 (User Story 1)
  ├── T007: Configure LiteLLM routing (text)
  ├── T008: [P] Test Lemonade endpoints
  ├── T009: [P] Validate model loading
  └── T010: Test text generation flow end-to-end
         ↓
Phase 4 (User Story 2)
  ├── T011: Deploy Apache reverse proxy (DMZ)
  ├── T012: [P] Configure TLS certificates
  ├── T013: Test secure routing (public → internal)
         ↓
Phase 5 (Extended Features)
  ├── T014: [P] Deploy OpenedAI-Speech (TTS)
  ├── T015: [P] Deploy ComfyUI (image generation)
  └── T016: [P] Configure extended model aliases
```

**Parallelizable Tasks**: T005-T006 can run parallel, T008-T009 can run parallel, T012 can run parallel to T011, T014-T016 can all run parallel after T013.

---

## PHASE 1: Setup & Infrastructure Validation

**Goal**: Establish feature directory, prepare configuration files, and verify network connectivity between DMZ and internal VLAN.

**Test Criteria**: 
- All configuration files exist with correct permissions
- Network connectivity verified (DMZ → internal VLAN on port 4014)
- No DNS or firewall issues blocking planned communication paths

---

### T001 - Create project feature directory and initialize structure

- [x] T001 Create feature directory `specs/006-nextcloud-litellm-infra` with subdirectories for configs and deployment scripts
  - **File**: `specs/006-nextcloud-litellm-infra/`
  - **Action**: Create directory structure including `configs/`, `docs/`, `checklists/`
  - **Acceptance**: `ls -la specs/006-nextcloud-litellm-infra/` shows all subdirectories with correct permissions

- [x] T001a Add `spec.md` for feature specification
  - **File**: `specs/006-nextcloud-litellm-infra/spec.md`
  - **Acceptance**: File present; contains goals, acceptance criteria, security notes

- [x] T001b Add `plan.md` with milestones and runbook
  - **File**: `specs/006-nextcloud-litellm-infra/plan.md`
  - **Acceptance**: File present; contains deployment runbook, verification & rollback steps

---

### T002 - Prepare and validate all configuration templates

- [x] T002 [P] Review and validate YAML syntax for LiteLLM configuration file
  - **File**: [configs/litellm-config.yaml](configs/litellm-config.yaml)
  - **Action**: Validate YAML schema, check model routes, verify timeout values
  - **Acceptance**: `python -m yaml < configs/litellm-config.yaml` produces no errors

- [x] T002b [P] Review and validate Apache configuration syntax
  - **File**: [configs/apache-api-proxy.conf](configs/apache-api-proxy.conf)
  - **Action**: Check VirtualHost syntax, verify ProxyPass paths, validate security headers
  - **Acceptance**: Apache config file exists with proper VirtualHost structure

- [x] T002c [P] Review and validate Bash setup script
  - **File**: [configs/nextcloud-setup.sh](configs/nextcloud-setup.sh)
  - **Action**: Check bash syntax, validate occ command paths, verify error handling
  - **Acceptance**: `bash -n configs/nextcloud-setup.sh` produces no syntax errors

---

### T003 - Verify network connectivity and firewall rules

- [x] T003 Test connectivity from DMZ server (192.168.178.41) to internal LiteLLM port (192.168.86.196:4014)
  - **Command**: `nc -zv 192.168.86.196 4014` (from DMZ server)
  - **Acceptance**: Connection succeeds, no timeout
  - **File**: Network validation via manual test or health check script

---

## PHASE 2: Foundational Services - LiteLLM Proxy & Lemonade Server

**Goal**: Deploy and verify Lemonade Server + LiteLLM Proxy before routing user requests through them.

**Test Criteria**:
- Lemonade Server starts and loads configured models
- LiteLLM Proxy starts and reaches health endpoint
- Direct calls to Lemonade `/v1/chat/completions` work
- Direct calls to LiteLLM `/v1/health` endpoint work

---

### T004 - Deploy and start Lemonade Server with configured models

- [x] T004 Start Lemonade Server using existing tooling on 192.168.86.196:8000
  - **File**: `tools/benchmarks/start_quality_multiport.ps1` (existing script)
  - **Action**: Executed PowerShell script to start Lemonade Server and load models
    - Qwen3-Next-80B-A3B-Instruct-GGUF (text generation)
    - Qwen3-Coder-30B-A3B-Instruct-GGUF (code generation)
    - Gemma-3-4b-it-GGUF (fast text)
    - Whisper-Large-v3-Turbo (audio transcription)
  - **Command**: `.\\tools\\benchmarks\\start_quality_multiport.ps1 -All` (executed)
  - **Acceptance / Evidence**: `curl http://localhost:8000/api/v1/models` shows the server online and `start_quality_multiport.ps1 -Load` reported `Summary: 4 loaded, 0 failed`

---

### T005 - Deploy LiteLLM Proxy on internal VLAN

- [~] T005 [P] Configure and start LiteLLM Proxy service on 192.168.86.196:4014 (verified locally, production service pending)
  - **File**: [configs/litellm-config.yaml](configs/litellm-config.yaml)
  - **Action**: 
    1. Copy `litellm-config.yaml` to deployment location
    2. Start LiteLLM: `litellm --config configs/litellm-config.yaml --port 4014`
    3. Verify process is running and listening on port 4014 and create a managed service (systemd/Windows service)
  - **Current status**: Environment issues (missing optional Python deps, Windows console encoding) were resolved for local verification. A **temporary OpenAPI-compatible proxy** (`specs/006-nextcloud-litellm-infra/simple_proxy.py`) was used to unblock integration tests. The real `litellm` binary can be started locally after installing the extras and setting `PYTHONIOENCODING=utf-8`, but **service installation and hardening (key rotation, log rotation, monitoring)** remain pending.
  - **Acceptance (two-stage)**:
    - **Verification (DEV)**: `curl -i http://localhost:4014/v1/health` → HTTP 200 (temporary proxy OR live litellm)
    - **Production acceptance**: `systemctl`/service shows running, listens on 0.0.0.0:4014, `ss -ltnp | grep 4014` shows process, service unit sets `PYTHONIOENCODING=utf-8`, rotated `master_key`, and CI/packaging installs the service correctly
  - **Next steps**: install service unit (systemd/Windows service), rotate `sk-lemonade-master-key-CHANGE-ME`, add log rotation and monitoring (Prometheus / filebeat)


---

### T006 - Verify API endpoints are reachable

- [x] T006 [P] Test direct connectivity to Lemonade Server and LiteLLM Proxy
  - **Test 1 - Lemonade Server**: `curl -X POST http://192.168.86.196:8000/api/v1/chat/completions -H "Content-Type: application/json" -d '{"model":"Qwen3-Next-80B-A3B-Instruct-GGUF","messages":[{"role":"user","content":"Hello"}]}'` — **OK (verified)**
  - **Test 2 - LiteLLM Proxy**: `curl http://192.168.86.196:4014/v1/health` — **OK (via `simple_proxy.py` / local litellm when started)**
  - **Acceptance**: Lemonade Server is reachable and responding; LiteLLM proxy health verified for integration tests (temporary proxy). Full production service verification remains as part of T005 (service install + key rotation).

---

## PHASE 3: User Story 1 - Text Generation via Nextcloud Assistant

**Goal**: Enable text generation requests from Nextcloud to flow through LiteLLM to Lemonade Server with model alias routing.

**Independent Test**: Send a chat completion request through Nextcloud AI Assistant and verify a coherent response is returned from the local LLM.

**Test Criteria**:
- LiteLLM correctly routes requests for `llm-text-gen` to Qwen3-Next-80B
- LiteLLM correctly routes requests for `llm-code-gen` to Qwen3-Coder-30B
- LiteLLM correctly routes requests for `llm-text-fast` to Gemma-3-4b
- Request timeout is 120 seconds
- Failed requests return HTTP 503 with no retries

---

### T007 - Configure LiteLLM model routing for text generation aliases

- [ ] T007 [US1] Create LiteLLM configuration with model alias routes for text generation
  - **File**: [configs/litellm-config.yaml](configs/litellm-config.yaml)
  - **Action**: 
    1. Configure `llm-text-gen` → Qwen3-Next-80B-A3B-Instruct-GGUF (32K context)
    2. Configure `llm-code-gen` → Qwen3-Coder-30B-A3B-Instruct-GGUF (64K context)
    3. Configure `llm-text-fast` → Gemma-3-4b-it-GGUF (16K context)
    4. Set `request_timeout: 120`
    5. Set `max_parallel_requests: 100` (no queuing, let Lemonade handle concurrency)
  - **Acceptance**: `litellm --config configs/litellm-config.yaml --port 4014` starts without errors

---

### T008 - Test Lemonade Server chat/completions endpoint for all text models

- [x] T008 [P] [US1] Verify Lemonade Server responds to /v1/chat/completions for text models
  - **Evidence**: `tools/benchmarks/start_quality_multiport.ps1 -Load` reported `Summary: 4 loaded, 0 failed`; direct `curl` requests to `http://192.168.86.196:8000/v1/chat/completions` for **Qwen3-Next-80B**, **Qwen3-Coder-30B** and **Gemma-3-4b** returned HTTP 200 with valid `choices[0].message.content` in manual smoke tests.
  - **Acceptance**: All three requests return HTTP 200 with valid JSON responses containing `choices[0].message.content` (verified)

---

### T009 - Validate model loading and concurrency settings

- [x] T009 [P] [US1] Verify Lemonade Server is running with correct concurrency settings
  - **Evidence**: `start_quality_multiport.ps1` completed with `Summary: 4 loaded, 0 failed`; process started with configured flags in development runs. Server logs show successful model loading for the four configured models.
  - **Action (recommended verification commands)**:
    - `ps aux | grep lemonade`
    - `grep -E "max-loaded-models|flash-attn" /proc/*/cmdline || ps auxwww | grep lemonade`
    - `nvidia-smi` or ROCm equivalent to confirm VRAM usage
  - **Acceptance**: Process list shows running Lemonade Server with flash-attn enabled; GPU memory and logs confirm expected model load (verified in dev environment).

---

### T010 - Test end-to-end text generation flow through LiteLLM

- [~] T010 [US1] Send a request through LiteLLM proxy using model aliases and verify response (verified via temporary proxy; production verification pending)
  - **Test Setup**: Temporary proxy running on internal host (`simple_proxy.py`) and `master_key` set for tests. Full LiteLLM service installation pending.
  - **Test 1 - Text generation via llm-text-gen alias** (DEV/verification):
    ```bash
    curl -X POST http://192.168.86.196:4014/v1/chat/completions \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer sk-lemonade-master-key" \
      -d '{"model":"llm-text-gen","messages":[{"role":"user","content":"What is machine learning?"}],"max_tokens":150}'
    ```
    - **Result (dev)**: returned HTTP 200 with `choices[0].message.content` (verified via `simple_proxy.py` routing to Lemonade)
  - **Test 2 - Code generation via llm-code-gen alias**: same pattern — returned HTTP 200 (verified)
  - **Acceptance**: 
    - **DEV**: Requests return HTTP 200 and responses contain `choices[0].message.content` (verified using temporary proxy)
    - **PROD**: Repeat tests after T005 completes (live `litellm` service installed, managed, and listening on 0.0.0.0:4014).

---

### T010a - SPIKE: Bifrost proof‑of‑concept (quick validation)

- [ ] T010a [SPIKE][P] Run a Bifrost gateway locally and verify Nextcloud + Lemonade can be routed through it
  - **Goal**: Determine integration work and blockers for migrating from LiteLLM → Bifrost
  - **Steps**:
    1. Start Bifrost (Docker): `docker run -p 8080:8080 maximhq/bifrost`
    2. Smoke test Bifrost: `curl -X POST http://localhost:8080/v1/chat/completions -H "Content-Type: application/json" -d '{"model":"openai/gpt-4o-mini","messages":[{"role":"user","content":"hi"}]}'`
    3. Configure Bifrost provider to proxy to Lemonade (local): add a provider entry that forwards requests to `http://localhost:8000` and enable it via the Bifrost UI or config
    4. Point Nextcloud (dev) at Bifrost: set OpenAI base_url → `http://localhost:8080/openai` and run `specs/006-nextcloud-litellm-infra/tests/dmz_smoke.sh`
    5. Collect basic perf: P50/P95 latency for 10 requests; capture logs for routing and auth
  - **Acceptance (Spike)**:
    - Nextcloud dev e2e completes for 3 sample prompts via Bifrost
    - Bifrost successfully proxies at least one model alias to Lemonade and returns coherent responses
    - No blocking ACL/permissions or auth issues discovered
    - Short report produced with recommended next steps and estimated effort for full migration
  - **Estimate**: 0.5–1 day
  - **Output**: `specs/006-nextcloud-litellm-infra/reports/bifrost-spike-YYYYMMDD.md`

---

## PHASE 4: User Story 2 - Secure API Gateway Access (DMZ ↔ Internal)

**Goal**: Deploy Apache reverse proxy in DMZ to securely forward public requests to internal LiteLLM, with TLS termination and security headers.

**Independent Test**: Send an authenticated HTTPS request to api.makerspace.ch/api/v1/chat/completions and verify it reaches LiteLLM on the internal server.

**Test Criteria**:
- Apache accepts HTTPS requests on public domain (api.makerspace.ch)
- Requests are forwarded to internal LiteLLM (http://192.168.86.196:4014)
- TLS certificate is valid
- Security headers are present in responses
- Unauthenticated requests are rejected (API key validation at LiteLLM level)

---

### T011 - Deploy Apache reverse proxy in DMZ

- [~] T011 [US2] Install and configure Apache reverse proxy on DMZ server (192.168.178.41) — in progress
  - **File**: [configs/apache-api-proxy.conf](configs/apache-api-proxy.conf)
  - **Action**:
    1. Copy apache-api-proxy.conf to `/etc/apache2/sites-available/` on DMZ server (use `configs/deploy_apache.sh`)
    2. Enable required Apache modules: `a2enmod proxy proxy_http ssl headers rewrite`
    3. Enable site: `a2ensite api-proxy` and verify `apache2ctl -t`
    4. Reload Apache: `systemctl reload apache2`
  - **Quick command (DMZ host)**: `sudo bash specs/006-nextcloud-litellm-infra/configs/deploy_apache.sh /etc/apache2/sites-available`
  - **Acceptance**: Apache starts without errors, site is enabled, syntax check passes; run `specs/006-nextcloud-litellm-infra/tests/dmz_smoke.sh` from DMZ or developer laptop (hosts override) to validate

---

### T012 - Configure TLS certificates for api.makerspace.ch

- [~] T012 [P] [US2] Obtain and install TLS certificate for api.makerspace.ch — in progress
  - **Action** (Choose one):
    - Option A (Let's Encrypt): `certbot certonly --apache -d api.makerspace.ch`
    - Option B (Existing cert): Copy existing certificate to `/etc/apache2/certs/`
  - **File Path**: `/etc/apache2/certs/api.makerspace.ch.crt` + `/etc/apache2/certs/api.makerspace.ch.key`
  - **Automation**: see `configs/README-DMZ.md` for step-by-step and `tests/dmz_smoke.sh` for verification
  - **Acceptance**: Certificate is valid, matches domain, and is not expired; `curl -vk` shows valid certificate and HSTS header

---

### T013 - Test secure routing from DMZ to internal LiteLLM

- [~] T013 [US2] Verify HTTPS request through Apache reverse proxy reaches internal LiteLLM — in progress (can be validated with temporary proxy)
  - **Test Setup**:
    1. Ensure Apache is running and listening on port 443 (HTTPS)
    2. Ensure firewall allows DMZ (192.168.178.41) → Internal (192.168.86.196:4014)
    3. Ensure DNS resolves api.makerspace.ch to 192.168.178.41 (or use hosts override for testing)
  - **Local hosts override (developer laptop)**:
    - `sudo -- sh -c "echo '192.168.178.41 api.makerspace.ch' >> /etc/hosts"`
  - **Test 1 - Unauthenticated request (should be rejected at LiteLLM)**:
    ```bash
    curl -i https://api.makerspace.ch/api/v1/health
    ```
  - **Test 2 - Authenticated request (should succeed)**:
    ```bash
    curl -i https://api.makerspace.ch/api/v1/chat/completions \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer sk-lemonade-master-key" \
      -d '{"model":"llm-text-gen","messages":[{"role":"user","content":"Test"}],"max_tokens":50}'
    ```
  - **Test 3 - Verify security headers**:
    ```bash
    bash specs/006-nextcloud-litellm-infra/tests/dmz_smoke.sh
    ```
  - **Acceptance**: 
    - Test 1: Returns HTTP 401 (LiteLLM rejects missing auth) or 200 for health endpoint depending on proxy policy
    - Test 2: Returns HTTP 200 with valid response (temporary proxy will be used if LiteLLM is not yet available)
    - Test 3: Security headers are present in response headers
    - Apache logs show successful proxy_pass routing
  - **Note**: If LiteLLM is not available, start the temporary proxy on the internal host (`run_proxy.ps1`) to validate end-to-end routing

  **Operator: Wie verbindest du in die DMZ? (Kurz‑anleitung)**
  - Empfohlenes Modell: SSH bastion/jump-host oder VPN — kein direktes Admin‑Zugriff aus dem Internet.
  - Schnelltests vom Entwickler‑Laptop (hosts-override):
    - `sudo -- sh -c "echo '192.168.178.41 api.makerspace.ch' >> /etc/hosts"`  # lokal testen
    - `curl -vk https://api.makerspace.ch/api/v1/health --resolve 'api.makerspace.ch:443:192.168.178.41'`
  - SSH / Bastion (example):
    - `ssh -J jumpuser@bastion.example.com admin@192.168.178.41`
    - `scp specs/006-nextcloud-litellm-infra/configs/apache-api-proxy.conf admin@192.168.178.41:/tmp/`
    - Auf DMZ: `sudo a2enmod proxy proxy_http ssl headers rewrite && sudo cp /tmp/apache-api-proxy.conf /etc/apache2/sites-available/api-proxy.conf && sudo a2ensite api-proxy && sudo apache2ctl -t && sudo systemctl reload apache2`
  - Windows DMZ host (PowerShell remoting):
    - `Enter-PSSession -ComputerName 192.168.178.41 -Credential (Get-Credential)` (nur wenn WinRM & firewall erlaubt)
  - Firewall / ops checklist:
    - Erlaube nur Management‑Quellen (bastion / admin VPN) zu Port 22/5985/443
    - Temporäre hosts‑Override für Entwickler ist OK — entferne Änderung nach Test
    - Verwende kurzlebige SSH keys oder cert‑based access; prüfe `auth.log` und `apache` logs nach Tests
  - **Acceptance for operator**: You can deploy `api-proxy` from the bastion, run `tests/dmz_smoke.sh` successfully from a machine that resolves `api.makerspace.ch` to the DMZ IP, and see proxied requests in Apache access logs.

---

## PHASE 5: User Story 3-5 - Extended Features (Image Generation, TTS, Audio)

**Goal**: Deploy additional services for image generation, text-to-speech, and audio transcription capabilities.

**Test Criteria**:
- OpenedAI-Speech (TTS) responds on port 8880
- ComfyUI responds on port 8188
- LiteLLM routes model aliases to correct backends
- All services reach Lemonade Server for Whisper transcription

---

### T014 - Deploy OpenedAI-Speech (TTS) with AMD ROCm support

- [ ] T014 [P] [US5] Deploy OpenedAI-Speech container on 192.168.86.196:8880 with ROCm
  - **File**: Docker command in quickstart.md
  - **Action**:
    ```bash
    docker run -d \
      --name openedai-speech-rocm \
      -p 8880:8000 \
      --device /dev/kfd \
      --device /dev/dri \
      ghcr.io/matatonic/openedai-speech-rocm:latest
    ```
  - **Verification**: 
    ```bash
    curl http://192.168.86.196:8880/v1/health
    ```
  - **Acceptance**: 
    - Container is running: `docker ps | grep openedai-speech-rocm`
    - Health endpoint returns HTTP 200
    - GPU acceleration is detected (ROCm devices available)

---

### T015 - Deploy ComfyUI for image generation on AMD ROCm

- [ ] T015 [P] [US3] Deploy ComfyUI container on 192.168.86.196:8188 with AMD ROCm
  - **File**: Docker command in quickstart.md
  - **Action**:
    ```bash
    docker run -d \
      --name comfyui-rocm \
      -p 8188:8188 \
      --device /dev/kfd \
      --device /dev/dri \
      -v /path/to/comfyui/models:/models \
      comfyui-rocm:latest
    ```
  - **Verification**: 
    ```bash
    curl http://192.168.86.196:8188/system_stats
    ```
  - **Acceptance**:
    - Container is running: `docker ps | grep comfyui-rocm`
    - System stats endpoint returns JSON with GPU info
    - ROCm GPU is detected

---

### T016 - Configure LiteLLM routing for extended model aliases (TTS, Image, Whisper)

- [ ] T016 [P] [US3] [US4] [US5] Add model aliases to LiteLLM config for TTS, image generation, and audio transcription
  - **File**: [configs/litellm-config.yaml](configs/litellm-config.yaml)
  - **Action**:
    1. Add `llm-text2speech` → OpenedAI-Speech (port 8880) with OpenAI-compatible routing
    2. Add `llm-image-gen` → ComfyUI (port 8188) with image generation endpoint
    3. Add `llm-audio-trans` → Whisper on Lemonade (port 8000) with audio endpoint
    4. Configure request routing and fallback error handling
    5. Restart LiteLLM with updated config
  - **Tests**:
    - TTS: `curl -X POST http://192.168.86.196:4014/v1/audio/speech -H "Authorization: Bearer sk-lemonade-master-key" -d '{"model":"llm-text2speech","input":"Hello world"}'`
    - Image: `curl -X POST http://192.168.86.196:4014/v1/images/generations -H "Authorization: Bearer sk-lemonade-master-key" -d '{"model":"llm-image-gen","prompt":"beautiful landscape"}'`
    - Audio: `curl -X POST http://192.168.86.196:4014/v1/audio/transcriptions -F "file=@audio.mp3" -F "model=llm-audio-trans" -H "Authorization: Bearer sk-lemonade-master-key"`
  - **Acceptance**: 
    - All three aliases are reachable through LiteLLM
    - Requests route to correct backends
    - Responses are valid (HTTP 200 with expected data format)
    - Error handling works (HTTP 503 when backend unavailable)

---

## PHASE 6: Integration & Nextcloud Configuration

**Goal**: Configure Nextcloud's AI integration app to use the LiteLLM proxy, enabling end-to-end functionality.

---

### T017 - Configure Nextcloud integration_openai app

- [ ] T017 [US1] Configure Nextcloud to use LiteLLM as AI service backend
  - **File**: [configs/nextcloud-setup.sh](configs/nextcloud-setup.sh)
  - **Action**:
    1. Run the setup script on Nextcloud server (192.168.178.41):
       ```bash
       bash configs/nextcloud-setup.sh
       ```
    2. Or manually execute occ commands:
       ```bash
       sudo -u www-data php occ config:app:set integration_openai url --value="http://192.168.86.196:4014"
       sudo -u www-data php occ config:app:set integration_openai api_key --value="sk-lemonade-master-key"
       sudo -u www-data php occ config:app:set integration_openai service_name --value="Lemonade AI"
       sudo -u www-data php occ config:system:set ai.enabled_backends '{"integration_openai"}' --type=json
       ```
  - **Verification**: 
    ```bash
    sudo -u www-data php occ config:app:get integration_openai url
    ```
  - **Acceptance**: 
    - Nextcloud AI Assistant is enabled
    - Nextcloud users can see "Lemonade AI" as available service
    - Configuration is persisted in Nextcloud config

---

## PHASE 7: Testing & Validation (Optional)

**Goal**: Validate end-to-end functionality and performance.

---

### T018 - End-to-end integration test via Nextcloud AI Assistant

- [ ] T018 [US1] Test text generation request through Nextcloud UI
  - **Manual Test**: 
    1. Login to Nextcloud as a test user
    2. Open AI Assistant chat
    3. Send prompt: "Explain artificial intelligence in 100 words"
    4. Verify response is generated within 120 seconds
  - **Acceptance**: 
    - Response is coherent and relevant
    - No errors in logs
    - Request completes within timeout

---

### T019 - Performance and load testing

- [ ] T019 [US1] [US2] Load test the system with concurrent requests
  - **Tools**: Use existing benchmarking tools (performance_benchmark.py)
  - **Test**: Send 10 concurrent requests through LiteLLM
    ```bash
    for i in {1..10}; do
      curl -X POST https://api.makerspace.ch/api/v1/chat/completions \
        -H "Authorization: Bearer sk-lemonade-master-key" \
        -d '{"model":"llm-text-gen","messages":[{"role":"user","content":"Hello"}]}' &
    done
    wait
    ```
  - **Acceptance**: 
    - All 10 requests return HTTP 200
    - No timeouts
    - Average response time < 30 seconds
    - System remains stable

---

## Parallel Execution Examples

### Scenario 1: Fast Track (MVP in 2 hours)

**Execute Phases 1-4 in order** (total ~3 hours):
1. Phase 1 (T001-T003): 30 min setup
2. Phase 2 (T004, then T005||T006): 15 min Lemonade + 30 min parallel LiteLLM+verify
3. Phase 3 (T007, then T008||T009, then T010): 15 min config + 30 min parallel tests + 15 min integration
4. Phase 4 (T011, then T012||forward, then T013): 15 min Apache + 15 min TLS + 15 min validation

**Result**: Full text generation + secure API gateway working. Deploy to production.

### Scenario 2: Extended Features (Full System)

After MVP is deployed:
1. T014-T016 can run in **parallel** (all deploy new services independently)
2. T017 configures Nextcloud to use all services
3. T018-T019 validate full system

---

## Success Metrics

| Metric | Target | Verification |
|--------|--------|--------------|
| Text generation latency | < 120 sec | curl response time < 120s |
| API gateway uptime | 99% | Apache/LiteLLM availability |
| Model accuracy | Baseline | Qualitative: response coherence |
| Concurrent requests | 4 models = 4 concurrent | Lemonade Server concurrency settings |
| Security | OWASP headers present | curl response headers check |
| Logging | Metadata only | Inspect log files, no prompts visible |

---

## Deployment Checklist

- [ ] All configuration files reviewed and validated (T002)
- [ ] Network connectivity verified (T003)
- [ ] Lemonade Server running with correct models (T004)
- [ ] LiteLLM Proxy deployed and healthy (T005-T006)
- [ ] Text generation flow tested (T007-T010)
- [ ] Apache reverse proxy configured in DMZ (T011-T012)
- [ ] Secure routing validated (T013)
- [ ] Optional: Extended features deployed (T014-T016)
- [ ] Nextcloud configured to use LiteLLM (T017)
- [ ] End-to-end test passed (T018)
- [ ] Load testing passed (T019)

---

## Rollback Procedures

If any phase fails:

1. **Phase 1-2 Failure**: Stop all services (`systemctl stop litellm apache2`), review configuration, redeploy
2. **Phase 3 Failure**: Revert LiteLLM config to previous version, restart proxy
3. **Phase 4 Failure**: Disable Apache site (`a2dissite api-proxy`), revert to direct Nextcloud→LiteLLM for testing
4. **Phase 5 Failure**: Stop optional services (ComfyUI, OpenedAI-Speech), core system remains functional

---

## Notes & Decisions

- **Configuration-First Approach**: No source code changes; all deployment via configuration files and deployment scripts
- **MVP Strategy**: Focus on text generation (T001-T013) first, add image/TTS/audio later
- **Security-First DMZ Design**: Apache reverse proxy provides TLS termination and header injection; internal network uses HTTP (trusted)
- **Fail-Fast Behavior**: HTTP 503 when backend unavailable (per specification); no retries to maintain predictable behavior
- **Observability**: Metadata logging only (timestamps, model names, status codes); no prompt/response content in logs
- **Concurrency**: LiteLLM configured with no aggressive queueing; Lemonade Server handles concurrency internally via `--max-loaded-models 4 1 1 1`
