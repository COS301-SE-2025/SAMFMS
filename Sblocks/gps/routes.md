# Maintenance Service Routes Documentation

## Overview

The SAMFMS Maintenance Service provides comprehensive maintenance management capabilities for fleet vehicles. It handles maintenance records, license tracking, analytics, and automated notifications through a RESTful API.

## Base URL

- Local Development: `http://localhost:21007`
- Production: Uses port from `MAINTENANCE_SERVICE_PORT` environment variable

## Authentication

All endpoints require JWT Bearer token authentication:

```
Authorization: Bearer <jwt_token>
```

## API Route Structure

### 1. Maintenance Records Management

#### **POST** `/maintenance/records/`

Creates a new maintenance record.

**Request Body:**

```json
{
  "vehicle_id": "string (required)",
  "maintenance_type": "preventive|corrective|scheduled|emergency|inspection",
  "title": "string (required)",
  "description": "string (optional)",
  "scheduled_date": "2025-07-25T10:00:00Z (required)",
  "priority": "low|medium|high|critical",
  "estimated_cost": 250.0,
  "estimated_duration": 2,
  "assigned_technician": "string",
  "vendor_id": "string",
  "mileage_at_service": 50000
}
```

**Response:**

```json
{
  "success": true,
  "message": "Maintenance record created successfully",
  "data": {
    "id": "maintenance_record_id",
    "vehicle_id": "vehicle_001",
    "status": "scheduled",
    "created_at": "2025-07-17T10:00:00Z",
    ...
  }
}
```

#### **GET** `/maintenance/records/`

Retrieves maintenance records with filtering and pagination.

**Query Parameters:**

- `vehicle_id` (optional): Filter by vehicle ID
- `status` (optional): Filter by status (scheduled, in_progress, completed, cancelled, overdue)
- `maintenance_type` (optional): Filter by maintenance type
- `priority` (optional): Filter by priority
- `scheduled_from` (optional): Filter by scheduled date from (ISO format)
- `scheduled_to` (optional): Filter by scheduled date to (ISO format)
- `vendor_id` (optional): Filter by vendor
- `technician_id` (optional): Filter by technician
- `skip` (default: 0): Number of records to skip for pagination
- `limit` (default: 100, max: 1000): Number of records to return
- `sort_by` (default: scheduled_date): Field to sort by
- `sort_order` (default: desc): Sort order (asc|desc)

**Response:**

```json
{
  "success": true,
  "message": "Maintenance records retrieved successfully",
  "data": [
    {
      "id": "maint_001",
      "vehicle_id": "vehicle_001",
      "maintenance_type": "preventive",
      "status": "scheduled",
      "title": "Oil Change",
      "scheduled_date": "2025-07-25T10:00:00Z",
      "estimated_cost": 150.00,
      ...
    }
  ],
  "total": 25,
  "skip": 0,
  "limit": 100
}
```

#### **GET** `/maintenance/records/{record_id}`

Retrieves a specific maintenance record.

#### **PUT** `/maintenance/records/{record_id}`

Updates a maintenance record.

#### **DELETE** `/maintenance/records/{record_id}`

Deletes a maintenance record.

#### **GET** `/maintenance/records/vehicle/{vehicle_id}`

Retrieves maintenance records for a specific vehicle.

#### **GET** `/maintenance/records/status/overdue`

Retrieves overdue maintenance records.

#### **GET** `/maintenance/records/status/upcoming?days=7`

Retrieves upcoming maintenance records.

#### **GET** `/maintenance/records/vehicle/{vehicle_id}/history`

Retrieves maintenance history for a vehicle.

#### **GET** `/maintenance/records/costs/summary`

Retrieves maintenance cost summary.

### 2. License Management

#### **POST** `/maintenance/licenses/`

Creates a new license record.

**Request Body:**

```json
{
  "entity_id": "vehicle_001 or driver_001",
  "entity_type": "vehicle|driver",
  "license_type": "vehicle_registration|drivers_license|insurance|roadworthy_certificate",
  "license_number": "string",
  "issue_date": "2025-01-01T00:00:00Z",
  "expiry_date": "2026-01-01T00:00:00Z",
  "issuing_authority": "string",
  "cost": 500.0,
  "is_active": true
}
```

#### **GET** `/maintenance/licenses/`

Retrieves license records with filtering.

**Query Parameters:**

- `entity_id`: Filter by entity ID
- `entity_type`: Filter by entity type (vehicle/driver)
- `license_type`: Filter by license type
- `expiring_within_days`: Filter by licenses expiring within X days
- `is_active`: Filter by active status

#### **GET** `/maintenance/licenses/{record_id}`

Retrieves a specific license record.

#### **PUT** `/maintenance/licenses/{record_id}`

Updates a license record.

