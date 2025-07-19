
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum
from bson import ObjectId


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


class AssignmentStatus(str, Enum):
    
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AssignmentType(str, Enum):
    
    TRIP = "trip"
    LONG_TERM = "long_term"
    MAINTENANCE = "maintenance"
    EMERGENCY = "emergency"


class DriverStatus(str, Enum):
    
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    ON_LEAVE = "on_leave"


class LicenseClass(str, Enum):
    
    A = "A"    
    A1 = "A1"  
    B = "B"    
    C = "C"    
    C1 = "C1"  
    EB = "EB"  
    EC = "EC"  
    EC1 = "EC1" 



class VehicleAssignment(BaseModel):
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    vehicle_id: str  
    driver_id: str
    assignment_type: AssignmentType
    status: AssignmentStatus = AssignmentStatus.ACTIVE
    start_date: datetime
    end_date: Optional[datetime] = None
    start_mileage: Optional[float] = None
    end_mileage: Optional[float] = None
    purpose: Optional[str] = None
    route: Optional[Dict] = None
    notes: Optional[str] = None
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class VehicleUsageLog(BaseModel):
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    vehicle_id: str
    driver_id: str
    assignment_id: Optional[str] = None
    trip_start: datetime
    trip_end: Optional[datetime] = None
    start_location: Optional[Dict] = None
    end_location: Optional[Dict] = None
    distance_km: Optional[float] = None
    fuel_consumed: Optional[float] = None
    purpose: Optional[str] = None
    odometer_start: Optional[float] = None
    odometer_end: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class Driver(BaseModel):
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    employee_id: str
    user_id: Optional[str] = None  
    first_name: str
    last_name: str
    email: str
    phone: str
    license_number: str
    license_class: List[LicenseClass]
    license_expiry: datetime
    status: DriverStatus = DriverStatus.ACTIVE
    department: Optional[str] = None
    current_vehicle_id: Optional[str] = None
    hire_date: datetime
    emergency_contact: Optional[Dict] = None
    address: Optional[Dict] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class AnalyticsSnapshot(BaseModel):
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    metric_type: str  
    data: Dict
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class AuditLog(BaseModel):
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    entity_type: str  
    entity_id: str
    action: str  
    user_id: str
    changes: Optional[Dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
