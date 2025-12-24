# Test Data for MoE Validation

This directory contains sample datasets for MMLU and GSM8k accuracy testing.

## Directory Structure

```
test_data/
├── mmlu/          # MMLU test data (multiple choice questions)
├── gsm8k/         # GSM8k test data (math problems)
└── README.md      # This file
```

## MMLU (Massive Multitask Language Understanding)

The `lm-eval` library automatically downloads MMLU datasets when running tests. No manual data setup is required.

**Subjects tested:**
- mmlu_abstract_algebra
- mmlu_anatomy
- mmlu_astronomy
- (Additional subjects can be added in the notebook)

**Data source:** https://github.com/hendrycks/test

**Format:** Multiple choice questions with 4 options (A, B, C, D)

## GSM8k (Grade School Math)

The `lm-eval` library automatically downloads GSM8k datasets when running tests. No manual data setup is required.

**Data source:** https://github.com/openai/grade-school-math

**Format:** Math word problems with step-by-step solutions

## Custom Test Data (Optional)

If you want to add custom test samples for quick validation:

### MMLU Custom Samples
Create `mmlu/custom_samples.json`:
```json
[
  {
    "question": "What is 2 + 2?",
    "choices": ["3", "4", "5", "6"],
    "answer": 1
  }
]
```

### GSM8k Custom Samples
Create `gsm8k/custom_samples.json`:
```json
[
  {
    "question": "John has 5 apples. He gives 2 to Mary. How many does he have left?",
    "answer": "3"
  }
]
```

## Cache Directory

Test data is cached locally by `lm-eval` in:
- Linux/macOS: `~/.cache/huggingface/datasets/`
- Windows: `%USERPROFILE%\.cache\huggingface\datasets\`

## Configuration

Test data paths can be configured in the notebook or test scripts:

```python
TEST_DATA_DIR = Path("tests/moe_validation/test_data")
MMLU_DATA = TEST_DATA_DIR / "mmlu"
GSM8K_DATA = TEST_DATA_DIR / "gsm8k"
```

## References

- [LM Evaluation Harness Documentation](https://github.com/EleutherAI/lm-evaluation-harness/tree/main/docs)
- [MMLU Paper](https://arxiv.org/abs/2009.03300)
- [GSM8K Paper](https://arxiv.org/abs/2110.14168)
