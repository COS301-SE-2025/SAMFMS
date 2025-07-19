# SAMFMS Backend Routes Comprehensive Documentation

## System Architecture

The SAMFMS backend uses a microservices architecture with the **Core Service** acting as an API gateway. All frontend requests go through the Core service, which then routes them to the appropriate service blocks via RabbitMQ.

### Request Flow

```
Frontend → Core Service → Service Block (via RabbitMQ) → Response
```

## Core Service Routes

### Authentication Routes (`/auth/*`)

**Base URL**: Core Service directly handles these routes
**Service**: Security Service (via proxy)

| Method | Endpoint                       | Description             |
| ------ | ------------------------------ | ----------------------- |
| POST   | `/auth/login`                  | User login              |
| POST   | `/auth/signup`                 | User registration       |
| POST   | `/auth/logout`                 | User logout             |
| GET    | `/auth/me`                     | Get current user info   |
| GET    | `/auth/user-exists`            | Check if user exists    |
| GET    | `/auth/users/count`            | Get user count          |
| POST   | `/auth/verify-token`           | Verify JWT token        |
| GET    | `/auth/roles`                  | Get available roles     |
| POST   | `/auth/update-preferences`     | Update user preferences |
| POST   | `/auth/update-profile`         | Update user profile     |
| POST   | `/auth/change-password`        | Change user password    |
| POST   | `/auth/upload-profile-picture` | Upload profile picture  |

### Service Routing (`/management/*`, `/maintenance/*`, `/gps/*`, `/trips/*`)

**Base URL**: Core Service routes these to service blocks

The Core service strips the prefix and forwards the request:

- `/management/vehicles` → Management Service `/vehicles`
- `/maintenance/records` → Maintenance Service `/records`
- `/gps/locations` → GPS Service `/locations`
- `/trips/plan` → Trip Planning Service `/plan`

## Service Block Routes

## 1. Management Service (`/management/*`)

### Vehicle Management

| Method | Endpoint                                        | Description             |
| ------ | ----------------------------------------------- | ----------------------- |
| GET    | `/management/vehicles`                          | List all vehicles       |
| POST   | `/management/vehicles`                          | Create new vehicle      |
| GET    | `/management/vehicles/{vehicle_id}`             | Get specific vehicle    |
| PUT    | `/management/vehicles/{vehicle_id}`             | Update vehicle          |
| DELETE | `/management/vehicles/{vehicle_id}`             | Delete vehicle          |
| GET    | `/management/vehicles/search`                   | Search vehicles         |
| GET    | `/management/vehicles/{vehicle_id}/assignments` | Get vehicle assignments |
| GET    | `/management/vehicles/{vehicle_id}/usage`       | Get vehicle usage stats |

### Driver Management

| Method | Endpoint                                           | Description                  |
| ------ | -------------------------------------------------- | ---------------------------- |
| GET    | `/management/drivers`                              | List all drivers             |
| POST   | `/management/drivers`                              | Create new driver            |
| GET    | `/management/drivers/{driver_id}`                  | Get specific driver          |
| PUT    | `/management/drivers/{driver_id}`                  | Update driver                |
| DELETE | `/management/drivers/{driver_id}`                  | Delete driver                |
| POST   | `/management/drivers/{driver_id}/activate`         | Activate driver              |
| POST   | `/management/drivers/{driver_id}/assign-vehicle`   | Assign vehicle to driver     |
| POST   | `/management/drivers/{driver_id}/unassign-vehicle` | Unassign vehicle from driver |
| GET    | `/management/drivers/search/{query}`               | Search drivers               |

### Analytics

