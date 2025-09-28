"""
Entity schemas for Trip Planning service
"""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class RouteBounds(BaseModel):
    """Route bounds information"""
    southWest: Dict[str, float] = Field(..., alias="_southWest", description="Southwest coordinate")
    northEast: Dict[str, float] = Field(..., alias="_northEast", description="Northeast coordinate")
    
    class Config:
        populate_by_name = True


class TurnByTurnInstruction(BaseModel):
    """Turn-by-turn navigation instruction"""
    text: str = Field(..., description="Human-readable instruction text")
    type: Optional[str] = Field(None, description="Maneuver type")
    distance: float = Field(0, description="Distance for this instruction in meters")
    time: float = Field(0, description="Time for this instruction in seconds")
    from_index: Optional[int] = Field(None, description="Starting geometry index")
    to_index: Optional[int] = Field(None, description="Ending geometry index")


class RoadDetail(BaseModel):
    """Detailed information about a road segment"""
    distance: float = Field(0, description="Segment distance in meters")
    time: float = Field(0, description="Segment time in seconds")
    speed_limit: Optional[float] = Field(None, description="Speed limit in km/h")
    road_class: Optional[str] = Field(None, description="Road class (motorway, trunk, primary, etc.)")
    surface: Optional[str] = Field(None, description="Road surface type")
    lane_count: Optional[int] = Field(None, description="Number of lanes")
    name: Optional[str] = Field(None, description="Road name")
    toll: bool = Field(False, description="Whether this segment has tolls")
    ferry: bool = Field(False, description="Whether this segment uses a ferry")
    tunnel: bool = Field(False, description="Whether this segment is a tunnel")
    bridge: bool = Field(False, description="Whether this segment is a bridge")


class DetailedRouteInfo(BaseModel):
    """Comprehensive route information from Geoapify Routing API"""
    # Basic route information
    distance: float = Field(..., description="Route distance in meters")
    duration: float = Field(..., description="Route duration in seconds")
    coordinates: List[List[float]] = Field(..., description="Route coordinates as [lat, lng] pairs")
    
    # Route characteristics
    toll: bool = Field(False, description="Whether the route includes tolls")
    ferry: bool = Field(False, description="Whether the route uses ferries")
    
    # Turn-by-turn navigation
    instructions: List[TurnByTurnInstruction] = Field(default_factory=list, description="Turn-by-turn navigation instructions")
    
    # Detailed road information
    road_details: List[RoadDetail] = Field(default_factory=list, description="Detailed information for each road segment")
    
    # API response metadata
    raw_response: Optional[Dict[str, Any]] = Field(None, description="Original routing API response for reference")
    
    # Timestamp when this route was fetched
    fetched_at: datetime = Field(default_factory=datetime.utcnow, description="When this route information was fetched")


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
    GEOFENCE_ALERT = "geofence_alert"
    DRIVER_ASSIGNED = "driver_assigned"
    DRIVER_UNASSIGNED = "driver_unassigned"

class Notification(BaseModel):
    """User notification"""
    id: Optional[str] = Field(None, alias="_id")
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
    detailed_route_info: Optional[DetailedRouteInfo] = Field(None, description="Comprehensive route information from Geoapify API including turn-by-turn instructions and road details")
    raw_route_response: Optional[Dict[str, Any]] = Field(None, description="Raw response from Geoapify Routing API for complete route data")
    
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

class ScheduledTrip(BaseModel):
    """Scheduled trip entity"""
    id: Optional[str] = Field(None, alias="_id", description="Trip ID")
    name: str = Field(..., description="Trip name/title")
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
    status: TripStatus = Field(default=TripStatus.SCHEDULED)
    estimated_distance: Optional[float] = Field(None, description="Estimated distance in km")
    estimated_duration: Optional[float] = Field(None, description="Estimated duration in minutes")

class ScheduleInfo(BaseModel):
    """Represents schedule information for a trip"""
    start_time: datetime = Field(..., description="Start time of the schedule")
    end_time: datetime = Field(..., description="End time of the schedule")
    vehicle_id: Optional[str] = Field(None, description="Assigned vehicle ID")
    vehicle_name: Optional[str] = Field(None, description="Assigned vehicle name")
    driver_id: Optional[str] = Field(None, description="Assigned driver ID")
    driver_name: Optional[str] = Field(None, description="Assigned driver name")


class RouteSummary(BaseModel):
    """Route summary information for the smart trip"""
    origin: Waypoint = Field(..., description="Starting point")
    destination: Waypoint = Field(..., description="End point")
    waypoints: List[Waypoint] = Field(default_factory=list, description="Intermediate stops")
    estimated_distance: Optional[float] = Field(None, description="Estimated distance in km")
    estimated_duration: Optional[float] = Field(None, description="Estimated duration in minutes")


