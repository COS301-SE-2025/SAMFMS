# SAMFMS Core Service - Simplified Routing System

## Overview

The SAMFMS Core Service has been updated to use a simplified path-based routing system that routes requests to appropriate service blocks via RabbitMQ message queues.

## Routing Architecture

### Path-Based Routing

The Core service now uses simple path prefixes to route requests:

- `/management/*` → Management service block
- `/maintenance/*` → Maintenance service block
- `/gps/*` → GPS service block
- `/trips/*` → Trip planning service block

### Route Processing

1. **Path Stripping**: The service prefix is stripped from the path before forwarding

   - Example: `/management/vehicles` becomes `/vehicles` when sent to Management service
   - Example: `/maintenance/schedules` becomes `/schedules` when sent to Maintenance service

2. **RabbitMQ Routing**: Each service block has its own exchange and queue
   - Management: `management_exchange` → `management_queue`
   - Maintenance: `maintenance_exchange` → `maintenance_queue`
   - GPS: `gps_exchange` → `gps_queue`
   - Trip Planning: `trip_planning_exchange` → `trip_planning_queue`

## Implementation Details

### Core Service (Gateway)

The Core service acts as an API gateway that:

1. Receives HTTP requests on the defined paths
2. Extracts request details (method, headers, body, query params)
3. Generates a unique request ID for correlation
4. Sends the request to the appropriate service block via RabbitMQ
5. Waits for the response from the service block
6. Returns the response to the client

### Service Blocks

Each service block should:

1. Listen for messages on their dedicated RabbitMQ queue
2. Process the request using the stripped path
3. Send the response back to the Core service via `core_responses` exchange
4. Include the original request ID for correlation

## Configuration

### RabbitMQ Exchanges and Queues

The system uses the following RabbitMQ configuration:

```python
SERVICE_BLOCKS = {
    "management": {
        "exchange": "management_exchange",
        "queue": "management_queue",
        "routing_key": "management.request"
    },
    "maintenance": {
        "exchange": "maintenance_exchange",
        "queue": "maintenance_queue",
        "routing_key": "maintenance.request"
    },
    "gps": {
        "exchange": "gps_exchange",
        "queue": "gps_queue",
        "routing_key": "gps.request"
    },
    "trips": {
        "exchange": "trip_planning_exchange",
        "queue": "trip_planning_queue",
        "routing_key": "trips.request"
    }
}
```

### Response Handling

- All service blocks send responses to: `core_responses` exchange
- Core service listens on: `core_responses` queue
- Routing key: `core.response`

## Example Usage

### HTTP Requests

```bash
# Management service requests
GET /management/vehicles           # → GET /vehicles to Management service
POST /management/drivers           # → POST /drivers to Management service
PUT /management/assignments/123    # → PUT /assignments/123 to Management service

# Maintenance service requests
GET /maintenance/schedules         # → GET /schedules to Maintenance service
POST /maintenance/work-orders      # → POST /work-orders to Maintenance service

# GPS service requests
GET /gps/locations                 # → GET /locations to GPS service
POST /gps/tracking                 # → POST /tracking to GPS service

# Trip planning service requests
GET /trips/routes                  # → GET /routes to Trip Planning service
POST /trips/plan                   # → POST /plan to Trip Planning service
```

### Service Block Implementation

See `examples/management_service_example.py` for a complete example of how to implement a service block consumer.

## Testing

### Test Script

Use the provided test script to validate the routing system:

```bash
python test_routing.py
```

### Manual Testing

1. Start the Core service
2. Start RabbitMQ
3. Optionally start example service blocks
4. Send HTTP requests to the Core service endpoints
5. Check logs for routing information

## Benefits

1. **Simplified Routing**: No complex route mappings required
2. **Service Isolation**: Each service block operates independently
3. **Scalability**: Service blocks can be scaled independently
4. **Fault Tolerance**: Service blocks can be restarted without affecting others
5. **Message Queuing**: Built-in reliability through RabbitMQ
6. **Easy Debugging**: Clear request/response correlation via request IDs

## Migration from Previous System

The new routing system replaces the previous consolidated routing approach:

- **Before**: Complex route mappings in multiple files
- **After**: Simple path-based routing with RabbitMQ message passing

### Breaking Changes

- Direct API routes are no longer available
- All requests must use the service block prefixes
- Service blocks must implement RabbitMQ consumers
- Response format is now standardized

## Future Enhancements

1. **Load Balancing**: Multiple instances of service blocks
2. **Circuit Breakers**: Automatic failover for unhealthy services
3. **Rate Limiting**: Per-service request throttling
4. **Caching**: Response caching for frequently accessed data
5. **Authentication**: Service-level authentication and authorization
