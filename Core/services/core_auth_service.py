"""
Enhanced Core Authentication Service
Handles authorization and token verification with Security block
"""

import httpx
import logging
import os
import asyncio
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from datetime import datetime

logger = logging.getLogger(__name__)

class CoreAuthService:
    """Enhanced authentication service for Core with Security block integration"""
    
    def __init__(self):
        self.security_url = os.getenv("SECURITY_URL", "http://security_service:8000")
        self.http_client = httpx.AsyncClient(timeout=10.0)
        
        # Permission mapping for endpoints
        self.permission_map = {
            # Vehicle management
            "/api/vehicles": {
                "GET": ["vehicle.read", "fleet.read"],
                "POST": ["vehicle.create", "fleet.manage"],
                "PUT": ["vehicle.update", "fleet.manage"],
                "DELETE": ["vehicle.delete", "fleet.manage"]
            },
            "/api/vehicle-assignments": {
                "GET": ["assignment.read", "fleet.read"],
                "POST": ["assignment.create", "fleet.manage"],
                "PUT": ["assignment.update", "fleet.manage"],
                "DELETE": ["assignment.delete", "fleet.manage"]
            },
            # GPS and tracking
            "/api/gps": {
                "GET": ["tracking.read", "gps.read"],
                "POST": ["tracking.create", "gps.manage"]
            },
            "/api/tracking": {
                "GET": ["tracking.read"],
                "POST": ["tracking.create"]
            },
            # Trip planning
            "/api/trips": {
                "GET": ["trip.read", "planning.read"],
                "POST": ["trip.create", "planning.create"],
                "PUT": ["trip.update", "planning.update"],
                "DELETE": ["trip.delete", "planning.manage"]
            },
            # Maintenance
            "/api/maintenance": {
                "GET": ["maintenance.read"],
                "POST": ["maintenance.create"],
                "PUT": ["maintenance.update"],
                "DELETE": ["maintenance.delete"]
            }
        }
        
        # Role-based permissions
        self.role_permissions = {
            "admin": ["*"],  # Admin has all permissions
            "fleet_manager": [
                "vehicle.read", "vehicle.update", "fleet.read", "fleet.manage",
                "assignment.read", "assignment.create", "assignment.update",
                "tracking.read", "gps.read", "trip.read", "planning.read",
                "maintenance.read", "maintenance.create", "maintenance.update"
            ],
            "driver": [
                "vehicle.read", "assignment.read", "tracking.read", "gps.read",
                "trip.read", "maintenance.read"
            ],
            "maintenance_staff": [
                "vehicle.read", "maintenance.read", "maintenance.create", 
                "maintenance.update", "maintenance.delete"
            ]
        }
    
    async def authorize_request(self, token: str, endpoint: str, method: str) -> Dict[str, Any]:
        """Authorize request by verifying token and checking permissions"""
        try:
            # Verify JWT with Security block
            user_info = await self.verify_token_with_security(token)
            
            # Check permissions for endpoint
            if not await self.check_permissions(user_info, endpoint, method):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions for this operation"
                )
              # Create user context for service calls
            user_context = {
                "user_id": user_info.get("user_id"),
                "role": user_info.get("role"),
                "permissions": user_info.get("permissions", []),
                "email": user_info.get("email"),
                "authorized_at": datetime.utcnow().isoformat()
            }
            
            return user_context
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authorization error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authorization service error"
            )

    async def verify_token_with_security(self, token: str) -> Dict[str, Any]:
        """Verify JWT token with Security block via direct HTTP call"""
        try:
            response = await self.http_client.post(
                f"{self.security_url}/auth/verify-token",
                headers={"Authorization": f"Bearer {token}"},
                json={"token": token}
            )
            
            if response.status_code == 200:
                user_info = response.json()
                logger.debug(f"Token verified for user: {user_info.get('email')}")
                return user_info
            elif response.status_code == 401:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token"
                )
            else:
                logger.error(f"Security service returned status {response.status_code}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Security service unavailable"
                )
                
        except httpx.TimeoutException:
            logger.error("Timeout verifying token with security service")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Security service timeout"
            )
        except httpx.RequestError as e:
            logger.error(f"Error connecting to security service: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Security service connection error"
            )
    
    async def check_permissions(self, user_info: Dict[str, Any], endpoint: str, method: str) -> bool:
        """Check if user has permission for the requested endpoint and method"""
        try:
            user_role = user_info.get("role")
            user_permissions = user_info.get("permissions", [])
            
            # Admin has access to everything
            if user_role == "admin":
                return True
            
            # Get required permissions for endpoint
            required_permissions = self.get_required_permissions(endpoint, method)
            if not required_permissions:
                # If no specific permissions required, allow based on role
                return user_role in ["admin", "fleet_manager", "driver", "maintenance_staff"]
            
            # Check if user has any of the required permissions
            user_all_permissions = set(user_permissions + self.role_permissions.get(user_role, []))
            
            # Check for wildcard permission
            if "*" in user_all_permissions:
                return True
            
            # Check if any required permission is in user's permissions
            for permission in required_permissions:
                if permission in user_all_permissions:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Permission check error: {e}")
            return False
    
    def get_required_permissions(self, endpoint: str, method: str) -> list:
        """Get required permissions for endpoint and method"""
        # Find matching endpoint pattern
        for endpoint_pattern, methods in self.permission_map.items():
            if endpoint.startswith(endpoint_pattern):
                return methods.get(method.upper(), [])
        
        return []
    
    async def check_resource_access(self, user_context: Dict[str, Any], resource_id: str, action: str) -> bool:
        """Check if user can access specific resource"""
        try:
            user_role = user_context.get("role")
            user_id = user_context.get("user_id")
            
            # Admin has access to all resources
            if user_role == "admin":
                return True
            
            # Fleet managers can access most resources
            if user_role == "fleet_manager":
                return action in ["read", "update", "create"]
            
            # Drivers can only access their own assignments and related resources
            if user_role == "driver":
                if action == "read":
                    # For read operations, we might need to check if resource belongs to user
                    # This would typically involve a database query
                    return True
                return False
            
            # Maintenance staff can access maintenance-related resources
            if user_role == "maintenance_staff":
                return action in ["read", "create", "update"] and "maintenance" in resource_id.lower()
            
            return False
            
        except Exception as e:
            logger.error(f"Resource access check error: {e}")
            return False
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()


# Global instance
core_auth_service = CoreAuthService()