| Method | Endpoint                                   | Description                   |
| ------ | ------------------------------------------ | ----------------------------- |
| GET    | `/management/analytics/dashboard`          | Get dashboard data            |
| GET    | `/management/analytics/fleet-utilization`  | Get fleet utilization metrics |
| GET    | `/management/analytics/vehicle-usage`      | Get vehicle usage analytics   |
| GET    | `/management/analytics/assignment-metrics` | Get assignment metrics        |
| GET    | `/management/analytics/driver-performance` | Get driver performance data   |
| POST   | `/management/analytics/refresh`            | Refresh analytics cache       |
| DELETE | `/management/analytics/cache`              | Clear analytics cache         |

## 2. Maintenance Service (`/maintenance/*`)

### Maintenance Records

| Method | Endpoint                                    | Description                         |
| ------ | ------------------------------------------- | ----------------------------------- |
| GET    | `/maintenance/records`                      | List maintenance records            |
| POST   | `/maintenance/records`                      | Create new maintenance record       |
| GET    | `/maintenance/records/{record_id}`          | Get specific maintenance record     |
| PUT    | `/maintenance/records/{record_id}`          | Update maintenance record           |
| DELETE | `/maintenance/records/{record_id}`          | Delete maintenance record           |
| GET    | `/maintenance/records/vehicle/{vehicle_id}` | Get maintenance records for vehicle |
| GET    | `/maintenance/records/search`               | Search maintenance records          |

### License Management

| Method | Endpoint                                        | Description                    |
| ------ | ----------------------------------------------- | ------------------------------ |
| GET    | `/maintenance/licenses`                         | List all licenses              |
| POST   | `/maintenance/licenses`                         | Create new license             |
| GET    | `/maintenance/licenses/{license_id}`            | Get specific license           |
| PUT    | `/maintenance/licenses/{license_id}`            | Update license                 |
| DELETE | `/maintenance/licenses/{license_id}`            | Delete license                 |
| GET    | `/maintenance/licenses/entity/{entity_id}`      | Get licenses for entity        |
| GET    | `/maintenance/licenses/status/expiring`         | Get expiring licenses          |
| GET    | `/maintenance/licenses/status/expired`          | Get expired licenses           |
| GET    | `/maintenance/licenses/type/{license_type}`     | Get licenses by type           |
| POST   | `/maintenance/licenses/{license_id}/renew`      | Renew license                  |
| POST   | `/maintenance/licenses/{license_id}/deactivate` | Deactivate license             |
| GET    | `/maintenance/licenses/summary/statistics`      | Get license summary statistics |

### Maintenance Analytics

| Method | Endpoint                           | Description               |
| ------ | ---------------------------------- | ------------------------- |
| GET    | `/maintenance/analytics/dashboard` | Get maintenance dashboard |
| GET    | `/maintenance/analytics/costs`     | Get cost analytics        |
| GET    | `/maintenance/analytics/trends`    | Get maintenance trends    |

### Maintenance Notifications

| Method | Endpoint                                            | Description               |
| ------ | --------------------------------------------------- | ------------------------- |
| GET    | `/maintenance/notifications`                        | List notifications        |
| POST   | `/maintenance/notifications`                        | Create notification       |
| GET    | `/maintenance/notifications/{notification_id}`      | Get specific notification |
| PUT    | `/maintenance/notifications/{notification_id}`      | Update notification       |
| DELETE | `/maintenance/notifications/{notification_id}`      | Delete notification       |
| POST   | `/maintenance/notifications/{notification_id}/read` | Mark notification as read |

## 3. GPS Service (`/gps/*`)

### Location Management

| Method | Endpoint                              | Description                      |
| ------ | ------------------------------------- | -------------------------------- |
| POST   | `/gps/locations/update`               | Update vehicle location          |
| GET    | `/gps/locations/{vehicle_id}`         | Get current location for vehicle |
| GET    | `/gps/locations`                      | Get all current locations        |
| GET    | `/gps/locations/{vehicle_id}/history` | Get location history             |
| POST   | `/gps/locations/search/area`          | Search locations in area         |

### Geofencing

