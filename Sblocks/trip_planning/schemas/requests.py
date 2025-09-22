"""
Request schemas for Trip Planning service
"""
from pydantic import BaseModel, Field, validator, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime

from .entities import (
    TripStatus, TripPriority, ConstraintType, NotificationType,
    LocationPoint, Address, Waypoint, TripConstraint, RouteInfo,
    ScheduleInfo, RouteSummary, SmartTripBenefits
)


class ScheduledTripRequest(BaseModel):
    """Request to create a scheduled trip"""
    name: str = Field(..., min_length=1, max_length=200, description="Trip name")
    description: Optional[str] = None

    start_time_window: datetime = Field(..., description="When the trip should start")
    end_time_window: datetime = Field(..., description="When the trip should end")

    # Route
    origin: Waypoint = Field(..., description="Starting point")
    destination: Waypoint = Field(..., description="End point")
    waypoints: List[Waypoint] = Field(default_factory=list, description="Intermediate stops")
    route_info: Optional[RouteInfo] = Field(None, description="Route information including distance, duration, and coordinates")
    
    # Trip details
    priority: TripPriority = Field(..., description="Trip priority")

class ScheduledTripRequest(BaseModel):
    """Request to create a scheduled trip"""
    name: str = Field(..., min_length=1, max_length=200, description="Trip name")
    description: Optional[str] = None

    start_time_window: datetime = Field(..., description="When the trip should start")
    end_time_window: datetime = Field(..., description="When the trip should end")

    # Route
    origin: Waypoint = Field(..., description="Starting point")
    destination: Waypoint = Field(..., description="End point")
    waypoints: List[Waypoint] = Field(default_factory=list, description="Intermediate stops")
    route_info: Optional[RouteInfo] = Field(None, description="Route information including distance, duration, and coordinates")
    
    # Trip details
    priority: TripPriority = Field(..., description="Trip priority")

class CreateTripRequest(BaseModel):
    """Request to create a new trip"""
    name: str = Field(..., min_length=1, max_length=200, description="Trip name")
    description: str = Field(..., max_length=1000, description="Trip description")
    
    # Schedule
    scheduled_start_time: datetime = Field(..., description="When the trip should start")
    scheduled_end_time: datetime = Field(..., description="When the trip should end")
    
    # Route
    origin: Waypoint = Field(..., description="Starting point")
    destination: Waypoint = Field(..., description="End point")
    waypoints: List[Waypoint] = Field(default_factory=list, description="Intermediate stops")
    route_info: Optional[RouteInfo] = Field(None, description="Route information including distance, duration, and coordinates")
    
    # Trip details
    priority: TripPriority = Field(..., description="Trip priority")
    vehicle_id: str = Field(..., description="Assigned vehicle ID")
    driver_assignment: str = Field(..., description="Assigned driver ID")
    
    # Constraints
    constraints: List[TripConstraint] = Field(default_factory=list)
    
    # Custom fields
    custom_fields: Optional[Dict[str, Any]] = None
    
    @validator('scheduled_end_time')
    def validate_end_time(cls, v, values):
        if v and 'scheduled_start_time' in values:
            if v <= values['scheduled_start_time']:
                raise ValueError('End time must be after start time')
        return v

    @validator('waypoints')
    def validate_waypoints_order(cls, v):
        if v:
            orders = [wp.order for wp in v]
            if len(orders) != len(set(orders)):
                raise ValueError('Waypoint orders must be unique')
            if orders != sorted(orders):
                raise ValueError('Waypoints must be ordered correctly')
        return v
    
class CreateSmartTripRequest(BaseModel):
    """Request to create a smart trip"""
    # normal trip details
    smart_id: str = Field(..., min_length=1, max_length=200, description="Trip name")
    trip_id: str
    trip_name: str = Field(..., min_length=1, max_length=200, description="Trip name")
    description: Optional[str] = None

    # Original schedule
    original_start_time: datetime = Field(..., description="When the trip should start")
    original_end_time: datetime = Field(..., description="When the trip should end")
    
    # Optimised schedule
    optimized_start_time: datetime = Field(..., description="When the trip should start")
    optimized_end_time: datetime = Field(..., description="When the trip should end")
    vehicle_id: str = Field(..., description="Assigned vehicle ID")
    vehicle_name: str
    driver_id: str 
    driver_name: str
    priority: TripPriority = Field(..., description="Trip priority")

    # route
    origin: Waypoint = Field(..., description="Starting point")
    destination: Waypoint = Field(..., description="End point")
    waypoints: Optional[List[Waypoint]] = None
    estimated_distance: float
    estimated_duration: float
    route_info: Optional[RouteInfo] = Field(None, description="Route information including distance, duration, and coordinates")
    
    # benefits
    time_saved: str
    fuel_efficiency: str
    route_optimisation: str
    driver_utilisation: str

    confidence: str
    reasoning: List[str]

    





