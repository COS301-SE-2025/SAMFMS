# GPS Tracking Service

A comprehensive GPS tracking service for the SAMFMS (Smart Autonomous Fleet Management System) that provides real-time vehicle tracking, geofencing, route management, and location analytics.

## Features

### 🚗 Real-time Vehicle Tracking
- Live location updates with configurable intervals
- WebSocket support for real-time streaming
- Historical location data with automatic cleanup
- Speed and heading tracking
- Driver assignment and monitoring

### 🗺️ Geofencing
- Create and manage custom geofences (circular and polygonal)
- Real-time geofence entry/exit detection
- Configurable alerts and notifications
- Dwell time calculation
- Multiple geofence types (depot, delivery zone, restricted area)

### 🛣️ Route Management
- Route planning and optimization
- Real-time route tracking and progress monitoring
- Waypoint management
- Route deviation detection
- Estimated vs actual time/distance analysis

### 📊 Analytics & Reporting
- Vehicle performance metrics
- Fleet utilization reports
- Speed analysis and violations
- Geofence statistics
- Historical data visualization

### 🔔 Event Management
- Real-time event processing via RabbitMQ
- Configurable alert types
- Emergency alert system
- Event logging and history

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │   GPS Service   │    │   Trip Planning │
│                 │◄──►│                 │◄──►│    Service      │
│ TrackingMap.jsx │    │  FastAPI + WS   │    │                 │
│ GeofenceManager │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                ┌─────────────────────────────────┐
                │         Data Layer              │
                │                                 │
                │  MongoDB      Redis    RabbitMQ │
                │ (Location)  (Cache)  (Messages) │
                └─────────────────────────────────┘
```

## Technology Stack

- **Backend**: FastAPI (Python 3.9+)
- **Database**: MongoDB with geospatial indexing
- **Cache**: Redis for session management
- **Message Queue**: RabbitMQ for real-time events
- **WebSockets**: Real-time communication
- **Containerization**: Docker & Docker Compose

## Quick Start

### Prerequisites

- Docker Desktop
- Docker Compose
- Git

### 1. Clone and Setup

```bash
git clone <repository-url>
cd SAMFMS/Sblocks/gps
```

### 2. Start Services

**Linux/macOS:**
```bash
chmod +x start.sh
./start.sh
```

**Windows (PowerShell):**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\start.ps1
```

### 3. Verify Installation

The startup script will display service URLs:
- **API Documentation**: http://localhost:8003/docs
- **Health Check**: http://localhost:8003/health
- **WebSocket Test**: ws://localhost:8003/ws

## Configuration

### Environment Variables

Create a `.env` file or set the following environment variables:

```env
# Service Configuration
GPS_SERVICE_ENV=development
DEBUG=true
API_HOST=0.0.0.0
API_PORT=8003

# Database Configuration
MONGODB_URL=mongodb://mongodb:27017/gps_tracking
REDIS_URL=redis://redis:6379/0

# Message Queue Configuration
RABBITMQ_URL=amqp://gps_service:gps_service_password@rabbitmq:5672/

# Location Tracking
LOCATION_UPDATE_INTERVAL=30
LOCATION_ACCURACY_THRESHOLD=50.0
ENABLE_REAL_TIME_TRACKING=true

# Geofencing
GEOFENCE_CHECK_INTERVAL=10
GEOFENCE_BUFFER_DISTANCE=10.0
ENABLE_GEOFENCE_MONITORING=true

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/gps_service.log
```

## API Endpoints

### Location Management

#### Update Vehicle Location
```http
POST /api/locations/update
Content-Type: application/json

{
  "vehicle_id": "VEH001",
  "driver_id": "DRV001",
  "latitude": 37.7749,
  "longitude": -122.4194,
  "speed": 45.5,
  "heading": 180.0,
  "accuracy": 10.0,
  "trip_id": "TRIP001"
}
```

#### Get Current Location
```http
GET /api/locations/vehicle/{vehicle_id}/current
```

#### Get Location History
```http
GET /api/locations/vehicle/{vehicle_id}/history?start_time=2024-01-01T00:00:00Z&end_time=2024-01-02T00:00:00Z
```

### Geofence Management

#### Create Geofence
```http
POST /api/geofences/
Content-Type: application/json

{
  "name": "Downtown Depot",
  "description": "Main vehicle depot",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[
      [-122.4194, 37.7749],
      [-122.4184, 37.7749],
      [-122.4184, 37.7759],
      [-122.4194, 37.7759],
      [-122.4194, 37.7749]
    ]]
  },
  "geofence_type": "depot"
}
```

#### List Geofences
```http
GET /api/geofences/?is_active=true&geofence_type=depot
```

#### Check Vehicle in Geofence
```http
GET /api/geofences/vehicle/{vehicle_id}/current
```

### Route Management

#### Create Route
```http
POST /api/routes/
Content-Type: application/json

{
  "name": "Downtown Express",
  "description": "Fast route to downtown area",
  "start_location": {
    "type": "Point",
    "coordinates": [-122.4194, 37.7749]
  },
  "end_location": {
    "type": "Point",
    "coordinates": [-122.4069, 37.7874]
  },
  "waypoints": [
    {
      "type": "Point",
      "coordinates": [-122.4150, 37.7800]
    }
  ]
}
```

