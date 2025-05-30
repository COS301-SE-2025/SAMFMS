#!/bin/bash
set -e

# Function to wait for a service
wait_for_service() {
    host=$1
    port=$2
    service_name=$3
    
    echo "Waiting for $service_name to be ready..."
    until nc -z $host $port; do
        echo "  $service_name is unavailable - sleeping"
        sleep 1
    done
    echo "  $service_name is ready!"
}

# Wait for dependencies
wait_for_service redis 6379 "Redis"
wait_for_service rabbitmq 5672 "RabbitMQ"

# Start the GPS service
echo "Starting GPS Service..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
