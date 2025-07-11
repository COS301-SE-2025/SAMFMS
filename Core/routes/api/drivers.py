"""
Driver Management API Routes
Handles driver CRUD operations
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any
import logging

from .common import handle_service_request

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/vehicles/drivers", tags=["Drivers"])
security = HTTPBearer()

@router.get("")
async def get_drivers(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get all drivers via Management service"""
    return await handle_service_request(
        credentials=credentials,
        endpoint="/api/drivers",
        method="GET",
        data=dict(request.query_params),
        auth_endpoint="/api/vehicles/drivers"
    )

@router.post("")
async def create_driver(
    driver_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a new driver via Management service"""
    return await handle_service_request(
        credentials=credentials,
        endpoint="/api/drivers",
        method="POST",
        data=driver_data,
        auth_endpoint="/api/vehicles/drivers"
    )

@router.get("/{driver_id}")
async def get_driver(
    driver_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get specific driver via Management service"""
    return await handle_service_request(
        credentials=credentials,
        endpoint=f"/api/drivers/{driver_id}",
        method="GET",
        data={"driver_id": driver_id},
        auth_endpoint="/api/vehicles/drivers"
    )

@router.put("/{driver_id}")
async def update_driver(
    driver_id: str,
    driver_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update driver via Management service"""
    return await handle_service_request(
        credentials=credentials,
        endpoint=f"/api/drivers/{driver_id}",
        method="PUT",
        data=driver_data,
        auth_endpoint="/api/vehicles/drivers"
    )

@router.delete("/{driver_id}")
async def delete_driver(
    driver_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete driver via Management service"""
    return await handle_service_request(
        credentials=credentials,
        endpoint=f"/api/drivers/{driver_id}",
        method="DELETE",
        data={"driver_id": driver_id},
        auth_endpoint="/api/vehicles/drivers"
    )
