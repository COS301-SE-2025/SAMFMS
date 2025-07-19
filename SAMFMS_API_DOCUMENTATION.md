# SAMFMS API Documentation

## Overview

This document provides a comprehensive overview of all available API endpoints in the SAMFMS (South African Fleet Management System) after the routing system cleanup. The system uses a simplified path-based routing architecture where requests are routed through the Core service to appropriate service blocks.

## Architecture

### Core Service (Port 8000)

- **Role**: API Gateway and request router
- **Routing**: Path-based routing to service blocks via RabbitMQ
- **Prefixes**:
  - `/management/*` → Management service block
  - `/maintenance/*` → Maintenance service block
  - `/gps/*` → GPS service block
  - `/trips/*` → Trip planning service block

### Service Blocks

- **Management Service** (Port 8001): Vehicles, drivers, analytics
- **Maintenance Service** (Port 8002): Maintenance records, licenses, notifications
- **Security Service** (Port 8003): Authentication, user management, admin functions
- **GPS Service** (Port 8004): Location tracking, geofencing
- **Trip Planning Service** (Port 8005): Route optimization, trip planning

---

## Core Service Endpoints

### Base Endpoints

#### GET `/`

- **Description**: Root endpoint with service information
- **Response**: Service info and routing configuration

#### GET `/health`

- **Description**: Health check endpoint
- **Response**: Service health status and component information

#### GET `/services`

- **Description**: List available service blocks
- **Response**: Available services and routing information

### Authentication Routes (via Core)

#### POST `/auth/signup`

- **Description**: User registration
- **Request Body**: `{full_name, email, password, role?, phoneNo?, details?, preferences?}`
- **Response**: JWT token and user information

#### POST `/auth/login`

- **Description**: User login
- **Request Body**: `{email, password}`
- **Response**: JWT token and user information

#### POST `/auth/logout`

- **Description**: User logout
- **Headers**: `Authorization: Bearer {token}`
- **Response**: Success message

#### GET `/auth/me`

- **Description**: Get current user information
- **Headers**: `Authorization: Bearer {token}`
- **Response**: User profile information

### Service Routing Endpoints

#### Route: `/management/*`

All requests with `/management` prefix are routed to the Management service block.

#### Route: `/maintenance/*`

All requests with `/maintenance` prefix are routed to the Maintenance service block.

#### Route: `/gps/*`

All requests with `/gps` prefix are routed to the GPS service block.

#### Route: `/trips/*`

All requests with `/trips` prefix are routed to the Trip planning service block.

### Debug/Development Endpoints (Development Only)

#### GET `/debug/routes`

- **Description**: List all registered routes
- **Environment**: Development only

#### GET `/test/simple`

- **Description**: Simple test endpoint
- **Environment**: Development only

#### GET `/test/connection`

- **Description**: Test database and service connections
- **Environment**: Development only

#### POST `/api/services/register`

- **Description**: Register a service with service discovery
- **Environment**: Development only

#### GET `/api/services`

- **Description**: List registered services
- **Environment**: Development only

---

## Management Service Block

### Base URL: `http://localhost:8001` (Direct) or `http://localhost:8000/management/*` (via Core)

### Vehicle Management

#### GET `/vehicles`

- **Description**: Get all vehicles with filtering and pagination
- **Query Parameters**: `skip?, limit?, status?, location?, department?`
- **Response**: List of vehicles with metadata

#### POST `/vehicles`

- **Description**: Create a new vehicle
- **Request Body**: Vehicle data object
- **Response**: Created vehicle information

#### GET `/vehicles/{vehicle_id}`

- **Description**: Get specific vehicle by ID
- **Path Parameters**: `vehicle_id`
- **Response**: Vehicle details

#### PUT `/vehicles/{vehicle_id}`

- **Description**: Update vehicle information
- **Path Parameters**: `vehicle_id`
- **Request Body**: Updated vehicle data
- **Response**: Updated vehicle information

#### DELETE `/vehicles/{vehicle_id}`

- **Description**: Delete a vehicle
- **Path Parameters**: `vehicle_id`
- **Response**: Success confirmation

#### GET `/vehicles/search/{query}`

- **Description**: Search vehicles by query
- **Path Parameters**: `query`
- **Response**: Matching vehicles

### Driver Management

#### GET `/drivers`

- **Description**: Get all drivers with filtering and pagination
- **Query Parameters**: `skip?, limit?, status?, department?`
- **Response**: List of drivers with metadata

