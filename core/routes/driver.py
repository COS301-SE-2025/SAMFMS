from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer
from models import DriverModel, DriverResponse, DriverCreateRequest, DriverUpdateRequest, UserModel, UserResponse
from auth_utils import get_current_active_user
from bson import ObjectId
from typing import List, Optional
from database import db
import uuid
import random
import re

router = APIRouter()
drivers_collection = db.drivers
users_collection = db.users
security = HTTPBearer()


def validate_sa_phone_number(phone: str) -> bool:
    """
    Validate South African phone number format
    Accepts: +27123456789, 0123456789
    """
    if not phone:
        return True  # Optional field
    
    # Remove spaces and normalize
    phone_clean = re.sub(r'\s+', '', phone)
    
    # SA phone regex: +27 followed by 9 digits or 0 followed by 9 digits
    sa_phone_regex = r'^(\+27|0)[1-9][0-9]{8}$'
    
    return bool(re.match(sa_phone_regex, phone_clean))


def validate_sa_license_number(license_number: str) -> bool:
    """
    Validate South African license number format
    SA license numbers are typically 13 digits
    """
    if not license_number:
        return False
    
    # Remove spaces and normalize
    license_clean = re.sub(r'\s+', '', license_number)
    
    # SA license regex: 13 digits
    sa_license_regex = r'^[0-9]{13}$'
    
    return bool(re.match(sa_license_regex, license_clean))


async def generate_unique_employee_id():
    """
    Generate a unique 6-digit employee ID with format EMP-XXXXXX
    where XXXXXX is a 6-digit number
    """
    max_attempts = 100  # Prevent infinite loop
    attempts = 0
    
    while attempts < max_attempts:
        # Generate a 6-digit number (100000 to 999999)
        employee_number = random.randint(100000, 999999)
        employee_id = f"EMP-{employee_number}"
        
        # Check if this employee ID already exists
        existing_driver = await drivers_collection.find_one({"employee_id": employee_id})
        if not existing_driver:
            return employee_id
        
        attempts += 1
    
    # If we couldn't generate a unique ID after max_attempts, use timestamp fallback
    import time
    timestamp_id = f"EMP-{int(time.time()) % 1000000:06d}"
    return timestamp_id


def validate_sa_phone_number(phone_number: str) -> bool:
    """
    Validate South African phone number format
    Accepts: +27123456789 or 0123456789 (with or without spaces)
    """
    if not phone_number:
        return True  # Optional field
    
    # Remove spaces and other formatting
    clean_phone = phone_number.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    
    # South African phone number regex
    # +27 followed by 9 digits or 0 followed by 9 digits
    import re
    sa_phone_pattern = r'^(\+27|0)[1-9][0-9]{8}$'
    
    return bool(re.match(sa_phone_pattern, clean_phone))


def validate_sa_license_number(license_number: str) -> bool:
    """
    Validate South African driver's license number format
    SA license numbers are typically 13 digits
    """
    if not license_number:
        return False
    
    # Remove spaces and other formatting
    clean_license = license_number.replace(" ", "").replace("-", "")
    
    # SA license number should be 13 digits
    import re
    sa_license_pattern = r'^[0-9]{13}$'
    
    return bool(re.match(sa_license_pattern, clean_license))


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
        # Validate phone numbers (South African format)
        if driver_data.phoneNo and not validate_sa_phone_number(driver_data.phoneNo):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid phone number format. Please use SA format: +27123456789 or 0123456789"
            )
            
        if driver_data.emergency_contact and not validate_sa_phone_number(driver_data.emergency_contact):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid emergency contact format. Please use SA format: +27123456789 or 0123456789"
            )
        
        # Validate license number (South African format)
        if not validate_sa_license_number(driver_data.license_number):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid license number format. SA license numbers must be 13 digits"
            )
        
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
          # Generate unique 6-digit employee ID
        employee_id = await generate_unique_employee_id()
        
        # Create driver entry
        driver_dict = {
            "user_id": user_id,
            "license_number": driver_data.license_number,
            "license_type": driver_data.license_type,
            "license_expiry": driver_data.license_expiry,
            "status": "available",
            "department": driver_data.department,
            "employee_id": employee_id,
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
