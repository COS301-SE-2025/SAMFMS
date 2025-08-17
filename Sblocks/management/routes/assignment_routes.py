"""
API routes for vehicle assignment management
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from datetime import datetime

from services.assignment_service import assignment_service
from schemas.requests import VehicleAssignmentCreateRequest

router = APIRouter(prefix="/assignments", tags=["assignments"])


@router.post("/", response_model=Dict[str, Any])
async def assign_vehicle_to_driver(
    request: VehicleAssignmentCreateRequest
):
    """Assign a vehicle to a driver"""
    try:
        result = await assignment_service.assign_vehicle_to_driver(request, "system")
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{assignment_id}", response_model=Dict[str, Any])
async def unassign_vehicle_from_driver(
    assignment_id: str,
    end_mileage: Optional[int] = None
):
    """Unassign a vehicle from a driver"""
    try:
        result = await assignment_service.unassign_vehicle_from_driver(
            assignment_id, "system", end_mileage
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/driver/{driver_id}/current", response_model=Dict[str, Any])
async def get_driver_current_assignment(
    driver_id: str
):
    """Get driver's current active vehicle assignment"""
    try:
        assignment = await assignment_service.get_driver_current_assignment(driver_id)
        return {"success": True, "data": assignment}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/vehicle/{vehicle_id}/current", response_model=Dict[str, Any])
async def get_vehicle_current_assignment(
    vehicle_id: str
):
    """Get vehicle's current active assignment"""
    try:
        assignment = await assignment_service.get_vehicle_current_assignment(vehicle_id)
        return {"success": True, "data": assignment}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/driver/{driver_id}", response_model=Dict[str, Any])
async def get_assignments_by_driver(
    driver_id: str
):
    """Get all assignments for a driver"""
    try:
        assignments = await assignment_service.get_assignments_by_driver(driver_id)
        return {"success": True, "data": assignments}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/vehicle/{vehicle_id}", response_model=Dict[str, Any])
async def get_assignments_by_vehicle(
    vehicle_id: str
):
    """Get all assignments for a vehicle"""
    try:
        assignments = await assignment_service.get_assignments_by_vehicle(vehicle_id)
        return {"success": True, "data": assignments}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/active", response_model=Dict[str, Any])
async def get_all_active_assignments():
    """Get all active assignments"""
    try:
        assignments = await assignment_service.get_all_active_assignments()
        return {"success": True, "data": assignments}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/driver/{driver_id}/visibility", response_model=Dict[str, Any])
async def get_driver_assignment_visibility(
    driver_id: str
):
    """Get comprehensive assignment visibility for a driver"""
    try:
        # Get current assignment
        current_assignment = await assignment_service.get_driver_current_assignment(driver_id)
        
        # Get assignment history
        assignment_history = await assignment_service.get_assignments_by_driver(driver_id)
        
        # Build visibility data
        visibility_data = {
            "driver_id": driver_id,
            "current_assignment": current_assignment,
            "assignment_history": assignment_history,
            "has_active_assignment": current_assignment is not None,
            "total_assignments": len(assignment_history)
        }
        
        return {"success": True, "data": visibility_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
