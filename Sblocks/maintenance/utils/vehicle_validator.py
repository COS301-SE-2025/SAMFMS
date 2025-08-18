"""
Vehicle validation utilities for maintenance service
"""

import logging
import os
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from bson.errors import InvalidId

logger = logging.getLogger(__name__)


class VehicleValidator:
    """Validates vehicle IDs against the vehicles collection"""
    
    def __init__(self):
        self.client = None
        self.vehicles_db = None
        self.vehicles_collection = None
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize connection to the management database"""
        try:
            # Use the same MongoDB URL but connect to management database
            mongodb_url = os.getenv(
                "MONGODB_URL", 
                "mongodb://samfms_admin:SafeMongoPass2025%21SecureDB%40SAMFMS@mongodb:27017"
            )
            self.client = AsyncIOMotorClient(mongodb_url)
            # Connect to the management database where vehicles are stored
            self.vehicles_db = self.client["samfms_management"]
            self.vehicles_collection = self.vehicles_db["vehicles"]
            logger.info("Initialized vehicle validator connection to management database")
        except Exception as e:
            logger.error(f"Failed to initialize vehicle validator: {e}")
            raise
    
    async def validate_vehicle_id(self, vehicle_id: str) -> bool:
        """
        Validate that a vehicle_id exists in the vehicles collection
        
        Args:
            vehicle_id: The vehicle ID to validate (can be ObjectId string or regular ID)
            
        Returns:
            bool: True if vehicle exists, False otherwise
        """
        if not vehicle_id:
            return False
            
        try:
            # Build query to check multiple possible ID fields
            query_conditions = []
            
            # Check if it's a valid ObjectId string
            try:
                if len(vehicle_id) == 24 and all(c in '0123456789abcdefABCDEF' for c in vehicle_id):
                    from bson import ObjectId
                    query_conditions.append({"_id": ObjectId(vehicle_id)})
            except Exception:
                pass
            
            # Also check by string fields
            query_conditions.extend([
                {"_id": vehicle_id},
                {"id": vehicle_id},
                {"vehicle_id": vehicle_id}
            ])
            
            # Use $or to check any of these conditions
            query = {"$or": query_conditions}
            
            # Check if vehicle exists
            vehicle = await self.vehicles_collection.find_one(query)
            exists = vehicle is not None
            
            if not exists:
                logger.warning(f"Vehicle ID {vehicle_id} not found in vehicles collection")
            else:
                logger.debug(f"Vehicle ID {vehicle_id} validated successfully")
                
            return exists
            
        except Exception as e:
            logger.error(f"Error validating vehicle ID {vehicle_id}: {e}")
            return False
    
    async def get_vehicle_details(self, vehicle_id: str) -> Optional[dict]:
        """
        Get vehicle details for a given vehicle_id
        
        Args:
            vehicle_id: The vehicle ID to lookup (can be ObjectId string or regular ID)
            
        Returns:
            dict: Vehicle details if found, None otherwise
        """
        if not vehicle_id:
            return None
            
        try:
            # Build query to check multiple possible ID fields
            query_conditions = []
            
            # Check if it's a valid ObjectId string
            try:
                if len(vehicle_id) == 24 and all(c in '0123456789abcdefABCDEF' for c in vehicle_id):
                    from bson import ObjectId
                    query_conditions.append({"_id": ObjectId(vehicle_id)})
            except Exception:
                pass
            
            # Also check by string fields
            query_conditions.extend([
                {"_id": vehicle_id},
                {"id": vehicle_id},
                {"vehicle_id": vehicle_id}
            ])
            
            # Use $or to check any of these conditions
            query = {"$or": query_conditions}
            
            vehicle = await self.vehicles_collection.find_one(query)
            
            if vehicle and "_id" in vehicle:
                # Convert ObjectId to string for JSON serialization and add id field
                vehicle["_id"] = str(vehicle["_id"])
                vehicle["id"] = vehicle["_id"]  # Add id field for frontend compatibility
                
            return vehicle
            
        except Exception as e:
            logger.error(f"Error getting vehicle details for {vehicle_id}: {e}")
            return None
    
    async def validate_multiple_vehicle_ids(self, vehicle_ids: list) -> dict:
        """
        Validate multiple vehicle IDs at once
        
        Args:
            vehicle_ids: List of vehicle IDs to validate
            
        Returns:
            dict: {"valid": [valid_ids], "invalid": [invalid_ids]}
        """
        valid_ids = []
        invalid_ids = []
        
        for vehicle_id in vehicle_ids:
            if await self.validate_vehicle_id(vehicle_id):
                valid_ids.append(vehicle_id)
            else:
                invalid_ids.append(vehicle_id)
        
        return {
            "valid": valid_ids,
            "invalid": invalid_ids
        }
    
    async def close_connection(self):
        """Close the database connection"""
        if self.client:
            self.client.close()
            logger.info("Closed vehicle validator database connection")


# Global instance
vehicle_validator = VehicleValidator()
