"""
Core domain entities for Management service
"""
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
    """Vehicle assignment status"""
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AssignmentType(str, Enum):
    """Types of vehicle assignments"""
    TRIP = "trip"
    LONG_TERM = "long_term"
    MAINTENANCE = "maintenance"
    EMERGENCY = "emergency"


class DriverStatus(str, Enum):
    """Driver status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    ON_LEAVE = "on_leave"


class LicenseClass(str, Enum):
    """South African license classes"""
    A = "A"    # Motorcycles
    A1 = "A1"  # Light motorcycles
    B = "B"    # Light motor vehicles
    C = "C"    # Heavy motor vehicles
    C1 = "C1"  # Medium heavy motor vehicles
    EB = "EB"  # Light motor vehicle with trailer
    EC = "EC"  # Heavy motor vehicle with trailer
    EC1 = "EC1" # Medium heavy motor vehicle with trailer


# Core Entities
class VehicleAssignment(BaseModel):
    """Vehicle assignment entity"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    vehicle_id: str  # Reference to vehicle in Vehicles Dblock
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
    """Vehicle usage tracking entity"""
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
    """Driver entity"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    employee_id: str
    user_id: Optional[str] = None  # Link to security service user
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
    """Cached analytics data entity"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    metric_type: str  # fleet_utilization, vehicle_usage, etc.
    data: Dict
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class FuelRecord(BaseModel):
    """Fuel record entity"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    vehicle_id: str
    driver_id: str
    liters: float
    cost: float
    fuel_type: str = "petrol"
    station_name: Optional[str] = None
    location: Optional[str] = None
    receipt_number: Optional[str] = None
    notes: Optional[str] = None
    purchase_date: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    created_by: str
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class MileageRecord(BaseModel):
    """Vehicle mileage record entity"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    vehicle_id: str
    driver_id: str
    previous_mileage: int
    new_mileage: int
    mileage_difference: int
    reading_date: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class NotificationStatus(str, Enum):
    """Notification status"""
    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"

class NotificationPriority(str, Enum):
    """Notification priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class Notification(BaseModel):
    """Notification entity"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    recipient_id: str
    recipient_type: str  # driver, manager, admin
    title: str
    message: str
    notification_type: str  # fuel, assignment, maintenance, etc.
    priority: NotificationPriority = NotificationPriority.NORMAL
    status: NotificationStatus = NotificationStatus.UNREAD
    related_entity_id: Optional[str] = None
    related_entity_type: Optional[str] = None
    action_required: bool = False
    is_read: bool = False
    is_archived: bool = False
    read_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class AuditLog(BaseModel):
    """Audit trail entity"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    entity_type: str  # assignment, usage, driver
    entity_id: str
    action: str  # create, update, delete
    user_id: str
    changes: Optional[Dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
