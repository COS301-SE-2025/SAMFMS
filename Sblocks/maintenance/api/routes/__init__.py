"""
API Routes Package for Maintenance Service
"""

from .maintenance_records import router as maintenance_records_router
from .licenses import router as licenses_router
from .analytics import router as analytics_router
from .notifications import router as notifications_router

__all__ = [
    "maintenance_records_router",
    "licenses_router",
    "analytics_router", 
    "notifications_router",
]
