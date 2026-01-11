from scripts.benchmarks.continue_testing.report_generator import ReportGenerator


def test_markdown_and_csv_output():
    runs = [
        {"model_name": "m1", "freeze_detected": False, "num_interactions_completed": 10, "response_time_ms": 8000, "tokens_per_second": 18},
        {"model_name": "m2", "freeze_detected": True, "num_interactions_completed": 2, "response_time_ms": 22000, "tokens_per_second": 5},
    ]
    matrix = ReportGenerator.generate_compatibility_matrix(runs)
    md = ReportGenerator.generate_markdown(matrix)
    csv = ReportGenerator.generate_csv(matrix)
    assert "| Model |" in md
    assert "m1" in md and "m2" in md
    assert "m1" in csv and "m2" in csv
