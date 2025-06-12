# GPS Service - Enhanced Microservice

The GPS Service is part of the SAMFMS (Student Affairs Management with Fleet Management System) microservices architecture. This service has been enhanced with comprehensive logging, health monitoring, and performance metrics.

## Features

### 🔍 Enhanced Logging
- **Structured JSON Logging**: All logs are formatted as JSON for easy parsing and aggregation
- **Environment-based Log Levels**: Configure log level via `LOG_LEVEL` environment variable
- **Request/Response Logging**: Automatic logging of HTTP requests and responses with performance metrics
- **Error Tracking**: Detailed error logging with stack traces and context information
- **Performance Monitoring**: Automatic detection and logging of slow requests

### 🏥 Health Monitoring
- **Comprehensive Health Checks**: Multi-component health monitoring
- **Dependency Status**: Real-time status of Redis and RabbitMQ connections
- **System Resources**: Memory, disk space, and CPU usage monitoring
- **Response Time Tracking**: Health check response time measurement

### 📊 Performance Metrics
- **System Metrics**: CPU, memory, and disk usage
- **Process Metrics**: Service-specific resource usage
- **Connection Metrics**: Database and message queue connection status
- **Application Metrics**: Request counts, error rates, and response times

### 🔧 Modular Architecture
- **Separation of Concerns**: Organized into focused modules
- **Reusable Components**: Common functionality extracted into utility modules
- **Clean Code Structure**: Easy to maintain and extend

## Project Structure

```
gps/
├── main.py                 # Main FastAPI application
├── logging_config.py       # Logging configuration and JSON formatter
├── connections.py          # Database and message queue connection management
├── middleware.py           # HTTP middleware for logging and security
├── health_metrics.py       # Health checks and performance metrics
├── utils.py               # Utility functions and common helpers
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker container configuration
├── .env                   # Environment variables (development)
└── README.md              # This documentation
```

## Quick Start

### Prerequisites
- Python 3.8+
- Redis server
- RabbitMQ server
- Docker (optional)

### Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set environment variables:**
```bash
export LOG_LEVEL=INFO
export ENVIRONMENT=development
export REDIS_HOST=localhost
export RABBITMQ_HOST=localhost
```

3. **Run the service:**
```bash
python main.py
```

### Using Docker

1. **Build the image:**
```bash
docker build -t gps-service .
```

2. **Run the container:**
```bash
docker run -p 8000:8000 -e LOG_LEVEL=INFO gps-service
```

## API Endpoints

### Core Endpoints

- `GET /` - Service information and status
- `GET /health` - Comprehensive health check
- `GET /metrics` - Performance metrics
- `GET /docs` - API documentation (development only)

### GPS Endpoints

- `GET /gps/locations` - Retrieve GPS location data
- `POST /gps/locations` - Update GPS location data

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `ENVIRONMENT` | `development` | Environment name (development, staging, production) |
| `SERVICE_NAME` | `gps-service` | Service identifier for logs |
| `REDIS_HOST` | `redis` | Redis server hostname |
| `REDIS_PORT` | `6379` | Redis server port |
| `RABBITMQ_HOST` | `rabbitmq` | RabbitMQ server hostname |
| `RABBITMQ_PORT` | `5672` | RabbitMQ server port |
| `API_HOST` | `0.0.0.0` | API server bind address |
| `API_PORT` | `8000` | API server port |

### Log Configuration

The service uses structured JSON logging with the following format:

```json
{
  "timestamp": "2023-12-07T10:30:00.000Z",
  "level": "INFO",
  "service": "gps-service",
  "environment": "development",
  "logger": "main",
  "message": "Request completed successfully",
  "module": "main",
  "function": "logging_middleware",
  "line": 45,
  "request_id": "req_1701942600000",
  "status_code": 200,
  "duration_ms": 12.5
}
```

## Health Check Response

The `/health` endpoint returns detailed status information:

```json
{
  "service": "gps-service",
  "version": "1.0.0",
  "status": "healthy",
  "timestamp": "2023-12-07T10:30:00.000Z",
  "uptime_seconds": 3600.0,
  "checks": {
    "redis": {
      "status": "healthy",
      "message": "Connection successful"
    },
    "rabbitmq": {
      "status": "healthy",
      "message": "Connection successful"
    },
    "disk": {
      "status": "healthy",
      "message": "Sufficient disk space: 75.2% free",
      "free_percent": 75.2,
      "free_gb": 150.4,
      "total_gb": 200.0
    },
    "memory": {
      "status": "healthy",
      "message": "Normal memory usage: 45.1%",
      "used_percent": 45.1,
      "available_gb": 2.2,
      "total_gb": 4.0
    }
  },
  "response_time_ms": 15.3
}
```

## Metrics Response

The `/metrics` endpoint provides performance data:

```json
{
  "service": "gps-service",
  "version": "1.0.0",
  "timestamp": "2023-12-07T10:30:00.000Z",
  "uptime_seconds": 3600.0,
  "system": {
    "cpu_percent": 25.5,
    "memory_percent": 45.1,
    "disk_percent": 24.8
  },
  "process": {
    "cpu_percent": 2.1,
    "memory_mb": 128.5,
    "memory_percent": 3.2,
    "num_threads": 8
  },
  "connections": {
    "redis": {
      "status": "connected",
      "pool_size": 10
    },
    "rabbitmq": {
      "status": "connected",
      "is_open": true
    }
  }
}
```

## Development

### Adding New Endpoints

1. Add your endpoint function to `main.py`
2. Use the logging utilities for consistent logging
3. Use connection managers for database access
4. Return formatted responses using utility functions

### Extending Health Checks

1. Add new health check functions to `health_metrics.py`
2. Update the `HealthChecker.get_health_status()` method
3. Add appropriate logging for your checks

### Custom Middleware

1. Add new middleware functions to `middleware.py`
2. Register them in `main.py` using `app.middleware("http")`

## Production Deployment

### Docker Compose

```yaml
version: '3.8'
services:
  gps-service:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LOG_LEVEL=INFO
      - ENVIRONMENT=production
      - REDIS_HOST=redis
      - RABBITMQ_HOST=rabbitmq
    depends_on:
      - redis
      - rabbitmq
```

### Log Aggregation

For production deployments, consider using log aggregation tools:

- **ELK Stack**: Elasticsearch, Logstash, and Kibana
- **Fluentd**: For log collection and forwarding
- **Grafana**: For metrics visualization
- **Prometheus**: For metrics collection

## Testing

Run tests with:

```bash
# Unit tests
python -m pytest tests/

# Health check
curl http://localhost:8000/health

# Metrics
curl http://localhost:8000/metrics
```

## Contributing

1. Follow the established code structure
2. Add appropriate logging to new features
3. Update health checks for new dependencies
4. Document any new environment variables
5. Write tests for new functionality

## License

This project is part of the SAMFMS system. See the main project for license information.
