from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer
from models import DriverModel, DriverResponse, DriverCreateRequest, DriverUpdateRequest, UserModel, UserResponse
from auth_utils import get_current_active_user
from bson import ObjectId
from typing import List, Optional
from database import db
import uuid

router = APIRouter()
drivers_collection = db.drivers
users_collection = db.users
security = HTTPBearer()


@router.post("/drivers", response_model=DriverResponse, status_code=status.HTTP_201_CREATED)
async def create_driver(
    driver_data: DriverCreateRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Create a new driver. This creates both a user entry and a driver entry.
    The user entry contains basic user information, the driver entry contains driver-specific details.
    """
    try:
        # Check if email already exists
        existing_user = await users_collection.find_one({"email": driver_data.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Check if license number already exists
        existing_driver = await drivers_collection.find_one({"license_number": driver_data.license_number})
        if existing_driver:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="License number already registered"
            )
        
        # Create user entry (drivers don't need passwords for now)
        user_dict = {
            "full_name": driver_data.full_name,
            "email": driver_data.email,
            "password": "",  # Empty password for drivers
            "role": driver_data.role,
            "phoneNo": driver_data.phoneNo,
            "details": {},
            "preferences": {
                "theme": "light",
                "animations": "true",
                "email_alerts": "true",
                "push_notifications": "true",
                "timezone": "UTC-5 (Eastern Time)",
                "date_format": "MM/DD/YYYY",
                "two_factor": "false",
                "activity_log": "true",
                "session_timeout": "30 minutes"
            }
        }
        
        # Insert user
        user_result = await users_collection.insert_one(user_dict)
        user_id = str(user_result.inserted_id)
        
        # Create driver entry
        driver_dict = {
            "user_id": user_id,
            "license_number": driver_data.license_number,
            "license_type": driver_data.license_type,
            "license_expiry": driver_data.license_expiry,
            "status": "available",
            "department": driver_data.department,
            "employee_id": driver_data.employee_id or f"EMP-{str(uuid.uuid4())[:8].upper()}",
            "joining_date": driver_data.joining_date,
            "emergency_contact": driver_data.emergency_contact,
            "rating": 0.0,
            "current_vehicle_id": None
        }
        
        # Insert driver
        driver_result = await drivers_collection.insert_one(driver_dict)
        driver_dict["_id"] = driver_result.inserted_id
        
        # Get user info for response
        user_info = await users_collection.find_one({"_id": ObjectId(user_id)})
        if user_info:
            user_info["_id"] = str(user_info["_id"])
            # Remove password from response
            user_info.pop("password", None)
        
        # Prepare response
        response_data = driver_dict.copy()
        response_data["id"] = str(driver_dict["_id"])
        response_data.pop("_id", None)
        response_data["user_info"] = user_info
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating driver: {str(e)}"
        )


@router.get("/drivers", response_model=List[DriverResponse])
async def get_drivers(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    department_filter: Optional[str] = None,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get all drivers with optional filtering
    """
    try:
        # Build filter query
        filter_query = {}
        if status_filter:
            filter_query["status"] = status_filter
        if department_filter:
            filter_query["department"] = department_filter
        
        # Get drivers
        drivers_cursor = drivers_collection.find(filter_query).skip(skip).limit(limit)
        drivers = await drivers_cursor.to_list(length=None)
        
        # Get user information for each driver
        drivers_with_user_info = []
        for driver in drivers:
            # Get user info
            user_info = await users_collection.find_one({"_id": ObjectId(driver["user_id"])})
            if user_info:
                user_info["_id"] = str(user_info["_id"])
                # Remove password from response
                user_info.pop("password", None)
            
            # Prepare driver response
            driver_response = driver.copy()
            driver_response["id"] = str(driver["_id"])
            driver_response.pop("_id", None)
            driver_response["user_info"] = user_info
            
            drivers_with_user_info.append(driver_response)
        
        return drivers_with_user_info
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching drivers: {str(e)}"
        )


