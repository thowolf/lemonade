@echo off
REM -----------------------------------------------------------------
REM START-LITELLM.bat
REM Starts LiteLLM Proxy Server for model routing and management
REM Location: scripts\litellm\start-litellm.bat
REM -----------------------------------------------------------------
setlocal enabledelayedexpansion

cd /d "%~dp0..\.."
echo Current directory: %CD%
echo.
echo ====================================================
echo   LITELLM PROXY SERVER STARTUP
echo ====================================================
echo.

REM Start PowerShell script
powershell -NoProfile -ExecutionPolicy Bypass -Command "& '.\scripts\litellm\start-litellm.ps1'"

if errorlevel 1 (
    echo.
    echo [ERROR] LiteLLM Server startup failed. Check the output above.
    pause
    exit /b 1
)

echo.
pause
