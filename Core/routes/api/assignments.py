"""
Vehicle Assignment Routes
Handles vehicle assignment operations
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials
from typing import Dict, Any
import logging

from .common import security, handle_service_request, validate_required_fields

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Vehicle Assignments"])

@router.get("/vehicle-assignments")
async def get_vehicle_assignments(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get vehicle assignments via Management service"""
    response = await handle_service_request(
        endpoint="/vehicle-assignments",
        method="GET",
        data=dict(request.query_params),
        credentials=credentials,
        auth_endpoint="/vehicle-assignments"
    )
    
    return response

@router.post("/vehicle-assignments")
async def create_vehicle_assignment(
    assignment_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create vehicle assignment via Management service"""
    required_fields = ["vehicle_id", "driver_id"]
    validate_required_fields(assignment_data, required_fields)
    
    response = await handle_service_request(
        endpoint="/vehicle-assignments",
        method="POST",
        data=assignment_data,
        credentials=credentials,
        auth_endpoint="/vehicle-assignments"
    )
    
    return response

@router.put("/vehicle-assignments/{assignment_id}")
async def update_vehicle_assignment(
    assignment_id: str,
    assignment_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update vehicle assignment via Management service"""
    response = await handle_service_request(
        endpoint=f"/vehicle-assignments/{assignment_id}",
        method="PUT",
        data=assignment_data,
        credentials=credentials,
        auth_endpoint="/vehicle-assignments"
    )
    
    return response

@router.delete("/vehicle-assignments/{assignment_id}")
async def delete_vehicle_assignment(
    assignment_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete vehicle assignment via Management service"""
    response = await handle_service_request(
        endpoint=f"/vehicle-assignments/{assignment_id}",
        method="DELETE",
        data={"assignment_id": assignment_id},
        credentials=credentials,
        auth_endpoint="/vehicle-assignments"
    )
    
    return response
