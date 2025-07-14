"""
GPS and Tracking Routes
Handles all GPS location and tracking operations through service proxy
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials
from typing import Dict, Any
import logging

from .base import security, handle_service_request

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["GPS & Tracking"])

@router.get("/gps/locations")
async def get_gps_locations(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get GPS locations via GPS service"""
    response = await handle_service_request(
        endpoint="/gps/locations",
        method="GET",
        data=dict(request.query_params),
        credentials=credentials,
        auth_endpoint="/api/gps"
    )
    
    return response

@router.post("/gps/locations")
async def create_gps_location(
    location_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create GPS location via GPS service"""
    response = await handle_service_request(
        endpoint="/gps/locations",
        method="POST",
        data=location_data,
        credentials=credentials,
        auth_endpoint="/api/gps"
    )
    
    return response

from .common import security, handle_service_request, validate_required_fields

logger = logging.getLogger(__name__)
router = APIRouter(tags=["GPS & Location"])

@router.get("/gps/locations")
async def get_gps_locations(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get GPS location data via GPS service"""
    response = await handle_service_request(
        endpoint="/gps/locations",
        method="GET",
        data=dict(request.query_params),
        credentials=credentials,
        auth_endpoint="/gps/locations"
    )
    
    return response

@router.post("/gps/locations")
async def create_gps_location(
    location_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create/update GPS location data via GPS service"""
    required_fields = ["vehicle_id", "latitude", "longitude"]
    validate_required_fields(location_data, required_fields)
    
    response = await handle_service_request(
        endpoint="/gps/locations",
        method="POST",
        data=location_data,
        credentials=credentials,
        auth_endpoint="/gps/locations"
    )
    
    return response

@router.get("/tracking/live")
async def get_live_tracking(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get live tracking data for vehicles"""
    response = await handle_service_request(
        endpoint="/tracking/live",
        method="GET",
        data=dict(request.query_params),
        credentials=credentials,
        auth_endpoint="/tracking"
    )
    
    return response

@router.get("/tracking/history/{vehicle_id}")
async def get_tracking_history(
    vehicle_id: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get tracking history for a specific vehicle"""
    query_params = dict(request.query_params)
    query_params["vehicle_id"] = vehicle_id
    
    response = await handle_service_request(
        endpoint=f"/tracking/history/{vehicle_id}",
        method="GET",
        data=query_params,
        credentials=credentials,
        auth_endpoint="/tracking"
    )
    
    return response
