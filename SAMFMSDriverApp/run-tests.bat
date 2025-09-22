@echo off
echo =====================================
echo   SAMFMS Algorithm Validation Tests
echo =====================================
echo.
echo Starting validation tests...
echo.

cd /d "%~dp0"
node runAlgorithmTests.js

echo.
echo =====================================
echo Tests completed! Check test-results folder for detailed reports.
echo =====================================
pause