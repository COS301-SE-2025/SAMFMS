"""
Vehicle Management API Routes
Handles vehicle CRUD operations and assignments
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any
import logging

from .common import handle_service_request, validate_required_fields, standardize_vehicle_response

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Vehicles"])
security = HTTPBearer()

# Vehicle CRUD Operations
@router.get("")
async def get_vehicles(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get all vehicles via Management service"""
    logger.info(f"Received get_vehicles request with params: {dict(request.query_params)}")
    
    response = await handle_service_request(
        credentials=credentials,
        endpoint="/api/vehicles",
        method="GET",
        data=dict(request.query_params)
    )
    
    # Standardize field names for frontend compatibility
    standardized_response = standardize_vehicle_response(response)
    logger.info("Response standardized successfully")
    
    return standardized_response

@router.post("")
async def create_vehicle(
    vehicle_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create vehicle via Management service"""
    # Validate input data
    required_fields = ["make", "model", "license_plate"]
    validate_required_fields(vehicle_data, required_fields, "Vehicle")
    
    return await handle_service_request(
        credentials=credentials,
        endpoint="/api/vehicles",
        method="POST",
        data=vehicle_data
    )

@router.get("/{vehicle_id}")
async def get_vehicle(
    vehicle_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get specific vehicle via Management service"""
    return await handle_service_request(
        credentials=credentials,
        endpoint=f"/api/vehicles/{vehicle_id}",
        method="GET",
        data={"vehicle_id": vehicle_id}
    )

@router.put("/{vehicle_id}")
async def update_vehicle(
    vehicle_id: str,
    vehicle_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update vehicle via Management service"""
    return await handle_service_request(
        credentials=credentials,
        endpoint=f"/api/vehicles/{vehicle_id}",
        method="PUT",
        data=vehicle_data
    )

@router.delete("/{vehicle_id}")
async def delete_vehicle(
    vehicle_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete vehicle via Management service"""
    return await handle_service_request(
        credentials=credentials,
        endpoint=f"/api/vehicles/{vehicle_id}",
        method="DELETE",
        data={"vehicle_id": vehicle_id}
    )

@router.get("/search/{query}")
async def search_vehicles(
    query: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Search vehicles via Management service"""
    return await handle_service_request(
        credentials=credentials,
        endpoint=f"/api/vehicles/search/{query}",
        method="GET",
        data={"query": query}
    )

# Vehicle Assignment Routes
@router.get("/assignments")
async def get_vehicle_assignments(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get vehicle assignments via Management service"""
    return await handle_service_request(
        credentials=credentials,
        endpoint="/api/vehicle-assignments",
        method="GET",
        data=dict(request.query_params),
        auth_endpoint="/api/vehicle-assignments"
    )

@router.post("/assignments")
async def create_vehicle_assignment(
    assignment_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create vehicle assignment via Management service"""
    return await handle_service_request(
        credentials=credentials,
        endpoint="/api/vehicle-assignments",
        method="POST",
        data=assignment_data,
        auth_endpoint="/api/vehicle-assignments"
    )

@router.put("/assignments/{assignment_id}")
async def update_vehicle_assignment(
    assignment_id: str,
    assignment_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update vehicle assignment via Management service"""
    return await handle_service_request(
        credentials=credentials,
        endpoint=f"/api/vehicle-assignments/{assignment_id}",
        method="PUT",
        data=assignment_data,
        auth_endpoint="/api/vehicle-assignments"
    )

@router.delete("/assignments/{assignment_id}")
async def delete_vehicle_assignment(
    assignment_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete vehicle assignment via Management service"""
    return await handle_service_request(
        credentials=credentials,
        endpoint=f"/api/vehicle-assignments/{assignment_id}",
        method="DELETE",
        data={"assignment_id": assignment_id},
        auth_endpoint="/api/vehicle-assignments"
    )
