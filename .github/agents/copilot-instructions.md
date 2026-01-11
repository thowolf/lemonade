> **Constitution:** Refer to `.specify/memory/constitution.md` for normative principles and mandatory project policies. If your change affects project principles, run `/speckit.constitution` and include a Sync Impact Report.

# lemonade Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-12-23

## Active Technologies
- C++ 17 (core server), Python 3.10-3.13 (API and tooling) (005-multi-llm-execution)
- Models stored in HuggingFace cache (`~/.cache/huggingface/hub`), FLM models in `~/Documents/flm/models`, user models JSON in `~/.lemonade/user_models.json` (005-multi-llm-execution)

- Python 3.10-3.13 (per Lemonade SDK compatibility), Windows 11 (build 22H2+) (001-max-395-rocm-test)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.10-3.13 (per Lemonade SDK compatibility), Windows 11 (build 22H2+): Follow standard conventions

## Recent Changes
- 005-multi-llm-execution: Added C++ 17 (core server), Python 3.10-3.13 (API and tooling)

- 001-max-395-rocm-test: Added Python 3.10-3.13 (per Lemonade SDK compatibility), Windows 11 (build 22H2+)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
