"""
Common utilities for API routes
"""

from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from typing import Dict, Any
import logging

from utils.exceptions import (
    ServiceUnavailableError, 
    AuthorizationError, 
    ValidationError, 
    ServiceTimeoutError
)
from services.request_router import request_router
from services.core_auth_service import core_auth_service

logger = logging.getLogger(__name__)

async def handle_service_request(
    credentials: HTTPAuthorizationCredentials,
    endpoint: str,
    method: str,
    data: Dict[str, Any],
    auth_endpoint: str = None
) -> Dict[str, Any]:
    """
    Common handler for service proxy requests with standardized error handling
    
    Args:
        credentials: Authorization credentials
        endpoint: Target service endpoint
        method: HTTP method
        data: Request data
        auth_endpoint: Endpoint for authorization (defaults to endpoint)
    
    Returns:
        Service response data
    """
    try:
        # Use auth_endpoint if provided, otherwise use endpoint
        auth_path = auth_endpoint or endpoint
        
        # Authorize request
        user_context = await core_auth_service.authorize_request(
            credentials.credentials, auth_path, method
        )
        
        # Route to appropriate service
        response = await request_router.route_request(
            endpoint=endpoint,
            method=method,
            data=data,
            user_context=user_context
        )
        
        return response
        
    except AuthorizationError as e:
        logger.warning(f"Authorization failed for {endpoint}: {e.message}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)
    except ServiceUnavailableError as e:
        logger.error(f"Service unavailable for {endpoint}: {e.message}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message)
    except ServiceTimeoutError as e:
        logger.error(f"Service timeout for {endpoint}: {e.message}")
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=e.message)
    except ValidationError as e:
        logger.warning(f"Validation error for {endpoint}: {e.message}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error for {endpoint}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

def validate_required_fields(data: Dict[str, Any], required_fields: list, entity_name: str = "Entity"):
    """
    Validate that required fields are present in the data
    
    Args:
        data: Data to validate
        required_fields: List of required field names
        entity_name: Name of the entity for error messages
    
    Raises:
        ValidationError: If required fields are missing
    """
    if not data:
        raise ValidationError(f"{entity_name} data is required")
    
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")

def standardize_vehicle_response(response_data):
    """Standardize vehicle response field names for frontend compatibility"""
    if isinstance(response_data, dict):
        if "vehicles" in response_data:
            # Handle list of vehicles
            response_data["vehicles"] = [standardize_single_vehicle(v) for v in response_data["vehicles"]]
        else:
            # Handle single vehicle
            response_data = standardize_single_vehicle(response_data)
    
    return response_data

def standardize_single_vehicle(vehicle):
    """Standardize single vehicle field names"""
    if not isinstance(vehicle, dict):
        return vehicle
        
    # Field mapping from backend to frontend expected names
    field_mappings = {
        "license_plate": "licensePlate",
        "fuel_type": "fuelType", 
        "driver_name": "driver",
        "driver_id": "driverId",
        "last_service": "lastService",
        "next_service": "nextService",
        "insurance_expiry": "insuranceExpiry",
        "acquisition_date": "acquisitionDate",
        "fuel_efficiency": "fuelEfficiency",
        "last_driver": "lastDriver",
        "maintenance_costs": "maintenanceCosts"
    }
    
    # Apply field mappings
    standardized = vehicle.copy()
    for backend_field, frontend_field in field_mappings.items():
        if backend_field in standardized:
            standardized[frontend_field] = standardized.pop(backend_field)
    
    # Ensure status is properly capitalized
    if "status" in standardized:
        status = standardized["status"]
        if isinstance(status, str):
            standardized["status"] = status.capitalize()
    
    return standardized
