"""
API dependencies and utilities
"""
from fastapi import HTTPException, Depends, Header
from typing import Optional

from schemas.entities import Trip
from services.trip_service import trip_service


async def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    """Extract current user from authorization header"""
    # This would integrate with actual authentication service
    # For now, return a mock user
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    # Mock user extraction
    if authorization.startswith("Bearer "):
        token = authorization[7:]
        # Would validate token here
        return "user_123"  # Mock user ID
    
    raise HTTPException(status_code=401, detail="Invalid authorization format")


async def get_current_user_secure(authorization: Optional[str] = Header(None)) -> dict:
    """Extract current user from authorization header and return user context"""
    # This would integrate with actual authentication service
    # For now, return a mock user context
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    # Mock user extraction
    if authorization.startswith("Bearer "):
        token = authorization[7:]
        # Would validate token here and get user details
        return {
            "user_id": "user_123",
            "role": "driver",  # Could be driver, admin, fleet_manager
            "permissions": ["read:notifications", "write:notifications"]
        }
    
    raise HTTPException(status_code=401, detail="Invalid authorization format")


async def validate_trip_access(trip_id: str, current_user: str = Depends(get_current_user)) -> Trip:
    """Validate that user has access to the trip"""
    trip = await trip_service.get_trip_by_id(trip_id)
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Check if user has access to this trip
    # This would implement proper access control
    # For now, allow access if user is creator or assigned driver
    if (trip.created_by != current_user and 
        (not trip.driver_assignment or trip.driver_assignment != current_user)):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return trip


def get_pagination_params(skip: int = 0, limit: int = 50) -> dict:
    """Get pagination parameters with validation"""
    if skip < 0:
        raise HTTPException(status_code=400, detail="Skip must be non-negative")
    
    if limit < 1 or limit > 1000:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 1000")
    
    return {"skip": skip, "limit": limit}
