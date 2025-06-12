import logging
import requests
import os
from typing import Optional, List, Dict, Any
from functools import wraps
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
import jwt

logger = logging.getLogger(__name__)

# Configuration
SECURITY_SERVICE_URL = os.getenv("SECURITY_SERVICE_URL", "http://security_service:8001")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
JWT_ALGORITHM = "HS256"

class AuthenticationError(Exception):
    """Custom exception for authentication errors"""
    pass

class AuthorizationError(Exception):
    """Custom exception for authorization errors"""
    pass

def verify_token_with_security_service(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify token with Security Sblock service
    Returns user data if token is valid, None otherwise
    """
    try:
        response = requests.post(
            f"{SECURITY_SERVICE_URL}/api/v1/auth/verify-token",
            json={"token": token},
            timeout=5
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.warning(f"Token verification failed: {response.status_code}")
            return None
            
    except requests.RequestException as e:
        logger.error(f"Failed to verify token with security service: {e}")
        return None

def verify_token_locally(token: str) -> Optional[Dict[str, Any]]:
    """
    Fallback local token verification
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None

def get_current_user(credentials: HTTPAuthorizationCredentials) -> Dict[str, Any]:
    """
    Extract and verify user from JWT token
    First tries Security service, falls back to local verification
    """
    token = credentials.credentials
    
    # Try Security service first
    user_data = verify_token_with_security_service(token)
    
    # Fallback to local verification
    if not user_data:
        user_data = verify_token_locally(token)
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user_data

def check_permission_with_security_service(token: str, permission: str) -> bool:
    """
    Check if user has specific permission via Security service
    """
    try:
        response = requests.post(
            f"{SECURITY_SERVICE_URL}/api/v1/auth/verify-permission",
            json={"token": token, "permission": permission},
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("has_permission", False)
        else:
            logger.warning(f"Permission check failed: {response.status_code}")
            return False
            
    except requests.RequestException as e:
        logger.error(f"Failed to check permission with security service: {e}")
        return False

def check_permission_locally(user_data: Dict[str, Any], permission: str) -> bool:
    """
    Local fallback permission checking
    """
    user_permissions = user_data.get("permissions", [])
    user_role = user_data.get("role", "")
    
    # Check direct permission
    if permission in user_permissions:
        return True
    
    # Check wildcard permissions
    for perm in user_permissions:
        if perm.endswith("*"):
            prefix = perm[:-1]
            if permission.startswith(prefix):
                return True
    
    # Role-based permissions
    role_permissions = {
        "admin": ["*"],  # Admin has all permissions
        "fleet_manager": [
            "vehicles:*", "drivers:*", "assignments:*", 
            "analytics:read", "reports:*"
        ],
        "driver": [
            "vehicles:read_own", "assignments:read_own", 
            "usage:create", "status:create"
        ]
    }
    
    if user_role in role_permissions:
        for role_perm in role_permissions[user_role]:
            if role_perm == "*" or role_perm == permission:
                return True
            if role_perm.endswith("*"):
                prefix = role_perm[:-1]
                if permission.startswith(prefix):
                    return True
    
    return False

def has_permission(user_data: Dict[str, Any], permission: str, token: str = None) -> bool:
    """
    Check if user has specific permission
    First tries Security service, falls back to local checking
    """
    # Try Security service first if token is available
    if token:
        has_perm = check_permission_with_security_service(token, permission)
        if has_perm:
            return True
    
    # Fallback to local checking
    return check_permission_locally(user_data, permission)

def require_permission(permission: str):
    """
    Decorator to require specific permission for route access
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract credentials from kwargs
            credentials = None
            for key, value in kwargs.items():
                if isinstance(value, HTTPAuthorizationCredentials):
                    credentials = value
                    break
            
            if not credentials:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            try:
                user_data = get_current_user(credentials)
                token = credentials.credentials
                
                if not has_permission(user_data, permission, token):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission '{permission}' required"
                    )
                
                # Add user data to kwargs for use in route handler
                kwargs['current_user'] = user_data
                return await func(*args, **kwargs)
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error in permission check: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Authentication error"
                )
        
        return wrapper
    return decorator

def require_role(required_role: str):
    """
    Decorator to require specific role for route access
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract credentials from kwargs
            credentials = None
            for key, value in kwargs.items():
                if isinstance(value, HTTPAuthorizationCredentials):
                    credentials = value
                    break
            
            if not credentials:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            try:
                user_data = get_current_user(credentials)
                user_role = user_data.get("role", "")
                
                if user_role != required_role and user_role != "admin":
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Role '{required_role}' required"
                    )
                
                # Add user data to kwargs for use in route handler
                kwargs['current_user'] = user_data
                return await func(*args, **kwargs)
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error in role check: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Authentication error"
                )
        
        return wrapper
    return decorator

def filter_data_by_role(data: List[Dict[str, Any]], user_data: Dict[str, Any], resource_type: str) -> List[Dict[str, Any]]:
    """
    Filter data based on user role and permissions
    """
    user_role = user_data.get("role", "")
    user_id = user_data.get("user_id")
    
    # Admin and fleet_manager can see all data
    if user_role in ["admin", "fleet_manager"]:
        return data
    
    # Driver can only see their own data
    if user_role == "driver":
        if resource_type == "drivers":
            return [item for item in data if item.get("user_id") == user_id]
        elif resource_type == "assignments":
            return [item for item in data if item.get("user_id") == user_id]
        elif resource_type == "usage":
            return [item for item in data if item.get("user_id") == user_id]
    
    return []

def can_access_resource(user_data: Dict[str, Any], resource_owner_id: str) -> bool:
    """
    Check if user can access a specific resource based on ownership
    """
    user_role = user_data.get("role", "")
    user_id = user_data.get("user_id")
    
    # Admin and fleet_manager can access all resources
    if user_role in ["admin", "fleet_manager"]:
        return True
    
    # Driver can only access their own resources
    if user_role == "driver":
        return user_id == resource_owner_id
    
    return False
