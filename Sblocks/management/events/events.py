
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    
    
    VEHICLE_CREATED = "vehicle.created"
    VEHICLE_UPDATED = "vehicle.updated"
    VEHICLE_DELETED = "vehicle.deleted"
    VEHICLE_STATUS_CHANGED = "vehicle.status_changed"
    
    
    ASSIGNMENT_CREATED = "assignment.created"
    ASSIGNMENT_UPDATED = "assignment.updated"
    ASSIGNMENT_COMPLETED = "assignment.completed"
    ASSIGNMENT_CANCELLED = "assignment.cancelled"
    
    
    TRIP_STARTED = "trip.started"
    TRIP_ENDED = "trip.ended"
    
    
    DRIVER_CREATED = "driver.created"
    DRIVER_UPDATED = "driver.updated"
    DRIVER_STATUS_CHANGED = "driver.status_changed"
    
    
    ANALYTICS_REFRESHED = "analytics.refreshed"
    
    
    SERVICE_STARTED = "service.started"
    SERVICE_STOPPED = "service.stopped"
    SERVICE_HEALTH_CHECK = "service.health_check"


class BaseEvent(BaseModel):
    
    event_id: str = Field(default_factory=lambda: str(datetime.utcnow().timestamp()))
    event_type: EventType
    service: str = "management"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None


class VehicleEvent(BaseEvent):
    
    vehicle_id: str
    registration_number: str
    status: str
    data: Optional[Dict[str, Any]] = None


class AssignmentEvent(BaseEvent):
    
    assignment_id: str
    vehicle_id: str
    driver_id: str
    assignment_type: str
    status: str
    data: Optional[Dict[str, Any]] = None


class TripEvent(BaseEvent):
    
    trip_id: str
    vehicle_id: str
    driver_id: str
    assignment_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class DriverEvent(BaseEvent):
    
    driver_id: str
    employee_id: str
    status: str
    data: Optional[Dict[str, Any]] = None


class AnalyticsEvent(BaseEvent):
    
    metric_type: str
    data: Optional[Dict[str, Any]] = None


class ServiceEvent(BaseEvent):
    
    service_status: str
    version: str = "1.0.0"
    data: Optional[Dict[str, Any]] = None


class UserEvent(BaseEvent):
    
    user_id: str
    action: str  
    data: Optional[Dict[str, Any]] = None
