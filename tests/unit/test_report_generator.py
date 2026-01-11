from scripts.benchmarks.continue_testing.report_generator import PerformanceAnalyzer, ReportGenerator


def test_calculate_aggregates_simple():
    rts = [100.0, 200.0, 300.0, 400.0, 500.0]
    tps = [10.0, 12.0, 11.0, 9.0, 10.0]
    ag = PerformanceAnalyzer.calculate_aggregates(rts, tps)
    assert round(ag["mean"], 2) == 300.0
    assert round(ag["p50"], 2) == 300.0
    assert ag["p95"] is not None
    assert round(ag["tps_mean"], 2) == round(sum(tps)/len(tps), 2)


def test_generate_compatibility_matrix():
    runs = [
        {"model_name": "m1", "freeze_detected": False, "num_interactions_completed": 10},
        {"model_name": "m1", "freeze_detected": False, "num_interactions_completed": 10},
        {"model_name": "m1", "freeze_detected": True, "freeze_after_interaction": 3, "num_interactions_completed": 3},
        {"model_name": "m2", "freeze_detected": True, "freeze_after_interaction": 2, "num_interactions_completed": 2},
    ]
    matrix = ReportGenerator.generate_compatibility_matrix(runs)
    assert "m1" in matrix and "m2" in matrix
    assert matrix["m1"]["freeze_rate_percent"] > 0.0
    assert matrix["m2"]["compatible"] is False
