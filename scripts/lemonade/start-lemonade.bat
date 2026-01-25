@echo off
REM -----------------------------------------------------------------
REM START-LEMONADE.bat
REM Starts Lemonade Server with quality configuration and loads 4 models
REM Location: scripts\lemonade\start-lemonade.bat
REM -----------------------------------------------------------------
setlocal enabledelayedexpansion

cd /d "%~dp0..\.."
echo Current directory: %CD%
echo.
echo Starting Lemonade (delegating to PowerShell script)...
echo.

REM Start PowerShell script
powershell -NoProfile -ExecutionPolicy Bypass -Command "& '.\scripts\lemonade\start-lemonade.ps1'"

if errorlevel 1 (
    echo.
    echo [ERROR] Lemonade Server startup failed. Check the output above.
    pause
    exit /b 1
)

echo.
pause
