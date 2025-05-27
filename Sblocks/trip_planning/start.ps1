# Trip Planning Service Startup Script for Windows
# PowerShell script to start the Trip Planning Service

Write-Host "Starting Trip Planning Service..." -ForegroundColor Green

# Set environment variables if not already set
if (-not $env:PYTHONPATH) {
    $env:PYTHONPATH = "$env:PYTHONPATH;$(Get-Location)"
}
if (-not $env:ENVIRONMENT) {
    $env:ENVIRONMENT = "development"
}

# Create necessary directories
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Name "logs"
}

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Install/upgrade dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Wait for database services to be ready
Write-Host "Waiting for database services..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check MongoDB connection
Write-Host "Checking MongoDB connection..." -ForegroundColor Yellow
try {
    $mongoCheck = python -c @"
import pymongo
try:
    client = pymongo.MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=5000)
    client.server_info()
    print('SUCCESS')
except Exception as e:
    print(f'FAILED: {e}')
    exit(1)
"@
    if ($mongoCheck -match "SUCCESS") {
        Write-Host "MongoDB connection successful" -ForegroundColor Green
    } else {
        Write-Host "MongoDB connection failed: $mongoCheck" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "Error checking MongoDB connection: $_" -ForegroundColor Red
    exit 1
}

# Check RabbitMQ connection
Write-Host "Checking RabbitMQ connection..." -ForegroundColor Yellow
try {
    $rabbitCheck = python -c @"
import pika
try:
    connection = pika.BlockingConnection(pika.URLParameters('amqp://guest:guest@localhost:5672/'))
    connection.close()
    print('SUCCESS')
except Exception as e:
    print(f'FAILED: {e}')
    exit(1)
"@
    if ($rabbitCheck -match "SUCCESS") {
        Write-Host "RabbitMQ connection successful" -ForegroundColor Green
    } else {
        Write-Host "RabbitMQ connection failed: $rabbitCheck" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "Error checking RabbitMQ connection: $_" -ForegroundColor Red
    exit 1
}

# Start the application
Write-Host "Starting Trip Planning Service..." -ForegroundColor Green
if ($env:ENVIRONMENT -eq "production") {
    Write-Host "Running in production mode..." -ForegroundColor Cyan
    uvicorn main:app --host 0.0.0.0 --port 8003 --workers 4
} else {
    Write-Host "Running in development mode..." -ForegroundColor Cyan
    uvicorn main:app --host 0.0.0.0 --port 8003 --reload
}
