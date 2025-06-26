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

# Utility function to validate ObjectId
def validate_object_id(id_string: str, field_name: str = "ID") -> ObjectId:
    """Validate and convert string to ObjectId"""
    try:
        return ObjectId(id_string)
    except Exception:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid {field_name} format: {id_string}"
        )

# Response standardization function
def standardize_vehicle_response(vehicle: Dict[str, Any]) -> Dict[str, Any]:
    """Standardize vehicle response for frontend compatibility"""
    if not vehicle:
        return vehicle
    
    return {
        "id": str(vehicle.get("_id", "")),
        "make": vehicle.get("make", ""),
        "model": vehicle.get("model", ""),
        "year": vehicle.get("year", ""),
        "vin": vehicle.get("vin", ""),
        "licensePlate": vehicle.get("license_plate", ""),
        "color": vehicle.get("color", ""),
        "fuelType": vehicle.get("fuel_type", ""),
        "mileage": vehicle.get("current_mileage", 0),
        "status": "Active" if vehicle.get("is_active", True) else "Inactive",
        "driver": vehicle.get("driver_name", "Unassigned"),
        "driverId": vehicle.get("driver_id"),
        "department": vehicle.get("department", ""),
        "lastService": vehicle.get("last_service", ""),
        "nextService": vehicle.get("next_service", ""),
        "insuranceExpiry": vehicle.get("insurance_expiry", ""),
        "acquisitionDate": vehicle.get("acquisition_date", ""),
        "fuelEfficiency": vehicle.get("fuel_efficiency", ""),
        "tags": vehicle.get("tags", []),
        "lastDriver": vehicle.get("last_driver", "None"),
        "maintenanceCosts": vehicle.get("maintenance_costs", []),
        # Keep original fields for backward compatibility
        "_id": str(vehicle.get("_id", "")),
        "license_plate": vehicle.get("license_plate", ""),
        "fuel_type": vehicle.get("fuel_type", ""),
        "current_mileage": vehicle.get("current_mileage", 0),
        "is_active": vehicle.get("is_active", True),
        "driver_name": vehicle.get("driver_name", ""),
        "driver_id": vehicle.get("driver_id"),
        "created_at": vehicle.get("created_at"),
        "updated_at": vehicle.get("updated_at"),
    }

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

@router.get("/vehicle-assignments")
async def get_vehicle_assignments(
    skip: int = 0,
    limit: int = 100,
    vehicle_id: Optional[str] = None,
    driver_id: Optional[str] = None
):
    """Get vehicle assignments with optional filters"""
    try:
        from database import vehicle_assignments_collection
        
        # Build filter query
        query = {}
        if vehicle_id:
            query["vehicle_id"] = vehicle_id
        if driver_id:
            query["driver_id"] = driver_id
        
        # Get assignments with pagination
        cursor = vehicle_assignments_collection.find(query).skip(skip).limit(limit)
        assignments = []
        async for assignment in cursor:
            assignment["_id"] = str(assignment["_id"])
            assignments.append(assignment)
        
        # Get total count
        total = await vehicle_assignments_collection.count_documents(query)
        
        return {"assignments": assignments, "total": total}
        
    except Exception as e:
        logger.error(f"Error getting vehicle assignments: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve vehicle assignments")

