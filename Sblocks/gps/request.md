# Maintenance Service Request/Response Models

## Overview

This document details the request and response models used by the SAMFMS Maintenance Service. All models use Pydantic for validation and serialization, ensuring type safety and automatic API documentation.

## Base Response Models

### DataResponse

Used for single item responses.

```python
{
  "success": bool,
  "message": str,
  "data": Any,
  "timestamp": str (ISO format)
}
```

### ListResponse

Used for paginated list responses.

```python
{
  "success": bool,
  "message": str,
  "data": List[Any],
  "total": int,
  "skip": int,
  "limit": int,
  "timestamp": str (ISO format)
}
```

### ErrorResponse

Used for error responses.

```python
{
  "success": false,
  "message": str,
  "error_code": str,
  "details": dict (optional),
  "timestamp": str (ISO format)
}
```

### AnalyticsResponse

Used for analytics data responses.

```python
{
  "success": bool,
  "message": str,
  "data": dict,
  "metadata": dict (optional),
  "timestamp": str (ISO format)
}
```

## Maintenance Records

### CreateMaintenanceRecordRequest

```python
{
  "vehicle_id": str,                              # Required
  "maintenance_type": str,                        # Required - Enum: preventive, corrective, scheduled, emergency, inspection
  "title": str,                                   # Required
  "description": str,                             # Optional
  "scheduled_date": str,                          # Required - ISO datetime format
  "priority": str,                                # Optional - Enum: low, medium, high, critical (default: medium)
  "estimated_duration": int,                      # Optional - Hours
  "estimated_cost": float,                        # Optional
  "assigned_technician": str,                     # Optional - Technician ID
  "technician_name": str,                         # Optional - Technician display name
  "vendor_id": str,                               # Optional - Vendor ID
  "vendor_name": str,                             # Optional - Vendor display name
  "mileage_at_service": int,                      # Optional - Current vehicle mileage
  "parts_used": List[dict],                       # Optional - List of parts
  "notes": str                                    # Optional - Additional notes
}
```

### UpdateMaintenanceRecordRequest

All fields optional - only provided fields will be updated.

```python
{
  "maintenance_type": str,                        # Optional - Enum: preventive, corrective, scheduled, emergency, inspection
  "title": str,                                   # Optional
  "description": str,                             # Optional
  "scheduled_date": str,                          # Optional - ISO datetime format
  "actual_start_date": str,                       # Optional - ISO datetime format
  "actual_completion_date": str,                  # Optional - ISO datetime format
  "status": str,                                  # Optional - Enum: scheduled, in_progress, completed, cancelled, overdue
  "priority": str,                                # Optional - Enum: low, medium, high, critical
  "estimated_duration": int,                      # Optional - Hours
  "estimated_cost": float,                        # Optional
  "actual_cost": float,                           # Optional
  "labor_cost": float,                            # Optional
  "parts_cost": float,                            # Optional
  "assigned_technician": str,                     # Optional - Technician ID
  "technician_name": str,                         # Optional - Technician display name
  "vendor_id": str,                               # Optional - Vendor ID
  "vendor_name": str,                             # Optional - Vendor display name
  "mileage_at_service": int,                      # Optional - Current vehicle mileage
  "next_service_mileage": int,                    # Optional - Next service mileage
  "work_performed": str,                          # Optional - Description of work done
  "parts_used": List[dict],                       # Optional - List of parts used
  "warranty_info": dict,                          # Optional - Warranty information
  "photos": List[str],                            # Optional - Photo URLs/paths
  "documents": List[str],                         # Optional - Document URLs/paths
  "notes": str                                    # Optional - Additional notes
}
```

### MaintenanceRecordResponse

