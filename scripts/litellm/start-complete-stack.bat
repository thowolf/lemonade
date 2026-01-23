@echo off
REM -----------------------------------------------------------------
REM START-COMPLETE-STACK.bat
REM Starts complete Lemonade AI Infrastructure
REM Includes: Lemonade Server, LiteLLM Proxy, OpenedAI Speech (RoCm)
REM Location: scripts\litellm\start-complete-stack.bat
REM -----------------------------------------------------------------
setlocal enabledelayedexpansion

cd /d "%~dp0..\.."
echo Current directory: %CD%
echo.
echo =====================================================
echo   COMPLETE LEMONADE AI INFRASTRUCTURE STARTUP
echo =====================================================
echo.

REM Check if we should skip Lemonade Server
set "SKIP_LEMONADE=0"
if /i "%1"=="docker-only" (
    set "SKIP_LEMONADE=1"
    echo Mode: Docker Services Only (skipping Lemonade Server)
) else (
    echo Mode: Full Stack (Lemonade + Docker + LiteLLM)
)
echo.

REM STEP 1: Start Lemonade Server (unless --docker-only)
if %SKIP_LEMONADE%==0 (
    echo [1/3] Starting Lemonade Server with models...
    echo.
    call .\scripts\lemonade\start-lemonade.bat
    if errorlevel 1 (
        echo.
        echo [ERROR] Lemonade Server startup failed.
        pause
        exit /b 1
    )
)

REM STEP 2: Start Docker Services (LiteLLM + OpenedAI Speech)
echo.
echo [2/3] Starting Docker containers...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -Command "& '.\scripts\litellm\manage-docker-services.ps1' -Action start -Service all"
if errorlevel 1 (
    echo.
    echo [ERROR] Docker startup failed.
    pause
    exit /b 1
)

REM STEP 3: Display status
echo.
echo [3/3] Checking service status...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -Command "& '.\scripts\litellm\manage-docker-services.ps1' -Action status"

echo.
echo =====================================================
echo   LEMONADE AI INFRASTRUCTURE READY
echo =====================================================
echo.
echo SERVICES RUNNING:
echo   - Lemonade Server: http://localhost:8000 (port 8000)
echo   - LiteLLM Proxy: http://localhost:4014 (port 4014)
echo   - OpenedAI Speech: http://localhost:8888 (port 8888)
echo.
echo NEXTCLOUD AI INTEGRATION:
echo   Configure at: http://localhost:4014
echo   API Key: sk-1234567890abcdefghijklmnopqrstuv
echo.
echo AVAILABLE MODELS:
echo   - llm-text-gen: Qwen3-Next-80B (powerful reasoning)
echo   - llm-code-gen: Qwen3-Coder-30B (code generation)
echo   - llm-text-fast: Gemma-3-4b (quick responses)
echo   - llm-instruct: Phi-4-mini (instruction following)
echo   - audio-transcription: Whisper (speech-to-text)
echo   - tts-openedai: OpenedAI Speech (text-to-speech with RoCm)
echo.
echo NEXT STEPS:
echo   1. Verify services with: .\scripts\litellm\manage-docker-services.ps1 -Action status
echo   2. Test API: curl http://localhost:4014/v1/models
echo   3. Configure Nextcloud AI app with proxy URL
echo.
pause
exit /b 0
