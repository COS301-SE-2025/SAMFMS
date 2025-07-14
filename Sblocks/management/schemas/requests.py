"""
Request and Response schemas for Management service API
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from .entities import AssignmentStatus, AssignmentType, DriverStatus, LicenseClass


# Request Schemas
class VehicleAssignmentRequest(BaseModel):
    """Request to create/update vehicle assignment"""
    vehicle_id: str
    driver_id: str
    assignment_type: AssignmentType
    start_date: datetime
    end_date: Optional[datetime] = None
    purpose: Optional[str] = None
    route: Optional[Dict] = None
    notes: Optional[str] = None


class VehicleUsageRequest(BaseModel):
    """Request to start vehicle usage logging"""
    vehicle_id: str
    driver_id: str
    assignment_id: Optional[str] = None
    start_location: Optional[Dict] = None
    purpose: Optional[str] = None
    odometer_start: Optional[float] = None


class VehicleUsageEndRequest(BaseModel):
    """Request to end vehicle usage logging"""
    end_location: Optional[Dict] = None
    distance_km: Optional[float] = None
    fuel_consumed: Optional[float] = None
    odometer_end: Optional[float] = None


class DriverCreateRequest(BaseModel):
    """Request to create new driver"""
    employee_id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    license_number: str
    license_class: List[LicenseClass]
    license_expiry: datetime
    department: Optional[str] = None
    hire_date: datetime
    emergency_contact: Optional[Dict] = None
    address: Optional[Dict] = None

    @validator('phone')
    def validate_phone(cls, v):
        # Basic SA phone number validation
        import re
        if not re.match(r'^(\+27|0)[6-8][0-9]{8}$', v):
            raise ValueError('Invalid South African phone number')
        return v

    @validator('license_number')
    def validate_license(cls, v):
        # Basic SA license number validation
        import re
        if not re.match(r'^[0-9]{8}[0-9]{2}$', v):
            raise ValueError('Invalid South African license number format')
        return v


class DriverUpdateRequest(BaseModel):
    """Request to update driver"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    license_number: Optional[str] = None
    license_class: Optional[List[LicenseClass]] = None
    license_expiry: Optional[datetime] = None
    status: Optional[DriverStatus] = None
    department: Optional[str] = None
    current_vehicle_id: Optional[str] = None
    emergency_contact: Optional[Dict] = None
    address: Optional[Dict] = None


# Response Schemas
class VehicleAssignmentResponse(BaseModel):
    """Response for vehicle assignment"""
    id: str
    vehicle_id: str
    driver_id: str
    assignment_type: AssignmentType
    status: AssignmentStatus
    start_date: datetime
    end_date: Optional[datetime] = None
    purpose: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class VehicleUsageResponse(BaseModel):
    """Response for vehicle usage log"""
    id: str
    vehicle_id: str
    driver_id: str
    assignment_id: Optional[str] = None
    trip_start: datetime
    trip_end: Optional[datetime] = None
    distance_km: Optional[float] = None
    fuel_consumed: Optional[float] = None
    purpose: Optional[str] = None


class DriverResponse(BaseModel):
    """Response for driver"""
    id: str
    employee_id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    license_number: str
    license_class: List[LicenseClass]
    license_expiry: datetime
    status: DriverStatus
    department: Optional[str] = None
    current_vehicle_id: Optional[str] = None
    hire_date: datetime


class AnalyticsResponse(BaseModel):
    """Generic analytics response"""
    metric_type: str
    data: Dict[str, Any]
    generated_at: datetime
    cache_expires_at: Optional[datetime] = None


class PaginatedResponse(BaseModel):
    """Generic paginated response"""
    items: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int


# Error Schemas
class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    detail: Optional[str] = None
    service: str = "management"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    trace_id: Optional[str] = None
