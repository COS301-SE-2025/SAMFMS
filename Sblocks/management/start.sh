#!/bin/bash

# Get port from environment variable or use default
PORT=${MANAGEMENT_PORT:-8000}

# Start Uvicorn with the configured port
uvicorn main:app --host 0.0.0.0 --port $PORT
