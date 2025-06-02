from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import json
import logging
import requests
import os

from .models import (
    VehicleAssignment, VehicleUsage, VehicleStatus, 
    VehicleAssignmentCreate, VehicleAssignmentUpdate,
    VehicleUsageCreate, VehicleUsageUpdate,
    VehicleStatusCreate, VehicleStatusUpdate,
    VehicleAssignmentResponse, VehicleUsageResponse, VehicleStatusResponse,
    DriverModel, DriverCreateRequest, DriverUpdateRequest, DriverResponse
)
from .database import get_db, log_vehicle_activity, get_driver_collection
from .message_queue import publish_vehicle_event
from .auth_utils import (
    require_permission, require_role, get_current_user, 
    filter_data_by_role, can_access_resource
)

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

# Vehicle Assignment Routes
@router.post("/assignments", response_model=VehicleAssignmentResponse)
@require_permission("assignments:write")
async def create_assignment(
    assignment: VehicleAssignmentCreate,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: Dict[str, Any] = None
):
    """Create a new vehicle assignment"""
    try:
        # Create assignment record
        db_assignment = VehicleAssignment(
            vehicle_id=assignment.vehicle_id,
            user_id=assignment.user_id,
            assigned_by=assignment.assigned_by,
            assignment_date=assignment.assignment_date or datetime.now(timezone.utc),
            expected_return_date=assignment.expected_return_date,
            purpose=assignment.purpose,
            location=assignment.location,
            status="active"
        )
        db.add(db_assignment)
        db.commit()
        db.refresh(db_assignment)
        
        # Log activity
        await log_vehicle_activity(
            vehicle_id=assignment.vehicle_id,
            activity_type="assignment_created",
            details=f"Assigned to user {assignment.user_id}",
            user_id=assignment.assigned_by
        )
        
        # Publish vehicle event
        await publish_vehicle_event({
            "event_type": "assignment_created",
            "vehicle_id": assignment.vehicle_id,
            "user_id": assignment.user_id,
            "assignment_id": db_assignment.id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return db_assignment
        
    except Exception as e:
        logger.error(f"Error creating assignment: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create assignment")

@router.get("/assignments", response_model=List[VehicleAssignmentResponse])
@require_permission("assignments:read")
async def get_assignments(
    vehicle_id: Optional[int] = None,
    user_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: Dict[str, Any] = None
):
    """Get vehicle assignments with optional filters"""
    query = db.query(VehicleAssignment)
    
    # Role-based filtering
    user_role = current_user.get("role", "")
    current_user_id = current_user.get("user_id")
    
    if user_role == "driver":
        # Drivers can only see their own assignments
        query = query.filter(VehicleAssignment.user_id == current_user_id)
    elif user_id and user_role in ["admin", "fleet_manager"]:
        # Admin and fleet managers can filter by user_id
        query = query.filter(VehicleAssignment.user_id == user_id)
    
    if vehicle_id:
        query = query.filter(VehicleAssignment.vehicle_id == vehicle_id)
    if status:
        query = query.filter(VehicleAssignment.status == status)
    
    assignments = query.offset(skip).limit(limit).all()
    return assignments

@router.get("/assignments/{assignment_id}", response_model=VehicleAssignmentResponse)
@require_permission("assignments:read")
async def get_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: Dict[str, Any] = None
):
    """Get specific vehicle assignment"""
    assignment = db.query(VehicleAssignment).filter(VehicleAssignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    # Check if user can access this assignment
    if not can_access_resource(current_user, str(assignment.user_id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this assignment"
        )
    
    return assignment

@router.put("/assignments/{assignment_id}", response_model=VehicleAssignmentResponse)
@require_permission("assignments:write")
async def update_assignment(
    assignment_id: int,
    assignment_update: VehicleAssignmentUpdate,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: Dict[str, Any] = None
):
    """Update vehicle assignment"""
    try:
        db_assignment = db.query(VehicleAssignment).filter(VehicleAssignment.id == assignment_id).first()
        if not db_assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        # Check if user can update this assignment
        if not can_access_resource(current_user, str(db_assignment.user_id)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to update this assignment"
            )
        
        # Update fields
        update_data = assignment_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_assignment, field, value)
        
        db_assignment.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(db_assignment)
        
        # Log activity
        await log_vehicle_activity(
            vehicle_id=db_assignment.vehicle_id,
            activity_type="assignment_updated",
            details=f"Assignment {assignment_id} updated",
            user_id=assignment_update.updated_by if hasattr(assignment_update, 'updated_by') else None
        )
        
        # Publish vehicle event
        await publish_vehicle_event({
            "event_type": "assignment_updated",
            "vehicle_id": db_assignment.vehicle_id,
            "assignment_id": assignment_id,
            "changes": update_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return db_assignment
        
    except Exception as e:
        logger.error(f"Error updating assignment: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update assignment")

@router.delete("/assignments/{assignment_id}")
@require_permission("assignments:delete")
async def delete_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: Dict[str, Any] = None
):
    """Delete vehicle assignment"""
    try:
        db_assignment = db.query(VehicleAssignment).filter(VehicleAssignment.id == assignment_id).first()
        if not db_assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        # Check if user can delete this assignment
        if not can_access_resource(current_user, str(db_assignment.user_id)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to delete this assignment"
            )
        
        vehicle_id = db_assignment.vehicle_id
        db.delete(db_assignment)
        db.commit()
        
        # Log activity
        await log_vehicle_activity(
            vehicle_id=vehicle_id,
            activity_type="assignment_deleted",
            details=f"Assignment {assignment_id} deleted"
        )
        
        # Publish vehicle event
        await publish_vehicle_event({
            "event_type": "assignment_deleted",
            "vehicle_id": vehicle_id,
            "assignment_id": assignment_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {"message": "Assignment deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting assignment: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete assignment")

# Vehicle Usage Routes
@router.post("/usage", response_model=VehicleUsageResponse)
@require_permission("usage:write")
async def create_usage_record(
    usage: VehicleUsageCreate,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: Dict[str, Any] = None
):
    """Create a new vehicle usage record"""
    try:
        db_usage = VehicleUsage(
            vehicle_id=usage.vehicle_id,
            user_id=usage.user_id,
            start_time=usage.start_time,
            end_time=usage.end_time,
            start_mileage=usage.start_mileage,
            end_mileage=usage.end_mileage,
            purpose=usage.purpose,
            route=usage.route,
            fuel_consumed=usage.fuel_consumed,
            notes=usage.notes
        )
        db.add(db_usage)
        db.commit()
        db.refresh(db_usage)
        
        # Log activity
        await log_vehicle_activity(
            vehicle_id=usage.vehicle_id,
            activity_type="usage_recorded",
            details=f"Usage recorded by user {usage.user_id}",
            user_id=usage.user_id
        )
        
        # Publish vehicle event
        await publish_vehicle_event({
            "event_type": "usage_recorded",
            "vehicle_id": usage.vehicle_id,
            "user_id": usage.user_id,
            "usage_id": db_usage.id,
            "mileage_delta": (usage.end_mileage - usage.start_mileage) if usage.end_mileage and usage.start_mileage else None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return db_usage
        
    except Exception as e:
        logger.error(f"Error creating usage record: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create usage record")

@router.get("/usage", response_model=List[VehicleUsageResponse])
@require_permission("usage:read")
async def get_usage_records(
    vehicle_id: Optional[int] = None,
    user_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: Dict[str, Any] = None
):
    """Get vehicle usage records with optional filters"""
    query = db.query(VehicleUsage)
    
    # Role-based filtering
    user_role = current_user.get("role", "")
    current_user_id = current_user.get("user_id")
    
    if user_role == "driver":
        # Drivers can only see their own usage records
        query = query.filter(VehicleUsage.user_id == current_user_id)
    elif user_id and user_role in ["admin", "fleet_manager"]:
        # Admin and fleet managers can filter by user_id
        query = query.filter(VehicleUsage.user_id == user_id)
    
    if vehicle_id:
        query = query.filter(VehicleUsage.vehicle_id == vehicle_id)
    if start_date:
        query = query.filter(VehicleUsage.start_time >= start_date)
    if end_date:
        query = query.filter(VehicleUsage.start_time <= end_date)
    
    usage_records = query.order_by(VehicleUsage.start_time.desc()).offset(skip).limit(limit).all()
    return usage_records

# Vehicle Status Routes
@router.post("/status", response_model=VehicleStatusResponse)
@require_permission("status:write")
async def create_status_record(
    status: VehicleStatusCreate,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: Dict[str, Any] = None
):
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a new vehicle status record"""
    try:
        db_status = VehicleStatus(
            vehicle_id=status.vehicle_id,
            status=status.status,
            location=status.location,
            fuel_level=status.fuel_level,
            mileage=status.mileage,
            condition_notes=status.condition_notes,
            reported_by=status.reported_by,
            reported_at=status.reported_at or datetime.now(timezone.utc)
        )
        db.add(db_status)
        db.commit()
        db.refresh(db_status)
        
        # Log activity
        await log_vehicle_activity(
            vehicle_id=status.vehicle_id,
            activity_type="status_updated",
            details=f"Status: {status.status}",
            user_id=status.reported_by
        )
        
        # Publish vehicle event
        await publish_vehicle_event({
            "event_type": "status_updated",
            "vehicle_id": status.vehicle_id,
            "status": status.status,
            "location": status.location,
            "fuel_level": status.fuel_level,
            "mileage": status.mileage,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return db_status
        
    except Exception as e:
        logger.error(f"Error creating status record: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create status record")

@router.get("/status/{vehicle_id}/latest", response_model=VehicleStatusResponse)
@require_permission("status:read")
async def get_latest_status(
    vehicle_id: int,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: Dict[str, Any] = None
):
    """Get latest status for a specific vehicle"""
    status = db.query(VehicleStatus)\
        .filter(VehicleStatus.vehicle_id == vehicle_id)\
        .order_by(VehicleStatus.reported_at.desc())\
        .first()
    
    if not status:
        raise HTTPException(status_code=404, detail="No status found for vehicle")
    return status

@router.get("/status", response_model=List[VehicleStatusResponse])
@require_permission("status:read")
async def get_status_records(
    vehicle_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: Dict[str, Any] = None
):
    """Get vehicle status records with optional filters"""
    query = db.query(VehicleStatus)
    
    if vehicle_id:
        query = query.filter(VehicleStatus.vehicle_id == vehicle_id)
    if status:
        query = query.filter(VehicleStatus.status == status)
    
    status_records = query.order_by(VehicleStatus.reported_at.desc()).offset(skip).limit(limit).all()
    return status_records

# Analytics Routes
@router.get("/analytics/usage/{vehicle_id}")
@require_permission("analytics:read")
async def get_vehicle_usage_analytics(
    vehicle_id: int,
    days: int = 30,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: Dict[str, Any] = None
):
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get usage analytics for a specific vehicle"""
    try:
        from sqlalchemy import func
        from datetime import timedelta
        
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get usage statistics
        usage_stats = db.query(
            func.count(VehicleUsage.id).label('total_trips'),
            func.sum(VehicleUsage.end_mileage - VehicleUsage.start_mileage).label('total_miles'),
            func.sum(VehicleUsage.fuel_consumed).label('total_fuel'),
            func.avg(VehicleUsage.end_mileage - VehicleUsage.start_mileage).label('avg_trip_distance')
        ).filter(
            VehicleUsage.vehicle_id == vehicle_id,
            VehicleUsage.start_time >= start_date
        ).first()
        
        # Get assignment statistics
        assignment_stats = db.query(
            func.count(VehicleAssignment.id).label('total_assignments'),
            func.count(VehicleAssignment.id).filter(VehicleAssignment.status == 'active').label('active_assignments')
        ).filter(
            VehicleAssignment.vehicle_id == vehicle_id,
            VehicleAssignment.assignment_date >= start_date
        ).first()
        
        return {
            "vehicle_id": vehicle_id,
            "period_days": days,
            "usage_stats": {
                "total_trips": usage_stats.total_trips or 0,
                "total_miles": float(usage_stats.total_miles or 0),
                "total_fuel": float(usage_stats.total_fuel or 0),
                "avg_trip_distance": float(usage_stats.avg_trip_distance or 0)
            },
            "assignment_stats": {
                "total_assignments": assignment_stats.total_assignments or 0,
                "active_assignments": assignment_stats.active_assignments or 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting usage analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics")

@router.get("/analytics/fleet")
@require_permission("analytics:read")
async def get_fleet_analytics(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: Dict[str, Any] = None
):
    """Get fleet-wide analytics"""
    try:
        from sqlalchemy import func, distinct
        
        # Get fleet overview
        total_vehicles = db.query(func.count(distinct(VehicleStatus.vehicle_id))).scalar()
        active_assignments = db.query(func.count(VehicleAssignment.id))\
            .filter(VehicleAssignment.status == 'active').scalar()
        
        # Get recent usage
        recent_usage = db.query(func.count(VehicleUsage.id))\
            .filter(VehicleUsage.start_time >= datetime.now(timezone.utc) - timedelta(days=7)).scalar()
        
        # Get status distribution
        status_distribution = db.query(
            VehicleStatus.status,
            func.count(distinct(VehicleStatus.vehicle_id)).label('count')
        ).group_by(VehicleStatus.status).all()
        
        return {
            "fleet_overview": {
                "total_vehicles": total_vehicles or 0,
                "active_assignments": active_assignments or 0,
                "recent_usage_count": recent_usage or 0
            },
            "status_distribution": [
                {"status": status.status, "count": status.count}
                for status in status_distribution
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting fleet analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get fleet analytics")

# Driver Management Routes
@router.post("/drivers", response_model=DriverResponse)
@require_permission("drivers:write")
async def create_driver(
    driver: DriverCreateRequest,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: Dict[str, Any] = None
):
    """Create a new driver with South African compliance validation"""
    try:
        drivers_collection = get_driver_collection()
        
        # Check if employee ID already exists
        existing_driver = await drivers_collection.find_one({"employee_id": driver.employee_id})
        if existing_driver:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Driver with this employee ID already exists"
            )
        
        # Check if license number already exists
        existing_license = await drivers_collection.find_one({"license_number": driver.license_number})
        if existing_license:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Driver with this license number already exists"
            )
        
        # Validate user exists in Users Dblock
        users_url = os.getenv("USERS_DBLOCK_URL", "http://users_db_service:8013")
        try:
            response = requests.get(f"{users_url}/api/v1/users/{driver.user_id}")
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User not found in system"
                )
        except requests.RequestException:
            logger.warning("Could not validate user existence - proceeding with driver creation")
        
        # Create driver document
        driver_data = driver.dict()
        driver_data["created_at"] = datetime.utcnow()
        driver_data["updated_at"] = datetime.utcnow()
        
        result = await drivers_collection.insert_one(driver_data)
        driver_data["_id"] = str(result.inserted_id)
        
        # Log activity
        await log_vehicle_activity(
            vehicle_id=None,
            activity_type="driver_created",
            details=f"Driver {driver.employee_id} created",
            user_id=driver.user_id
        )
        
        # Publish event
        await publish_vehicle_event({
            "event_type": "driver_created",
            "driver_id": str(result.inserted_id),
            "employee_id": driver.employee_id,
            "user_id": driver.user_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return DriverResponse(**driver_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating driver: {e}")
        raise HTTPException(status_code=500, detail="Failed to create driver")


@router.get("/drivers", response_model=List[DriverResponse])
@require_permission("drivers:read")
async def get_drivers(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    department_filter: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: Dict[str, Any] = None
):
    """Get drivers with optional filters"""
    try:
        drivers_collection = get_driver_collection()
        
        # Build filter query
        filter_query = {}
        if status_filter:
            filter_query["status"] = status_filter
        if department_filter:
            filter_query["department"] = department_filter
        
        # Role-based filtering for drivers
        user_role = current_user.get("role", "")
        user_id = current_user.get("user_id")
        
        if user_role == "driver":
            # Drivers can only see their own record
            filter_query["user_id"] = user_id
        
        # Get drivers with pagination
        drivers_cursor = drivers_collection.find(filter_query).skip(skip).limit(limit)
        drivers = []
        
        async for driver in drivers_cursor:
            driver["_id"] = str(driver["_id"])
            
            # Optionally fetch user details
            if driver.get("user_id"):
                try:
                    users_url = os.getenv("USERS_DBLOCK_URL", "http://users_db_service:8013")
                    response = requests.get(f"{users_url}/api/v1/users/{driver['user_id']}")
                    if response.status_code == 200:
                        user_data = response.json()
                        driver["full_name"] = user_data.get("full_name")
                        driver["email"] = user_data.get("email")
                except Exception as e:
                    logger.warning(f"Could not fetch user details for driver {driver['employee_id']}: {e}")
            
            drivers.append(DriverResponse(**driver))
        
        return drivers
        
    except Exception as e:
        logger.error(f"Error fetching drivers: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch drivers")


@router.get("/drivers/{driver_id}", response_model=DriverResponse)
@require_permission("drivers:read")
async def get_driver(
    driver_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: Dict[str, Any] = None
):
    """Get specific driver by ID"""
    try:
        drivers_collection = get_driver_collection()
        
        # Try to find by MongoDB ObjectId first, then by employee_id
        from bson import ObjectId
        
        if ObjectId.is_valid(driver_id):
            driver = await drivers_collection.find_one({"_id": ObjectId(driver_id)})
        else:
            driver = await drivers_collection.find_one({"employee_id": driver_id})
        
        if not driver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Driver not found"
            )
        
        # Check if user can access this driver record
        if not can_access_resource(current_user, driver.get("user_id")):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this driver record"
            )
        
        driver["_id"] = str(driver["_id"])
        
        # Fetch user details
        if driver.get("user_id"):
            try:
                users_url = os.getenv("USERS_DBLOCK_URL", "http://users_db_service:8013")
                response = requests.get(f"{users_url}/api/v1/users/{driver['user_id']}")
                if response.status_code == 200:
                    user_data = response.json()
                    driver["full_name"] = user_data.get("full_name")
                    driver["email"] = user_data.get("email")
            except Exception as e:
                logger.warning(f"Could not fetch user details: {e}")
        
        return DriverResponse(**driver)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching driver: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch driver")


@router.put("/drivers/{driver_id}", response_model=DriverResponse)
@require_permission("drivers:write")
async def update_driver(
    driver_id: str,
    driver_update: DriverUpdateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: Dict[str, Any] = None
):
    """Update driver information"""
    try:
        drivers_collection = get_driver_collection()
        from bson import ObjectId
        
        # Find driver
        if ObjectId.is_valid(driver_id):
            existing_driver = await drivers_collection.find_one({"_id": ObjectId(driver_id)})
            query = {"_id": ObjectId(driver_id)}
        else:
            existing_driver = await drivers_collection.find_one({"employee_id": driver_id})
            query = {"employee_id": driver_id}
        
        if not existing_driver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Driver not found"
            )
        
        # Check if user can update this driver record
        if not can_access_resource(current_user, existing_driver.get("user_id")):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to update this driver record"
            )
        
        # Prepare update data
        update_data = {}
        for field, value in driver_update.dict(exclude_unset=True).items():
            if value is not None:
                update_data[field] = value
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields to update"
            )
        
        update_data["updated_at"] = datetime.utcnow()
        
        # Update driver
        result = await drivers_collection.update_one(query, {"$set": update_data})
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No changes made to driver"
            )
        
        # Get updated driver
        updated_driver = await drivers_collection.find_one(query)
        updated_driver["_id"] = str(updated_driver["_id"])
        
        # Log activity
        await log_vehicle_activity(
            vehicle_id=updated_driver.get("current_vehicle_id"),
            activity_type="driver_updated",
            details=f"Driver {updated_driver['employee_id']} updated",
            user_id=updated_driver["user_id"]
        )
        
        return DriverResponse(**updated_driver)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating driver: {e}")
        raise HTTPException(status_code=500, detail="Failed to update driver")


@router.delete("/drivers/{driver_id}")
@require_permission("drivers:delete")
async def delete_driver(
    driver_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: Dict[str, Any] = None
):
    """Delete driver record"""
    try:
        drivers_collection = get_driver_collection()
        from bson import ObjectId
        
        # Find and delete driver
        if ObjectId.is_valid(driver_id):
            driver = await drivers_collection.find_one({"_id": ObjectId(driver_id)})
            query = {"_id": ObjectId(driver_id)}
        else:
            driver = await drivers_collection.find_one({"employee_id": driver_id})
            query = {"employee_id": driver_id}
        
        if not driver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Driver not found"
            )
        
        # Check if user can delete this driver record
        if not can_access_resource(current_user, driver.get("user_id")):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to delete this driver record"
            )
        
        # Check if driver is currently assigned to vehicles
        if driver.get("current_vehicle_id"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete driver currently assigned to a vehicle"
            )
        
        result = await drivers_collection.delete_one(query)
        
        if result.deleted_count == 1:
            # Log activity
            await log_vehicle_activity(
                vehicle_id=None,
                activity_type="driver_deleted",
                details=f"Driver {driver['employee_id']} deleted"
            )
            
            return {"success": True, "message": "Driver successfully deleted"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete driver"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting driver: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete driver")


@router.get("/drivers/search/{query}")
@require_permission("drivers:read")
async def search_drivers(
    query: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: Dict[str, Any] = None
):
    """Search drivers by name, employee ID, or license number"""
    try:
        drivers_collection = get_driver_collection()
        
        # Build search query
        search_filter = {
            "$or": [
                {"employee_id": {"$regex": query, "$options": "i"}},
                {"license_number": {"$regex": query, "$options": "i"}},
                {"department": {"$regex": query, "$options": "i"}}
            ]
        }
        
        # Role-based filtering for drivers
        user_role = current_user.get("role", "")
        user_id = current_user.get("user_id")
        
        if user_role == "driver":
            # Drivers can only search their own record
            search_filter["user_id"] = user_id
        
        drivers_cursor = drivers_collection.find(search_filter).limit(50)
        drivers = []
        
        async for driver in drivers_cursor:
            driver["_id"] = str(driver["_id"])
            
            # Fetch user details for name search
            if driver.get("user_id"):
                try:
                    users_url = os.getenv("USERS_DBLOCK_URL", "http://users_db_service:8013")
                    response = requests.get(f"{users_url}/api/v1/users/{driver['user_id']}")
                    if response.status_code == 200:
                        user_data = response.json()
                        driver["full_name"] = user_data.get("full_name", "")
                        driver["email"] = user_data.get("email", "")
                        
                        # Check if query matches name
                        full_name = user_data.get("full_name", "").lower()
                        if query.lower() in full_name:
                            drivers.append(DriverResponse(**driver))
                            continue
                except Exception:
                    pass
            
            drivers.append(DriverResponse(**driver))
        
        return drivers
        
    except Exception as e:
        logger.error(f"Error searching drivers: {e}")
        raise HTTPException(status_code=500, detail="Failed to search drivers")
