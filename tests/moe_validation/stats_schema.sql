-- MoE Validation Stats Database Schema
-- Feature: 002-moe-qwen3-tests
-- Purpose: Store test results for MoE model validation runs

-- Model Artifact Table
CREATE TABLE IF NOT EXISTS model_artifacts (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    path TEXT NOT NULL,
    checksum TEXT,
    size_bytes INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON
);

-- Test Run Table
CREATE TABLE IF NOT EXISTS test_runs (
    id TEXT PRIMARY KEY,
    model_id TEXT NOT NULL,
    device TEXT NOT NULL CHECK(device IN ('cpu', 'igpu', 'hybrid', 'npu')),
    seed INTEGER,
    build_id TEXT,
    config JSON,
    status TEXT NOT NULL CHECK(status IN ('pending', 'running', 'completed', 'failed')),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    FOREIGN KEY (model_id) REFERENCES model_artifacts(id)
);

-- Results Report Table
CREATE TABLE IF NOT EXISTS results_reports (
    run_id TEXT PRIMARY KEY,
    ttft_seconds REAL CHECK(ttft_seconds >= 0),
    tps REAL CHECK(tps >= 0),
    memory_gb REAL CHECK(memory_gb >= 0),
    mmlu_score REAL CHECK(mmlu_score >= 0 AND mmlu_score <= 1),
    gsm8k_score REAL CHECK(gsm8k_score >= 0 AND gsm8k_score <= 1),
    llm_judgement INTEGER CHECK(llm_judgement >= 1 AND llm_judgement <= 5),
    llm_judgement_reason TEXT,
    csv_path TEXT,
    stats_db_path TEXT,
    FOREIGN KEY (run_id) REFERENCES test_runs(id)
);

-- CI Job Table
CREATE TABLE IF NOT EXISTS ci_jobs (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    runner TEXT,
    exit_code INTEGER,
    output TEXT,
    duration_seconds REAL CHECK(duration_seconds > 0),
    passed BOOLEAN,
    FOREIGN KEY (run_id) REFERENCES test_runs(id)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_test_runs_model_id ON test_runs(model_id);
CREATE INDEX IF NOT EXISTS idx_test_runs_status ON test_runs(status);
CREATE INDEX IF NOT EXISTS idx_test_runs_device ON test_runs(device);
CREATE INDEX IF NOT EXISTS idx_ci_jobs_run_id ON ci_jobs(run_id);
CREATE INDEX IF NOT EXISTS idx_ci_jobs_passed ON ci_jobs(passed);

-- View: Latest Results Summary
CREATE VIEW IF NOT EXISTS latest_results AS
SELECT
    tr.id AS run_id,
    ma.name AS model_name,
    tr.device,
    tr.status,
    tr.started_at,
    rr.ttft_seconds,
    rr.tps,
    rr.memory_gb,
    rr.mmlu_score,
    rr.gsm8k_score,
    rr.llm_judgement,
    rr.llm_judgement_reason
FROM test_runs tr
JOIN model_artifacts ma ON tr.model_id = ma.id
LEFT JOIN results_reports rr ON tr.id = rr.run_id
ORDER BY tr.started_at DESC;

-- View: CI Job Success Rate
CREATE VIEW IF NOT EXISTS ci_success_rate AS
SELECT
    COUNT(*) AS total_jobs,
    SUM(CASE WHEN passed = 1 THEN 1 ELSE 0 END) AS passed_jobs,
    ROUND(100.0 * SUM(CASE WHEN passed = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) AS success_rate_percent
FROM ci_jobs;

-- Sample Data (for testing)
-- INSERT INTO model_artifacts (id, name, path, checksum, size_bytes)
-- VALUES ('model-001', 'qwen3-next-80b-q4_k_m.gguf', '/path/to/model.gguf', 'sha256hash', 42949672960);

-- INSERT INTO test_runs (id, model_id, device, seed, build_id, config, status, started_at)
-- VALUES ('run-001', 'model-001', 'cpu', 42, 'build-123', '{"limit": 5, "warmup": 0}', 'running', CURRENT_TIMESTAMP);

-- INSERT INTO results_reports (run_id, ttft_seconds, tps, memory_gb, mmlu_score, gsm8k_score, llm_judgement, llm_judgement_reason)
-- VALUES ('run-001', 2.3, 15.7, 8.2, 0.72, 0.45, 4, 'Clear and relevant response');
