"""
Enhanced Authentication Service for SAMFMS Core
Provides JWT token verification, user management, permissions, caching, and circuit breaker patterns
"""

import jwt
import logging
import aiohttp
import asyncio
import os
import time
import hashlib
from typing import Dict, Optional, List, Set, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from fastapi import HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from threading import Lock
import json

from logging_config import get_logger, log_with_context
from common.exceptions import SAMFMSError

logger = get_logger(__name__)

class AuthenticationError(SAMFMSError):
    """Authentication error"""
    pass

class AuthorizationError(SAMFMSError):
    """Authorization error"""
    pass

class ServiceUnavailableError(SAMFMSError):
    """Service unavailable error"""
    pass

class UserRole(Enum):
    """User role enumeration"""
    ADMIN = "admin"
    MANAGER = "manager"
    DISPATCHER = "dispatcher"
    DRIVER = "driver"
    VIEWER = "viewer"

class PermissionScope(Enum):
    """Permission scope enumeration"""
    SYSTEM = "system"
    ORGANIZATION = "organization"
    FLEET = "fleet"
    VEHICLE = "vehicle"
    USER = "user"

@dataclass
class Permission:
    """Permission data class"""
    action: str  # create, read, update, delete, execute
    resource: str  # vehicles, users, routes, etc.
    scope: PermissionScope = PermissionScope.ORGANIZATION
    conditions: Dict = field(default_factory=dict)
    
    def __str__(self) -> str:
        return f"{self.action}:{self.resource}:{self.scope.value}"
    
    @classmethod
    def from_string(cls, permission_str: str) -> 'Permission':
        """Create permission from string representation"""
        parts = permission_str.split(':')
        if len(parts) >= 3:
            return cls(
                action=parts[0],
                resource=parts[1],
                scope=PermissionScope(parts[2])
            )
        elif len(parts) == 2:
            return cls(action=parts[0], resource=parts[1])
        else:
            raise ValueError(f"Invalid permission format: {permission_str}")

@dataclass
class UserData:
    """User data structure"""
    user_id: str
    email: str
    role: UserRole
    permissions: List[Permission] = field(default_factory=list)
    organization_id: Optional[str] = None
    fleet_ids: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    last_activity: Optional[datetime] = None
    
    def has_permission(self, required_permission: Union[str, Permission]) -> bool:
        """Check if user has the required permission"""
        if isinstance(required_permission, str):
            required_permission = Permission.from_string(required_permission)
        
        # Admin has all permissions
        if self.role == UserRole.ADMIN:
            return True
        
        # Check direct permissions
        for permission in self.permissions:
            if self._permission_matches(permission, required_permission):
                return True
        
        return False
    
    def _permission_matches(self, user_perm: Permission, required_perm: Permission) -> bool:
        """Check if user permission matches required permission"""
        # Check action (support wildcards)
        if user_perm.action != "*" and user_perm.action != required_perm.action:
            return False
        
        # Check resource (support wildcards)
        if user_perm.resource != "*" and user_perm.resource != required_perm.resource:
            return False
        
        # Check scope (user scope must be equal or higher)
        scope_hierarchy = {
            PermissionScope.USER: 1,
            PermissionScope.VEHICLE: 2,
            PermissionScope.FLEET: 3,
            PermissionScope.ORGANIZATION: 4,
            PermissionScope.SYSTEM: 5
        }
        
        user_scope_level = scope_hierarchy.get(user_perm.scope, 0)
        required_scope_level = scope_hierarchy.get(required_perm.scope, 0)
        
        return user_scope_level >= required_scope_level

class TokenCache:
    """Token caching with TTL"""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self._cache: Dict[str, Dict] = {}
        self._expiry: Dict[str, datetime] = {}
        self._lock = Lock()
        self.default_ttl = default_ttl
    
    def get(self, token_hash: str) -> Optional[UserData]:
        """Get cached user data"""
        with self._lock:
            if token_hash in self._cache:
                if datetime.utcnow() < self._expiry[token_hash]:
                    cached_data = self._cache[token_hash]
                    return self._dict_to_user_data(cached_data)
                else:
                    # Expired
                    del self._cache[token_hash]
                    del self._expiry[token_hash]
            return None
    
    def set(self, token_hash: str, user_data: UserData, ttl: Optional[int] = None) -> None:
        """Cache user data"""
        with self._lock:
            self._cache[token_hash] = self._user_data_to_dict(user_data)
            expiry_time = datetime.utcnow() + timedelta(seconds=ttl or self.default_ttl)
            self._expiry[token_hash] = expiry_time
    
    def invalidate(self, token_hash: str) -> None:
        """Invalidate cached token"""
        with self._lock:
            if token_hash in self._cache:
                del self._cache[token_hash]
                del self._expiry[token_hash]
    
    def clear_expired(self) -> None:
        """Clear expired entries"""
        now = datetime.utcnow()
        with self._lock:
            expired_keys = [
                key for key, expiry in self._expiry.items()
                if now >= expiry
            ]
            for key in expired_keys:
                if key in self._cache:
                    del self._cache[key]
                del self._expiry[key]
    
    def _user_data_to_dict(self, user_data: UserData) -> Dict:
        """Convert UserData to dictionary for caching"""
        return {
            'user_id': user_data.user_id,
            'email': user_data.email,
            'role': user_data.role.value,
            'permissions': [str(p) for p in user_data.permissions],
            'organization_id': user_data.organization_id,
            'fleet_ids': user_data.fleet_ids,
            'metadata': user_data.metadata,
            'last_activity': user_data.last_activity.isoformat() if user_data.last_activity else None
        }
    
    def _dict_to_user_data(self, data: Dict) -> UserData:
        """Convert dictionary to UserData"""
        permissions = [Permission.from_string(p) for p in data.get('permissions', [])]
        last_activity = None
        if data.get('last_activity'):
            last_activity = datetime.fromisoformat(data['last_activity'])
        
        return UserData(
            user_id=data['user_id'],
            email=data['email'],
            role=UserRole(data['role']),
            permissions=permissions,
            organization_id=data.get('organization_id'),
            fleet_ids=data.get('fleet_ids', []),
            metadata=data.get('metadata', {}),
            last_activity=last_activity
        )

