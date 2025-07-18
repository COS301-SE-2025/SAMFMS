"""
Request and Response schemas for Management service API
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from .entities import AssignmentStatus, AssignmentType, DriverStatus, LicenseClass


# Vehicle Request Schemas
class VehicleCreateRequest(BaseModel):
    """Request to create new vehicle"""
    # Support both license_plate (frontend) and registration_number (backend)
    registration_number: Optional[str] = Field(None, description="Vehicle registration number")
    license_plate: Optional[str] = Field(None, description="Vehicle license plate")
    make: str = Field(..., description="Vehicle make")
    model: str = Field(..., description="Vehicle model")
    year: int = Field(..., description="Vehicle year", ge=1900, le=2030)
    type: Optional[str] = Field("sedan", description="Vehicle type (e.g., sedan, SUV, truck)")
    department: Optional[str] = Field("General", description="Department responsible for vehicle")
    capacity: Optional[int] = Field(5, description="Passenger capacity")
    fuel_type: Optional[str] = Field("petrol", description="Fuel type")
    color: Optional[str] = Field("white", description="Vehicle color")
    vin: Optional[str] = Field(None, description="Vehicle identification number")
    status: Optional[str] = Field("available", description="Vehicle status")
    mileage: Optional[int] = Field(0, description="Current mileage")
    
    @validator('registration_number', pre=True, always=True)
    def validate_registration(cls, v, values):
        """Use license_plate if registration_number is not provided"""
        if not v and 'license_plate' in values:
            return values['license_plate']
        return v or values.get('license_plate')
    
    @validator('license_plate', pre=True, always=True)
    def validate_license_plate(cls, v, values):
        """Use registration_number if license_plate is not provided"""
        if not v and 'registration_number' in values:
            return values['registration_number']
        return v or values.get('registration_number')
    
    @validator('fuel_type')
    def validate_fuel_type(cls, v):
        """Normalize fuel type values"""
        if v:
            fuel_type_map = {
                'petrol': 'petrol',
                'gasoline': 'petrol',  # US term -> SA term
                'gas': 'petrol',       # Short form -> SA term
                'diesel': 'diesel',
                'hybrid': 'hybrid',
                'electric': 'electric'
            }
            return fuel_type_map.get(v.lower(), v)
        return v
    
    @validator('status')
    def validate_status(cls, v):
        """Normalize status values"""
        if v:
            status_map = {
                'active': 'available',
                'available': 'available',
                'inactive': 'out_of_service',
                'out_of_service': 'out_of_service',
                'maintenance': 'maintenance'
            }
            return status_map.get(v.lower(), v)
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "license_plate": "ABC123GP",
                "make": "Toyota",
                "model": "Corolla",
                "year": 2022,
                "type": "sedan",
                "department": "General",
                "capacity": 5,
                "fuel_type": "petrol",
                "color": "white",
                "status": "available",
                "vin": "1234567890ABCDEFG",
                "mileage": 0
            }
        }


class VehicleUpdateRequest(BaseModel):
    """Request to update vehicle"""
    registration_number: Optional[str] = Field(None, description="Vehicle registration number")
    make: Optional[str] = Field(None, description="Vehicle make")
    model: Optional[str] = Field(None, description="Vehicle model")
    year: Optional[int] = Field(None, description="Vehicle year", ge=1900, le=2030)
    type: Optional[str] = Field(None, description="Vehicle type")
    department: Optional[str] = Field(None, description="Department responsible for vehicle")
    capacity: Optional[int] = Field(None, description="Passenger capacity")
    fuel_type: Optional[str] = Field(None, description="Fuel type")
    color: Optional[str] = Field(None, description="Vehicle color")
    vin: Optional[str] = Field(None, description="Vehicle identification number")
    status: Optional[str] = Field(None, description="Vehicle status")
    mileage: Optional[int] = Field(None, description="Vehicle mileage in kilometers", ge=0)
    
    @validator('fuel_type')
    def validate_fuel_type(cls, v):
        """Normalize fuel type values"""
        if v:
            fuel_type_map = {
                'petrol': 'petrol',
                'gasoline': 'petrol',  # US term -> SA term
                'gas': 'petrol',       # Short form -> SA term
                'diesel': 'diesel',
                'hybrid': 'hybrid',
                'electric': 'electric'
            }
            return fuel_type_map.get(v.lower(), v)
        return v
    
    @validator('status')
    def validate_status(cls, v):
        """Normalize status values"""
        if v:
            status_map = {
                'active': 'available',
                'available': 'available',
                'inactive': 'out_of_service',
                'out_of_service': 'out_of_service',
                'maintenance': 'maintenance'
            }
            return status_map.get(v.lower(), v)
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "maintenance",
                "department": "Security",
                "mileage": 50000,
                "fuel_type": "petrol"
            }
        }


# Assignment Request Schemas
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


class AssignmentCreateRequest(BaseModel):
    """Request to create new assignment"""
    vehicle_id: str = Field(..., description="Vehicle ID to assign")
    driver_id: str = Field(..., description="Driver ID to assign")
    assignment_type: AssignmentType = Field(..., description="Type of assignment")
    start_date: datetime = Field(..., description="Assignment start date")
    end_date: Optional[datetime] = Field(None, description="Assignment end date")
    purpose: Optional[str] = Field(None, description="Purpose of assignment")
    route: Optional[Dict] = Field(None, description="Route information")
    notes: Optional[str] = Field(None, description="Additional notes")


class AssignmentUpdateRequest(BaseModel):
    """Request to update existing assignment"""
    assignment_type: Optional[AssignmentType] = Field(None, description="Type of assignment")
    status: Optional[AssignmentStatus] = Field(None, description="Assignment status")
    start_date: Optional[datetime] = Field(None, description="Assignment start date")
    end_date: Optional[datetime] = Field(None, description="Assignment end date")
    purpose: Optional[str] = Field(None, description="Purpose of assignment")
    route: Optional[Dict] = Field(None, description="Route information")
    notes: Optional[str] = Field(None, description="Additional notes")


# Driver Request Schemas
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
