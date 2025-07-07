# SAMFMS Technical Installation Guide

## Table of Contents

- [Overview](#overview)
- [System Requirements](#system-requirements)
- [Prerequisites](#prerequisites)
- [Installation Methods](#installation-methods)
- [Quick Start (Docker)](#quick-start-docker)
- [Development Setup](#development-setup)
- [Manual Installation](#manual-installation)
- [Configuration](#configuration)
- [Service Architecture](#service-architecture)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Production Deployment](#production-deployment)

## Overview

The SAMFMS (Smart Autonomous Fleet Management System) is a comprehensive microservices-based fleet management solution developed by Team Firewall Five. The system consists of:

- **Core Service**: Central API gateway and orchestrator
- **Service Blocks (Sblocks)**: Modular microservices for specific functionality
- **Data Blocks (Dblocks)**: Data management services
- **Frontend**: React-based web interface
- **Infrastructure**: RabbitMQ, MongoDB, Redis for messaging and data storage

## System Requirements

### Minimum Requirements

- **CPU**: 4 cores (Intel i5 or AMD Ryzen 5)
- **RAM**: 8GB (16GB recommended for full system)
- **Storage**: 20GB free space
- **OS**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+)

### Network Requirements

- Internet connection for dependency downloads
- Available ports: 21000-21020 (configurable)

## Prerequisites

### Required Software

1. **Docker** (v20.10+) and **Docker Compose** (v2.0+)
   ```powershell
   # Windows (PowerShell as Administrator)
   winget install Docker.DockerDesktop
   ```
2. **Git** (v2.30+)

   ```powershell
   winget install Git.Git
   ```

3. **Node.js** (v18+) and **npm** (for frontend development)

   ```powershell
   winget install OpenJS.NodeJS
   ```

4. **Python** (v3.9+) for local development
   ```powershell
   winget install Python.Python.3.9
   ```

### Optional Development Tools

- **Visual Studio Code** with Docker and Python extensions
- **Postman** or **Insomnia** for API testing
- **MongoDB Compass** for database management

## Installation Methods

Choose one of the following installation methods based on your needs:

1. **[Quick Start (Docker)](#quick-start-docker)** - Recommended for testing and evaluation
2. **[Development Setup](#development-setup)** - For active development
3. **[Manual Installation](#manual-installation)** - For custom configurations

## Quick Start (Docker)

### 1. Clone the Repository

```powershell
git clone https://github.com/COS301-SE-2025/SAMFMS.git
cd SAMFMS
```

### 2. Configure Environment

```powershell
# Copy environment template
copy .env.example .env

# Edit .env file with your preferred settings (optional)
notepad .env
```

### 3. Start Infrastructure Services

```powershell
# Start core infrastructure
docker-compose up -d rabbitmq mongodb redis

# Wait for services to be ready (30-60 seconds)
docker-compose logs -f rabbitmq
```

### 4. Start Application Services

```powershell
# Start all services
docker-compose up -d

# Check service status
docker-compose ps
```

### 5. Verify Installation

```powershell
# Check Core service
curl http://localhost:21004/health

# Check Service Blocks
curl http://localhost:21005/health  # GPS Service
curl http://localhost:21006/health  # Trip Planning
curl http://localhost:21007/health  # Vehicle Maintenance
curl http://localhost:21008/health  # Security Service
```

### 6. Access the Application

- **Frontend**: http://localhost:3000
- **Core API**: http://localhost:21004
- **API Documentation**: http://localhost:21004/docs
- **RabbitMQ Management**: http://localhost:21001 (samfms_rabbit / RabbitPass2025!)
- **MongoDB**: localhost:21003

## Development Setup

### 1. Clone and Prepare Repository

```powershell
git clone https://github.com/COS301-SE-2025/SAMFMS.git
cd SAMFMS

# Install development dependencies
npm install
```

### 2. Set Up Python Virtual Environment

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Upgrade pip
python -m pip install --upgrade pip
```

### 3. Install Core Dependencies

```powershell
# Navigate to Core service
cd Core

# Install Python dependencies
pip install -r requirements.txt

# Return to root
cd ..
```

### 4. Install Service Block Dependencies

```powershell
# Install dependencies for each service block
cd Sblocks/security
pip install -r requirements.txt
cd ../..

cd Sblocks/gps
pip install -r requirements.txt
cd ../..

cd Sblocks/management
pip install -r requirements.txt
cd ../..

cd Sblocks/vehicle_maintenance
pip install -r requirements.txt
cd ../..

cd Sblocks/trip_planning
pip install -r requirements.txt
cd ../..

cd Sblocks/utilities
pip install -r requirements.txt
cd ../..
```

### 5. Start Infrastructure in Development Mode

```powershell
# Start only infrastructure services for development
docker-compose up -d rabbitmq mongodb redis

# Wait for services to initialize
timeout /t 30
```

### 6. Run Services Locally

Open multiple terminal windows/tabs:

```powershell
# Terminal 1: Core Service
cd Core
python main.py

# Terminal 2: Security Service
cd Sblocks/security
python main.py

# Terminal 3: GPS Service
cd Sblocks/gps
python main.py

# Terminal 4: Management Service
cd Sblocks/management
python main.py

# Terminal 5: Frontend (if developing UI)
cd Frontend/samfms
npm install
npm start
```

## Manual Installation

### 1. Install Infrastructure Services

#### MongoDB

```powershell
# Download and install MongoDB Community Server
# Configure with authentication enabled
mongod --auth --port 27017
```

#### RabbitMQ

```powershell
# Download and install RabbitMQ Server
# Enable management plugin
rabbitmq-plugins enable rabbitmq_management
```

#### Redis

```powershell
# Download and install Redis
redis-server --port 6379
```

### 2. Configure Services

Create configuration files for each service:

```yaml
# config/mongodb.conf
storage:
  dbPath: ./data/db
net:
  port: 27017
security:
  authorization: enabled
```

### 3. Install Application Dependencies

Follow the Python dependency installation from the Development Setup section.

### 4. Configure Environment Variables

Set the following environment variables:

```powershell
# Database Configuration
set MONGODB_URL=mongodb://username:password@localhost:27017
set REDIS_HOST=localhost
set REDIS_PORT=6379

# Message Queue Configuration
set RABBITMQ_URL=amqp://username:password@localhost:5672/
set RABBITMQ_HOST=localhost
set RABBITMQ_PORT=5672

# Service Configuration
set ENVIRONMENT=development
set LOG_LEVEL=INFO
set JWT_SECRET_KEY=your-secret-key-here
```

## Configuration

### Environment Variables

The system supports extensive configuration through environment variables:

#### Core Service Configuration

```env
# Database
MONGODB_URL=mongodb://user:pass@host:port/db
DATABASE_NAME=samfms_core

# Authentication
JWT_SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=15

# Message Queue
RABBITMQ_URL=amqp://user:pass@host:port/
RABBITMQ_CONNECTION_RETRY_ATTEMPTS=30
RABBITMQ_CONNECTION_RETRY_DELAY=2

# Service Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO
SERVICE_STARTUP_DELAY=10
```

#### Service Block Configuration

```env
# Each service block supports similar configuration
MONGODB_URL=mongodb://user:pass@host:port/db
DATABASE_NAME=samfms_service_name
RABBITMQ_URL=amqp://user:pass@host:port/
REDIS_HOST=redis
REDIS_PORT=6379
```

### Port Configuration

Default port assignments:

| Service             | Default Port | Environment Variable             |
| ------------------- | ------------ | -------------------------------- |
| Core                | 21004        | CORE_PORT                        |
| GPS                 | 21005        | GPS_SERVICE_PORT                 |
| Trip Planning       | 21006        | TRIP_PLANNING_SERVICE_PORT       |
| Vehicle Maintenance | 21007        | VEHICLE_MAINTENANCE_SERVICE_PORT |
| Security            | 21008        | SECURITY_SERVICE_PORT            |
| Management          | 21009        | MANAGEMENT_SERVICE_PORT          |
| Utilities           | 21010        | UTILITIES_SERVICE_PORT           |
| RabbitMQ            | 21000        | RABBITMQ_PORT                    |
| RabbitMQ Management | 21001        | RABBITMQ_MANAGEMENT_PORT         |
| Redis               | 21002        | REDIS_EXTERNAL_PORT              |
| MongoDB             | 21003        | MONGODB_PORT                     |

## Service Architecture

### Core Service (`Core/`)

- **Purpose**: API Gateway and request router
- **Key Components**:
  - `main.py`: FastAPI application entry point
  - `routes/`: API endpoint definitions
  - `services/`: Business logic and routing
  - `middleware/`: Cross-cutting concerns
- **Dependencies**: FastAPI, Motor (MongoDB), aio-pika (RabbitMQ)

### Service Blocks (`Sblocks/`)

#### Security Service (`Sblocks/security/`)

- **Purpose**: Authentication and authorization
- **Features**: JWT tokens, role-based access, user management
- **Dependencies**: FastAPI, PyJWT, Passlib, Motor

#### GPS Service (`Sblocks/gps/`)

- **Purpose**: Vehicle tracking and location management
- **Features**: Real-time tracking, geofencing, route optimization
- **Dependencies**: FastAPI, Motor, Redis, aio-pika

#### Management Service (`Sblocks/management/`)

- **Purpose**: Fleet and resource management
- **Features**: Vehicle assignments, driver management, reporting
- **Dependencies**: FastAPI, Motor, aio-pika

#### Trip Planning Service (`Sblocks/trip_planning/`)

- **Purpose**: Route planning and optimization
- **Features**: Route calculation, optimization algorithms
- **Dependencies**: FastAPI, Motor, aio-pika

#### Vehicle Maintenance Service (`Sblocks/vehicle_maintenance/`)

- **Purpose**: Maintenance scheduling and tracking
- **Features**: Maintenance schedules, service records, alerts
- **Dependencies**: FastAPI, Motor, aio-pika

#### Utilities Service (`Sblocks/utilities/`)

- **Purpose**: Common utilities and notifications
- **Features**: Email service, notifications, file handling
- **Dependencies**: FastAPI, SMTP libraries, aio-pika

### Data Blocks (`Dblocks/`)

- **GPS Data Block**: GPS-specific data operations
- **Users Data Block**: User data management
- **Vehicles Data Block**: Vehicle data operations

## Testing

### Automated Testing

```powershell
# Run all tests
npm test

# Run specific service tests
cd Sblocks/security
run-tests.bat

# Run with coverage
run-tests.bat --coverage
```

### Manual Testing

```powershell
# Test Core service
curl http://localhost:21004/health
curl http://localhost:21004/docs

# Test authentication
curl -X POST http://localhost:21008/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'
```

### Integration Testing

```powershell
# Test communication architecture
python test_communication_architecture.py

# Test specific endpoints
python scripts/test_endpoints.py
```

## Troubleshooting

### Common Issues

#### 1. Docker Build Failures

```powershell
# Clear Docker cache
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache
```

#### 2. Port Conflicts

```powershell
# Check port usage
netstat -an | findstr "21000"

# Stop conflicting services
docker-compose down
```

#### 3. Database Connection Issues

```powershell
# Check MongoDB status
docker logs mongodb

# Test database connection
docker exec -it mongodb mongo --eval "db.runCommand({ping: 1})"
```

#### 4. RabbitMQ Connection Issues

```powershell
# Check RabbitMQ status
docker logs rabbitmq

# Access management interface
# http://localhost:21001 (samfms_rabbit / RabbitPass2025!)
```

#### 5. Service Startup Issues

```powershell
# Check service logs
docker-compose logs core
docker-compose logs gps

# Restart specific service
docker-compose restart core
```

### Log Analysis

```powershell
# View real-time logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f core gps security

# Export logs for analysis
docker-compose logs > samfms-logs.txt
```

### Performance Issues

```powershell
# Monitor resource usage
docker stats

# Check service health
curl http://localhost:21004/health
curl http://localhost:21005/metrics
```

## Production Deployment

### Security Hardening

1. **Change Default Passwords**

   ```env
   MONGODB_PASSWORD=secure_production_password
   RABBITMQ_PASSWORD=secure_production_password
   JWT_SECRET_KEY=secure_random_key_256_bits
   ```

2. **Enable SSL/TLS**

   ```powershell
   # Use provided SSL configuration
   docker-compose -f docker-compose.ssl.yml up -d
   ```

3. **Configure Firewall**
   ```powershell
   # Allow only necessary ports
   # 21004 (Core API), 21001 (RabbitMQ Management - restrict access)
   ```

### Scaling Configuration

```yaml
# docker-compose.prod.yml
services:
  core:
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M

  gps:
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 256M
```

### Monitoring Setup

```powershell
# Enable health checks
curl http://localhost:21004/health
curl http://localhost:21005/metrics

# Set up log aggregation
docker-compose -f docker-compose.monitoring.yml up -d
```

### Backup Strategy

```powershell
# Database backup
docker exec mongodb mongodump --out /backup/$(date +%Y%m%d)

# Configuration backup
cp -r config/ backup/config-$(date +%Y%m%d)/
```

### Load Balancing

For production deployments, consider using:

- **NGINX** for reverse proxy and load balancing
- **HAProxy** for advanced load balancing
- **Docker Swarm** or **Kubernetes** for container orchestration

## Support and Documentation

- **Project Repository**: https://github.com/COS301-SE-2025/SAMFMS
- **Communication Architecture**: [docs/Communication_Architecture.md](Communication_Architecture.md)
- **Quick Start Guide**: [docs/Quick_Start_Communication_Architecture.md](Quick_Start_Communication_Architecture.md)
- **Developer Guide**: [docs/Developer_Docker_Guide.md](Developer_Docker_Guide.md)
- **API Documentation**: Available at `/docs` endpoint of each service

## Version Information

- **System Version**: 1.0.0
- **Python**: 3.9+
- **Docker**: 20.10+
- **Node.js**: 18+

---

**Last Updated**: July 2025  
**Authors**: Team Firewall Five  
**License**: See main project repository
