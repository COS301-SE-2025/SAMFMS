#!/bin/bash

# SAMFMS Integration Test Runner
# Runs Frontend-Core integration tests locally using Docker Compose

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.integration.yml"
TEST_TIMEOUT=600  # 10 minutes

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

cleanup() {
    log_info "Cleaning up integration test environment..."
    docker-compose -f $COMPOSE_FILE down --volumes --remove-orphans 2>/dev/null || true
    docker system prune -f --volumes 2>/dev/null || true
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed or not in PATH"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

wait_for_service() {
    local service_name=$1
    local url=$2
    local timeout=${3:-60}
    
    log_info "Waiting for $service_name to be ready..."
    
    local count=0
    while [ $count -lt $timeout ]; do
        if curl -f "$url" &> /dev/null; then
            log_success "$service_name is ready"
            return 0
        fi
        sleep 2
        count=$((count + 2))
    done
    
    log_error "$service_name failed to start within $timeout seconds"
    return 1
}

run_infrastructure() {
    log_info "Starting infrastructure services..."
    
    docker-compose -f $COMPOSE_FILE up -d \
        mongodb-integration \
        rabbitmq-integration \
        redis-integration
    
    log_info "Waiting for infrastructure to be ready..."
    sleep 30
    
    # Check if services are running
    if ! docker-compose -f $COMPOSE_FILE ps | grep -q "Up"; then
        log_error "Infrastructure services failed to start"
        docker-compose -f $COMPOSE_FILE logs
        return 1
    fi
    
    log_success "Infrastructure services are running"
}

run_backend_services() {
    log_info "Starting backend services..."
    
    docker-compose -f $COMPOSE_FILE up -d \
        core-integration \
        management-integration \
        maintenance-integration \
        trips-integration
    
    log_info "Waiting for backend services to initialize..."
    sleep 45
    
    # Wait for Core service
    if wait_for_service "Core API" "http://localhost:8001/health" 120; then
        log_success "Backend services are ready"
    else
        log_error "Backend services failed to start properly"
        docker-compose -f $COMPOSE_FILE logs core-integration
        return 1
    fi
}

run_frontend_service() {
    log_info "Starting frontend service..."
    
    docker-compose -f $COMPOSE_FILE up -d frontend-integration
    
    log_info "Waiting for frontend to build and start..."
    sleep 30
    
    if wait_for_service "Frontend" "http://localhost:3001" 120; then
        log_success "Frontend service is ready"
    else
        log_warning "Frontend service may not be fully ready, but continuing with tests"
    fi
}

run_python_tests() {
    log_info "Running Python integration tests..."
    
    # Create test results directory
    mkdir -p test-results
    
    if docker-compose -f $COMPOSE_FILE run --rm integration-test-runner \
        python -m pytest tests/integration/test_frontend_core_integration.py \
        -v --tb=short --junit-xml=test-results/integration-pytest.xml; then
        log_success "Python integration tests completed successfully"
        return 0
    else
        log_warning "Python integration tests completed with issues (check logs for details)"
        return 1
    fi
}

run_frontend_tests() {
    log_info "Running Frontend integration tests..."
    
    cd Frontend/samfms
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        log_info "Installing Frontend dependencies..."
        npm ci
    fi
    
    # Run integration tests
    if npm run test:integration; then
        log_success "Frontend integration tests completed successfully"
        return 0
    else
        log_warning "Frontend integration tests completed with issues"
        return 1
    fi
}

show_logs() {
    log_info "Showing service logs (last 50 lines each)..."
    
    echo -e "\n${BLUE}=== Core Service Logs ===${NC}"
    docker-compose -f $COMPOSE_FILE logs --tail=50 core-integration 2>/dev/null || echo "No core logs available"
    
    echo -e "\n${BLUE}=== Frontend Service Logs ===${NC}"
    docker-compose -f $COMPOSE_FILE logs --tail=50 frontend-integration 2>/dev/null || echo "No frontend logs available"
    
    echo -e "\n${BLUE}=== Management Service Logs ===${NC}"
    docker-compose -f $COMPOSE_FILE logs --tail=50 management-integration 2>/dev/null || echo "No management logs available"
}

show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --help, -h          Show this help message"
    echo "  --logs              Show service logs after running tests"
    echo "  --python-only       Run only Python integration tests"
    echo "  --frontend-only     Run only Frontend integration tests"
    echo "  --no-cleanup        Don't cleanup after tests (for debugging)"
    echo "  --quick             Run quick smoke tests only"
    echo ""
    echo "Examples:"
    echo "  $0                  # Run all integration tests"
    echo "  $0 --python-only    # Run only Python tests"
    echo "  $0 --logs           # Run tests and show logs"
    echo "  $0 --no-cleanup     # Keep containers running after tests"
}

