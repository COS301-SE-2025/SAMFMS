"""
GPS API Package

Contains all API routes for the GPS tracking system.
"""

from .location_routes import router as location_router
from .geofence_routes import router as geofence_router
from .route_routes import router as route_router
from .websocket_routes import router as websocket_router

__all__ = [
    "location_router",
    "geofence_router",
    "route_router",
    "websocket_router"
]
