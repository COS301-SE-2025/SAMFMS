# Maintenance Analytics API Documentation

This document provides comprehensive documentation for all available analytics endpoints in the Maintenance Service.

## Base URL

```
/api/v1/maintenance/analytics
```

## Authentication

All endpoints require authentication. Include the JWT token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## Permissions

All analytics endpoints require the `maintenance.analytics.read` permission.

---

## Endpoints Overview

### 1. Dashboard Overview

**GET** `/dashboard`

Get maintenance dashboard overview data including key metrics and summaries.

**Response Format:**

```json
{
  "status": "success",
  "data": {
    "overview": {
      "total_vehicles": 150,
      "overdue_maintenance": 12,
      "upcoming_maintenance": 25,
      "expiring_licenses": 8,
      "expired_licenses": 3
    },
    "costs": {
      "total_cost_last_30_days": 45670.50,
      "average_cost": 1523.35,
      "total_jobs": 30
    },
    "recent_activity": [...]
  }
}
```

### 2. Cost Analytics

**GET** `/costs`

Get maintenance cost analytics with time-based grouping and filtering.

**Query Parameters:**

- `vehicle_id` (optional): Filter by specific vehicle ID
- `start_date` (optional): Start date for analysis (ISO format)
- `end_date` (optional): End date for analysis (ISO format)
- `group_by` (optional): Time grouping - `day`, `week`, or `month` (default: `month`)

**Example Request:**

```
GET /costs?start_date=2024-01-01&end_date=2024-12-31&group_by=month
```

**Response Format:**

```json
{
  "status": "success",
  "data": {
    "cost_timeline": [
      {
        "period": "2024-01",
        "total_cost": 12450.0,
        "record_count": 15
      }
    ],
    "summary": {
      "total_cost": 89750.5,
      "average_monthly_cost": 7479.21
    }
  }
}
```

### 3. Total Cost for Timeframe

**GET** `/timeframe/total-cost`

Get total maintenance cost within a specific timeframe.

**Query Parameters:**

- `start_date` (required): Start date (ISO format)
- `end_date` (required): End date (ISO format)

**Example Request:**

```
GET /timeframe/total-cost?start_date=2024-01-01T00:00:00Z&end_date=2024-01-31T23:59:59Z
```

**Response Format:**

```json
{
  "status": "success",
  "data": {
    "total_cost": 15420.75,
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-01-31T23:59:59Z",
    "period_days": 31
  }
}
```

### 4. Records Count for Timeframe

**GET** `/timeframe/records-count`

Get number of maintenance records within a specific timeframe.

**Query Parameters:**

- `start_date` (required): Start date (ISO format)
- `end_date` (required): End date (ISO format)

**Example Request:**

```
GET /timeframe/records-count?start_date=2024-01-01T00:00:00Z&end_date=2024-01-31T23:59:59Z
```

**Response Format:**

```json
{
  "status": "success",
  "data": {
    "records_count": 45,
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-01-31T23:59:59Z",
    "period_days": 31
  }
}
```

### 5. Vehicles Serviced in Timeframe

**GET** `/timeframe/vehicles-serviced`

Get number of unique vehicles serviced within a specific timeframe.

**Query Parameters:**

- `start_date` (required): Start date (ISO format)
- `end_date` (required): End date (ISO format)

**Example Request:**

```
GET /timeframe/vehicles-serviced?start_date=2024-01-01T00:00:00Z&end_date=2024-01-31T23:59:59Z
```

**Response Format:**

```json
{
  "status": "success",
  "data": {
    "vehicles_serviced": 32,
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-01-31T23:59:59Z",
    "period_days": 31
  }
}
```

### 6. Maintenance Records by Type

**GET** `/maintenance-by-type`

Get maintenance records grouped by maintenance type with cost analytics.

**Query Parameters:**

- `start_date` (optional): Start date filter (ISO format)
- `end_date` (optional): End date filter (ISO format)

**Example Request:**

```
GET /maintenance-by-type?start_date=2024-01-01T00:00:00Z&end_date=2024-12-31T23:59:59Z
```

