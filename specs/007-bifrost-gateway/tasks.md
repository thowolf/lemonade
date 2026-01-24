# Tasks: 007 - Bifrost gateway

## Summary
- Total tasks: 6 (Spike → Pilot → Rollout)

## T100 - Spike: Bifrost proof‑of‑concept
- [ ] T100a Run Bifrost locally and proxy a provider to Lemonade
- [ ] T100b Validate Nextcloud DEV e2e via Bifrost
- [ ] T100c Produce spike report with blockers & estimate

## T101 - Pilot on staging
- [ ] T101a Deploy Bifrost behind DMZ proxy (staging)
- [ ] T101b Run integration tests and perf baseline

## T102 - Rollout & cutover
- [ ] T102a Dual-run traffic with Canary routing
- [ ] T102b Cutover and decommission LiteLLM

Notes
- T100 is highest priority and should be executed before other T10x tasks.