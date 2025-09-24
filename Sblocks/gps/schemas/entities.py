"""
Entity schemas for GPS service - Pydantic V2
"""
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from enum import Enum

class GeofenceType(str, Enum):
    CIRCLE = "Circle"
    POINT = "Point"
    POLYGON = "Polygon"
    RECTANGLE = "Rectangle"

class GeofenceStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"

class GeofenceCategory(str, Enum):
    DEPOT = "depot"
    SERVICE = "service"
    DELIVERY = "delivery"
    RESTRICTED = "restricted"
    EMERGENCY = "emergency"
    BOUNDARY = "boundary"


class GeofenceCenter(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")

class GeofenceGeometry(BaseModel):
    type: GeofenceType = Field(..., description="Type of geofence geometry")
    coordinates: List[Any] = Field(..., description="GeoJSON coordinates")
    radius: Optional[int] = Field(None, ge=1, description="Radius for circle type")

    @field_validator('radius')
    @classmethod
    def validate_radius_for_circle(cls, v, info):
        if info.data.get('type') == GeofenceType.CIRCLE and v is None:
            raise ValueError("Radius is required for circle type geofences")
        return v

    @field_validator('coordinates')
    @classmethod
    def validate_coordinates(cls, v, info):
        if info.data.get('type') in [GeofenceType.POLYGON, GeofenceType.RECTANGLE] and not v:
            raise ValueError("Coordinates are required for polygon/rectangle geofences")
        return v


class Geofence(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat() + 'Z'}
    )

    id: Optional[str] = Field(default=None, alias="_id")
    name: str
    description: Optional[str] = ""
    type: GeofenceCategory
    status: GeofenceStatus = GeofenceStatus.ACTIVE
    geometry: GeofenceGeometry
    geojson_geometry: Optional[Dict[str, Any]] = None
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True



class LocationPoint(BaseModel):
    """Geographic point representation"""
    type: str = Field(default="Point", description="GeoJSON type")
    coordinates: List[float] = Field(..., description="[longitude, latitude]")
    
    @field_validator('coordinates')
    @classmethod
    def validate_coordinates(cls, v):
        if len(v) != 2:
            raise ValueError('Coordinates must contain exactly 2 values [longitude, latitude]')
        if not (-180 <= v[0] <= 180):
            raise ValueError('Longitude must be between -180 and 180')
        if not (-90 <= v[1] <= 90):
            raise ValueError('Latitude must be between -90 and 90')
        return v

class VehicleLocation(BaseModel):
    """Current vehicle location"""
    model_config = ConfigDict(populate_by_name=True)
    
    id: Optional[str] = Field(None, alias="_id", description="Document ID")
    vehicle_id: str = Field(..., description="Vehicle identifier")
    location: LocationPoint = Field(..., description="GeoJSON point")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    altitude: Optional[float] = Field(None, description="Altitude in meters")
    speed: Optional[float] = Field(None, ge=0, description="Speed in km/h")
    heading: Optional[float] = Field(None, ge=0, lt=360, description="Heading in degrees")
    accuracy: Optional[float] = Field(None, ge=0, description="GPS accuracy in meters")
    timestamp: datetime = Field(..., description="Location timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

class LocationHistory(BaseModel):
    """Historical vehicle location"""
    model_config = ConfigDict(populate_by_name=True)
    
    id: Optional[str] = Field(None, alias="_id", description="Document ID")
    vehicle_id: str = Field(..., description="Vehicle identifier")
    location: LocationPoint = Field(..., description="GeoJSON point")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    altitude: Optional[float] = Field(None, description="Altitude in meters")
    speed: Optional[float] = Field(None, ge=0, description="Speed in km/h")
    heading: Optional[float] = Field(None, ge=0, lt=360, description="Heading in degrees")
    accuracy: Optional[float] = Field(None, ge=0, description="GPS accuracy in meters")
    timestamp: datetime = Field(..., description="Location timestamp")
    created_at: datetime = Field(..., description="Record creation timestamp")

class GeofenceEventType(str, Enum):
    """Geofence event types"""
    ENTER = "enter"
    EXIT = "exit"
    DWELL = "dwell"

class Geofence(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={
            datetime: lambda v: v.isoformat() + 'Z'
        }
    )
    
    id: Optional[str] = Field(default=None, alias="_id")
    name: str = Field(..., min_length=1, max_length=100, description="Geofence name")
    description: Optional[str] = Field(default="", max_length=500, description="Geofence description")
    type: GeofenceCategory = Field(..., description="Category/type of geofence")
    status: GeofenceStatus = Field(default=GeofenceStatus.ACTIVE, description="Geofence status")
    geometry: GeofenceGeometry = Field(..., description="Geofence geometric definition")

class PlaceType(str, Enum):
    """Place types"""
    HOME = "home"
    WORK = "work"
    CUSTOM = "custom"
    DEPOT = "depot"
    FUEL_STATION = "fuel_station"
    SERVICE_CENTER = "service_center"

class Place(BaseModel):
    """User-saved place"""
    model_config = ConfigDict(populate_by_name=True)
    
    id: Optional[str] = Field(None, alias="_id", description="Document ID")
    user_id: str = Field(..., description="User identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Place name")
    description: Optional[str] = Field(None, max_length=500, description="Place description")
    location: LocationPoint = Field(..., description="GeoJSON point")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    address: Optional[str] = Field(None, max_length=200, description="Human-readable address")
    place_type: PlaceType = Field(default=PlaceType.CUSTOM, description="Type of place")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional place data")
    created_by: Optional[str] = Field(None, description="User who created the place")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

class TrackingSession(BaseModel):
    """Vehicle tracking session"""
    model_config = ConfigDict(populate_by_name=True)
    
    id: Optional[str] = Field(None, alias="_id", description="Document ID")
    vehicle_id: str = Field(..., description="Vehicle identifier")
    user_id: str = Field(..., description="User who started the session")
    started_at: datetime = Field(..., description="Session start timestamp")
    ended_at: Optional[datetime] = Field(None, description="Session end timestamp")
    is_active: bool = Field(default=True, description="Whether session is active")
    created_at: datetime = Field(..., description="Record creation timestamp")

class LocationUpdateRequest(BaseModel):
    """Request to update vehicle location"""
    vehicle_id: str = Field(..., description="Vehicle identifier")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    altitude: Optional[float] = Field(None, description="Altitude in meters")
    speed: Optional[float] = Field(None, ge=0, description="Speed in km/h")
    heading: Optional[float] = Field(None, ge=0, lt=360, description="Heading in degrees")
    accuracy: Optional[float] = Field(None, ge=0, description="GPS accuracy in meters")
    timestamp: Optional[datetime] = Field(None, description="Location timestamp")

class GeofenceCreateRequest(BaseModel):
    """Request to create a geofence"""
    name: str = Field(..., min_length=1, max_length=100, description="Geofence name")
    description: Optional[str] = Field(None, max_length=500, description="Geofence description")
    geometry: Dict[str, Any] = Field(..., description="Geofence geometry in unified format")
    type: GeofenceCategory = Field(default=GeofenceCategory.DEPOT, description="Category of geofence")
    status: GeofenceStatus = Field(default=GeofenceStatus.ACTIVE, description="Geofence status")

class PlaceCreateRequest(BaseModel):
    """Request to create a place"""
    name: str = Field(..., min_length=1, max_length=100, description="Place name")
    description: Optional[str] = Field(None, max_length=500, description="Place description")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    address: Optional[str] = Field(None, max_length=200, description="Human-readable address")
    place_type: PlaceType = Field(default=PlaceType.CUSTOM, description="Type of place")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional place data")