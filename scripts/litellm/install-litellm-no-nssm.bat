@echo off
REM -----------------------------------------------------------------
REM install-litellm-no-nssm.bat - Alternative: Use Windows SC.exe
REM For when NSSM download fails
REM -----------------------------------------------------------------
setlocal enabledelayedexpansion

cd /d "%~dp0..\.."
echo.
echo =====================================================
echo   LiteLLM Windows Service Installation (SC.exe)
echo =====================================================
echo.

REM Check if running as admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: This script requires Administrator privileges
    echo Please run "Command Prompt as Administrator"
    pause
    exit /b 1
)

echo [1/4] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found in PATH
    echo Please install Python 3.8+ or add to PATH
    pause
    exit /b 1
)
echo OK: Python found

echo.
echo [2/4] Installing LiteLLM package...
python -m pip install --upgrade litellm >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Failed to install LiteLLM
    pause
    exit /b 1
)
echo OK: LiteLLM installed

echo.
echo [3/4] Creating Windows Service (LiteLLM-Proxy)...

REM Get Python executable path
for /f "tokens=*" %%i in ('python -c "import sys; print(sys.executable)"') do set PYTHON_EXE=%%i

REM Get config path
set CONFIG_PATH=%CD%\scripts\litellm\litellm-config.yaml

REM Check if service exists
sc query LiteLLM-Proxy >nul 2>&1
if %errorlevel% equ 0 (
    echo Service already exists. Removing...
    sc delete LiteLLM-Proxy >nul 2>&1
    timeout /t 2 /nobreak
)

REM Create service with SC.exe
REM Note: SC.exe has limitations with complex paths, so we create a wrapper batch file
set SERVICE_WRAPPER=%CD%\scripts\litellm\litellm-service-wrapper.bat

echo Creating service wrapper...
(
    echo @echo off
    echo set PYTHONIOENCODING=utf-8
    echo set LITELLM_MASTER_KEY=sk-1234567890abcdefghijklmnopqrstuv
    echo "%PYTHON_EXE%" -m litellm.main --config "%CONFIG_PATH%" --port 4014
) > "%SERVICE_WRAPPER%"

REM Create service using SC.exe
sc create LiteLLM-Proxy binPath= "%SERVICE_WRAPPER%" DisplayName= "LiteLLM API Proxy (Lemonade)" start= auto >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Failed to create service
    pause
    exit /b 1
)
echo OK: Service created

echo.
echo [4/4] Starting LiteLLM service...
net start LiteLLM-Proxy >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Service creation may have succeeded but failed to start
    echo Try manually: net start LiteLLM-Proxy
) else (
    echo OK: Service started
)

echo.
echo =====================================================
echo   INSTALLATION COMPLETE
echo =====================================================
echo.
echo Service: LiteLLM-Proxy
echo Status: Running
echo Port: 4014
echo.
echo Management Commands:
echo   net start LiteLLM-Proxy      - Start service
echo   net stop LiteLLM-Proxy       - Stop service
echo   sc delete LiteLLM-Proxy      - Delete service
echo.
echo Master Key: sk-1234567890abcdefghijklmnopqrstuv (CHANGE THIS!)
echo Config: %CONFIG_PATH%
echo.
pause
exit /b 0
