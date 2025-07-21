"""
API Dependencies for Maintenance Service
Authentication, authorization, and common utilities
"""

import os
import uuid
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from functools import wraps

from fastapi import HTTPException, Request, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import logging

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()

# Authentication configuration
SECURITY_SERVICE_URL = os.getenv("SECURITY_SERVICE_URL", "http://localhost:8000")
SECURITY_SERVICE_TIMEOUT = int(os.getenv("SECURITY_SERVICE_TIMEOUT", "10"))

class AuthenticationError(Exception):
    """Custom authentication error"""
    pass

class AuthorizationError(Exception):
    """Custom authorization error"""
    pass

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Get current user from Security service
    Validates JWT token and returns user information
    """
    try:
        async with httpx.AsyncClient(timeout=SECURITY_SERVICE_TIMEOUT) as client:
            response = await client.get(
                f"{SECURITY_SERVICE_URL}/auth/validate",
                headers={"Authorization": f"Bearer {credentials.credentials}"}
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid or expired token"
                )
            else:
                raise HTTPException(
                    status_code=403,
                    detail="Authentication service error"
                )
                
    except httpx.RequestError as e:
        logger.error(f"Authentication service connection error: {e}")
        raise AuthenticationError("Authentication service unavailable")
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")

# Alias for consistency with route imports
get_authenticated_user = get_current_user

def require_permission(permission: str):
    """
    Decorator factory for requiring specific permissions
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user from kwargs (should be injected by Depends)
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            # Check if user has required permission
            user_permissions = current_user.get('permissions', [])
            if permission not in user_permissions:
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied: {permission} required"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    
    # Return dependency function
    async def permission_dependency(current_user: Dict[str, Any] = Depends(get_current_user)):
        user_permissions = current_user.get('permissions', [])
        if permission not in user_permissions:
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: {permission} required"
            )
        return current_user
    
    return permission_dependency

def require_permissions(permissions: list):
    """
    Decorator factory for requiring multiple permissions (any one of them)
    """
    async def permission_dependency(current_user: Dict[str, Any] = Depends(get_current_user)):
        user_permissions = current_user.get('permissions', [])
        has_permission = any(perm in user_permissions for perm in permissions)
        if not has_permission:
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: One of {permissions} required"
            )
        return None  # Return None as expected by routes
    
    return permission_dependency

class PaginationParams:
    """Pagination parameters"""
    def __init__(self, page: int = 1, page_size: int = 50):
        self.page = max(1, page)
        self.page_size = min(100, max(1, page_size))
        self.skip = (self.page - 1) * self.page_size
        self.limit = self.page_size

async def get_pagination_params(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page")
) -> PaginationParams:
    """Get pagination parameters with validation"""
    return PaginationParams(page=page, page_size=page_size)

def validate_object_id(object_id: str, field_name: str = "ID"):
    """Validate ObjectId format"""
    if not object_id:
        raise ValueError(f"{field_name} is required")
    
    if len(object_id) != 24:
        raise ValueError(f"Invalid {field_name} format")
    
    try:
        int(object_id, 16)
    except ValueError:
        raise ValueError(f"Invalid {field_name} format")

async def get_request_id(request: Request) -> str:
    """Get or generate request ID"""
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())
    return request_id

class RequestTimer:
    """Context manager for timing requests"""
    def __init__(self):
        self.start_time = None
        self.execution_time_ms = None
        self.request_id = str(uuid.uuid4())
    
    def __enter__(self):
        self.start_time = datetime.now(timezone.utc)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            end_time = datetime.now(timezone.utc)
            self.execution_time_ms = int((end_time - self.start_time).total_seconds() * 1000)
    
    @property
    def elapsed(self):
        """Get elapsed time in milliseconds"""
        if self.start_time:
            current_time = datetime.now(timezone.utc)
            return int((current_time - self.start_time).total_seconds() * 1000)
        return 0

async def get_request_timer() -> RequestTimer:
    """Get a request timer instance"""
    timer = RequestTimer()
    timer.__enter__()
    return timer

async def get_user_context(request: Request) -> Dict[str, Any]:
    """Get user context from request"""
    try:
        # Try to get authenticated user
        try:
            credentials = await security(request)
            current_user = await get_current_user(credentials)
            return {
                "user_id": current_user.get("user_id"),
                "username": current_user.get("username"),
                "permissions": current_user.get("permissions", []),
                "authenticated": True
            }
        except:
            # Return anonymous context if authentication fails
            return {
                "user_id": None,
                "username": "anonymous",
                "permissions": [],
                "authenticated": False
            }
    except Exception as e:
        logger.error(f"Error getting user context: {e}")
        return {
            "user_id": None,
            "username": "anonymous",
            "permissions": [],
            "authenticated": False
        }

def validate_date_range(start_date: Optional[str], end_date: Optional[str]):
    """Validate date range parameters"""
    if start_date and end_date:
        try:
            start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            if start >= end:
                raise ValueError("Start date must be before end date")
        except ValueError as e:
            if "Start date must be before end date" in str(e):
                raise
            raise ValueError("Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)")
