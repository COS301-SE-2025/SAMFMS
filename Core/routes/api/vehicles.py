"""
Vehicle Management Routes
Handles all vehicle-related operations
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials
from typing import Dict, Any
import logging

from .common import security, handle_service_request, validate_required_fields
from utils.response_utils import standardize_vehicle_response

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Vehicles"])

@router.get("/vehicles")
async def get_vehicles(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get all vehicles via Management service"""
    logger.info(f"Received get_vehicles request with params: {dict(request.query_params)}")
    
    response = await handle_service_request(
        endpoint="/vehicles",
        method="GET",
        data=dict(request.query_params),
        credentials=credentials,
        auth_endpoint="/vehicles"
    )
    
    # Standardize field names for frontend compatibility
    standardized_response = standardize_vehicle_response(response)
    logger.info("Response standardized successfully")
    
    return standardized_response

@router.post("/vehicles")
async def create_vehicle(
    vehicle_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create vehicle via Management service"""
    # Validate input data
    required_fields = ["make", "model", "license_plate"]
    validate_required_fields(vehicle_data, required_fields)
    
    response = await handle_service_request(
        endpoint="/vehicles",
        method="POST",
        data=vehicle_data,
        credentials=credentials,
        auth_endpoint="/vehicles"
    )
    
    return response

@router.get("/vehicles/{vehicle_id}")
async def get_vehicle(
    vehicle_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get specific vehicle via Management service"""
    response = await handle_service_request(
        endpoint=f"/vehicles/{vehicle_id}",
        method="GET",
        data={"vehicle_id": vehicle_id},
        credentials=credentials,
        auth_endpoint="/vehicles"
    )
    
    return response

@router.put("/vehicles/{vehicle_id}")
async def update_vehicle(
    vehicle_id: str,
    vehicle_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update vehicle via Management service"""
    response = await handle_service_request(
        endpoint=f"/vehicles/{vehicle_id}",
        method="PUT",
        data=vehicle_data,
        credentials=credentials,
        auth_endpoint="/vehicles"
    )
    
    return response

@router.delete("/vehicles/{vehicle_id}")
async def delete_vehicle(
    vehicle_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete vehicle via Management service"""
    response = await handle_service_request(
        endpoint=f"/vehicles/{vehicle_id}",
        method="DELETE",
        data={"vehicle_id": vehicle_id},
        credentials=credentials,
        auth_endpoint="/vehicles"
    )
    
    return response

@router.get("/vehicles/search/{query}")
async def search_vehicles(
    query: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Search vehicles via Management service"""
    response = await handle_service_request(
        endpoint=f"/vehicles/search/{query}",
        method="GET",
        data={"query": query},
        credentials=credentials,
        auth_endpoint="/vehicles"
    )
    
    return response
