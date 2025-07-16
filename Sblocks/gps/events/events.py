"""
Event definitions for GPS service
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class EventType(str, Enum):
    """Event types for GPS service"""
    SERVICE_STARTED = "service_started"
    LOCATION_UPDATED = "location_updated"
    GEOFENCE_CREATED = "geofence_created"
    GEOFENCE_EVENT = "geofence_event"
    PLACE_CREATED = "place_created"
    TRACKING_SESSION_STARTED = "tracking_session_started"
    TRACKING_SESSION_ENDED = "tracking_session_ended"


class BaseEvent(BaseModel):
    """Base event schema"""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique event ID")
    event_type: EventType = Field(..., description="Type of event")
    service: str = Field(default="gps", description="Service that generated the event")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for request tracing")
    data: Dict[str, Any] = Field(default_factory=dict, description="Event data")


class LocationUpdatedEvent(BaseEvent):
    """Location updated event"""
    event_type: EventType = Field(default=EventType.LOCATION_UPDATED, description="Event type")
    vehicle_id: str = Field(..., description="Vehicle identifier")
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    timestamp_location: datetime = Field(..., description="Location timestamp")


class GeofenceCreatedEvent(BaseEvent):
    """Geofence created event"""
    event_type: EventType = Field(default=EventType.GEOFENCE_CREATED, description="Event type")
    geofence_id: str = Field(..., description="Geofence identifier")
    name: str = Field(..., description="Geofence name")
    created_by: Optional[str] = Field(None, description="User who created the geofence")


class GeofenceEvent(BaseEvent):
    """Geofence event (enter/exit/dwell)"""
    event_type: EventType = Field(default=EventType.GEOFENCE_EVENT, description="Event type")
    vehicle_id: str = Field(..., description="Vehicle identifier")
    geofence_id: str = Field(..., description="Geofence identifier")
    geofence_event_type: str = Field(..., description="Geofence event type (enter/exit/dwell)")
    timestamp_event: datetime = Field(..., description="Geofence event timestamp")


class PlaceCreatedEvent(BaseEvent):
    """Place created event"""
    event_type: EventType = Field(default=EventType.PLACE_CREATED, description="Event type")
    place_id: str = Field(..., description="Place identifier")
    user_id: str = Field(..., description="User identifier")
    name: str = Field(..., description="Place name")


class TrackingSessionEvent(BaseEvent):
    """Tracking session event"""
    vehicle_id: str = Field(..., description="Vehicle identifier")
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session identifier")


class ServiceStartedEvent(BaseEvent):
    """Service started event"""
    event_type: EventType = Field(default=EventType.SERVICE_STARTED, description="Event type")
    version: str = Field(..., description="Service version")
    features: Dict[str, Any] = Field(default_factory=dict, description="Service features")