class SmartTripBenefits(BaseModel):
    """Benefits gained from smart trip optimization"""
    time_saved: str = Field(..., description="Time saved as a formatted string")
    fuel_efficiency: str = Field(..., description="Fuel efficiency information")
    route_optimization: str = Field(..., description="Description of route optimization")
    driver_utilization: str = Field(..., description="Driver utilization efficiency as formatted string")


class SmartTrip(BaseModel):
    """Smart trip entity with optimization details"""
    id: str = Field(..., description="Unique Smart Trip ID")
    trip_id: str = Field(..., description="Reference to ScheduledTrip ID")
    trip_name: str = Field(..., description="Name of the trip")
    description: Optional[str] = None
    priority: TripPriority = Field(..., description="Trip priority")

    original_schedule: ScheduleInfo = Field(..., description="Original schedule details")
    optimized_schedule: ScheduleInfo = Field(..., description="Optimized schedule details")
    route: RouteSummary = Field(..., description="Route information summary")
    benefits: SmartTripBenefits = Field(..., description="Benefits from optimization")
    route_info: Optional[RouteInfo] = Field(None, description="Route information including distance, duration, and coordinates")

    confidence: int = Field(..., description="Confidence score of the optimization")
    reasoning: List[str] = Field(..., description="Reasoning behind optimization decisions")

    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when SmartTrip was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when SmartTrip was last updated")

    class Config:
        populate_by_name = True


class TrafficType(str, Enum):
    """Traffic type enumeration"""
    LIGHT = "light"
    MODERATE = "moderate"
    HEAVY = "heavy"
    SEVERE = "severe"

class RouteRecommendationStatus(str, Enum):
    """Route Rec. Status types"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"

class TrafficCondition(BaseModel):
    """Represents current traffic condition for a route segment"""
    segment_id: str = Field(..., description="Unique identifier for the route segment")
    current_duration: float = Field(..., description="Current travel duration in seconds")
    free_flow_duration: float = Field(..., description="Travel duration in free-flow traffic conditions")
    traffic_ratio: float = Field(..., description="Current / Free flow travel duration ratio")
    severity: TrafficType = Field(..., description="Traffic severity level")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Time when condition was recorded")

    class Config:
        populate_by_name = True


class RouteRecommendation(BaseModel):
    """Represents a route optimization recommendation"""
    id: Optional[str] = Field(None, description="Unique Smart Trip ID")
    trip_name: str= Field(..., description="Associated trip name")
    trip_id: str = Field(..., description="Associated Trip ID")
    vehicle_id: str = Field(..., description="Associated Vehicle ID")
    vehicle_name: str = Field(..., description="Associated Vehicle name")
    emp_id: str = Field(..., description="Driver employee ID")
    current_route: RouteInfo = Field(..., description="Current route information")
    recommended_route: RouteInfo = Field(..., description="Recommended optimized route")
    time_savings: float = Field(..., description="Time saved in seconds if recommendation is accepted")
    traffic_avoided: TrafficType = Field(..., description="Traffic severity avoided with the new route")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score of recommendation")
    reason: str = Field(..., description="Reason for the recommendation")
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


class SpeedViolation(BaseModel):
    """Speed violation record"""
    id: Optional[str] = Field(None, alias="_id", description="Violation ID")
    trip_id: str = Field(..., description="Associated trip ID")
    driver_id: str = Field(..., description="Driver ID")
    
    # Speed data
    speed: float = Field(..., ge=0, description="Vehicle speed in km/h")
    speed_limit: float = Field(..., ge=0, description="Posted speed limit in km/h")
    
    # Location and time
    location: LocationPoint = Field(..., description="Location where violation occurred")
    time: datetime = Field(..., description="When violation occurred")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True


class ExcessiveBrakingViolation(BaseModel):
    """Excessive braking violation record"""
    id: Optional[str] = Field(None, alias="_id", description="Violation ID")
    trip_id: str = Field(..., description="Associated trip ID")
    driver_id: str = Field(..., description="Driver ID")
    
    # Braking data
    deceleration: float = Field(..., description="Deceleration rate in m/s²")
    threshold: float = Field(..., description="Maximum allowed deceleration in m/s²")
    
    # Location and time
    location: LocationPoint = Field(..., description="Location where violation occurred")
    time: datetime = Field(..., description="When violation occurred")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True


class ExcessiveAccelerationViolation(BaseModel):
    """Excessive acceleration violation record"""
    id: Optional[str] = Field(None, alias="_id", description="Violation ID")
    trip_id: str = Field(..., description="Associated trip ID")
    driver_id: str = Field(..., description="Driver ID")
    
    # Acceleration data
    acceleration: float = Field(..., description="Acceleration rate in m/s²")
    threshold: float = Field(..., description="Maximum allowed acceleration in m/s²")
    
    # Location and time
    location: LocationPoint = Field(..., description="Location where violation occurred")
    time: datetime = Field(..., description="When violation occurred")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
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


class RiskLevel(str, Enum):
    """Driver risk level enum"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DriverHistory(BaseModel):
    """Driver performance history and metrics"""
    id: Optional[str] = Field(None, alias="_id", description="History record ID")
    driver_id: str = Field(..., description="Driver ID")
    employee_id: Optional[str] = Field(None, description="Employee ID")
    driver_name: str = Field(..., description="Driver full name")
    
    # Trip statistics
    total_assigned_trips: int = Field(default=0, description="Total number of assigned trips")
    completed_trips: int = Field(default=0, description="Number of trips completed")
    cancelled_trips: int = Field(default=0, description="Number of cancelled trips")
    trip_completion_rate: float = Field(default=0.0, description="Trip completion rate as percentage")
    
    # Violation counts
    braking_violations: int = Field(default=0, description="Number of excessive braking violations")
    acceleration_violations: int = Field(default=0, description="Number of excessive acceleration violations")
    phone_usage_violations: int = Field(default=0, description="Number of phone usage violations")
    speeding_violations: int = Field(default=0, description="Number of speeding violations")
    
    # Safety metrics
    driver_safety_score: float = Field(default=100.0, description="Driver safety score (0-100)")
    driver_risk_level: RiskLevel = Field(default=RiskLevel.LOW, description="Driver risk level")
    
    # Metadata
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Record creation timestamp")
    
    class Config:
        populate_by_name = True


