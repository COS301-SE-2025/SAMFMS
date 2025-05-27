#!/bin/bash

# GPS Tracking Service Startup Script
# This script starts the GPS tracking service with all dependencies

set -e

echo "Starting GPS Tracking Service..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

# Ensure this script uses Unix (LF) line endings only

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose > /dev/null 2>&1; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Set environment variables if not already set
export GPS_SERVICE_ENV=${GPS_SERVICE_ENV:-development}
export MONGODB_URL=${MONGODB_URL:-mongodb://localhost:27017/gps_tracking}
export REDIS_URL=${REDIS_URL:-redis://localhost:6379/0}
export RABBITMQ_URL=${RABBITMQ_URL:-amqp://gps_service:gps_service_password@localhost:5672/}

print_status "Environment: $GPS_SERVICE_ENV"
print_status "MongoDB URL: $MONGODB_URL"
print_status "Redis URL: $REDIS_URL"
print_status "RabbitMQ URL: $RABBITMQ_URL"

# Create necessary directories
mkdir -p logs
mkdir -p data/mongodb
mkdir -p data/redis

print_status "Created necessary directories"

# Copy configuration files if they don't exist
if [ ! -f .env ]; then
    print_warning ".env file not found, creating from template..."
    cat > .env << EOF
# GPS Service Environment Configuration
GPS_SERVICE_ENV=development
DEBUG=true

# Database Configuration
MONGODB_URL=mongodb://mongodb:27017/gps_tracking
REDIS_URL=redis://redis:6379/0

# Message Queue Configuration
RABBITMQ_URL=amqp://gps_service:gps_service_password@rabbitmq:5672/

# API Configuration
API_HOST=0.0.0.0
API_PORT=8003
API_WORKERS=4

# Location Tracking Configuration
LOCATION_UPDATE_INTERVAL=30
LOCATION_ACCURACY_THRESHOLD=50.0
ENABLE_REAL_TIME_TRACKING=true

# Geofencing Configuration
GEOFENCE_CHECK_INTERVAL=10
GEOFENCE_BUFFER_DISTANCE=10.0
ENABLE_GEOFENCE_MONITORING=true

# Security Configuration
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/gps_service.log

# Performance Configuration
MAX_WORKERS=10
ENABLE_METRICS=true
METRICS_PORT=8004
EOF
    print_status "Created .env file with default configuration"
fi

# Stop any existing containers
print_status "Stopping existing containers..."
docker-compose down > /dev/null 2>&1 || true

# Pull latest images
print_status "Pulling latest Docker images..."
docker-compose pull

# Build the GPS service image
print_status "Building GPS service image..."
docker-compose build gps-service

# Start the services
print_status "Starting services..."
docker-compose up -d

# Wait for services to be ready
print_status "Waiting for services to be ready..."

# Wait for MongoDB
print_status "Waiting for MongoDB..."
timeout 60 bash -c 'until docker-compose exec -T mongodb mongosh --eval "db.adminCommand(\"ismaster\")" > /dev/null 2>&1; do sleep 2; done'

# Wait for Redis
print_status "Waiting for Redis..."
timeout 60 bash -c 'until docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; do sleep 2; done'

# Wait for RabbitMQ
print_status "Waiting for RabbitMQ..."
timeout 60 bash -c 'until docker-compose exec -T rabbitmq rabbitmqctl status > /dev/null 2>&1; do sleep 2; done'

# Initialize MongoDB if needed
print_status "Initializing MongoDB..."
docker-compose exec -T mongodb mongosh gps_tracking /docker-entrypoint-initdb.d/mongo-init.js

# Wait for GPS service to be ready
print_status "Waiting for GPS service..."
timeout 60 bash -c 'until curl -f http://localhost:8003/health > /dev/null 2>&1; do sleep 2; done'

# Display service status
print_status "Service Status:"
docker-compose ps

print_status "GPS Tracking Service started successfully!"
print_status ""
print_status "Service URLs:"
print_status "  • GPS API: http://localhost:8003"
print_status "  • API Documentation: http://localhost:8003/docs"
print_status "  • Health Check: http://localhost:8003/health"
print_status "  • WebSocket: ws://localhost:8003/ws"
print_status ""
print_status "Management Interfaces:"
print_status "  • MongoDB Express: http://localhost:8081"
print_status "  • RabbitMQ Management: http://localhost:15672 (gps_service/gps_service_password)"
print_status "  • Redis Commander: http://localhost:8082"
print_status ""
print_status "Logs:"
print_status "  • View all logs: docker-compose logs -f"
print_status "  • GPS service logs: docker-compose logs -f gps-service"
print_status ""
print_status "To stop the service: docker-compose down"

# Optional: Open browser to API documentation
if command -v xdg-open > /dev/null 2>&1; then
    read -p "Open API documentation in browser? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        xdg-open http://localhost:8003/docs
    fi
fi
