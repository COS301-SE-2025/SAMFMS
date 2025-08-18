@echo off
REM Frontend-Compatible Driver Creation Script for Windows
REM Creates drivers using exact same endpoint and structure as frontend

setlocal enabledelayedexpansion

echo 🎯 Frontend-Compatible Driver Creation
echo =====================================
echo.
echo This script creates drivers using:
echo • Exact same data structure as frontend AddDriverModal.jsx
echo • Same API endpoint (/management/drivers)
echo • Standard password: Password1! for all drivers
echo.
echo 🔐 Login required - Email: mvanheerdentuks@gmail.com
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is required but not installed.
    echo Please install Python 3.8 or later from https://python.org
    pause
    exit /b 1
)

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo 🐍 Activating Python virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo ⚠️  No virtual environment found. Installing dependencies globally...
)

REM Install required packages
echo 📦 Installing/updating required packages...
pip install -r requirements.txt >nul 2>&1

if errorlevel 1 (
    echo ❌ Failed to install required packages.
    echo Please check your Python environment.
    pause
    exit /b 1
)

REM Parse command line arguments
set "COUNT=30"
set "VERBOSE=false"

:parse_args
if "%~1"=="--count" (
    set "COUNT=%~2"
    shift
    shift
    goto parse_args
)
if "%~1"=="--verbose" (
    set "VERBOSE=true"
    shift
    goto parse_args
)
if "%~1"=="--help" (
    echo Usage: run_frontend_drivers.bat [options]
    echo.
    echo Options:
    echo   --count N   Number of drivers to create (default: 30)
    echo   --verbose   Enable verbose logging
    echo   --help      Show this help message
    pause
    exit /b 0
)
if not "%~1"=="" (
    shift
    goto parse_args
)

REM Run the frontend-compatible driver creation
echo 🚗 Creating %COUNT% frontend-compatible drivers...

if "%VERBOSE%"=="true" (
    python create_drivers_frontend.py --count %COUNT% --verbose
) else (
    python create_drivers_frontend.py --count %COUNT%
)

if errorlevel 1 (
    echo ❌ Driver creation failed!
    pause
    exit /b 1
)

echo.
echo ✅ Frontend-compatible driver creation completed!
echo.
echo 💡 What was created:
echo    • %COUNT% drivers using Management service endpoint
echo    • Same data structure as AddDriverModal.jsx frontend form
echo    • All drivers have password: Password1!
echo    • Compatible with ActiveTripsMap vehicle filtering
echo.
echo 🔍 Next steps:
echo    1. Check the Drivers page in SAMFMS web interface
echo    2. Test vehicle filtering on ActiveTripsMap
echo    3. Verify trip assignment functionality

pause
