# Trip Planning Service

A comprehensive trip planning and fleet management microservice built with FastAPI and MongoDB. This service handles trip scheduling, vehicle management, driver allocation, route optimization, and real-time communication with the MCore system via RabbitMQ.

## Features

### Core Functionality

- **Trip Management**: Complete CRUD operations for trip planning and tracking
- **Vehicle Management**: Fleet tracking, maintenance scheduling, and performance monitoring
- **Driver Management**: Driver profiles, license tracking, performance metrics, and availability
- **Route Optimization**: Intelligent route planning with distance and time calculations
- **Schedule Management**: Conflict detection, resource allocation, and automatic rescheduling

### Advanced Features

- **Real-time Communication**: RabbitMQ integration for event-driven architecture
- **Performance Analytics**: Comprehensive metrics and reporting
- **Conflict Resolution**: Automatic detection and resolution of scheduling conflicts
- **Resource Optimization**: Intelligent allocation of drivers and vehicles
- **Maintenance Tracking**: Proactive maintenance scheduling and alerts

## Architecture

```
Trip Planning Service
├── FastAPI Application (main.py)
├── Database Layer (MongoDB)
├── Services Layer
│   ├── TripService
│   ├── VehicleService
│   ├── DriverService
│   ├── RouteService
│   └── ScheduleService
├── API Routes
├── Messaging (RabbitMQ)
└── Utilities
    ├── Route Optimization
    ├── Scheduling Algorithms
    └── Data Validation
```

## Prerequisites

### Required Software

- Python 3.9 or higher
- MongoDB 4.4 or higher
- RabbitMQ 3.8 or higher
- Redis 6.0 or higher (optional, for caching)

### Development Tools

- Git
- Docker and Docker Compose (optional)
- VS Code or preferred IDE

## Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd SAMFMS/Sblocks/trip_planning
```

### 2. Create Virtual Environment

```bash
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1

# Or using conda
conda create -n trip-planning python=3.9
conda activate trip-planning
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

```bash
# Copy environment template
Copy-Item .env.example .env

# Edit .env file with your configurations
notepad .env
```

### 5. Database Setup

#### MongoDB

1. Install MongoDB or use Docker:

```bash
# Using Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Or install locally from https://www.mongodb.com/try/download/community
```

2. Verify MongoDB connection:

```bash
# Test connection
mongosh mongodb://localhost:27017
```

#### RabbitMQ

1. Install RabbitMQ or use Docker:

```bash
# Using Docker
docker run -d -p 5672:5672 -p 15672:15672 --name rabbitmq rabbitmq:3-management

# Or install locally from https://www.rabbitmq.com/download.html
```

2. Access RabbitMQ Management UI:

- URL: http://localhost:15672
- Username: guest
- Password: guest

### 6. Redis (Optional)

```bash
# Using Docker
docker run -d -p 6379:6379 --name redis redis:latest

# Or install locally
```

## Running the Service

### Development Mode

```bash
# Start the service with auto-reload
python main.py

# Or using uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8003 --reload
```

### Production Mode

```bash
# Set environment
$env:ENVIRONMENT="production"

# Run with production settings
uvicorn main:app --host 0.0.0.0 --port 8003 --workers 4
```

### Using Docker

```bash
# Build the image
docker build -t trip-planning-service .

# Run the container
docker run -d -p 8003:8003 --name trip-planning trip-planning-service
```

### Using Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f trip-planning

# Stop services
docker-compose down
```

## API Documentation

Once the service is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8003/docs
- **ReDoc**: http://localhost:8003/redoc
- **OpenAPI JSON**: http://localhost:8003/openapi.json

## Service Endpoints

### Health Check

- `GET /health` - Service health status

### Trip Management

- `GET /api/v1/trips` - List all trips
- `POST /api/v1/trips` - Create new trip
- `GET /api/v1/trips/{id}` - Get trip details
- `PUT /api/v1/trips/{id}` - Update trip
- `DELETE /api/v1/trips/{id}` - Cancel trip

### Vehicle Management

- `GET /api/v1/vehicles` - List all vehicles
- `POST /api/v1/vehicles` - Add new vehicle
- `GET /api/v1/vehicles/{id}` - Get vehicle details
- `PUT /api/v1/vehicles/{id}` - Update vehicle
- `PUT /api/v1/vehicles/{id}/location` - Update vehicle location

### Driver Management

- `GET /api/v1/drivers` - List all drivers
- `POST /api/v1/drivers` - Add new driver
- `GET /api/v1/drivers/{id}` - Get driver details
- `PUT /api/v1/drivers/{id}` - Update driver
- `GET /api/v1/drivers/available` - Get available drivers

### Route Management

- `GET /api/v1/routes` - List all routes
- `POST /api/v1/routes` - Create new route
- `POST /api/v1/routes/optimize` - Optimize route
- `GET /api/v1/routes/{id}/metrics` - Get route metrics

### Schedule Management

- `GET /api/v1/schedules` - List all schedules
- `POST /api/v1/schedules` - Create new schedule
- `GET /api/v1/schedules/conflicts` - Check for conflicts
- `POST /api/v1/schedules/optimize` - Optimize schedules

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test files
pytest tests/test_services.py -v
```

