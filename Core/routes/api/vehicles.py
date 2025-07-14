"""
Vehicle Management Routes
Handles all vehicle-related operations through service proxy
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials
from typing import Dict, Any
import logging

from .base import security, handle_service_request, validate_required_fields
from .utils import standardize_vehicle_response
from utils.exceptions import ValidationError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Vehicles"])

@router.get("/vehicles")
async def get_vehicles(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get all vehicles via Management service"""
    logger.info(f"Received get_vehicles request with params: {dict(request.query_params)}")
    
    response = await handle_service_request(
        endpoint="/api/vehicles",
        method="GET",
        data=dict(request.query_params),
        credentials=credentials,
        auth_endpoint="/api/vehicles"
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
    # Validate input data - support both license_plate and registration_number
    required_fields = ["make", "model", "year"]
    validate_required_fields(vehicle_data, required_fields)
    
    # Ensure license plate is provided (either as license_plate or registration_number)
    if not vehicle_data.get("license_plate") and not vehicle_data.get("registration_number"):
        raise ValidationError("Either license_plate or registration_number is required")
    
    # Add default values for backend compatibility
    if "type" not in vehicle_data:
        vehicle_data["type"] = "sedan"
    if "department" not in vehicle_data:
        vehicle_data["department"] = "General"
    if "status" not in vehicle_data:
        vehicle_data["status"] = "available"
    
    response = await handle_service_request(
        endpoint="/api/vehicles",
        method="POST",
        data=vehicle_data,
        credentials=credentials,
        auth_endpoint="/api/vehicles"
    )
    
    return response

@router.get("/vehicles/{vehicle_id}")
async def get_vehicle(
    vehicle_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get specific vehicle via Management service"""
    response = await handle_service_request(
        endpoint=f"/api/vehicles/{vehicle_id}",
        method="GET",
        data={"vehicle_id": vehicle_id},
        credentials=credentials,
        auth_endpoint="/api/vehicles"
    )
    
    return response

@router.put("/vehicles/{vehicle_id}")
async def update_vehicle(
    vehicle_id: str,
    vehicle_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update vehicle via Management service"""
    logger.info(f"Updating vehicle {vehicle_id} with data: {vehicle_data}")
    
    response = await handle_service_request(
        endpoint=f"/api/vehicles/{vehicle_id}",
        method="PUT",
        data=vehicle_data,
        credentials=credentials,
        auth_endpoint="/api/vehicles"
    )
    
    logger.info(f"Vehicle {vehicle_id} updated successfully")
    return response

@router.delete("/vehicles/{vehicle_id}")
async def delete_vehicle(
    vehicle_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete vehicle via Management service"""
    logger.info(f"Deleting vehicle {vehicle_id}")
    
    response = await handle_service_request(
        endpoint=f"/api/vehicles/{vehicle_id}",
        method="DELETE",
        data={"vehicle_id": vehicle_id},
        credentials=credentials,
        auth_endpoint="/api/vehicles"
    )
    
    logger.info(f"Vehicle {vehicle_id} deleted successfully")
    return response

@router.get("/vehicles/search/{query}")
async def search_vehicles(
    query: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Search vehicles via Management service"""
    response = await handle_service_request(
        endpoint=f"/api/vehicles/search/{query}",
        method="GET",
        data={"query": query},
        credentials=credentials,
        auth_endpoint="/api/vehicles"
    )
    
    return response

# Driver Management Routes (under vehicles namespace)
@router.get("/vehicles/drivers")
async def get_drivers(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get all drivers via Management service"""
    response = await handle_service_request(
        endpoint="/api/drivers",
        method="GET",
        data=dict(request.query_params),
        credentials=credentials,
        auth_endpoint="/api/vehicles/drivers"
    )
    
    return response

@router.post("/vehicles/drivers")
async def create_driver(
    driver_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a new driver via Management service"""
    response = await handle_service_request(
        endpoint="/api/drivers",
        method="POST",
        data=driver_data,
        credentials=credentials,
        auth_endpoint="/api/vehicles/drivers"
    )
    
    return response

@router.get("/vehicles/drivers/{driver_id}")
async def get_driver(
    driver_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get specific driver via Management service"""
    response = await handle_service_request(
        endpoint=f"/api/drivers/{driver_id}",
        method="GET",
        data={"driver_id": driver_id},
        credentials=credentials,
        auth_endpoint="/api/vehicles/drivers"
    )
    
    return response

@router.put("/vehicles/drivers/{driver_id}")
async def update_driver(
    driver_id: str,
    driver_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update driver via Management service"""
    response = await handle_service_request(
        endpoint=f"/api/drivers/{driver_id}",
        method="PUT",
        data=driver_data,
        credentials=credentials,
        auth_endpoint="/api/vehicles/drivers"
    )
    
    return response

@router.delete("/vehicles/drivers/{driver_id}")
async def delete_driver(
    driver_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete driver via Management service"""
    response = await handle_service_request(
        endpoint=f"/api/drivers/{driver_id}",
        method="DELETE",
        data={"driver_id": driver_id},
        credentials=credentials,
        auth_endpoint="/api/vehicles/drivers"
    )
    
    return response
