# Quickstart: MoE Qwen3 Model Validation

**Goal**: Run your first Mixture-of-Experts model validation using the Lemonade Server in under 15 minutes

**Prerequisites**: Lemonade Server running, Python 3.10-3.13, internet connection

## Step 1: Start Lemonade Server (2 minutes)

### Verify Server is Running

```powershell
# Check if Lemonade Server is already running
curl http://localhost:8000/api/v1/models
```

If not running, start it:

```powershell
# Start Lemonade Server with default configuration
lemonade-server serve

# Or use development mode for testing
lemonade-server-dev serve
```

**Verify**:
```powershell
# Should return JSON with available models
curl http://localhost:8000/api/v1/models
```

## Step 2: Install Dependencies (3 minutes)

### Install Required Packages

```powershell
# Navigate to repository root
cd C:\path\to\lemonade

# Install core dependencies
pip install lemonade-sdk[dev,oga-ryzenai] --extra-index-url=https://pypi.amd.com/simple

# Install notebook dependencies
pip install jupyter openai pandas

# Optional: Install lm-evaluation-harness for accuracy tests
pip install lm-eval
```

**Verify installations**:
```powershell
python -c "import openai, pandas; print('Dependencies OK')"
```

## Step 3: Open Validation Notebook (2 minutes)

### Launch Jupyter Notebook

```powershell
# Navigate to examples directory
cd examples\notebooks

# Start Jupyter
jupyter notebook moe_qwen3_validation.ipynb
```

**Alternative**: Open in VS Code
- Open `examples/notebooks/moe_qwen3_validation.ipynb`
- Select Python kernel (Python 3.10+)
- Run cells sequentially

## Step 4: Run Quick Validation (5 minutes)

### Execute Notebook Cells

1. **Setup Cell**: Run first code cell to configure environment
2. **Server Check**: Verify server connection and model availability
3. **Benchmark**: Run performance tests (TTFT, TPS)
4. **Results**: View aggregated results and CSV export

### Expected Output

```
Using configuration: quick-demo
✓ Server running at http://localhost:8000/api/v1
✓ Model 'Qwen3-Next-80B-A3B-Instruct-GGUF' available

Benchmark Results:
Input Length 256: TTFT=15.932s, TPS=2.91
Input Length 512: TTFT=1.627s, TPS=26.06
...

Results saved to: moe-validation-cache/moe_validation_results.csv
```

## Step 5: View Results (1 minute)

### Check Generated Files

```powershell
# View CSV results
type moe-validation-cache\moe_validation_results.csv

# View benchmark details
type moe-validation-cache\benchmark_results.json
```

**Sample CSV Output**:
```csv
model,server,config,ttft_seconds,tps,memory_gb,mmlu_score,gsm8k_score,llm_judgement,llm_judgement_reason
Qwen3-Next-80B-A3B-Instruct-GGUF,http://localhost:8000/api/v1,quick-demo,5.302,20.807,N/A (server-side),See lm_eval output above,See lm_eval output above,5,Excellent explanation...
```

## Troubleshooting

### Server Connection Issues
**Error**: `ConnectionError: Cannot connect to Lemonade Server`
- **Solution**: Ensure server is running on port 8000
- **Check**: `netstat -ano | findstr 8000`

### Model Not Available
**Error**: `Model 'Qwen3-Next-80B-A3B-Instruct-GGUF' not found`
- **Solution**: Check available models: `curl http://localhost:8000/api/v1/models`
- **Alternative**: Use a different model name from the list

### Import Errors
**Error**: `ModuleNotFoundError: No module named 'openai'`
- **Solution**: `pip install openai`

### Memory Issues
**Error**: Out of memory during benchmark
- **Solution**: Reduce `iterations` in config or use `CONFIG = "quick-demo"`

## Next Steps

- **Full Validation**: Change `CONFIG = "full"` for comprehensive testing
- **Accuracy Tests**: Enable lm_eval cells for MMLU/GSM8k evaluation
- **Custom Models**: Modify `MODEL_NAME` to test other MoE models
- **CI Integration**: Use `scripts/ci/smoke_test_moe_server.py` for automated testing

---

*This quickstart gets you validating MoE models in minutes. For detailed documentation, see the main notebook and feature specification.*