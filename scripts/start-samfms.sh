#!/bin/bash
# SAMFMS Startup Script
# Validates environment and starts services with proper error handling

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_error() {
    echo -e "${RED}❌ ERROR: $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Function to show usage
show_usage() {
    echo "SAMFMS Startup Script"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --dev         Start in development mode"
    echo "  --prod        Start in production mode"
    echo "  --ssl         Start with SSL profile"
    echo "  --build       Force rebuild of images"
    echo "  --validate    Only run validation, don't start"
    echo "  --stop        Stop all services"
    echo "  --logs        Show service logs"
    echo "  --status      Show service status"
    echo "  --help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --dev --build    # Build and start in development mode"
    echo "  $0 --prod --ssl     # Start in production with SSL"
    echo "  $0 --validate       # Only validate configuration"
    echo "  $0 --stop           # Stop all services"
}

# Function to validate environment
validate_environment() {
    if [ -f "./scripts/validate-environment.sh" ]; then
        print_info "Running environment validation..."
        if ./scripts/validate-environment.sh; then
            print_success "Environment validation passed"
            return 0
        else
            print_error "Environment validation failed"
            return 1
        fi
    else
        print_warning "Environment validation script not found, skipping..."
        return 0
    fi
}

# Function to start services
start_services() {
    local compose_args=""
    local profile_args=""
    
    if [ "$BUILD" = "true" ]; then
        compose_args="$compose_args --build"
    fi
    
    if [ "$SSL_MODE" = "true" ]; then
        profile_args="--profile ssl"
    fi
    
    if [ "$DEV_MODE" = "true" ]; then
        if [ -f "docker-compose.dev.yml" ]; then
            compose_args="-f docker-compose.yml -f docker-compose.dev.yml $compose_args"
        else
            print_warning "docker-compose.dev.yml not found, using default configuration"
        fi
    fi
    
    print_info "Starting SAMFMS services..."
    
    # Create necessary directories
    mkdir -p ./ssl-certs ./ssl-private ./certbot/conf ./certbot/www
    
    # Start services
    if eval "docker-compose $compose_args $profile_args up -d"; then
        print_success "Services started successfully"
        
        # Show service status
        echo ""
        print_info "Service Status:"
        docker-compose ps
        
        echo ""
        print_info "Access URLs:"
        source .env 2>/dev/null || true
        echo "  Frontend: https://${REACT_APP_DOMAIN:-localhost}:${NGINX_HTTPS_PORT:-21017}"
        echo "  API: https://${REACT_APP_DOMAIN:-localhost}:${NGINX_HTTPS_PORT:-21017}/api"
        echo "  RabbitMQ Management: http://localhost:${RABBITMQ_MANAGEMENT_PORT:-21001}"
        
        return 0
    else
        print_error "Failed to start services"
        return 1
    fi
}

# Function to stop services
stop_services() {
    print_info "Stopping SAMFMS services..."
    
    if docker-compose down; then
        print_success "Services stopped successfully"
        return 0
    else
        print_error "Failed to stop services"
        return 1
    fi
}

# Function to show logs
show_logs() {
    if [ -n "$SERVICE" ]; then
        docker-compose logs -f "$SERVICE"
    else
        docker-compose logs -f
    fi
}

# Function to show status
show_status() {
    print_info "SAMFMS Service Status:"
    docker-compose ps
    
    echo ""
    print_info "Resource Usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" \
        $(docker-compose ps -q) 2>/dev/null || print_warning "Could not get resource usage"
}

# Parse command line arguments
DEV_MODE=false
PROD_MODE=false
SSL_MODE=false
BUILD=false
VALIDATE_ONLY=false
STOP_SERVICES=false
SHOW_LOGS=false
SHOW_STATUS=false
SERVICE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --dev)
            DEV_MODE=true
            shift
            ;;
        --prod)
            PROD_MODE=true
            shift
            ;;
        --ssl)
            SSL_MODE=true
            shift
            ;;
        --build)
            BUILD=true
            shift
            ;;
        --validate)
            VALIDATE_ONLY=true
            shift
            ;;
        --stop)
            STOP_SERVICES=true
            shift
            ;;
        --logs)
            SHOW_LOGS=true
            shift
            if [[ $1 && $1 != --* ]]; then
                SERVICE=$1
                shift
            fi
            ;;
        --status)
            SHOW_STATUS=true
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
main() {
    print_info "SAMFMS Service Manager"
    echo ""
    
    # Handle stop command
    if [ "$STOP_SERVICES" = "true" ]; then
        stop_services
        exit $?
    fi
    
    # Handle logs command
    if [ "$SHOW_LOGS" = "true" ]; then
        show_logs
        exit $?
    fi
    
    # Handle status command
    if [ "$SHOW_STATUS" = "true" ]; then
        show_status
        exit $?
    fi
    
    # Validate environment
    if ! validate_environment; then
        exit 1
    fi
    
    # If only validation requested
    if [ "$VALIDATE_ONLY" = "true" ]; then
        print_success "Validation completed successfully"
        exit 0
    fi
    
    # Set default mode if none specified
    if [ "$DEV_MODE" = "false" ] && [ "$PROD_MODE" = "false" ]; then
        print_info "No mode specified, defaulting to production mode"
        PROD_MODE=true
    fi
    
    # Start services
    if ! start_services; then
        exit 1
    fi
    
    print_success "SAMFMS startup completed successfully!"
}

# Run main function
main
