"""
API dependencies and common utilities
"""
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)
security = HTTPBearer()


# Temporary auth dependency - to be replaced with proper Security service integration
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current user from token - placeholder implementation"""
    # TODO: Integrate with Security service via events
    return {
        "user_id": "temp_user",
        "role": "admin",
        "permissions": ["*"]
    }


def require_permission(permission: str):
    """Decorator to require specific permission"""
    def dependency(current_user: Dict[str, Any] = Depends(get_current_user)):
        # TODO: Implement proper permission checking
        if current_user.get("role") != "admin" and permission not in current_user.get("permissions", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission}"
            )
        return current_user
    return dependency


async def get_pagination_params(skip: int = 0, limit: int = 100) -> Dict[str, int]:
    """Get pagination parameters"""
    if skip < 0:
        skip = 0
    if limit <= 0 or limit > 1000:
        limit = 100
    
    return {"skip": skip, "limit": limit}


def validate_object_id(obj_id: str, field_name: str = "ID") -> str:
    """Validate ObjectId format"""
    from bson import ObjectId
    
    if not ObjectId.is_valid(obj_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field_name} format: {obj_id}"
        )
    
    return obj_id
