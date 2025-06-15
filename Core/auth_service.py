"""
Authentication service for Core
Handles JWT token verification and user information extraction
"""

import jwt
import logging
import requests
import os
import time
from typing import Dict, Optional
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from collections import defaultdict
from threading import Lock

logger = logging.getLogger(__name__)

# JWT Configuration - must match the Security service exactly
JWT_ALGORITHM = "HS256"
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))

if not JWT_SECRET_KEY:
    logger.error("JWT_SECRET_KEY environment variable is required for production")
    raise ValueError("JWT_SECRET_KEY must be set in environment variables")

# Security service URL for token verification
SECURITY_URL = "http://security_service:8000"

security = HTTPBearer()

# Circuit breaker implementation
class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=60, expected_exception=Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
        self.lock = Lock()
    
    def call(self, func, *args, **kwargs):
        with self.lock:
            if self.state == 'OPEN':
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = 'HALF_OPEN'
                else:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Authentication service is temporarily unavailable"
                    )
            
            try:
                result = func(*args, **kwargs)
                self.on_success()
                return result
            except self.expected_exception as e:
                self.on_failure()
                raise e
    
    def on_success(self):
        self.failure_count = 0
        self.state = 'CLOSED'
    
    def on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'

# Circuit breaker instance for Security service
security_service_breaker = CircuitBreaker(
    failure_threshold=3, 
    recovery_timeout=30,
    expected_exception=requests.RequestException
)

logger.info(f"JWT configuration loaded - Algorithm: {JWT_ALGORITHM}, Token expiry: {ACCESS_TOKEN_EXPIRE_MINUTES} minutes")

def verify_token(credentials: HTTPAuthorizationCredentials) -> Dict:
    """
    Verify JWT token with the Security service
    Centralized verification ensures consistency and proper session management
    """
    try:
        token = credentials.credentials
        
        # Always verify with Security service to ensure proper session management
        # and blacklist checking
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
    Verify token with the Security service using circuit breaker pattern
    """
    def _verify_request():
        response = requests.post(
            f"{SECURITY_URL}/auth/verify-token",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise requests.RequestException(f"Token verification failed with status {response.status_code}")
    
    try:
        return security_service_breaker.call(_verify_request)
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