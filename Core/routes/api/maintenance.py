"""
Maintenance Routes
Handles vehicle maintenance operations through service proxy
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials
from typing import Dict, Any
import logging

from .base import security, handle_service_request, validate_required_fields

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Maintenance"])

@router.get("/maintenance")
async def get_maintenance_records(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get maintenance records via Vehicle Maintenance service"""
    response = await handle_service_request(
        endpoint="/api/maintenance",
        method="GET",
        data=dict(request.query_params),
        credentials=credentials,
        auth_endpoint="/api/maintenance"
    )
    
    return response

@router.post("/maintenance")
async def create_maintenance_record(
    maintenance_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create maintenance record via Vehicle Maintenance service"""
    required_fields = ["vehicle_id", "maintenance_type", "description"]
    validate_required_fields(maintenance_data, required_fields)
    
    response = await handle_service_request(
        endpoint="/api/maintenance",
        method="POST",
        data=maintenance_data,
        credentials=credentials,
        auth_endpoint="/api/maintenance"
    )
    
    return response

@router.get("/maintenance/{maintenance_id}")
async def get_maintenance_record(
    maintenance_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get specific maintenance record via Vehicle Maintenance service"""
    response = await handle_service_request(
        endpoint=f"/maintenance/{maintenance_id}",
        method="GET",
        data={"maintenance_id": maintenance_id},
        credentials=credentials,
        auth_endpoint="/api/maintenance"
    )
    
    return response

@router.put("/maintenance/{maintenance_id}")
async def update_maintenance_record(
    maintenance_id: str,
    maintenance_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update maintenance record via Vehicle Maintenance service"""
    response = await handle_service_request(
        endpoint=f"/maintenance/{maintenance_id}",
        method="PUT",
        data=maintenance_data,
        credentials=credentials,
        auth_endpoint="/api/maintenance"
    )
    
    return response

@router.delete("/maintenance/{maintenance_id}")
async def delete_maintenance_record(
    maintenance_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete maintenance record via Vehicle Maintenance service"""
    response = await handle_service_request(
        endpoint=f"/maintenance/{maintenance_id}",
        method="DELETE",
        data={"maintenance_id": maintenance_id},
        credentials=credentials,
        auth_endpoint="/api/maintenance"
    )
    
    return response
