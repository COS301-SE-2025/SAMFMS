# GPS Tracking Service Setup Guide

This guide will walk you through setting up the GPS Tracking Service for the SAMFMS (Smart Autonomous Fleet Management System).

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Starting the Service](#starting-the-service)
5. [Verification](#verification)
6. [Common Issues](#common-issues)
7. [Next Steps](#next-steps)

## Prerequisites

### Required Software

- **Docker Desktop** (latest version)

  - [Download for Windows](https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe)
  - [Download for macOS](https://desktop.docker.com/mac/main/amd64/Docker.dmg)
  - [Download for Linux](https://docs.docker.com/desktop/install/linux-install/)

- **Git** (for cloning the repository)
  - [Download Git](https://git-scm.com/downloads)

### System Requirements

- **RAM**: Minimum 8GB, Recommended 16GB
- **Storage**: At least 10GB free space
- **CPU**: 2+ cores recommended
- **Network**: Internet connection for downloading images

### Port Requirements

The following ports must be available:

- `8003`: GPS Service API
- `8004`: GPS Service Metrics (optional)
- `27017`: MongoDB
- `6379`: Redis
- `5672`: RabbitMQ AMQP
- `15672`: RabbitMQ Management
- `1883`: MQTT (for IoT devices)
- `8081`: MongoDB Express
- `8082`: Redis Commander

## Installation

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd SAMFMS/Sblocks/gps
```

### Step 2: Verify Docker Installation

```bash
docker --version
docker-compose --version
```

You should see version information for both commands.

### Step 3: Check Available Ports

**Windows (PowerShell):**

```powershell
netstat -an | findstr "8003 27017 6379 5672 15672"
```

**Linux/macOS:**

```bash
netstat -an | grep -E "(8003|27017|6379|5672|15672)"
```

If any ports are in use, you may need to stop other services or modify the port configuration.

## Configuration

### Step 1: Environment Configuration

The startup script will create a default `.env` file, but you can customize it:

```env
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
LOCATION_UPDATE_INTERVAL=30          # seconds
LOCATION_ACCURACY_THRESHOLD=50.0     # meters
ENABLE_REAL_TIME_TRACKING=true

# Geofencing Configuration
GEOFENCE_CHECK_INTERVAL=10           # seconds
GEOFENCE_BUFFER_DISTANCE=10.0        # meters
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
```

### Step 2: Security Configuration

For production environments, make sure to:

1. **Change default passwords** in `docker-compose.yml`
2. **Generate a strong secret key**:
   ```python
   import secrets
   print(secrets.token_urlsafe(32))
   ```
3. **Configure SSL/TLS certificates** if needed

### Step 3: Resource Limits

Adjust Docker resource limits in `docker-compose.yml` based on your system:

```yaml
services:
  gps-service:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'
```

## Starting the Service

### Option 1: Using Startup Scripts (Recommended)

**Linux/macOS:**

```bash
chmod +x start.sh
./start.sh
```

**Windows (PowerShell as Administrator):**

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\start.ps1
```

### Option 2: Manual Docker Compose

```bash
# Create necessary directories
mkdir -p logs data/mongodb data/redis

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### Startup Process

The startup script will:

1. ✅ Check Docker availability
2. ✅ Create necessary directories
3. ✅ Generate default configuration
4. ✅ Pull required Docker images
5. ✅ Build the GPS service image
6. ✅ Start all services
7. ✅ Wait for services to be ready
8. ✅ Initialize the MongoDB database
9. ✅ Verify service health

## Verification

### Step 1: Check Service Status

```bash
docker-compose ps
```

All services should show as "Up":

```
        Name                      Command               State                    Ports
------------------------------------------------------------------------------------------------
gps_gps-service_1        uvicorn main:app --host 0. ...   Up      0.0.0.0:8003->8003/tcp
gps_mongodb_1            docker-entrypoint.sh mongod     Up      0.0.0.0:27017->27017/tcp
gps_rabbitmq_1           docker-entrypoint.sh rabbi ...   Up      0.0.0.0:15672->15672/tcp, ...
gps_redis_1              docker-entrypoint.sh redis ...   Up      0.0.0.0:6379->6379/tcp
```

### Step 2: Health Check

```bash
curl http://localhost:8003/health
```

Expected response:

```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0",
  "services": {
    "database": "connected",
    "redis": "connected",
    "rabbitmq": "connected"
  }
}
```

### Step 3: API Documentation

Open your browser and navigate to:

- **API Docs**: http://localhost:8003/docs
- **ReDoc**: http://localhost:8003/redoc

### Step 4: Management Interfaces

- **MongoDB Express**: http://localhost:8081
- **RabbitMQ Management**: http://localhost:15672
  - Username: `gps_service`
  - Password: `gps_service_password`
- **Redis Commander**: http://localhost:8082

### Step 5: Test Basic Functionality

#### Create a Test Vehicle Location

```bash
curl -X POST "http://localhost:8003/api/locations/update" \
  -H "Content-Type: application/json" \
  -d '{
    "vehicle_id": "TEST001",
    "driver_id": "DRIVER001",
    "latitude": 37.7749,
    "longitude": -122.4194,
    "speed": 45.5,
    "heading": 180.0,
    "accuracy": 10.0
  }'
```

#### Retrieve the Location

```bash
curl "http://localhost:8003/api/locations/vehicle/TEST001/current"
```

#### Test WebSocket Connection

```javascript
// Open browser console and run:
const ws = new WebSocket('ws://localhost:8003/ws/vehicle/TEST001');
ws.onmessage = event => console.log('Received:', JSON.parse(event.data));
ws.onopen = () => console.log('WebSocket connected');
ws.onerror = error => console.error('WebSocket error:', error);
```

## Common Issues

### Issue 1: Port Already in Use

**Error**: `Error starting userland proxy: listen tcp 0.0.0.0:8003: bind: address already in use`

**Solution**:

```bash
# Find what's using the port
lsof -i :8003  # Linux/macOS
netstat -ano | findstr :8003  # Windows

# Stop the conflicting service or change the port in docker-compose.yml
```

### Issue 2: Docker Not Running

**Error**: `Cannot connect to the Docker daemon`

**Solution**:

- Start Docker Desktop
- Ensure Docker daemon is running
- Check Docker service status

### Issue 3: MongoDB Connection Failed

**Error**: `MongoServerError: Authentication failed`

**Solution**:

```bash
# Reset MongoDB data
docker-compose down -v
docker-compose up -d mongodb
# Wait for MongoDB to start, then restart other services
docker-compose up -d
```

### Issue 4: RabbitMQ Management Not Accessible

**Error**: `Connection refused` when accessing http://localhost:15672

**Solution**:

```bash
# Check if RabbitMQ is running
docker-compose logs rabbitmq

# Enable management plugin
docker-compose exec rabbitmq rabbitmq-plugins enable rabbitmq_management
```

### Issue 5: High Memory Usage

**Symptoms**: System becomes slow, Docker containers being killed

**Solution**:

1. Increase Docker memory limits in Docker Desktop settings
2. Reduce resource allocations in `docker-compose.yml`
3. Adjust location history retention settings

### Issue 6: WebSocket Connection Fails

**Error**: `WebSocket connection failed`

**Solution**:

1. Check firewall settings
2. Verify the service is running: `curl http://localhost:8003/health`
3. Test with a WebSocket client tool
4. Check browser console for CORS errors

## Next Steps

### 1. Integration with Frontend

The GPS service is designed to work with the React frontend components:

- `TrackingMap.jsx`: Real-time vehicle tracking
- `GeofenceManager.jsx`: Geofence management
- `LocationHistory.jsx`: Historical location data

### 2. Integration with Trip Planning Service

Configure the GPS service to communicate with the trip planning service:

```env
TRIP_PLANNING_SERVICE_URL=http://trip-planning:8002
```

### 3. Production Deployment

For production deployment:

1. **Security Hardening**:

   - Use strong passwords
   - Enable SSL/TLS
   - Configure firewalls
   - Set up monitoring

2. **Scaling**:

   - Use Docker Swarm or Kubernetes
   - Set up load balancers
   - Configure database clusters

3. **Monitoring**:
   - Set up log aggregation
   - Configure alerts
   - Monitor performance metrics

### 4. Data Management

Configure data retention policies:

```env
LOCATION_HISTORY_RETENTION_DAYS=90
GEOFENCE_EVENTS_RETENTION_DAYS=180
ENABLE_DATA_ARCHIVAL=true
```

### 5. IoT Device Integration

For IoT device integration:

1. Configure MQTT settings
2. Set up device authentication
3. Configure message routing

## Support and Troubleshooting

### Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f gps-service
docker-compose logs -f mongodb
docker-compose logs -f rabbitmq
docker-compose logs -f redis

# View log files
tail -f logs/gps_service.log
```

### Debug Mode

Enable debug mode for more detailed logging:

```env
DEBUG=true
LOG_LEVEL=DEBUG
```

### Performance Monitoring

```bash
# Check container resource usage
docker stats

# Monitor database performance
docker-compose exec mongodb mongosh --eval "db.stats()"

# Check queue status
docker-compose exec rabbitmq rabbitmqctl list_queues
```

### Getting Help

1. Check the [README.md](README.md) for detailed documentation
2. Review API documentation at http://localhost:8003/docs
3. Check service logs for error messages
4. Verify all prerequisites are met
5. Contact the development team

## Conclusion

You should now have a fully functional GPS Tracking Service running. The service provides:

- ✅ Real-time vehicle location tracking
- ✅ Geofencing capabilities
- ✅ Route management
- ✅ WebSocket support for real-time updates
- ✅ Comprehensive API for integration
- ✅ Message queue for event processing
- ✅ Management interfaces for monitoring

The service is ready to integrate with the SAMFMS frontend and other microservices.
