"""
API dependencies for GPS service
"""
import logging
import time
import uuid
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

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
            "permissions": ["gps:read", "gps:write"],
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


async def get_optional_user(request: Request) -> Optional[Dict[str, Any]]:
    """Get user information if authentication header is present"""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=auth_header.split(" ")[1]
        )
        
        return await get_current_user(credentials)
    except:
        return None
