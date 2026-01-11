from scripts.benchmarks.continue_testing.examples import compute_avg_from_per_run


def test_compute_avg_from_per_run():
    per_run = [
        {"name": "r1", "summary": {"avg_cpu": 10, "foo": 1}},
        {"name": "r2", "summary": {"avg_cpu": 20, "foo": 3}},
    ]
    out = compute_avg_from_per_run(per_run)
    assert out["avg_cpu"] == 15.0
    assert out["foo"] == 2.0