**Response Format:**

```json
{
  "status": "success",
  "data": {
    "records_by_type": [
      {
        "maintenance_type": "oil_change",
        "count": 125,
        "total_cost": 8750.0,
        "average_cost": 70.0
      },
      {
        "maintenance_type": "brake_service",
        "count": 45,
        "total_cost": 15670.5,
        "average_cost": 348.23
      }
    ],
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-12-31T23:59:59Z",
    "total_types": 8
  }
}
```

### 7. Maintenance Cost Outliers

**GET** `/cost-outliers`

Get maintenance records with outlier costs (significantly above average).

**Query Parameters:**

- `start_date` (optional): Start date filter (ISO format)
- `end_date` (optional): End date filter (ISO format)
- `threshold_multiplier` (optional): Outlier threshold multiplier (default: 2.0, range: 1.0-5.0)

**Example Request:**

```
GET /cost-outliers?threshold_multiplier=2.5&start_date=2024-01-01T00:00:00Z
```

**Response Format:**

```json
{
  "status": "success",
  "data": {
    "outliers": [
      {
        "id": "507f1f77bcf86cd799439011",
        "vehicle_id": "vehicle_123",
        "maintenance_type": "engine_service",
        "title": "Major Engine Overhaul",
        "cost": 8500.0,
        "created_at": "2024-01-15T10:30:00Z",
        "cost_multiplier": 4.25
      }
    ],
    "statistics": {
      "average_cost": 2000.0,
      "threshold": 5000.0,
      "threshold_multiplier": 2.5,
      "total_records": 150,
      "outlier_count": 3
    }
  },
  "metadata": {
    "threshold_multiplier": 2.5,
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": null
  }
}
```

### 8. Maintenance Per Vehicle in Timeframe

**GET** `/timeframe/maintenance-per-vehicle`

Get number of maintenance records per vehicle within a specific timeframe.

**Query Parameters:**

- `start_date` (required): Start date (ISO format)
- `end_date` (required): End date (ISO format)

**Example Request:**

```
GET /timeframe/maintenance-per-vehicle?start_date=2024-01-01T00:00:00Z&end_date=2024-01-31T23:59:59Z
```

**Response Format:**

```json
{
  "status": "success",
  "data": {
    "maintenance_per_vehicle": [
      {
        "vehicle_id": "vehicle_123",
        "maintenance_count": 8,
        "total_cost": 2450.0,
        "average_cost": 306.25,
        "maintenance_types": ["oil_change", "brake_service", "tire_rotation"],
        "types_count": 3,
        "latest_maintenance": "2024-01-28T14:30:00Z",
        "earliest_maintenance": "2024-01-03T09:15:00Z"
      }
    ],
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-01-31T23:59:59Z",
    "period_days": 31,
    "total_vehicles": 25
  }
}
```

### 9. Maintenance Trends

**GET** `/trends`

Get maintenance trends over time with pattern analysis.

**Query Parameters:**

- `days` (optional): Number of days to analyze (30-365, default: 90)

**Example Request:**

```
GET /trends?days=180
```

**Response Format:**

```json
{
  "status": "success",
  "data": {
    "trend_data": [
      {
        "date": "2024-01-01",
        "maintenance_count": 12,
        "total_cost": 2340.0
      }
    ],
    "patterns": {
      "peak_day": "Monday",
      "average_daily_cost": 890.5,
      "trend_direction": "increasing"
    }
  }
}
```

### 10. Vendor Analytics

**GET** `/vendors`

Get vendor performance analytics and cost comparisons.

**Response Format:**

```json
{
  "status": "success",
  "data": {
    "vendor_performance": [
      {
        "vendor_id": "vendor_001",
        "total_jobs": 45,
        "total_cost": 15670.50,
        "average_cost": 348.23,
        "average_rating": 4.2
      }
    ],
    "cost_comparison": {...}
  }
}
```

### 11. License Analytics

**GET** `/licenses`

Get license expiry and compliance analytics.