class CircuitBreaker:
    """Circuit breaker for external service calls"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60, half_open_max_calls: int = 3):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
        self.half_open_calls = 0
        self.lock = Lock()
    
    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        with self.lock:
            if self.state == 'OPEN':
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = 'HALF_OPEN'
                    self.half_open_calls = 0
                else:
                    raise ServiceUnavailableError("Authentication service circuit breaker is OPEN")
            
            elif self.state == 'HALF_OPEN':
                if self.half_open_calls >= self.half_open_max_calls:
                    raise ServiceUnavailableError("Authentication service circuit breaker is HALF_OPEN (max calls reached)")
                self.half_open_calls += 1
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Handle successful call"""
        with self.lock:
            self.failure_count = 0
            self.state = 'CLOSED'
            self.half_open_calls = 0
    
    def _on_failure(self):
        """Handle failed call"""
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = 'OPEN'

class AuthService:
    """Enhanced authentication service"""
    
    def __init__(self):
        # Configuration
        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY")
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.security_service_url = os.getenv("SECURITY_URL", "http://security_service:8000")
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
        
        if not self.jwt_secret_key:
            raise ValueError("JWT_SECRET_KEY must be set in environment variables")
        
        # Components
        self.token_cache = TokenCache()
        self.circuit_breaker = CircuitBreaker()
        self.security = HTTPBearer()
        
        # Cache cleanup task
        self._cleanup_task = None
        
        logger.info("🔧 Enhanced authentication service initialized")
        logger.info(f"JWT Algorithm: {self.jwt_algorithm}")
        logger.info(f"Token expiry: {self.access_token_expire_minutes} minutes")
        logger.info(f"Security service URL: {self.security_service_url}")
    
    async def start(self):
        """Start the auth service"""
        # Start cache cleanup task
        self._cleanup_task = asyncio.create_task(self._cache_cleanup_loop())
        logger.info("🔧 Auth service started")
    
    async def stop(self):
        """Stop the auth service"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("🔧 Auth service stopped")
    
    async def _cache_cleanup_loop(self):
        """Periodically clean up expired cache entries"""
        while True:
            try:
                await asyncio.sleep(300)  # Clean every 5 minutes
                self.token_cache.clear_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cache cleanup: {e}")
    
    def _hash_token(self, token: str) -> str:
        """Create hash of token for caching"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    async def verify_token(self, credentials: HTTPAuthorizationCredentials, request: Optional[Request] = None) -> UserData:
        """
        Verify JWT token and return user data
        
        Args:
            credentials: HTTP authorization credentials
            request: Optional request object for correlation ID
        
        Returns:
            UserData object
        
        Raises:
            AuthenticationError: If token is invalid
            AuthorizationError: If user doesn't have access
            ServiceUnavailableError: If auth service is unavailable
        """
        token = credentials.credentials
        token_hash = self._hash_token(token)
        correlation_id = getattr(request.state, 'correlation_id', None) if request else None
        
        # Check cache first
        cached_user = self.token_cache.get(token_hash)
        if cached_user:
            log_with_context(
                logger, 'debug',
                f"Token verification cache hit for user {cached_user.user_id}",
                correlation_id=correlation_id
            )
            return cached_user
        
        # Verify with security service
        try:
            user_data = await self.circuit_breaker.call(
                self._verify_with_security_service, token, correlation_id
            )
            
            # Cache the result
            self.token_cache.set(token_hash, user_data)
            
            log_with_context(
                logger, 'info',
                f"Token verified for user {user_data.user_id}",
                correlation_id=correlation_id,
                user_id=user_data.user_id
            )
            
            return user_data
            
        except Exception as e:
            log_with_context(
                logger, 'error',
                f"Token verification failed: {e}",
                correlation_id=correlation_id
            )
            
            if isinstance(e, (AuthenticationError, AuthorizationError, ServiceUnavailableError)):
                raise e
            else:
                raise AuthenticationError("Token verification failed")
    
    async def _verify_with_security_service(self, token: str, correlation_id: Optional[str] = None) -> UserData:
        """Verify token with security service"""
        headers = {"Authorization": f"Bearer {token}"}
        if correlation_id:
            headers["X-Correlation-ID"] = correlation_id
        
        timeout = aiohttp.ClientTimeout(total=10)
        
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{self.security_service_url}/auth/verify-token",
                    headers=headers
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_user_data(data)
                    
                    elif response.status == 401:
                        raise AuthenticationError("Invalid or expired token")
                    
                    elif response.status == 403:
                        raise AuthorizationError("Insufficient permissions")
                    
                    else:
                        error_text = await response.text()
                        raise ServiceUnavailableError(f"Security service error: {response.status} - {error_text}")
        
        except asyncio.TimeoutError:
            raise ServiceUnavailableError("Security service timeout")
        except aiohttp.ClientError as e:
            raise ServiceUnavailableError(f"Security service connection error: {e}")
    
    def _parse_user_data(self, data: Dict) -> UserData:
        """Parse user data from security service response"""
        permissions = []
        for perm_str in data.get('permissions', []):
            try:
                permissions.append(Permission.from_string(perm_str))
            except ValueError:
                logger.warning(f"Invalid permission format: {perm_str}")
        
        return UserData(
            user_id=data['user_id'],
            email=data['email'],
            role=UserRole(data.get('role', 'viewer')),
            permissions=permissions,
            organization_id=data.get('organization_id'),
            fleet_ids=data.get('fleet_ids', []),
            metadata=data.get('metadata', {}),
            last_activity=datetime.utcnow()
        )
    
    async def check_permission(self, user_data: UserData, required_permission: Union[str, Permission]) -> bool:
        """Check if user has required permission"""
        return user_data.has_permission(required_permission)
    
    async def require_permission(self, user_data: UserData, required_permission: Union[str, Permission]) -> None:
        """Require user to have permission, raise exception if not"""
        if not await self.check_permission(user_data, required_permission):
            raise AuthorizationError(f"Permission required: {required_permission}")
    
    def invalidate_token(self, token: str) -> None:
        """Invalidate token in cache"""
        token_hash = self._hash_token(token)
        self.token_cache.invalidate(token_hash)
    
    async def get_user_permissions(self, user_data: UserData) -> List[str]:
        """Get list of user permissions as strings"""
        return [str(perm) for perm in user_data.permissions]

