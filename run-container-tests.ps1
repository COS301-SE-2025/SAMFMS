# SAMFMS Container-based Testing Script for Windows PowerShell
# This script runs comprehensive tests using Docker containers

param(
    [int]$Timeout = 300,
    [int]$CoverageThreshold = 80,
    [string]$ComposeFile = "docker-compose.test-enhanced.yml",
    [string]$ProjectName = "samfms-test"
)

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Blue"

function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor $Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor $Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $Red
}

function Cleanup {
    Write-Status "Cleaning up containers..."
    docker-compose -f $ComposeFile -p $ProjectName down -v --remove-orphans
    docker system prune -f
}

Write-Host "🚀 Starting SAMFMS Container-based Testing" -ForegroundColor $Blue

# Check if Docker is running
try {
    docker info | Out-Null
} catch {
    Write-Error "Docker is not running. Please start Docker and try again."
    exit 1
}

# Check if docker-compose is available
try {
    docker-compose --version | Out-Null
} catch {
    Write-Error "docker-compose is not installed. Please install it and try again."
    exit 1
}

Write-Status "Checking Docker Compose file..."
if (!(Test-Path $ComposeFile)) {
    Write-Error "Docker Compose file $ComposeFile not found."
    exit 1
}

# Setup cleanup on exit
trap { Cleanup }

