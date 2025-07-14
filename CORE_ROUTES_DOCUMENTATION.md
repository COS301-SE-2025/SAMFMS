# SAMFMS Core Service - API Routes Documentation

## Overview

This document provides a comprehensive reference for all available API routes in the SAMFMS Core service. The Core service acts as the central gateway that routes requests to appropriate service blocks and manages authentication, WebSocket connections, and system administration.

**Base URL:** `http://localhost:21004` (default development)

## Table of Contents

1. [Health Check Routes](#health-check-routes)
2. [Authentication Routes](#authentication-routes)
3. [Vehicle Management Routes](#vehicle-management-routes)
4. [Driver Management Routes](#driver-management-routes)
5. [GPS & Location Routes](#gps--location-routes)
6. [Analytics Routes](#analytics-routes)
7. [Trip Planning Routes](#trip-planning-routes)
8. [Maintenance Routes](#maintenance-routes)
9. [WebSocket Routes](#websocket-routes)
10. [Plugin Management Routes](#plugin-management-routes)
11. [Service Block Management](#service-block-management)
12. [Debug & Testing Routes](#debug--testing-routes)
13. [Direct Service Routes](#direct-service-routes)

---

## Health Check Routes

### System Health

- **GET** `/health`

  - **Description:** Check Core service health status
  - **Authentication:** None required
  - **Response:** `{"status": "healthy", "timestamp": "2025-07-11T16:03:41.664437"}`

- **GET** `/health/startup`
  - **Description:** Get startup validation results
  - **Authentication:** None required

### Service-Specific Health

- **GET** `/auth/health`
  - **Description:** Check authentication routes and Security service connectivity
  - **Authentication:** None required
  - **Response:** `{"auth_routes": "working", "security_service": "reachable", "security_url": "..."}`

---

## Authentication Routes

**Base Path:** `/auth`

### Core Authentication

- **POST** `/auth/login`

  - **Description:** Authenticate user and get access token
  - **Body:** `{"email": "user@example.com", "password": "password"}`
  - **Response:** `TokenResponse` with access_token, user_id, role, permissions

- **POST** `/auth/signup`

  - **Description:** Register a new user account
  - **Body:** `{"full_name": "John Doe", "email": "user@example.com", "password": "password", "role": "driver"}`
  - **Response:** `TokenResponse`

- **POST** `/auth/verify-token`

  - **Description:** Verify JWT token validity
  - **Headers:** `Authorization: Bearer <token>`
  - **Response:** Token validation result

- **POST** `/auth/logout`

  - **Description:** Logout current session
  - **Headers:** `Authorization: Bearer <token>`
  - **Response:** `{"message": "Logged out successfully"}`

- **POST** `/auth/logout-all`

  - **Description:** Logout from all devices
  - **Headers:** `Authorization: Bearer <token>`
  - **Response:** `{"message": "Logged out from all devices"}`

- **POST** `/auth/refresh`
  - **Description:** Refresh access token
  - **Body:** Refresh token data
  - **Response:** New access token

### User Management

- **GET** `/auth/me`

  - **Description:** Get current user information
  - **Headers:** `Authorization: Bearer <token>`
  - **Response:** User profile data

- **GET** `/auth/users`

  - **Description:** Get all users (Admin/Fleet Manager only)
  - **Headers:** `Authorization: Bearer <token>`
  - **Response:** Array of user objects

- **GET** `/auth/user-exists`
  - **Description:** Check if any users exist in the system
  - **Authentication:** None required
  - **Response:** `{"userExists": true/false}`

### Profile Management

- **POST** `/auth/update-profile`

  - **Description:** Update user profile information
  - **Headers:** `Authorization: Bearer <token>`
  - **Body:** `{"phoneNo": "...", "full_name": "..."}`

- **POST** `/auth/upload-profile-picture`

  - **Description:** Upload user profile picture
  - **Headers:** `Authorization: Bearer <token>`
  - **Body:** Multipart form with profile_picture file

- **POST** `/auth/update-preferences`

  - **Description:** Update user preferences
  - **Headers:** `Authorization: Bearer <token>`
  - **Body:** `{"preferences": {...}}`

- **POST** `/auth/change-password`
  - **Description:** Change user password
  - **Headers:** `Authorization: Bearer <token>`
  - **Body:** `{"current_password": "...", "new_password": "..."}`

### User Administration

- **POST** `/auth/invite-user`

  - **Description:** Invite a new user (Admin only)
  - **Headers:** `Authorization: Bearer <token>`
  - **Body:** Invitation data

- **POST** `/auth/create-user`

  - **Description:** Manually create user without invitation flow (Admin only)
  - **Headers:** `Authorization: Bearer <token>`
  - **Body:** `{"full_name": "...", "email": "...", "role": "...", "password": "..."}`

- **POST** `/auth/update-permissions`
  - **Description:** Update user permissions (Admin only)
  - **Headers:** `Authorization: Bearer <token>`
  - **Body:** `{"user_id": "...", "role": "...", "custom_permissions": [...]}`

### Invitation System

- **GET** `/auth/invitations`

  - **Description:** Get pending invitations
  - **Headers:** `Authorization: Bearer <token>`

- **POST** `/auth/resend-invitation`

  - **Description:** Resend invitation OTP
  - **Headers:** `Authorization: Bearer <token>`

- **POST** `/auth/verify-otp`

  - **Description:** Verify OTP for invitation (public)
  - **Body:** OTP verification data

- **POST** `/auth/complete-registration`
  - **Description:** Complete user registration after OTP verification (public)
  - **Body:** Registration completion data

### Role Management

- **GET** `/auth/roles`
  - **Description:** Get available roles and permissions
  - **Headers:** `Authorization: Bearer <token>`

---

## Vehicle Management Routes

### Vehicle CRUD Operations

- **GET** `/vehicles`

  - **Description:** Get all vehicles with optional filtering
  - **Headers:** `Authorization: Bearer <token>`
  - **Query Params:** `skip`, `limit`, `status_filter`, `make_filter`
  - **Response:** `{"vehicles": [...], "total": number, "analytics": {...}}`

- **POST** `/vehicles`

  - **Description:** Create a new vehicle
  - **Headers:** `Authorization: Bearer <token>`
  - **Body:** Vehicle data object

- **GET** `/vehicles/{vehicle_id}`

  - **Description:** Get specific vehicle by ID
  - **Headers:** `Authorization: Bearer <token>`
  - **Response:** Vehicle object

- **PUT** `/vehicles/{vehicle_id}`

  - **Description:** Update vehicle information
  - **Headers:** `Authorization: Bearer <token>`
  - **Body:** Updated vehicle data

- **DELETE** `/vehicles/{vehicle_id}`
  - **Description:** Delete vehicle
  - **Headers:** `Authorization: Bearer <token>`

### Vehicle Search & Assignment

- **GET** `/vehicles/search/{query}`

  - **Description:** Search vehicles by query
  - **Headers:** `Authorization: Bearer <token>`

- **GET** `/vehicle-assignments`

  - **Description:** Get vehicle assignments
  - **Headers:** `Authorization: Bearer <token>`
  - **Query Params:** `skip`, `limit`, `vehicle_id`, `driver_id`

- **POST** `/vehicle-assignments`

  - **Description:** Create vehicle assignment
  - **Headers:** `Authorization: Bearer <token>`
  - **Body:** Assignment data

- **PUT** `/vehicle-assignments/{assignment_id}`

  - **Description:** Update vehicle assignment
  - **Headers:** `Authorization: Bearer <token>`
  - **Body:** Updated assignment data

- **DELETE** `/vehicle-assignments/{assignment_id}`
  - **Description:** Delete vehicle assignment
  - **Headers:** `Authorization: Bearer <token>`

---

## Driver Management Routes

### Driver CRUD Operations

- **GET** `/drivers`

  - **Description:** Get all drivers
  - **Headers:** `Authorization: Bearer <token>`
  - **Query Params:** `limit`

- **POST** `/drivers`

  - **Description:** Create a new driver
  - **Headers:** `Authorization: Bearer <token>`
  - **Body:** Driver data object

- **GET** `/drivers/{driver_id}`

  - **Description:** Get specific driver by ID
  - **Headers:** `Authorization: Bearer <token>`

- **PUT** `/drivers/{driver_id}`

  - **Description:** Update driver information
  - **Headers:** `Authorization: Bearer <token>`
  - **Body:** Updated driver data

- **DELETE** `/drivers/{driver_id}`
  - **Description:** Delete driver
  - **Headers:** `Authorization: Bearer <token>`

---

## GPS & Location Routes

### Real-time GPS Data

- **POST** `/gps/request_location`

  - **Description:** Request location data from GPS service
  - **Body:** `{"vehicle_id": "...", "parameters": {...}}`

- **POST** `/gps/request_speed`

  - **Description:** Request speed data from GPS service
  - **Body:** GPS request parameters

- **POST** `/gps/request_direction`

  - **Description:** Request direction data from GPS service
  - **Body:** GPS request parameters

- **POST** `/gps/request_fuel_level`

  - **Description:** Request fuel level data from GPS service
  - **Body:** GPS request parameters

- **POST** `/gps/request_last_update`
  - **Description:** Request last update timestamp from GPS service
  - **Body:** GPS request parameters

### Location Management

- **GET** `/gps/locations`

  - **Description:** Get GPS location data
  - **Headers:** `Authorization: Bearer <token>`

- **POST** `/gps/locations`
  - **Description:** Create/update GPS location data
  - **Headers:** `Authorization: Bearer <token>`
  - **Body:** Location data

### Geofencing

- **POST** `/gps/geofences/circle`
  - **Description:** Create a new circular geofence
  - **Body:** `{"center": {"lat": number, "lng": number}, "radius": number, "name": "..."}`

---

## Analytics Routes

### Fleet Analytics

- **GET** `/analytics/fleet-utilization`

  - **Description:** Get fleet utilization analytics
  - **Headers:** `Authorization: Bearer <token>`

- **GET** `/analytics/vehicle-usage`

  - **Description:** Get vehicle usage analytics
  - **Headers:** `Authorization: Bearer <token>`

- **GET** `/analytics/assignment-metrics`

  - **Description:** Get assignment metrics
  - **Headers:** `Authorization: Bearer <token>`

- **GET** `/analytics/maintenance`

  - **Description:** Get maintenance analytics
  - **Headers:** `Authorization: Bearer <token>`

- **GET** `/analytics/driver-performance`

  - **Description:** Get driver performance analytics
  - **Headers:** `Authorization: Bearer <token>`

- **GET** `/analytics/costs`

  - **Description:** Get cost analytics
  - **Headers:** `Authorization: Bearer <token>`

- **GET** `/analytics/status-breakdown`

  - **Description:** Get vehicle status breakdown
  - **Headers:** `Authorization: Bearer <token>`

- **GET** `/analytics/incidents`

  - **Description:** Get incident analytics
  - **Headers:** `Authorization: Bearer <token>`

- **GET** `/analytics/department-location`
  - **Description:** Get department location analytics
  - **Headers:** `Authorization: Bearer <token>`

### Generic Analytics

- **GET** `/analytics/{path:path}`

  - **Description:** Generic analytics endpoint for custom paths
  - **Headers:** `Authorization: Bearer <token>`

- **POST** `/analytics/{path:path}`
  - **Description:** Submit analytics data for custom paths
  - **Headers:** `Authorization: Bearer <token>`

---

## Trip Planning Routes

### Trip Management

- **GET** `/trips/planned`

  - **Description:** Get planned trips
  - **Headers:** `Authorization: Bearer <token>`

- **POST** `/trips/create`

  - **Description:** Create new trip plan
  - **Headers:** `Authorization: Bearer <token>`

- **PUT** `/trips/{trip_id}/update`

  - **Description:** Update existing trip plan
  - **Headers:** `Authorization: Bearer <token>`

- **DELETE** `/trips/{trip_id}/cancel`
  - **Description:** Cancel trip plan
  - **Headers:** `Authorization: Bearer <token>`

### Generic Trip Operations

- **GET** `/trips/{path:path}`

  - **Description:** Generic trip endpoint for custom paths
  - **Headers:** `Authorization: Bearer <token>`

- **POST** `/trips/{path:path}`

  - **Description:** Submit trip data for custom paths
  - **Headers:** `Authorization: Bearer <token>`

- **PUT** `/trips/{path:path}`

  - **Description:** Update trip data for custom paths
  - **Headers:** `Authorization: Bearer <token>`

- **DELETE** `/trips/{path:path}`
  - **Description:** Delete trip data for custom paths
  - **Headers:** `Authorization: Bearer <token>`

---

## Maintenance Routes

### Maintenance Management

- **GET** `/maintenance/records`

  - **Description:** Get maintenance records
  - **Headers:** `Authorization: Bearer <token>`

- **POST** `/maintenance/schedule`

  - **Description:** Schedule maintenance
  - **Headers:** `Authorization: Bearer <token>`
  - **Body:** Maintenance schedule data

- **PUT** `/maintenance/{maintenance_id}/complete`

  - **Description:** Mark maintenance as complete
  - **Headers:** `Authorization: Bearer <token>`

- **DELETE** `/maintenance/{maintenance_id}/cancel`
  - **Description:** Cancel scheduled maintenance
  - **Headers:** `Authorization: Bearer <token>`

### Generic Maintenance Operations

- **GET** `/maintenance/{path:path}`

  - **Description:** Generic maintenance endpoint for custom paths
  - **Headers:** `Authorization: Bearer <token>`

- **POST** `/maintenance/{path:path}`
  - **Description:** Submit maintenance data for custom paths
  - **Headers:** `Authorization: Bearer <token>`
  - **Body:** Maintenance data

---

## WebSocket Routes

### Real-time Vehicle Tracking

- **WebSocket** `/ws/vehicles`
  - **Description:** WebSocket endpoint for real-time vehicle tracking
  - **Usage:** Connect via WebSocket client for live vehicle updates

### Testing Endpoints

- **GET** `/test/live_vehicles`
  - **Description:** Test endpoint to fetch live vehicle data
  - **Response:** Live vehicle data for testing WebSocket functionality

---

## Plugin Management Routes

### Plugin Information

- **GET** `/plugins/`

  - **Description:** Get all available plugins (Admin only)
  - **Headers:** `Authorization: Bearer <token>`
  - **Response:** Array of plugin information

- **GET** `/plugins/available`

  - **Description:** Get plugins available to current user based on role
  - **Headers:** `Authorization: Bearer <token>`

- **GET** `/plugins/{plugin_id}`
  - **Description:** Get specific plugin information
  - **Headers:** `Authorization: Bearer <token>`

### Plugin Control

- **POST** `/plugins/{plugin_id}/start`

  - **Description:** Start a plugin (Admin only)
  - **Headers:** `Authorization: Bearer <token>`
  - **Response:** `PluginStatusResponse`

- **POST** `/plugins/{plugin_id}/stop`

  - **Description:** Stop a plugin (Admin only)
  - **Headers:** `Authorization: Bearer <token>`
  - **Response:** `PluginStatusResponse`

- **GET** `/plugins/{plugin_id}/status`
  - **Description:** Get plugin status
  - **Headers:** `Authorization: Bearer <token>`

### Plugin Configuration

- **PUT** `/plugins/{plugin_id}/roles`

  - **Description:** Update plugin role requirements (Admin only)
  - **Headers:** `Authorization: Bearer <token>`
  - **Body:** Role configuration

- **POST** `/plugins/sync-status`
  - **Description:** Sync plugin status across the system
  - **Headers:** `Authorization: Bearer <token>`

### Plugin Debug

- **GET** `/plugins/debug/docker`
  - **Description:** Debug Docker access for plugin management (Admin only)
  - **Headers:** `Authorization: Bearer <token>`

### Service Block Plugin Routes

- **POST** `/plugins/sblock/{path:path}`

  - **Description:** Execute service block operations via plugin
  - **Headers:** `Authorization: Bearer <token>`
  - **Parameters:** Dynamic path routing to service blocks

- **GET** `/plugins/sblock/{path:path}`

  - **Description:** Query service block operations via plugin
  - **Headers:** `Authorization: Bearer <token>`
  - **Parameters:** Dynamic path routing to service blocks

- **PUT** `/plugins/sblock/{path:path}`

  - **Description:** Update service block operations via plugin
  - **Headers:** `Authorization: Bearer <token>`
  - **Parameters:** Dynamic path routing to service blocks

- **DELETE** `/plugins/sblock/{path:path}`
  - **Description:** Delete service block operations via plugin
  - **Headers:** `Authorization: Bearer <token>`
  - **Parameters:** Dynamic path routing to service blocks

---

## Service Block Management

**Base Path:** `/sblock`

### Service Block Operations

- **GET** `/sblock/add/{sblock_ip}/{username}`

  - **Description:** Add a new service block to the system
  - **Parameters:**
    - `sblock_ip`: IP address of the service block
    - `username`: Username for authentication

- **GET** `/sblock/remove/{sblock_ip}/{username}`
  - **Description:** Remove a service block from the system
  - **Parameters:**
    - `sblock_ip`: IP address of the service block
    - `username`: Username for authentication

### Plugin-based Service Block Management

- **GET** `/api/plugins/sblock/add/{username}`

  - **Description:** Add service block via plugin system (Admin only)
  - **Headers:** `Authorization: Bearer <token>`

- **GET** `/api/plugins/sblock/remove/{username}`
  - **Description:** Remove service block via plugin system (Admin only)
  - **Headers:** `Authorization: Bearer <token>`

---

## Debug & Testing Routes

### System Debug

- **GET** `/debug/routes`

  - **Description:** List all available routes in the system
  - **Response:** Array of route information

- **GET** `/api/debug/routes`

  - **Description:** Debug endpoint to check registered API routes
  - **Response:** `{"total_routes": number, "routes": [...], "api_routes": [...]}`

- **GET** `/service_presence`
  - **Description:** Check presence and status of connected services
  - **Response:** Service availability information

### API Testing

- **GET** `/api/test/simple`

  - **Description:** Simple test endpoint to verify API routing
  - **Response:** `{"status": "success", "message": "API routing is working", "timestamp": "..."}`

- **GET** `/api/test/connection`
  - **Description:** Test Core to Management service communication
  - **Response:** Connection test results

### Routing Debug

- **GET** `/api/debug/routing/{endpoint:path}`
  - **Description:** Debug endpoint to test routing configuration
  - **Parameters:** `endpoint` - the endpoint path to test
  - **Response:** Routing information and service mapping

---

## Direct Service Routes

### Direct Vehicle Access

- **GET** `/api/vehicles/direct`
  - **Description:** Direct access to vehicle data bypassing service proxy
  - **Query Params:** `limit`
  - **Response:** Vehicle data directly from management service

### Direct Management Routes

- **GET** `/api/vehicles` (Management Direct)

  - **Description:** Direct vehicles endpoint for testing routing
  - **Query Params:** `limit`

- **GET** `/api/drivers` (Management Direct)

  - **Description:** Fetch drivers from management service
  - **Query Params:** `limit`

- **PUT** `/api/drivers/{driver_id}` (Management Direct)
  - **Description:** Update driver by forwarding to management service
  - **Body:** Driver update data

---

## Authentication & Authorization

### Header Format

All authenticated endpoints require the `Authorization` header:

```
Authorization: Bearer <jwt_token>
```

### Role-based Access

- **Admin:** Full access to all endpoints
- **Fleet Manager:** Access to vehicle and driver management, limited analytics
- **Driver:** Limited access to assigned vehicles and personal data
- **Viewer:** Read-only access to basic information

### Permission System

The system uses a combination of:

- Role-based permissions
- Custom permission assignments
- Resource-level access control

---

## Error Responses

### Standard Error Format

```json
{
  "detail": "Error message description",
  "status_code": 400
}
```

### Common HTTP Status Codes

- **200:** Success
- **201:** Created
- **400:** Bad Request
- **401:** Unauthorized (authentication required)
- **403:** Forbidden (insufficient permissions)
- **404:** Not Found
- **422:** Validation Error
- **500:** Internal Server Error
- **503:** Service Unavailable

---

## Rate Limiting & Performance

### Request Limits

- Authentication endpoints: Limited to prevent brute force attacks
- WebSocket connections: Limited concurrent connections per user
- Analytics endpoints: Cached responses to improve performance

### Timeouts

- Service communication: 10-15 seconds default timeout
- File uploads: 30 seconds timeout
- WebSocket connections: Configurable keep-alive

---

## Development & Testing

### Environment Variables

- `SECURITY_URL`: URL for the Security service (default: `http://security_service:8000`)
- Core service ports and service block URLs are configurable

### Testing Endpoints

Use the `/api/test/*` and `/debug/*` endpoints for development and testing purposes. These should be disabled or secured in production environments.

### WebSocket Testing

Connect to `/ws/vehicles` endpoint for real-time vehicle tracking. Use the `/test/live_vehicles` endpoint to verify WebSocket functionality.

---

## Notes

1. **Service Proxy Pattern:** Most `/api/*` routes are proxied to appropriate service blocks (Management, GPS, Trip Planning, etc.)

2. **Authentication Proxy:** All `/auth/*` routes are proxied to the Security service block

3. **Real-time Communication:** WebSocket routes provide real-time updates for vehicle tracking

4. **Plugin System:** Dynamic plugin management allows for extensible functionality

5. **Microservice Architecture:** Core acts as an API gateway routing requests to specialized service blocks

6. **RabbitMQ Integration:** Background communication between services uses RabbitMQ message queuing

This documentation reflects the current state of the SAMFMS Core service API. For the most up-to-date route information, use the `/debug/routes` endpoint.
