from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from bson import ObjectId
from datetime import datetime
from enum import Enum
import re


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, field=None):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


class VehicleStatus(str, Enum):
    """Vehicle status enumeration"""
    AVAILABLE = "available"
    ASSIGNED = "assigned" 
    IN_USE = "in_use"
    MAINTENANCE = "maintenance"
    OUT_OF_SERVICE = "out_of_service"


class VehicleAssignmentStatus(str, Enum):
    """Vehicle assignment status"""
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# Management-specific vehicle models
class VehicleManagement(BaseModel):
    """Business logic vehicle data stored in Management service"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    vehicle_id: str  # Reference to vehicle in Vehicles Dblock
    status: VehicleStatus = VehicleStatus.AVAILABLE
    current_driver_id: Optional[str] = None
    current_assignment_id: Optional[str] = None
    department: Optional[str] = None
    cost_center: Optional[str] = None
    daily_rate: Optional[float] = None
    mileage_rate: Optional[float] = None
    fuel_budget: Optional[float] = None
    insurance_policy: Optional[str] = None
    next_service_date: Optional[datetime] = None
    last_inspection_date: Optional[datetime] = None
    location: Optional[Dict] = None  # Current location
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        validate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class VehicleAssignment(BaseModel):
    """Vehicle assignment records"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    vehicle_id: str
    driver_id: str
    assignment_type: str  # "trip", "long_term", "maintenance"
    status: VehicleAssignmentStatus = VehicleAssignmentStatus.ACTIVE
    start_date: datetime
    end_date: Optional[datetime] = None
    start_mileage: Optional[int] = None
    end_mileage: Optional[int] = None
    purpose: Optional[str] = None
    route: Optional[Dict] = None
    notes: Optional[str] = None
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        validate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class VehicleUsageLog(BaseModel):
    """Vehicle usage tracking"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    vehicle_id: str
    driver_id: str
    trip_start: datetime
    trip_end: Optional[datetime] = None
    start_location: Optional[Dict] = None
    end_location: Optional[Dict] = None
    distance_km: Optional[float] = None
    fuel_consumed: Optional[float] = None
    purpose: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        validate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# Request/Response models
class VehicleManagementResponse(BaseModel):
    """Response model for vehicle management data"""
    vehicle_id: str
    status: VehicleStatus
    current_driver_id: Optional[str] = None
    current_assignment_id: Optional[str] = None
    department: Optional[str] = None
    cost_center: Optional[str] = None
    daily_rate: Optional[float] = None
    location: Optional[Dict] = None
    next_service_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class VehicleAssignmentRequest(BaseModel):
    """Request model for vehicle assignment"""
    vehicle_id: str
    driver_id: str
    assignment_type: str
    start_date: datetime
    end_date: Optional[datetime] = None
    purpose: Optional[str] = None
    route: Optional[Dict] = None
    notes: Optional[str] = None


class VehicleAssignmentResponse(BaseModel):
    """Response model for vehicle assignment"""
    id: str
    vehicle_id: str
    driver_id: str
    assignment_type: str
    status: VehicleAssignmentStatus
    start_date: datetime
    end_date: Optional[datetime] = None
    purpose: Optional[str] = None
    created_at: datetime


class VehicleStatusUpdateRequest(BaseModel):
    """Request model for updating vehicle status"""
    status: VehicleStatus
    notes: Optional[str] = None


class VehicleUsageRequest(BaseModel):
    """Request model for vehicle usage logging"""
    vehicle_id: str
    trip_start: datetime
    start_location: Optional[Dict] = None
    purpose: Optional[str] = None


class VehicleUsageEndRequest(BaseModel):
    """Request model for ending vehicle usage"""
    end_location: Optional[Dict] = None
    distance_km: Optional[float] = None
    fuel_consumed: Optional[float] = None


# Message Queue models
class VehicleCreatedMessage(BaseModel):
    vehicle_id: str
    make: str
    model: str
    year: int
    vin: str
    license_plate: str


class VehicleUpdatedMessage(BaseModel):
    vehicle_id: str
    updates: Dict


class VehicleDeletedMessage(BaseModel):
    vehicle_id: str


class VehicleSpecs(BaseModel):
    """Technical vehicle specifications for Vehicles Dblock"""
    vehicle_id: str
    make: str
    model: str
    year: int
    vin: str
    license_plate: str
    color: Optional[str] = None
    fuel_type: Optional[str] = "gasoline"
    engine_size: Optional[str] = None
    transmission: Optional[str] = None
    seating_capacity: Optional[int] = None
    cargo_capacity: Optional[str] = None
    weight: Optional[float] = None
    dimensions: Optional[Dict] = None
    tire_size: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DriverStatus(str, Enum):
    """Driver status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    ON_LEAVE = "on_leave"