#### POST `/drivers`

- **Description**: Create a new driver
- **Request Body**: Driver data object
- **Response**: Created driver information

#### GET `/drivers/{driver_id}`

- **Description**: Get specific driver by ID
- **Path Parameters**: `driver_id`
- **Response**: Driver details

#### PUT `/drivers/{driver_id}`

- **Description**: Update driver information
- **Path Parameters**: `driver_id`
- **Request Body**: Updated driver data
- **Response**: Updated driver information

#### DELETE `/drivers/{driver_id}`

- **Description**: Delete a driver
- **Path Parameters**: `driver_id`
- **Response**: Success confirmation

### Analytics

#### GET `/analytics/dashboard`

- **Description**: Get comprehensive dashboard analytics
- **Query Parameters**: `use_cache?`
- **Response**: Dashboard data with KPIs

#### GET `/analytics/fleet-utilization`

- **Description**: Get fleet utilization metrics
- **Query Parameters**: `period?, use_cache?`
- **Response**: Fleet utilization data

#### GET `/analytics/vehicle-usage`

- **Description**: Get vehicle usage statistics
- **Query Parameters**: `period?, vehicle_id?, use_cache?`
- **Response**: Vehicle usage metrics

#### GET `/analytics/assignment-metrics`

- **Description**: Get assignment metrics and trends
- **Query Parameters**: `period?, department?, use_cache?`
- **Response**: Assignment analytics

#### GET `/analytics/driver-performance`

- **Description**: Get driver performance metrics
- **Query Parameters**: `period?, driver_id?, use_cache?`
- **Response**: Driver performance data

#### GET `/analytics/cost-analytics`

- **Description**: Get cost analysis and trends
- **Query Parameters**: `period?, category?, use_cache?`
- **Response**: Cost analytics

#### GET `/analytics/status-breakdown`

- **Description**: Get status breakdown across fleet
- **Response**: Status distribution data

#### GET `/analytics/incidents`

- **Description**: Get incident analytics
- **Query Parameters**: `period?, severity?`
- **Response**: Incident data and trends

#### GET `/analytics/department-location`

- **Description**: Get analytics by department and location
- **Query Parameters**: `department?, location?`
- **Response**: Department/location analytics

---

## Maintenance Service Block

### Base URL: `http://localhost:8002` (Direct) or `http://localhost:8000/maintenance/*` (via Core)

### Maintenance Records

#### GET `/maintenance/records`

- **Description**: Get maintenance records with filtering
- **Query Parameters**: `vehicle_id?, status?, maintenance_type?, priority?, scheduled_from?, scheduled_to?, vendor_id?, technician_id?, skip?, limit?, sort_by?, sort_order?`
- **Response**: List of maintenance records

#### POST `/maintenance/records`

- **Description**: Create a new maintenance record
- **Request Body**: Maintenance record data
- **Response**: Created maintenance record

#### GET `/maintenance/records/{record_id}`

- **Description**: Get specific maintenance record
- **Path Parameters**: `record_id`
- **Response**: Maintenance record details

#### PUT `/maintenance/records/{record_id}`

- **Description**: Update maintenance record
- **Path Parameters**: `record_id`
- **Request Body**: Updated maintenance data
- **Response**: Updated maintenance record

#### DELETE `/maintenance/records/{record_id}`

- **Description**: Delete maintenance record
- **Path Parameters**: `record_id`
- **Response**: Success confirmation

#### GET `/maintenance/records/vehicle/{vehicle_id}`

- **Description**: Get maintenance records for specific vehicle
- **Path Parameters**: `vehicle_id`
- **Query Parameters**: `skip?, limit?`
- **Response**: Vehicle-specific maintenance records

#### GET `/maintenance/records/status/overdue`

- **Description**: Get overdue maintenance records
- **Response**: List of overdue maintenance items

#### GET `/maintenance/records/status/upcoming`

- **Description**: Get upcoming maintenance records
- **Query Parameters**: `days?` (default: 7)
- **Response**: List of upcoming maintenance items

### License Management

#### GET `/maintenance/licenses`

- **Description**: Get license records with filtering
- **Query Parameters**: `entity_id?, entity_type?, license_type?, expiring_within_days?, is_active?, skip?, limit?, sort_by?, sort_order?`
- **Response**: List of license records

#### POST `/maintenance/licenses`

- **Description**: Create a new license record
- **Request Body**: License data
- **Response**: Created license record

#### GET `/maintenance/licenses/{record_id}`

