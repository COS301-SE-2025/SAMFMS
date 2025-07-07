# SAMFMS Docker System - Developer Guide

**Last Updated:** May 30, 2025  
**System Status:** ✅ Operational  
**Docker Compose Version:** 3.8+

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [System Architecture](#system-architecture)
4. [Service Details](#service-details)
5. [Health Monitoring](#health-monitoring)
6. [Debugging Guide](#debugging-guide)
7. [Common Issues & Solutions](#common-issues--solutions)
8. [Development Workflow](#development-workflow)
9. [Testing & Validation](#testing--validation)
10. [Logging & Monitoring](#logging--monitoring)

## 🛠️ Prerequisites

### Required Software

- **Docker Desktop:** Version 4.0+ with WSL2 backend (Windows)
- **Docker Compose:** Version 2.0+
- **Git:** For version control
- **PowerShell:** Windows default shell
- **Text Editor:** VS Code recommended

### System Requirements

- **RAM:** Minimum 8GB (16GB recommended)
- **Disk Space:** At least 10GB free
- **CPU:** Multi-core processor recommended
- **Network:** Internet access for Docker image pulls

### Verify Installation

```powershell
# Check Docker installation
docker --version
docker-compose --version

# Verify Docker is running
docker ps

# Check available resources
docker system df
```

## 🚀 Quick Start

### 1. Clone and Navigate

```powershell
git clone <repository-url>
cd SAMFMS
```

### 2. Build and Start All Services

```powershell
# Build all images (first time or after code changes)
docker-compose build

# Start all services in detached mode
docker-compose up -d

# View startup logs
docker-compose logs -f
```

### 3. Verify System Health

```powershell
# Check all containers are running
docker-compose ps

# Quick health check
curl http://localhost:8001/health  # GPS Service
curl http://localhost:8002/health  # Trip Planning
curl http://localhost:8004/health  # Vehicle Maintenance
curl http://localhost:8000/health  # Core API
```

### 4. Access Services

- **GPS Service:** http://localhost:8001
- **Trip Planning:** http://localhost:8002
- **Vehicle Maintenance:** http://localhost:8004
- **Core API:** http://localhost:8000
- **RabbitMQ Management:** http://localhost:15672 (guest/guest)

## 🏗️ System Architecture

### Infrastructure Services

| Service                         | Container                              | Port(s)     | Purpose             |
| ------------------------------- | -------------------------------------- | ----------- | ------------------- |
| **RabbitMQ**                    | `samfms-rabbitmq-1`                    | 5672, 15672 | Message queuing     |
| **Redis**                       | `samfms-redis-1`                       | 6379        | Caching & sessions  |
| **MongoDB Core**                | `samfms-mongodb_core-1`                | 27017       | Core API data       |
| **MongoDB GPS**                 | `samfms-mongodb_gps-1`                 | 27018       | GPS tracking data   |
| **MongoDB Trip Planning**       | `samfms-mongodb_trip_planning-1`       | 27019       | Route planning data |
| **MongoDB Vehicle Maintenance** | `samfms-mongodb_vehicle_maintenance-1` | 27020       | Maintenance records |

### Application Services

| Service                 | Container                              | Port | Health Endpoint |
| ----------------------- | -------------------------------------- | ---- | --------------- |
| **GPS Service**         | `samfms-gps_service-1`                 | 8001 | `/health`       |
| **Trip Planning**       | `samfms-trip_planning_service-1`       | 8002 | `/health`       |
| **Vehicle Maintenance** | `samfms-vehicle_maintenance_service-1` | 8004 | `/health`       |
| **Core API**            | `samfms-mcore-1`                       | 8000 | `/health`       |
| **Utilities**           | `samfms-utilities_service-1`           | 8005 | `/health`       |
| **Security**            | `samfms-security_service-1`            | 8006 | `/health`       |
| **Management**          | `samfms-management_service-1`          | 8007 | `/health`       |
| **Micro Frontend**      | `samfms-micro_frontend_service-1`      | 8008 | `/health`       |

### Data Block Services

| Service         | Container                      | Port | Purpose                 |
| --------------- | ------------------------------ | ---- | ----------------------- |
| **Users DB**    | `samfms-users_db_service-1`    | 8009 | User data management    |
| **Vehicles DB** | `samfms-vehicles_db_service-1` | 8010 | Vehicle data management |
| **GPS DB**      | `samfms-gps_db_service-1`      | 8011 | GPS data management     |

## 📊 Service Details

### Enhanced Services (Python Startup Scripts)

These services use robust Python startup scripts with dependency management:

- **GPS Service** (`Sblocks/gps/`)
- **Trip Planning** (`Sblocks/trip_planning/`)
- **Vehicle Maintenance** (`Sblocks/vehicle_maintainence/`)

**Features:**

- ✅ Automatic dependency waiting
- ✅ Connection health checks
- ✅ Structured JSON logging
- ✅ Performance metrics
- ✅ Error handling and recovery

### Standard Services (Shell Scripts)

Other services use traditional shell scripts but are fully functional:

- **Core API** (`Core/`)
- **Data Block Services** (`Dblocks/`)
- **Other Sblock Services** (`Sblocks/`)

## 🔍 Health Monitoring

### Health Check Endpoints

All services provide standardized health endpoints:

```powershell
# Check individual service health
curl http://localhost:8001/health | ConvertFrom-Json
curl http://localhost:8002/health | ConvertFrom-Json
curl http://localhost:8004/health | ConvertFrom-Json

# Check metrics
curl http://localhost:8001/metrics | ConvertFrom-Json
```

### Health Status Interpretation

```json
{
  "status": "healthy", // healthy | degraded | unhealthy
  "timestamp": "2025-05-30T...",
  "uptime_seconds": 3600,
  "service": "gps",
  "metrics": {
    "cpu_percent": 25.5,
    "memory_percent": 45.2,
    "request_count": 150,
    "error_count": 2,
    "error_rate": 0.013
  },
  "checks": {
    "database": "healthy",
    "disk_space": "healthy",
    "memory": "healthy",
    "cpu": "healthy"
  }
}
```

### System-Wide Health Check

```powershell
# Custom health check script
$services = @(8001, 8002, 8004, 8000)
foreach ($port in $services) {
    try {
        $response = Invoke-RestMethod "http://localhost:$port/health"
        Write-Host "Port $port : $($response.status)" -ForegroundColor Green
    } catch {
        Write-Host "Port $port : FAILED" -ForegroundColor Red
    }
}
```

## 🐛 Debugging Guide

### Container Debugging Commands

```powershell
# View all containers and their status
docker-compose ps

# View logs for specific service
docker-compose logs gps_service
docker-compose logs -f trip_planning_service  # Follow logs

# View last 50 lines of logs
docker-compose logs --tail=50 vehicle_maintenance_service

# Execute commands inside container
docker-compose exec gps_service bash
docker-compose exec mongodb_core mongosh

# Inspect container details
docker inspect samfms-gps_service-1

# View container resource usage
docker stats
```

### Log Analysis

#### Structured JSON Logs (Enhanced Services)

```powershell
# View structured logs with filtering
docker-compose logs gps_service | Select-String "event_type"
docker-compose logs gps_service | Select-String "http_request"
docker-compose logs gps_service | Select-String "ERROR"
```

#### Log File Locations (Inside Containers)

- **Enhanced Services:** `/app/logs/{service_name}.log`
- **Standard Services:** Container stdout/stderr

### Network Debugging

```powershell
# View Docker networks
docker network ls

# Inspect SAMFMS network
docker network inspect samfms_default

# Test connectivity between containers
docker-compose exec gps_service ping rabbitmq
docker-compose exec gps_service ping mongodb_gps
```

### Database Debugging

```powershell
# Connect to MongoDB instances
docker-compose exec mongodb_core mongosh
docker-compose exec mongodb_gps mongosh --port 27018
docker-compose exec mongodb_trip_planning mongosh --port 27019

# Connect to Redis
docker-compose exec redis redis-cli

# View RabbitMQ management interface
# Open http://localhost:15672 (guest/guest)
```

## ⚠️ Common Issues & Solutions

### 1. Container Startup Failures

**Symptoms:**

- Container exits immediately
- "Connection refused" errors
- Dependency timeout errors

**Solutions:**

```powershell
# Check container logs
docker-compose logs [service_name]

# Rebuild images
docker-compose build --no-cache [service_name]

# Restart with fresh containers
docker-compose down
docker-compose up -d
```

### 2. Port Conflicts

**Symptoms:**

- "Port already in use" errors
- Cannot bind to port

**Solutions:**

```powershell
# Check what's using the port
netstat -ano | findstr :[PORT_NUMBER]

# Kill process using port (if safe)
taskkill /PID [PID_NUMBER] /F

# Or change port in docker-compose.yml
```

### 3. MongoDB Connection Issues

**Symptoms:**

- "Connection timeout" in service logs
- Services stuck in dependency waiting

**Solutions:**

```powershell
# Check MongoDB container status
docker-compose ps | findstr mongodb

# Restart MongoDB services
docker-compose restart mongodb_core mongodb_gps mongodb_trip_planning

# Check MongoDB logs
docker-compose logs mongodb_core
```

### 4. Memory/Resource Issues

**Symptoms:**

- Containers randomly stopping
- Slow performance
- "Out of memory" errors

**Solutions:**

```powershell
# Check Docker resource usage
docker stats

# Increase Docker Desktop memory allocation
# Docker Desktop → Settings → Resources → Advanced

# Clean up unused resources
docker system prune -f
docker volume prune -f
```

### 5. Line Ending Issues (Windows)

**Symptoms:**

- "end of file unexpected" errors
- ": not found" in shell scripts

**Solutions:**

```powershell
# Already fixed in enhanced services with Python startup scripts
# For remaining services, convert line endings:
git config core.autocrlf false
git add . -u
git commit -m "Fix line endings"
```

## 🔄 Development Workflow

### Making Code Changes

1. **Edit Code:** Make changes to service files
2. **Rebuild Service:**
   ```powershell
   docker-compose build [service_name]
   ```
3. **Restart Service:**
   ```powershell
   docker-compose restart [service_name]
   ```
4. **Test Changes:**
   ```powershell
   curl http://localhost:[port]/health
   ```

### Adding New Dependencies

1. **Update requirements.txt** in service directory
2. **Rebuild container:**
   ```powershell
   docker-compose build [service_name] --no-cache
   ```
3. **Restart service:**
   ```powershell
   docker-compose restart [service_name]
   ```

### Database Migrations

```powershell
# For Core MongoDB
docker-compose exec mongodb_core mongosh
# Run your migration scripts

# For service-specific databases
docker-compose exec mongodb_gps mongosh --port 27018
```

## ✅ Testing & Validation

### Automated Health Checks

```powershell
# Create test script: test_health.ps1
$endpoints = @{
    "GPS Service" = "http://localhost:8001/health"
    "Trip Planning" = "http://localhost:8002/health"
    "Vehicle Maintenance" = "http://localhost:8004/health"
    "Core API" = "http://localhost:8000/health"
}

foreach ($service in $endpoints.Keys) {
    try {
        $response = Invoke-RestMethod $endpoints[$service]
        $status = $response.status
        Write-Host "$service : $status" -ForegroundColor $(if($status -eq "healthy"){"Green"}else{"Red"})
    } catch {
        Write-Host "$service : ERROR - $($_.Exception.Message)" -ForegroundColor Red
    }
}
```

### API Testing

```powershell
# Test Core API endpoints
curl http://localhost:8000/
curl http://localhost:8000/users
curl http://localhost:8000/vehicles

# Test service-specific endpoints
curl http://localhost:8001/
curl http://localhost:8002/
curl http://localhost:8004/
```

### Load Testing

```powershell
# Simple load test with PowerShell
1..100 | ForEach-Object -Parallel {
    Invoke-RestMethod "http://localhost:8001/health"
} -ThrottleLimit 10
```

## 📈 Logging & Monitoring

### Centralized Logging

**Enhanced Services** (GPS, Trip Planning, Vehicle Maintenance):

- Structured JSON logging
- Multiple log levels (DEBUG, INFO, WARN, ERROR)
- Event-based logging with context

**Viewing Structured Logs:**

```powershell
# Filter by event type
docker-compose logs gps_service | Select-String "http_request"
docker-compose logs gps_service | Select-String "service_startup"

# Filter by log level
docker-compose logs gps_service | Select-String '"level":"ERROR"'
```

### Performance Monitoring

```powershell
# Get service metrics
curl http://localhost:8001/metrics | ConvertFrom-Json
curl http://localhost:8002/metrics | ConvertFrom-Json
curl http://localhost:8004/metrics | ConvertFrom-Json

# Monitor container resources
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
```

### Log Rotation and Cleanup

```powershell
# Clean up Docker logs
docker system prune -f

# For enhanced services, logs are in /app/logs/ inside containers
docker-compose exec gps_service ls -la /app/logs/
```

## 🔧 Maintenance Commands

### Regular Maintenance

```powershell
# Weekly cleanup
docker system prune -f
docker volume prune -f

# Update all images
docker-compose pull
docker-compose build --no-cache
docker-compose up -d

# Backup databases
docker-compose exec mongodb_core mongodump --out /backup
docker-compose exec mongodb_gps mongodump --out /backup
```

### Emergency Procedures

```powershell
# Complete system restart
docker-compose down
docker system prune -f
docker-compose up -d

# Reset all data (DESTRUCTIVE)
docker-compose down -v  # Removes volumes
docker-compose up -d

# Check system after restart
docker-compose ps
curl http://localhost:8001/health
```

## 📞 Support & Troubleshooting

### Getting Help

1. **Check this guide first** for common issues
2. **Review container logs** for error details
3. **Check health endpoints** for service status
4. **Verify system resources** (memory, disk, CPU)
5. **Test network connectivity** between services

### Reporting Issues

When reporting issues, include:

1. **Error messages** from logs
2. **Container status** (`docker-compose ps`)
3. **System resources** (`docker stats`)
4. **Steps to reproduce** the issue
5. **Environment details** (OS, Docker version)

### Emergency Contacts

- **Infrastructure Issues:** Check Docker Desktop status
- **Service Issues:** Review individual service logs
- **Database Issues:** Check MongoDB container health
- **Network Issues:** Verify Docker network configuration

---

## 📋 Quick Reference

### Essential Commands

```powershell
# Start system
docker-compose up -d

# Stop system
docker-compose down

# View status
docker-compose ps

# View logs
docker-compose logs -f [service_name]

# Restart service
docker-compose restart [service_name]

# Rebuild service
docker-compose build [service_name]

# Health check
curl http://localhost:[port]/health
```

### Service Ports Quick Reference

- **8000:** Core API
- **8001:** GPS Service
- **8002:** Trip Planning
- **8004:** Vehicle Maintenance
- **8005:** Utilities
- **8006:** Security
- **8007:** Management
- **8008:** Micro Frontend
- **8009:** Users DB
- **8010:** Vehicles DB
- **8011:** GPS DB
- **15672:** RabbitMQ Management UI

---

**Status:** ✅ **SYSTEM OPERATIONAL**  
**Last Validated:** May 30, 2025  
**Next Review:** June 15, 2025
