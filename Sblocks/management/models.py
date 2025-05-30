from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from bson import ObjectId
from datetime import datetime
from enum import Enum


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
