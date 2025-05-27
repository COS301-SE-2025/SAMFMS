from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class TripStatus(str, Enum):
    PLANNED = "planned"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DELAYED = "delayed"

class TripPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class VehicleStatus(str, Enum):
    ACTIVE = "active"
    IDLE = "idle"
    MAINTENANCE = "maintenance"
    BREAKDOWN = "breakdown"
    OUT_OF_SERVICE = "out_of_service"

class DriverStatus(str, Enum):
    AVAILABLE = "available"
    ON_TRIP = "on_trip"
    ON_LEAVE = "on_leave"
    INACTIVE = "inactive"

class LocationType(str, Enum):
    DEPOT = "depot"
    CLIENT = "client"
    SERVICE_POINT = "service_point"
    FUEL_STATION = "fuel_station"
    PARKING = "parking"
    CUSTOM = "custom"

class Location(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str
    address: str
    latitude: float
    longitude: float
    location_type: LocationType
    contact_info: Optional[Dict[str, str]] = None
    access_hours: Optional[Dict[str, str]] = None
    special_instructions: Optional[str] = None
    geofence_radius: Optional[float] = 100  # meters
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class Vehicle(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    vehicle_id: str  # External vehicle ID from main system
    make: str
    model: str
    year: int
    license_plate: str
    vin: str
    status: VehicleStatus
    current_location: Optional[Dict[str, float]] = None  # {lat, lng}
    fuel_level: Optional[float] = None
    mileage: Optional[float] = None
    capacity: Optional[Dict[str, Any]] = None  # weight, volume, passengers
    equipment: Optional[List[str]] = None
    restrictions: Optional[List[str]] = None
    last_service_date: Optional[datetime] = None
    next_service_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class Driver(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    driver_id: str  # External driver ID from main system
    name: str
    license_number: str
    license_expiry: datetime
    phone: str
    email: Optional[str] = None
    status: DriverStatus
    current_location: Optional[Dict[str, float]] = None
    skills: Optional[List[str]] = None  # certifications, vehicle types
    restrictions: Optional[List[str]] = None
    shift_schedule: Optional[Dict[str, Any]] = None
    performance_rating: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class RouteWaypoint(BaseModel):
    location_id: Optional[PyObjectId] = None
    latitude: float
    longitude: float
    name: str
    estimated_arrival: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None
    stop_duration: Optional[int] = 0  # minutes
    instructions: Optional[str] = None
    order: int

class Route(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str
    description: Optional[str] = None
    waypoints: List[RouteWaypoint]
    total_distance: Optional[float] = None  # kilometers
    estimated_duration: Optional[int] = None  # minutes
    optimized: bool = False
    route_data: Optional[Dict[str, Any]] = None  # external route service data
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class TripTemplate(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str
    description: Optional[str] = None
    route_id: Optional[PyObjectId] = None
    default_vehicle_requirements: Optional[Dict[str, Any]] = None
    default_driver_requirements: Optional[Dict[str, Any]] = None
    default_duration: Optional[int] = None  # minutes
    recurring_schedule: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class Trip(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    trip_id: str  # External trip ID for reference
    name: str
    description: Optional[str] = None
    
    # Assignment
    vehicle_id: Optional[PyObjectId] = None
    driver_id: Optional[PyObjectId] = None
    route_id: Optional[PyObjectId] = None
    template_id: Optional[PyObjectId] = None
    
    # Scheduling
    scheduled_start: datetime
    scheduled_end: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    
    # Status and Priority
    status: TripStatus
    priority: TripPriority = TripPriority.MEDIUM
    
    # Trip Details
    origin: Dict[str, Any]  # location info
    destination: Dict[str, Any]  # location info
    waypoints: Optional[List[Dict[str, Any]]] = None
    
    # Requirements
    vehicle_requirements: Optional[Dict[str, Any]] = None
    driver_requirements: Optional[Dict[str, Any]] = None
    
    # Progress Tracking
    current_location: Optional[Dict[str, float]] = None
    progress_percentage: float = 0.0
    estimated_arrival: Optional[datetime] = None
    
    # Metrics
    distance_planned: Optional[float] = None
    distance_actual: Optional[float] = None
    duration_planned: Optional[int] = None  # minutes
    duration_actual: Optional[int] = None
    fuel_consumed: Optional[float] = None
    
    # Additional Data
    cargo_details: Optional[Dict[str, Any]] = None
    special_instructions: Optional[str] = None
    weather_conditions: Optional[Dict[str, Any]] = None
    traffic_conditions: Optional[Dict[str, Any]] = None
    
    # Metadata
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # External references
    external_refs: Optional[Dict[str, str]] = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class Schedule(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str
    description: Optional[str] = None
    
    # Time frame
    start_date: datetime
    end_date: Optional[datetime] = None
    
    # Recurring pattern
    is_recurring: bool = False
    recurrence_pattern: Optional[Dict[str, Any]] = None  # daily, weekly, monthly patterns
    
    # Resource assignments
    vehicle_assignments: Optional[List[Dict[str, Any]]] = None
    driver_assignments: Optional[List[Dict[str, Any]]] = None
    
    # Generated trips
    trip_ids: List[PyObjectId] = []
    
    # Status
    is_active: bool = True
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class TripEvent(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    trip_id: PyObjectId
    event_type: str  # start, waypoint_reached, delay, completion, etc.
    timestamp: datetime
    location: Optional[Dict[str, float]] = None
    description: str
    metadata: Optional[Dict[str, Any]] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
