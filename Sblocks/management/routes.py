from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
import json
import logging
import requests
import os
from bson import ObjectId

from models import (
    VehicleAssignment, VehicleUsageLog, VehicleStatus, 
    VehicleAssignmentResponse
)
from auth_utils import (
    require_permission, require_role, get_current_user, 
    filter_data_by_role, can_access_resource
)

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

# Driver Management Routes

@router.get("/drivers")
async def get_drivers(limit: int = 100):
    """Get all drivers"""
    try:
        from database import get_driver_collection
        drivers_collection = get_driver_collection()
        
        # Get drivers with limit
        cursor = drivers_collection.find({}).limit(limit)
        drivers = []
        async for driver in cursor:
            driver["_id"] = str(driver["_id"])
            drivers.append(driver)
        
        return {"drivers": drivers, "total": len(drivers)}
        
    except Exception as e:
        logger.error(f"Error getting drivers: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve drivers")

@router.post("/drivers")
async def create_driver(driver_data: Dict[str, Any]):
    """Create a new driver"""
    try:
        from database import get_driver_collection
        drivers_collection = get_driver_collection()
        
        # Add timestamp
        driver_data["created_at"] = datetime.now(timezone.utc)
        driver_data["updated_at"] = datetime.now(timezone.utc)
        
        # Insert driver
        result = await drivers_collection.insert_one(driver_data)
        
        # Get created driver
        created_driver = await drivers_collection.find_one({"_id": result.inserted_id})
        created_driver["_id"] = str(created_driver["_id"])
        
        return {"driver": created_driver, "message": "Driver created successfully"}
        
    except Exception as e:
        logger.error(f"Error creating driver: {e}")
        raise HTTPException(status_code=500, detail="Failed to create driver")

@router.get("/drivers/{driver_id}")
async def get_driver(driver_id: str):
    """Get specific driver"""
    try:
        from database import get_driver_collection
        drivers_collection = get_driver_collection()
        
        # Get driver by ID
        driver = await drivers_collection.find_one({"_id": ObjectId(driver_id)})
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
        
        driver["_id"] = str(driver["_id"])
        return {"driver": driver}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting driver: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve driver")

@router.put("/drivers/{driver_id}")
async def update_driver(driver_id: str, driver_data: Dict[str, Any]):
    """Update driver"""
    try:
        from database import get_driver_collection
        drivers_collection = get_driver_collection()
        
        # Add update timestamp
        driver_data["updated_at"] = datetime.now(timezone.utc)
        
        # Update driver
        result = await drivers_collection.update_one(
            {"_id": ObjectId(driver_id)},
            {"$set": driver_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Driver not found")
        
        # Get updated driver
        updated_driver = await drivers_collection.find_one({"_id": ObjectId(driver_id)})
        updated_driver["_id"] = str(updated_driver["_id"])
        
        return {"driver": updated_driver, "message": "Driver updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating driver: {e}")
        raise HTTPException(status_code=500, detail="Failed to update driver")

@router.delete("/drivers/{driver_id}")
async def delete_driver(driver_id: str):
    """Delete driver"""
    try:
        from database import get_driver_collection
        drivers_collection = get_driver_collection()
        
        # Delete driver
        result = await drivers_collection.delete_one({"_id": ObjectId(driver_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Driver not found")
        
        return {"message": "Driver deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting driver: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete driver")

# Vehicle Assignment Routes