@router.get("/drivers/{driver_id}", response_model=DriverResponse)
async def get_driver(
    driver_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get a specific driver by ID
    """
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(driver_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid driver ID format"
            )
        
        # Get driver
        driver = await drivers_collection.find_one({"_id": ObjectId(driver_id)})
        if not driver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Driver not found"
            )
        
        # Get user info
        user_info = await users_collection.find_one({"_id": ObjectId(driver["user_id"])})
        if user_info:
            user_info["_id"] = str(user_info["_id"])
            # Remove password from response
            user_info.pop("password", None)
        
        # Prepare response
        driver_response = driver.copy()
        driver_response["id"] = str(driver["_id"])
        driver_response.pop("_id", None)
        driver_response["user_info"] = user_info
        
        return driver_response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching driver: {str(e)}"
        )


@router.put("/drivers/{driver_id}", response_model=DriverResponse)
async def update_driver(
    driver_id: str,
    driver_update: DriverUpdateRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Update a driver's information
    """
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(driver_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid driver ID format"
            )
        
        # Check if driver exists
        existing_driver = await drivers_collection.find_one({"_id": ObjectId(driver_id)})
        if not existing_driver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Driver not found"
            )
        
        # Prepare update data (only include fields that are not None)
        update_data = {}
        for field, value in driver_update.model_dump(exclude_unset=True).items():
            if value is not None:
                update_data[field] = value
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields to update"
            )
        
        # Update driver
        result = await drivers_collection.update_one(
            {"_id": ObjectId(driver_id)},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No changes made to driver"
            )
        
        # Get updated driver
        updated_driver = await drivers_collection.find_one({"_id": ObjectId(driver_id)})
        
        # Get user info
        user_info = await users_collection.find_one({"_id": ObjectId(updated_driver["user_id"])})
        if user_info:
            user_info["_id"] = str(user_info["_id"])
            # Remove password from response
            user_info.pop("password", None)
        
        # Prepare response
        driver_response = updated_driver.copy()
        driver_response["id"] = str(updated_driver["_id"])
        driver_response.pop("_id", None)
        driver_response["user_info"] = user_info
        
        return driver_response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating driver: {str(e)}"
        )


@router.delete("/drivers/{driver_id}")
async def delete_driver(
    driver_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Delete a driver (and their associated user)
    """
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(driver_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid driver ID format"
            )
        
        # Get driver to find associated user
        driver = await drivers_collection.find_one({"_id": ObjectId(driver_id)})
        if not driver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Driver not found"
            )
        
        # Delete driver
        await drivers_collection.delete_one({"_id": ObjectId(driver_id)})
        
        # Delete associated user
        await users_collection.delete_one({"_id": ObjectId(driver["user_id"])})
        
        return {"message": "Driver deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting driver: {str(e)}"
        )


@router.get("/drivers/search/{query}")
async def search_drivers(
    query: str,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Search drivers by name, email, license number, or employee ID
    """
    try:
        # Get all drivers
        drivers = await drivers_collection.find({}).to_list(length=None)
        
        # Get user information and filter by search query
        matching_drivers = []
        for driver in drivers:
            # Get user info
            user_info = await users_collection.find_one({"_id": ObjectId(driver["user_id"])})
            if user_info:
                user_info["_id"] = str(user_info["_id"])
                # Remove password from response
                user_info.pop("password", None)
                
                # Check if query matches any field
                search_fields = [
                    user_info.get("full_name", "").lower(),
                    user_info.get("email", "").lower(),
                    driver.get("license_number", "").lower(),
                    driver.get("employee_id", "").lower(),
                    driver.get("department", "").lower()
                ]
                
                if any(query.lower() in field for field in search_fields):
                    # Prepare driver response
                    driver_response = driver.copy()
                    driver_response["id"] = str(driver["_id"])
                    driver_response.pop("_id", None)
                    driver_response["user_info"] = user_info
                    
                    matching_drivers.append(driver_response)
        
        return matching_drivers
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching drivers: {str(e)}"
        )
