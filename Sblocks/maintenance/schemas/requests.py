"""
Request and Response schemas for Maintenance Service API
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from .entities import MaintenanceType, MaintenanceStatus, MaintenancePriority, LicenseType


# Request Schemas
class CreateMaintenanceRecordRequest(BaseModel):
    """Request to create a new maintenance record"""
    vehicle_id: str
    maintenance_type: MaintenanceType
    priority: MaintenancePriority = MaintenancePriority.MEDIUM
    scheduled_date: datetime
    estimated_duration: Optional[int] = None
    title: str
    description: Optional[str] = None
    estimated_cost: Optional[float] = None
    assigned_technician: Optional[str] = None
    vendor_id: Optional[str] = None
    service_provider: Optional[str] = None
    is_recurring: bool = False
    recurrence_interval: Optional[int] = None


class UpdateMaintenanceRecordRequest(BaseModel):
    """Request to update an existing maintenance record"""
    status: Optional[MaintenanceStatus] = None
    priority: Optional[MaintenancePriority] = None
    scheduled_date: Optional[datetime] = None
    estimated_duration: Optional[int] = None
    actual_start_date: Optional[datetime] = None
    actual_completion_date: Optional[datetime] = None
    title: Optional[str] = None
    description: Optional[str] = None
    work_performed: Optional[str] = None
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    labor_cost: Optional[float] = None
    parts_cost: Optional[float] = None
    assigned_technician: Optional[str] = None
    vendor_id: Optional[str] = None
    service_provider: Optional[str] = None
    mileage_at_service: Optional[int] = None
    next_service_mileage: Optional[int] = None
    parts_used: Optional[List[Dict[str, Any]]] = None
    warranty_info: Optional[Dict[str, Any]] = None


class CreateMaintenanceScheduleRequest(BaseModel):
    """Request to create a maintenance schedule"""
    vehicle_id: Optional[str] = None
    vehicle_type: Optional[str] = None
    name: str
    description: Optional[str] = None
    maintenance_type: MaintenanceType
    priority: MaintenancePriority = MaintenancePriority.MEDIUM
    interval_type: str  # time_based, mileage_based, or hybrid
    interval_days: Optional[int] = None
    interval_mileage: Optional[int] = None
    estimated_cost: Optional[float] = None
    estimated_duration: Optional[int] = None
    advance_notice_days: int = 7


class CreateLicenseRecordRequest(BaseModel):
    """Request to create a license record"""
    entity_id: str
    entity_type: str  # vehicle or driver
    license_type: LicenseType
    license_number: str
    title: str
    description: Optional[str] = None
    issue_date: date
    expiry_date: date
    issuing_authority: str
    issuing_country: Optional[str] = None
    issuing_state: Optional[str] = None
    advance_notice_days: int = 30
    cost: Optional[float] = None


class UpdateLicenseRecordRequest(BaseModel):
    """Request to update a license record"""
    license_number: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    renewal_date: Optional[date] = None
    issuing_authority: Optional[str] = None
    issuing_country: Optional[str] = None
    issuing_state: Optional[str] = None
    is_active: Optional[bool] = None
    advance_notice_days: Optional[int] = None
    cost: Optional[float] = None
    renewal_cost: Optional[float] = None


class CreateVendorRequest(BaseModel):
    """Request to create a maintenance vendor"""
    name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    services_offered: List[str] = []
    specializations: List[str] = []
    business_hours: Optional[str] = None
    emergency_contact: Optional[str] = None


class UpdateVendorRequest(BaseModel):
    """Request to update a vendor"""
    name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    services_offered: Optional[List[str]] = None
    specializations: Optional[List[str]] = None
    business_hours: Optional[str] = None
    emergency_contact: Optional[str] = None
    rating: Optional[float] = None
    is_active: Optional[bool] = None
    is_preferred: Optional[bool] = None


class MaintenanceQueryParams(BaseModel):
    """Query parameters for maintenance records"""
    vehicle_id: Optional[str] = None
    status: Optional[MaintenanceStatus] = None
    maintenance_type: Optional[MaintenanceType] = None
    priority: Optional[MaintenancePriority] = None
    scheduled_from: Optional[datetime] = None
    scheduled_to: Optional[datetime] = None
    vendor_id: Optional[str] = None
    technician_id: Optional[str] = None
    skip: int = 0
    limit: int = 100
    sort_by: str = "scheduled_date"
    sort_order: str = "asc"


class LicenseQueryParams(BaseModel):
    """Query parameters for license records"""
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None
    license_type: Optional[LicenseType] = None
    expiring_within_days: Optional[int] = None
    is_active: Optional[bool] = None
    skip: int = 0
    limit: int = 100
    sort_by: str = "expiry_date"
    sort_order: str = "asc"


# Response Schemas
class MaintenanceRecordResponse(BaseModel):
    """Response for maintenance record operations"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class MaintenanceRecordsListResponse(BaseModel):
    """Response for listing maintenance records"""
    success: bool
    message: str
    data: List[Dict[str, Any]] = []
    total: int = 0
    skip: int = 0
    limit: int = 100


class MaintenanceScheduleResponse(BaseModel):
    """Response for maintenance schedule operations"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class LicenseRecordResponse(BaseModel):
    """Response for license record operations"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class LicenseRecordsListResponse(BaseModel):
    """Response for listing license records"""
    success: bool
    message: str
    data: List[Dict[str, Any]] = []
    total: int = 0
    skip: int = 0
    limit: int = 100


class VendorResponse(BaseModel):
    """Response for vendor operations"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class VendorsListResponse(BaseModel):
    """Response for listing vendors"""
    success: bool
    message: str
    data: List[Dict[str, Any]] = []
    total: int = 0


class MaintenanceAnalyticsResponse(BaseModel):
    """Response for maintenance analytics"""
    success: bool
    message: str
    data: Dict[str, Any] = {}


class MaintenanceDashboardResponse(BaseModel):
    """Response for maintenance dashboard data"""
    success: bool
    message: str
    data: Dict[str, Any] = {}


class NotificationResponse(BaseModel):
    """Response for notification operations"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


# Internal service communication schemas
class ServiceRequest(BaseModel):
    """Generic service request schema"""
    action: str
    endpoint: str
    data: Optional[Dict[str, Any]] = None
    params: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    request_id: Optional[str] = None


class ServiceResponse(BaseModel):
    """Generic service response schema"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    request_id: Optional[str] = None
