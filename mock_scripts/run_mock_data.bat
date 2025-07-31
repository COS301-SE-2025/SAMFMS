@echo off
REM SAMFMS Mock Data Generation Script for Windows
REM Quick setup and execution

setlocal enabledelayedexpansion

echo 🚀 SAMFMS Mock Data Generator
echo ==============================
echo.
echo 🔐 Note: You will be prompted for your SAMFMS password
echo    Email: mvanheerdentuks@gmail.com
echo    (Password input will be hidden for security)
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is required but not installed.
    echo Please install Python 3.8 or later from https://python.org
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "config.py" (
    echo ❌ Please run this script from the mock_scripts directory
    pause
    exit /b 1
)

REM Install dependencies if needed
echo 📦 Installing dependencies...
python -m pip install -q aiohttp

REM Check if services are running (Windows doesn't have curl by default, so we skip this)
echo 🔍 Note: Please ensure SAMFMS services are running:
echo    - Core service: http://localhost:21000
echo    - Maintenance service: http://localhost:21004

REM Parse command line arguments
set QUICK_MODE=false
set VERBOSE=false

:parse_args
if "%~1"=="--quick" (
    set QUICK_MODE=true
    shift
    goto parse_args
)
if "%~1"=="--verbose" (
    set VERBOSE=true
    shift
    goto parse_args
)
if "%~1"=="--help" (
    echo Usage: %0 [options]
    echo Options:
    echo   --quick    Run quick test with minimal data
    echo   --verbose  Enable verbose logging
    echo   --help     Show this help message
    pause
    exit /b 0
)
if not "%~1"=="" (
    shift
    goto parse_args
)

REM Run the mock data generation
echo 🎬 Starting mock data generation...

if "%QUICK_MODE%"=="true" (
    echo 🧪 Running in quick test mode...
    if "%VERBOSE%"=="true" (
        python create_all_mock_data.py --quick --verbose
    ) else (
        python create_all_mock_data.py --quick
    )
) else (
    echo 🏭 Running full data generation...
    if "%VERBOSE%"=="true" (
        python create_all_mock_data.py --verbose
    ) else (
        python create_all_mock_data.py
    )
)

if errorlevel 1 (
    echo ❌ Mock data generation failed!
    pause
    exit /b 1
)

echo ✅ Mock data generation completed!
echo.
echo 💡 Next steps:
echo    1. Check the SAMFMS web interface
echo    2. Verify data via API endpoints
echo    3. Review service logs for any issues

pause