### Test Environment

Tests use a separate database (`trip_planning_test_db`) to avoid conflicts with development data.

## Configuration

### Environment Variables

Key configuration options in `.env`:

```env
# Service
DEBUG=true
HOST=0.0.0.0
PORT=8003

# Database
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=trip_planning_db

# Messaging
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
EXCHANGE_NAME=mcore_exchange

# Security
SECRET_KEY=your-secret-key-here
```

### Configuration Classes

- `DevelopmentSettings` - Debug enabled, verbose logging
- `ProductionSettings` - Security focused, minimal logging
- `TestSettings` - Isolated test environment

## Monitoring & Logging

### Health Monitoring

```bash
# Check service health
curl http://localhost:8003/health
```

### Log Levels

- `DEBUG` - Detailed debugging information
- `INFO` - General operational messages
- `WARNING` - Warning conditions
- `ERROR` - Error conditions

### Metrics

The service provides comprehensive metrics for:

- Trip completion rates
- Vehicle utilization
- Driver performance
- Route efficiency
- System performance

## Integration with MCore

The service communicates with MCore through RabbitMQ events:

### Published Events

- `trip.created` - New trip scheduled
- `trip.status_changed` - Trip status updates
- `vehicle.location_updated` - Real-time vehicle tracking
- `driver.assigned_to_trip` - Driver assignments
- `schedule.conflict_detected` - Scheduling conflicts

### Event Format

```json
{
  "event_type": "trip.created",
  "data": {
    "trip_id": "60f7b3b3b3b3b3b3b3b3b3b3",
    "status": "scheduled",
    "timestamp": "2025-05-26T10:30:00Z"
  }
}
```

## Troubleshooting

### Common Issues

1. **Database Connection Failed**

   - Verify MongoDB is running: `docker ps` or check service status
   - Check connection string in `.env`
   - Ensure firewall allows port 27017

2. **RabbitMQ Connection Failed**

   - Verify RabbitMQ is running
   - Check credentials and connection string
   - Ensure port 5672 is accessible

3. **Import Errors**

   - Activate virtual environment
   - Install dependencies: `pip install -r requirements.txt`
   - Check Python path

4. **Port Already in Use**
   - Change port in `.env`: `PORT=8004`
   - Or stop conflicting service

### Debug Mode

Enable debug mode for detailed error messages:

```env
DEBUG=true
LOG_LEVEL=DEBUG
```

### Service Logs

```bash
# View real-time logs
docker-compose logs -f trip-planning

# Or check application logs
tail -f logs/trip-planning.log
```

## Performance Optimization

### Database Indexing

Key indexes are automatically created for:

- Trip queries by status and date
- Vehicle queries by status and location
- Driver queries by status and availability
- Route optimization queries

### Caching

Redis caching is implemented for:

- Frequently accessed routes
- Driver availability status
- Vehicle location data
- Performance metrics

### Async Operations

All database and messaging operations are asynchronous for better performance.

## Security Considerations

### Production Deployment

1. Change default SECRET_KEY
2. Use secure database credentials
3. Enable SSL/TLS for all connections
4. Implement rate limiting
5. Use environment-specific configurations
6. Regular security updates

### API Security

- Input validation on all endpoints
- Request size limits
- CORS configuration
- Authentication tokens (if implemented)

## Development Guidelines

### Code Style

- Follow PEP 8 guidelines
- Use type hints
- Document functions and classes
- Write comprehensive tests

### Git Workflow

- Use feature branches
- Write descriptive commit messages
- Include tests with new features
- Update documentation

## Support & Contributing

### Getting Help

1. Check the documentation
2. Review API documentation at `/docs`
3. Check logs for error details
4. Consult troubleshooting section

### Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit pull request

## License

[Specify your license here]

---

**Last Updated**: May 26, 2025
**Version**: 1.0.0
