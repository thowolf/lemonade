# Test Results Directory

This directory contains benchmark results, test outputs, and performance data from ROCm Max395 testing.

## File Structure

- `benchmark_*.json`: Individual benchmark result files (one per test run)
- `summary_*.txt`: Formatted summary reports
- `comparison_*.txt`: Performance comparison reports between different configurations
- `*.html`: HTML reports with charts and visualizations

## Result File Format

Each benchmark result follows the JSON schema defined in `contracts/benchmark_results.json`.

### Key Metrics

- **tokens_per_second**: Generation throughput (higher is better)
- **time_to_first_token_ms**: Initial response latency (lower is better)
- **total_latency_ms**: Complete response time (lower is better)
- **vram_usage_gb**: GPU memory consumption
- **vram_utilization_percent**: Percentage of total VRAM used
- **error_rate_percent**: Percentage of failed requests (lower is better)

### Performance Targets (AMD AI Max+ 395)

| Model Size | Target Tokens/sec | Target Latency (ms) | Expected VRAM (GB) |
|------------|-------------------|---------------------|-------------------|
| 1B         | 40+              | <500               | 2-3              |
| 7B         | 20+              | <1000              | 5-8              |
| 13B        | 10+              | <1500              | 10-15            |
| 30B+       | 5+               | <2000              | 25-60            |

## Interpreting Results

### Success Criteria

- **Tokens/second**: Should meet or exceed targets for model size
- **Latency**: Should be under target thresholds
- **VRAM Usage**: Should be efficient (not exceeding 80% for large models)
- **Error Rate**: Should be 0% for stable testing
- **Stability**: Performance should remain consistent across iterations

### Common Issues

- **Low tokens/second**: Check ROCm driver installation, model quantization
- **High latency**: Verify GPU utilization, check for background processes
- **VRAM exhaustion**: Model too large for available memory, consider smaller model
- **High error rate**: Check Lemonade Server logs, verify API connectivity

## Generating Reports

Use the `ReportGenerator` utility to create formatted reports:

```python
from utils.report_generator import create_report_generator

generator = create_report_generator(Path("results/"))
# Generate summary report
generator.generate_test_summary_report(test_results, environment)
# Generate performance report
generator.generate_performance_report(benchmark_results)
```

## Comparison Analysis

Compare results between different configurations:

```python
# Compare ROCm vs Vulkan backends
generator.generate_comparison_report(
    rocm_results, vulkan_results,
    "ROCm Backend", "Vulkan Backend"
)
```

## Archiving Results

Results are automatically excluded from git (see `.gitignore`), but can be archived:

```bash
# Create timestamped archive
timestamp=$(date +%Y%m%d_%H%M%S)
tar -czf results_archive_${timestamp}.tar.gz results/
```

## Troubleshooting

### Missing Results
- Check that tests completed successfully
- Verify file permissions in results directory
- Check Lemonade Server logs for API errors

### Invalid JSON
- Results follow strict schema validation
- Check for encoding issues or truncated files
- Re-run tests if corruption detected

### Performance Issues
- Compare against baseline results
- Check system resource usage during testing
- Verify ROCm driver and hardware configuration