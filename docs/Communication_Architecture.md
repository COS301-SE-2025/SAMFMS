# SAMFMS Communication Architecture

## Overview

This document describes the robust, scalable communication architecture implemented for the South African Fleet Management System (SAMFMS). The architecture uses the Core service as a central proxy/orchestrator that facilitates communication between the frontend and service blocks via RabbitMQ.

## Architecture Components

### 1. Core Service (Proxy/Orchestrator)

- **Location**: `Core/`
- **Role**: Central API gateway and message router
- **Key Components**:
  - `routes/service_proxy.py`: API endpoints that proxy frontend requests
  - `services/request_router.py`: Routes requests to appropriate service blocks
  - `services/core_auth_service.py`: Handles authorization with security block
  - `services/resilience.py`: Implements circuit breaker, retry, and tracing

### 2. Service Blocks

- **Management Service**: `Sblocks/management/`
- **GPS Service**: `Sblocks/gps/`
- **Trip Planning Service**: `Sblocks/trip_planning/`
- **Vehicle Maintenance Service**: `Sblocks/vehicle_maintainence/`

### 3. Communication Patterns

#### RabbitMQ-based Communication

- **Exchange**: `service_requests` (Direct)
- **Request Queues**: `{service}.requests` (e.g., `management.requests`)
- **Response Queue**: `core.responses`
- **Response Exchange**: `service_responses` (Direct)

#### Direct API Communication

- **Security Block**: Direct HTTP API calls for authentication and authorization

## Request Flow

```
Frontend → Core API → Core Auth Service → Request Router → RabbitMQ → Service Block
                                                              ↓
Frontend ← Core API ← Response Manager ← RabbitMQ ← Service Response Handler
```

### Detailed Flow:

1. **Frontend Request**: Client makes HTTP request to Core API endpoint
2. **Authentication**: Core validates token with Security block via direct API
3. **Authorization**: Core checks user permissions for the requested resource
4. **Request Routing**: Core determines target service block based on endpoint pattern
5. **Message Publishing**: Core publishes request message to service-specific queue
6. **Service Processing**: Service block processes request and prepares response
7. **Response Publishing**: Service block publishes response to Core response queue
8. **Response Correlation**: Core correlates response with original request
9. **HTTP Response**: Core returns response to frontend

## Key Features

### 1. Scalability

- **Asynchronous Processing**: All communication is non-blocking
- **Message Queuing**: RabbitMQ provides reliable message delivery
- **Load Distribution**: Multiple service instances can consume from same queue

### 2. Resilience

- **Circuit Breaker**: Prevents cascade failures by temporarily blocking calls to failed services
- **Retry Logic**: Automatic retry with exponential backoff for transient failures
- **Timeout Handling**: Configurable timeouts for all service calls
- **Health Monitoring**: Each service reports health status

### 3. Observability

- **Request Tracing**: Distributed tracing with correlation IDs
- **Logging**: Comprehensive logging at all levels
- **Metrics**: Performance and health metrics collection

### 4. Security

- **Token Validation**: All requests require valid JWT tokens
- **Authorization**: Permission-based access control
- **Secure Communication**: TLS encryption for sensitive data

## Configuration

### Routing Configuration

The request router uses pattern matching to determine target services:

```python
routing_map = {
    "/api/vehicles/*": "management",
    "/api/vehicle-assignments/*": "management",
    "/api/vehicle-usage/*": "management",
    "/api/gps/*": "gps",
    "/api/tracking/*": "gps",
    "/api/trips/*": "trip_planning",
    "/api/trip-planning/*": "trip_planning",
    "/api/maintenance/*": "maintenance",
    "/api/vehicle-maintenance/*": "maintenance"
}
```

### Resilience Configuration

```python
circuit_breaker_config = {
    "failure_threshold": 5,
    "recovery_timeout": 30.0,
    "expected_recovery_time": 60.0
}

retry_config = {
    "max_retries": 3,
    "base_delay": 1.0,
    "max_delay": 30.0
}
```

## Service Block Implementation

### Request Handler Structure

Each service block implements a `ServiceRequestHandler` class:

