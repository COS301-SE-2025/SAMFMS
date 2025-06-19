# Security Service Test Runner (PowerShell)
param(
    [switch]$Unit,
    [switch]$Integration,
    [switch]$Coverage,
    [switch]$Verbose,
    [switch]$Help
)

function Write-Status {
    param($Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param($Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param($Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param($Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Show help
if ($Help) {
    Write-Host ""
    Write-Host "🧪 Security Service Test Runner"
    Write-Host "================================"
    Write-Host ""
    Write-Host "Usage: .\run-tests.ps1 [OPTIONS]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Unit         Run only unit tests"
    Write-Host "  -Integration  Run only integration tests"
    Write-Host "  -Coverage     Generate coverage report"
    Write-Host "  -Verbose      Verbose output"
    Write-Host "  -Help         Show this help message"
    Write-Host ""
    exit 0
}

Write-Host ""
Write-Host "🧪 Running Security Service Tests" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
try {
    docker info *>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker not running"
    }
    Write-Status "Docker is running..."
} catch {
    Write-Error "Docker is not running or not installed."
    Write-Host "Please start Docker Desktop and try again."
    Read-Host "Press Enter to exit"
    exit 1
}

# Check for Docker Compose
$dockerComposeCmd = ""
try {
    docker-compose --version *>$null
    if ($LASTEXITCODE -eq 0) {
        $dockerComposeCmd = "docker-compose"
    }
} catch {
    # Try docker compose
    try {
        docker compose --version *>$null
        if ($LASTEXITCODE -eq 0) {
            $dockerComposeCmd = "docker compose"
        }
    } catch {
        Write-Error "Docker Compose is not installed or not in PATH."
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Status "Docker Compose is available..."

# Build test command
$testCmd = "python -m pytest"
$extraArgs = @()

if ($Unit) {
    $testCmd += " tests/unit"
    Write-Status "Running unit tests only..."
} elseif ($Integration) {
    $testCmd += " tests/integration"
    Write-Status "Running integration tests only..."
} else {
    Write-Status "Running all tests..."
}

if ($Coverage) {
    $extraArgs += "--cov=.", "--cov-report=html:htmlcov"
}

if ($Verbose) {
    $extraArgs += "-v"
}

if ($extraArgs.Count -gt 0) {
    $testCmd += " " + ($extraArgs -join " ")
}

Write-Status "Cleaning up any existing test containers..."
& $dockerComposeCmd.Split() -f docker-compose.test.yml down --volumes --remove-orphans *>$null

Write-Status "Building test environment..."
& $dockerComposeCmd.Split() -f docker-compose.test.yml build
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to build test environment."
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Status "Starting test dependencies..."
& $dockerComposeCmd.Split() -f docker-compose.test.yml up -d test-mongo test-redis test-rabbitmq
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to start test dependencies."
    & $dockerComposeCmd.Split() -f docker-compose.test.yml logs
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Status "Waiting for dependencies to be ready..."
Start-Sleep -Seconds 15

Write-Status "Running tests..."
Write-Status "Command: $testCmd"
Write-Host ""

& $dockerComposeCmd.Split() -f docker-compose.test.yml run --rm security-test $testCmd.Split()
$testResult = $LASTEXITCODE

Write-Host ""
if ($testResult -eq 0) {
    Write-Success "All tests passed! ✅"
} else {
    Write-Error "Some tests failed! ❌"
    Write-Status "Check the output above for details."
}

Write-Host ""
Write-Status "Cleaning up test containers..."
& $dockerComposeCmd.Split() -f docker-compose.test.yml down --volumes *>$null

if ($testResult -eq 0) {
    Write-Success "Test run completed successfully."
} else {
    Write-Error "Test run completed with failures."
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
exit $testResult
