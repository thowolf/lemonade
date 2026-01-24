# specs/006-nextcloud-litellm-infra — Specification

Summary
- Purpose: enable Nextcloud → LiteLLM → Lemonade Server on-prem routing with a secure, observable, and recoverable DMZ proxy (Apache) and a resilient internal LLM gateway/service.
- Owners: Platform / AI Ops
- Priority: High (local infra + Nextcloud integration)

Goals
- Provide a reproducible, secure deployment for Nextcloud AI Assistant that routes requests to local LLMs via LiteLLM and Lemonade Server.
- Ensure the gateway is OpenAI‑compatible so Nextcloud and existing clients require minimal changes.
- Deliver a hardened NSSM/systemd service for LiteLLM that runs migrations and preserves encoding + secrets handling.

Scope
- In scope: Nextcloud Assistant integration, LiteLLM proxy service (Windows NSSM + Linux service unit), Lemonade model hosting, Apache DMZ reverse proxy, local SQLite persistence for dev, CI smoke tests.
- Out of scope: full K8s production migration (separate epic), multi‑region HA (future work).

Assumptions
- Target environment: mixed Windows (service host) and Linux (Lemonade), developer has admin on hosts.
- Primary dev/test model storage is local files; production may use HF/TGI later.

Architecture (high level)
- Nextcloud (frontend) → Apache DMZ (public TLS) → LiteLLM Proxy (internal, port 4014) → Lemonade Server (models, port 8000)
- Persistence: local SQLite for metadata (dev); Prisma runs in the same Python env as the service.
- Observability: Prometheus metrics + service logs; health and readiness endpoints.

Security / Secrets
- Secrets stored out of VCS (use OS keyring or HashiCorp Vault for production). `LITELLM_MASTER_KEY` rotated at install time.
- TLS terminated at DMZ Apache; internal traffic uses mTLS or strict ACLs when possible.

Acceptance criteria (must pass)
- `specs/006-nextcloud-litellm-infra/spec.md` and `plan.md` exist in the repo (this file)
- `curl http://localhost:4014/v1/health` → HTTP 200 (service or temporary proxy)
- LiteLLM service runs under the Python that has `prisma` installed and Alembic/prisma migrations run successfully (see `logs/litellm-service.log` for "Running upgrade" / "Connected to DB")
- Nextcloud Assistant can call `/v1/chat/completions` (end‑to‑end smoke test)

Dependencies
- LiteLLM, Lemonade Server, Prisma (Python), NSSM (Windows) or systemd (Linux), Apache (DMZ), Nextcloud instance.

Non‑functional requirements
- Startup latency (gateway overhead) < 2 ms (target for local dev); production P95 target depends on model.  
- Failover: automatic fallback when upstream provider fails (for hybrid deployments).

Risks & Mitigations
- Risk: Service runs under wrong Python → Mitigation: installer detects service Python and installs `prisma` into it; health check fails fast with actionable logs.
- Risk: Secrets leakage in .env → Mitigation: .env remains git‑ignored; installer documents Vault integration.

Open issues
- Decide production persistence (SQLite → Postgres) and migration plan.

Audit / Compliance notes
- Document data retention for user prompts in Nextcloud; redact PII before persisting logs; configurable retention policy in `configs`.

Contacts
- Primary: platform@yourorg (owner)
- Reviewer: tomwo