# Global auth service instance
_auth_service: Optional[AuthService] = None

async def get_auth_service() -> AuthService:
    """Get global auth service instance"""
    global _auth_service
    
    if _auth_service is None:
        _auth_service = AuthService()
        await _auth_service.start()
    
    return _auth_service

async def shutdown_auth_service():
    """Shutdown global auth service instance"""
    global _auth_service
    
    if _auth_service:
        await _auth_service.stop()
        _auth_service = None

# Dependency functions for FastAPI
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = None,
    request: Request = None
) -> UserData:
    """FastAPI dependency to get current user"""
    if not credentials:
        raise AuthenticationError("Authorization header required")
    
    auth_service = await get_auth_service()
    return await auth_service.verify_token(credentials, request)

def require_permission(permission: Union[str, Permission]):
    """FastAPI dependency factory for permission checking"""
    async def permission_checker(user_data: UserData = None) -> UserData:
        if not user_data:
            raise AuthenticationError("Authentication required")
        
        auth_service = await get_auth_service()
        await auth_service.require_permission(user_data, permission)
        return user_data
    
    return permission_checker

def require_role(role: UserRole):
    """FastAPI dependency factory for role checking"""
    async def role_checker(user_data: UserData = None) -> UserData:
        if not user_data:
            raise AuthenticationError("Authentication required")
        
        if user_data.role != role and user_data.role != UserRole.ADMIN:
            raise AuthorizationError(f"Role required: {role.value}")
        
        return user_data
    
    return role_checker

# Legacy support functions
async def verify_token(credentials: HTTPAuthorizationCredentials) -> Dict:
    """Legacy function for backward compatibility"""
    auth_service = await get_auth_service()
    user_data = await auth_service.verify_token(credentials)
    
    return {
        "user_id": user_data.user_id,
        "email": user_data.email,
        "role": user_data.role.value,
        "permissions": [str(p) for p in user_data.permissions],
        "organization_id": user_data.organization_id,
        "fleet_ids": user_data.fleet_ids
    }

def has_permission(user_data: Dict, required_permission: str) -> bool:
    """Legacy function for backward compatibility"""
    # Convert dict back to UserData for checking
    try:
        permissions = [Permission.from_string(p) for p in user_data.get('permissions', [])]
        user_obj = UserData(
            user_id=user_data['user_id'],
            email=user_data['email'],
            role=UserRole(user_data.get('role', 'viewer')),
            permissions=permissions,
            organization_id=user_data.get('organization_id'),
            fleet_ids=user_data.get('fleet_ids', [])
        )
        return user_obj.has_permission(required_permission)
    except Exception:
        return False