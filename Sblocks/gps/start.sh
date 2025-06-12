#!/bin/bash

# Wait for Redis to be ready
echo "Waiting for Redis..."
while ! nc -z redis 6379; do
    sleep 1
done
echo "Redis is ready!"

# Wait for RabbitMQ to be ready
echo "Waiting for RabbitMQ..."
while ! nc -z rabbitmq 5672; do
    sleep 1
done
echo "RabbitMQ is ready!"

# Start the GPS service
echo "Starting GPS Service..."
uvicorn main:app --host 0.0.0.0 --port 8000