```python
{
  "id": str,                                      # Maintenance record ID
  "vehicle_id": str,                              # Vehicle identifier
  "maintenance_type": str,                        # Enum: preventive, corrective, scheduled, emergency, inspection
  "status": str,                                  # Enum: scheduled, in_progress, completed, cancelled, overdue
  "priority": str,                                # Enum: low, medium, high, critical

  # Scheduling Information
  "scheduled_date": str,                          # ISO datetime format
  "estimated_duration": int,                      # Hours
  "actual_start_date": str,                       # ISO datetime format (nullable)
  "actual_completion_date": str,                  # ISO datetime format (nullable)

  # Description and Details
  "title": str,                                   # Maintenance task title
  "description": str,                             # Detailed description (nullable)
  "work_performed": str,                          # Work that was performed (nullable)
  "notes": str,                                   # Additional notes (nullable)

  # Cost Tracking
  "estimated_cost": float,                        # Estimated cost (nullable)
  "actual_cost": float,                           # Actual cost incurred (nullable)
  "labor_cost": float,                            # Labor cost (nullable)
  "parts_cost": float,                            # Parts cost (nullable)
  "other_costs": float,                           # Other miscellaneous costs (nullable)
  "total_cost": float,                            # Computed total cost (nullable)

  # Personnel and Vendor Information
  "assigned_technician": str,                     # Assigned technician ID (nullable)
  "technician_name": str,                         # Assigned technician name (nullable)
  "vendor_id": str,                               # Service vendor ID (nullable)
  "vendor_name": str,                             # Service vendor name (nullable)
  "service_provider": str,                        # Service provider name (nullable)

  # Mileage Information
  "mileage_at_service": int,                      # Vehicle mileage at service (nullable)
  "next_service_mileage": int,                    # Next service due at mileage (nullable)
  "odometer_reading": int,                        # Odometer reading at service (nullable)

  # Parts and Materials
  "parts_used": List[dict],                       # Parts used in maintenance (nullable)
  "warranty_info": dict,                          # Warranty information (nullable)

  # Images and Documents
  "photos": List[str],                            # Photo URLs/paths (nullable)
  "documents": List[str],                         # Document URLs/paths (nullable)

  # Metadata
  "created_at": str,                              # ISO datetime format
  "updated_at": str,                              # ISO datetime format
  "created_by": str,                              # User who created the record (nullable)
  "updated_by": str,                              # User who last updated the record (nullable)

  # Recurring Maintenance
  "is_recurring": bool,                           # Whether this is part of recurring maintenance
  "recurrence_interval": int,                     # Recurrence interval in days (nullable)
  "recurrence_type": str,                         # Type of recurrence (nullable)
  "parent_schedule_id": str,                      # Parent schedule if recurring (nullable)

  # Computed Fields
  "is_overdue": bool,                             # Whether maintenance is overdue (nullable)
  "days_until_due": int,                          # Days until due (nullable)
}
```

## License Management

### CreateLicenseRecordRequest

```python
{
  "entity_id": str,                               # Required - Vehicle or driver ID
  "entity_type": str,                             # Required - Enum: vehicle, driver
  "license_type": str,                            # Required - Enum: vehicle_registration, drivers_license, etc.
  "license_number": str,                          # Required - License number/identifier
  "license_description": str,                     # Optional - Description of the license
  "issue_date": str,                              # Required - ISO date format
  "expiry_date": str,                             # Required - ISO date format
  "issuing_authority": str,                       # Required - Authority that issued the license
  "issuing_location": str,                        # Optional - Location where issued
  "cost": float,                                  # Optional - Cost of the license
  "renewal_cost": float,                          # Optional - Cost to renew
  "auto_renewal": bool,                           # Optional - Whether auto-renewal is enabled
  "renewal_notice_days": int,                     # Optional - Days before expiry to send notice
  "document_path": str,                           # Optional - Path to license document
  "notes": str,                                   # Optional - Additional notes
  "restrictions": List[str],                      # Optional - License restrictions
  "conditions": List[str]                         # Optional - License conditions
}
```

### UpdateLicenseRecordRequest

All fields optional - only provided fields will be updated.

```python
{
  "license_number": str,                          # Optional
  "license_description": str,                     # Optional
  "issue_date": str,                              # Optional - ISO date format
  "expiry_date": str,                             # Optional - ISO date format
  "issuing_authority": str,                       # Optional
  "issuing_location": str,                        # Optional
  "cost": float,                                  # Optional
  "renewal_cost": float,                          # Optional
  "auto_renewal": bool,                           # Optional
  "renewal_notice_days": int,                     # Optional
  "is_active": bool,                              # Optional
  "document_path": str,                           # Optional
  "notes": str,                                   # Optional
  "restrictions": List[str],                      # Optional
  "conditions": List[str]                         # Optional
}
```

### LicenseRecordResponse

```python
{
  "id": str,                                      # License record ID
  "entity_id": str,                               # Vehicle or driver ID
  "entity_type": str,                             # Enum: vehicle, driver
  "license_type": str,                            # License type
  "license_number": str,                          # License number/identifier
  "license_description": str,                     # Description of the license (nullable)
  "issue_date": str,                              # ISO date format
  "expiry_date": str,                             # ISO date format
  "issuing_authority": str,                       # Authority that issued the license
  "issuing_location": str,                        # Location where issued (nullable)
  "cost": float,                                  # Cost of the license (nullable)
  "renewal_cost": float,                          # Cost to renew (nullable)
  "auto_renewal": bool,                           # Whether auto-renewal is enabled
  "renewal_notice_days": int,                     # Days before expiry to send notice
  "is_active": bool,                              # Whether license is active
  "is_valid": bool,                               # Whether license is valid
  "validation_status": str,                       # Validation status
  "last_verified": str,                           # Last verification date (ISO format, nullable)
  "document_path": str,                           # Path to license document (nullable)
  "document_type": str,                           # Document type (nullable)
  "created_at": str,                              # ISO datetime format
  "updated_at": str,                              # ISO datetime format
  "created_by": str,                              # User who created the record (nullable)
  "notes": str,                                   # Additional notes (nullable)
  "restrictions": List[str],                      # License restrictions
  "conditions": List[str],                        # License conditions
  "days_until_expiry": int                        # Computed days until expiry
}
```

