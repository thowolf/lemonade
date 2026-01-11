# Continue Extension Model Testing Framework

A comprehensive testing framework for evaluating local coder models with the Continue VSCode extension on AMD Ryzen AI hardware. Supports interactive testing, automated scheduling, trend analysis, and performance benchmarking.

## Features

- ✅ **Model Compatibility Testing**: Automated testing of multiple models for freeze detection
- ✅ **Hardware Monitoring**: Real-time NPU, CPU, and memory utilization tracking
- ✅ **Freeze Detection**: Automatic detection and diagnostic data collection
- ✅ **Performance Benchmarking**: Response time, tokens/sec, and resource usage metrics
- ✅ **Automated Scheduling**: Cron-style scheduled testing with notifications
- ✅ **Trend Analysis**: Historical performance trend detection and alerting
- ✅ **Multi-format Reporting**: JSON, Markdown, and CSV report generation

## Prerequisites

1. **Python 3.13+**: Required for the testing framework
2. **VSCode with Continue Extension**: Install VSCode and configure Continue with local models
3. **AMD Ryzen AI Hardware**: System with NPU support for optimal testing
4. **Local Model Server**: Ollama, LM Studio, or compatible local LLM server
5. **Dependencies**: Install with `pip install -e .[continue_testing]`

## Quick Start

### 1. Install Dependencies
```bash
cd scripts/benchmarks/continue-testing
pip install -e .[continue_testing]
```

### 2. Configure Models
Edit `config/models.yaml` to specify your test models:
```yaml
models:
  qwen3:0.6b:
    name: "Qwen 2.5 Coder 7B"
    source: "ollama"
    quantization: "q4"
    expected_memory_mb: 4000
  llama3.2:3b:
    name: "Llama 3.2 3B Instruct"
    source: "ollama"
    quantization: "q4"
    expected_memory_mb: 2000
```

### 3. Run Interactive Test
```bash
# Test a specific model interactively
python test_runner.py --model qwen3:0.6b --interactive --interactions 5
```

### 4. Generate Reports
```bash
# Generate compatibility matrix
python report_generator.py compatibility --format markdown

# Generate performance comparison
python report_generator.py performance --format markdown

# Analyze historical trends
python report_generator.py trends --days-back 30 --format markdown
```

## Weights & Biases Integration

The framework supports experiment tracking and visualization with Weights & Biases (W&B).

### Setup W&B

1. **Install W&B**:
   ```bash
   pip install wandb
   ```

2. **Login to W&B**:
   ```bash
   wandb login
   ```
   Or set your API key:
   ```bash
   export WANDB_API_KEY=your_api_key_here
   ```

3. **Create a Project** (optional):
   Create a project in W&B web interface or let the framework create one automatically.

### Using W&B with Tests

**Interactive Testing with W&B**:
```bash
python test_runner.py --model qwen3:0.6b --interactive --wandb
```

**Scheduled Testing with W&B**:
```bash
python test_runner.py --schedule "0 */4 * * *" --wandb
```

**Offline W&B Mode** (for air-gapped environments):
```bash
# Run tests offline, sync later when connected
python test_runner.py --model qwen3:0.6b --interactive --wandb --offline-wandb

# Sync offline data when connected
wandb sync
```

**Disable W&B**:
```bash
# Explicitly disable W&B even if installed
python test_runner.py --model qwen3:0.6b --interactive --no-wandb
```

### What Gets Logged

- **Test Runs**: Model performance, freeze events, interaction counts
- **Performance Metrics**: Response times, tokens/second, NPU utilization, memory usage
- **System Metrics**: CPU, memory, and NPU utilization over time
- **Trend Analysis**: Performance comparisons across models and time periods

### W&B Project Structure

- **Project**: `lemonade-continue-testing`
- **Run Groups**: Organized by test type (interactive, scheduled, monitor-only)
- **Run Names**: Include model name, timestamp, and test parameters

## Usage Modes

### Interactive Testing
Guided testing with user prompts for each interaction:
```bash
python test_runner.py --model qwen3:0.6b --interactive --interactions 10 --verbose
```

### Monitor-Only Mode
Background system monitoring without model testing:
```bash
python test_runner.py --monitor-only --duration 300
```

### Scheduled Automated Testing
Continuous testing with cron-style scheduling:
```bash
# Run tests every 4 hours
python test_runner.py --schedule "0 */4 * * *"

# Run daily at 2 AM
python test_runner.py --schedule "0 2 * * *"
```

## Configuration Files

### models.yaml
Model configurations with hardware requirements:
```yaml
models:
  model_id:
    name: "Display Name"
    source: "ollama"  # or "lmstudio"
    quantization: "q4"
    expected_memory_mb: 4000
    max_tokens: 4096
```

### notifications.yaml
Configure automated notifications for alerts:
```yaml
# Email notifications
email_enabled: true
email_smtp_server: "smtp.gmail.com"
email_smtp_port: 587
email_username: "your-email@gmail.com"
email_password: "your-app-password"
email_from: "your-email@gmail.com"
email_to:
  - "admin@example.com"

# Slack notifications
slack_enabled: true
slack_webhook_url: "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"

# Notification triggers
notify_on_degradation: true
notify_on_improvement: true
notify_on_freeze: true
notify_on_completion: false
```

