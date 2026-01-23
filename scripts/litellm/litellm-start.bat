@echo off
REM LiteLLM Startup Wrapper with UTF-8 Encoding Fix
REM This wrapper fixes "UnicodeEncodeError" on Windows by setting PYTHONIOENCODING=utf-8

setlocal enabledelayedexpansion

REM Set UTF-8 encoding
set PYTHONIOENCODING=utf-8

REM Set Master Key if not already set
if not defined LITELLM_MASTER_KEY (
    set LITELLM_MASTER_KEY=test123
)

REM Get the script directory
set SCRIPT_DIR=%~dp0

REM Start LiteLLM with config from script directory
litellm --config "%SCRIPT_DIR%litellm-config.yaml" --port 4014

endlocal