```python
class ServiceRequestHandler:
    async def initialize(self):
        # Set up RabbitMQ consumption

    async def _handle_request_message(self, message):
        # Process incoming request
        # Route to appropriate handler
        # Send response back to Core

    async def route_to_handler(self, endpoint, method, data, user_context):
        # Route request to specific handler method
```

### Handler Methods

Each service implements handlers for different endpoints:

- `_get_*`: Handle GET requests
- `_create_*`: Handle POST requests
- `_update_*`: Handle PUT requests
- `_delete_*`: Handle DELETE requests

## Adding New Service Blocks

To add a new service block to the architecture:

1. **Create Service Request Handler**:

   ```python
   # new_service/service_request_handler.py
   from service_request_handler_base import ServiceRequestHandler

   class NewServiceRequestHandler(ServiceRequestHandler):
       def __init__(self):
           super().__init__()
           self.endpoint_handlers = {
               "/api/new-service": {
                   "GET": self._get_items,
                   "POST": self._create_item
               }
           }

   service_request_handler = NewServiceRequestHandler()
   ```

2. **Update Service Main Application**:

   ```python
   # new_service/main.py
   from service_request_handler import service_request_handler

   @app.on_event("startup")
   async def startup_event():
       await service_request_handler.initialize()
   ```

3. **Update Core Routing Map**:

   ```python
   # Core/services/request_router.py
   routing_map = {
       # ... existing routes ...
       "/api/new-service/*": "new_service"
   }
   ```

4. **Add Proxy Routes (Optional)**:
   ```python
   # Core/routes/service_proxy.py
   @router.get("/new-service")
   async def get_new_service_items(...)
   ```

## Testing

### Manual Testing

Use the provided test script:

```bash
python test_communication_architecture.py
```

### Integration Testing

1. Start all services (Core + Service Blocks)
2. Make requests through Core API
3. Verify requests reach correct service blocks
4. Verify responses return to frontend

### Load Testing

- Use tools like Apache Bench or k6
- Test concurrent requests to different service blocks
- Monitor RabbitMQ queue depths and processing times

## Monitoring and Debugging

### Logs

- **Core**: Central logging of all request routing
- **Service Blocks**: Individual service processing logs
- **RabbitMQ**: Message queue logs and metrics

### Health Checks

- Each service exposes `/health` endpoint
- Core aggregates health status from all services
- RabbitMQ provides management interface

### Troubleshooting Common Issues

1. **Service Not Responding**:

   - Check service health endpoint
   - Verify RabbitMQ connection
   - Check circuit breaker status

2. **Request Timeout**:

   - Increase timeout configuration
   - Check service load and performance
   - Verify network connectivity

3. **Authentication Failures**:
   - Verify security block is running
   - Check token validity and expiration
   - Validate user permissions

## Performance Considerations

### Message Size

- Keep message payloads reasonable (< 1MB)
- Use pagination for large datasets
- Consider compression for large responses

### Connection Pooling

- RabbitMQ connections are managed by aio_pika
- Database connections use connection pooling
- HTTP client sessions are reused

### Caching

- Implement response caching where appropriate
- Cache user permissions for short periods
- Use Redis for distributed caching

## Security Considerations

### Message Security

- All messages include user context for authorization
- Sensitive data should be encrypted at rest
- Use TLS for all network communication

### Access Control

- Service blocks validate user permissions
- Core performs centralized authorization
- Audit logging for all requests

## Future Enhancements

1. **Event-Driven Architecture**: Add event publishing for real-time updates
2. **Service Discovery**: Implement dynamic service registration
3. **API Versioning**: Support multiple API versions
4. **Rate Limiting**: Implement per-user rate limiting
5. **Message Encryption**: Add end-to-end message encryption

## Dependencies

### Core Service

- FastAPI
- aio-pika (RabbitMQ client)
- httpx (HTTP client)
- Motor (MongoDB async driver)

### Service Blocks

- FastAPI
- aio-pika
- Motor or appropriate database driver
- Service-specific dependencies

### Infrastructure

- RabbitMQ
- MongoDB
- Redis (for caching)
- Docker (for containerization)

## Conclusion

This communication architecture provides a robust, scalable foundation for the SAMFMS system. It supports easy integration of new services while maintaining security, reliability, and performance standards. The architecture is designed to handle high loads and provides comprehensive monitoring and debugging capabilities.
