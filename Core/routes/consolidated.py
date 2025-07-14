"""
Consolidated API Router
Replaces the large service_proxy.py with organized, smaller route modules
"""

from fastapi import APIRouter
from .api import api_router

# Create the main consolidated router without any prefix
consolidated_router = APIRouter()

# Include the organized API routes (includes debug via api_router)
consolidated_router.include_router(api_router)

__all__ = ["consolidated_router"]
