# SAMFMS Communication Architecture - Quick Start Guide

## Prerequisites

- Docker and Docker Compose
- Python 3.9+
- Git

## Quick Start

### 1. Start Infrastructure Services

```powershell
# Start RabbitMQ, MongoDB, and Redis
docker-compose up -d rabbitmq mongodb redis
```

### 2. Start Core Service

```powershell
cd Core
pip install -r requirements.txt
python main.py
```

### 3. Start Service Blocks

In separate terminals:

```powershell
# Management Service
cd Sblocks/management
pip install -r requirements.txt
python main.py

# GPS Service
cd Sblocks/gps
pip install -r requirements.txt
python main.py

# Trip Planning Service
cd Sblocks/trip_planning
pip install -r requirements.txt
python main.py

# Vehicle Maintenance Service
cd Sblocks/vehicle_maintainence
pip install -r requirements.txt
python main.py
```

### 4. Test the Architecture

#### Manual Testing

```powershell
# Test Core health
curl http://localhost:8080/health

# Test service health
curl http://localhost:8001/health  # Management
curl http://localhost:8002/health  # GPS
curl http://localhost:8003/health  # Trip Planning
curl http://localhost:8004/health  # Vehicle Maintenance
```

#### Automated Testing

```powershell
python test_communication_architecture.py
```

## Verification Checklist

- [ ] All services start without errors
- [ ] RabbitMQ queues are created (`management.requests`, `gps.requests`, etc.)
- [ ] Core can route requests to service blocks
- [ ] Responses are properly correlated and returned
- [ ] Circuit breaker and retry mechanisms work
- [ ] Authentication and authorization flow works

## Common Issues

### RabbitMQ Connection Failed

- Ensure RabbitMQ is running: `docker ps | grep rabbitmq`
- Check RabbitMQ logs: `docker logs rabbitmq`

### Service Not Responding

- Check service logs for errors
- Verify all dependencies are installed
- Check port conflicts

### Request Timeout

- Increase timeout values in configuration
- Check service performance and load

## Service Ports

- Core: 8080
- Management: 8001
- GPS: 8002
- Trip Planning: 8003
- Vehicle Maintenance: 8004
- Security: 8005
- RabbitMQ Management: 15672
- MongoDB: 27017
- Redis: 6379

## Next Steps

1. Review the detailed architecture documentation in `Communication_Architecture.md`
2. Implement additional endpoints as needed
3. Add comprehensive error handling and monitoring
4. Set up production deployment with proper scaling
