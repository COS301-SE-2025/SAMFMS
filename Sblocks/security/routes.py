# Backward compatibility - redirect to new structure
# This file provides backward compatibility for existing imports

from routes.auth_routes import router as auth_router
from routes.user_routes import router as user_router  
from routes.admin_routes import router as admin_router

# Create main router that includes all sub-routers
from fastapi import APIRouter

router = APIRouter()

# Include all route modules
router.include_router(auth_router)
router.include_router(user_router)
router.include_router(admin_router)

# Keep router export for backward compatibility
__all__ = ["router"]
