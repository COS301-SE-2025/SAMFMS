"""
Drivers Routes
Handles all driver-related operations through service proxy
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from fastapi.security import HTTPAuthorizationCredentials
from typing import Dict, Any, Optional
import logging

from .base import security, handle_service_request

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Drivers"])

@router.get("/drivers")
async def get_drivers(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get all drivers via Management service"""
    logger.info(f"Received get drivers request with params: {dict(request.query_params)}")
    
    response = await handle_service_request(
        endpoint="/api/drivers",
        method="GET",
        data=dict(request.query_params),
        credentials=credentials,
        auth_endpoint="/api/drivers"
    )
    
    return response

@router.post("/drivers")
async def create_driver(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a new driver via Management service"""
    logger.info("Received create driver request")
    
    # Get the request body
    data = await request.json()
    
    response = await handle_service_request(
        endpoint="/api/drivers",
        method="POST",
        data=data,
        credentials=credentials,
        auth_endpoint="/api/drivers"
    )
    
    return response

@router.get("/drivers/{driver_id}")
async def get_driver(
    driver_id: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get a specific driver via Management service"""
    logger.info(f"Received get driver request for ID: {driver_id}")
    
    response = await handle_service_request(
        endpoint=f"/api/drivers/{driver_id}",
        method="GET",
        data=dict(request.query_params),
        credentials=credentials,
        auth_endpoint="/api/drivers"
    )
    
    return response

@router.put("/drivers/{driver_id}")
async def update_driver(
    driver_id: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update a driver via Management service"""
    logger.info(f"Received update driver request for ID: {driver_id}")
    
    # Get the request body
    data = await request.json()
    
    response = await handle_service_request(
        endpoint=f"/api/drivers/{driver_id}",
        method="PUT",
        data=data,
        credentials=credentials,
        auth_endpoint="/api/drivers"
    )
    
    return response

@router.delete("/drivers/{driver_id}")
async def delete_driver(
    driver_id: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete a driver via Management service"""
    logger.info(f"Received delete driver request for ID: {driver_id}")
    
    response = await handle_service_request(
        endpoint=f"/api/drivers/{driver_id}",
        method="DELETE",
        data=dict(request.query_params),
        credentials=credentials,
        auth_endpoint="/api/drivers"
    )
    
    return response

@router.get("/vehicles/drivers")
async def get_drivers_for_vehicles(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get all drivers for vehicle assignment dropdown via Management service"""
    logger.info(f"Received get drivers for vehicles request with params: {dict(request.query_params)}")
    
    # This endpoint should return drivers formatted for vehicle assignment
    response = await handle_service_request(
        endpoint="/api/drivers",
        method="GET",
        data=dict(request.query_params),
        credentials=credentials,
        auth_endpoint="/api/drivers"
    )
    
    return response
