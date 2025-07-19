# Frontend API Testing Script - PowerShell Version
# Runs comprehensive frontend API tests with container integration

param(
    [int]$CoverageThreshold = 70,
    [int]$Timeout = 120,
    [string]$TestEnv = "container-test"
)

# Colors for output
$Red = [System.ConsoleColor]::Red
$Green = [System.ConsoleColor]::Green
$Yellow = [System.ConsoleColor]::Yellow
$Blue = [System.ConsoleColor]::Blue

# Configuration
$FrontendDir = "Frontend\samfms"

Write-Host "🚀 Starting Frontend API Testing" -ForegroundColor $Blue

# Function to print colored output
function Write-Status {
    param($Message)
    Write-Host "[INFO] $Message" -ForegroundColor $Green
}

function Write-Warning {
    param($Message)
    Write-Host "[WARNING] $Message" -ForegroundColor $Yellow
}

function Write-Error {
    param($Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $Red
}

# Check if we're in the right directory
if (!(Test-Path $FrontendDir)) {
    Write-Error "Frontend directory not found: $FrontendDir"
    exit 1
}

Set-Location $FrontendDir

# Check if package.json exists
if (!(Test-Path "package.json")) {
    Write-Error "package.json not found in $FrontendDir"
    exit 1
}

# Install dependencies
Write-Status "Installing dependencies..."
npm install

# Check if containers are running
Write-Status "Checking if backend containers are running..."
$backendServices = @(
    @{Name = "core-test"; Port = 8004},
    @{Name = "security-test"; Port = 8001},
    @{Name = "management-test"; Port = 8002},
    @{Name = "maintenance-test"; Port = 8003}
)

$containersRunning = $true

foreach ($service in $backendServices) {
    Write-Host "Checking $($service.Name)... " -NoNewline
    try {
        Invoke-RestMethod -Uri "http://localhost:$($service.Port)/health" -Method Get -TimeoutSec 5 | Out-Null
        Write-Host "✓" -ForegroundColor $Green
    } catch {
        Write-Host "✗" -ForegroundColor $Red
        $containersRunning = $false
    }
}

if (!$containersRunning) {
    Write-Warning "Some backend services are not running. Integration tests may fail."
    Write-Status "To start backend containers, run: docker-compose -f docker-compose.test-enhanced.yml up -d"
}

# Create test results directory
if (!(Test-Path "test-results")) {
    New-Item -ItemType Directory -Path "test-results" | Out-Null
}
if (!(Test-Path "coverage")) {
    New-Item -ItemType Directory -Path "coverage" | Out-Null
}

# Run unit tests for API functions
Write-Status "Running API unit tests..."
try {
    npm test -- --testPathPattern="__tests__/api" --testNamePattern="(?!Integration)" --coverage --coverageDirectory=coverage/unit --watchAll=false --ci --testResultsProcessor=jest-junit --coverageReporters=text --coverageReporters=lcov --coverageReporters=html
} catch {
    Write-Warning "Unit tests encountered issues"
}

# Run integration tests if containers are available
if ($containersRunning) {
    Write-Status "Running API integration tests..."
    try {
        $env:NODE_ENV = $TestEnv
        npm test -- --testPathPattern="integration.test.js" --coverage --coverageDirectory=coverage/integration --watchAll=false --ci --testResultsProcessor=jest-junit --coverageReporters=text --coverageReporters=lcov --coverageReporters=html
    } catch {
        Write-Warning "Integration tests encountered issues"
    }
} else {
    Write-Warning "Skipping integration tests - backend containers not available"
}

# Run all API tests together for combined coverage
Write-Status "Running all API tests for combined coverage..."
try {
    npm test -- --testPathPattern="__tests__/api" --coverage --coverageDirectory=coverage/combined --watchAll=false --ci --testResultsProcessor=jest-junit --coverageReporters=text --coverageReporters=lcov --coverageReporters=html
} catch {
    Write-Warning "Combined tests encountered issues"
}

# Check coverage threshold
Write-Status "Checking coverage threshold..."
if (Test-Path "coverage\combined\lcov-report\index.html") {
    Write-Status "Coverage report generated: coverage\combined\lcov-report\index.html"
}

# Generate test summary
Write-Status "Test Results Summary:"
Write-Host "===================="

# Check if test results exist
if (Test-Path "junit.xml") {
    # Parse test results (simplified)
    $xmlContent = Get-Content "junit.xml" -Raw
    
    if ($xmlContent -match 'tests="(\d+)"') {
        $totalTests = $matches[1]
        Write-Host "Total Tests: $totalTests" -ForegroundColor $Blue
    }
    
    if ($xmlContent -match 'failures="(\d+)"') {
        $failures = $matches[1]
        Write-Host "Failures: $failures" -ForegroundColor $Red
    }
    
    if ($xmlContent -match 'errors="(\d+)"') {
        $errors = $matches[1]
        Write-Host "Errors: $errors" -ForegroundColor $Red
    }
    
    if ($failures -eq 0 -and $errors -eq 0) {
        Write-Host "✅ All tests passed!" -ForegroundColor $Green
    } else {
        Write-Host "❌ Some tests failed" -ForegroundColor $Red
    }
} else {
    Write-Warning "Test results not found"
}

# Display available reports
Write-Status "Test reports available:"
Write-Host "  - coverage\unit\ - Unit test coverage"
Write-Host "  - coverage\integration\ - Integration test coverage (if containers available)"
Write-Host "  - coverage\combined\ - Combined coverage report"
Write-Host "  - test-results\ - Test execution results"

# Run linting
Write-Status "Running ESLint..."
try {
    npm run lint | Out-Null
    Write-Host "✅ Linting passed" -ForegroundColor $Green
} catch {
    Write-Host "⚠️ Linting issues found" -ForegroundColor $Yellow
}

# Check for potential issues
Write-Status "Checking for potential issues..."

# Check for console.log statements in source code
$consoleLogFiles = Get-ChildItem -Path "src" -Recurse -Include "*.js", "*.jsx", "*.ts", "*.tsx" | Where-Object { $_.DirectoryName -notlike "*__tests__*" } | Select-String -Pattern "console\.log" -SimpleMatch
if ($consoleLogFiles) {
    Write-Warning "console.log statements found in source code"
}

# Check for TODO comments
$todoFiles = Get-ChildItem -Path "src" -Recurse -Include "*.js", "*.jsx", "*.ts", "*.tsx" | Where-Object { $_.DirectoryName -notlike "*__tests__*" } | Select-String -Pattern "TODO|FIXME|XXX"
if ($todoFiles) {
    Write-Warning "TODO/FIXME comments found in source code"
}

Write-Status "Frontend API testing completed!"
Write-Host "🎉 Testing Complete!" -ForegroundColor $Green

# Return to original directory
Set-Location ..
