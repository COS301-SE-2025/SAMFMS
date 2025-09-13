"""
Entity schemas for Trip Planning service
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class RouteBounds(BaseModel):
    """Route bounds information"""
    southWest: Dict[str, float] = Field(..., alias="_southWest", description="Southwest coordinate")
    northEast: Dict[str, float] = Field(..., alias="_northEast", description="Northeast coordinate")
    
    class Config:
        populate_by_name = True


class RouteInfo(BaseModel):
    """Route information including distance, duration, and coordinates"""
    distance: float = Field(..., description="Route distance in meters")
    duration: float = Field(..., description="Route duration in seconds") 
    coordinates: List[List[float]] = Field(..., description="Route coordinates as [lat, lng] pairs")
    bounds: Optional[RouteBounds] = Field(None, description="Route bounds")


class TripStatus(str, Enum):
    """Trip status enumeration"""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DELAYED = "delayed"
    MISSED = "missed"


class TripPriority(str, Enum):
    """Trip priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ConstraintType(str, Enum):
    """Trip constraint types"""
    AVOID_TOLLS = "avoid_tolls"
    AVOID_HIGHWAYS = "avoid_highways"
    AVOID_FERRIES = "avoid_ferries"
    SHORTEST_ROUTE = "shortest_route"
    FASTEST_ROUTE = "fastest_route"
    FUEL_EFFICIENT = "fuel_efficient"
    AVOID_AREA = "avoid_area"
    PREFERRED_ROUTE = "preferred_route"
    TIME_WINDOW = "time_window"


class NotificationType(str, Enum):
    """Notification types"""
    TRIP_STARTED = "trip_started"
    TRIP_COMPLETED = "trip_completed"
    TRIP_DELAYED = "trip_delayed"
    DRIVER_LATE = "driver_late"
    ROUTE_CHANGED = "route_changed"
    TRAFFIC_ALERT = "traffic_alert"
    DRIVER_ASSIGNED = "driver_assigned"
    DRIVER_UNASSIGNED = "driver_unassigned"


class LocationPoint(BaseModel):
    """Geographic point representation"""
    type: str = Field(default="Point", description="GeoJSON type")
    coordinates: List[float] = Field(..., description="[longitude, latitude]")


class Address(BaseModel):
    """Address information"""
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    formatted_address: Optional[str] = None


class Waypoint(BaseModel):
    """Trip waypoint"""
    id: Optional[str] = Field(None, alias="_id")
    location: LocationPoint = Field(..., description="GeoJSON point")
    address: Optional[Address] = None
    name: Optional[str] = None
    arrival_time: Optional[datetime] = None
    departure_time: Optional[datetime] = None
    stop_duration: Optional[int] = Field(None, description="Stop duration in minutes")
    order: int = Field(..., description="Order in the trip")
    
    class Config:
        populate_by_name = True


class TripConstraint(BaseModel):
    """Trip routing constraint"""
    id: Optional[str] = Field(None, alias="_id")
    trip_id: str = Field(..., description="Associated trip ID")
    type: ConstraintType = Field(..., description="Type of constraint")
    value: Optional[Dict[str, Any]] = Field(None, description="Constraint parameters")
    priority: int = Field(default=1, description="Constraint priority (1-10)")
    is_active: bool = Field(default=True, description="Whether constraint is active")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True


class DriverAssignment(BaseModel):
    """Driver assignment to trip"""
    driver_id: str = Field(..., description="Driver ID")
    driver_name: Optional[str] = Field(None, description="Driver name")

    class Config:
        populate_by_name = True


class Trip(BaseModel):
    """Trip entity"""
    id: Optional[str] = Field(None, alias="_id", description="Trip ID")
    name: str = Field(..., description="Trip name/title")
    description: Optional[str] = None
    
    # Trip schedule
    scheduled_start_time: datetime = Field(..., description="Scheduled start time")
    scheduled_end_time: Optional[datetime] = None
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    
    # Trip route
    origin: Waypoint = Field(..., description="Starting point")
    destination: Waypoint = Field(..., description="End point")
    waypoints: List[Waypoint] = Field(default_factory=list, description="Intermediate stops")
    route_info: Optional[RouteInfo] = Field(None, description="Route information including distance, duration, and coordinates")
    
    # Trip details
    status: TripStatus = Field(default=TripStatus.SCHEDULED)
    priority: TripPriority = Field(default=TripPriority.NORMAL)
    estimated_end_time: Optional[datetime] = Field(None, description="Estimated end time")
    estimated_distance: Optional[float] = Field(None, description="Estimated distance in km")
    estimated_duration: Optional[float] = Field(None, description="Estimated duration in minutes")
    
    # Assignments
    driver_assignment: Optional[str] = None
    vehicle_id: Optional[str] = None
    
    # Constraints
    constraints: List[TripConstraint] = Field(default_factory=list)
    
    # Metadata
    created_by: str = Field(..., description="User who created the trip")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Custom fields
    custom_fields: Optional[Dict[str, Any]] = None
    
    class Config:
        populate_by_name = True