class RiskLevel(str, Enum):
    """Driver risk level enum"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DriverHistory(BaseModel):
    """Driver performance history and metrics"""
    id: Optional[str] = Field(None, alias="_id", description="History record ID")
    driver_id: str = Field(..., description="Driver ID")
    employee_id: Optional[str] = Field(None, description="Employee ID")
    driver_name: str = Field(..., description="Driver full name")
    
    # Trip statistics
    total_assigned_trips: int = Field(default=0, description="Total number of assigned trips")
    completed_trips: int = Field(default=0, description="Number of trips completed")
    cancelled_trips: int = Field(default=0, description="Number of cancelled trips")
    trip_completion_rate: float = Field(default=0.0, description="Trip completion rate as percentage")
    
    # Violation counts
    braking_violations: int = Field(default=0, description="Number of excessive braking violations")
    acceleration_violations: int = Field(default=0, description="Number of excessive acceleration violations")
    phone_usage_violations: int = Field(default=0, description="Number of phone usage violations")
    speeding_violations: int = Field(default=0, description="Number of speeding violations")
    
    # Safety metrics
    driver_safety_score: float = Field(default=100.0, description="Driver safety score (0-100)")
    driver_risk_level: RiskLevel = Field(default=RiskLevel.LOW, description="Driver risk level")
    
    # Metadata
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Record creation timestamp")
    
    class Config:
        populate_by_name = True

class TripCombinationRecommendation(BaseModel):
    """Schema for trip combination recommendations"""
    id: str
    primary_trip_id: str
    secondary_trip_id: str
    primary_trip_name: str
    secondary_trip_name: str
    recommended_driver: str
    recommended_vehicle: str
    combined_route: Optional[RouteInfo]
    travel_distance_km: float
    time_gap_hours: float
    benefits: Dict[str, Any]
    confidence_score: float  # 0-1
    reasoning: List[str]
    created_at: datetime
    expires_at: datetime
    
    class Config:
        from_attributes = True

class Savings(BaseModel):
    time_minutes: float
    distance_km: float
    cost: str

class CombinationInfo(BaseModel):
    is_combined: bool
    original_primary_trip: str
    original_secondary_trip: str
    recommendation_id: str
    combined_at: datetime
    savings: Savings

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

class GeofenceProperties(BaseModel):
    radius: float

class GeofenceGeometry(BaseModel):
    type: GeofenceType = Field(..., description="Type of geofence geometry")
    coordinates: List[Any] = Field(..., description="GeoJSON coordinates")
    radius: Optional[int] = Field(None, ge=1, description="Radius for circle type")
    properties: Optional[GeofenceProperties] = None
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