"""
Vehicle Assignment Management Routes
Handles all assignment-related operations through service proxy
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from fastapi.security import HTTPAuthorizationCredentials
from typing import Dict, Any, Optional
import logging

from .base import security, handle_service_request, validate_required_fields
from utils.exceptions import ValidationError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Vehicle Assignments"])

@router.get("/assignments")
async def get_assignments(
    request: Request,
    vehicle_id: Optional[str] = Query(None, description="Filter by vehicle ID"),
    driver_id: Optional[str] = Query(None, description="Filter by driver ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get all assignments via Management service"""
    logger.info(f"Received get_assignments request with params: {dict(request.query_params)}")
    
    response = await handle_service_request(
        endpoint="/api/assignments",
        method="GET",
        data=dict(request.query_params),
        credentials=credentials,
        auth_endpoint="/api/assignments"
    )
    
    return response

@router.post("/assignments")
async def create_assignment(
    assignment_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create assignment via Management service"""
    # Validate input data
    required_fields = ["vehicle_id", "driver_id"]
    validate_required_fields(assignment_data, required_fields)
    
    # Add default values for backend compatibility
    if "status" not in assignment_data:
        assignment_data["status"] = "active"
    
    response = await handle_service_request(
        endpoint="/api/assignments",
        method="POST",
        data=assignment_data,
        credentials=credentials,
        auth_endpoint="/api/assignments"
    )
    
    return response

@router.get("/assignments/{assignment_id}")
async def get_assignment(
    assignment_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get specific assignment via Management service"""
    response = await handle_service_request(
        endpoint=f"/api/assignments/{assignment_id}",
        method="GET",
        data={"assignment_id": assignment_id},
        credentials=credentials,
        auth_endpoint="/api/assignments"
    )
    
    return response

@router.put("/assignments/{assignment_id}")
async def update_assignment(
    assignment_id: str,
    assignment_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update assignment via Management service"""
    logger.info(f"Updating assignment {assignment_id} with data: {assignment_data}")
    
    response = await handle_service_request(
        endpoint=f"/api/assignments/{assignment_id}",
        method="PUT",
        data=assignment_data,
        credentials=credentials,
        auth_endpoint="/api/assignments"
    )
    
    logger.info(f"Assignment {assignment_id} updated successfully")
    return response

@router.delete("/assignments/{assignment_id}")
async def delete_assignment(
    assignment_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete assignment via Management service"""
    logger.info(f"Deleting assignment {assignment_id}")
    
    response = await handle_service_request(
        endpoint=f"/api/assignments/{assignment_id}",
        method="DELETE",
        data={"assignment_id": assignment_id},
        credentials=credentials,
        auth_endpoint="/api/assignments"
    )
    
    logger.info(f"Assignment {assignment_id} deleted successfully")
    return response

@router.put("/assignments/{assignment_id}/complete")
async def complete_assignment(
    assignment_id: str,
    completion_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Complete assignment via Management service"""
    logger.info(f"Completing assignment {assignment_id}")
    
    response = await handle_service_request(
        endpoint=f"/api/assignments/{assignment_id}/complete",
        method="PUT",
        data=completion_data,
        credentials=credentials,
        auth_endpoint="/api/assignments"
    )
    
    logger.info(f"Assignment {assignment_id} completed successfully")
    return response

@router.put("/assignments/{assignment_id}/cancel")
async def cancel_assignment(
    assignment_id: str,
    cancellation_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Cancel assignment via Management service"""
    logger.info(f"Cancelling assignment {assignment_id}")
    
    response = await handle_service_request(
        endpoint=f"/api/assignments/{assignment_id}/cancel",
        method="PUT",
        data=cancellation_data,
        credentials=credentials,
        auth_endpoint="/api/assignments"
    )
    
    logger.info(f"Assignment {assignment_id} cancelled successfully")
    return response