class TripAnalytics(BaseModel):
    """Trip analytics data"""
    id: Optional[str] = Field(None, alias="_id")
    trip_id: str = Field(..., description="Trip ID")
    
    # Performance metrics
    planned_duration: Optional[int] = Field(None, description="Planned duration in minutes")
    actual_duration: Optional[int] = Field(None, description="Actual duration in minutes")
    planned_distance: Optional[float] = Field(None, description="Planned distance in km")
    actual_distance: Optional[float] = Field(None, description="Actual distance in km")
    
    # Efficiency metrics
    fuel_consumption: Optional[float] = Field(None, description="Fuel consumed in liters")
    cost: Optional[float] = Field(None, description="Trip cost")
    delays: Optional[int] = Field(None, description="Total delays in minutes")
    
    # Route metrics
    route_deviation: Optional[float] = Field(None, description="Deviation from planned route in km")
    traffic_delays: Optional[int] = Field(None, description="Traffic-related delays in minutes")
    
    # Timestamps
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True


class Notification(BaseModel):
    """User notification"""
    id: Optional[str] = Field(None, alias="_id")
    user_id: str = Field(..., description="Recipient user ID")
    type: NotificationType = Field(..., description="Notification type")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    
    # Related entities
    trip_id: Optional[str] = None
    driver_id: Optional[str] = None
    
    # Notification data
    data: Optional[Dict[str, Any]] = Field(None, description="Additional notification data")
    
    # Status
    is_read: bool = Field(default=False)
    sent_at: datetime = Field(default_factory=datetime.utcnow)
    read_at: Optional[datetime] = None
    
    # Delivery
    channels: List[str] = Field(default_factory=list, description="Delivery channels (email, push, sms)")
    delivery_status: Optional[Dict[str, Any]] = None
    
    class Config:
        populate_by_name = True


class NotificationPreferences(BaseModel):
    """User notification preferences"""
    id: Optional[str] = Field(None, alias="_id")
    user_id: str = Field(..., description="User ID")
    
    # Notification types preferences
    trip_started: bool = Field(default=True)
    trip_completed: bool = Field(default=True)
    trip_delayed: bool = Field(default=True)
    driver_late: bool = Field(default=True)
    route_changed: bool = Field(default=True)
    traffic_alert: bool = Field(default=False)
    driver_assigned: bool = Field(default=True)
    driver_unassigned: bool = Field(default=True)
    
    # Delivery channels
    email_enabled: bool = Field(default=True)
    push_enabled: bool = Field(default=True)
    sms_enabled: bool = Field(default=False)
    
    # Contact information
    email: Optional[str] = None
    phone: Optional[str] = None
    
    # Schedule
    quiet_hours_start: Optional[str] = Field(None, description="HH:MM format")
    quiet_hours_end: Optional[str] = Field(None, description="HH:MM format")
    timezone: str = Field(default="UTC")
    
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True

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


class PhoneUsageViolationType(str, Enum):
    """Phone usage violation types"""
    PHONE_USAGE = "phone_usage"


class PhoneUsageViolation(BaseModel):
    """Phone usage violation during trip"""
    id: Optional[str] = Field(None, alias="_id", description="Violation ID")
    trip_id: str = Field(..., description="Associated trip ID")
    driver_id: str = Field(..., description="Driver ID")
    violation_type: PhoneUsageViolationType = Field(default=PhoneUsageViolationType.PHONE_USAGE)
    
    # Start violation data
    start_time: datetime = Field(..., description="When violation started")
    start_location: LocationPoint = Field(..., description="Location where violation started")
    
    # End violation data (optional - set when violation ends)
    end_time: Optional[datetime] = Field(None, description="When violation ended")
    end_location: Optional[LocationPoint] = Field(None, description="Location where violation ended")
    
    # Metadata
    duration_seconds: Optional[int] = Field(None, description="Violation duration in seconds")
    is_active: bool = Field(default=True, description="Whether violation is currently active")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True


class SpeedViolationType(str, Enum):
    """Speed violation types"""
    SPEED_LIMIT_EXCEEDED = "speed_limit_exceeded"


class SpeedViolation(BaseModel):
    """Speed limit violation during trip"""
    id: Optional[str] = Field(None, alias="_id", description="Violation ID")
    trip_id: str = Field(..., description="Associated trip ID")
    driver_id: str = Field(..., description="Driver ID")
    violation_type: SpeedViolationType = Field(default=SpeedViolationType.SPEED_LIMIT_EXCEEDED)
    
    # Speed data
    actual_speed: float = Field(..., ge=0, description="Actual vehicle speed in km/h")
    speed_limit: float = Field(..., ge=0, description="Posted speed limit in km/h")
    speed_over_limit: float = Field(..., ge=0, description="Speed over limit in km/h")
    
    # Location and time
    location: LocationPoint = Field(..., description="Location where violation occurred")
    timestamp: datetime = Field(..., description="When violation was detected")
    
    # Road information (from Google Roads API)
    place_id: Optional[str] = Field(None, description="Google Maps place ID for road segment")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True


class DriverPingSession(BaseModel):
    """Driver phone ping session tracking"""
    id: Optional[str] = Field(None, alias="_id", description="Session ID")
    trip_id: str = Field(..., description="Associated trip ID")
    driver_id: str = Field(..., description="Driver ID")
    
    # Session status
    is_active: bool = Field(default=True, description="Whether session is currently active")
    started_at: datetime = Field(default_factory=datetime.utcnow, description="When session started")
    ended_at: Optional[datetime] = Field(None, description="When session ended")
    
    # Ping tracking
    last_ping_time: Optional[datetime] = Field(None, description="Last successful ping time")
    last_ping_location: Optional[LocationPoint] = Field(None, description="Last ping location")
    ping_count: int = Field(default=0, description="Total pings received")
    
    # Violation tracking
    current_violation_id: Optional[str] = Field(None, description="ID of current active violation")
    total_violations: int = Field(default=0, description="Total violations in this session")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
