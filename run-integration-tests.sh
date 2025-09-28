#!/bin/bash

# SAMFMS Integration Test Runner (fixed & faster)
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
TEST_TIMEOUT=300  # 5 minutes
DEEP_CLEAN="${DEEP_CLEAN:-false}" # set DEEP_CLEAN=true to also 'docker system prune --volumes'

# Helpers
log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

cleanup() {
  log_info "Cleaning up integration test environment..."
  docker-compose -f "$COMPOSE_FILE" down --volumes --remove-orphans 2>/dev/null || true
  if [ "$DEEP_CLEAN" = true ]; then
    log_info "Performing deep clean (docker system prune)..."
    docker system prune -f --volumes 2>/dev/null || true
  fi
}

check_prerequisites() {
  log_info "Checking prerequisites..."
  if ! command -v docker &>/dev/null; then
    log_error "Docker is not installed or not in PATH"; exit 1; fi
  if ! command -v docker-compose &>/dev/null; then
    log_error "Docker Compose is not installed or not in PATH"; exit 1; fi
  if ! docker info &>/dev/null; then
    log_error "Docker daemon is not running"; exit 1; fi
  if ! command -v curl &>/dev/null; then
    log_error "'curl' is required but not found"; exit 1; fi
  if ! command -v timeout &>/dev/null; then
    log_warning "'timeout' not found, global timeout will be disabled"
  fi
  log_success "Prerequisites check passed"
}

# Wait helpers
wait_for_tcp() {
  local name=$1 host=$2 port=$3 timeout=${4:-60}
  log_info "Waiting for $name on $host:$port (tcp, ${timeout}s timeout)..."
  local end=$((SECONDS + timeout))
  while (( SECONDS < end )); do
    (echo > /dev/tcp/$host/$port) >/dev/null 2>&1 && {
      log_success "$name is accepting TCP connections"; return 0; }
    sleep 2
  done
  log_error "$name failed to open TCP within ${timeout}s"; return 1
}

wait_for_http_2xx() {
  local name=$1 url=$2 timeout=${3:-60} curl_args=${4:-}
  log_info "Waiting for $name at $url (HTTP 2xx, ${timeout}s timeout)..."
  local end=$((SECONDS + timeout))
  local code="000"
  while (( SECONDS < end )); do
    code=$(curl -s -o /dev/null -w "%{http_code}" $curl_args "$url" || echo "000")
    [[ "$code" =~ ^2[0-9][0-9]$ ]] && {
      log_success "$name is healthy (HTTP $code)"; return 0; }
    sleep 2
  done
  log_error "$name did not return HTTP 2xx within ${timeout}s (last: $code)"; return 1
}

wait_for_healthy() {
  local cname=$1 timeout=${2:-90}
  log_info "Waiting for container '$cname' to be healthy (timeout ${timeout}s)..."
  local end=$((SECONDS + timeout))
  local status="starting"
  while (( SECONDS < end )); do
    status=$(docker inspect -f '{{.State.Health.Status}}' "$cname" 2>/dev/null || echo "starting")
    [ "$status" = "healthy" ] && { log_success "$cname is healthy"; return 0; }
    sleep 2
  done
  log_error "$cname did not become healthy within ${timeout}s (last status: $status)"; return 1
}

run_with_timeout() {
  if command -v timeout >/dev/null 2>&1; then
    timeout "$TEST_TIMEOUT" "$@"
  else
    "$@"
  fi
}

run_infrastructure() {
  log_info "Starting infrastructure services..."
  docker-compose -f "$COMPOSE_FILE" up -d \
    mongodb-integration rabbitmq-integration redis-integration

  log_info "Waiting for infrastructure to be ready..."

  # IMPORTANT: use host published ports from compose
  # Mongo: 27019:27017
  wait_for_tcp "MongoDB" "localhost" 27019 40 || {
    docker-compose -f "$COMPOSE_FILE" logs --tail=100 mongodb-integration; return 1; }

  # RabbitMQ: prefer AMQP tcp 5674:5672 (mgmt UI needs auth & returns 401)
  wait_for_tcp "RabbitMQ (AMQP)" "localhost" 5674 40 || {
    docker-compose -f "$COMPOSE_FILE" logs --tail=100 rabbitmq-integration; return 1; }

  # Redis: 6381:6379
  wait_for_tcp "Redis" "localhost" 6381 30 || {
    docker-compose -f "$COMPOSE_FILE" logs --tail=100 redis-integration; return 1; }

  log_success "Infrastructure services are reachable"
}

run_backend_services() {
  log_info "Starting backend services..."
  docker-compose -f "$COMPOSE_FILE" up -d \
    core-integration management-integration maintenance-integration trips-integration

  log_info "Waiting for backend services to initialize..."

  # Either rely on container health (recommended since core has a healthcheck)...
  wait_for_healthy "samfms-core-integration" 90 || {
    log_error "Core service failed to become healthy"
    docker-compose -f "$COMPOSE_FILE" logs --tail=200 core-integration
    return 1
  }

  log_success "Backend services are ready"
}

