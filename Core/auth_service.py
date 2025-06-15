"""
Authentication service for Core
Handles JWT token verification and user information extraction
"""

import jwt
import logging
import requests
from typing import Dict, Optional
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

# JWT Configuration - should match the Security service
JWT_ALGORITHM = "HS256"
JWT_SECRET_KEY = "your-secret-key-here"  # In production, use environment variable

# Security service URL for token verification
SECURITY_URL = "http://security_service:8000"

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials) -> Dict:
    """
    Verify JWT token and return user information
    """
    try:
        token = credentials.credentials
        
        # Try to decode the JWT token locally first
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.InvalidTokenError:
            # If local verification fails, try the Security service
            return verify_token_with_security_service(token)
            
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

def verify_token_with_security_service(token: str) -> Dict:
    """
    Verify token with the Security service
    """
    try:
        response = requests.post(
            f"{SECURITY_URL}/auth/verify-token",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token verification failed",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except requests.RequestException as e:
        logger.error(f"Failed to verify token with Security service: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable"
        )

def get_current_user_from_token(token: str) -> Dict:
    """
    Extract user information from JWT token
    """
    try:
        # Create a mock credentials object for verify_token
        class MockCredentials:
            def __init__(self, token):
                self.credentials = token
        
        credentials = MockCredentials(token)
        user_data = verify_token(credentials)
        
        # Extract relevant user information
        return {
            "user_id": user_data.get("user_id"),
            "email": user_data.get("email"),
            "role": user_data.get("role"),
            "permissions": user_data.get("permissions", [])
        }
    except Exception as e:
        logger.error(f"Failed to extract user from token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or user information"
        )

def has_permission(user_data: Dict, required_permission: str) -> bool:
    """
    Check if user has the required permission
    """
    user_permissions = user_data.get("permissions", [])
    user_role = user_data.get("role", "")
    
    # Admin has all permissions
    if user_role == "admin" or "*" in user_permissions:
        return True
    
    # Check direct permission
    if required_permission in user_permissions:
        return True
    
    # Check wildcard permissions
    for permission in user_permissions:
        if permission.endswith("*"):
            prefix = permission[:-1]
            if required_permission.startswith(prefix):
                return True
    
    return False