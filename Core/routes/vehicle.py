from fastapi import APIRouter, HTTPException, Body, Depends, status
from models import VehicleModel, VehicleResponse, VehicleUpdateRequest
from auth_utils import get_current_active_user
from bson import ObjectId
from database import db
from typing import List, Optional, Dict, Any
import logging
import re

logger = logging.getLogger(__name__)
router = APIRouter()

# Validator function for license plate
def validate_license_plate(plate: str) -> bool:
    """
    Validate South African license plate format
    """
    if not plate:
        return False
    
    # Remove spaces and normalize
    plate_clean = re.sub(r'\s+', '', plate)
    
    # Basic validation - can be expanded based on specific requirements
    return len(plate_clean) >= 4 and len(plate_clean) <= 10

# Validator function for VIN
def validate_vin(vin: str) -> bool:
    """
    Validate Vehicle Identification Number
    Standard VIN is 17 characters
    """
    if not vin:
        return False
    
    # Remove spaces and normalize
    vin_clean = re.sub(r'\s+', '', vin.upper())
    
    # Basic VIN validation - should be 17 characters
    return len(vin_clean) == 17

# Function to get all the current vehicles
@router.get("/vehicles", response_model=List[VehicleResponse])
async def list_vehicles(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    make_filter: Optional[str] = None,
    current_user: dict = Depends(get_current_active_user)
):
    try:
        # Build filter query
        filter_query = {}
        if status_filter:
            filter_query["status"] = status_filter
        if make_filter:
            filter_query["make"] = make_filter
            
        # Get vehicles with pagination
        vehicles_cursor = db.vehicles.find(filter_query).skip(skip).limit(limit)
        vehicles = []
        
        async for vehicle in vehicles_cursor:
            vehicle["_id"] = str(vehicle["_id"])  # Convert ObjectId to string for JSON serialization
            
            # If a vehicle has a driver_id, get the driver's name
            if vehicle.get("driver_id"):
                try:
                    driver = await db.drivers.find_one({"_id": ObjectId(vehicle["driver_id"])})
                    if driver:
                        user = await db.users.find_one({"_id": ObjectId(driver["user_id"])})
                        if user:
                            vehicle["driver_name"] = user.get("full_name", "Unknown")
                except Exception as e:
                    logger.error(f"Error fetching driver for vehicle: {e}")
                    vehicle["driver_name"] = "Unknown"
            
            vehicles.append(VehicleResponse(**vehicle))
            
        return vehicles
    except Exception as e:
        logger.error(f"Error fetching vehicles: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch vehicles")

# Function to get a specific vehicle
@router.get("/vehicles/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(
    vehicle_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(vehicle_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid vehicle ID format"
            )
        
        # Get vehicle
        vehicle = await db.vehicles.find_one({"_id": ObjectId(vehicle_id)})
        if not vehicle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehicle not found"
            )
        
        # Convert ObjectId to string for JSON serialization
        vehicle["_id"] = str(vehicle["_id"])
        
        # Get driver information if available
        if vehicle.get("driver_id"):
            try:
                driver = await db.drivers.find_one({"_id": ObjectId(vehicle["driver_id"])})
                if driver:
                    user = await db.users.find_one({"_id": ObjectId(driver["user_id"])})
                    if user:
                        vehicle["driver_name"] = user.get("full_name", "Unknown")
            except Exception as e:
                logger.error(f"Error fetching driver for vehicle: {e}")
        
        return VehicleResponse(**vehicle)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching vehicle: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch vehicle: {str(e)}")

# Function to add new vehicle
@router.post("/vehicles", response_model=VehicleResponse)
async def add_vehicle(
    vehicle: VehicleModel,
    current_user: dict = Depends(get_current_active_user)
):
    try:
        # Convert the model to dict and remove the id field for insertion
        vehicle_dict = vehicle.dict(by_alias=True, exclude={"id"})
        
        # Validate VIN
        if not validate_vin(vehicle_dict["vin"]):
            raise HTTPException(
                status_code=400, 
                detail="Invalid VIN format. VIN must be 17 characters."
            )
            
        # Validate license plate
        if not validate_license_plate(vehicle_dict["license_plate"]):
            raise HTTPException(
                status_code=400, 
                detail="Invalid license plate format."
            )
        
        # Check if vehicle with same VIN already exists
        existing_vehicle = await db.vehicles.find_one({"vin": vehicle_dict["vin"]})
        if existing_vehicle:
            raise HTTPException(status_code=400, detail="Vehicle with this VIN already exists")
        
        # Check if vehicle with same license plate already exists
        existing_plate = await db.vehicles.find_one({"license_plate": vehicle_dict["license_plate"]})
        if existing_plate:
            raise HTTPException(status_code=400, detail="Vehicle with this license plate already exists")
        
        # Set default values if not provided
        if "status" not in vehicle_dict:
            vehicle_dict["status"] = "active"
            
        # Insert the vehicle
        result = await db.vehicles.insert_one(vehicle_dict)
        vehicle_dict["_id"] = str(result.inserted_id)
        
        return VehicleResponse(**vehicle_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding vehicle: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add vehicle: {str(e)}")

# Function to delete a vehicle
@router.delete("/vehicles/{vehicle_id}", response_model=Dict[str, Any])
async def delete_vehicle(
    vehicle_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(vehicle_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid vehicle ID format"
            )
        
        # Check if vehicle exists
        vehicle = await db.vehicles.find_one({"_id": ObjectId(vehicle_id)})
        if not vehicle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehicle not found"
            )
        
        # Delete the vehicle
        result = await db.vehicles.delete_one({"_id": ObjectId(vehicle_id)})
        
        if result.deleted_count == 1:
            return {"success": True, "message": "Vehicle successfully deleted"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete vehicle"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting vehicle: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete vehicle: {str(e)}")