- **Description**: Get specific license record
- **Path Parameters**: `record_id`
- **Response**: License record details

#### GET `/maintenance/licenses/expiring`

- **Description**: Get licenses expiring soon
- **Query Parameters**: `days?` (default: 30)
- **Response**: List of expiring licenses

### Maintenance Analytics

#### GET `/maintenance/analytics/dashboard`

- **Description**: Get maintenance dashboard overview
- **Response**: Maintenance overview data

#### GET `/maintenance/analytics/costs`

- **Description**: Get maintenance cost analytics
- **Query Parameters**: `vehicle_id?, start_date?, end_date?, group_by?`
- **Response**: Cost analytics data

#### GET `/maintenance/analytics/trends`

- **Description**: Get maintenance trends over time
- **Query Parameters**: `days?` (default: 90)
- **Response**: Maintenance trends data

#### GET `/maintenance/analytics/licenses`

- **Description**: Get license expiry and compliance analytics
- **Response**: License analytics data

### Notifications

#### GET `/maintenance/notifications/pending`

- **Description**: Get pending maintenance notifications
- **Response**: List of pending notifications

#### POST `/maintenance/notifications/process`

- **Description**: Process and send pending notifications
- **Response**: Processing results

---

## Security Service Block

### Base URL: `http://localhost:8003` (Direct) or via Core `/auth/*` routes

### Authentication

#### POST `/auth/signup`

- **Description**: User registration
- **Request Body**: `{full_name, email, password, role?, phoneNo?, details?, preferences?}`
- **Response**: JWT token and user information

#### POST `/auth/login`

- **Description**: User login
- **Request Body**: `{email, password}`
- **Response**: JWT token and user information

#### POST `/auth/logout`

- **Description**: User logout
- **Headers**: `Authorization: Bearer {token}`
- **Response**: Success message

#### GET `/auth/me`

- **Description**: Get current user information
- **Headers**: `Authorization: Bearer {token}`
- **Response**: User profile information

#### GET `/auth/user-exists`

- **Description**: Check if user exists
- **Query Parameters**: `email`
- **Response**: Boolean indicating user existence

#### GET `/auth/users/count`

- **Description**: Get total user count
- **Response**: User count information

#### POST `/auth/verify-token`

- **Description**: Verify JWT token validity
- **Request Body**: `{token}`
- **Response**: Token validation result

#### GET `/auth/roles`

- **Description**: Get available user roles
- **Response**: List of available roles

#### POST `/auth/update-preferences`

- **Description**: Update user preferences
- **Headers**: `Authorization: Bearer {token}`
- **Request Body**: Preferences object
- **Response**: Updated preferences

#### POST `/auth/update-profile`

- **Description**: Update user profile
- **Headers**: `Authorization: Bearer {token}`
- **Request Body**: Profile data
- **Response**: Updated profile information

#### POST `/auth/change-password`

- **Description**: Change user password
- **Headers**: `Authorization: Bearer {token}`
- **Request Body**: `{current_password, new_password, confirm_password}`
- **Response**: Success confirmation

#### POST `/auth/upload-profile-picture`

- **Description**: Upload profile picture
- **Headers**: `Authorization: Bearer {token}`
- **Request Body**: Multipart form with image file
- **Response**: Updated profile with picture URL

### User Management

#### GET `/users`

- **Description**: Get all users (admin only)
- **Headers**: `Authorization: Bearer {token}`
- **Query Parameters**: `skip?, limit?`
- **Response**: List of users

#### GET `/users/{user_id}`

- **Description**: Get specific user (admin only)
- **Headers**: `Authorization: Bearer {token}`
- **Path Parameters**: `user_id`
- **Response**: User details

#### PUT `/users/{user_id}/permissions`

- **Description**: Update user permissions (admin only)
- **Headers**: `Authorization: Bearer {token}`
- **Path Parameters**: `user_id`
- **Request Body**: Permissions object
- **Response**: Updated permissions

#### PUT `/users/{user_id}/profile`

- **Description**: Update user profile (admin only)
- **Headers**: `Authorization: Bearer {token}`
- **Path Parameters**: `user_id`
- **Request Body**: Profile data
- **Response**: Updated profile

#### POST `/users/{user_id}/change-password`

- **Description**: Change user password (admin only)
- **Headers**: `Authorization: Bearer {token}`
- **Path Parameters**: `user_id`
- **Request Body**: `{new_password, confirm_password}`
- **Response**: Success confirmation

