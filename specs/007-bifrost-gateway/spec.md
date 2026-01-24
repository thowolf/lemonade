# Feature: 007 - Bifrost gateway (LiteLLM → Bifrost migration)

Goal
- Validate feasibility and cost of replacing the on-prem LiteLLM proxy with a Bifrost gateway that provides OpenAI-compatible routing, multi-provider fallbacks, and lightweight semantic caching.

Non-goals
- Full production cut-over (this feature begins with a Spike + staged rollout plan).

Acceptance criteria
- Spike demonstrates end-to-end Nextcloud → Bifrost → Lemonade routing on a developer machine or staging host
- A migration plan with risks, rollout steps, and estimated work is produced
- No regressions for existing Nextcloud flows (text generation) in DEV

Security
- Bifrost must be run behind the same DMZ reverse-proxy and honor existing API-key auth and rate-limits

Outputs
- `specs/007-bifrost-gateway/plan.md` (migration plan)
- `specs/007-bifrost-gateway/tasks.md` (work breakdown)
- Spike report: `specs/006-nextcloud-litellm-infra/reports/bifrost-spike-YYYYMMDD.md`