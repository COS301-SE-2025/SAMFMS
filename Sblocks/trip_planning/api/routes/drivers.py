"""
Driver assignment and availability API routes
"""
import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime

from schemas.requests import AssignDriverRequest, DriverAvailabilityRequest
from schemas.responses import ResponseBuilder
from schemas.entities import Trip
from services.driver_service import driver_service
from api.dependencies import get_current_user_legacy as get_current_user, validate_trip_access

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=Dict[str, Any])
async def get_all_drivers(
    status: Optional[str] = Query(None, description="Filter by driver status"),
    department: Optional[str] = Query(None, description="Filter by department"),
    skip: int = Query(0, ge=0, description="Number of drivers to skip"),
    limit: int = Query(100, ge=1, le=500, description="Number of drivers to return"),
    current_user: str = Depends(get_current_user)
):
    """Get all drivers from the drivers collection"""
    try:
        result = await driver_service.get_all_drivers(
            status=status,
            department=department, 
            skip=skip,
            limit=limit
        )
        
        return ResponseBuilder.success(
            data=result,
            message=f"Retrieved {len(result['drivers'])} drivers successfully"
        )
    
    except Exception as e:
        logger.error(f"Error getting all drivers: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve drivers")


@router.post("/{trip_id}/assign", response_model=Dict[str, Any])
async def assign_driver_to_trip(
    trip_id: str,
    request: AssignDriverRequest,
    current_user: str = Depends(get_current_user),
    trip: Trip = Depends(validate_trip_access)
):
    """Assign a driver to a trip"""
    try:
        assignment = await driver_service.assign_driver_to_trip(
            trip_id, request, current_user
        )
        
        return ResponseBuilder.success(
            data={"assignment": assignment.dict()},
            message="Driver assigned successfully"
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to assign driver")


@router.delete("/{trip_id}/unassign", response_model=Dict[str, Any])
async def unassign_driver_from_trip(
    trip_id: str,
    current_user: str = Depends(get_current_user),
    trip: Trip = Depends(validate_trip_access)
):
    """Remove driver assignment from a trip"""
    try:
        success = await driver_service.unassign_driver_from_trip(trip_id, current_user)
        
        if not success:
            raise HTTPException(status_code=404, detail="No assignment found")
        
        return ResponseBuilder.success(message="Driver unassigned successfully")
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to unassign driver")


@router.get("/{driver_id}/availability", response_model=Dict[str, Any])
async def check_single_driver_availability(
    driver_id: str,
    start_time: datetime = Query(..., description="Start of time period"),
    end_time: datetime = Query(..., description="End of time period"),
    current_user: str = Depends(get_current_user)
):
    """Check if a specific driver is available in a given timeframe"""
    try:
        if end_time <= start_time:
            raise HTTPException(status_code=400, detail="End time must be after start time")
        
        # Check driver availability using the existing service method
        is_available = await driver_service.check_driver_availability(
            driver_id, start_time, end_time
        )
        
        return ResponseBuilder.success(
            data={
                "driver_id": driver_id,
                "is_available": is_available,
                "start_time": start_time,
                "end_time": end_time
            },
            message=f"Driver availability checked successfully"
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error checking driver {driver_id} availability: {e}")
        raise HTTPException(status_code=500, detail="Failed to check driver availability")


@router.get("/availability", response_model=Dict[str, Any])
async def check_driver_availability(
    start_time: datetime = Query(..., description="Start of time period"),
    end_time: datetime = Query(..., description="End of time period"),
    driver_ids: Optional[List[str]] = Query(None, description="Specific driver IDs to check"),
    current_user: str = Depends(get_current_user)
):
    """Check driver availability for a time period"""
    try:
        if end_time <= start_time:
            raise HTTPException(status_code=400, detail="End time must be after start time")
        
        request = DriverAvailabilityRequest(
            driver_ids=driver_ids,
            start_time=start_time,
            end_time=end_time
        )
        
        availability = await driver_service.get_driver_availability(request)
        
        return ResponseBuilder.success(
            data={"availability": availability},
            message="Driver availability retrieved successfully"
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to check driver availability")


@router.get("/available", response_model=Dict[str, Any])
async def get_available_drivers(
    start_time: datetime = Query(..., description="Start of time period"),
    end_time: datetime = Query(..., description="End of time period"),
    current_user: str = Depends(get_current_user)
):
    """Get all drivers that are available within a given timeframe"""
    try:
        if end_time <= start_time:
            raise HTTPException(status_code=400, detail="End time must be after start time")
        
        # Get all drivers from the management database
        all_drivers_result = await driver_service.get_all_drivers()
        all_drivers = all_drivers_result.get("drivers", [])
        
        available_drivers = []
        
        # Check each driver's availability
        for driver in all_drivers:
            driver_id = driver.get("employee_id")
            if not driver_id:
                continue
                
            # Check if driver is available during the timeframe
            is_available = await driver_service.check_driver_availability(
                driver_id, start_time, end_time
            )
            
            if is_available:
                available_drivers.append({
                    **driver,
                    "is_available": True,
                    "checked_timeframe": {
                        "start_time": start_time,
                        "end_time": end_time
                    }
                })
        
        return ResponseBuilder.success(
            data={
                "available_drivers": available_drivers,
                "total_available": len(available_drivers),
                "total_checked": len(all_drivers),
                "timeframe": {
                    "start_time": start_time,
                    "end_time": end_time
                }
            },
            message=f"Found {len(available_drivers)} available drivers out of {len(all_drivers)} total drivers"
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting available drivers: {e}")
        raise HTTPException(status_code=500, detail="Failed to get available drivers")


@router.get("/{driver_id}/assignments", response_model=Dict[str, Any])
async def get_driver_assignments(
    driver_id: str,
    active_only: bool = Query(True, description="Show only active assignments"),
    current_user: str = Depends(get_current_user)
):
    """Get assignments for a specific driver"""
    try:
        assignments = await driver_service.get_driver_assignments(
            driver_id=driver_id,
            active_only=active_only
        )
        
        return ResponseBuilder.success(
            data={"assignments": [assignment.dict() for assignment in assignments]},
            message="Driver assignments retrieved successfully"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get driver assignments")


@router.get("/assignments", response_model=Dict[str, Any])
async def get_all_assignments(
    active_only: bool = Query(True, description="Show only active assignments"),
    driver_id: Optional[str] = Query(None, description="Filter by driver ID"),
    trip_id: Optional[str] = Query(None, description="Filter by trip ID"),
    current_user: str = Depends(get_current_user)
):
    """Get all driver assignments with optional filtering"""
    try:
        assignments = await driver_service.get_driver_assignments(
            driver_id=driver_id,
            trip_id=trip_id,
            active_only=active_only
        )
        
        return ResponseBuilder.success(
            data={"assignments": [assignment.dict() for assignment in assignments]},
            message="Assignments retrieved successfully"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get assignments")