| Method | Endpoint                       | Description           |
| ------ | ------------------------------ | --------------------- |
| GET    | `/gps/geofences`               | List geofences        |
| POST   | `/gps/geofences`               | Create geofence       |
| GET    | `/gps/geofences/{geofence_id}` | Get specific geofence |
| PUT    | `/gps/geofences/{geofence_id}` | Update geofence       |
| DELETE | `/gps/geofences/{geofence_id}` | Delete geofence       |

### Tracking

| Method | Endpoint                     | Description       |
| ------ | ---------------------------- | ----------------- |
| GET    | `/gps/tracking/{vehicle_id}` | Get tracking data |
| POST   | `/gps/tracking/start`        | Start tracking    |
| POST   | `/gps/tracking/stop`         | Stop tracking     |

### Places

| Method | Endpoint                 | Description        |
| ------ | ------------------------ | ------------------ |
| GET    | `/gps/places`            | List places        |
| POST   | `/gps/places`            | Create place       |
| GET    | `/gps/places/{place_id}` | Get specific place |
| PUT    | `/gps/places/{place_id}` | Update place       |
| DELETE | `/gps/places/{place_id}` | Delete place       |

## 4. Trip Planning Service (`/trips/*`)

**Note**: This service is currently minimal and only provides basic health check endpoints.

| Method | Endpoint        | Description           |
| ------ | --------------- | --------------------- |
| GET    | `/trips/`       | Health check          |
| GET    | `/trips/health` | Service health status |

## 5. Security Service (Internal)

**Note**: This service is accessed via Core's auth proxy routes. Direct access routes:

| Method | Endpoint                       | Description             |
| ------ | ------------------------------ | ----------------------- |
| POST   | `/auth/signup`                 | User registration       |
| POST   | `/auth/login`                  | User login              |
| POST   | `/auth/logout`                 | User logout             |
| GET    | `/auth/me`                     | Get current user        |
| GET    | `/auth/user-exists`            | Check if user exists    |
| GET    | `/auth/users/count`            | Get user count          |
| POST   | `/auth/verify-token`           | Verify JWT token        |
| GET    | `/auth/roles`                  | Get available roles     |
| POST   | `/auth/update-preferences`     | Update user preferences |
| POST   | `/auth/update-profile`         | Update user profile     |
| POST   | `/auth/change-password`        | Change user password    |
| POST   | `/auth/upload-profile-picture` | Upload profile picture  |

## Frontend API Configuration Status

### ✅ Correctly Configured Routes

- **Authentication**: `/auth/*` → Core Service
- **Management**: `/management/*` → Management Service
- **Maintenance**: `/maintenance/*` → Maintenance Service
- **GPS**: `/gps/*` → GPS Service
- **Vehicle Management**: `/vehicles/*` → Management Service
- **Driver Management**: `/vehicles/drivers/*` → Management Service

### ⚠️ Routes Needing Attention

1. **Trip Planning Routes**: Frontend expects `/trips/*` but service only provides health endpoints
2. **Maintenance Schedules**: Frontend expects `/maintenance/schedules/*` but service doesn't provide these routes
3. **Maintenance Vendors**: Frontend expects `/maintenance/vendors/*` but service doesn't provide these routes

## Recommendations

### 1. Update Frontend Configuration

Remove or update references to non-existent routes:

- Remove `/maintenance/schedules/*` endpoints
- Remove `/maintenance/vendors/*` endpoints
- Simplify trip planning to only health check

### 2. Service Development

Consider implementing missing functionality:

- Trip planning service routes
- Maintenance schedules management
- Vendor management for maintenance

### 3. Route Consistency

Ensure all routes follow the pattern:

- Frontend calls Core with service prefix
- Core strips prefix and forwards to service
- Service handles the unprefixed route

## Service Communication

All services communicate via RabbitMQ:

- **Exchange Types**: Direct exchange for request/response
- **Routing Keys**: `{service}.request` and `{service}.response`
- **Message Format**: JSON with correlation IDs

## Health Check Endpoints

Each service provides:

- `GET /health` - Service health status
- `GET /` - Basic service information
