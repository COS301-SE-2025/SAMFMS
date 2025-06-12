@echo off
REM Quick log viewer for SAMFMS
REM Usage: logs.bat [service] [options]

if "%1"=="help" goto :help
if "%1"=="--help" goto :help
if "%1"=="-h" goto :help

if "%1"=="clean" (
    powershell -ExecutionPolicy Bypass -File filter-logs.ps1 -Clean -Follow
    goto :end
)

if "%1"=="errors" (
    powershell -ExecutionPolicy Bypass -File filter-logs.ps1 -Errors
    goto :end
)

if "%1"=="summary" (
    powershell -ExecutionPolicy Bypass -File filter-logs.ps1 -Summary
    goto :end
)

if "%1"=="" (
    powershell -ExecutionPolicy Bypass -File filter-logs.ps1 -Clean -Tail 30
    goto :end
)

REM Service-specific logs
powershell -ExecutionPolicy Bypass -File filter-logs.ps1 -Service %1 -Tail 50

goto :end

:help
echo SAMFMS Log Viewer
echo.
echo Usage:
echo   logs.bat              - Show recent clean logs
echo   logs.bat clean        - Follow clean logs (no MongoDB noise)
echo   logs.bat errors       - Show only errors
echo   logs.bat summary      - Show service status
echo   logs.bat [service]    - Show specific service logs
echo.
echo Examples:
echo   logs.bat gps_service
echo   logs.bat mongodb_core
echo   logs.bat clean

:end
