"""
Request schemas for GPS service
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from schemas.entities import GeofenceType, PlaceType


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


class LocationHistoryRequest(BaseModel):
    """Request for location history"""
    vehicle_id: str = Field(..., description="Vehicle identifier")
    start_time: Optional[datetime] = Field(None, description="Start time for history")
    end_time: Optional[datetime] = Field(None, description="End time for history")
    limit: int = Field(default=1000, ge=1, le=10000, description="Maximum number of records")


class GeofenceCreateRequest(BaseModel):
    """Request to create a geofence"""
    name: str = Field(..., min_length=1, max_length=100, description="Geofence name")
    description: Optional[str] = Field(None, max_length=500, description="Geofence description")
    geometry: Dict[str, Any] = Field(..., description="GeoJSON geometry")
    geofence_type: GeofenceType = Field(default=GeofenceType.POLYGON, description="Type of geofence")
    is_active: bool = Field(default=True, description="Whether geofence is active")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class GeofenceUpdateRequest(BaseModel):
    """Request to update a geofence"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Geofence name")
    description: Optional[str] = Field(None, max_length=500, description="Geofence description")
    geometry: Optional[Dict[str, Any]] = Field(None, description="GeoJSON geometry")
    is_active: Optional[bool] = Field(None, description="Whether geofence is active")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class PlaceCreateRequest(BaseModel):
    """Request to create a place"""
    name: str = Field(..., min_length=1, max_length=100, description="Place name")
    description: Optional[str] = Field(None, max_length=500, description="Place description")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    address: Optional[str] = Field(None, max_length=200, description="Human-readable address")
    place_type: PlaceType = Field(default=PlaceType.CUSTOM, description="Type of place")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional place data")


class PlaceUpdateRequest(BaseModel):
    """Request to update a place"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Place name")
    description: Optional[str] = Field(None, max_length=500, description="Place description")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude coordinate")
    address: Optional[str] = Field(None, max_length=200, description="Human-readable address")
    place_type: Optional[PlaceType] = Field(None, description="Type of place")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional place data")


class TrackingSessionRequest(BaseModel):
    """Request to start tracking session"""
    vehicle_id: str = Field(..., description="Vehicle identifier")


class VehicleSearchRequest(BaseModel):
    """Request to search vehicles in area"""
    center_latitude: float = Field(..., ge=-90, le=90, description="Center latitude")
    center_longitude: float = Field(..., ge=-180, le=180, description="Center longitude")
    radius_meters: float = Field(..., gt=0, le=100000, description="Search radius in meters")


class PlaceSearchRequest(BaseModel):
    """Request to search places"""
    search_term: str = Field(..., min_length=1, max_length=100, description="Search term")
    limit: int = Field(default=50, ge=1, le=100, description="Maximum number of results")


class NearbyPlacesRequest(BaseModel):
    """Request for nearby places"""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    radius_meters: float = Field(default=1000, gt=0, le=50000, description="Search radius in meters")
    limit: int = Field(default=50, ge=1, le=100, description="Maximum number of results")