## Analytics

### MaintenanceDashboardResponse

```python
{
  "total_records": int,                           # Total maintenance records
  "overdue_count": int,                           # Number of overdue maintenance items
  "upcoming_count": int,                          # Number of upcoming maintenance items (next 7 days)
  "completed_this_month": int,                    # Completed maintenance this month
  "total_cost_this_month": float,                 # Total cost this month
  "average_cost_per_maintenance": float,          # Average cost per maintenance
  "maintenance_by_type": {                        # Breakdown by maintenance type
    "preventive": int,
    "corrective": int,
    "scheduled": int,
    "emergency": int,
    "inspection": int
  },
  "maintenance_by_status": {                      # Breakdown by status
    "scheduled": int,
    "in_progress": int,
    "completed": int,
    "overdue": int
  },
  "cost_trends": List[dict],                      # Monthly cost trends
  "vehicle_health_scores": List[dict],            # Vehicle health indicators
  "top_maintenance_types": List[dict],            # Most common maintenance types
  "vendor_performance": List[dict],               # Vendor performance metrics
  "fleet_overview": {
    "total_vehicles": int,
    "vehicles_needing_maintenance": int,
    "vehicles_with_overdue_maintenance": int,
    "average_maintenance_frequency": float
  }
}
```

### CostAnalyticsResponse

```python
{
  "total_cost": float,                            # Total cost in period
  "period_breakdown": List[dict],                 # Cost breakdown by time period
  "cost_by_type": dict,                           # Cost breakdown by maintenance type
  "cost_by_vehicle": List[dict],                  # Cost breakdown by vehicle
  "cost_by_vendor": List[dict],                   # Cost breakdown by vendor
  "trends": {
    "monthly_average": float,
    "trend_direction": str,                       # increasing, decreasing, stable
    "percentage_change": float
  },
  "budget_analysis": {
    "budget_limit": float,                        # Budget limit if set
    "budget_used": float,                         # Amount used
    "budget_remaining": float,                    # Amount remaining
    "projected_annual_cost": float                # Projected cost for year
  }
}
```

### MaintenanceTrendsResponse

```python
{
  "period_days": int,                             # Analysis period in days
  "trends": {
    "maintenance_frequency": {
      "daily_data": List[dict],                   # Daily maintenance counts
      "weekly_average": float,                    # Weekly average
      "trend_direction": str                      # increasing, decreasing, stable
    },
    "cost_trends": {
      "daily_data": List[dict],                   # Daily cost data
      "weekly_average": float,                    # Weekly average cost
      "trend_direction": str                      # increasing, decreasing, stable
    },
    "completion_rates": {
      "on_time_percentage": float,                # Percentage completed on time
      "average_delay_days": float,                # Average delay in days
      "trend_direction": str                      # improving, declining, stable
    }
  },
  "insights": List[str],                          # Key insights and recommendations
  "recommendations": List[str]                    # Actionable recommendations
}
```

### VendorAnalyticsResponse

```python
{
  "total_vendors": int,                           # Total number of vendors
  "active_vendors": int,                          # Number of active vendors
  "vendor_performance": List[{
    "vendor_id": str,
    "vendor_name": str,
    "total_jobs": int,
    "completed_jobs": int,
    "completion_rate": float,
    "average_cost": float,
    "average_completion_time": float,
    "rating": float,
    "on_time_percentage": float,
    "customer_satisfaction": float
  }],
  "cost_comparison": List[dict],                  # Cost comparison between vendors
  "performance_metrics": {
    "best_rated_vendor": dict,
    "most_cost_effective_vendor": dict,
    "fastest_vendor": dict,
    "most_reliable_vendor": dict
  }
}
```

## Notifications

### CreateNotificationRequest

```python
{
  "notification_type": str,                       # Required - Type of notification
  "priority": str,                                # Required - Enum: low, medium, high, critical
  "recipient_id": str,                            # Required - Recipient ID
  "recipient_type": str,                          # Required - Enum: user, role, department
  "title": str,                                   # Required - Notification title
  "message": str,                                 # Required - Full message
  "short_message": str,                           # Optional - Short message for mobile
  "related_entity_type": str,                     # Optional - Related entity type
  "related_entity_id": str,                       # Optional - Related entity ID
  "vehicle_id": str,                              # Optional - Related vehicle ID
  "scheduled_for": str,                           # Optional - When to send (ISO datetime)
  "delivery_methods": List[str],                  # Optional - Delivery methods
  "action_url": str,                              # Optional - Action URL
  "action_text": str,                             # Optional - Action button text
  "expires_at": str                               # Optional - Expiration date (ISO datetime)
}
```

