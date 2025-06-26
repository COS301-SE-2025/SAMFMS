#!/bin/bash

# SAMFMS Test Runner - Run tests for all services
echo "🧪 SAMFMS Test Suite Runner"
echo "==========================="
echo

SERVICE="all"
TEST_TYPE="all"
EXTRA_ARGS=""
SHOW_HELP=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --service)
            SERVICE="$2"
            shift 2
            ;;
        --unit)
            TEST_TYPE="unit"
            shift
            ;;
        --integration)
            TEST_TYPE="integration"
            shift
            ;;
        --coverage)
            EXTRA_ARGS="$EXTRA_ARGS --coverage"
            shift
            ;;
        --verbose)
            EXTRA_ARGS="$EXTRA_ARGS --verbose"
            shift
            ;;
        --help)
            SHOW_HELP=true
            shift
            ;;
        *)
            EXTRA_ARGS="$EXTRA_ARGS $1"
            shift
            ;;
    esac
done

if [ "$SHOW_HELP" = true ]; then
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --service SERVICE     Run tests for specific service (security, core, all)"
    echo "  --unit               Run unit tests only"
    echo "  --integration        Run integration tests only"
    echo "  --coverage           Generate coverage reports"
    echo "  --verbose            Verbose output"
    echo "  --help               Show this help message"
    echo ""
    exit 0
fi

# Ensure test environment is ready
echo "🔧 Preparing test environment..."
docker-compose -f docker-compose.test.yml down --volumes --remove-orphans 2>/dev/null
docker-compose -f docker-compose.test.yml build

# Run tests based on service and type
if [ "$SERVICE" = "all" ] || [ "$SERVICE" = "security" ]; then
    echo "🔐 Running security service tests..."
    if [ "$TEST_TYPE" = "unit" ] || [ "$TEST_TYPE" = "all" ]; then
        docker-compose -f docker-compose.test.yml run --rm security-test pytest tests/unit/ $EXTRA_ARGS
    fi
    if [ "$TEST_TYPE" = "integration" ] || [ "$TEST_TYPE" = "all" ]; then
        docker-compose -f docker-compose.test.yml run --rm security-test pytest tests/integration/ $EXTRA_ARGS
    fi
fi

if [ "$SERVICE" = "all" ] || [ "$SERVICE" = "core" ]; then
    echo "⚙️ Running core service tests..."
    if [ "$TEST_TYPE" = "unit" ] || [ "$TEST_TYPE" = "all" ]; then
        docker-compose -f docker-compose.test.yml run --rm mcore pytest tests/unit/ $EXTRA_ARGS
    fi
    if [ "$TEST_TYPE" = "integration" ] || [ "$TEST_TYPE" = "all" ]; then
        docker-compose -f docker-compose.test.yml run --rm mcore pytest tests/integration/ $EXTRA_ARGS
    fi
fi

echo "✅ Tests completed!"
echo "🧹 Cleaning up..."
docker-compose -f docker-compose.test.yml down --volumes --remove-orphans
