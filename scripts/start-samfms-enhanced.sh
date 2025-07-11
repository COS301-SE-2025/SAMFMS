#!/bin/bash

# SAMFMS Service Startup Script with Dependency Management
# Starts services in correct order and validates startup

set -e

echo "🚀 SAMFMS Service Startup Script"
echo "=================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
STARTUP_TIMEOUT=120
HEALTH_CHECK_INTERVAL=5
MAX_RETRIES=3

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check if service is healthy
check_service_health() {
    local service_name=$1
    local health_url=$2
    local timeout=${3:-10}
    
    log "Checking health of $service_name..."
    
    if curl -f -s --max-time $timeout "$health_url" > /dev/null 2>&1; then
        success "$service_name is healthy"
        return 0
    else
        error "$service_name health check failed"
        return 1
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local service_name=$1
    local health_url=$2
    local max_wait=${3:-$STARTUP_TIMEOUT}
    
    log "Waiting for $service_name to be ready..."
    
    local start_time=$(date +%s)
    local current_time=$start_time
    local elapsed=0
    
    while [ $elapsed -lt $max_wait ]; do
        if check_service_health "$service_name" "$health_url" 5; then
            success "$service_name is ready (${elapsed}s)"
            return 0
        fi
        
        sleep $HEALTH_CHECK_INTERVAL
        current_time=$(date +%s)
        elapsed=$((current_time - start_time))
        
        if [ $((elapsed % 30)) -eq 0 ] && [ $elapsed -gt 0 ]; then
            log "Still waiting for $service_name... (${elapsed}s elapsed)"
        fi
    done
    
    error "$service_name did not become ready within ${max_wait}s"
    return 1
}

# Function to validate environment
validate_environment() {
    log "Validating environment configuration..."
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        warning ".env file not found, using defaults"
    else
        success ".env file found"
    fi
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        error "Docker is not running. Please start Docker first."
        exit 1
    fi
    success "Docker is running"
    
    # Check if docker-compose is available
    if ! command -v docker-compose &> /dev/null; then
        error "docker-compose is not installed or not in PATH"
        exit 1
    fi
    success "docker-compose is available"
    
    # Validate configuration using Python script
    if [ -f "Core/config/env_validator.py" ]; then
        log "Running environment validation..."
        if python3 Core/config/env_validator.py; then
            success "Environment validation passed"
        else
            warning "Environment validation failed, continuing anyway..."
        fi
    fi
}

# Function to start infrastructure services
start_infrastructure() {
    log "Starting infrastructure services..."
    
    # Start MongoDB first
    log "Starting MongoDB..."
    docker-compose up -d mongodb
    wait_for_service "MongoDB" "http://localhost:21003" 60
    
    # Start Redis
    log "Starting Redis..."
    docker-compose up -d redis
    wait_for_service "Redis" "http://localhost:21002" 30
    
    # Start RabbitMQ
    log "Starting RabbitMQ..."
    docker-compose up -d rabbitmq
    wait_for_service "RabbitMQ Management" "http://localhost:21001" 60
    
    success "Infrastructure services started successfully"
}

# Function to start core services
start_core_services() {
    log "Starting core services..."
    
    # Start Security service first (Core depends on it)
    log "Starting Security service..."
    docker-compose up -d security
    wait_for_service "Security" "http://localhost:21009/health" 60
    
    # Start Core service
    log "Starting Core service..."
    docker-compose up -d core
    wait_for_service "Core" "http://localhost:21004/health" 60
    
    success "Core services started successfully"
}

# Function to start service blocks
start_service_blocks() {
    log "Starting service blocks..."
    
    # Start all service blocks in parallel
    local services=("gps" "trip_planning" "vehicle_maintenance" "utilities" "management" "micro_frontend")
    
    for service in "${services[@]}"; do
        log "Starting $service service..."
        docker-compose up -d "$service"
    done
    
    # Wait for all services to be ready
    local service_ports=("21005" "21006" "21007" "21008" "21010" "21011")
    local service_names=("GPS" "Trip Planning" "Vehicle Maintenance" "Utilities" "Management" "Micro Frontend")
    
    for i in "${!services[@]}"; do
        wait_for_service "${service_names[$i]}" "http://localhost:${service_ports[$i]}/health" 60
    done
    
    success "Service blocks started successfully"
}

