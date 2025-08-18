"""
Location tracking API routes
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Request, BackgroundTasks
from typing import Optional, List
import logging
from datetime import datetime

from services.location_service import location_service
from services.geofence_service import geofence_service
from api.dependencies import get_current_user, require_permission, get_request_id, RequestTimer
from schemas.responses import ResponseBuilder
from schemas.requests import LocationUpdateRequest, LocationHistoryRequest, TrackingSessionRequest, VehicleSearchRequest
from api.exception_handlers import BusinessLogicError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/locations/update")
async def update_vehicle_location(
    request: Request,
    location_data: LocationUpdateRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(require_permission("gps:write"))
):
    """Update vehicle location"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            logger.info(f"Location update for vehicle {location_data.vehicle_id}")
            
            # Update location
            updated_location = await location_service.update_vehicle_location(
                vehicle_id=location_data.vehicle_id,
                latitude=location_data.latitude,
                longitude=location_data.longitude,
                altitude=location_data.altitude,
                speed=location_data.speed,
                heading=location_data.heading,
                accuracy=location_data.accuracy,
                timestamp=location_data.timestamp
            )
            
            # Check geofences in background
            background_tasks.add_task(
                check_geofences_for_location,
                location_data.vehicle_id,
                location_data.latitude,
                location_data.longitude
            )
            
            return ResponseBuilder.success(
                data=updated_location.model_dump(),
                message="Vehicle location updated successfully",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
            
        except Exception as e:
            logger.error(f"Error updating vehicle location: {e}")
            raise BusinessLogicError("Failed to update vehicle location")


@router.get("/locations/{vehicle_id}")
async def get_vehicle_location(
    request: Request,
    vehicle_id: str,
    current_user = Depends(require_permission("gps:read"))
):
    """Get current location of a vehicle"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            location = await location_service.get_vehicle_location(vehicle_id)
            
            if not location:
                raise HTTPException(status_code=404, detail="Vehicle location not found")
            
            return ResponseBuilder.success(
                data=location.model_dump(),
                message="Vehicle location retrieved successfully",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting vehicle location: {e}")
            raise BusinessLogicError("Failed to retrieve vehicle location")


@router.get("/locations")
async def get_multiple_vehicle_locations(
    request: Request,
    vehicle_ids: str = Query(..., description="Comma-separated vehicle IDs"),
    current_user = Depends(require_permission("gps:read"))
):
    """Get current locations of multiple vehicles"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            vehicle_id_list = [vid.strip() for vid in vehicle_ids.split(",") if vid.strip()]
            
            if not vehicle_id_list:
                raise HTTPException(status_code=400, detail="No vehicle IDs provided")
            
            locations = await location_service.get_multiple_vehicle_locations(vehicle_id_list)
            
            return ResponseBuilder.success(
                data=[loc.model_dump() for loc in locations],
                message=f"Retrieved locations for {len(locations)} vehicles",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting multiple vehicle locations: {e}")
            raise BusinessLogicError("Failed to retrieve vehicle locations")


@router.get("/locations/{vehicle_id}/history")
async def get_location_history(
    request: Request,
    vehicle_id: str,
    start_time: Optional[datetime] = Query(None, description="Start time for history"),
    end_time: Optional[datetime] = Query(None, description="End time for history"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum number of records"),
    current_user = Depends(require_permission("gps:read"))
):
    """Get location history for a vehicle"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            history = await location_service.get_location_history(
                vehicle_id=vehicle_id,
                start_time=start_time,
                end_time=end_time,
                limit=limit
            )
            
            return ResponseBuilder.success(
                data=[loc.model_dump() for loc in history],
                message=f"Retrieved {len(history)} location history records",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
            
        except Exception as e:
            logger.error(f"Error getting location history: {e}")
            raise BusinessLogicError("Failed to retrieve location history")


@router.post("/locations/search/area")
async def search_vehicles_in_area(
    request: Request,
    search_data: VehicleSearchRequest,
    current_user = Depends(require_permission("gps:read"))
):
    """Search for vehicles within a circular area"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            vehicles = await location_service.get_vehicles_in_area(
                center_lat=search_data.center_latitude,
                center_lng=search_data.center_longitude,
                radius_meters=search_data.radius_meters
            )
            
            return ResponseBuilder.success(
                data=[vehicle.model_dump() for vehicle in vehicles],
                message=f"Found {len(vehicles)} vehicles in area",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
            
        except Exception as e:
            logger.error(f"Error searching vehicles in area: {e}")
            raise BusinessLogicError("Failed to search vehicles in area")


# Background task function
async def check_geofences_for_location(vehicle_id: str, latitude: float, longitude: float):
    """Background task to check geofence events"""
    try:
        # Check which geofences the vehicle is in
        intersecting_geofences = await geofence_service.check_vehicle_geofences(
            vehicle_id, latitude, longitude
        )
        
        # Record geofence events if needed
        for geofence in intersecting_geofences:
            await geofence_service.record_geofence_event(
                vehicle_id=vehicle_id,
                geofence_id=geofence.id,
                event_type="enter",  # This would need more sophisticated logic
                latitude=latitude,
                longitude=longitude
            )
            
    except Exception as e:
        logger.error(f"Error checking geofences for location: {e}")
