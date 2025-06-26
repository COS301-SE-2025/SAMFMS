#!/bin/bash
# Improved startup script with better error handling and diagnostics

set -e  # Exit on any error

echo "Core Service Startup Script v2.0"
echo "================================="

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check system compatibility
check_system() {
    log "Checking system compatibility..."
    
    # Check CPU architecture
    ARCH=$(uname -m)
    log "CPU Architecture: $ARCH"
    
    # Check for required CPU features
    if [ -f /proc/cpuinfo ]; then
        if grep -q "sse2" /proc/cpuinfo; then
            log "SSE2 support: OK"
        else
            log "WARNING: SSE2 support not detected"
        fi
    fi
    
    # Check Python version and environment
    python3 --version || {
        log "ERROR: Python3 not found"
        exit 1
    }
    
    # Check if we're in a container
    if [ -f /.dockerenv ]; then
        log "Running in Docker container"
    fi
}

# Function to wait for dependencies
wait_for_dependencies() {
    log "Checking dependencies..."
    
    # Wait for MongoDB (if using external MongoDB)
    if [ "${MONGODB_HOST:-}" != "" ] && [ "${MONGODB_HOST}" != "localhost" ]; then
        log "Waiting for external MongoDB at ${MONGODB_HOST}..."
        timeout=30
        while ! nc -z "${MONGODB_HOST}" 27017 2>/dev/null && [ $timeout -gt 0 ]; do
            log "MongoDB not ready, waiting... ($timeout seconds left)"
            sleep 2
            timeout=$((timeout - 2))
        done
        
        if [ $timeout -le 0 ]; then
            log "WARNING: MongoDB connection timeout"
        else
            log "MongoDB connection successful"
        fi
    fi
    
    # Wait for RabbitMQ
    if [ "${RABBITMQ_HOST:-}" != "" ]; then
        log "Waiting for RabbitMQ at ${RABBITMQ_HOST}..."
        timeout=60
        while ! nc -z "${RABBITMQ_HOST}" 5672 2>/dev/null && [ $timeout -gt 0 ]; do
            log "RabbitMQ not ready, waiting... ($timeout seconds left)"
            sleep 2
            timeout=$((timeout - 2))
        done
        
        if [ $timeout -le 0 ]; then
            log "WARNING: RabbitMQ connection timeout"
        else
            log "RabbitMQ connection successful"
        fi
    fi
}

# Function to start the API server with error handling
start_api_server() {
    log "Starting API server..."
    
    # Set CPU compatibility flags if needed
    export OPENBLAS_CORETYPE=generic
    export MKL_DEBUG_CPU_TYPE=5
    
    # Start with increased timeout and better error handling
    exec python3 -m uvicorn main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --timeout-keep-alive 65 \
        --access-log \
        --log-level info
}

# Main execution
main() {
    log "Starting Core service initialization..."
    
    # System checks
    check_system
    
    # Wait for dependencies
    wait_for_dependencies
    
    # Add startup delay if configured
    if [ "${SERVICE_STARTUP_DELAY:-0}" -gt 0 ]; then
        log "Service startup delay: ${SERVICE_STARTUP_DELAY} seconds"
        sleep "${SERVICE_STARTUP_DELAY}"
    fi
    
    # Start the API server
    start_api_server
}

# Trap signals for graceful shutdown
trap 'log "Received shutdown signal, exiting..."; exit 0' SIGTERM SIGINT

# Run main function
main "$@"
