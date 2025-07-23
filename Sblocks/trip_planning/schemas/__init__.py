"""
Schema package initialization
"""
from .entities import (
    Trip, TripStatus, TripPriority, TripConstraint, ConstraintType,
    DriverAssignment, TripAnalytics, Notification, NotificationType,
    NotificationPreferences, LocationPoint, Address, Waypoint
)

from .requests import (
    CreateTripRequest, UpdateTripRequest, TripFilterRequest,
    AssignDriverRequest, CreateConstraintRequest, UpdateConstraintRequest,
    RouteOptimizationRequest, AnalyticsRequest, NotificationRequest,
    UpdateNotificationPreferencesRequest, DriverAvailabilityRequest,
    TripProgressRequest
)

from .responses import (
    ResponseBuilder, TripResponse, TripListResponse, DriverAvailabilityResponse,
    RouteOptimizationResponse, TripAnalyticsResponse, DriverPerformanceResponse,
    NotificationResponse, NotificationListResponse, ConstraintResponse,
    AssignmentResponse, HealthResponse
)

__all__ = [
    # Entities
    "Trip", "TripStatus", "TripPriority", "TripConstraint", "ConstraintType",
    "DriverAssignment", "TripAnalytics", "Notification", "NotificationType",
    "NotificationPreferences", "LocationPoint", "Address", "Waypoint",
    
    # Requests
    "CreateTripRequest", "UpdateTripRequest", "TripFilterRequest",
    "AssignDriverRequest", "CreateConstraintRequest", "UpdateConstraintRequest",
    "RouteOptimizationRequest", "AnalyticsRequest", "NotificationRequest",
    "UpdateNotificationPreferencesRequest", "DriverAvailabilityRequest",
    "TripProgressRequest",
    
    # Responses
    "ResponseBuilder", "TripResponse", "TripListResponse", "DriverAvailabilityResponse",
    "RouteOptimizationResponse", "TripAnalyticsResponse", "DriverPerformanceResponse",
    "NotificationResponse", "NotificationListResponse", "ConstraintResponse",
    "AssignmentResponse", "HealthResponse"
]
