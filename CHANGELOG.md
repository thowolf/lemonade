# Changelog

## Unreleased

- scripts/benchmarks/continue-testing: Make W&B logging resilient to partial implementations — the test runner now checks for callable W&B methods before invoking them (e.g., `start_run`, `log_metrics`, `log_test_run`, `finish_run`). This prevents AttributeError when using lightweight test fakes and improves robustness. (tests updated)
- scripts/benchmarks/continue-testing: Expanded W&B support with grouping and time-series support (added `log_metrics_series` with optional step/timestamp, `set_group`, and group/run metadata in `start_run`). Added integration tests for W&B, scheduled runs, and long-duration monitoring under `tests/integration/`. (integration tests added)