**Response Format:**

```json
{
  "status": "success",
  "data": {
    "licenses_by_type": [
      {
        "_id": "driver_license",
        "count": 150,
        "expired": 3,
        "expiring_soon": 8
      }
    ],
    "expiry_timeline": {
      "expiring_30_days": 15,
      "expiring_60_days": 28,
      "expiring_90_days": 41
    },
    "total_active_licenses": 450
  }
}
```

### 12. Vehicle Maintenance Summary

**GET** `/summary/vehicle/{vehicle_id}`

Get maintenance summary for a specific vehicle.

**Path Parameters:**

- `vehicle_id` (required): The vehicle ID

**Query Parameters:**

- `start_date` (optional): Start date for summary (ISO format)
- `end_date` (optional): End date for summary (ISO format)

**Example Request:**

```
GET /summary/vehicle/vehicle_123?start_date=2024-01-01&end_date=2024-12-31
```

### 13. Maintenance KPIs

**GET** `/metrics/kpi`

Get key performance indicators for maintenance operations.

**Response Format:**

```json
{
  "status": "success",
  "data": {
    "operational_kpis": {
      "total_vehicles": 150,
      "overdue_maintenance_count": 12,
      "upcoming_maintenance_count": 25,
      "overdue_percentage": 8.0,
      "maintenance_compliance": 92.0
    },
    "financial_kpis": {
      "total_cost_last_30_days": 45670.5,
      "average_cost_per_job": 1523.35,
      "total_jobs_last_30_days": 30,
      "cost_per_vehicle": 304.47
    },
    "compliance_kpis": {
      "expiring_licenses": 8,
      "expired_licenses": 3,
      "license_compliance_rate": 98.0
    }
  }
}
```

---

## Date Format Requirements

All date parameters should be provided in ISO 8601 format:

- With timezone: `2024-01-01T00:00:00Z`
- Without timezone: `2024-01-01T00:00:00` (treated as UTC)
- Date only: `2024-01-01` (treated as start of day UTC)

## Error Responses

All endpoints follow a consistent error response format:

```json
{
  "status": "error",
  "message": "Error description",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_123456789"
}
```

## Common HTTP Status Codes

- `200 OK`: Successful request
- `400 Bad Request`: Invalid parameters or request format
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Rate Limiting

All endpoints are subject to rate limiting:

- 100 requests per minute per user
- 1000 requests per hour per user

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Caching

Analytics data is cached for performance:

- Dashboard data: 5 minutes
- Cost analytics: 15 minutes
- Trend data: 1 hour
- KPI data: 10 minutes

Cache headers indicate freshness:

```
Cache-Control: public, max-age=300
ETag: "abc123"
Last-Modified: Mon, 01 Jan 2024 12:00:00 GMT
```

## Example Usage

### Python Example

```python
import requests
from datetime import datetime, timedelta

# Authentication
headers = {
    'Authorization': 'Bearer your-jwt-token',
    'Content-Type': 'application/json'
}

# Get total cost for last month
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

response = requests.get(
    'https://api.samfms.com/api/v1/maintenance/analytics/timeframe/total-cost',
    params={
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat()
    },
    headers=headers
)

if response.status_code == 200:
    data = response.json()
    total_cost = data['data']['total_cost']
    print(f"Total maintenance cost for last 30 days: ${total_cost:,.2f}")
```

### JavaScript Example

```javascript
const apiUrl = 'https://api.samfms.com/api/v1/maintenance/analytics';
const token = 'your-jwt-token';

// Get maintenance records by type
async function getMaintenanceByType() {
  try {
    const response = await fetch(`${apiUrl}/maintenance-by-type`, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    const data = await response.json();
    console.log('Maintenance by type:', data.data.records_by_type);
  } catch (error) {
    console.error('Error:', error);
  }
}
```

## Support

For API support and questions:

- Documentation: `/docs` (Swagger UI)
- Health Check: `/health`
- Status Page: `/status`

---

_Last Updated: August 2025_
_Version: 2.0.0_