@router.post("/vehicle-assignments")
async def create_vehicle_assignment(assignment_data: Dict[str, Any]):
    """Create a new vehicle assignment"""
    try:
        from database import vehicle_assignments_collection, get_vehicle_collection
        vehicles_collection = get_vehicle_collection()
        
        # Validate required fields
        if "vehicle_id" not in assignment_data or "driver_id" not in assignment_data:
            raise HTTPException(status_code=400, detail="vehicle_id and driver_id are required")
        
        # Validate vehicle exists
        vehicle_obj_id = validate_object_id(assignment_data["vehicle_id"], "vehicle ID")
        vehicle = await vehicles_collection.find_one({"_id": vehicle_obj_id})
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        # Add timestamp
        assignment_data["created_at"] = datetime.now(timezone.utc)
        assignment_data["updated_at"] = datetime.now(timezone.utc)
        assignment_data["status"] = assignment_data.get("status", "active")
        
        # Insert assignment
        result = await vehicle_assignments_collection.insert_one(assignment_data)
        
        # Update vehicle with driver assignment
        await vehicles_collection.update_one(
            {"_id": vehicle_obj_id},
            {"$set": {
                "driver_id": assignment_data["driver_id"],
                "driver_name": assignment_data.get("driver_name", ""),
                "updated_at": datetime.now(timezone.utc)
            }}
        )
        
        # Get created assignment
        created_assignment = await vehicle_assignments_collection.find_one({"_id": result.inserted_id})
        created_assignment["_id"] = str(created_assignment["_id"])
        
        return {"assignment": created_assignment, "message": "Vehicle assignment created successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating vehicle assignment: {e}")
        raise HTTPException(status_code=500, detail="Failed to create vehicle assignment")

