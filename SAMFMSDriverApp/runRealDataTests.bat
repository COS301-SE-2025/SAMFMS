@echo off
echo.
echo ========================================
echo  Driver Behavior Algorithm Real Data Test
echo ========================================
echo.

cd /d "%~dp0"

if not exist datasets (
    echo ERROR: datasets folder not found!
    echo Please ensure the datasets folder exists in the parent directory.
    echo Expected path: %cd%\..\datasets
    pause
    exit /b 1
)

echo Running real data validation tests...
echo.

node runRealDataTests.js

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Test execution failed!
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo Test completed successfully!
echo Check the test-results folder for detailed output.
echo.
pause