#### DELETE `/users/{user_id}`

- **Description**: Delete user (admin only)
- **Headers**: `Authorization: Bearer {token}`
- **Path Parameters**: `user_id`
- **Response**: Success confirmation

### Administration

#### GET `/admin/dashboard`

- **Description**: Get admin dashboard data
- **Headers**: `Authorization: Bearer {token}` (admin role required)
- **Response**: Admin dashboard information

#### GET `/admin/users`

- **Description**: Get all users with admin details
- **Headers**: `Authorization: Bearer {token}` (admin role required)
- **Response**: Detailed user list

#### GET `/admin/audit-logs`

- **Description**: Get audit logs
- **Headers**: `Authorization: Bearer {token}` (admin role required)
- **Query Parameters**: `skip?, limit?, user_id?, action?, start_date?, end_date?`
- **Response**: Audit log entries

#### POST `/admin/users/{user_id}/activate`

- **Description**: Activate/deactivate user
- **Headers**: `Authorization: Bearer {token}` (admin role required)
- **Path Parameters**: `user_id`
- **Request Body**: `{is_active: boolean}`
- **Response**: Success confirmation

---

## GPS Service Block

### Base URL: `http://localhost:8004` (Direct) or `http://localhost:8000/gps/*` (via Core)

> **Note**: GPS service routes are handled by the GPS service block. Detailed endpoints would be defined in the GPS service implementation.

### Expected GPS Endpoints:

#### GET `/gps/locations`

- **Description**: Get current vehicle locations
- **Response**: List of vehicle locations

#### GET `/gps/locations/{vehicle_id}`

- **Description**: Get specific vehicle location
- **Path Parameters**: `vehicle_id`
- **Response**: Vehicle location data

#### GET `/gps/history/{vehicle_id}`

- **Description**: Get vehicle location history
- **Path Parameters**: `vehicle_id`
- **Query Parameters**: `start_date?, end_date?`
- **Response**: Location history

#### GET `/gps/geofences`

- **Description**: Get defined geofences
- **Response**: List of geofences

#### POST `/gps/geofences`

- **Description**: Create new geofence
- **Request Body**: Geofence data
- **Response**: Created geofence

---

## Trip Planning Service Block

### Base URL: `http://localhost:8005` (Direct) or `http://localhost:8000/trips/*` (via Core)

> **Note**: Trip planning service routes are handled by the Trip Planning service block. Detailed endpoints would be defined in the Trip Planning service implementation.

### Expected Trip Planning Endpoints:

#### GET `/trips/routes`

- **Description**: Get optimized routes
- **Response**: List of routes

#### POST `/trips/plan`

- **Description**: Create new trip plan
- **Request Body**: Trip planning data
- **Response**: Optimized trip plan

#### GET `/trips/{trip_id}`

- **Description**: Get specific trip details
- **Path Parameters**: `trip_id`
- **Response**: Trip information

#### PUT `/trips/{trip_id}`

- **Description**: Update trip plan
- **Path Parameters**: `trip_id`
- **Request Body**: Updated trip data
- **Response**: Updated trip information

---

## Common Response Format

All API responses follow a standardized format:

```json
{
  "success": true,
  "data": {
    // Response data
  },
  "message": "Success message",
  "timestamp": "2024-01-01T12:00:00Z",
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "pages": 5
  }
}
```

## Error Response Format

Error responses follow this format:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Error description",
    "details": "Additional error details"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Authentication

Most endpoints require authentication via JWT tokens:

```
Authorization: Bearer {jwt_token}
```

Tokens are obtained through the `/auth/login` endpoint and should be included in the Authorization header for protected routes.

## Rate Limiting

All services implement rate limiting:

- **Management Service**: 120 requests per minute
- **Maintenance Service**: 120 requests per minute
- **Security Service**: 100 requests per minute

## Status Codes

- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `422`: Validation Error
- `429`: Too Many Requests
- `500`: Internal Server Error
- `502`: Bad Gateway (Service communication error)
- `504`: Gateway Timeout (Service timeout)

---

## Updated After Route Cleanup

✅ **Removed API Prefixes**: All `/api/v1` and `/api` prefixes have been removed from service routes
✅ **Simplified Routing**: Core service uses path-based routing (`/management/*`, `/maintenance/*`, etc.)
✅ **Management Service**: Only provides `/vehicles`, `/drivers`, and `/analytics` routes
✅ **Clean Architecture**: Clear separation between Core gateway and service blocks
