# GPS Tracking Service Startup Script for Windows
# This script starts the GPS tracking service with all dependencies

param(
    [switch]$SkipBrowser,
    [string]$Environment = "development"
)

$ErrorActionPreference = "Stop"

Write-Host "Starting GPS Tracking Service..." -ForegroundColor Green

# Function to print colored output
function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Check if Docker is running
try {
    docker info | Out-Null
} catch {
    Write-Error "Docker is not running. Please start Docker Desktop first."
    exit 1
}

# Check if Docker Compose is available
try {
    docker-compose --version | Out-Null
} catch {
    Write-Error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
}

# Set environment variables if not already set
$env:GPS_SERVICE_ENV = if ($env:GPS_SERVICE_ENV) { $env:GPS_SERVICE_ENV } else { $Environment }
$env:MONGODB_URL = if ($env:MONGODB_URL) { $env:MONGODB_URL } else { "mongodb://localhost:27017/gps_tracking" }
$env:REDIS_URL = if ($env:REDIS_URL) { $env:REDIS_URL } else { "redis://localhost:6379/0" }
$env:RABBITMQ_URL = if ($env:RABBITMQ_URL) { $env:RABBITMQ_URL } else { "amqp://gps_service:gps_service_password@localhost:5672/" }

Write-Status "Environment: $($env:GPS_SERVICE_ENV)"
Write-Status "MongoDB URL: $($env:MONGODB_URL)"
Write-Status "Redis URL: $($env:REDIS_URL)"
Write-Status "RabbitMQ URL: $($env:RABBITMQ_URL)"

# Create necessary directories
$directories = @("logs", "data\mongodb", "data\redis")
foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

Write-Status "Created necessary directories"

# Create .env file if it doesn't exist
if (!(Test-Path ".env")) {
    Write-Warning ".env file not found, creating from template..."
    
    $envContent = @"
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
"@
    
    $envContent | Out-File -FilePath ".env" -Encoding UTF8
    Write-Status "Created .env file with default configuration"
}

# Stop any existing containers
Write-Status "Stopping existing containers..."
try {
    docker-compose down 2>$null | Out-Null
} catch {
    # Ignore errors if containers aren't running
}

# Pull latest images
Write-Status "Pulling latest Docker images..."
docker-compose pull

# Build the GPS service image
Write-Status "Building GPS service image..."
docker-compose build gps-service

# Start the services
Write-Status "Starting services..."
docker-compose up -d

# Wait for services to be ready
Write-Status "Waiting for services to be ready..."

# Function to wait for a service
function Wait-ForService {
    param(
        [string]$ServiceName,
        [string]$Command,
        [int]$TimeoutSeconds = 60
    )
    
    Write-Status "Waiting for $ServiceName..."
    $timeout = (Get-Date).AddSeconds($TimeoutSeconds)
    
    while ((Get-Date) -lt $timeout) {
        try {
            Invoke-Expression $Command | Out-Null
            Write-Status "$ServiceName is ready"
            return
        } catch {
            Start-Sleep -Seconds 2
        }
    }
    
    Write-Error "Timeout waiting for $ServiceName"
    exit 1
}

# Wait for MongoDB
Wait-ForService "MongoDB" 'docker-compose exec -T mongodb mongosh --eval "db.adminCommand(\"ismaster\")"'

# Wait for Redis
Wait-ForService "Redis" 'docker-compose exec -T redis redis-cli ping'

# Wait for RabbitMQ
Wait-ForService "RabbitMQ" 'docker-compose exec -T rabbitmq rabbitmqctl status'

# Initialize MongoDB
Write-Status "Initializing MongoDB..."
try {
    docker-compose exec -T mongodb mongosh gps_tracking /docker-entrypoint-initdb.d/mongo-init.js | Out-Null
} catch {
    Write-Warning "MongoDB initialization may have already been completed"
}

# Wait for GPS service
Wait-ForService "GPS Service" 'Invoke-RestMethod -Uri "http://localhost:8003/health" -Method Get'

# Display service status
Write-Status "Service Status:"
docker-compose ps

Write-Host ""
Write-Status "GPS Tracking Service started successfully!"
Write-Host ""
Write-Status "Service URLs:"
Write-Host "  • GPS API: http://localhost:8003" -ForegroundColor Cyan
Write-Host "  • API Documentation: http://localhost:8003/docs" -ForegroundColor Cyan
Write-Host "  • Health Check: http://localhost:8003/health" -ForegroundColor Cyan
Write-Host "  • WebSocket: ws://localhost:8003/ws" -ForegroundColor Cyan
Write-Host ""
Write-Status "Management Interfaces:"
Write-Host "  • MongoDB Express: http://localhost:8081" -ForegroundColor Cyan
Write-Host "  • RabbitMQ Management: http://localhost:15672 (gps_service/gps_service_password)" -ForegroundColor Cyan
Write-Host "  • Redis Commander: http://localhost:8082" -ForegroundColor Cyan
Write-Host ""
Write-Status "Logs:"
Write-Host "  • View all logs: docker-compose logs -f" -ForegroundColor Cyan
Write-Host "  • GPS service logs: docker-compose logs -f gps-service" -ForegroundColor Cyan
Write-Host ""
Write-Status "To stop the service: docker-compose down"

# Optional: Open browser to API documentation
if (-not $SkipBrowser) {
    $response = Read-Host "Open API documentation in browser? (y/n)"
    if ($response -eq "y" -or $response -eq "Y") {
        Start-Process "http://localhost:8003/docs"
    }
}
