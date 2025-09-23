"""
API dependencies and utilities
"""
import logging
import time
import uuid
from fastapi import HTTPException, Depends, Header, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any

from schemas.entities import Trip
from services.trip_service import trip_service

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()


class RequestTimer:
    """Context manager for timing requests"""
    
    def __init__(self):
        self.start_time = None
        self.execution_time_ms = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            self.execution_time_ms = (time.time() - self.start_time) * 1000


async def get_request_id(request: Request) -> str:
    """Get or generate request ID for tracing"""
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())
    return request_id


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Extract user information from JWT token
    This is a simplified version - in production, you'd validate the JWT properly
    """
    try:
        # In a real implementation, you would:
        # 1. Decode and validate the JWT token
        # 2. Extract user information
        # 3. Check token expiration
        # 4. Verify token signature
        
        # For now, return a mock user (replace with actual JWT validation)
        mock_user = {
            "user_id": "user123",
            "username": "testuser",
            "email": "test@example.com",
            "permissions": ["trips:read", "trips:write", "trips:ping"],
            "is_admin": False
        }
        
        return mock_user
        
    except Exception as e:
        logger.error(f"Error validating token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_permission(permission: str):
    """Dependency to check if user has required permission"""
    async def check_permission(current_user: Dict[str, Any] = Depends(get_current_user)):
        user_permissions = current_user.get("permissions", [])
        
        # Check if user has the required permission or is admin
        if permission not in user_permissions and not current_user.get("is_admin", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission}"
            )
        
        return current_user
    
    return check_permission


async def get_current_user_legacy(authorization: Optional[str] = Header(None)) -> str:
    """Legacy function - Extract current user from authorization header"""
    # This would integrate with actual authentication service
    # For now, return a mock user
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    # Mock user extraction
    if authorization.startswith("Bearer "):
        token = authorization[7:]
        # Would validate token here
        return "user_123"  # Mock user ID
    
    raise HTTPException(status_code=401, detail="Invalid authorization format")


async def get_current_user_id(current_user: Dict[str, Any] = Depends(get_current_user)) -> str:
    """Helper function to get just the user ID for backward compatibility"""
    return current_user.get("user_id")


async def get_current_user_secure(authorization: Optional[str] = Header(None)) -> dict:
    """Extract current user from authorization header and return user context"""
    # This would integrate with actual authentication service
    # For now, return a mock user context
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    # Mock user extraction
    if authorization.startswith("Bearer "):
        token = authorization[7:]
        # Would validate token here and get user details
        return {
            "user_id": "user_123",
            "role": "driver",  # Could be driver, admin, fleet_manager
            "permissions": ["read:notifications", "write:notifications"]
        }
    
    raise HTTPException(status_code=401, detail="Invalid authorization format")


async def validate_trip_access(trip_id: str, current_user: Dict[str, Any] = Depends(get_current_user)) -> Trip:
    """Validate that user has access to the trip"""
    trip = await trip_service.get_trip_by_id(trip_id)
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Check if user has access to this trip
    # This would implement proper access control
    # For now, allow access if user is creator or assigned driver
    user_id = current_user.get("user_id")
    if (trip.created_by != user_id and 
        (not trip.driver_assignment or trip.driver_assignment != user_id)):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return trip


def get_pagination_params(skip: int = 0, limit: int = 50) -> dict:
    """Get pagination parameters with validation"""
    if skip < 0:
        raise HTTPException(status_code=400, detail="Skip must be non-negative")
    
    if limit < 1 or limit > 1000:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 1000")
    
    return {"skip": skip, "limit": limit}
