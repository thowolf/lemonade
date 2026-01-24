# Plan: 007 - Bifrost gateway migration (high level)

Summary
- Run a short Spike (0.5–1 day) to validate Bifrost as a drop-in replacement for LiteLLM for Nextcloud use-cases.

Phases
1. Spike (DEV): local Docker Bifrost + provider proxy to Lemonade — validate routing, auth, latency
2. Pilot (STAGING): run Bifrost on staging host behind Apache DMZ proxy; exercise Nextcloud E2E
3. Gradual rollout (PROD): dual-run LiteLLM+Bifrost, route a small percent of traffic to Bifrost, monitor
4. Cutover: switch DNS/proxy to Bifrost; retire LiteLLM after 2 weeks of stable metrics

Rollout risks & mitigations
- Auth / header mismatch: add middleware to map headers (mitigation: provider-level header rewrite)
- Rate-limiting differences: sync rate-limit config and apply conservative quotas during pilot
- Observability gaps: ensure tracing/metrics exported (Prometheus + request logs)

Runbook (Spike)
- Start Lemonade (dev host)
- Start Bifrost (docker): `docker run -p 8080:8080 maximhq/bifrost`
- Add provider forwarding config to Bifrost pointing to `http://localhost:8000`
- Point Nextcloud dev to Bifrost and run `specs/006-nextcloud-litellm-infra/tests/dmz_smoke.sh`

Deliverables
- Spike report (issues, blockers, effort estimate)
- Migration TCK (tests that must pass before cutover)

Estimate
- Spike: 0.5–1 day
- Pilot: 1–2 days
- Rollout & polish: 3–5 days