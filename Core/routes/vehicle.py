from fastapi import APIRouter, HTTPException, Body
from models import UserModel
from bson import ObjectId
from database import db

router = APIRouter()

# Function to get all the current vehicles
@router.get("/vehicles")
async def list_vehicles():
    vehicles = []
    async for vehicle in db.vehicles.find():
        vehicle["_id"] = str(vehicle["_id"])  # Convert ObjectId to string for JSON serialization
        vehicles.append(vehicle)
    return vehicles

# Function to add new vehicle
@router.post("/vehicles")
async def add_vehicle(vehicle: dict = Body(...)):
    result = await db.vehicles.insert_one(vehicle)
    vehicle["_id"] = str(result.inserted_id)
    return vehicle

