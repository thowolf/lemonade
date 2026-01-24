# Quickstart — Bifrost Spike (developer)

Requirements
- Docker
- Lemonade running locally on port 8000

Steps
1. Start Lemonade (dev): `./tools/benchmarks/start_quality_multiport.ps1 -Load`
2. Start Bifrost (docker):
   `docker run --rm -p 8080:8080 maximhq/bifrost`
3. Smoke test Bifrost (proxy to an external model):
   `curl -X POST http://localhost:8080/v1/chat/completions -H "Content-Type: application/json" -d '{"model":"openai/gpt-4o-mini","messages":[{"role":"user","content":"hi"}]}'`
4. Add a local provider to forward requests to Lemonade (example config in `examples/`)
5. Point Nextcloud dev at `http://localhost:8080/openai` and run `specs/006-nextcloud-litellm-infra/tests/dmz_smoke.sh`

If you hit auth errors: verify `Authorization` header is passed through and that `sk-lemonade-master-key` is accepted by Lemonade.