"""
GPS API Package

Contains all API routes for the GPS tracking system.
"""

from api.location_routes import router as location_router
from api.geofence_routes import router as geofence_router
from api.route_routes import router as route_router
from api.websocket_routes import router as websocket_router

__all__ = [
    "location_router",
    "geofence_router",
    "route_router",
    "websocket_router"
]
