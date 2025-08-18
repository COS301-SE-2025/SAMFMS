"""
Geofences API routes
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from typing import Optional, List
import logging

from services.geofence_service import geofence_service
from api.dependencies import get_current_user, require_permission, get_request_id, RequestTimer
from schemas.responses import ResponseBuilder
from schemas.requests import GeofenceCreateRequest, GeofenceUpdateRequest
from api.exception_handlers import BusinessLogicError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/geofences")
async def create_geofence(
    request: Request,
    geofence_data: GeofenceCreateRequest,
    current_user = Depends(require_permission("gps:write"))
):
    """Create a new geofence"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            created_by = current_user.get('user_id')
            
            geofence = await geofence_service.create_geofence(
                name=geofence_data.name,
                description=geofence_data.description,
                geometry=geofence_data.geometry,
                geofence_type=geofence_data.geofence_type,
                is_active=geofence_data.is_active,
                created_by=created_by,
                metadata=geofence_data.metadata
            )
            
            return ResponseBuilder.success(
                data=geofence.model_dump(),
                message="Geofence created successfully",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
            
        except Exception as e:
            logger.error(f"Error creating geofence: {e}")
            raise BusinessLogicError("Failed to create geofence")


@router.get("/geofences/{geofence_id}")
async def get_geofence(
    request: Request,
    geofence_id: str,
    current_user = Depends(require_permission("gps:read"))
):
    """Get a geofence by ID"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            geofence = await geofence_service.get_geofence(geofence_id)
            
            if not geofence:
                raise HTTPException(status_code=404, detail="Geofence not found")
            
            return ResponseBuilder.success(
                data=geofence.model_dump(),
                message="Geofence retrieved successfully",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting geofence: {e}")
            raise BusinessLogicError("Failed to retrieve geofence")


@router.get("/geofences")
async def get_geofences(
    request: Request,
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    created_by: Optional[str] = Query(None, description="Filter by creator"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    current_user = Depends(require_permission("gps:read"))
):
    """Get list of geofences with filters"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            # If created_by not provided and user doesn't have admin permission, filter by their user_id
            if not created_by and not current_user.get('is_admin', False):
                created_by = current_user.get('user_id')
            
            geofences = await geofence_service.get_geofences(
                is_active=is_active,
                created_by=created_by,
                limit=limit,
                offset=offset
            )
            
            return ResponseBuilder.success(
                data=[geofence.model_dump() for geofence in geofences],
                message=f"Retrieved {len(geofences)} geofences",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
            
        except Exception as e:
            logger.error(f"Error getting geofences: {e}")
            raise BusinessLogicError("Failed to retrieve geofences")


@router.put("/geofences/{geofence_id}")
async def update_geofence(
    request: Request,
    geofence_id: str,
    geofence_data: GeofenceUpdateRequest,
    current_user = Depends(require_permission("gps:write"))
):
    """Update a geofence"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            updated_geofence = await geofence_service.update_geofence(
                geofence_id=geofence_id,
                name=geofence_data.name,
                description=geofence_data.description,
                geometry=geofence_data.geometry,
                is_active=geofence_data.is_active,
                metadata=geofence_data.metadata
            )
            
            if not updated_geofence:
                raise HTTPException(status_code=404, detail="Geofence not found")
            
            return ResponseBuilder.success(
                data=updated_geofence.model_dump(),
                message="Geofence updated successfully",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating geofence: {e}")
            raise BusinessLogicError("Failed to update geofence")


@router.delete("/geofences/{geofence_id}")
async def delete_geofence(
    request: Request,
    geofence_id: str,
    current_user = Depends(require_permission("gps:write"))
):
    """Delete a geofence"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            success = await geofence_service.delete_geofence(geofence_id)
            
            if not success:
                raise HTTPException(status_code=404, detail="Geofence not found")
            
            return ResponseBuilder.success(
                data={"geofence_id": geofence_id, "deleted": True},
                message="Geofence deleted successfully",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting geofence: {e}")
            raise BusinessLogicError("Failed to delete geofence")


@router.get("/geofences/{geofence_id}/events")
async def get_geofence_events(
    request: Request,
    geofence_id: str,
    vehicle_id: Optional[str] = Query(None, description="Filter by vehicle ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum number of records"),
    current_user = Depends(require_permission("gps:read"))
):
    """Get events for a geofence"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            events = await geofence_service.get_geofence_events(
                geofence_id=geofence_id,
                vehicle_id=vehicle_id,
                event_type=event_type,
                limit=limit
            )
            
            return ResponseBuilder.success(
                data=[event.model_dump() for event in events],
                message=f"Retrieved {len(events)} geofence events",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
            
        except Exception as e:
            logger.error(f"Error getting geofence events: {e}")
            raise BusinessLogicError("Failed to retrieve geofence events")


@router.get("/geofences/{geofence_id}/statistics")
async def get_geofence_statistics(
    request: Request,
    geofence_id: str,
    current_user = Depends(require_permission("gps:read"))
):
    """Get statistics for a geofence"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            stats = await geofence_service.get_geofence_statistics(geofence_id)
            
            return ResponseBuilder.success(
                data=stats,
                message="Geofence statistics retrieved successfully",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
            
        except Exception as e:
            logger.error(f"Error getting geofence statistics: {e}")
            raise BusinessLogicError("Failed to retrieve geofence statistics")
