@echo off
REM Lemonade Quality Config - Server + Models Launcher
REM Startet den Server mit max-loaded-models 4 1 1 1 und ladet die 4 Modelle

setlocal enabledelayedexpansion

echo.
echo ====================================================
echo   LEMONADE SERVER - QUALITY CONFIG
echo ====================================================
echo.

REM Check if lemonade-server is available
where lemonade-server >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: lemonade-server not found in PATH
    echo Please install Lemonade Server first
    pause
    exit /b 1
)

REM Stop any existing server
echo [1/3] Stopping any existing Lemonade instances...
lemonade-server stop >nul 2>&1
timeout /t 2 /nobreak >nul

REM Start server with correct config
echo [2/3] Starting Lemonade Server on port 8000...
echo       (with max-loaded-models 4 1 1 1)
echo.

start "Lemonade Server" /min lemonade-server serve ^
    --port 8000 ^
    --max-loaded-models 4 1 1 1 ^
    --log-level info ^
    --llamacpp-args "--flash-attn on"

timeout /t 10 /nobreak

REM Load all 4 models
echo.
echo [3/3] Loading all 4 Quality Config models...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0benchmarks\start_quality_multiport.ps1" -Load

echo.
echo ====================================================
echo QUALITY CONFIG - ALL 4 MODELS LOADED
echo ====================================================
echo.
echo Server: http://localhost:8000/api/v1
echo Models: Qwen3-Next-80B, Qwen3-Coder-30B, Gemma, Whisper
echo.
pause

