"""
Entity schemas for GPS service
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class LocationPoint(BaseModel):
    """Geographic point representation"""
    type: str = Field(default="Point", description="GeoJSON type")
    coordinates: List[float] = Field(..., description="[longitude, latitude]")


class VehicleLocation(BaseModel):
    """Current vehicle location"""
    id: Optional[str] = Field(None, alias="_id", description="Document ID")
    vehicle_id: str = Field(..., description="Vehicle identifier")
    location: LocationPoint = Field(..., description="GeoJSON point")
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    altitude: Optional[float] = Field(None, description="Altitude in meters")
    speed: Optional[float] = Field(None, description="Speed in km/h")
    heading: Optional[float] = Field(None, description="Heading in degrees")
    accuracy: Optional[float] = Field(None, description="GPS accuracy in meters")
    timestamp: datetime = Field(..., description="Location timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        populate_by_name = True


class LocationHistory(BaseModel):
    """Historical vehicle location"""
    id: Optional[str] = Field(None, alias="_id", description="Document ID")
    vehicle_id: str = Field(..., description="Vehicle identifier")
    location: LocationPoint = Field(..., description="GeoJSON point")
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    altitude: Optional[float] = Field(None, description="Altitude in meters")
    speed: Optional[float] = Field(None, description="Speed in km/h")
    heading: Optional[float] = Field(None, description="Heading in degrees")
    accuracy: Optional[float] = Field(None, description="GPS accuracy in meters")
    timestamp: datetime = Field(..., description="Location timestamp")
    created_at: datetime = Field(..., description="Record creation timestamp")
    
    class Config:
        populate_by_name = True


class GeofenceType(str, Enum):
    """Geofence types"""
    POLYGON = "polygon"
    CIRCLE = "circle"
    RECTANGLE = "rectangle"


class Geofence(BaseModel):
    """Geofence definition"""
    id: Optional[str] = Field(None, alias="_id", description="Document ID")
    name: str = Field(..., description="Geofence name")
    description: Optional[str] = Field(None, description="Geofence description")
    geometry: Dict[str, Any] = Field(..., description="GeoJSON geometry")
    geofence_type: GeofenceType = Field(..., description="Type of geofence")
    is_active: bool = Field(default=True, description="Whether geofence is active")
    created_by: Optional[str] = Field(None, description="User who created the geofence")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        populate_by_name = True


class GeofenceEventType(str, Enum):
    """Geofence event types"""
    ENTER = "enter"
    EXIT = "exit"
    DWELL = "dwell"


class GeofenceEvent(BaseModel):
    """Geofence event record"""
    id: Optional[str] = Field(None, alias="_id", description="Document ID")
    vehicle_id: str = Field(..., description="Vehicle identifier")
    geofence_id: str = Field(..., description="Geofence identifier")
    event_type: GeofenceEventType = Field(..., description="Type of event")
    location: LocationPoint = Field(..., description="GeoJSON point where event occurred")
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    timestamp: datetime = Field(..., description="Event timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional event data")
    created_at: datetime = Field(..., description="Record creation timestamp")
    
    class Config:
        populate_by_name = True


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
    id: Optional[str] = Field(None, alias="_id", description="Document ID")
    user_id: str = Field(..., description="User identifier")
    name: str = Field(..., description="Place name")
    description: Optional[str] = Field(None, description="Place description")
    location: LocationPoint = Field(..., description="GeoJSON point")
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    address: Optional[str] = Field(None, description="Human-readable address")
    place_type: PlaceType = Field(default=PlaceType.CUSTOM, description="Type of place")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional place data")
    created_by: Optional[str] = Field(None, description="User who created the place")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        populate_by_name = True


class TrackingSession(BaseModel):
    """Vehicle tracking session"""
    id: Optional[str] = Field(None, alias="_id", description="Document ID")
    vehicle_id: str = Field(..., description="Vehicle identifier")
    user_id: str = Field(..., description="User who started the session")
    started_at: datetime = Field(..., description="Session start timestamp")
    ended_at: Optional[datetime] = Field(None, description="Session end timestamp")
    is_active: bool = Field(default=True, description="Whether session is active")
    created_at: datetime = Field(..., description="Record creation timestamp")
    
    class Config:
        populate_by_name = True


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
    geometry: Dict[str, Any] = Field(..., description="GeoJSON geometry")
    geofence_type: GeofenceType = Field(default=GeofenceType.POLYGON, description="Type of geofence")
    is_active: bool = Field(default=True, description="Whether geofence is active")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class PlaceCreateRequest(BaseModel):
    """Request to create a place"""
    name: str = Field(..., min_length=1, max_length=100, description="Place name")
    description: Optional[str] = Field(None, max_length=500, description="Place description")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    address: Optional[str] = Field(None, max_length=200, description="Human-readable address")
    place_type: PlaceType = Field(default=PlaceType.CUSTOM, description="Type of place")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional place data")
