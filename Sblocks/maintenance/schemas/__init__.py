"""
Maintenance Service Schemas Package
"""

from .entities import *
from .requests import *
from .responses import *

__all__ = [
    # Entities
    "MaintenanceType",
    "MaintenanceStatus", 
    "MaintenancePriority",
    "LicenseType",
    "MaintenanceRecord",
    "MaintenanceSchedule",
    "LicenseRecord",
    "MaintenanceVendor",
    "MaintenanceNotification",
    
    # Requests
    "CreateMaintenanceRecordRequest",
    "UpdateMaintenanceRecordRequest",
    "CreateMaintenanceScheduleRequest", 
    "CreateLicenseRecordRequest",
    "UpdateLicenseRecordRequest",
    "CreateVendorRequest",
    "UpdateVendorRequest",
    "MaintenanceQueryParams",
    "LicenseQueryParams",
    "ServiceRequest",
    
    # Responses
    "BaseResponse",
    "ErrorResponse",
    "DataResponse", 
    "ListResponse",
    "AnalyticsResponse",
    "HealthResponse",
    "ServiceStatusResponse",
    "MaintenanceRecordResponse",
    "MaintenanceRecordsListResponse",
    "MaintenanceScheduleResponse",
    "LicenseRecordResponse",
    "LicenseRecordsListResponse",
    "VendorResponse",
    "VendorsListResponse",
    "MaintenanceAnalyticsResponse",
    "MaintenanceDashboardResponse",
    "NotificationResponse",
    "ServiceResponse",
]
