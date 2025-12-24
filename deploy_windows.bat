@echo off
REM AMD AI Max+ 395 Quick Deployment Batch Script
REM For users with existing Lemonade Server installation

echo AMD AI Max+ 395 ROCm Deployment Script
echo ======================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running as Administrator - OK
) else (
    echo ERROR: Please run as Administrator
    pause
    exit /b 1
)

echo.
echo Step 1: Setting up Python environment...
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Python not found. Please install Python 3.10-3.13 first.
    pause
    exit /b 1
)

echo Python found. Installing dependencies...
pip install -r amd_max395_requirements.txt

if %errorLevel% neq 0 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)

echo.
echo Step 2: Running deployment script...
echo.

REM Run PowerShell deployment script
powershell.exe -ExecutionPolicy Bypass -File "deploy_amd_max395.ps1" -SkipLemonadeServer -EnableVerbose

if %errorLevel% neq 0 (
    echo ERROR: Deployment script failed
    pause
    exit /b 1
)

echo.
echo Step 3: Running validation...
echo.

REM Run validation
python deployment_validation.py --verbose

if %errorLevel% neq 0 (
    echo WARNING: Validation found issues. Check logs for details.
)

echo.
echo Step 4: Running test suite...
echo.

REM Change to test directory and run tests
cd tests\rocm_max395
python -m pytest --tb=short -v --maxfail=5

if %errorLevel% neq 0 (
    echo WARNING: Some tests failed. Check test output for details.
)

echo.
echo Step 5: Starting monitoring...
echo.

REM Start monitoring in background
start "AMD Max+ 395 Monitor" cmd /c "python ..\..\production_monitor.py --daemon --interval 60"

echo.
echo ======================================
echo Deployment completed!
echo.
echo Next steps:
echo 1. Check Lemonade Server configuration
echo 2. Load models in Lemonade Server
echo 3. Run performance benchmarks
echo 4. Monitor system health
echo.
echo Press any key to exit...
pause >nul