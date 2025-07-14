"""
Trip Planning Routes
Handles trip planning and management operations through service proxy
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials
from typing import Dict, Any
import logging

from .base import security, handle_service_request, validate_required_fields

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Trip Planning"])

@router.get("/trips")
async def get_trips(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get trips via Trip Planning service"""
    response = await handle_service_request(
        endpoint="/trips",
        method="GET",
        data=dict(request.query_params),
        credentials=credentials,
        auth_endpoint="/trips"
    )
    
    return response

@router.post("/trips")
async def create_trip(
    trip_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a new trip via Trip Planning service"""
    required_fields = ["vehicle_id", "driver_id", "destination"]
    validate_required_fields(trip_data, required_fields)
    
    response = await handle_service_request(
        endpoint="/trips",
        method="POST",
        data=trip_data,
        credentials=credentials,
        auth_endpoint="/trips"
    )
    
    return response

@router.get("/trips/{trip_id}")
async def get_trip(
    trip_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get specific trip via Trip Planning service"""
    response = await handle_service_request(
        endpoint=f"/trips/{trip_id}",
        method="GET",
        data={"trip_id": trip_id},
        credentials=credentials,
        auth_endpoint="/trips"
    )
    
    return response

@router.put("/trips/{trip_id}")
async def update_trip(
    trip_id: str,
    trip_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update trip via Trip Planning service"""
    response = await handle_service_request(
        endpoint=f"/trips/{trip_id}",
        method="PUT",
        data=trip_data,
        credentials=credentials,
        auth_endpoint="/trips"
    )
    
    return response

@router.delete("/trips/{trip_id}")
async def delete_trip(
    trip_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete trip via Trip Planning service"""
    response = await handle_service_request(
        endpoint=f"/trips/{trip_id}",
        method="DELETE",
        data={"trip_id": trip_id},
        credentials=credentials,
        auth_endpoint="/trips"
    )
    
    return response
