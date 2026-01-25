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

REM Load DATABASE_URL from .env if present, otherwise default to local sqlite file
if exist "%SCRIPT_DIR%.env" (
    for /f "usebackq tokens=1* delims==" %%A in ("%SCRIPT_DIR%.env") do (
        if /i "%%A"=="DATABASE_URL" set "DATABASE_URL=%%B"
    )
)
if not defined DATABASE_URL (
    set DATABASE_URL=sqlite:///C:/Users/tomwo/git/lemonade/scripts/litellm/litellm.db
)

REM Ensure sqlite DB file exists (create empty DB via Python if necessary)
if not exist "%SCRIPT_DIR%\litellm.db" (
    %~dp0\..\..\..\..\python -c "import sqlite3, os; p=r'%SCRIPT_DIR%litellm.db'; os.makedirs(os.path.dirname(p), exist_ok=True); sqlite3.connect(p).close()" 2>nul || (
        python -c "import sqlite3, os; p=r'%SCRIPT_DIR%litellm.db'; os.makedirs(os.path.dirname(p), exist_ok=True); sqlite3.connect(p).close()"
    )
)

REM Export DATABASE_URL for the process
set DATABASE_URL=%DATABASE_URL%

REM Start LiteLLM with config from script directory
litellm --config "%SCRIPT_DIR%litellm-config.yaml" --port 4014

endlocal
