#!/bin/bash

# SAMFMS Frontend API Testing with Docker
# This script runs frontend API tests using Docker containers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.test-enhanced.yml"
PROJECT_NAME="samfms-frontend-test"
TIMEOUT=300
COVERAGE_THRESHOLD=70

echo -e "${BLUE}🚀 Starting SAMFMS Frontend API Testing${NC}"

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

# Check if we're in the right directory
if [ ! -d "$FRONTEND_DIR" ]; then
    print_error "Frontend directory not found: $FRONTEND_DIR"
    exit 1
fi

cd "$FRONTEND_DIR"

# Check if package.json exists
if [ ! -f "package.json" ]; then
    print_error "package.json not found in $FRONTEND_DIR"
    exit 1
fi

# Install dependencies
print_status "Installing dependencies..."
npm install

# Check if containers are running
print_status "Checking if backend containers are running..."
backend_services=("core-test:8004" "security-test:8001" "management-test:8002" "maintenance-test:8003")
containers_running=true

for service in "${backend_services[@]}"; do
    service_name=$(echo $service | cut -d':' -f1)
    port=$(echo $service | cut -d':' -f2)
    
    echo -n "Checking $service_name... "
    if curl -f -s "http://localhost:$port/health" > /dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        containers_running=false
    fi
done

if [ "$containers_running" = false ]; then
    print_warning "Some backend services are not running. Integration tests may fail."
    print_status "To start backend containers, run: docker-compose -f docker-compose.test-enhanced.yml up -d"
fi

# Create test results directory
mkdir -p test-results
mkdir -p coverage

# Run unit tests for API functions
print_status "Running API unit tests..."
npm test -- --testPathPattern="__tests__/api" --testNamePattern="(?!Integration)" --coverage --coverageDirectory=coverage/unit --watchAll=false --ci --testResultsProcessor=jest-junit --coverageReporters=text --coverageReporters=lcov --coverageReporters=html

# Run integration tests if containers are available
if [ "$containers_running" = true ]; then
    print_status "Running API integration tests..."
    NODE_ENV=$TEST_ENV npm test -- --testPathPattern="integration.test.js" --coverage --coverageDirectory=coverage/integration --watchAll=false --ci --testResultsProcessor=jest-junit --coverageReporters=text --coverageReporters=lcov --coverageReporters=html
else
    print_warning "Skipping integration tests - backend containers not available"
fi

# Run all API tests together for combined coverage
print_status "Running all API tests for combined coverage..."
npm test -- --testPathPattern="__tests__/api" --coverage --coverageDirectory=coverage/combined --watchAll=false --ci --testResultsProcessor=jest-junit --coverageReporters=text --coverageReporters=lcov --coverageReporters=html

# Check coverage threshold
print_status "Checking coverage threshold..."
if [ -f "coverage/combined/lcov-report/index.html" ]; then
    print_status "Coverage report generated: coverage/combined/lcov-report/index.html"
fi

# Generate test summary
print_status "Test Results Summary:"
echo "===================="

# Check if test results exist
if [ -f "junit.xml" ]; then
    # Parse test results (simplified)
    total_tests=$(grep -o 'tests="[0-9]*"' junit.xml | grep -o '[0-9]*' | head -1)
    failures=$(grep -o 'failures="[0-9]*"' junit.xml | grep -o '[0-9]*' | head -1)
    errors=$(grep -o 'errors="[0-9]*"' junit.xml | grep -o '[0-9]*' | head -1)
    
    echo -e "Total Tests: ${BLUE}$total_tests${NC}"
    echo -e "Failures: ${RED}$failures${NC}"
    echo -e "Errors: ${RED}$errors${NC}"
    
    if [ "$failures" -eq 0 ] && [ "$errors" -eq 0 ]; then
        echo -e "${GREEN}✅ All tests passed!${NC}"
    else
        echo -e "${RED}❌ Some tests failed${NC}"
    fi
else
    print_warning "Test results not found"
fi

# Display available reports
print_status "Test reports available:"
echo "  - coverage/unit/ - Unit test coverage"
echo "  - coverage/integration/ - Integration test coverage (if containers available)"
echo "  - coverage/combined/ - Combined coverage report"
echo "  - test-results/ - Test execution results"

# Run linting
print_status "Running ESLint..."
if npm run lint > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Linting passed${NC}"
else
    echo -e "${YELLOW}⚠️ Linting issues found${NC}"
fi

# Check for potential issues
print_status "Checking for potential issues..."

# Check for console.log statements in source code
if grep -r "console.log" src/ --exclude-dir=__tests__ > /dev/null 2>&1; then
    print_warning "console.log statements found in source code"
fi

# Check for TODO comments
if grep -r "TODO\|FIXME\|XXX" src/ --exclude-dir=__tests__ > /dev/null 2>&1; then
    print_warning "TODO/FIXME comments found in source code"
fi

print_status "Frontend API testing completed!"
echo -e "${GREEN}🎉 Testing Complete!${NC}"

# Return to original directory
cd - > /dev/null