### NotificationResponse

```python
{
  "id": str,                                      # Notification ID
  "notification_type": str,                       # Type of notification
  "priority": str,                                # Priority level
  "status": str,                                  # Enum: pending, sent, failed
  "recipient_id": str,                            # Recipient ID
  "recipient_type": str,                          # Recipient type
  "recipient_email": str,                         # Recipient email (nullable)
  "recipient_phone": str,                         # Recipient phone (nullable)
  "title": str,                                   # Notification title
  "message": str,                                 # Full message
  "short_message": str,                           # Short message (nullable)
  "related_entity_type": str,                     # Related entity type (nullable)
  "related_entity_id": str,                       # Related entity ID (nullable)
  "vehicle_id": str,                              # Related vehicle ID (nullable)
  "scheduled_for": str,                           # Scheduled send time (ISO datetime, nullable)
  "sent_at": str,                                 # Actual send time (ISO datetime, nullable)
  "read_at": str,                                 # Read time (ISO datetime, nullable)
  "delivery_methods": List[str],                  # Delivery methods
  "delivery_status": dict,                        # Delivery status by method
  "created_at": str,                              # ISO datetime format
  "expires_at": str,                              # Expiration date (ISO datetime, nullable)
  "is_read": bool,                                # Whether notification is read
  "is_actionable": bool,                          # Whether notification has actions
  "action_url": str,                              # Action URL (nullable)
  "action_text": str                              # Action button text (nullable)
}
```

## Health and Monitoring

### HealthCheckResponse

```python
{
  "service": "maintenance",
  "status": str,                                  # healthy, unhealthy, degraded
  "timestamp": str,                               # ISO datetime format
  "version": str,                                 # Service version
  "dependencies": {
    "database": {
      "status": str,                              # healthy, unhealthy, disconnected
      "response_time_ms": int,                    # Response time (nullable)
      "error": str                                # Error message (nullable)
    },
    "rabbitmq": {
      "status": str,                              # healthy, not_consuming
      "is_consuming": bool                        # Whether consuming messages
    }
  },
  "background_jobs": {
    "is_running": bool,                           # Whether background jobs are running
    "active_tasks": int,                          # Number of active background tasks
    "status": str                                 # healthy, stopped
  }
}
```

### MetricsResponse

```python
{
  "service": "maintenance",
  "uptime_seconds": float,                        # Service uptime in seconds
  "timestamp": str,                               # ISO datetime format
  "database_status": str,                         # connected, disconnected
  "rabbitmq_status": str,                         # consuming, not consuming
  "performance_metrics": {
    "requests_per_minute": float,
    "average_response_time_ms": float,
    "error_rate_percentage": float,
    "database_query_time_ms": float
  },
  "background_jobs_metrics": {
    "jobs_processed_last_hour": int,
    "failed_jobs_last_hour": int,
    "average_job_duration_ms": float
  }
}
```

## Validation Rules

### Common Validations

- **Dates**: Must be in ISO format (YYYY-MM-DDTHH:mm:ssZ)
- **Costs**: Must be positive numbers or zero
- **IDs**: Must be non-empty strings
- **Enums**: Must match predefined values exactly
- **Required fields**: Cannot be null or empty strings

### Business Logic Validations

- **Scheduled Date**: Cannot be in the past for new records
- **Completion Date**: Cannot be before start date
- **Mileage**: Must be positive integers
- **License Expiry**: Must be after issue date
- **Cost Fields**: Cannot exceed reasonable limits (configurable)

## Error Handling

### Common Error Responses

```python
# Validation Error (422)
{
  "success": false,
  "message": "Validation error",
  "error_code": "VALIDATION_ERROR",
  "details": [
    {
      "field": "scheduled_date",
      "message": "Invalid date format",
      "received_value": "2025-13-01"
    }
  ],
  "timestamp": "2025-07-17T10:00:00Z"
}

# Not Found Error (404)
{
  "success": false,
  "message": "Maintenance record not found",
  "error_code": "NOT_FOUND",
  "timestamp": "2025-07-17T10:00:00Z"
}

# Internal Server Error (500)
{
  "success": false,
  "message": "Internal server error",
  "error_code": "INTERNAL_ERROR",
  "timestamp": "2025-07-17T10:00:00Z"
}
```
