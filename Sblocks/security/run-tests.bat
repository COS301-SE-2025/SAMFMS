@echo off
REM Security Service Test Runner for Windows
echo.
echo 🧪 Running Security Service Tests
echo ==================================
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

REM Check if docker-compose exists
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] docker-compose not found, trying docker compose...
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

REM Parse command line arguments
set TEST_TYPE=all
set EXTRA_ARGS=

:parse_args
if "%1"=="" goto end_parse
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
    set EXTRA_ARGS=%EXTRA_ARGS% --cov=. --cov-report=html:htmlcov
    shift
    goto parse_args
)
if "%1"=="--verbose" (
    set EXTRA_ARGS=%EXTRA_ARGS% -v
    shift
    goto parse_args
)
if "%1"=="--help" (
    echo.
    echo Usage: run-tests.bat [OPTIONS]
    echo.
    echo Options:
    echo   --unit         Run only unit tests
    echo   --integration  Run only integration tests
    echo   --coverage     Generate coverage report
    echo   --verbose      Verbose output
    echo   --help         Show this help message
    echo.
    pause
    exit /b 0
)
set EXTRA_ARGS=%EXTRA_ARGS% %1
shift
goto parse_args

:end_parse

echo [INFO] Cleaning up any existing test containers...
%DOCKER_COMPOSE_CMD% -f docker-compose.test.yml down --volumes --remove-orphans >nul 2>&1

echo [INFO] Building test environment...
%DOCKER_COMPOSE_CMD% -f docker-compose.test.yml build
if %errorlevel% neq 0 (
    echo [ERROR] Failed to build test environment.
    pause
    exit /b 1
)

echo [INFO] Starting test dependencies...
%DOCKER_COMPOSE_CMD% -f docker-compose.test.yml up -d test-mongo test-redis test-rabbitmq
if %errorlevel% neq 0 (
    echo [ERROR] Failed to start test dependencies.
    %DOCKER_COMPOSE_CMD% -f docker-compose.test.yml logs
    pause
    exit /b 1
)

echo [INFO] Waiting for dependencies to be ready...
timeout /t 15 /nobreak >nul

REM Set test command based on type
if "%TEST_TYPE%"=="unit" (
    set TEST_CMD=python -m pytest tests/unit %EXTRA_ARGS%
) else if "%TEST_TYPE%"=="integration" (
    set TEST_CMD=python -m pytest tests/integration %EXTRA_ARGS%
) else (
    set TEST_CMD=python -m pytest %EXTRA_ARGS%
)

echo [INFO] Running %TEST_TYPE% tests...
echo [INFO] Command: %TEST_CMD%
echo.

%DOCKER_COMPOSE_CMD% -f docker-compose.test.yml run --rm security-test %TEST_CMD%
set TEST_RESULT=%errorlevel%

echo.
if %TEST_RESULT% equ 0 (
    echo [SUCCESS] All tests passed! ✅
) else (
    echo [ERROR] Some tests failed! ❌
    echo [INFO] Check the output above for details.
)

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
