#!/bin/bash

# GPS Service Test Runner
echo "Running GPS Service Tests..."

# Set environment variables for testing
export MONGODB_URL="mongodb://localhost:27017"
export DATABASE_NAME="test_samfms_gps"
export RABBITMQ_URL="amqp://guest:guest@localhost:5672/"

# Install test dependencies
echo "Installing test dependencies..."
pip install pytest pytest-asyncio pytest-cov

# Run tests with coverage
echo "Running tests with coverage..."
pytest tests/ -v --cov=. --cov-report=html --cov-report=term

echo "Tests completed. Coverage report available in htmlcov/"
