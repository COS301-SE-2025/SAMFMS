from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from bson import ObjectId
from database import db
from typing import List, Optional
import jwt
import bcrypt
import requests
import os
from datetime import datetime, timedelta

# JWT Configuration - should match Security Sblock
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Security Sblock service URL
SECURITY_SERVICE_URL = os.getenv("SECURITY_SERVICE_URL", "http://security_service:8001")

security = HTTPBearer()
users_collection = db.users


def verify_token_with_security_service(token: str) -> dict:
    """Verify token with Security Sblock service"""
    try:
        response = requests.post(
            f"{SECURITY_SERVICE_URL}/auth/verify-token",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    except requests.RequestException:
        # Fallback to local token verification if Security service is unavailable
        return verify_token_locally(token)


def verify_token_locally(token: str) -> dict:
    """Local token verification as fallback"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        role: str = payload.get("role")
        permissions: List[str] = payload.get("permissions", [])
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        return {
            "user_id": user_id,
            "role": role,
            "permissions": permissions,
            "valid": True
        }
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


def check_permission(user_permissions: List[str], required_permission: str) -> bool:
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
            
            # Verify token and check permissions
            user_info = verify_token_with_security_service(credentials.credentials)
            if not check_permission(user_info.get("permissions", []), permission):
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
            user_info = verify_token_with_security_service(credentials.credentials)
            if user_info.get("role") not in allowed_roles:
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
    """Get current user with role and permissions from Security service"""
    return verify_token_with_security_service(credentials.credentials)


async def get_current_active_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get current active user with role and permissions"""
    user_info = verify_token_with_security_service(credentials.credentials)
    
    # The Security service already validates if the user is active
    # But we can add additional checks here if needed
    return user_info
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: dict = Depends(get_current_user)):
    """Get current active user."""
    # Add any additional checks here if needed (e.g., user is active)
    return current_user


async def authenticate_user(email: str, password: str):
    """Authenticate a user by email and password."""
    user = await users_collection.find_one({"email": email})
    if not user:
        return False
    if not verify_password(password, user["password"]):
        return False
    return user
