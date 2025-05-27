"""
Geofence models for GPS service
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class GeofenceCoordinates(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Center latitude in decimal degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Center longitude in decimal degrees")

class Geofence(BaseModel):
    """Geofence definition model"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(..., min_length=1, max_length=100, description="Geofence name")
    description: Optional[str] = Field(None, max_length=500, description="Geofence description")
    type: str = Field(..., description="Geofence type")
    coordinates: GeofenceCoordinates
    radius: float = Field(..., gt=0, le=50000, description="Radius in meters")
    status: str = Field(default="active", description="Geofence status")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = Field(None, description="User who created the geofence")
    vehicle_ids: Optional[List[str]] = Field(default_factory=list, description="Vehicles this geofence applies to")
    schedule: Optional[Dict[str, Any]] = Field(None, description="Time-based schedule for geofence")
    alert_settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Alert configuration")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional geofence data")
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

    @validator('type')
    def validate_type(cls, v):
        valid_types = ['depot', 'restricted', 'customer', 'service', 'parking', 'maintenance', 'fuel_station', 'loading_zone']
        if v not in valid_types:
            raise ValueError(f"Geofence type must be one of {valid_types}")
        return v

    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ['active', 'inactive', 'restricted', 'emergency']
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return v

class GeofenceEvent(BaseModel):
    """Geofence entry/exit event model"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    geofence_id: str = Field(..., description="Geofence identifier")
    vehicle_id: str = Field(..., description="Vehicle identifier")
    event_type: str = Field(..., description="Event type (enter/exit)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    coordinates: GeofenceCoordinates
    speed: Optional[float] = Field(None, ge=0, description="Vehicle speed at event")
    heading: Optional[float] = Field(None, ge=0, lt=360, description="Vehicle heading at event")
    driver_id: Optional[str] = Field(None, description="Driver ID at time of event")
    trip_id: Optional[str] = Field(None, description="Associated trip ID")
    dwell_time: Optional[int] = Field(None, ge=0, description="Time spent in geofence (seconds)")
    alert_sent: bool = Field(default=False, description="Whether alert was sent")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional event data")
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

    @validator('event_type')
    def validate_event_type(cls, v):
        valid_types = ['enter', 'exit', 'dwell', 'violation']
        if v not in valid_types:
            raise ValueError(f"Event type must be one of {valid_types}")
        return v

class GeofenceCreate(BaseModel):
    """Input model for creating geofences"""
    name: str = Field(..., min_length=1, max_length=100, description="Geofence name")
    description: Optional[str] = Field(None, max_length=500, description="Geofence description")
    type: str = Field(..., description="Geofence type")
    coordinates: GeofenceCoordinates
    radius: float = Field(..., gt=0, le=50000, description="Radius in meters")
    status: str = Field(default="active", description="Geofence status")
    vehicle_ids: Optional[List[str]] = Field(default_factory=list, description="Vehicles this geofence applies to")
    schedule: Optional[Dict[str, Any]] = Field(None, description="Time-based schedule for geofence")
    alert_settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Alert configuration")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional geofence data")

class GeofenceUpdate(BaseModel):
    """Input model for updating geofences"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Geofence name")
    description: Optional[str] = Field(None, max_length=500, description="Geofence description")
    type: Optional[str] = Field(None, description="Geofence type")
    coordinates: Optional[GeofenceCoordinates] = Field(None, description="Geofence coordinates")
    radius: Optional[float] = Field(None, gt=0, le=50000, description="Radius in meters")
    status: Optional[str] = Field(None, description="Geofence status")
    vehicle_ids: Optional[List[str]] = Field(None, description="Vehicles this geofence applies to")
    schedule: Optional[Dict[str, Any]] = Field(None, description="Time-based schedule for geofence")
    alert_settings: Optional[Dict[str, Any]] = Field(None, description="Alert configuration")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional geofence data")

class GeofenceQuery(BaseModel):
    """Query parameters for geofences"""
    name: Optional[str] = Field(None, description="Filter by name (partial match)")
    type: Optional[str] = Field(None, description="Filter by geofence type")
    status: Optional[str] = Field(None, description="Filter by status")
    vehicle_id: Optional[str] = Field(None, description="Filter by vehicle ID")
    bounds: Optional[Dict[str, float]] = Field(None, description="Geographic bounds filter")
    limit: Optional[int] = Field(100, ge=1, le=1000, description="Maximum results")
    skip: Optional[int] = Field(0, ge=0, description="Results to skip for pagination")

class GeofenceResponse(BaseModel):
    """Response model for geofences"""
    geofences: List[Geofence]
    total_count: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool

class GeofenceEventQuery(BaseModel):
    """Query parameters for geofence events"""
    geofence_ids: Optional[List[str]] = Field(None, description="Filter by geofence IDs")
    vehicle_ids: Optional[List[str]] = Field(None, description="Filter by vehicle IDs")
    event_types: Optional[List[str]] = Field(None, description="Filter by event types")
    start_time: Optional[datetime] = Field(None, description="Start time for events")
    end_time: Optional[datetime] = Field(None, description="End time for events")
    driver_id: Optional[str] = Field(None, description="Filter by driver")
    trip_id: Optional[str] = Field(None, description="Filter by trip")
    limit: Optional[int] = Field(100, ge=1, le=1000, description="Maximum results")
    skip: Optional[int] = Field(0, ge=0, description="Results to skip for pagination")

class GeofenceEventResponse(BaseModel):
    """Response model for geofence events"""
    events: List[GeofenceEvent]
    total_count: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool
