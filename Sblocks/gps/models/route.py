"""
Route and path models for GPS service
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator
from bson import ObjectId

class RouteStatus(str, Enum):
    """Route status enumeration"""
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

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

class RoutePoint(BaseModel):
    """Single point in a route"""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")
    sequence: int = Field(..., ge=0, description="Order in the route")
    timestamp: Optional[datetime] = Field(None, description="When vehicle reached this point")
    speed: Optional[float] = Field(None, ge=0, description="Speed at this point")
    heading: Optional[float] = Field(None, ge=0, lt=360, description="Direction at this point")

class VehicleRoute(BaseModel):
    """Route/path data for vehicles"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    vehicle_id: str = Field(..., description="Vehicle identifier")
    route_name: Optional[str] = Field(None, description="Human readable route name")
    route_type: str = Field(default="tracked", description="Type of route")
    trip_id: Optional[str] = Field(None, description="Associated trip ID")
    driver_id: Optional[str] = Field(None, description="Driver who drove this route")
    points: List[RoutePoint] = Field(..., description="Route points in order")
    start_time: Optional[datetime] = Field(None, description="Route start time")
    end_time: Optional[datetime] = Field(None, description="Route end time")
    total_distance: Optional[float] = Field(None, ge=0, description="Total distance in km")
    total_duration: Optional[int] = Field(None, ge=0, description="Total duration in seconds")
    average_speed: Optional[float] = Field(None, ge=0, description="Average speed in km/h")
    max_speed: Optional[float] = Field(None, ge=0, description="Maximum speed in km/h")
    fuel_consumed: Optional[float] = Field(None, ge=0, description="Fuel consumed in liters")
    status: str = Field(default="active", description="Route status")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional route data")
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

    @validator('route_type')
    def validate_route_type(cls, v):
        valid_types = ['tracked', 'planned', 'optimized', 'manual', 'emergency']
        if v not in valid_types:
            raise ValueError(f"Route type must be one of {valid_types}")
        return v

    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ['active', 'completed', 'interrupted', 'planned']
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return v

class RouteSegment(BaseModel):
    """Individual segment of a route for analysis"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    route_id: str = Field(..., description="Parent route ID")
    vehicle_id: str = Field(..., description="Vehicle identifier")
    start_point: RoutePoint
    end_point: RoutePoint
    distance: float = Field(..., ge=0, description="Segment distance in km")
    duration: int = Field(..., ge=0, description="Segment duration in seconds")
    average_speed: float = Field(..., ge=0, description="Average speed in km/h")
    max_speed: float = Field(..., ge=0, description="Maximum speed in km/h")
    idle_time: Optional[int] = Field(None, ge=0, description="Idle time in seconds")
    fuel_consumed: Optional[float] = Field(None, ge=0, description="Fuel consumed in liters")
    events: Optional[List[str]] = Field(default_factory=list, description="Event IDs that occurred in this segment")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class PlannedRoute(BaseModel):
    """Planned route for vehicles"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(..., min_length=1, description="Route name")
    description: Optional[str] = Field(None, description="Route description")
    vehicle_id: Optional[str] = Field(None, description="Assigned vehicle")
    driver_id: Optional[str] = Field(None, description="Assigned driver")
    trip_id: Optional[str] = Field(None, description="Associated trip")
    waypoints: List[RoutePoint] = Field(..., description="Planned waypoints")
    estimated_distance: Optional[float] = Field(None, ge=0, description="Estimated distance in km")
    estimated_duration: Optional[int] = Field(None, ge=0, description="Estimated duration in seconds")
    scheduled_start: Optional[datetime] = Field(None, description="Scheduled start time")
    scheduled_end: Optional[datetime] = Field(None, description="Scheduled end time")
    priority: int = Field(default=1, ge=1, le=5, description="Route priority (1=low, 5=high)")
    status: str = Field(default="planned", description="Route status")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = Field(None, description="User who created the route")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional route data")
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ['planned', 'assigned', 'in_progress', 'completed', 'cancelled']
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return v

class RouteEvent(BaseModel):
    """Route event model for tracking route-related events"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    route_id: str = Field(..., description="Route identifier")
    vehicle_id: str = Field(..., description="Vehicle identifier")
    event_type: str = Field(..., description="Type of event (started, completed, paused, etc.)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    location: Optional[Dict[str, Any]] = Field(None, description="Location where event occurred")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional event data")
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class RouteCreate(BaseModel):
    """Input model for creating routes"""
    vehicle_id: str = Field(..., description="Vehicle identifier")
    route_name: Optional[str] = Field(None, description="Human readable route name")
    route_type: str = Field(default="tracked", description="Type of route")
    trip_id: Optional[str] = Field(None, description="Associated trip ID")
    driver_id: Optional[str] = Field(None, description="Driver who drove this route")
    points: List[RoutePoint] = Field(..., description="Route points in order")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional route data")

class PlannedRouteCreate(BaseModel):
    """Input model for creating planned routes"""
    name: str = Field(..., min_length=1, description="Route name")
    description: Optional[str] = Field(None, description="Route description")
    vehicle_id: Optional[str] = Field(None, description="Assigned vehicle")
    driver_id: Optional[str] = Field(None, description="Assigned driver")
    trip_id: Optional[str] = Field(None, description="Associated trip")
    waypoints: List[RoutePoint] = Field(..., description="Planned waypoints")
    scheduled_start: Optional[datetime] = Field(None, description="Scheduled start time")
    scheduled_end: Optional[datetime] = Field(None, description="Scheduled end time")
    priority: int = Field(default=1, ge=1, le=5, description="Route priority")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional route data")

class RouteQuery(BaseModel):
    """Query parameters for routes"""
    vehicle_ids: Optional[List[str]] = Field(None, description="Filter by vehicle IDs")
    route_type: Optional[str] = Field(None, description="Filter by route type")
    trip_id: Optional[str] = Field(None, description="Filter by trip ID")
    driver_id: Optional[str] = Field(None, description="Filter by driver ID")
    start_time: Optional[datetime] = Field(None, description="Filter by start time")
    end_time: Optional[datetime] = Field(None, description="Filter by end time")
    status: Optional[str] = Field(None, description="Filter by status")
    limit: Optional[int] = Field(100, ge=1, le=1000, description="Maximum results")
    skip: Optional[int] = Field(0, ge=0, description="Results to skip for pagination")

class RouteResponse(BaseModel):
    """Response model for routes"""
    routes: List[VehicleRoute]
    total_count: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool

class PlannedRouteResponse(BaseModel):
    """Response model for planned routes"""
    routes: List[PlannedRoute]
    total_count: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool

class RouteAnalytics(BaseModel):
    """Route analytics model"""
    route_id: str
    total_distance: float
    total_duration: int
    average_speed: float
    max_speed: float
    idle_time: int
    fuel_efficiency: Optional[float]
    geofence_violations: int
    speed_violations: int
    stops_count: int
    route_efficiency: float  # Percentage of optimal route
    cost_estimate: Optional[float]