class UpdateTripRequest(BaseModel):
    """Request to update a trip"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    scheduled_start_time: Optional[datetime] = None
    scheduled_end_time: Optional[datetime] = None
    priority: Optional[TripPriority] = None
    status: Optional[TripStatus] = None
    vehicle_id: Optional[str] = None
    actual_start_time: Optional[datetime]= None
    actual_end_time: Optional[datetime] = None
    route_info: Optional[RouteInfo] = Field(None, description="Route information")
    custom_fields: Optional[Dict[str, Any]] = None

class FinishTripRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    actual_end_time: Optional[datetime] = None
    driver_assignment: Optional[str] = None
    status: Optional[str]



class TripFilterRequest(BaseModel):
    """Request to filter trips"""
    name: Optional[str] = None
    status: Optional[List[TripStatus]] = None
    priority: Optional[List[TripPriority]] = None
    driver_assignment: Optional[str] = None
    vehicle_id: Optional[str] = None
    created_by: Optional[str] = None
    
    # Date filters
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    # Location filters
    origin_area: Optional[LocationPoint] = None
    destination_area: Optional[LocationPoint] = None
    area_radius: Optional[float] = Field(None, description="Radius in km for area filters")
    
    # Pagination
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1, le=1000)
    
    # Sorting
    sort_by: Optional[str] = Field(default="scheduled_start_time")
    sort_order: Optional[str] = Field(default="asc", pattern="^(asc|desc)$")


class AssignDriverRequest(BaseModel):
    """Request to assign a driver to a trip"""
    driver_id: str = Field(..., description="Driver ID to assign")
    vehicle_id: Optional[str] = Field(None, description="Vehicle ID (optional)")
    notes: Optional[str] = Field(None, max_length=500)


class CreateConstraintRequest(BaseModel):
    """Request to add a constraint to a trip"""
    type: ConstraintType = Field(..., description="Type of constraint")
    value: Optional[Dict[str, Any]] = Field(None, description="Constraint parameters")
    priority: int = Field(default=1, ge=1, le=10, description="Constraint priority")


class UpdateConstraintRequest(BaseModel):
    """Request to update a trip constraint"""
    value: Optional[Dict[str, Any]] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    is_active: Optional[bool] = None


class RouteOptimizationRequest(BaseModel):
    """Request to optimize a trip route"""
    trip_id: str = Field(..., description="Trip ID to optimize")
    optimization_type: str = Field(
        default="fastest",
        pattern="^(fastest|shortest|fuel_efficient|balanced)$"
    )
    avoid_traffic: bool = Field(default=True)
    real_time: bool = Field(default=True, description="Use real-time traffic data")


class AnalyticsRequest(BaseModel):
    """Request for trip analytics"""
    # Date range
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    # Filters
    driver_ids: Optional[List[str]] = None
    vehicle_ids: Optional[List[str]] = None
    trip_ids: Optional[List[str]] = None
    
    # Grouping
    group_by: Optional[str] = Field(
        default=None,
        pattern="^(day|week|month|driver|vehicle)$"
    )
    
    # Metrics
    metrics: List[str] = Field(
        default=["duration", "distance", "fuel", "cost"],
        description="Metrics to include in analytics"
    )


class NotificationRequest(BaseModel):
    """Request to send a notification"""
    user_ids: List[str] = Field(..., description="Recipient user IDs")
    type: NotificationType = Field(..., description="Notification type")
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=1000)
    
    # Related entities
    trip_id: Optional[str] = None
    driver_id: Optional[str] = None
    
    # Delivery options
    channels: List[str] = Field(
        default=["push"],
        description="Delivery channels"
    )
    scheduled_for: Optional[datetime] = Field(
        None,
        description="Schedule notification for future delivery"
    )
    
    # Additional data
    data: Optional[Dict[str, Any]] = None


class UpdateNotificationPreferencesRequest(BaseModel):
    """Request to update notification preferences"""
    trip_started: Optional[bool] = None
    trip_completed: Optional[bool] = None
    trip_delayed: Optional[bool] = None
    driver_late: Optional[bool] = None
    route_changed: Optional[bool] = None
    traffic_alert: Optional[bool] = None
    driver_assigned: Optional[bool] = None
    driver_unassigned: Optional[bool] = None
    
    # Delivery channels
    email_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    
    # Contact info
    email: Optional[str] = Field(None, pattern=r'^[^@]+@[^@]+\.[^@]+$')
    phone: Optional[str] = Field(None, pattern=r'^\+?[\d\s\-\(\)]+$')
    
    # Schedule
    quiet_hours_start: Optional[str] = Field(None, pattern=r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
    quiet_hours_end: Optional[str] = Field(None, pattern=r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
    timezone: Optional[str] = None


class DriverAvailabilityRequest(BaseModel):
    """Request to check driver availability"""
    driver_ids: Optional[List[str]] = None
    start_time: datetime = Field(..., description="Start of time period to check")
    end_time: datetime = Field(..., description="End of time period to check")
    
    @validator('end_time')
    def validate_end_time(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v


class TripProgressRequest(BaseModel):
    """Request to update trip progress"""
    current_location: LocationPoint = Field(..., description="Current vehicle location")
    status: Optional[TripStatus] = None
    estimated_arrival: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=500)


class DriverPingRequest(BaseModel):
    """Request from driver's phone ping"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat() + 'Z'})
    
    trip_id: str = Field(..., description="Trip ID that driver is currently on")
    location: LocationPoint = Field(..., description="Driver's current location")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Ping timestamp")
