"""
Response utilities for consistent API responses
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class APIResponse:
    """Standard API response format"""
    
    @staticmethod
    def success(data: Any, message: str = "Success", meta: Optional[Dict] = None) -> Dict[str, Any]:
        """Create a successful response"""
        response = {
            "success": True,
            "message": message,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if meta:
            response["meta"] = meta
            
        return response
    
    @staticmethod
    def error(message: str, error_code: str = None, details: Any = None) -> Dict[str, Any]:
        """Create an error response"""
        response = {
            "success": False,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if error_code:
            response["error_code"] = error_code
            
        if details:
            response["details"] = details
            
        return response
    
    @staticmethod
    def validation_error(errors: List[str]) -> Dict[str, Any]:
        """Create a validation error response"""
        return APIResponse.error(
            message="Validation failed",
            error_code="VALIDATION_ERROR",
            details={"validation_errors": errors}
        )

def standardize_vehicle_response(response: Any) -> Dict[str, Any]:
    """
    Standardize vehicle response format for frontend compatibility
    """
    try:
        if isinstance(response, dict):
            if "data" in response:
                # Response is already in standard format
                vehicles = response["data"]
            else:
                # Response is raw data
                vehicles = response
                
            # Ensure vehicles is a list
            if not isinstance(vehicles, list):
                vehicles = [vehicles] if vehicles else []
            
            # Standardize field names
            standardized_vehicles = []
            for vehicle in vehicles:
                if isinstance(vehicle, dict):
                    standardized_vehicle = {
                        "id": vehicle.get("_id") or vehicle.get("id"),
                        "license_plate": vehicle.get("license_plate") or vehicle.get("licensePlate"),
                        "make": vehicle.get("make"),
                        "model": vehicle.get("model"),
                        "year": vehicle.get("year"),
                        "status": vehicle.get("status", "active"),
                        "assigned_driver": vehicle.get("assigned_driver") or vehicle.get("assignedDriver"),
                        "created_at": vehicle.get("created_at") or vehicle.get("createdAt"),
                        "updated_at": vehicle.get("updated_at") or vehicle.get("updatedAt")
                    }
                    # Remove None values
                    standardized_vehicle = {k: v for k, v in standardized_vehicle.items() if v is not None}
                    standardized_vehicles.append(standardized_vehicle)
            
            return APIResponse.success(
                data=standardized_vehicles,
                message="Vehicles retrieved successfully",
                meta={"count": len(standardized_vehicles)}
            )
        else:
            logger.warning(f"Unexpected response format: {type(response)}")
            return APIResponse.error("Invalid response format from service")
            
    except Exception as e:
        logger.error(f"Error standardizing vehicle response: {e}")
        return APIResponse.error("Failed to process vehicle data")

def standardize_user_response(response: Any) -> Dict[str, Any]:
    """
    Standardize user response format for frontend compatibility
    """
    try:
        if isinstance(response, dict):
            if "data" in response:
                users = response["data"]
            else:
                users = response
                
            if not isinstance(users, list):
                users = [users] if users else []
            
            standardized_users = []
            for user in users:
                if isinstance(user, dict):
                    standardized_user = {
                        "id": user.get("_id") or user.get("id"),
                        "email": user.get("email"),
                        "first_name": user.get("first_name") or user.get("firstName"),
                        "last_name": user.get("last_name") or user.get("lastName"),
                        "role": user.get("role"),
                        "status": user.get("status", "active"),
                        "created_at": user.get("created_at") or user.get("createdAt"),
                        "updated_at": user.get("updated_at") or user.get("updatedAt")
                    }
                    standardized_user = {k: v for k, v in standardized_user.items() if v is not None}
                    standardized_users.append(standardized_user)
            
            return APIResponse.success(
                data=standardized_users,
                message="Users retrieved successfully", 
                meta={"count": len(standardized_users)}
            )
        else:
            return APIResponse.error("Invalid response format from service")
            
    except Exception as e:
        logger.error(f"Error standardizing user response: {e}")
        return APIResponse.error("Failed to process user data")
