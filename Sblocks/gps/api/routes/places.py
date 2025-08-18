"""
Places API routes
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from typing import Optional, List
import logging

from services.places_service import places_service
from api.dependencies import get_current_user, require_permission, get_request_id, RequestTimer
from schemas.responses import ResponseBuilder
from schemas.requests import PlaceCreateRequest, PlaceUpdateRequest, PlaceSearchRequest, NearbyPlacesRequest
from api.exception_handlers import BusinessLogicError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/places")
async def create_place(
    request: Request,
    place_data: PlaceCreateRequest,
    current_user = Depends(require_permission("gps:write"))
):
    """Create a new place"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            user_id = current_user.get('user_id')
            
            place = await places_service.create_place(
                user_id=user_id,
                name=place_data.name,
                description=place_data.description,
                latitude=place_data.latitude,
                longitude=place_data.longitude,
                address=place_data.address,
                place_type=place_data.place_type,
                metadata=place_data.metadata,
                created_by=user_id
            )
            
            return ResponseBuilder.success(
                data=place.model_dump(),
                message="Place created successfully",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
            
        except Exception as e:
            logger.error(f"Error creating place: {e}")
            raise BusinessLogicError("Failed to create place")


@router.get("/places/{place_id}")
async def get_place(
    request: Request,
    place_id: str,
    current_user = Depends(require_permission("gps:read"))
):
    """Get a place by ID"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            place = await places_service.get_place(place_id)
            
            if not place:
                raise HTTPException(status_code=404, detail="Place not found")
            
            # Check if user has access to this place
            user_id = current_user.get('user_id')
            if place.user_id != user_id and not current_user.get('is_admin', False):
                raise HTTPException(status_code=403, detail="Access denied")
            
            return ResponseBuilder.success(
                data=place.model_dump(),
                message="Place retrieved successfully",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting place: {e}")
            raise BusinessLogicError("Failed to retrieve place")


@router.get("/places")
async def get_user_places(
    request: Request,
    place_type: Optional[str] = Query(None, description="Filter by place type"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    current_user = Depends(require_permission("gps:read"))
):
    """Get places for the current user"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            user_id = current_user.get('user_id')
            
            places = await places_service.get_user_places(
                user_id=user_id,
                place_type=place_type,
                limit=limit,
                offset=offset
            )
            
            return ResponseBuilder.success(
                data=[place.model_dump() for place in places],
                message=f"Retrieved {len(places)} places",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
            
        except Exception as e:
            logger.error(f"Error getting user places: {e}")
            raise BusinessLogicError("Failed to retrieve places")


@router.post("/places/search")
async def search_places(
    request: Request,
    search_data: PlaceSearchRequest,
    current_user = Depends(require_permission("gps:read"))
):
    """Search places by name or description"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            user_id = current_user.get('user_id')
            
            places = await places_service.search_places(
                user_id=user_id,
                search_term=search_data.search_term,
                limit=search_data.limit
            )
            
            return ResponseBuilder.success(
                data=[place.model_dump() for place in places],
                message=f"Found {len(places)} places matching search",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
            
        except Exception as e:
            logger.error(f"Error searching places: {e}")
            raise BusinessLogicError("Failed to search places")


@router.post("/places/nearby")
async def get_nearby_places(
    request: Request,
    location_data: NearbyPlacesRequest,
    current_user = Depends(require_permission("gps:read"))
):
    """Get places near a location"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            user_id = current_user.get('user_id')
            
            places = await places_service.get_places_near_location(
                user_id=user_id,
                latitude=location_data.latitude,
                longitude=location_data.longitude,
                radius_meters=location_data.radius_meters,
                limit=location_data.limit
            )
            
            return ResponseBuilder.success(
                data=[place.model_dump() for place in places],
                message=f"Found {len(places)} places nearby",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
            
        except Exception as e:
            logger.error(f"Error getting nearby places: {e}")
            raise BusinessLogicError("Failed to retrieve nearby places")


@router.put("/places/{place_id}")
async def update_place(
    request: Request,
    place_id: str,
    place_data: PlaceUpdateRequest,
    current_user = Depends(require_permission("gps:write"))
):
    """Update a place"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            user_id = current_user.get('user_id')
            
            updated_place = await places_service.update_place(
                place_id=place_id,
                user_id=user_id,
                name=place_data.name,
                description=place_data.description,
                latitude=place_data.latitude,
                longitude=place_data.longitude,
                address=place_data.address,
                place_type=place_data.place_type,
                metadata=place_data.metadata
            )
            
            if not updated_place:
                raise HTTPException(status_code=404, detail="Place not found or access denied")
            
            return ResponseBuilder.success(
                data=updated_place.model_dump(),
                message="Place updated successfully",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating place: {e}")
            raise BusinessLogicError("Failed to update place")


@router.delete("/places/{place_id}")
async def delete_place(
    request: Request,
    place_id: str,
    current_user = Depends(require_permission("gps:write"))
):
    """Delete a place"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            user_id = current_user.get('user_id')
            
            success = await places_service.delete_place(place_id, user_id)
            
            if not success:
                raise HTTPException(status_code=404, detail="Place not found or access denied")
            
            return ResponseBuilder.success(
                data={"place_id": place_id, "deleted": True},
                message="Place deleted successfully",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting place: {e}")
            raise BusinessLogicError("Failed to delete place")


@router.get("/places/statistics")
async def get_place_statistics(
    request: Request,
    current_user = Depends(require_permission("gps:read"))
):
    """Get statistics for user's places"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            user_id = current_user.get('user_id')
            
            stats = await places_service.get_place_statistics(user_id)
            
            return ResponseBuilder.success(
                data=stats,
                message="Place statistics retrieved successfully",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
            
        except Exception as e:
            logger.error(f"Error getting place statistics: {e}")
            raise BusinessLogicError("Failed to retrieve place statistics")
