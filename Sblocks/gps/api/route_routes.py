"""
Route API Routes for GPS Tracking System

Handles route management, tracking, and analytics.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

from ..models.route import VehicleRoute, RouteStatus, RoutePoint
from ..models.location import Coordinate
from ..services.route_service import RouteService
from ..utils.analytics import calculate_route_efficiency

router = APIRouter(prefix="/routes", tags=["routes"])

# Dependency injection
async def get_route_service() -> RouteService:
    service = RouteService()
    await service.initialize()
    return service


# Request/Response models
class RouteCreateRequest(BaseModel):
    vehicle_id: str
    trip_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    waypoints: List[Coordinate]
    planned_distance: Optional[float] = None
    estimated_duration: Optional[float] = None
    metadata: Dict[str, Any] = {}


class RouteUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[RouteStatus] = None
    metadata: Optional[Dict[str, Any]] = None


class RouteAnalyticsResponse(BaseModel):
    route_id: str
    analytics: dict
    efficiency: dict


@router.post("/", response_model=VehicleRoute)
async def create_route(
    request: RouteCreateRequest,
    service: RouteService = Depends(get_route_service)
):
    """Create a new vehicle route"""
    try:
        route_data = request.dict()
        route = await service.create_route(route_data)
        return route
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[VehicleRoute])
async def get_routes(
    vehicle_id: Optional[str] = Query(None, description="Filter by vehicle ID"),
    status: Optional[RouteStatus] = Query(None, description="Filter by route status"),
    trip_id: Optional[str] = Query(None, description="Filter by trip ID"),
    limit: int = Query(100, ge=1, le=1000),
    service: RouteService = Depends(get_route_service)
):
    """Get routes with optional filtering"""
    try:
        if vehicle_id:
            routes = await service.get_vehicle_routes(
                vehicle_id=vehicle_id,
                status=status,
                limit=limit
            )
        else:
            # Get all routes (you may want to implement this in the service)
            routes = await service.get_active_routes() if status in [RouteStatus.ACTIVE, RouteStatus.IN_PROGRESS] else []
        
        # Filter by trip_id if provided
        if trip_id:
            routes = [route for route in routes if route.trip_id == trip_id]
        
        return routes[:limit]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{route_id}", response_model=VehicleRoute)
async def get_route(
    route_id: str,
    service: RouteService = Depends(get_route_service)
):
    """Get a specific route by ID"""
    try:
        route = await service.get_route(route_id)
        if route:
            return route
        else:
            raise HTTPException(status_code=404, detail="Route not found")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{route_id}", response_model=VehicleRoute)
async def update_route(
    route_id: str,
    request: RouteUpdateRequest,
    service: RouteService = Depends(get_route_service)
):
    """Update a route"""
    try:
        # Get existing route first
        existing_route = await service.get_route(route_id)
        if not existing_route:
            raise HTTPException(status_code=404, detail="Route not found")
        
        # Handle status update separately if provided
        if request.status:
            await service.update_route_status(route_id, request.status)
        
        # Handle other updates
        update_data = {k: v for k, v in request.dict().items() if v is not None and k != "status"}
        if update_data:
            # Note: You may need to implement a general update method in RouteService
            pass
        
        updated_route = await service.get_route(route_id)
        return updated_route
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{route_id}")
async def delete_route(
    route_id: str,
    service: RouteService = Depends(get_route_service)
):
    """Delete a route"""
    try:
        success = await service.delete_route(route_id)
        if success:
            return {"message": "Route deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Route not found")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{route_id}/start")
async def start_route(
    route_id: str,
    service: RouteService = Depends(get_route_service)
):
    """Start a route (set status to IN_PROGRESS)"""
    try:
        success = await service.update_route_status(route_id, RouteStatus.IN_PROGRESS)
        if success:
            return {"message": "Route started successfully", "status": RouteStatus.IN_PROGRESS}
        else:
            raise HTTPException(status_code=404, detail="Route not found")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{route_id}/complete")
async def complete_route(
    route_id: str,
    service: RouteService = Depends(get_route_service)
):
    """Complete a route (set status to COMPLETED)"""
    try:
        success = await service.update_route_status(route_id, RouteStatus.COMPLETED)
        if success:
            return {"message": "Route completed successfully", "status": RouteStatus.COMPLETED}
        else:
            raise HTTPException(status_code=404, detail="Route not found")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{route_id}/cancel")
async def cancel_route(
    route_id: str,
    service: RouteService = Depends(get_route_service)
):
    """Cancel a route (set status to CANCELLED)"""
    try:
        success = await service.update_route_status(route_id, RouteStatus.CANCELLED)
        if success:
            return {"message": "Route cancelled successfully", "status": RouteStatus.CANCELLED}
        else:
            raise HTTPException(status_code=404, detail="Route not found")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{route_id}/analytics", response_model=RouteAnalyticsResponse)
async def get_route_analytics(
    route_id: str,
    service: RouteService = Depends(get_route_service)
):
    """Get analytics for a specific route"""
    try:
        route = await service.get_route(route_id)
        if not route:
            raise HTTPException(status_code=404, detail="Route not found")
        
        analytics = await service.get_route_analytics(route_id)
        efficiency = calculate_route_efficiency(route)
        
        return {
            "route_id": route_id,
            "analytics": analytics,
            "efficiency": efficiency
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{route_id}/events")
async def add_route_event(
    route_id: str,
    event_type: str,
    description: str,
    data: Optional[Dict[str, Any]] = None,
    service: RouteService = Depends(get_route_service)
):
    """Add an event to a route"""
    try:
        success = await service.add_route_event(
            route_id=route_id,
            event_type=event_type,
            description=description,
            data=data or {}
        )
        
        if success:
            return {
                "message": "Event added successfully",
                "route_id": route_id,
                "event_type": event_type
            }
        else:
            raise HTTPException(status_code=404, detail="Route not found")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{route_id}/progress")
async def get_route_progress(
    route_id: str,
    service: RouteService = Depends(get_route_service)
):
    """Get current progress of a route"""
    try:
        route = await service.get_route(route_id)
        if not route:
            raise HTTPException(status_code=404, detail="Route not found")
        
        progress_data = {
            "route_id": route_id,
            "status": route.status,
            "current_progress": route.current_progress or 0,
            "distance_remaining": route.distance_remaining,
            "total_distance": route.total_distance,
            "points_tracked": len(route.route_points) if route.route_points else 0,
            "last_updated": route.updated_at.isoformat() if route.updated_at else None
        }
        
        # Calculate ETA if route is in progress
        if route.status == RouteStatus.IN_PROGRESS and route.route_points:
            last_point = route.route_points[-1]
            if last_point.speed and route.distance_remaining:
                eta_hours = route.distance_remaining / last_point.speed
                eta_time = datetime.utcnow() + timedelta(hours=eta_hours)
                progress_data["estimated_arrival"] = eta_time.isoformat()
        
        return progress_data
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active/summary")
async def get_active_routes_summary(
    service: RouteService = Depends(get_route_service)
):
    """Get summary of all active routes"""
    try:
        active_routes = await service.get_active_routes()
        
        summary = {
            "total_active_routes": len(active_routes),
            "routes_by_status": {},
            "routes": []
        }
        
        # Count by status
        status_counts = {}
        for route in active_routes:
            status = route.status
            status_counts[status] = status_counts.get(status, 0) + 1
            
            summary["routes"].append({
                "route_id": route.id,
                "vehicle_id": route.vehicle_id,
                "trip_id": route.trip_id,
                "status": route.status,
                "progress": route.current_progress or 0,
                "last_updated": route.updated_at.isoformat() if route.updated_at else None
            })
        
        summary["routes_by_status"] = status_counts
        
        return summary
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vehicle/{vehicle_id}/current")
async def get_current_vehicle_route(
    vehicle_id: str,
    service: RouteService = Depends(get_route_service)
):
    """Get current active route for a vehicle"""
    try:
        routes = await service.get_vehicle_routes(
            vehicle_id=vehicle_id,
            status=RouteStatus.IN_PROGRESS,
            limit=1
        )
        
        if routes:
            current_route = routes[0]
            return {
                "vehicle_id": vehicle_id,
                "current_route": current_route,
                "has_active_route": True
            }
        else:
            return {
                "vehicle_id": vehicle_id,
                "current_route": None,
                "has_active_route": False
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
