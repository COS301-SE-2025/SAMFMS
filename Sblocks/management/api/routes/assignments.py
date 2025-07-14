"""
Vehicle Assignment Routes
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
import logging

from repositories.repositories import VehicleAssignmentRepository
from schemas.requests import VehicleAssignmentRequest
from schemas.entities import AssignmentStatus
from events.publisher import event_publisher
from api.dependencies import (
    get_current_user, 
    require_permission, 
    get_pagination_params,
    validate_object_id
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/assignments")
async def get_assignments(
    vehicle_id: Optional[str] = Query(None, description="Filter by vehicle ID"),
    driver_id: Optional[str] = Query(None, description="Filter by driver ID"),
    status: Optional[AssignmentStatus] = Query(None, description="Filter by status"),
    pagination = Depends(get_pagination_params),
    current_user = Depends(require_permission("assignments:read"))
):
    """Get vehicle assignments with optional filters"""
    try:
        assignment_repo = VehicleAssignmentRepository()
        
        # Build filter
        filter_query = {}
        if vehicle_id:
            filter_query["vehicle_id"] = vehicle_id
        if driver_id:
            filter_query["driver_id"] = driver_id
        if status:
            filter_query["status"] = status.value
        
        # Get assignments
        assignments = await assignment_repo.find(
            filter_query=filter_query,
            skip=pagination["skip"],
            limit=pagination["limit"],
            sort=[("created_at", -1)]
        )
        
        # Get total count
        total = await assignment_repo.count(filter_query)
        total_pages = (total + pagination["limit"] - 1) // pagination["limit"]
        
        return {
            "assignments": assignments,
            "pagination": {
                "total": total,
                "page": pagination["skip"] // pagination["limit"] + 1,
                "page_size": pagination["limit"],
                "total_pages": total_pages
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting assignments: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve assignments")


@router.post("/assignments")
async def create_assignment(
    assignment_request: VehicleAssignmentRequest,
    current_user = Depends(require_permission("assignments:create"))
):
    """Create new vehicle assignment"""
    try:
        assignment_repo = VehicleAssignmentRepository()
        
        # Convert request to dict
        assignment_data = assignment_request.model_dump()
        assignment_data["created_by"] = current_user["user_id"]
        assignment_data["status"] = "active"
        
        # Create assignment
        assignment_id = await assignment_repo.create(assignment_data)
        
        # Get created assignment
        assignment = await assignment_repo.get_by_id(assignment_id)
        
        # Publish event
        await event_publisher.publish_assignment_created(
            assignment, 
            current_user["user_id"]
        )
        
        return {"assignment": assignment, "message": "Assignment created successfully"}
        
    except Exception as e:
        logger.error(f"Error creating assignment: {e}")
        raise HTTPException(status_code=500, detail="Failed to create assignment")


@router.get("/assignments/{assignment_id}")
async def get_assignment(
    assignment_id: str,
    current_user = Depends(require_permission("assignments:read"))
):
    """Get specific assignment"""
    try:
        validate_object_id(assignment_id, "assignment ID")
        assignment_repo = VehicleAssignmentRepository()
        
        assignment = await assignment_repo.get_by_id(assignment_id)
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        return {"assignment": assignment}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting assignment {assignment_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve assignment")


@router.put("/assignments/{assignment_id}")
async def update_assignment(
    assignment_id: str,
    updates: dict,
    current_user = Depends(require_permission("assignments:update"))
):
    """Update assignment"""
    try:
        validate_object_id(assignment_id, "assignment ID")
        assignment_repo = VehicleAssignmentRepository()
        
        # Check if assignment exists
        assignment = await assignment_repo.get_by_id(assignment_id)
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        # Update assignment
        success = await assignment_repo.update(assignment_id, updates)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to update assignment")
        
        # Get updated assignment
        updated_assignment = await assignment_repo.get_by_id(assignment_id)
        
        # Publish event if completed
        if updates.get("status") == "completed":
            await event_publisher.publish_assignment_completed(
                updated_assignment,
                current_user["user_id"]
            )
        
        return {"assignment": updated_assignment, "message": "Assignment updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating assignment {assignment_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update assignment")


@router.delete("/assignments/{assignment_id}")
async def delete_assignment(
    assignment_id: str,
    current_user = Depends(require_permission("assignments:delete"))
):
    """Delete assignment"""
    try:
        validate_object_id(assignment_id, "assignment ID")
        assignment_repo = VehicleAssignmentRepository()
        
        # Check if assignment exists
        assignment = await assignment_repo.get_by_id(assignment_id)
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        # Delete assignment
        success = await assignment_repo.delete(assignment_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to delete assignment")
        
        return {"message": "Assignment deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting assignment {assignment_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete assignment")


@router.post("/assignments/{assignment_id}/complete")
async def complete_assignment(
    assignment_id: str,
    end_mileage: Optional[float] = None,
    current_user = Depends(require_permission("assignments:update"))
):
    """Complete an assignment"""
    try:
        validate_object_id(assignment_id, "assignment ID")
        assignment_repo = VehicleAssignmentRepository()
        
        # Complete assignment
        success = await assignment_repo.complete_assignment(assignment_id, end_mileage)
        if not success:
            raise HTTPException(status_code=404, detail="Assignment not found or already completed")
        
        # Get completed assignment
        assignment = await assignment_repo.get_by_id(assignment_id)
        
        # Publish event
        await event_publisher.publish_assignment_completed(
            assignment,
            current_user["user_id"]
        )
        
        return {"assignment": assignment, "message": "Assignment completed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing assignment {assignment_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to complete assignment")
