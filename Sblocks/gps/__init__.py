# Import commonly used submodules or symbols
from gps.api import geofence_routes, location_routes, route_routes, websocket_routes
from gps.config import settings
from gps.services import geofence_service, location_service, route_service

# Define what is accessible when importing `gps`
__all__ = [
    "geofence_routes",
    "location_routes",
    "route_routes",
    "websocket_routes",
    "settings",
    "geofence_service",
    "location_service",
    "route_service",
]