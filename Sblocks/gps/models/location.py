"""
Location tracking models for GPS service
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
    def __get_pydantic_json_schema__(cls, schema, _handler):
        schema.update(type="string")

class GPSCoordinates(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")
    altitude: Optional[float] = Field(None, description="Altitude in meters")
    accuracy: Optional[float] = Field(None, description="GPS accuracy in meters")

class Coordinate(BaseModel):
    """Simple coordinate model for geofencing and routing"""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")

class VehicleLocation(BaseModel):
    """Current location data for a vehicle"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    vehicle_id: str = Field(..., description="Vehicle identifier")
    coordinates: GPSCoordinates
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    speed: Optional[float] = Field(None, ge=0, description="Speed in km/h")
    heading: Optional[float] = Field(None, ge=0, lt=360, description="Direction in degrees")
    direction: Optional[str] = Field(None, description="Cardinal direction (N, NE, E, etc.)")
    status: str = Field(default="active", description="Vehicle status")
    fuel_level: Optional[float] = Field(None, ge=0, le=100, description="Fuel percentage")
    odometer: Optional[float] = Field(None, ge=0, description="Odometer reading in km")
    driver_id: Optional[str] = Field(None, description="Current driver ID")
    ignition: Optional[bool] = Field(None, description="Engine ignition status")
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

    @validator('direction')
    def validate_direction(cls, v):
        if v is not None:
            valid_directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW', 'North', 'South', 'East', 'West', 'North-East', 'South-East', 'South-West', 'North-West', 'Stopped']
            if v not in valid_directions:
                raise ValueError(f"Direction must be one of {valid_directions}")
        return v

class LocationHistory(BaseModel):
    """Historical location data for tracking and analytics"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    vehicle_id: str = Field(..., description="Vehicle identifier")
    coordinates: GPSCoordinates
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    speed: Optional[float] = Field(None, ge=0, description="Speed in km/h")
    heading: Optional[float] = Field(None, ge=0, lt=360, description="Direction in degrees")
    event_type: str = Field(default="location", description="Type of location event")
    event_description: Optional[str] = Field(None, description="Human readable event description")
    location_name: Optional[str] = Field(None, description="Named location if available")
    geofence_id: Optional[str] = Field(None, description="Associated geofence ID")
    trip_id: Optional[str] = Field(None, description="Associated trip ID")
    driver_id: Optional[str] = Field(None, description="Driver ID at time of event")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional event data")
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

    @validator('event_type')
    def validate_event_type(cls, v):
        valid_types = ['location', 'start', 'stop', 'idle', 'speeding', 'geofence_enter', 'geofence_exit', 'arrival', 'departure', 'maintenance', 'emergency']
        if v not in valid_types:
            raise ValueError(f"Event type must be one of {valid_types}")
        return v

class LocationUpdate(BaseModel):
    """Input model for location updates"""
    vehicle_id: str = Field(..., description="Vehicle identifier")
    coordinates: GPSCoordinates
    speed: Optional[float] = Field(None, ge=0, description="Speed in km/h")
    heading: Optional[float] = Field(None, ge=0, lt=360, description="Direction in degrees")
    status: Optional[str] = Field("active", description="Vehicle status")
    fuel_level: Optional[float] = Field(None, ge=0, le=100, description="Fuel percentage")
    odometer: Optional[float] = Field(None, ge=0, description="Odometer reading in km")
    driver_id: Optional[str] = Field(None, description="Current driver ID")
    ignition: Optional[bool] = Field(None, description="Engine ignition status")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional data")

class LocationQuery(BaseModel):
    """Query parameters for location data"""
    vehicle_ids: Optional[List[str]] = Field(None, description="Filter by vehicle IDs")
    start_time: Optional[datetime] = Field(None, description="Start time for historical data")
    end_time: Optional[datetime] = Field(None, description="End time for historical data")
    event_types: Optional[List[str]] = Field(None, description="Filter by event types")
    geofence_id: Optional[str] = Field(None, description="Filter by geofence")
    trip_id: Optional[str] = Field(None, description="Filter by trip")
    driver_id: Optional[str] = Field(None, description="Filter by driver")
    limit: Optional[int] = Field(100, ge=1, le=1000, description="Maximum results")
    skip: Optional[int] = Field(0, ge=0, description="Results to skip for pagination")

class LocationResponse(BaseModel):
    """Response model for location data"""
    locations: List[VehicleLocation]
    total_count: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool

class HistoryResponse(BaseModel):
    """Response model for historical location data"""
    history: List[LocationHistory]
    total_count: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool
