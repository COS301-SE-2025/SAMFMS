"""
Enhanced API dependencies with proper authentication and utilities
"""
from fastapi import HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional, List
import logging
import time
import uuid
from datetime import datetime

from schemas.responses import ResponseBuilder, ErrorResponse

logger = logging.getLogger(__name__)
security = HTTPBearer()


class AuthenticationError(Exception):
    """Custom authentication error"""
    pass


class AuthorizationError(Exception):
    """Custom authorization error"""
    pass


async def get_request_id(request: Request) -> str:
    """Generate or extract request ID for tracing"""
    request_id = request.headers.get("x-request-id")
    if not request_id:
        request_id = str(uuid.uuid4())
    return request_id


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    request: Request = None
) -> Dict[str, Any]:
    """Get current user from token with enhanced validation"""
    try:
        import aiohttp
        import os
        
        token = credentials.credentials
        
        # Basic token validation
        if not token or len(token) < 10:
            raise AuthenticationError("Invalid token format")
        
        # Call Security service to validate token
        security_service_url = os.getenv("SECURITY_SERVICE_URL", "http://security:8000")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{security_service_url}/auth/verify-token",
                    json={"token": token},
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        user_data = await response.json()
                        return user_data
                    else:
                        raise AuthenticationError("Invalid token")
        except aiohttp.ClientError as e:
            logger.warning(f"Security service unavailable: {e}")
            # Fallback to basic validation for development
            if os.getenv("ENVIRONMENT") == "development":
                return {
                    "user_id": "dev_user",
                    "email": "dev@example.com",
                    "role": "admin",
                    "permissions": ["*"]
                }
            raise AuthenticationError("Authentication service unavailable")
            
    except AuthenticationError:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise AuthenticationError("Authentication failed")
        
        # Mock user data - replace with actual token decoding
        if token == "admin_token":
            return {
                "user_id": "admin_user",
                "email": "admin@samfms.com",
                "role": "admin",
                "permissions": ["*"],
                "department": "admin"
            }
        elif token == "manager_token":
            return {
                "user_id": "manager_user",
                "email": "manager@samfms.com", 
                "role": "manager",
                "permissions": [
                    "analytics:read", "assignments:read", "assignments:create",
                    "assignments:update", "drivers:read", "drivers:create"
                ],
                "department": "operations"
            }
        elif token == "driver_token":
            return {
                "user_id": "driver_user",
                "email": "driver@samfms.com",
                "role": "driver", 
                "permissions": ["assignments:read", "drivers:read"],
                "department": "operations"
            }
        else:
            # For development - create a basic user
            return {
                "user_id": f"user_{token[:8]}",
                "email": f"user@samfms.com",
                "role": "user",
                "permissions": ["analytics:read"],
                "department": "general"
            }
            
    except AuthenticationError:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise AuthenticationError("Token validation failed")


def require_permission(permission: str):
    """Decorator to require specific permission with detailed checking"""
    def dependency(current_user: Dict[str, Any] = Depends(get_current_user)):
        try:
            user_permissions = current_user.get("permissions", [])
            user_role = current_user.get("role", "")
            
            # Admin users have all permissions
            if "*" in user_permissions or user_role == "admin":
                return current_user
            
            # Check specific permission
            if permission not in user_permissions:
                logger.warning(
                    f"User {current_user.get('user_id')} denied access to {permission}. "
                    f"User permissions: {user_permissions}"
                )
                raise AuthorizationError(f"Insufficient permissions: {permission} required")
            
            return current_user
            
        except AuthorizationError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission} Current permissions: {current_user.get('permissions', [])}"
            )
        except Exception as e:
            logger.error(f"Authorization error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authorization check failed"
            )
    
    return dependency


def require_roles(allowed_roles: List[str]):
    """Decorator to require specific roles"""
    def dependency(current_user: Dict[str, Any] = Depends(get_current_user)):
        user_role = current_user.get("role", "")
        
        if user_role not in allowed_roles and "admin" not in allowed_roles:
            logger.warning(
                f"User {current_user.get('user_id')} with role {user_role} "
                f"denied access. Required roles: {allowed_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: one of {allowed_roles}"
            )
        
        return current_user
    
    return dependency


async def get_pagination_params(
    skip: int = 0, 
    limit: int = 100,
    page: Optional[int] = None,
    page_size: Optional[int] = None
) -> Dict[str, int]:
    """Get pagination parameters with validation"""
    # Support both skip/limit and page/page_size patterns
    if page is not None and page_size is not None:
        if page < 1:
            page = 1
        if page_size <= 0 or page_size > 1000:
            page_size = 100
        
        skip = (page - 1) * page_size
        limit = page_size
    else:
        # Traditional skip/limit
        if skip < 0:
            skip = 0
        if limit <= 0 or limit > 1000:
            limit = 100
        
        page = (skip // limit) + 1
        page_size = limit
    
    return {
        "skip": skip,
        "limit": limit,
        "page": page,
        "page_size": page_size
    }


def validate_object_id(obj_id: str, field_name: str = "ID") -> str:
    """Validate ObjectId format with detailed error"""
    from bson import ObjectId
    from bson.errors import InvalidId
    
    try:
        if not obj_id:
            raise ValueError(f"{field_name} cannot be empty")
        
        if not ObjectId.is_valid(obj_id):
            raise ValueError(f"Invalid {field_name} format: {obj_id}")
        
        return obj_id
        
    except (ValueError, InvalidId) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


def validate_date_range(start_date: Optional[datetime], end_date: Optional[datetime]):
    """Validate date range parameters"""
    if start_date and end_date:
        if start_date >= end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date must be before end date"
            )
    
    return start_date, end_date


class RequestTimer:
    """Context manager for tracking request execution time"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
    
    @property
    def execution_time_ms(self) -> float:
        """Get execution time in milliseconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0.0


async def get_user_context(request: Request) -> Dict[str, Any]:
    """Get comprehensive user context for logging and auditing"""
    try:
        # Extract user information (if authenticated)
        user_info = {}
        if hasattr(request.state, 'user'):
            user_info = request.state.user
        
        # Extract request metadata
        context = {
            "request_id": await get_request_id(request),
            "method": request.method,
            "url": str(request.url),
            "user_agent": request.headers.get("user-agent"),
            "client_ip": request.client.host if request.client else None,
            "timestamp": datetime.utcnow().isoformat(),
            "user_info": user_info
        }
        
        return context
        
    except Exception as e:
        logger.error(f"Failed to build user context: {e}")
        return {
            "request_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "error": "context_build_failed"
        }
