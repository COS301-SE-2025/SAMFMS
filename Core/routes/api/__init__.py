"""
API Routes Package
Organizes all API routes in separate modules for better maintainability
"""

from fastapi import APIRouter
from .vehicles import router as vehicles_router
from .drivers import router as drivers_router
from .assignments import router as assignments_router
from .gps import router as gps_router
from .analytics import router as analytics_router
from .trips import router as trips_router
from .maintenance import router as maintenance_router

# Create main API router
api_router = APIRouter()

# Include all route modules
api_router.include_router(vehicles_router)
api_router.include_router(drivers_router)
api_router.include_router(assignments_router)
api_router.include_router(gps_router)
api_router.include_router(analytics_router)
api_router.include_router(trips_router)
api_router.include_router(maintenance_router)

__all__ = ["api_router"]
