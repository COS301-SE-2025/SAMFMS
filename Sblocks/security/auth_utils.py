from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Dict, Optional
import os

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Role definitions and permissions
ROLES = {
    "admin": {
        "name": "Administrator",
        "permissions": ["*"],  # Full access to everything
        "description": "Full system access and user management"
    },
    "fleet_manager": {
        "name": "Fleet Manager", 
        "permissions": [
            "vehicles:read", "vehicles:write", "vehicles:delete",
            "drivers:read", "drivers:write", "drivers:delete",
            "maintenance:read", "maintenance:write",
            "assignments:read", "assignments:write", "assignments:delete",
            "reports:read", "analytics:read"
        ],
        "description": "Manage vehicles, drivers, and fleet operations"
    },
    "driver": {
        "name": "Driver",
        "permissions": [
            "vehicles:read_assigned", "profile:read", "profile:write",
            "trips:read_own", "trips:write_own", "maintenance:read_assigned"
        ],
        "description": "Access to assigned vehicles and personal information"
    }
}

# Default role assignments - first user becomes admin
DEFAULT_FIRST_USER_ROLE = "admin"
DEFAULT_USER_ROLE = None  # No default role - must be assigned by admin/fleet_manager


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Create a JWT access token with user role and permissions"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str) -> dict:
    """Verify and decode a JWT access token with role information"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        role: str = payload.get("role")
        permissions: List[str] = payload.get("permissions", [])
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return {
            "user_id": user_id,
            "role": role,
            "permissions": permissions
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials", 
            headers={"WWW-Authenticate": "Bearer"},
        )


def has_permission(user_permissions: List[str], required_permission: str) -> bool:
    """Check if user has the required permission"""
    # Admin has all permissions
    if "*" in user_permissions:
        return True
    
    # Check exact permission match
    if required_permission in user_permissions:
        return True
    
    # Check wildcard permissions (e.g., "vehicles:*" matches "vehicles:read")
    for permission in user_permissions:
        if permission.endswith(":*"):
            permission_base = permission[:-2]
            if required_permission.startswith(permission_base + ":"):
                return True
    
    return False


def require_permission(permission: str):
    """Decorator to require specific permission for endpoint access"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract credentials from kwargs (FastAPI dependency injection)
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
            
            # Verify token and check permissions
            user_info = verify_access_token(credentials.credentials)
            if not has_permission(user_info["permissions"], permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required: {permission}"
                )
            
            # Add user info to kwargs for use in endpoint
            kwargs["current_user"] = user_info
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_role(allowed_roles: List[str]):
    """Decorator to require specific roles for endpoint access"""
    def decorator(func):
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
            
            # Verify token and check role
            user_info = verify_access_token(credentials.credentials)
            if user_info["role"] not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient role. Required: {', '.join(allowed_roles)}"
                )
            
            # Add user info to kwargs for use in endpoint
            kwargs["current_user"] = user_info
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get current user from JWT token with role and permissions"""
    return verify_access_token(credentials.credentials)


def get_role_permissions(role: str, custom_permissions: Optional[List[str]] = None) -> List[str]:
    """Get permissions for a role, with optional custom permissions override"""
    if custom_permissions:
        return custom_permissions
    
    return ROLES.get(role, {}).get("permissions", [])


async def check_first_user() -> bool:
    """Check if this is the first user in the system (who should become admin)"""
    # This will be implemented in the routes file with database access
    pass
