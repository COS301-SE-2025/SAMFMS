#!/bin/bash

# Start script for Maintenance Service
# Following the same patterns as Management service

echo "Starting SAMFMS Maintenance Service..."

# Wait for dependencies
echo "Waiting for dependencies..."
sleep 10

# Start the service
exec python main.py
