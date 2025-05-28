from fastapi import APIRouter, HTTPException, Body, status
from models import VehicleModel, VehicleResponse
from bson import ObjectId
from database import db
from typing import List
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Function to get all the current vehicles
@router.get("/vehicles", response_model=List[VehicleResponse])
async def list_vehicles():
    try:
        vehicles = []
        async for vehicle in db.vehicles.find():
            vehicle["_id"] = str(vehicle["_id"])  # Convert ObjectId to string for JSON serialization
            vehicles.append(VehicleResponse(**vehicle))
        return vehicles
    except Exception as e:
        logger.error(f"Error fetching vehicles: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch vehicles")

# Function to add new vehicle
@router.post("/vehicles", response_model=VehicleResponse)
async def add_vehicle(vehicle: VehicleModel):
    try:
        # Convert the model to dict and remove the id field for insertion
        vehicle_dict = vehicle.dict(by_alias=True, exclude={"id"})
        
        # Check if vehicle with same VIN already exists
        existing_vehicle = await db.vehicles.find_one({"vin": vehicle_dict["vin"]})
        if existing_vehicle:
            raise HTTPException(status_code=400, detail="Vehicle with this VIN already exists")
        
        # Check if vehicle with same license plate already exists
        existing_plate = await db.vehicles.find_one({"license_plate": vehicle_dict["license_plate"]})
        if existing_plate:
            raise HTTPException(status_code=400, detail="Vehicle with this license plate already exists")
        
        result = await db.vehicles.insert_one(vehicle_dict)
        vehicle_dict["_id"] = str(result.inserted_id)
        
        return VehicleResponse(**vehicle_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding vehicle: {e}")
        raise HTTPException(status_code=500, detail="Failed to add vehicle")

