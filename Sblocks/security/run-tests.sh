#!/bin/bash

# Security Service Test Runner
echo "🧪 Running Security Service Tests"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose >/dev/null 2>&1; then
    print_error "docker-compose is not installed. Please install it and try again."
    exit 1
fi

# Clean up any existing test containers
print_status "Cleaning up existing test containers..."
docker-compose -f docker-compose.test.yml down -v --remove-orphans

# Create test reports directory
mkdir -p test-reports

# Run tests
print_status "Building test environment..."
docker-compose -f docker-compose.test.yml build

print_status "Starting test dependencies..."
docker-compose -f docker-compose.test.yml up -d test-mongo test-redis test-rabbitmq

print_status "Waiting for dependencies to be ready..."
sleep 15

print_status "Running tests..."
if docker-compose -f docker-compose.test.yml run --rm security-test; then
    print_success "All tests passed! 🎉"
    
    # Show coverage summary if available
    if [ -f "test-reports/coverage.xml" ]; then
        print_status "Test coverage report generated at: test-reports/htmlcov/index.html"
    fi
    
    EXIT_CODE=0
else
    print_error "Some tests failed! ❌"
    EXIT_CODE=1
fi

# Cleanup
print_status "Cleaning up test environment..."
docker-compose -f docker-compose.test.yml down -v

if [ $EXIT_CODE -eq 0 ]; then
    print_success "Test run completed successfully!"
    echo ""
    echo "📊 Test Reports:"
    echo "   - Coverage Report: test-reports/htmlcov/index.html"
    echo "   - JUnit XML: test-reports/junit.xml"
    echo "   - Coverage XML: test-reports/coverage.xml"
else
    print_error "Test run failed!"
fi

exit $EXIT_CODE
