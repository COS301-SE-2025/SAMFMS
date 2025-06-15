# Import all routers for easy access
from .auth_routes import router as auth_router
from .user_routes import router as user_router  
from .admin_routes import router as admin_router

# Export all routers
__all__ = [
    "auth_router",
    "user_router", 
    "admin_router"
]