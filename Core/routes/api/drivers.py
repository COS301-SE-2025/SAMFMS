"""
Driver Management Routes
Handles all driver-related operations
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials
from typing import Dict, Any
import logging

from .common import security, handle_service_request, validate_required_fields

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Drivers"])

@router.get("/drivers")
async def get_drivers(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get all drivers via Management service"""
    response = await handle_service_request(
        endpoint="/drivers",
        method="GET",
        data=dict(request.query_params),
        credentials=credentials,
        auth_endpoint="/drivers"
    )
    
    return response

@router.post("/drivers")
async def create_driver(
    driver_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create driver via Management service"""
    required_fields = ["full_name", "license_number"]
    validate_required_fields(driver_data, required_fields)
    
    response = await handle_service_request(
        endpoint="/drivers",
        method="POST",
        data=driver_data,
        credentials=credentials,
        auth_endpoint="/drivers"
    )
    
    return response

@router.get("/drivers/{driver_id}")
async def get_driver(
    driver_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get specific driver via Management service"""
    response = await handle_service_request(
        endpoint=f"/drivers/{driver_id}",
        method="GET",
        data={"driver_id": driver_id},
        credentials=credentials,
        auth_endpoint="/drivers"
    )
    
    return response

@router.put("/drivers/{driver_id}")
async def update_driver(
    driver_id: str,
    driver_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update driver via Management service"""
    response = await handle_service_request(
        endpoint=f"/drivers/{driver_id}",
        method="PUT",
        data=driver_data,
        credentials=credentials,
        auth_endpoint="/drivers"
    )
    
    return response

@router.delete("/drivers/{driver_id}")
async def delete_driver(
    driver_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete driver via Management service"""
    response = await handle_service_request(
        endpoint=f"/drivers/{driver_id}",
        method="DELETE",
        data={"driver_id": driver_id},
        credentials=credentials,
        auth_endpoint="/drivers"
    )
    
    return response