try {
    # Build and start services
    Write-Status "Building and starting test containers..."
    docker-compose -f $ComposeFile -p $ProjectName build --no-cache

    Write-Status "Starting infrastructure services..."
    docker-compose -f $ComposeFile -p $ProjectName up -d mongodb-test rabbitmq-test redis-test

    Write-Status "Waiting for infrastructure services to be ready..."
    Start-Sleep -Seconds 30

    Write-Status "Starting application services..."
    docker-compose -f $ComposeFile -p $ProjectName up -d security-test management-test maintenance-test core-test

    Write-Status "Waiting for application services to be ready..."
    Start-Sleep -Seconds 60

    # Check service health
    Write-Status "Checking service health..."
    $services = @(
        @{Name="core-test"; Port=8004},
        @{Name="security-test"; Port=8001},
        @{Name="management-test"; Port=8002},
        @{Name="maintenance-test"; Port=8003}
    )

    foreach ($service in $services) {
        Write-Host "Checking $($service.Name) health... " -NoNewline
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:$($service.Port)/health" -TimeoutSec 5
            if ($response.StatusCode -eq 200) {
                Write-Host "✓" -ForegroundColor $Green
            } else {
                Write-Host "✗" -ForegroundColor $Red
                Write-Warning "$($service.Name) is not healthy, continuing anyway..."
            }
        } catch {
            Write-Host "✗" -ForegroundColor $Red
            Write-Warning "$($service.Name) is not healthy, continuing anyway..."
        }
    }

    # Create test results directories
    New-Item -ItemType Directory -Path "test-results" -Force | Out-Null
    New-Item -ItemType Directory -Path "coverage-reports" -Force | Out-Null

    # Run tests
    Write-Status "Running integration tests..."

    # Run container-based integration tests
    Write-Status "Running container integration tests..."
    docker-compose -f $ComposeFile -p $ProjectName run --rm test-runner `
        python -m pytest tests/integration/test_container_integration.py `
        -v --tb=short --junitxml=test-results/container-integration.xml `
        --cov=Core --cov=Sblocks `
        --cov-report=html:coverage-reports/container-integration `
        --cov-report=xml:coverage-reports/container-integration.xml `
        --cov-report=term-missing

    # Run security integration tests
    Write-Status "Running security integration tests..."
    docker-compose -f $ComposeFile -p $ProjectName run --rm test-runner `
        python -m pytest tests/integration/test_security_integration.py `
        -v --tb=short --junitxml=test-results/security-integration.xml `
        --cov=Sblocks/security `
        --cov-report=html:coverage-reports/security-integration `
        --cov-report=xml:coverage-reports/security-integration.xml `
        --cov-report=term-missing

    # Run core routes tests
    Write-Status "Running core routes tests..."
    docker-compose -f $ComposeFile -p $ProjectName run --rm test-runner `
        python -m pytest tests/integration/test_core_routes_final.py `
        -v --tb=short --junitxml=test-results/core-routes.xml `
        --cov=Core `
        --cov-report=html:coverage-reports/core-routes `
        --cov-report=xml:coverage-reports/core-routes.xml `
        --cov-report=term-missing

    # Run all unit tests
    Write-Status "Running unit tests..."
    docker-compose -f $ComposeFile -p $ProjectName run --rm test-runner `
        python -m pytest tests/unit/ `
        -v --tb=short --junitxml=test-results/unit-tests.xml `
        --cov=Core --cov=Sblocks `
        --cov-report=html:coverage-reports/unit-tests `
        --cov-report=xml:coverage-reports/unit-tests.xml `
        --cov-report=term-missing

    # Generate combined coverage report
    Write-Status "Generating combined coverage report..."
    docker-compose -f $ComposeFile -p $ProjectName run --rm test-runner `
        python -m pytest tests/ `
        -v --tb=short --junitxml=test-results/all-tests.xml `
        --cov=Core --cov=Sblocks `
        --cov-report=html:coverage-reports/combined `
        --cov-report=xml:coverage-reports/combined.xml `
        --cov-report=term-missing `
        --cov-fail-under=$CoverageThreshold

    # Copy reports from container to host
    Write-Status "Copying test reports..."
    docker-compose -f $ComposeFile -p $ProjectName run --rm test-runner `
        sh -c "cp -r test-results/* /app/test-results/ && cp -r coverage-reports/* /app/coverage-reports/"

    # Display results
    Write-Status "Test Results Summary:"
    Write-Host "===================="

    if (Test-Path "test-results/all-tests.xml") {
        # Parse test results (simplified)
        $testResults = Get-Content "test-results/all-tests.xml" -Raw
        
        if ($testResults -match 'tests="(\d+)"') {
            $totalTests = $matches[1]
            Write-Host "Total Tests: $totalTests" -ForegroundColor $Blue
        }
        
        if ($testResults -match 'failures="(\d+)"') {
            $failures = $matches[1]
            Write-Host "Failures: $failures" -ForegroundColor $Red
        }
        
        if ($testResults -match 'errors="(\d+)"') {
            $errors = $matches[1]
            Write-Host "Errors: $errors" -ForegroundColor $Red
        }
        
        if ($failures -eq 0 -and $errors -eq 0) {
            Write-Host "✅ All tests passed!" -ForegroundColor $Green
        } else {
            Write-Host "❌ Some tests failed" -ForegroundColor $Red
        }
    } else {
        Write-Warning "Test results XML not found"
    }

    # Display coverage information
    if (Test-Path "coverage-reports/combined.xml") {
        $coverageXml = Get-Content "coverage-reports/combined.xml" -Raw
        if ($coverageXml -match 'line-rate="([0-9.]+)"') {
            $coveragePercent = [math]::Round([double]$matches[1] * 100, 0)
            Write-Host "Coverage: $coveragePercent%" -ForegroundColor $Blue
            
            if ($coveragePercent -ge $CoverageThreshold) {
                Write-Host "✅ Coverage threshold met!" -ForegroundColor $Green
            } else {
                Write-Host "❌ Coverage below threshold ($CoverageThreshold%)" -ForegroundColor $Red
            }
        }
    }

    Write-Status "Test reports available in:"
    Write-Host "  - test-results/ (JUnit XML)"
    Write-Host "  - coverage-reports/ (HTML and XML)"

    # Service logs for debugging
    Write-Status "Collecting service logs..."
    New-Item -ItemType Directory -Path "logs" -Force | Out-Null
    docker-compose -f $ComposeFile -p $ProjectName logs core-test > logs/core-test.log 2>&1
    docker-compose -f $ComposeFile -p $ProjectName logs security-test > logs/security-test.log 2>&1
    docker-compose -f $ComposeFile -p $ProjectName logs management-test > logs/management-test.log 2>&1
    docker-compose -f $ComposeFile -p $ProjectName logs maintenance-test > logs/maintenance-test.log 2>&1

    Write-Status "Service logs available in logs/ directory"

    Write-Status "Container-based testing completed!"
    Write-Host "🎉 SAMFMS Testing Complete!" -ForegroundColor $Green

} catch {
    Write-Error "An error occurred during testing: $($_.Exception.Message)"
    exit 1
} finally {
    Cleanup
}
