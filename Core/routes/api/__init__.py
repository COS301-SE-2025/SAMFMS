"""
API Routes Package
Organizes remaining API routes for development/debugging purposes
Note: Core service now uses simplified service routing via RabbitMQ
"""

from fastapi import APIRouter
from .vehicles import router as vehicles_router
from .drivers import router as drivers_router
from .analytics import router as analytics_router
from .debug import router as debug_router

# Create main API router without prefix since individual routers have /api prefix
api_router = APIRouter()

# Include remaining route modules (mainly for development/debugging)
api_router.include_router(vehicles_router)
api_router.include_router(drivers_router)
api_router.include_router(analytics_router)
api_router.include_router(debug_router)

__all__ = ["api_router"]
