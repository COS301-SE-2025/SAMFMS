#!/bin/bash

# Trip Planning Service Startup Script
echo "Starting Trip Planning Service..."

# Ensure this script uses Unix (LF) line endings only

# Set environment variables if not already set
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export ENVIRONMENT="${ENVIRONMENT:-development}"

# Create necessary directories
mkdir -p logs
mkdir -p /tmp/trip-planning

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Wait for database services to be ready
echo "Waiting for database services..."
sleep 10

# Check MongoDB connection
echo "Checking MongoDB connection..."
python -c <<EOF
import pymongo
import sys
try:
    client = pymongo.MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=5000)
    client.server_info()
    print('MongoDB connection successful')
except Exception as e:
    print(f'MongoDB connection failed: {e}')
    sys.exit(1)
EOF

# Check RabbitMQ connection
echo "Checking RabbitMQ connection..."
python -c <<EOF
import pika
import sys
try:
    connection = pika.BlockingConnection(pika.URLParameters('amqp://guest:guest@localhost:5672/'))
    connection.close()
    print('RabbitMQ connection successful')
except Exception as e:
    print(f'RabbitMQ connection failed: {e}')
    sys.exit(1)
EOF

# Start the application
echo "Starting Trip Planning Service..."
if [ "$ENVIRONMENT" = "production" ]; then
    echo "Running in production mode..."
    uvicorn main:app --host 0.0.0.0 --port 8003 --workers 4
else
    echo "Running in development mode..."
    uvicorn main:app --host 0.0.0.0 --port 8003 --reload
fi
