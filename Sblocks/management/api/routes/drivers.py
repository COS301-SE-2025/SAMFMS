"""
Driver routes
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
import logging

from services.driver_service import driver_service
from schemas.requests import DriverCreateRequest, DriverUpdateRequest
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
        
        return {"drivers": drivers, "total": len(drivers)}
        
    except Exception as e:
        logger.error(f"Error getting drivers: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve drivers")


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
        
        return {"driver": driver, "message": "Driver created successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating driver: {e}")
        raise HTTPException(status_code=500, detail="Failed to create driver")


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
            raise HTTPException(status_code=404, detail="Driver not found")
        
        return {"driver": driver}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting driver {driver_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve driver")


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
        
        return {"driver": driver, "message": "Driver updated successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating driver {driver_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update driver")


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
        
        return {"message": "Driver deactivated successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deactivating driver {driver_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to deactivate driver")


@router.post("/drivers/{driver_id}/assign-vehicle")
async def assign_vehicle_to_driver(
    driver_id: str,
    vehicle_id: str,
    current_user = Depends(require_permission("drivers:assign_vehicle"))
):
    """Assign vehicle to driver"""
    try:
        validate_object_id(driver_id, "driver ID")
        
        await driver_service.assign_vehicle_to_driver(
            driver_id,
            vehicle_id,
            current_user["user_id"]
        )
        
        return {"message": f"Vehicle {vehicle_id} assigned to driver successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error assigning vehicle to driver {driver_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to assign vehicle to driver")


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
        
        return {"message": "Vehicle unassigned from driver successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error unassigning vehicle from driver {driver_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to unassign vehicle from driver")


@router.get("/drivers/search/{query}")
async def search_drivers(
    query: str,
    limit: int = Query(50, le=100),
    current_user = Depends(require_permission("drivers:read"))
):
    """Search drivers by name, employee ID, or email"""
    try:
        drivers = await driver_service.search_drivers(query, limit)
        return {"drivers": drivers, "total": len(drivers)}
        
    except Exception as e:
        logger.error(f"Error searching drivers: {e}")
        raise HTTPException(status_code=500, detail="Failed to search drivers")
