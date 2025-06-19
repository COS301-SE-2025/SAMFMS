@echo off
REM SAMFMS Test Runner - Run tests for all services from root
echo.
echo 🧪 SAMFMS Test Suite Runner
echo ===========================
echo.

setlocal enabledelayedexpansion

REM Parse command line arguments
set SERVICE=all
set TEST_TYPE=all
set EXTRA_ARGS=
set SHOW_HELP=false

:parse_args
if "%1"=="" goto end_parse
if "%1"=="--service" (
    set SERVICE=%2
    shift
    shift
    goto parse_args
)
if "%1"=="--unit" (
    set TEST_TYPE=unit
    shift
    goto parse_args
)
if "%1"=="--integration" (
    set TEST_TYPE=integration
    shift
    goto parse_args
)
if "%1"=="--coverage" (
    set EXTRA_ARGS=%EXTRA_ARGS% --coverage
    shift
    goto parse_args
)
if "%1"=="--verbose" (
    set EXTRA_ARGS=%EXTRA_ARGS% --verbose
    shift
    goto parse_args
)
if "%1"=="--help" (
    set SHOW_HELP=true
    shift
    goto parse_args
)
set EXTRA_ARGS=%EXTRA_ARGS% %1
shift
goto parse_args

:end_parse

REM Show help
if "%SHOW_HELP%"=="true" (
    echo Usage: run-tests.bat [OPTIONS]
    echo.
    echo Options:
    echo   --service SERVICE    Run tests for specific service ^(security, core, all^)
    echo   --unit              Run only unit tests
    echo   --integration       Run only integration tests
    echo   --coverage          Generate coverage reports
    echo   --verbose           Verbose output
    echo   --help              Show this help message
    echo.
    echo Examples:
    echo   run-tests.bat                          # Run all tests for all services
    echo   run-tests.bat --service security       # Run all security tests
    echo   run-tests.bat --service security --unit # Run security unit tests only
    echo   run-tests.bat --coverage               # Run all tests with coverage
    echo.
    pause
    exit /b 0
)

echo [INFO] Running tests for: %SERVICE%
echo [INFO] Test type: %TEST_TYPE%
if not "%EXTRA_ARGS%"=="" echo [INFO] Extra arguments: %EXTRA_ARGS%
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not running or not installed.
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo [INFO] Docker is running...

REM Check for Docker Compose
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    docker compose --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Docker Compose is not installed or not in PATH.
        pause
        exit /b 1
    )
    set DOCKER_COMPOSE_CMD=docker compose
) else (
    set DOCKER_COMPOSE_CMD=docker-compose
)

echo [INFO] Docker Compose is available...

REM Clean up any existing test containers
echo [INFO] Cleaning up existing test containers...
%DOCKER_COMPOSE_CMD% -f docker-compose.test.yml down --volumes --remove-orphans >nul 2>&1

REM Run tests based on service selection
if "%SERVICE%"=="security" (
    call :run_security_tests
) else if "%SERVICE%"=="core" (
    call :run_core_tests
) else if "%SERVICE%"=="all" (
    call :run_all_tests
) else (
    echo [ERROR] Unknown service: %SERVICE%
    echo Available services: security, core, all
    pause
    exit /b 1
)

goto :cleanup

:run_security_tests
echo [INFO] Running Security Service tests...
cd Sblocks\security
if exist run-tests.bat (
    call run-tests.bat %EXTRA_ARGS%
    set TEST_RESULT=!errorlevel!
) else (
    echo [ERROR] Security test script not found
    set TEST_RESULT=1
)
cd ..\..
exit /b %TEST_RESULT%

:run_core_tests
echo [INFO] Running Core Service tests...
echo [INFO] Building and running core tests...
%DOCKER_COMPOSE_CMD% -f docker-compose.test.yml build mcore
if %errorlevel% neq 0 (
    echo [ERROR] Failed to build core test environment
    exit /b 1
)
%DOCKER_COMPOSE_CMD% -f docker-compose.test.yml up --abort-on-container-exit mcore
set TEST_RESULT=%errorlevel%
exit /b %TEST_RESULT%

:run_all_tests
echo [INFO] Running tests for all services...
set OVERALL_RESULT=0

REM Run security tests
echo.
echo [INFO] === SECURITY SERVICE TESTS ===
call :run_security_tests
if !errorlevel! neq 0 (
    echo [ERROR] Security tests failed
    set OVERALL_RESULT=1
)

REM Run core tests
echo.
echo [INFO] === CORE SERVICE TESTS ===
call :run_core_tests
if !errorlevel! neq 0 (
    echo [ERROR] Core tests failed
    set OVERALL_RESULT=1
)

echo.
if %OVERALL_RESULT% equ 0 (
    echo [SUCCESS] All service tests passed! ✅
) else (
    echo [ERROR] Some service tests failed! ❌
)

exit /b %OVERALL_RESULT%

:cleanup
echo.
echo [INFO] Cleaning up test containers...
%DOCKER_COMPOSE_CMD% -f docker-compose.test.yml down --volumes >nul 2>&1

if %TEST_RESULT% equ 0 (
    echo [SUCCESS] Test run completed successfully.
) else (
    echo [ERROR] Test run completed with failures.
)

echo.
echo Press any key to exit...
pause >nul
exit /b %TEST_RESULT%
