# SAMFMS Test Runner (PowerShell) - Run tests for all services from root
param(
    [string]$Service = "all",
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
    Write-Host "🧪 SAMFMS Test Suite Runner" -ForegroundColor Cyan
    Write-Host "============================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\run-tests.ps1 [OPTIONS]"
    Write-Host ""
    Write-Host "Parameters:"
    Write-Host "  -Service SERVICE     Run tests for specific service (security, core, all)"
    Write-Host "  -Unit               Run only unit tests"
    Write-Host "  -Integration        Run only integration tests"
    Write-Host "  -Coverage           Generate coverage reports"
    Write-Host "  -Verbose            Verbose output"
    Write-Host "  -Help               Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\run-tests.ps1                          # Run all tests for all services"
    Write-Host "  .\run-tests.ps1 -Service security        # Run all security tests"
    Write-Host "  .\run-tests.ps1 -Service security -Unit  # Run security unit tests only"
    Write-Host "  .\run-tests.ps1 -Coverage                # Run all tests with coverage"
    Write-Host ""
    exit 0
}

Write-Host ""
Write-Host "🧪 SAMFMS Test Suite Runner" -ForegroundColor Cyan
Write-Host "============================" -ForegroundColor Cyan
Write-Host ""

Write-Status "Running tests for: $Service"
if ($Unit) { Write-Status "Test type: unit" }
elseif ($Integration) { Write-Status "Test type: integration" }
else { Write-Status "Test type: all" }

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

# Clean up any existing test containers
Write-Status "Cleaning up existing test containers..."
& $dockerComposeCmd.Split() -f docker-compose.test.yml down --volumes --remove-orphans *>$null

function Run-SecurityTests {
    Write-Status "Running Security Service tests..."
    Push-Location "Sblocks\security"
    
    if (Test-Path "run-tests.ps1") {
        $args = @()
        if ($Unit) { $args += "-Unit" }
        if ($Integration) { $args += "-Integration" }
        if ($Coverage) { $args += "-Coverage" }
        if ($Verbose) { $args += "-Verbose" }
        
        & ".\run-tests.ps1" @args
        $result = $LASTEXITCODE
    } else {
        Write-Error "Security test script not found"
        $result = 1
    }
    
    Pop-Location
    return $result
}

function Run-CoreTests {
    Write-Status "Running Core Service tests..."
    Write-Status "Building and running core tests..."
    
    & $dockerComposeCmd.Split() -f docker-compose.test.yml build mcore
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to build core test environment"
        return 1
    }
    
    & $dockerComposeCmd.Split() -f docker-compose.test.yml up --abort-on-container-exit mcore
    return $LASTEXITCODE
}

function Run-AllTests {
    Write-Status "Running tests for all services..."
    $overallResult = 0
    
    # Run security tests
    Write-Host ""
    Write-Status "=== SECURITY SERVICE TESTS ===" 
    $securityResult = Run-SecurityTests
    if ($securityResult -ne 0) {
        Write-Error "Security tests failed"
        $overallResult = 1
    }
    
    # Run core tests
    Write-Host ""
    Write-Status "=== CORE SERVICE TESTS ==="
    $coreResult = Run-CoreTests
    if ($coreResult -ne 0) {
        Write-Error "Core tests failed"
        $overallResult = 1
    }
    
    Write-Host ""
    if ($overallResult -eq 0) {
        Write-Success "All service tests passed! ✅"
    } else {
        Write-Error "Some service tests failed! ❌"
    }
    
    return $overallResult
}

# Run tests based on service selection
$testResult = 0
switch ($Service.ToLower()) {
    "security" {
        $testResult = Run-SecurityTests
    }
    "core" {
        $testResult = Run-CoreTests
    }
    "all" {
        $testResult = Run-AllTests
    }
    default {
        Write-Error "Unknown service: $Service"
        Write-Host "Available services: security, core, all"
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Cleanup
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
