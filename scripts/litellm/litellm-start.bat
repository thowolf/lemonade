@echo off
REM LiteLLM Startup Wrapper with UTF-8 Encoding Fix
REM This wrapper fixes "UnicodeEncodeError" on Windows by setting PYTHONIOENCODING=utf-8

setlocal enabledelayedexpansion

REM Get the script directory
set SCRIPT_DIR=%~dp0

REM Change to script directory to load .env file
cd /d "%SCRIPT_DIR%"

REM Set UTF-8 encoding
set PYTHONIOENCODING=utf-8

REM Set Master Key for UI Login
REM Format: UI_USERNAME=admin, UI_PASSWORD=<this_key>
if not defined LITELLM_MASTER_KEY (
    set LITELLM_MASTER_KEY=test123
)

REM Also set UI credentials explicitly
if not defined UI_USERNAME (
    set UI_USERNAME=admin
)

if not defined UI_PASSWORD (
    set UI_PASSWORD=%LITELLM_MASTER_KEY%
)

REM Start LiteLLM with config from script directory
litellm --config "%SCRIPT_DIR%litellm-config.yaml" --port 4014

endlocal
