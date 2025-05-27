"""Routes package initialization"""

from fastapi import APIRouter
from .trips import router as trips_router
from .vehicles import router as vehicles_router
from .drivers import router as drivers_router
from .routes import router as routes_router
from .schedules import router as schedules_router

# Create main API router
api_router = APIRouter()

# Include all route modules
api_router.include_router(trips_router, prefix="/trips", tags=["trips"])
api_router.include_router(vehicles_router, prefix="/vehicles", tags=["vehicles"])
api_router.include_router(drivers_router, prefix="/drivers", tags=["drivers"])
api_router.include_router(routes_router, prefix="/routes", tags=["routes"])
api_router.include_router(schedules_router, prefix="/schedules", tags=["schedules"])

__all__ = ["api_router"]
