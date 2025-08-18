# GPS Service

The GPS Service is responsible for location tracking, geofencing, and places management within the SAMFMS system.

## Features

- **Real-time Location Tracking**: Track vehicle locations in real-time
- **Location History**: Store and retrieve historical location data
- **Geofencing**: Create and manage geofences with entry/exit detection
- **Places Management**: User-defined places with search capabilities
- **Map Provider Agnostic**: Compatible with Leaflet and other mapping libraries
- **Event-Driven Architecture**: Publishes events for location updates and geofence activities

## Architecture

The GPS service follows the same architectural patterns as other SAMFMS services:

- **Repository Pattern**: Data access abstraction
- **Service Layer**: Business logic separation
- **Event-Driven Communication**: RabbitMQ for inter-service messaging
- **Standardized API Responses**: Consistent response format
- **Comprehensive Error Handling**: Robust error management
- **Health Monitoring**: Built-in health checks and metrics

## API Endpoints

### Location Tracking

- `POST /api/locations/update` - Update vehicle location
- `GET /api/locations/{vehicle_id}` - Get current vehicle location
- `GET /api/locations` - Get multiple vehicle locations
- `GET /api/locations/{vehicle_id}/history` - Get location history
- `POST /api/locations/search/area` - Search vehicles in area

### Geofencing

- `POST /api/geofences` - Create geofence
- `GET /api/geofences/{geofence_id}` - Get geofence
- `GET /api/geofences` - List geofences
- `PUT /api/geofences/{geofence_id}` - Update geofence
- `DELETE /api/geofences/{geofence_id}` - Delete geofence
- `GET /api/geofences/{geofence_id}/events` - Get geofence events
- `GET /api/geofences/{geofence_id}/statistics` - Get geofence statistics

### Places Management

- `POST /api/places` - Create place
- `GET /api/places/{place_id}` - Get place
- `GET /api/places` - List user places
- `POST /api/places/search` - Search places
- `POST /api/places/nearby` - Get nearby places
- `PUT /api/places/{place_id}` - Update place
- `DELETE /api/places/{place_id}` - Delete place
- `GET /api/places/statistics` - Get place statistics

### Tracking Sessions

- `POST /api/tracking/sessions` - Start tracking session
- `DELETE /api/tracking/sessions/{session_id}` - End tracking session
- `GET /api/tracking/sessions` - Get active tracking sessions

## Data Models

### Location Data

- Vehicle locations with coordinates, speed, heading
- Altitude and GPS accuracy information
- Timestamp-based history tracking

### Geofences

- Polygon, circle, and rectangle geofences
- GeoJSON-based geometry storage
- Entry, exit, and dwell event tracking

### Places

- User-defined places with categories
- Address and metadata support
- Spatial search capabilities

## Environment Configuration

The service uses environment variables for configuration:

```bash
# Service Configuration
GPS_HOST=gps
GPS_PORT=8000
SERVICE_NAME=gps
SERVICE_VERSION=1.0.0

# Database
MONGODB_URL=mongodb://samfms_admin:SafeMongoPass2025%21SecureDB%40SAMFMS@mongodb:27017
DATABASE_NAME=samfms_gps

# RabbitMQ
RABBITMQ_URL=amqp://samfms_rabbit:RabbitPass2025%21@rabbitmq:5672/

# GPS-Specific
LOCATION_HISTORY_DAYS=90
GEOFENCE_CHECK_ENABLED=true
REAL_TIME_TRACKING=true
```

## Database Collections

### vehicle_locations

Current vehicle locations with GeoJSON points and 2dsphere indexing.

### location_history

Historical location data with TTL for automatic cleanup.

### geofences

Geofence definitions with spatial indexing for intersection queries.

### geofence_events

Events triggered by geofence interactions.

### places

User-defined places with spatial indexing for proximity searches.

### tracking_sessions

Active and historical tracking sessions.

## Integration with Frontend

The GPS service is designed to work seamlessly with frontend mapping libraries:

- **Leaflet Compatible**: Uses standard GeoJSON formats
- **Real-time Updates**: WebSocket support for live tracking
- **Efficient Queries**: Optimized spatial queries for map views
- **Flexible Filtering**: Support for various filtering options

## Running the Service

### Development

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker

```bash
docker build -t samfms-gps .
docker run -p 8000:8000 samfms-gps
```

### Docker Compose

The service is integrated into the main SAMFMS docker-compose.yml configuration.

## Testing

```bash
pytest tests/ -v
```

## Health Check

The service provides health checks at `/health` endpoint with component status:

- Database connectivity
- RabbitMQ connectivity
- Service uptime and metrics
