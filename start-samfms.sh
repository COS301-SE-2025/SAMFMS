#!/bin/bash

# SAMFMS Startup Script
# This script ensures proper startup sequence for all services

set -e

echo "🚀 Starting SAMFMS Infrastructure..."

# Function to check if a service is healthy
wait_for_service() {
    local service_name=$1
    local max_attempts=60
    local attempt=1
    
    echo "⏳ Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose ps $service_name | grep -q "(healthy)"; then
            echo "✅ $service_name is ready!"
            return 0
        fi
        
        echo "   Attempt $attempt/$max_attempts: $service_name not ready yet..."
        sleep 5
        attempt=$((attempt + 1))
    done
    
    echo "❌ $service_name failed to become ready after $max_attempts attempts"
    return 1
}

# Stop any existing containers
echo "🧹 Cleaning up existing containers..."
docker-compose down --remove-orphans

# Start infrastructure services first
echo "🏗️  Starting infrastructure services..."
docker-compose up -d rabbitmq redis mongodb

# Wait for infrastructure to be ready
wait_for_service rabbitmq
wait_for_service redis  
wait_for_service mongodb

# Start core services
echo "🔧 Starting core services..."
docker-compose up -d security core

# Wait for core services
wait_for_service security
wait_for_service core

# Start all other services
echo "📦 Starting remaining services..."
docker-compose up -d

echo "🎉 SAMFMS startup completed!"
echo "📊 Service status:"
docker-compose ps

echo ""
echo "🌐 Access points:"
echo "   Frontend: http://localhost:21015"
echo "   Core API: http://localhost:21004"
echo "   RabbitMQ Management: http://localhost:21001"
echo "   MongoDB: mongodb://localhost:21003"