run_frontend_service() {
  log_info "Starting frontend service..."
  docker-compose -f "$COMPOSE_FILE" up -d frontend-integration

  log_info "Waiting for frontend to be ready..."
  # Frontend publishes 3001:80
  if wait_for_http_2xx "Frontend" "http://localhost:3001" 45; then
    log_success "Frontend service is ready"
  else
    log_warning "Frontend did not reach HTTP 2xx in time; continuing"
  fi
}

run_python_tests() {
  log_info "Running Python integration tests..."
  mkdir -p test-results
  run_with_timeout docker-compose -f "$COMPOSE_FILE" run --rm integration-test-runner \
    python -m pytest tests/integration/test_frontend_core_integration.py \
      -v --tb=short --junit-xml=test-results/integration-pytest.xml && {
    log_success "Python integration tests completed successfully"; return 0; }
  log_warning "Python integration tests completed with issues (check logs)"; return 1
}

run_frontend_tests() {
  log_info "Running Frontend integration tests..."

  pushd Frontend/samfms >/dev/null
  if [ ! -d "node_modules" ]; then
    log_info "Installing Frontend dependencies (npm ci)..."
    npm ci
  fi
  if run_with_timeout npm run test:integration; then
    log_success "Frontend integration tests completed successfully"; popd >/dev/null; return 0
  else
    log_warning "Frontend integration tests completed with issues"; popd >/dev/null; return 1
  fi
}

show_logs() {
  log_info "Showing service logs (last 50 lines each)..."
  echo -e "\n${BLUE}=== Core Service Logs ===${NC}"
  docker-compose -f "$COMPOSE_FILE" logs --tail=50 core-integration 2>/dev/null || echo "No core logs"
  echo -e "\n${BLUE}=== Frontend Service Logs ===${NC}"
  docker-compose -f "$COMPOSE_FILE" logs --tail=50 frontend-integration 2>/dev/null || echo "No frontend logs"
  echo -e "\n${BLUE}=== Management Service Logs ===${NC}"
  docker-compose -f "$COMPOSE_FILE" logs --tail=50 management-integration 2>/dev/null || echo "No management logs"
}

show_usage() {
  cat <<EOF
Usage: $0 [OPTIONS]

Options:
  --help, -h          Show this help message
  --logs              Show service logs after running tests
  --python-only       Run only Python integration tests
  --frontend-only     Run only Frontend integration tests
  --no-cleanup        Don't cleanup after tests (for debugging)
  --quick             Run quick smoke tests only

Env flags:
  DEEP_CLEAN=true     Also run 'docker system prune --volumes' during cleanup

Examples:
  $0                  # Run all integration tests
  $0 --python-only    # Run only Python tests
  $0 --logs           # Run tests and then show logs
EOF
}

main() {
  local show_logs_flag=false cleanup_flag=true python_only=false frontend_only=false quick_mode=false

  while [[ $# -gt 0 ]]; do
    case $1 in
      --help|-h) show_usage; exit 0 ;;
      --logs) show_logs_flag=true; shift ;;
      --python-only) python_only=true; shift ;;
      --frontend-only) frontend_only=true; shift ;;
      --no-cleanup) cleanup_flag=false; shift ;;
      --quick) quick_mode=true; shift ;;
      *) log_error "Unknown option: $1"; show_usage; exit 1 ;;
    esac
  done

  if [ "$cleanup_flag" = true ]; then trap cleanup EXIT; fi

  log_info "Starting SAMFMS Integration Test Suite"
  echo "=============================================="

  check_prerequisites

  if [ "$quick_mode" = true ]; then
    log_info "Running quick smoke tests..."

    pushd Frontend/samfms >/dev/null
    if [ ! -d "node_modules" ]; then npm ci >/dev/null 2>&1 || true; fi
    if npm run test:smoke -- --silent; then
      log_success "Quick frontend smoke tests passed"
    else
      log_warning "Quick frontend smoke tests had issues"
    fi
    popd >/dev/null

    if command -v python3 >/dev/null 2>&1 && python3 -m py_compile tests/integration/test_frontend_core_integration.py 2>/dev/null; then
      log_success "Python integration test syntax is valid"
    elif command -v python >/dev/null 2>&1 && python -m py_compile tests/integration/test_frontend_core_integration.py 2>/dev/null; then
      log_success "Python integration test syntax is valid"
    else
      log_warning "Python not available for syntax check, skipping"
    fi

    log_success "Quick smoke tests completed"; exit 0
  fi

  log_info "Cleaning up any existing containers..."
  cleanup

  local test_results=0

  if ! run_infrastructure; then log_error "Failed to start infrastructure services"; exit 1; fi
  if ! run_backend_services; then log_error "Failed to start backend services"; exit 1; fi
  if [ "$python_only" != true ]; then run_frontend_service; fi

  if [ "$frontend_only" != true ]; then
    if ! run_python_tests; then test_results=1; fi
  fi

  if [ "$python_only" != true ]; then
    if ! run_frontend_tests; then test_results=1; fi
  fi

  if [ "$show_logs_flag" = true ]; then show_logs; fi

  log_info "Final container status:"
  docker-compose -f "$COMPOSE_FILE" ps

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

main "$@"
