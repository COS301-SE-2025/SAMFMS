"""
Models package initialization
"""
from models.location import (
    VehicleLocation,
    LocationHistory,
    LocationUpdate,
    LocationQuery,
    LocationResponse,
    HistoryResponse,
    GPSCoordinates,
    Coordinate
)
from models.geofence import (
    Geofence,
    GeofenceEvent,
    GeofenceCreate,
    GeofenceUpdate,
    GeofenceQuery,
    GeofenceResponse,
    GeofenceEventQuery,
    GeofenceEventResponse,
    GeofenceCoordinates,
    GeofenceType
)
from models.route import (
    VehicleRoute,
    RouteSegment,
    PlannedRoute,
    RouteCreate,
    PlannedRouteCreate,
    RouteQuery,
    RouteResponse,
    PlannedRouteResponse,
    RouteAnalytics,
    RoutePoint
)

__all__ = [
    # Location models
    "VehicleLocation",
    "LocationHistory", 
    "LocationUpdate",
    "LocationQuery",
    "LocationResponse",
    "HistoryResponse",
    "GPSCoordinates",
    
    # Geofence models
    "Geofence",
    "GeofenceEvent",
    "GeofenceCreate",
    "GeofenceUpdate",
    "GeofenceQuery", 
    "GeofenceResponse",
    "GeofenceEventQuery",
    "GeofenceEventResponse",
    "GeofenceCoordinates",
    
    # Route models
    "VehicleRoute",
    "RouteSegment",
    "PlannedRoute",
    "RouteCreate",
    "PlannedRouteCreate",
    "RouteQuery",
    "RouteResponse",
    "PlannedRouteResponse",
    "RouteAnalytics",
    "RoutePoint"
]