### hardware.yaml
Auto-detected hardware configuration (generated automatically):
```yaml
hardware:
  cpu:
    model: "AMD Ryzen AI 9 365"
    cores: 8
  memory:
    total_gb: 32
  npu:
    available: true
    device_count: 1
```

## Report Generation

### Compatibility Matrix
Shows which models work reliably without freezing:
```bash
python report_generator.py compatibility --format markdown
```

### Performance Comparison
Quantitative performance metrics across models:
```bash
python report_generator.py performance --format markdown
```

### Trend Analysis
Historical performance trends and degradation detection:
```bash
python report_generator.py trends --days-back 30 --format markdown
```

### Freeze Pattern Analysis
Analysis of freeze events and patterns:
```bash
python report_generator.py freeze-analysis --format markdown
```

## Automated Testing Setup

### 1. Configure Notifications (Optional)
Create `config/notifications.yaml` to enable alerts for:
- Performance degradation
- Model improvements
- Freeze events
- Test completion

### 2. Start Scheduled Testing
```bash
# Run tests every 6 hours
python test_runner.py --schedule "0 */6 * * *"

# The framework will:
# - Test all configured models automatically
# - Save results with timestamps
# - Analyze trends and detect degradation
# - Send notifications for significant changes
# - Generate updated reports
```

### 3. Monitor Results
Results are organized by date in `results/`:
```
results/
├── 2025-12-25/
│   ├── scheduled_qwen3-0.6b_1735084800.json
│   └── scheduled_llama3.2-3b_1735084800.json
├── reports/
│   ├── trend_analysis_2025-12-25.md
│   └── compatibility_matrix_2025-12-25.md
└── freeze_events/
    └── freeze_2025-12-25_001.json
```

## Output Formats

All reports support multiple output formats:

- **JSON**: Machine-readable data for further processing
- **Markdown**: Human-readable reports with tables and formatting
- **CSV**: Spreadsheet-compatible data for analysis

## Troubleshooting

### Model Connection Issues
- Verify Continue extension is configured with correct API endpoint
- Check that local model server is running and accessible
- Confirm model IDs match exactly in configuration

### NPU Monitoring Not Working
- Ensure AMD Ryzen AI drivers are installed
- Check that `xrt-smi` command is available in PATH
- Verify NPU is enabled in BIOS/UEFI settings

### Scheduled Testing Not Starting
- Check cron expression syntax
- Ensure notifications.yaml exists if notifications are expected
- Verify all dependencies are installed

### High Memory Usage
- Reduce `--interactions` count for memory-constrained systems
- Use smaller models or higher quantization levels
- Close other applications during testing

## Architecture

### Core Components

- **test_runner.py**: Main CLI with interactive, monitor, and scheduled modes
- **report_generator.py**: Report generation and trend analysis
- **model_manager.py**: Configuration management and model handling
- **metrics_collector.py**: System resource monitoring
- **freeze_detector.py**: Freeze detection and diagnostics

### Data Flow

1. **Configuration**: Load models, scenarios, and hardware config
2. **Testing**: Execute interactions with real-time monitoring
3. **Analysis**: Process results and detect patterns
4. **Reporting**: Generate formatted reports and alerts
5. **Scheduling**: Repeat testing on configured schedule

## Integration

### RyzenAI Benchmarks
Leverages patterns from existing RyzenAI-SW benchmarks for:
- NPU utilization monitoring via xrt-smi
- System resource tracking
- Performance metrics collection

### Continue Extension
Integrates with Continue VSCode extension for:
- Model API communication
- Freeze detection via timeout monitoring
- Log analysis for error patterns

## Development

### Adding New Test Scenarios
Extend `config/test_scenarios.yaml` with new test cases:
```yaml
scenarios:
  - name: "code_review"
    description: "Test code review capabilities"
    prompt: "Review this code for bugs..."
    expected_contains: ["bug", "issue"]
```

### Custom Metrics
Extend `SystemMonitor` class for additional metrics:
```python
def _sample_custom_metric(self) -> float:
    # Add custom monitoring logic
    return custom_value
```

### Notification Channels
Add new notification methods in `NotificationHandler`:
```python
def _send_custom_notification(self, title: str, message: str) -> None:
    # Implement custom notification logic
    pass
```

## Success Criteria

- ✅ **Model Compatibility**: At least one model completes 20+ interactions without freezing
- ✅ **Freeze Detection**: Automatic detection within 30 seconds with full diagnostics
- ✅ **NPU Utilization**: Hardware acceleration monitoring and validation
- ✅ **Performance Metrics**: <5% variance between identical test runs
- ✅ **Automated Testing**: Reliable scheduled execution with notifications
- ✅ **Trend Analysis**: Accurate degradation/improvement detection over time

## License

This framework is part of the Lemonade project for AMD Ryzen AI optimization.