"""
Routes package for SAMFMS Utilities
"""
from fastapi import APIRouter
from routes.email_routes import router as email_router

# Create main API router
api_router = APIRouter()

# Include all routers
api_router.include_router(email_router)

__all__ = ["api_router"]