class DriverLicenseClass(str, Enum):
    """South African driving license classes"""
    A = "A"      # Motorcycles
    A1 = "A1"    # Light motorcycles
    B = "B"      # Light motor vehicles
    C = "C"      # Heavy motor vehicles
    C1 = "C1"    # Medium heavy motor vehicles
    EB = "EB"    # Light motor vehicle with trailer
    EC = "EC"    # Heavy motor vehicle with trailer
    EC1 = "EC1"  # Medium heavy motor vehicle with trailer


def validate_sa_phone_number(phone: str) -> bool:
    """
    Validate South African phone number format
    Accepts: +27123456789, 0123456789
    """
    if not phone:
        return True  # Optional field
    
    # Remove spaces and normalize
    phone_clean = re.sub(r'\s+', '', phone)
    
    # SA phone regex: +27 followed by 9 digits or 0 followed by 9 digits
    sa_phone_regex = r'^(\+27|0)[1-9][0-9]{8}$'
    
    return bool(re.match(sa_phone_regex, phone_clean))


def validate_sa_license_number(license_number: str) -> bool:
    """
    Validate South African license number format
    SA license numbers are typically 13 digits
    """
    if not license_number:
        return False
    
    # Remove spaces and normalize
    license_clean = re.sub(r'\s+', '', license_number)
    
    # SA license regex: 13 digits
    sa_license_regex = r'^[0-9]{13}$'
    
    return bool(re.match(sa_license_regex, license_clean))


class DriverModel(BaseModel):
    """Driver management model with South African compliance"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    employee_id: str
    user_id: str  # Reference to user profile in Users Dblock
    license_number: str
    license_class: List[DriverLicenseClass]
    license_expiry: datetime
    phone_number: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    department: Optional[str] = None
    hire_date: Optional[datetime] = None
    status: DriverStatus = DriverStatus.ACTIVE
    medical_certificate_expiry: Optional[datetime] = None
    prdp_certificate: Optional[bool] = False  # Professional Driving Permit
    driving_record_points: Optional[int] = 0
    current_vehicle_id: Optional[str] = None
    authorized_vehicle_types: Optional[List[str]] = []
    performance_rating: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('license_number')
    def validate_license(cls, v):
        if not validate_sa_license_number(v):
            raise ValueError('Invalid South African license number format (must be 13 digits)')
        return v
    
    @validator('phone_number')
    def validate_phone(cls, v):
        if v and not validate_sa_phone_number(v):
            raise ValueError('Invalid South African phone number format')
        return v
    
    @validator('emergency_phone')
    def validate_emergency_phone(cls, v):
        if v and not validate_sa_phone_number(v):
            raise ValueError('Invalid South African emergency phone number format')
        return v
    
    class Config:
        validate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class DriverCreateRequest(BaseModel):
    """Request model for creating a new driver"""
    employee_id: str
    user_id: str
    license_number: str
    license_class: List[DriverLicenseClass]
    license_expiry: datetime
    phone_number: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    department: Optional[str] = None
    hire_date: Optional[datetime] = None
    medical_certificate_expiry: Optional[datetime] = None
    prdp_certificate: Optional[bool] = False
    authorized_vehicle_types: Optional[List[str]] = []
    notes: Optional[str] = None


class DriverUpdateRequest(BaseModel):
    """Request model for updating driver information"""
    license_number: Optional[str] = None
    license_class: Optional[List[DriverLicenseClass]] = None
    license_expiry: Optional[datetime] = None
    phone_number: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    department: Optional[str] = None
    status: Optional[DriverStatus] = None
    medical_certificate_expiry: Optional[datetime] = None
    prdp_certificate: Optional[bool] = None
    driving_record_points: Optional[int] = None
    current_vehicle_id: Optional[str] = None
    authorized_vehicle_types: Optional[List[str]] = None
    performance_rating: Optional[float] = None
    notes: Optional[str] = None


class DriverResponse(BaseModel):
    """Response model for driver data"""
    id: str = Field(alias="_id")
    employee_id: str
    user_id: str
    license_number: str
    license_class: List[DriverLicenseClass]
    license_expiry: datetime
    phone_number: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    department: Optional[str] = None
    hire_date: Optional[datetime] = None
    status: DriverStatus
    medical_certificate_expiry: Optional[datetime] = None
    prdp_certificate: Optional[bool] = False
    driving_record_points: Optional[int] = 0
    current_vehicle_id: Optional[str] = None
    authorized_vehicle_types: Optional[List[str]] = []
    performance_rating: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Additional fields from user profile
    full_name: Optional[str] = None
    email: Optional[str] = None
    
    class Config:
        validate_by_name = True
        allow_population_by_field_name = True
