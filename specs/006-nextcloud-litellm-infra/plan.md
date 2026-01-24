# Implementation plan — 006-nextcloud-litellm-infra

Overview
This plan converts the specification into actionable milestones, commands, verification steps and rollback procedures so the feature can be delivered reproducibly in the `lemonade` repo and on the target hosts.

Milestones
- M1 — Prepare & validate configs (DEV smoke) — 0.5 day
- M2 — Service hardening: NSSM/systemd + prisma migrations — 1 day
- M3 — DMZ proxy & Nextcloud integration — 0.5 day
- M4 — E2E tests, documentation, cutover & rollback plan — 0.5 day

Phases & Tasks (mapping to tasks.md)
- Phase 1 (Setup): T001–T003 — directory, config templates, network checks
- Phase 2 (Foundational): T004–T006 — Lemonade + LiteLLM proxy + service install
- Phase 3 (Integration): T007–T010 — model routing, e2e tests
- Phase 4 (Secure Gateway): T011–T013 — Apache DMZ, TLS, health
- Phase 5 (Polish): T014–T016 — extended features and documentation

Runbook (deploy to a single host — DMZ + internal)
Prereqs (on operator workstation / admin): Git repo checked out, Admin rights on target hosts, Docker or Python/Conda available.

1) Dev smoke (local)
- Start Lemonade locally (dev):
  tools\benchmarks\start_quality_multiport.ps1 -Load
- Start temporary proxy (dev unblock):
  python specs/006-nextcloud-litellm-infra/simple_proxy.py --port 4014 --backend http://localhost:8000
- Verify health:
  curl -i http://localhost:4014/v1/health

2) Service install (Windows NSSM) — idempotent
- Ensure prisma is installed in the Python that will run the service:
  "C:\Users\tomwo\miniconda3\python.exe" -m pip install prisma
- Configure NSSM (example):
  nssm set LiteLLM-Proxy Application "C:\Users\tomwo\miniconda3\python.exe"
  nssm set LiteLLM-Proxy AppParameters "-m litellm --config C:\\path\\to\\litellm-config.yaml --port 4014"
  nssm set LiteLLM-Proxy AppEnvironmentExtra "PYTHONIOENCODING=utf-8" "DATABASE_URL=sqlite:///C:/path/to/litellm.db" "LITELLM_MASTER_KEY=<REDACTED>"
  nssm restart LiteLLM-Proxy
- Verify migrations in logs:
  Get-Content scripts/litellm/logs/litellm-service.log -Tail 200 | Select-String 'alembic|Running upgrade|Connected to DB'

3) DMZ proxy (Apache) — one‑liner (example)
- Deploy config and enable site:
  sudo cp specs/006-nextcloud-litellm-infra/configs/apache-api-proxy.conf /etc/apache2/sites-available/
  sudo a2ensite apache-api-proxy.conf && sudo apachectl configtest && sudo systemctl reload apache2
- Verify from external host:
  curl -v --resolve 'api.example.com:443:PUBLIC_IP' 'https://api.example.com/v1/health'

4) Nextcloud integration & smoke
- Configure Nextcloud Assistant to use OpenAI base_url → `https://<dmz-host>/openai`
- Run e2e smoke:
  bash specs/006-nextcloud-litellm-infra/tests/dmz_smoke.sh

Rollback plan
- If DB migrations fail: stop service, restore DB file from predeploy snapshot, revert NSSM AppEnvironmentExtra to previous value, restart service.
- If DMZ proxy fails: disable site (`a2dissite`) and revert to maintenance page, alert ops.

Verification matrix
- Unit: config YAML schema validation (automated)
- Smoke: /v1/health (automated in CI)
- Integration: Nextcloud Assistant end‑to‑end (manual + automated nightly)

Acceptance checklist (pre‑release)
- [ ] Installer sets service to use detected Python and verifies `prisma` import
- [ ] Health endpoints return OK and DB migrations logged
- [ ] Nextcloud Assistant returns valid LLM completions in 3 sample prompts
- [ ] Documentation (quickstart + runbook) added to `specs/006-nextcloud-litellm-infra/`

Post‑deploy tasks
- Rotate master key and publish new secret in Vault
- Schedule monitoring dashboard and alerting (error rate, latency)

Appendix — useful commands
- Show NSSM env: `nssm get LiteLLM-Proxy AppEnvironmentExtra`
- Tail logs: `Get-Content scripts/litellm/logs/litellm-service.log -Tail 200 -Wait`
- Health check (uses master key if present):
  `curl -H "Authorization: Bearer $(nssm get LiteLLM-Proxy AppEnvironmentExtra LITELLM_MASTER_KEY)" http://localhost:4014/health`

Owners & reviewers
- Implementation: platform team (tomwo)
- Security review: infra/security
- Product acceptance: ai-product
