"""
Trip management API routes
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import List, Optional, Dict, Any
from datetime import datetime

from schemas.requests import (
    CreateTripRequest, UpdateTripRequest, TripFilterRequest, 
    TripProgressRequest, RouteOptimizationRequest
)
from schemas.responses import (
    ResponseBuilder
)
from schemas.entities import Trip, TripStatus
from services.trip_service import trip_service
from services.constraint_service import constraint_service
from api.dependencies import get_current_user, validate_trip_access

router = APIRouter()


@router.post("/", response_model=Dict[str, Any])
async def create_trip(
    request: CreateTripRequest,
    current_user: str = Depends(get_current_user)
):
    """Create a new trip"""
    try:
        trip = await trip_service.create_trip(request, current_user)
        return ResponseBuilder.success(
            data={"trip": trip.dict()},
            message="Trip created successfully"
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create trip")


@router.get("/", response_model=Dict[str, Any])
async def list_trips(
    status: Optional[List[TripStatus]] = Query(None),
    priority: Optional[List[str]] = Query(None),
    driver_id: Optional[str] = Query(None),
    vehicle_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    sort_by: str = Query("scheduled_start_time"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    current_user: str = Depends(get_current_user)
):
    """List trips with filtering and pagination"""
    try:
        filter_request = TripFilterRequest(
            status=status,
            priority=priority,
            driver_id=driver_id,
            vehicle_id=vehicle_id,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        trips, total = await trip_service.list_trips(filter_request)
        
        return ResponseBuilder.paginated(
            items=[trip.dict() for trip in trips],
            total=total,
            skip=skip,
            limit=limit,
            message="Trips retrieved successfully"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve trips")


@router.get("/{trip_id}", response_model=Dict[str, Any])
async def get_trip(
    trip_id: str,
    current_user: str = Depends(get_current_user),
    trip: Trip = Depends(validate_trip_access)
):
    """Get trip details by ID"""
    return ResponseBuilder.success(
        data={"trip": trip.dict()},
        message="Trip retrieved successfully"
    )


@router.put("/{trip_id}", response_model=Dict[str, Any])
async def update_trip(
    trip_id: str,
    request: UpdateTripRequest,
    current_user: str = Depends(get_current_user),
    trip: Trip = Depends(validate_trip_access)
):
    """Update a trip"""
    try:
        updated_trip = await trip_service.update_trip(trip_id, request, current_user)
        
        if not updated_trip:
            raise HTTPException(status_code=404, detail="Trip not found")
        
        return ResponseBuilder.success(
            data={"trip": updated_trip.dict()},
            message="Trip updated successfully"
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update trip")


@router.delete("/{trip_id}", response_model=Dict[str, Any])
async def delete_trip(
    trip_id: str,
    current_user: str = Depends(get_current_user),
    trip: Trip = Depends(validate_trip_access)
):
    """Delete a trip"""
    try:
        success = await trip_service.delete_trip(trip_id, current_user)
        
        if not success:
            raise HTTPException(status_code=404, detail="Trip not found")
        
        return ResponseBuilder.success(message="Trip deleted successfully")
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete trip")


@router.post("/{trip_id}/start", response_model=Dict[str, Any])
async def start_trip(
    trip_id: str,
    current_user: str = Depends(get_current_user),
    trip: Trip = Depends(validate_trip_access)
):
    """Start a trip"""
    try:
        started_trip = await trip_service.start_trip(trip_id, current_user)
        
        if not started_trip:
            raise HTTPException(status_code=404, detail="Trip not found")
        
        return ResponseBuilder.success(
            data={"trip": started_trip.dict()},
            message="Trip started successfully"
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to start trip")


@router.post("/{trip_id}/complete", response_model=Dict[str, Any])
async def complete_trip(
    trip_id: str,
    current_user: str = Depends(get_current_user),
    trip: Trip = Depends(validate_trip_access)
):
    """Complete a trip and move it to history"""
    try:
        completed_trip = await trip_service.complete_trip(trip_id, current_user)
        
        if not completed_trip:
            raise HTTPException(status_code=404, detail="Trip not found")
        
        return ResponseBuilder.success(
            data={"trip": completed_trip.dict()},
            message="Trip completed successfully and moved to history"
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to complete trip")
    
@router.post("/{trip_id}/pause", response_model=Dict[str, Any])
async def start_trip(
    trip_id: str,
    current_user: str = Depends(get_current_user),
    trip: Trip = Depends(validate_trip_access)
):
    """Start a trip"""
    try:
        started_trip = await trip_service.start_trip(trip_id, current_user)
        
        if not started_trip:
            raise HTTPException(status_code=404, detail="Trip not found")
        
        return ResponseBuilder.success(
            data={"trip": started_trip.dict()},
            message="Trip started successfully"
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to start trip")



@router.post("/{trip_id}/pause", response_model=Dict[str, Any])
async def pause_trip(
    trip_id: str,
    current_user: str = Depends(get_current_user),
    trip: Trip = Depends(validate_trip_access)
):

    """Pause a trip"""
    try:
        paused_trip = await trip_service.pause_trip(trip_id, current_user)
        
        if not paused_trip:
            raise HTTPException(status_code=404, detail="Trip not found")
        
        return ResponseBuilder.success(
            data={"trip": paused_trip.dict()},
            message="Trip paused successfully"
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to pause trip")


@router.post("/{trip_id}/resume", response_model=Dict[str, Any])
async def resume_trip(
    trip_id: str,
    current_user: str = Depends(get_current_user),
    trip: Trip = Depends(validate_trip_access)
):
    """Resume a paused trip"""
    try:
        resumed_trip = await trip_service.resume_trip(trip_id, current_user)
        
        if not resumed_trip:
            raise HTTPException(status_code=404, detail="Trip not found")
        
        return ResponseBuilder.success(
            data={"trip": resumed_trip.dict()},
            message="Trip resumed successfully"
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to resume trip")


@router.post("/{trip_id}/cancel", response_model=Dict[str, Any])
async def cancel_trip(
    trip_id: str,
    reason: Optional[str] = Body("User requested cancellation", embed=True),
    current_user: str = Depends(get_current_user),
    trip: Trip = Depends(validate_trip_access)
):
    """Cancel a trip and move it to history"""
    try:
        cancelled_trip = await trip_service.cancel_trip(trip_id, current_user, reason)
        
        if not cancelled_trip:
            raise HTTPException(status_code=404, detail="Trip not found")
        
        return ResponseBuilder.success(
            data={"trip": cancelled_trip.dict()},
            message="Trip cancelled successfully and moved to history"
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to cancel trip")

@router.post("/{trip_id}/optimize-route", response_model=Dict[str, Any])
async def optimize_trip_route(
    trip_id: str,
    request: RouteOptimizationRequest,
    current_user: str = Depends(get_current_user),
    trip: Trip = Depends(validate_trip_access)
):
    """Optimize trip route based on constraints"""
    try:
        # Get trip constraints
        constraints = await constraint_service.get_active_constraints_for_trip(trip_id)
        
        # Build route data
        route_data = {
            "origin": trip.origin.dict(),
            "destination": trip.destination.dict(),
            "waypoints": [wp.dict() for wp in trip.waypoints],
            "optimization_type": request.optimization_type,
            "avoid_traffic": request.avoid_traffic,
            "real_time": request.real_time
        }
        
        # Apply constraints
        optimized_route = await constraint_service.apply_constraints_to_route(trip_id, route_data)
        
        # Mock optimization results (would integrate with actual routing service)
        optimization_result = {
            "trip_id": trip_id,
            "original_duration": trip.estimated_duration or 120,
            "optimized_duration": max(60, (trip.estimated_duration or 120) - 15),
            "original_distance": trip.estimated_distance or 100.0,
            "optimized_distance": max(50.0, (trip.estimated_distance or 100.0) - 5.0),
            "time_saved": 15,
            "distance_saved": 5.0,
            "optimized_route": optimized_route
        }
        
        return ResponseBuilder.success(
            data=optimization_result,
            message="Route optimized successfully"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to optimize route")


@router.put("/{trip_id}/progress", response_model=Dict[str, Any])
async def update_trip_progress(
    trip_id: str,
    request: TripProgressRequest,
    current_user: str = Depends(get_current_user),
    trip: Trip = Depends(validate_trip_access)
):
    """Update trip progress"""
    try:
        # This would integrate with real-time tracking
        # For now, just return success
        
        progress_data = {
            "trip_id": trip_id,
            "current_location": request.current_location.dict(),
            "status": request.status,
            "estimated_arrival": request.estimated_arrival,
            "updated_at": datetime.utcnow()
        }
        
        return ResponseBuilder.success(
            data=progress_data,
            message="Trip progress updated successfully"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update trip progress")


@router.get("/{trip_id}/status", response_model=Dict[str, Any])
async def get_trip_status(
    trip_id: str,
    current_user: str = Depends(get_current_user),
    trip: Trip = Depends(validate_trip_access)
):
    """Get current trip status and progress"""
    try:
        status_data = {
            "trip_id": trip.id,
            "status": trip.status,
            "scheduled_start_time": trip.scheduled_start_time,
            "actual_start_time": trip.actual_start_time,
            "actual_end_time": trip.actual_end_time,
            "estimated_duration": trip.estimated_duration,
            "estimated_distance": trip.estimated_distance,
            "driver_assignment": trip.driver_assignment.dict() if trip.driver_assignment else None,
            "vehicle_id": trip.vehicle_id
        }
        
        return ResponseBuilder.success(
            data=status_data,
            message="Trip status retrieved successfully"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get trip status")


@router.get("/driver/{driver_id}/upcoming", response_model=Dict[str, Any])
async def get_upcoming_trips(
    driver_id: str,
    limit: int = Query(10, ge=1, le=50),
    current_user: str = Depends(get_current_user)
):
    """Get upcoming trips for a specific driver"""
    try:
        trips = await trip_service.get_upcoming_trips(driver_id, limit)
        
        return ResponseBuilder.success(
            data={
                "trips": [trip.dict() for trip in trips],
                "count": len(trips)
            },
            message=f"Found {len(trips)} upcoming trips"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get upcoming trips")


@router.get("/driver/{driver_id}/recent", response_model=Dict[str, Any])
async def get_recent_trips(
    driver_id: str,
    limit: int = Query(10, ge=1, le=50),
    days: int = Query(30, ge=1, le=365),
    current_user: str = Depends(get_current_user)
):
    """Get recent completed trips for a specific driver"""
    try:
        trips = await trip_service.get_recent_trips(driver_id, limit, days)
        
        return ResponseBuilder.success(
            data={
                "trips": [trip.dict() for trip in trips],
                "count": len(trips)
            },
            message=f"Found {len(trips)} recent trips"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get recent trips")


@router.get("/recent", response_model=Dict[str, Any])
async def get_all_recent_trips(
    limit: int = Query(10, ge=1, le=50),
    days: int = Query(30, ge=1, le=365),
    current_user: str = Depends(get_current_user)
):
    """Get recent completed trips for all drivers"""
    try:
        trips = await trip_service.get_all_recent_trips(limit, days)
        
        return ResponseBuilder.success(
            data={
                "trips": [trip.dict() for trip in trips],
                "count": len(trips)
            },
            message=f"Found {len(trips)} recent trips"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get recent trips")
