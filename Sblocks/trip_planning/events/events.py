"""
Event definitions for Trip Planning service
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

from schemas.entities import Trip, DriverAssignment


class EventType(str, Enum):
    """Event types for trip planning"""
    # Trip events
    TRIP_CREATED = "trip.created"
    TRIP_UPDATED = "trip.updated"
    TRIP_DELETED = "trip.deleted"
    TRIP_STARTED = "trip.started"
    TRIP_COMPLETED = "trip.completed"
    TRIP_DELAYED = "trip.delayed"
    
    # Driver events
    DRIVER_ASSIGNED = "driver.assigned"
    DRIVER_UNASSIGNED = "driver.unassigned"
    
    # Route events
    ROUTE_OPTIMIZED = "route.optimized"
    ROUTE_DEVIATED = "route.deviated"
    
    # Notification events
    NOTIFICATION_SENT = "notification.sent"
    
    # Service events
    SERVICE_STARTED = "service.started"


class BaseEvent(BaseModel):
    """Base event structure"""
    event_type: EventType
    event_id: str = Field(default_factory=lambda: str(datetime.utcnow().timestamp()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    service: str = "trip_planning"
    version: str = "1.0.0"
    data: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True


class TripCreatedEvent(BaseEvent):
    """Event published when a trip is created"""
    event_type: EventType = EventType.TRIP_CREATED
    
    @classmethod
    def from_trip(cls, trip: Trip) -> "TripCreatedEvent":
        return cls(
            data={
                "trip_id": trip.id,
                "name": trip.name,
                "created_by": trip.created_by,
                "scheduled_start_time": trip.scheduled_start_time.isoformat(),
                "origin": trip.origin.dict(),
                "destination": trip.destination.dict(),
                "status": trip.status,
                "priority": trip.priority
            }
        )


class TripUpdatedEvent(BaseEvent):
    """Event published when a trip is updated"""
    event_type: EventType = EventType.TRIP_UPDATED
    
    @classmethod
    def from_trip(cls, trip: Trip, previous_trip: Trip) -> "TripUpdatedEvent":
        # Calculate what changed
        changes = {}
        if trip.name != previous_trip.name:
            changes["name"] = {"old": previous_trip.name, "new": trip.name}
        if trip.status != previous_trip.status:
            changes["status"] = {"old": previous_trip.status, "new": trip.status}
        if trip.scheduled_start_time != previous_trip.scheduled_start_time:
            changes["scheduled_start_time"] = {
                "old": previous_trip.scheduled_start_time.isoformat(),
                "new": trip.scheduled_start_time.isoformat()
            }
        
        return cls(
            data={
                "trip_id": trip.id,
                "updated_at": trip.updated_at.isoformat(),
                "changes": changes
            }
        )


class TripDeletedEvent(BaseEvent):
    """Event published when a trip is deleted"""
    event_type: EventType = EventType.TRIP_DELETED
    
    @classmethod
    def from_trip(cls, trip: Trip) -> "TripDeletedEvent":
        return cls(
            data={
                "trip_id": trip.id,
                "name": trip.name,
                "created_by": trip.created_by,
                "status": trip.status
            }
        )


class TripStartedEvent(BaseEvent):
    """Event published when a trip starts"""
    event_type: EventType = EventType.TRIP_STARTED
    
    @classmethod
    def from_trip(cls, trip: Trip) -> "TripStartedEvent":
        return cls(
            data={
                "trip_id": trip.id,
                "name": trip.name,
                "actual_start_time": trip.actual_start_time.isoformat() if trip.actual_start_time else None,
                "scheduled_start_time": trip.scheduled_start_time.isoformat(),
                "driver_id": trip.driver_assignment.driver_id if trip.driver_assignment else None,
                "vehicle_id": trip.vehicle_id,
                "origin": trip.origin.dict(),
                "destination": trip.destination.dict()
            }
        )


class TripCompletedEvent(BaseEvent):
    """Event published when a trip is completed"""
    event_type: EventType = EventType.TRIP_COMPLETED
    
    @classmethod
    def from_trip(cls, trip: Trip) -> "TripCompletedEvent":
        duration = None
        if trip.actual_start_time and trip.actual_end_time:
            duration = int((trip.actual_end_time - trip.actual_start_time).total_seconds() / 60)
        
        return cls(
            data={
                "trip_id": trip.id,
                "name": trip.name,
                "actual_end_time": trip.actual_end_time.isoformat() if trip.actual_end_time else None,
                "actual_start_time": trip.actual_start_time.isoformat() if trip.actual_start_time else None,
                "duration_minutes": duration,
                "driver_id": trip.driver_assignment.driver_id if trip.driver_assignment else None,
                "vehicle_id": trip.vehicle_id
            }
        )


class TripDelayedEvent(BaseEvent):
    """Event published when a trip is delayed"""
    event_type: EventType = EventType.TRIP_DELAYED
    
    @classmethod
    def from_trip(cls, trip: Trip, delay_minutes: int, reason: str = None) -> "TripDelayedEvent":
        return cls(
            data={
                "trip_id": trip.id,
                "name": trip.name,
                "delay_minutes": delay_minutes,
                "reason": reason,
                "scheduled_start_time": trip.scheduled_start_time.isoformat(),
                "driver_id": trip.driver_assignment.driver_id if trip.driver_assignment else None
            }
        )


class DriverAssignedEvent(BaseEvent):
    """Event published when a driver is assigned to a trip"""
    event_type: EventType = EventType.DRIVER_ASSIGNED
    
    @classmethod
    def from_assignment(cls, assignment: DriverAssignment, trip: Trip) -> "DriverAssignedEvent":
        return cls(
            data={
                "assignment_id": assignment.id,
                "trip_id": assignment.trip_id,
                "driver_id": assignment.driver_id,
                "vehicle_id": assignment.vehicle_id,
                "assigned_by": assignment.assigned_by,
                "assigned_at": assignment.assigned_at.isoformat(),
                "trip_name": trip.name,
                "scheduled_start_time": trip.scheduled_start_time.isoformat()
            }
        )


class DriverUnassignedEvent(BaseEvent):
    """Event published when a driver is unassigned from a trip"""
    event_type: EventType = EventType.DRIVER_UNASSIGNED
    
    @classmethod
    def from_assignment(cls, assignment: DriverAssignment, trip: Trip) -> "DriverUnassignedEvent":
        return cls(
            data={
                "assignment_id": assignment.id,
                "trip_id": assignment.trip_id,
                "driver_id": assignment.driver_id,
                "vehicle_id": assignment.vehicle_id,
                "trip_name": trip.name,
                "unassigned_at": datetime.utcnow().isoformat()
            }
        )


class RouteOptimizedEvent(BaseEvent):
    """Event published when a route is optimized"""
    event_type: EventType = EventType.ROUTE_OPTIMIZED
    
    @classmethod
    def from_optimization(
        cls,
        trip_id: str,
        original_duration: int,
        optimized_duration: int,
        original_distance: float,
        optimized_distance: float
    ) -> "RouteOptimizedEvent":
        return cls(
            data={
                "trip_id": trip_id,
                "original_duration": original_duration,
                "optimized_duration": optimized_duration,
                "original_distance": original_distance,
                "optimized_distance": optimized_distance,
                "time_saved": original_duration - optimized_duration,
                "distance_saved": original_distance - optimized_distance
            }
        )


class NotificationSentEvent(BaseEvent):
    """Event published when a notification is sent"""
    event_type: EventType = EventType.NOTIFICATION_SENT
    
    @classmethod
    def from_notification(cls, notification_id: str, user_id: str, notification_type: str) -> "NotificationSentEvent":
        return cls(
            data={
                "notification_id": notification_id,
                "user_id": user_id,
                "notification_type": notification_type
            }
        )


class ServiceStartedEvent(BaseEvent):
    """Event published when the service starts"""
    event_type: EventType = EventType.SERVICE_STARTED
    
    @classmethod
    def create(cls, service_name: str, version: str) -> "ServiceStartedEvent":
        return cls(
            data={
                "service_name": service_name,
                "version": version,
                "started_at": datetime.utcnow().isoformat()
            }
        )