@router.put("/vehicle-assignments/{assignment_id}")
async def update_vehicle_assignment(assignment_id: str, assignment_data: Dict[str, Any]):
    """Update vehicle assignment. If assignment is completed (vehicle returned), return analytics."""
    try:
        from database import vehicle_assignments_collection
        # Import analytics functions directly
        from analytics import (
            fleet_utilization, vehicle_usage, assignment_metrics, maintenance_analytics,
            driver_performance, cost_analytics, status_breakdown, incident_statistics, department_location_analytics
        )
        # Validate ObjectId format
        obj_id = validate_object_id(assignment_id, "assignment ID")
        # Add update timestamp
        assignment_data["updated_at"] = datetime.now(timezone.utc)
        # Update assignment
        result = await vehicle_assignments_collection.update_one(
            {"_id": obj_id},
            {"$set": assignment_data}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Vehicle assignment not found")
        # Get updated assignment
        updated_assignment = await vehicle_assignments_collection.find_one({"_id": obj_id})
        updated_assignment["_id"] = str(updated_assignment["_id"])
        # If assignment is completed (vehicle returned), return analytics
        if assignment_data.get("status", "").lower() == "completed":
            analytics = {}
            analytics["fleet_utilization"] = await fleet_utilization()
            analytics["vehicle_usage"] = await vehicle_usage()
            analytics["assignment_metrics"] = await assignment_metrics()
            analytics["maintenance_analytics"] = await maintenance_analytics()
            analytics["driver_performance"] = await driver_performance()
            analytics["cost_analytics"] = await cost_analytics()
            analytics["status_breakdown"] = await status_breakdown()
            analytics["incident_statistics"] = await incident_statistics()
            analytics["department_location_analytics"] = await department_location_analytics()
            return {
                "assignment": updated_assignment,
                "message": "Vehicle assignment updated successfully. Vehicle returned.",
                "analytics": analytics
            }
        return {"assignment": updated_assignment, "message": "Vehicle assignment updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating vehicle assignment: {e}")
        raise HTTPException(status_code=500, detail="Failed to update vehicle assignment")

@router.delete("/vehicle-assignments/{assignment_id}")
async def delete_vehicle_assignment(assignment_id: str):
    """Delete vehicle assignment"""
    try:
        from database import vehicle_assignments_collection, get_vehicle_collection
        vehicles_collection = get_vehicle_collection()
        
        # Validate ObjectId format
        obj_id = validate_object_id(assignment_id, "assignment ID")
        
        # Get assignment to find vehicle_id
        assignment = await vehicle_assignments_collection.find_one({"_id": obj_id})
        if not assignment:
            raise HTTPException(status_code=404, detail="Vehicle assignment not found")
        
        # Delete assignment
        result = await vehicle_assignments_collection.delete_one({"_id": obj_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Vehicle assignment not found")
        
        # Remove driver assignment from vehicle
        if "vehicle_id" in assignment:
            vehicle_obj_id = validate_object_id(assignment["vehicle_id"], "vehicle ID")
            await vehicles_collection.update_one(
                {"_id": vehicle_obj_id},
                {"$unset": {"driver_id": "", "driver_name": ""},
                 "$set": {"updated_at": datetime.now(timezone.utc)}}
            )
        
        return {"message": "Vehicle assignment deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting vehicle assignment: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete vehicle assignment")

# Vehicle Management Routes

@router.get("/vehicles")
async def get_vehicles(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    make_filter: Optional[str] = None
):
    """Get all vehicles with optional filters and include analytics in the response."""
    try:
        from database import get_vehicle_collection
        # Import analytics functions directly
        from analytics import (
            fleet_utilization, vehicle_usage, assignment_metrics, maintenance_analytics,
            driver_performance, cost_analytics, status_breakdown, incident_statistics, department_location_analytics
        )
        vehicles_collection = get_vehicle_collection()
        # Build filter query
        query = {}
        if status_filter:
            # Note: vehicles use is_active instead of status
            if status_filter.lower() == "active":
                query["is_active"] = True
            elif status_filter.lower() == "inactive":
                query["is_active"] = False
        if make_filter:
            query["make"] = {"$regex": make_filter, "$options": "i"}
        # Get vehicles with pagination
        cursor = vehicles_collection.find(query).skip(skip).limit(limit)
        vehicles = []
        async for vehicle in cursor:
            standardized_vehicle = standardize_vehicle_response(vehicle)
            vehicles.append(standardized_vehicle)
        # Get total count
        total = await vehicles_collection.count_documents(query)
        # Get analytics
        analytics = {}
        analytics["fleet_utilization"] = await fleet_utilization()
        analytics["vehicle_usage"] = await vehicle_usage()
        analytics["assignment_metrics"] = await assignment_metrics()
        analytics["maintenance_analytics"] = await maintenance_analytics()
        analytics["driver_performance"] = await driver_performance()
        analytics["cost_analytics"] = await cost_analytics()
        analytics["status_breakdown"] = await status_breakdown()
        analytics["incident_statistics"] = await incident_statistics()
        analytics["department_location_analytics"] = await department_location_analytics()
        return {"vehicles": vehicles, "total": total, "analytics": analytics}
    except Exception as e:
        logger.error(f"Error getting vehicles: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve vehicles")

@router.post("/vehicles")
async def create_vehicle(vehicle_data: Dict[str, Any]):
    """Create a new vehicle"""
    try:
        from database import get_vehicle_collection
        vehicles_collection = get_vehicle_collection()
        
        # Add timestamp and ensure required fields are present
        vehicle_data["created_at"] = datetime.now(timezone.utc)
        vehicle_data["updated_at"] = datetime.now(timezone.utc)
        
        # Set defaults for required fields if not provided
        if "current_mileage" not in vehicle_data:
            vehicle_data["current_mileage"] = 0.0
        if "is_active" not in vehicle_data:
            vehicle_data["is_active"] = True
        
        # Insert vehicle
        result = await vehicles_collection.insert_one(vehicle_data)
        
        # Get created vehicle
        created_vehicle = await vehicles_collection.find_one({"_id": result.inserted_id})
        standardized_vehicle = standardize_vehicle_response(created_vehicle)
        
        return {"vehicle": standardized_vehicle, "message": "Vehicle created successfully"}
        
    except Exception as e:
        logger.error(f"Error creating vehicle: {e}")
        raise HTTPException(status_code=500, detail="Failed to create vehicle")

@router.get("/vehicles/{vehicle_id}")
async def get_vehicle(vehicle_id: str):
    """Get specific vehicle"""
    try:
        from database import get_vehicle_collection
        vehicles_collection = get_vehicle_collection()
        
        # Validate ObjectId format
        obj_id = validate_object_id(vehicle_id, "vehicle ID")
        
        # Get vehicle by ID
        vehicle = await vehicles_collection.find_one({"_id": obj_id})
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        standardized_vehicle = standardize_vehicle_response(vehicle)
        return {"vehicle": standardized_vehicle}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting vehicle: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve vehicle")

@router.put("/vehicles/{vehicle_id}")
async def update_vehicle(vehicle_id: str, vehicle_data: Dict[str, Any]):
    """Update vehicle"""
    try:
        from database import get_vehicle_collection
        vehicles_collection = get_vehicle_collection()
        
        # Validate ObjectId format
        obj_id = validate_object_id(vehicle_id, "vehicle ID")
        
        # Add update timestamp
        vehicle_data["updated_at"] = datetime.now(timezone.utc)
        
        # Update vehicle
        result = await vehicles_collection.update_one(
            {"_id": obj_id},
            {"$set": vehicle_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        # Get updated vehicle
        updated_vehicle = await vehicles_collection.find_one({"_id": obj_id})
        standardized_vehicle = standardize_vehicle_response(updated_vehicle)
        
        return {"vehicle": standardized_vehicle, "message": "Vehicle updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating vehicle: {e}")
        raise HTTPException(status_code=500, detail="Failed to update vehicle")

@router.delete("/vehicles/{vehicle_id}")
async def delete_vehicle(vehicle_id: str):
    """Delete vehicle"""
    try:
        from database import get_vehicle_collection
        vehicles_collection = get_vehicle_collection()
        
        # Validate ObjectId format
        obj_id = validate_object_id(vehicle_id, "vehicle ID")
        
        # Delete vehicle
        result = await vehicles_collection.delete_one({"_id": obj_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        return {"message": "Vehicle deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting vehicle: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete vehicle")

@router.get("/vehicles/search/{query}")
async def search_vehicles(query: str, limit: int = 50):
    """Search vehicles by make, model, vehicle_number, or license plate, and include analytics in the response."""
    try:
        from database import get_vehicle_collection
        # Import analytics functions directly
        from analytics import (
            fleet_utilization, vehicle_usage, assignment_metrics, maintenance_analytics,
            driver_performance, cost_analytics, status_breakdown, incident_statistics, department_location_analytics
        )
        vehicles_collection = get_vehicle_collection()
        # Create search query (case-insensitive partial match)
        search_query = {
            "$or": [
                {"make": {"$regex": query, "$options": "i"}},
                {"model": {"$regex": query, "$options": "i"}},
                {"vehicle_number": {"$regex": query, "$options": "i"}},
                {"license_plate": {"$regex": query, "$options": "i"}},
                {"vin": {"$regex": query, "$options": "i"}}
            ]
        }
        # Find matching vehicles
        cursor = vehicles_collection.find(search_query).limit(limit)
        vehicles = []
        async for vehicle in cursor:
            standardized_vehicle = standardize_vehicle_response(vehicle)
            vehicles.append(standardized_vehicle)
        # Get analytics
        analytics = {}
        analytics["fleet_utilization"] = await fleet_utilization()
        analytics["vehicle_usage"] = await vehicle_usage()
        analytics["assignment_metrics"] = await assignment_metrics()
        analytics["maintenance_analytics"] = await maintenance_analytics()
        analytics["driver_performance"] = await driver_performance()
        analytics["cost_analytics"] = await cost_analytics()
        analytics["status_breakdown"] = await status_breakdown()
        analytics["incident_statistics"] = await incident_statistics()
        analytics["department_location_analytics"] = await department_location_analytics()
        return {"vehicles": vehicles, "total": len(vehicles), "analytics": analytics}
    except Exception as e:
        logger.error(f"Error searching vehicles: {e}")
        raise HTTPException(status_code=500, detail="Failed to search vehicles")
