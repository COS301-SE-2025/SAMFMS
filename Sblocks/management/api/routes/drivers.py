"""
Driver routes
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional
import logging

from services.driver_service import driver_service
from schemas.requests import DriverCreateRequest, DriverUpdateRequest
from schemas.responses import ResponseBuilder
from api.dependencies import (
    get_current_user, 
    require_permission, 
    get_pagination_params,
    validate_object_id
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/drivers")
async def get_drivers(
    department: Optional[str] = Query(None, description="Filter by department"),
    status: Optional[str] = Query(None, description="Filter by status"),
    pagination = Depends(get_pagination_params),
    current_user = Depends(require_permission("drivers:read"))
):
    """Get drivers with optional filters"""
    try:
        if department:
            drivers = await driver_service.get_drivers_by_department(department)
        elif status == "active":
            drivers = await driver_service.get_active_drivers()
        else:
            from repositories.repositories import DriverRepository
            driver_repo = DriverRepository()
            
            filter_query = {}
            if status:
                filter_query["status"] = status
            
            drivers = await driver_repo.find(
                filter_query=filter_query,
                skip=pagination["skip"],
                limit=pagination["limit"],
                sort=[("last_name", 1), ("first_name", 1)]
            )
        
        return ResponseBuilder.success(
            data={"drivers": drivers, "total": len(drivers)},
            message="Drivers retrieved successfully"
        ).model_dump()
        
    except Exception as e:
        logger.error(f"Error getting drivers: {e}")
        return ResponseBuilder.error(
            error="DriversRetrievalError",
            message="Failed to retrieve drivers",
            details={"error": str(e)}
        ).model_dump()


@router.post("/drivers")
async def create_driver(
    driver_request: DriverCreateRequest,
    current_user = Depends(require_permission("drivers:create"))
):
    """Create new driver"""
    try:
        driver = await driver_service.create_driver(
            driver_request, 
            current_user["user_id"]
        )
        
        return ResponseBuilder.success(
            data={"driver": driver},
            message="Driver created successfully"
        ).model_dump()
        
    except ValueError as e:
        return ResponseBuilder.error(
            error="ValidationError",
            message=str(e),
            details={"field_errors": str(e)}
        ).model_dump()
    except Exception as e:
        logger.error(f"Error creating driver: {e}")
        return ResponseBuilder.error(
            error="DriverCreationError",
            message="Failed to create driver",
            details={"error": str(e)}
        ).model_dump()


@router.get("/drivers/{driver_id}")
async def get_driver(
    driver_id: str,
    current_user = Depends(require_permission("drivers:read"))
):
    """Get specific driver"""
    try:
        validate_object_id(driver_id, "driver ID")
        
        from repositories.repositories import DriverRepository
        driver_repo = DriverRepository()
        
        driver = await driver_repo.get_by_id(driver_id)
        if not driver:
            return ResponseBuilder.error(
                error="DriverNotFound",
                message="Driver not found",
                details={"driver_id": driver_id}
            ).model_dump()
        
        return ResponseBuilder.success(
            data={"driver": driver},
            message="Driver retrieved successfully"
        ).model_dump()
        
    except Exception as e:
        logger.error(f"Error getting driver {driver_id}: {e}")
        return ResponseBuilder.error(
            error="DriverRetrievalError",
            message="Failed to retrieve driver",
            details={"driver_id": driver_id, "error": str(e)}
        ).model_dump()


@router.put("/drivers/{driver_id}")
async def update_driver(
    driver_id: str,
    driver_updates: DriverUpdateRequest,
    current_user = Depends(require_permission("drivers:update"))
):
    """Update driver"""
    try:
        validate_object_id(driver_id, "driver ID")
        
        driver = await driver_service.update_driver(
            driver_id,
            driver_updates, 
            current_user["user_id"]
        )
        
        return ResponseBuilder.success(
            data={"driver": driver},
            message="Driver updated successfully"
        ).model_dump()
        
    except ValueError as e:
        return ResponseBuilder.error(
            error="ValidationError",
            message=str(e),
            details={"field_errors": str(e)}
        ).model_dump()
    except Exception as e:
        logger.error(f"Error updating driver {driver_id}: {e}")
        return ResponseBuilder.error(
            error="DriverUpdateError",
            message="Failed to update driver",
            details={"driver_id": driver_id, "error": str(e)}
        ).model_dump()


@router.delete("/drivers/{driver_id}")
async def delete_driver(
    driver_id: str,
    current_user = Depends(require_permission("drivers:delete"))
):
    """Delete (deactivate) driver"""
    try:
        validate_object_id(driver_id, "driver ID")
        
        from schemas.requests import DriverUpdateRequest
        
        # Instead of deleting, deactivate the driver
        await driver_service.update_driver(
            driver_id,
            DriverUpdateRequest(status="inactive"),
            current_user["user_id"]
        )
        
        return ResponseBuilder.success(
            message="Driver deactivated successfully"
        ).model_dump()
        
    except ValueError as e:
        return ResponseBuilder.error(
            error="ValidationError",
            message=str(e),
            details={"field_errors": str(e)}
        ).model_dump()
    except Exception as e:
        logger.error(f"Error deactivating driver {driver_id}: {e}")
        return ResponseBuilder.error(
            error="DriverDeactivationError",
            message="Failed to deactivate driver",
            details={"driver_id": driver_id, "error": str(e)}
        ).model_dump()


@router.post("/drivers/{driver_id}/activate")
async def activate_driver(
    driver_id: str,
    current_user = Depends(require_permission("drivers:update"))
):
    """Activate driver"""
    try:
        validate_object_id(driver_id, "driver ID")
        
        await driver_service.activate_driver(
            driver_id,
            current_user["user_id"]
        )
        
        return ResponseBuilder.success(
            message="Driver activated successfully"
        ).model_dump()
        
    except ValueError as e:
        return ResponseBuilder.error(
            error="ValidationError",
            message=str(e),
            details={"field_errors": str(e)}
        ).model_dump()
    except Exception as e:
        logger.error(f"Error activating driver {driver_id}: {e}")
        return ResponseBuilder.error(
            error="DriverActivationError",
            message="Failed to activate driver",
            details={"driver_id": driver_id, "error": str(e)}
        ).model_dump()


@router.post("/drivers/{driver_id}/assign-vehicle")
async def assign_vehicle_to_driver(
    driver_id: str,
    vehicle_id: str = Query(..., description="Vehicle ID to assign to driver"),
    current_user = Depends(require_permission("drivers:assign_vehicle"))
):
    """Assign vehicle to driver"""
    try:
        validate_object_id(driver_id, "driver ID")
        validate_object_id(vehicle_id, "vehicle ID")
        
        await driver_service.assign_vehicle_to_driver(
            driver_id,
            vehicle_id,
            current_user["user_id"]
        )
        
        return ResponseBuilder.success(
            message=f"Vehicle {vehicle_id} assigned to driver successfully"
        ).model_dump()
        
    except ValueError as e:
        return ResponseBuilder.error(
            error="ValidationError",
            message=str(e),
            details={"field_errors": str(e)}
        ).model_dump()
    except Exception as e:
        logger.error(f"Error assigning vehicle to driver {driver_id}: {e}")
        return ResponseBuilder.error(
            error="VehicleAssignmentError",
            message="Failed to assign vehicle to driver",
            details={"driver_id": driver_id, "vehicle_id": vehicle_id, "error": str(e)}
        ).model_dump()


@router.post("/drivers/{driver_id}/unassign-vehicle")
async def unassign_vehicle_from_driver(
    driver_id: str,
    current_user = Depends(require_permission("drivers:assign_vehicle"))
):
    """Remove vehicle assignment from driver"""
    try:
        validate_object_id(driver_id, "driver ID")
        
        await driver_service.unassign_vehicle_from_driver(
            driver_id,
            current_user["user_id"]
        )
        
        return ResponseBuilder.success(
            message="Vehicle unassigned from driver successfully"
        ).model_dump()
        
    except ValueError as e:
        return ResponseBuilder.error(
            error="ValidationError",
            message=str(e),
            details={"field_errors": str(e)}
        ).model_dump()
    except Exception as e:
        logger.error(f"Error unassigning vehicle from driver {driver_id}: {e}")
        return ResponseBuilder.error(
            error="VehicleUnassignmentError",
            message="Failed to unassign vehicle from driver",
            details={"driver_id": driver_id, "error": str(e)}
        ).model_dump()


@router.get("/drivers/search/{query}")
async def search_drivers(
    query: str,
    limit: int = Query(50, le=100),
    current_user = Depends(require_permission("drivers:read"))
):
    """Search drivers by name, employee ID, or email"""
    try:
        drivers = await driver_service.search_drivers(query, limit)
        return ResponseBuilder.success(
            data={"drivers": drivers, "total": len(drivers)},
            message="Driver search completed successfully"
        ).model_dump()
        
    except Exception as e:
        logger.error(f"Error searching drivers: {e}")
        return ResponseBuilder.error(
            error="DriverSearchError",
            message="Failed to search drivers",
            details={"query": query, "error": str(e)}
        ).model_dump()