# Function to start data blocks
start_data_blocks() {
    log "Starting data blocks..."
    
    local data_services=("users_dblock" "vehicles_dblock" "gps_dblock")
    
    for service in "${data_services[@]}"; do
        log "Starting $service..."
        docker-compose up -d "$service"
    done
    
    # Wait for data blocks to be ready
    local data_ports=("21012" "21013" "21014")
    local data_names=("Users Data Block" "Vehicles Data Block" "GPS Data Block")
    
    for i in "${!data_services[@]}"; do
        wait_for_service "${data_names[$i]}" "http://localhost:${data_ports[$i]}/health" 60
    done
    
    success "Data blocks started successfully"
}

# Function to start frontend and nginx
start_frontend() {
    log "Starting frontend services..."
    
    # Start Frontend
    log "Starting Frontend..."
    docker-compose up -d frontend
    wait_for_service "Frontend" "http://localhost:21015" 60
    
    # Start Nginx
    log "Starting Nginx..."
    docker-compose up -d nginx
    wait_for_service "Nginx" "http://localhost:21016" 30
    
    success "Frontend services started successfully"
}

# Function to start additional services
start_additional_services() {
    log "Starting additional services..."
    
    # Start Traccar
    log "Starting Traccar..."
    docker-compose up -d traccar
    sleep 10  # Traccar takes longer to start
    
    # Start Certbot (if needed)
    if [ "$ENVIRONMENT" = "production" ]; then
        log "Starting Certbot..."
        docker-compose up -d certbot
    fi
    
    success "Additional services started successfully"
}

# Function to run final health check
run_final_health_check() {
    log "Running final health check..."
    
    if [ -f "scripts/health-monitor.py" ]; then
        if python3 scripts/health-monitor.py; then
            success "All services are healthy!"
        else
            warning "Some services reported issues. Check the health report above."
        fi
    else
        warning "Health monitor script not found, skipping final health check"
    fi
}

# Function to display startup summary
display_summary() {
    echo ""
    echo "🎉 SAMFMS Startup Complete!"
    echo "=========================="
    echo ""
    echo "🌐 Frontend: http://localhost:21015"
    echo "🔒 Nginx (HTTP): http://localhost:21016"
    echo "🔐 Nginx (HTTPS): https://localhost:21017"
    echo "🔧 Core API: http://localhost:21004"
    echo "🐰 RabbitMQ Management: http://localhost:21001 (user: samfms_rabbit)"
    echo "🍃 MongoDB: localhost:21003"
    echo "📊 Redis: localhost:21002"
    echo ""
    echo "📝 To monitor services: ./scripts/health-monitor.py --continuous"
    echo "🛑 To stop all services: docker-compose down"
    echo "📋 To view logs: docker-compose logs -f [service-name]"
    echo ""
}

# Main startup sequence
main() {
    echo ""
    log "Starting SAMFMS system startup sequence..."
    echo ""
    
    # Validate environment
    validate_environment
    echo ""
    
    # Stop any existing containers
    log "Stopping any existing containers..."
    docker-compose down --remove-orphans
    echo ""
    
    # Start services in dependency order
    start_infrastructure
    echo ""
    
    start_core_services
    echo ""
    
    start_service_blocks
    echo ""
    
    start_data_blocks
    echo ""
    
    start_frontend
    echo ""
    
    start_additional_services
    echo ""
    
    # Final health check
    run_final_health_check
    echo ""
    
    # Display summary
    display_summary
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "SAMFMS Service Startup Script"
        echo ""
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h          Show this help message"
        echo "  --infrastructure    Start only infrastructure services"
        echo "  --core             Start only core services"
        echo "  --services         Start only service blocks"
        echo "  --frontend         Start only frontend services"
        echo "  --health-check     Run health check only"
        echo ""
        exit 0
        ;;
    --infrastructure)
        validate_environment
        start_infrastructure
        ;;
    --core)
        start_core_services
        ;;
    --services)
        start_service_blocks
        ;;
    --frontend)
        start_frontend
        ;;
    --health-check)
        run_final_health_check
        ;;
    "")
        main
        ;;
    *)
        error "Unknown option: $1"
        echo "Use --help for usage information"
        exit 1
        ;;
esac
