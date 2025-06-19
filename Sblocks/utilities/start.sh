#!/bin/bash

# Email service startup script

echo "Starting SAMFMS Utilities Service with Email capabilities..."

# Check for required environment variables
if [ -z "$EMAIL_PASSWORD" ]; then
    echo "WARNING: EMAIL_PASSWORD is not set. Email sending will be disabled."
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Start the FastAPI application with uvicorn
exec uvicorn main:app --host 0.0.0.0 --port 8000 --log-level info
