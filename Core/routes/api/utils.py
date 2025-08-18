"""
Response utilities for API routes
Handles response standardization and formatting
"""

from typing import Dict, Any, Union
import logging

logger = logging.getLogger(__name__)

def standardize_vehicle_response(response_data: Union[Dict[str, Any], None]) -> Dict[str, Any]:
    """Standardize vehicle response field names for frontend compatibility"""
    if not response_data:
        return {}
        
    if isinstance(response_data, dict):
        if "vehicles" in response_data:
            # Handle list of vehicles
            response_data["vehicles"] = [standardize_single_vehicle(v) for v in response_data.get("vehicles", [])]
        else:
            # Handle single vehicle
            response_data = standardize_single_vehicle(response_data)
    
    return response_data

def standardize_single_vehicle(vehicle: Dict[str, Any]) -> Dict[str, Any]:
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

def standardize_error_response(error: Exception, endpoint: str) -> Dict[str, Any]:
    """Standardize error responses"""
    return {
        "error": True,
        "message": str(error),
        "endpoint": endpoint,
        "type": type(error).__name__
    }

def standardize_success_response(data: Any, message: str = "Success") -> Dict[str, Any]:
    """Standardize success responses"""
    return {
        "success": True,
        "message": message,
        "data": data
    }
