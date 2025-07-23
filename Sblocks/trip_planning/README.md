# Trip Planning Service

The Trip Planning Service is responsible for trip scheduling, management, analytics, and notifications within the SAMFMS system.

## Features

- **Trip CRUD Operations**: Create, read, update, and delete scheduled trips
- **Trip Constraints**: Support for avoiding toll gates, highways, and other constraints
- **Driver Assignment**: Assign drivers to trips with availability tracking
- **Route Optimization**: Calculate optimal routes based on constraints
- **Trip Analytics**: Statistics on trip performance, duration, and costs
- **Real-time Notifications**: Alerts for trip events (started, ended, delays, rerouting)
- **Trip Monitoring**: Track trip progress and driver compliance

## Architecture

The Trip Planning service follows the same architectural patterns as other SAMFMS services:

- **Repository Pattern**: Data access abstraction
- **Service Layer**: Business logic separation
- **Event-Driven Communication**: RabbitMQ for inter-service messaging
- **Standardized API Responses**: Consistent response format
- **Comprehensive Error Handling**: Robust error management
- **Health Monitoring**: Built-in health checks and metrics

## API Endpoints

### Trip Management

- `POST /api/trips` - Create a new trip
- `GET /api/trips` - List trips with filtering
- `GET /api/trips/{trip_id}` - Get trip details
- `PUT /api/trips/{trip_id}` - Update trip
- `DELETE /api/trips/{trip_id}` - Delete trip

### Driver Assignment

- `POST /api/trips/{trip_id}/assign-driver` - Assign driver to trip
- `DELETE /api/trips/{trip_id}/unassign-driver` - Remove driver assignment
- `GET /api/drivers/availability` - Check driver availability

### Trip Constraints

- `POST /api/trips/{trip_id}/constraints` - Add constraints to trip
- `GET /api/trips/{trip_id}/constraints` - Get trip constraints
- `PUT /api/trips/{trip_id}/constraints/{constraint_id}` - Update constraint
- `DELETE /api/trips/{trip_id}/constraints/{constraint_id}` - Remove constraint

### Analytics

- `GET /api/analytics/trips/summary` - Get trip statistics
- `GET /api/analytics/drivers/performance` - Driver performance metrics
- `GET /api/analytics/routes/efficiency` - Route efficiency analysis

### Notifications

- `GET /api/notifications` - Get user notifications
- `POST /api/notifications/preferences` - Set notification preferences
- `PUT /api/notifications/{notification_id}/read` - Mark notification as read

## Database Schema

### Collections

- `trips` - Trip information and schedules
- `trip_constraints` - Trip routing constraints
- `driver_assignments` - Driver-trip assignments
- `trip_analytics` - Trip performance data
- `notifications` - User notifications
- `notification_preferences` - User notification settings

## Events

### Published Events

- `trip.created` - New trip scheduled
- `trip.updated` - Trip details modified
- `trip.deleted` - Trip cancelled
- `trip.started` - Trip began
- `trip.completed` - Trip finished
- `trip.delayed` - Trip running late
- `driver.assigned` - Driver assigned to trip
- `driver.unassigned` - Driver removed from trip
- `route.optimized` - Route recalculated
- `notification.sent` - Notification delivered

### Consumed Events

- `vehicle.location_updated` - For trip monitoring
- `driver.availability_changed` - For assignment validation
- `traffic.update` - For route optimization

## Configuration

Environment variables:

- `MONGODB_URL` - Database connection string
- `RABBITMQ_URL` - Message broker connection
- `NOTIFICATION_PROVIDERS` - External notification services
- `MAPS_API_KEY` - Map provider API key
- `TRIP_PLANNING_PORT` - Service port (default: 8005)

## Dependencies

- FastAPI
- Motor (MongoDB async driver)
- aio-pika (RabbitMQ client)
- Pydantic
- APScheduler (for scheduled tasks)
- httpx (for external API calls)

## Running the Service

```bash
# Development
python main.py

# Docker
docker build -t samfms-trip-planning .
docker run -p 8005:8005 samfms-trip-planning
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html
```
