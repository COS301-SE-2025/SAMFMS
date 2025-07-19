#!/bin/bash

# SAMFMS Container-based Testing Script
# This script runs comprehensive tests using Docker containers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.test-enhanced.yml"
PROJECT_NAME="samfms-test"
TIMEOUT=300
COVERAGE_THRESHOLD=80

echo -e "${BLUE}🚀 Starting SAMFMS Container-based Testing${NC}"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to cleanup containers
cleanup() {
    print_status "Cleaning up containers..."
    docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME down -v --remove-orphans
    docker system prune -f
}

# Trap cleanup on exit
trap cleanup EXIT

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose > /dev/null 2>&1; then
    print_error "docker-compose is not installed. Please install it and try again."
    exit 1
fi

print_status "Checking Docker Compose file..."
if [ ! -f "$COMPOSE_FILE" ]; then
    print_error "Docker Compose file $COMPOSE_FILE not found."
    exit 1
fi

# Build and start services
print_status "Building and starting test containers..."
docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME build --no-cache

print_status "Starting infrastructure services..."
docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME up -d mongodb-test rabbitmq-test redis-test

print_status "Waiting for infrastructure services to be ready..."
sleep 30

print_status "Starting application services..."
docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME up -d security-test management-test maintenance-test core-test

print_status "Waiting for application services to be ready..."
sleep 60

# Check service health
print_status "Checking service health..."
services=("core-test:8004" "security-test:8001" "management-test:8002" "maintenance-test:8003")
for service in "${services[@]}"; do
    service_name=$(echo $service | cut -d':' -f1)
    port=$(echo $service | cut -d':' -f2)
    
    echo -n "Checking $service_name health... "
    if curl -f -s "http://localhost:$port/health" > /dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        print_warning "$service_name is not healthy, continuing anyway..."
    fi
done

# Run tests
print_status "Running integration tests..."

# Create test results directory
mkdir -p test-results
mkdir -p coverage-reports

# Run container-based integration tests
print_status "Running container integration tests..."
docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME run --rm test-runner \
    python -m pytest tests/integration/test_container_integration.py \
    -v --tb=short --junitxml=test-results/container-integration.xml \
    --cov=Core --cov=Sblocks \
    --cov-report=html:coverage-reports/container-integration \
    --cov-report=xml:coverage-reports/container-integration.xml \
    --cov-report=term-missing || true

# Run security integration tests
print_status "Running security integration tests..."
docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME run --rm test-runner \
    python -m pytest tests/integration/test_security_integration.py \
    -v --tb=short --junitxml=test-results/security-integration.xml \
    --cov=Sblocks/security \
    --cov-report=html:coverage-reports/security-integration \
    --cov-report=xml:coverage-reports/security-integration.xml \
    --cov-report=term-missing || true

# Run core routes tests
print_status "Running core routes tests..."
docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME run --rm test-runner \
    python -m pytest tests/integration/test_core_routes_final.py \
    -v --tb=short --junitxml=test-results/core-routes.xml \
    --cov=Core \
    --cov-report=html:coverage-reports/core-routes \
    --cov-report=xml:coverage-reports/core-routes.xml \
    --cov-report=term-missing || true

# Run all unit tests
print_status "Running unit tests..."
docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME run --rm test-runner \
    python -m pytest tests/unit/ \
    -v --tb=short --junitxml=test-results/unit-tests.xml \
    --cov=Core --cov=Sblocks \
    --cov-report=html:coverage-reports/unit-tests \
    --cov-report=xml:coverage-reports/unit-tests.xml \
    --cov-report=term-missing || true

# Generate combined coverage report
print_status "Generating combined coverage report..."
docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME run --rm test-runner \
    python -m pytest tests/ \
    -v --tb=short --junitxml=test-results/all-tests.xml \
    --cov=Core --cov=Sblocks \
    --cov-report=html:coverage-reports/combined \
    --cov-report=xml:coverage-reports/combined.xml \
    --cov-report=term-missing \
    --cov-fail-under=$COVERAGE_THRESHOLD || true

# Copy reports from container to host
print_status "Copying test reports..."
docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME run --rm test-runner \
    sh -c "cp -r test-results/* /app/test-results/ && cp -r coverage-reports/* /app/coverage-reports/" || true

# Display results
print_status "Test Results Summary:"
echo "===================="

if [ -f "test-results/all-tests.xml" ]; then
    # Parse test results (simplified)
    total_tests=$(grep -o 'tests="[0-9]*"' test-results/all-tests.xml | grep -o '[0-9]*' | head -1)
    failures=$(grep -o 'failures="[0-9]*"' test-results/all-tests.xml | grep -o '[0-9]*' | head -1)
    errors=$(grep -o 'errors="[0-9]*"' test-results/all-tests.xml | grep -o '[0-9]*' | head -1)
    
    echo -e "Total Tests: ${BLUE}$total_tests${NC}"
    echo -e "Failures: ${RED}$failures${NC}"
    echo -e "Errors: ${RED}$errors${NC}"
    
    if [ "$failures" -eq 0 ] && [ "$errors" -eq 0 ]; then
        echo -e "${GREEN}✅ All tests passed!${NC}"
    else
        echo -e "${RED}❌ Some tests failed${NC}"
    fi
else
    print_warning "Test results XML not found"
fi

# Display coverage information
if [ -f "coverage-reports/combined.xml" ]; then
    coverage_percent=$(grep -o 'line-rate="[0-9.]*"' coverage-reports/combined.xml | grep -o '[0-9.]*' | head -1)
    if [ ! -z "$coverage_percent" ]; then
        coverage_percent=$(echo "$coverage_percent * 100" | bc -l | cut -d'.' -f1)
        echo -e "Coverage: ${BLUE}$coverage_percent%${NC}"
        
        if [ "$coverage_percent" -ge "$COVERAGE_THRESHOLD" ]; then
            echo -e "${GREEN}✅ Coverage threshold met!${NC}"
        else
            echo -e "${RED}❌ Coverage below threshold ($COVERAGE_THRESHOLD%)${NC}"
        fi
    fi
fi

print_status "Test reports available in:"
echo "  - test-results/ (JUnit XML)"
echo "  - coverage-reports/ (HTML and XML)"

# Service logs for debugging
print_status "Collecting service logs..."
mkdir -p logs
docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME logs core-test > logs/core-test.log 2>&1
docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME logs security-test > logs/security-test.log 2>&1
docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME logs management-test > logs/management-test.log 2>&1
docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME logs maintenance-test > logs/maintenance-test.log 2>&1

print_status "Service logs available in logs/ directory"

print_status "Container-based testing completed!"
echo -e "${GREEN}🎉 SAMFMS Testing Complete!${NC}"