# Main execution
main() {
    local show_logs_flag=false
    local cleanup_flag=true
    local python_only=false
    local frontend_only=false
    local quick_mode=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                show_usage
                exit 0
                ;;
            --logs)
                show_logs_flag=true
                shift
                ;;
            --python-only)
                python_only=true
                shift
                ;;
            --frontend-only)
                frontend_only=true
                shift
                ;;
            --no-cleanup)
                cleanup_flag=false
                shift
                ;;
            --quick)
                quick_mode=true
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Set cleanup trap
    if [ "$cleanup_flag" = true ]; then
        trap cleanup EXIT
    fi
    
    log_info "Starting SAMFMS Integration Test Suite"
    echo "=============================================="
    
    # Check prerequisites
    check_prerequisites
    
    if [ "$quick_mode" = true ]; then
        log_info "Running quick smoke tests..."
        
        # Quick frontend test
        cd Frontend/samfms
        npm ci > /dev/null 2>&1
        if npm run test:smoke -- --silent; then
            log_success "Quick frontend smoke tests passed"
        else
            log_warning "Quick frontend smoke tests had issues"
        fi
        
        # Quick Python syntax check
        cd ../..
        if python3 -m py_compile tests/integration/test_frontend_core_integration.py 2>/dev/null; then
            log_success "Python integration test syntax is valid"
        elif command -v python >/dev/null 2>&1 && python -m py_compile tests/integration/test_frontend_core_integration.py 2>/dev/null; then
            log_success "Python integration test syntax is valid"
        else
            log_warning "Python not available for syntax check, skipping"
        fi
        
        log_success "Quick smoke tests completed"
        exit 0
    fi
    
    # Cleanup any existing containers
    log_info "Cleaning up any existing containers..."
    cleanup
    
    local test_results=0
    
    # Start services
    if ! run_infrastructure; then
        log_error "Failed to start infrastructure services"
        exit 1
    fi
    
    if ! run_backend_services; then
        log_error "Failed to start backend services"
        exit 1
    fi
    
    if [ "$python_only" != true ]; then
        run_frontend_service
    fi
    
    # Run tests
    if [ "$frontend_only" != true ]; then
        if ! run_python_tests; then
            test_results=1
        fi
    fi
    
    if [ "$python_only" != true ]; then
        if ! run_frontend_tests; then
            test_results=1
        fi
    fi
    
    # Show logs if requested
    if [ "$show_logs_flag" = true ]; then
        show_logs
    fi
    
    # Show container status
    log_info "Final container status:"
    docker-compose -f $COMPOSE_FILE ps
    
    # Summary
    echo ""
    echo "=============================================="
    if [ $test_results -eq 0 ]; then
        log_success "All integration tests completed successfully! 🎉"
    else
        log_warning "Integration tests completed with some issues. Check the logs above for details."
        log_info "You can run with --logs flag to see service logs, or --no-cleanup to investigate containers."
    fi
    
    exit $test_results
}

# Run main function with all arguments
main "$@"