#### **DELETE** `/maintenance/licenses/{record_id}`

Deletes a license record.

#### **GET** `/maintenance/licenses/expiring?days=30`

Retrieves licenses expiring within specified days.

#### **GET** `/maintenance/licenses/entity/{entity_id}`

Retrieves licenses for a specific entity.

### 3. Analytics

#### **GET** `/maintenance/analytics/dashboard`

Retrieves maintenance dashboard overview data.

**Response:**

```json
{
  "success": true,
  "data": {
    "total_records": 150,
    "overdue_count": 5,
    "upcoming_count": 12,
    "completed_this_month": 25,
    "total_cost_this_month": 15000.00,
    "cost_trends": [...],
    "maintenance_by_type": {...},
    "vehicle_health_scores": [...]
  }
}
```

#### **GET** `/maintenance/analytics/costs`

Retrieves cost analytics with time-based grouping.

**Query Parameters:**

- `vehicle_id`: Filter by vehicle
- `start_date`: Start date for analysis
- `end_date`: End date for analysis
- `group_by`: Time grouping (day|week|month)

#### **GET** `/maintenance/analytics/trends?days=90`

Retrieves maintenance trends over time.

#### **GET** `/maintenance/analytics/vendors`

Retrieves vendor performance analytics.

#### **GET** `/maintenance/analytics/fleet-health`

Retrieves fleet health overview.

### 4. Notifications

#### **GET** `/maintenance/notifications/`

Retrieves notifications with filtering.

#### **POST** `/maintenance/notifications/`

Creates a new notification.

#### **PUT** `/maintenance/notifications/{notification_id}/read`

Marks a notification as read.

#### **DELETE** `/maintenance/notifications/{notification_id}`

Deletes a notification.

#### **GET** `/maintenance/notifications/unread`

Retrieves unread notifications.

### 5. Health and Monitoring

#### **GET** `/health`

Health check endpoint with dependency status.

**Response:**

```json
{
  "service": "maintenance",
  "status": "healthy",
  "timestamp": "2025-07-17T10:00:00Z",
  "version": "1.0.0",
  "dependencies": {
    "database": {
      "status": "healthy",
      "response_time_ms": 15
    },
    "rabbitmq": {
      "status": "healthy",
      "is_consuming": true
    }
  },
  "background_jobs": {
    "is_running": true,
    "active_tasks": 4,
    "status": "healthy"
  }
}
```

#### **GET** `/metrics`

Service metrics endpoint.

#### **GET** `/`

Root endpoint with service information.

## Error Handling

All endpoints return standardized error responses:

```json
{
  "success": false,
  "message": "Error description",
  "error_code": "ERROR_TYPE",
  "timestamp": "2025-07-17T10:00:00Z",
  "details": {} // Optional additional details
}
```

### Common Error Codes:

- `400`: Bad Request - Invalid input data
- `401`: Unauthorized - Invalid or missing authentication token
- `403`: Forbidden - Insufficient permissions
- `404`: Not Found - Requested resource not found
- `422`: Validation Error - Data validation failed
- `500`: Internal Server Error - Server-side error

## Request/Response Patterns

### Data Validation

- All datetime fields accept ISO 8601 format
- Cost fields must be positive numbers
- Required fields are validated before processing
- Enum values are validated against allowed options

### Pagination

- Uses `skip` and `limit` parameters
- Responses include `total`, `skip`, and `limit` metadata
- Maximum limit is 1000 records per request

### Sorting

- Default sort is by `scheduled_date` descending
- Supports sorting by any field in the response
- Sort order can be `asc` or `desc`

### Filtering

- Multiple filters can be applied simultaneously
- Date filters support range queries
- String filters support exact matches
- Supports filtering by related entities (vehicle_id, technician_id, etc.)

## Background Jobs

The service runs automated background tasks:

1. **Overdue Status Updater**: Updates maintenance records to overdue status (runs hourly)
2. **Notification Sender**: Sends scheduled notifications (runs every 15 minutes)
3. **License Expiry Checker**: Checks for expiring licenses (runs daily)
4. **Maintenance Reminder Generator**: Generates maintenance reminders (runs daily)

## Integration with Core Service

The maintenance service integrates with the SAMFMS Core service through:

1. **RabbitMQ Messaging**: Receives requests from Core via `maintenance_service_requests` queue
2. **Authentication**: Uses JWT tokens validated by Core service
3. **Service Discovery**: Registers with Core's service discovery system
4. **Request Routing**: All frontend requests go through Core's proxy routes at `/api/maintenance/*`

## Database Collections

The service uses the following MongoDB collections:

- `maintenance_records`: Primary maintenance data
- `maintenance_schedules`: Recurring maintenance templates
- `license_records`: License and certification tracking
- `notifications`: Notification history
- `vendors`: Service provider information