#### Start Route Tracking
```http
POST /api/routes/{route_id}/start
Content-Type: application/json

{
  "vehicle_id": "VEH001",
  "driver_id": "DRV001",
  "trip_id": "TRIP001"
}
```

### WebSocket Connection

#### Connect to Real-time Updates
```javascript
const ws = new WebSocket('ws://localhost:8003/ws/vehicle/VEH001');

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Location update:', data);
};
```

## Data Models

### Vehicle Location
```python
{
  "vehicle_id": "string",
  "driver_id": "string",
  "location": {
    "type": "Point",
    "coordinates": [longitude, latitude]
  },
  "speed": 0.0,
  "heading": 0.0,
  "accuracy": 0.0,
  "timestamp": "2024-01-01T00:00:00Z",
  "trip_id": "string",
  "metadata": {}
}
```

### Geofence
```python
{
  "name": "string",
  "description": "string",
  "geometry": {
    "type": "Polygon|Circle",
    "coordinates": [...] | {"center": [...], "radius": 100}
  },
  "geofence_type": "depot|delivery_zone|restricted_area",
  "is_active": true,
  "created_by": "string",
  "metadata": {}
}
```

### Route
```python
{
  "name": "string",
  "description": "string",
  "start_location": {"type": "Point", "coordinates": [...]},
  "end_location": {"type": "Point", "coordinates": [...]},
  "waypoints": [{"type": "Point", "coordinates": [...]}],
  "estimated_duration": 1800,
  "estimated_distance": 5.2,
  "is_active": true,
  "metadata": {}
}
```

## Database Schema

### Collections

1. **vehicle_locations**: Current vehicle positions
2. **location_history**: Historical location data (90-day TTL)
3. **geofences**: Geofence definitions
4. **geofence_events**: Geofence entry/exit events (180-day TTL)
5. **routes**: Route definitions
6. **route_tracking**: Route progress tracking (90-day TTL)

### Indexes

- Geospatial indexes for location queries
- Compound indexes for vehicle + time queries
- Text indexes for search functionality
- TTL indexes for automatic data cleanup

## Message Queue Events

### Location Events
- `location.update.{vehicle_id}`: Location updates
- `location.speed_violation.{vehicle_id}`: Speed violations

### Geofence Events
- `geofence.entry.{geofence_id}`: Geofence entry
- `geofence.exit.{geofence_id}`: Geofence exit
- `geofence.dwell.{geofence_id}`: Dwell time alerts

### Route Events
- `route.started.{route_id}`: Route tracking started
- `route.completed.{route_id}`: Route completed
- `route.deviation.{route_id}`: Route deviation detected

### Emergency Events
- `emergency.alert.{vehicle_id}`: Emergency alerts
- `emergency.panic.{vehicle_id}`: Panic button events

## Management Interfaces

- **MongoDB Express**: http://localhost:8081
- **RabbitMQ Management**: http://localhost:15672
  - Username: `gps_service`
  - Password: `gps_service_password`
- **Redis Commander**: http://localhost:8082

## Monitoring and Logging

### Health Checks
```http
GET /health
```

### Metrics
```http
GET /metrics
```

### Logs
```bash
# All services
docker-compose logs -f

# GPS service only
docker-compose logs -f gps-service

# Tail log files
tail -f logs/gps_service.log
```

## Development

### Local Development Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start external services:
```bash
docker-compose up -d mongodb redis rabbitmq
```

3. Run the service:
```bash
uvicorn main:app --reload --port 8003
```

### Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=. tests/
```

### Code Quality

```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

## Production Deployment

### Docker Swarm

```bash
docker stack deploy -c docker-compose.prod.yml gps-stack
```

### Kubernetes

```bash
kubectl apply -f k8s/
```

### Environment Configuration

Set production environment variables:
```env
GPS_SERVICE_ENV=production
DEBUG=false
MONGODB_URL=mongodb://mongo-cluster:27017/gps_tracking
REDIS_URL=redis://redis-cluster:6379/0
RABBITMQ_URL=amqp://user:password@rabbitmq-cluster:5672/
SECRET_KEY=<strong-secret-key>
```

## Security

- JWT token authentication
- Rate limiting on API endpoints
- Input validation and sanitization
- Secure WebSocket connections
- Database access controls

## Performance

- MongoDB indexes for fast queries
- Redis caching for frequent data
- Async processing for heavy operations
- Connection pooling
- Horizontal scaling support

## Troubleshooting

### Common Issues

1. **Service won't start**: Check Docker is running
2. **Database connection failed**: Verify MongoDB is accessible
3. **WebSocket connection refused**: Check firewall settings
4. **High memory usage**: Adjust location history retention

### Debug Mode

Enable debug logging:
```env
DEBUG=true
LOG_LEVEL=DEBUG
```

### Performance Monitoring

Monitor service performance:
```bash
# Check container stats
docker stats

# Monitor database performance
docker-compose exec mongodb mongosh --eval "db.stats()"

# Check queue status
docker-compose exec rabbitmq rabbitmqctl list_queues
```

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the API documentation at `/docs`
3. Check service logs for error messages
4. Contact the development team

## License

[License information here]
