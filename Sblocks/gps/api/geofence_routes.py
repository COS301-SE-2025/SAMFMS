"""
Geofence API Routes for GPS Tracking System

Handles geofence management, monitoring, and events.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

from models.geofence import Geofence, GeofenceEvent, GeofenceType
from models.location import Coordinate
from services.geofence_service import GeofenceService
from utils.analytics import analyze_geofence_events, calculate_dwell_time

router = APIRouter(prefix="/geofences", tags=["geofences"])

# Dependency injection
async def get_geofence_service() -> GeofenceService:
    service = GeofenceService()
    await service.initialize()
    return service


# Request/Response models
class GeofenceCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    shape: str  # "circle" or "polygon"
    fence_type: GeofenceType
    center: Optional[Coordinate] = None  # Required for circle
    radius: Optional[float] = None  # Required for circle, in kilometers
    coordinates: Optional[List[Coordinate]] = None  # Required for polygon
    is_active: bool = True
    metadata: Dict[str, Any] = {}


class GeofenceUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class GeofenceEventsResponse(BaseModel):
    geofence_id: str
    events: List[GeofenceEvent]
    total_count: int
    analytics: dict


@router.post("/", response_model=Geofence)
async def create_geofence(
    request: GeofenceCreateRequest,
    service: GeofenceService = Depends(get_geofence_service)
):
    """Create a new geofence"""
    try:
        # Validate shape-specific requirements
        if request.shape == "circle":
            if not request.center or request.radius is None:
                raise HTTPException(
                    status_code=400, 
                    detail="Circle geofence requires center and radius"
                )
        elif request.shape == "polygon":
            if not request.coordinates or len(request.coordinates) < 3:
                raise HTTPException(
                    status_code=400,
                    detail="Polygon geofence requires at least 3 coordinates"
                )
        else:
            raise HTTPException(
                status_code=400,
                detail="Shape must be 'circle' or 'polygon'"
            )
        
        geofence_data = request.dict()
        geofence = await service.create_geofence(geofence_data)
        return geofence
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[Geofence])
async def get_geofences(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    fence_type: Optional[GeofenceType] = Query(None, description="Filter by fence type"),
    limit: int = Query(100, ge=1, le=1000),
    service: GeofenceService = Depends(get_geofence_service)
):
    """Get all geofences with optional filtering"""
    try:
        geofences = await service.get_geofences(
            is_active=is_active,
            fence_type=fence_type,
            limit=limit
        )
        return geofences
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{geofence_id}", response_model=Geofence)
async def get_geofence(
    geofence_id: str,
    service: GeofenceService = Depends(get_geofence_service)
):
    """Get a specific geofence by ID"""
    try:
        geofence = await service.get_geofence(geofence_id)
        if geofence:
            return geofence
        else:
            raise HTTPException(status_code=404, detail="Geofence not found")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{geofence_id}", response_model=Geofence)
async def update_geofence(
    geofence_id: str,
    request: GeofenceUpdateRequest,
    service: GeofenceService = Depends(get_geofence_service)
):
    """Update a geofence"""
    try:
        # Get existing geofence first
        existing_geofence = await service.get_geofence(geofence_id)
        if not existing_geofence:
            raise HTTPException(status_code=404, detail="Geofence not found")
        
        update_data = {k: v for k, v in request.dict().items() if v is not None}
        success = await service.update_geofence(geofence_id, update_data)
        
        if success:
            updated_geofence = await service.get_geofence(geofence_id)
            return updated_geofence
        else:
            raise HTTPException(status_code=500, detail="Failed to update geofence")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{geofence_id}")
async def delete_geofence(
    geofence_id: str,
    service: GeofenceService = Depends(get_geofence_service)
):
    """Delete a geofence"""
    try:
        success = await service.delete_geofence(geofence_id)
        if success:
            return {"message": "Geofence deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Geofence not found")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{geofence_id}/events", response_model=GeofenceEventsResponse)
async def get_geofence_events(
    geofence_id: str,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    vehicle_id: Optional[str] = Query(None, description="Filter by vehicle"),
    limit: int = Query(100, ge=1, le=1000),
    include_analytics: bool = Query(True, description="Include event analytics"),
    service: GeofenceService = Depends(get_geofence_service)
):
    """Get events for a specific geofence"""
    try:
        # Set default time range
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(days=7)  # Last 7 days
        
        events = await service.get_geofence_events(
            geofence_id=geofence_id,
            start_time=start_time,
            end_time=end_time,
            event_type=event_type,
            vehicle_id=vehicle_id,
            limit=limit
        )
        
        response_data = {
            "geofence_id": geofence_id,
            "events": events,
            "total_count": len(events),
            "analytics": {}
        }
        
        if include_analytics and events:
            response_data["analytics"] = analyze_geofence_events(events)
        
        return response_data
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{geofence_id}/dwell-time/{vehicle_id}")
async def get_dwell_time(
    geofence_id: str,
    vehicle_id: str,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    service: GeofenceService = Depends(get_geofence_service)
):
    """Calculate dwell time for a vehicle in a geofence"""
    try:
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(days=7)
        
        dwell_data = await service.calculate_dwell_time(
            geofence_id=geofence_id,
            vehicle_id=vehicle_id,
            start_time=start_time,
            end_time=end_time
        )
        
        return {
            "geofence_id": geofence_id,
            "vehicle_id": vehicle_id,
            "period": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            },
            "dwell_analysis": dwell_data
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{geofence_id}/check-vehicle/{vehicle_id}")
async def check_vehicle_in_geofence(
    geofence_id: str,
    vehicle_id: str,
    service: GeofenceService = Depends(get_geofence_service)
):
    """Check if a vehicle is currently in a geofence"""
    try:
        is_inside = await service.check_vehicle_in_geofence(vehicle_id, geofence_id)
        
        return {
            "geofence_id": geofence_id,
            "vehicle_id": vehicle_id,
            "is_inside": is_inside,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{geofence_id}/vehicles")
async def get_vehicles_in_geofence(
    geofence_id: str,
    service: GeofenceService = Depends(get_geofence_service)
):
    """Get all vehicles currently in a geofence"""
    try:
        vehicles = await service.get_vehicles_in_geofence(geofence_id)
        
        return {
            "geofence_id": geofence_id,
            "vehicle_count": len(vehicles),
            "vehicles": vehicles,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{geofence_id}/enable")
async def enable_geofence(
    geofence_id: str,
    service: GeofenceService = Depends(get_geofence_service)
):
    """Enable a geofence"""
    try:
        success = await service.update_geofence(geofence_id, {"is_active": True})
        if success:
            return {"message": "Geofence enabled successfully"}
        else:
            raise HTTPException(status_code=404, detail="Geofence not found")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{geofence_id}/disable")
async def disable_geofence(
    geofence_id: str,
    service: GeofenceService = Depends(get_geofence_service)
):
    """Disable a geofence"""
    try:
        success = await service.update_geofence(geofence_id, {"is_active": False})
        if success:
            return {"message": "Geofence disabled successfully"}
        else:
            raise HTTPException(status_code=404, detail="Geofence not found")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/recent")
async def get_recent_geofence_events(
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    event_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    service: GeofenceService = Depends(get_geofence_service)
):
    """Get recent geofence events across all geofences"""
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        events = await service.get_recent_events(
            start_time=start_time,
            event_type=event_type,
            limit=limit
        )
        
        return {
            "period": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "hours": hours
            },
            "events": events,
            "count": len(events)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/summary")
async def get_geofence_analytics_summary(
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    service: GeofenceService = Depends(get_geofence_service)
):
    """Get overall geofence analytics summary"""
    try:
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(days=7)
        
        # Get all events in the time period
        all_events = await service.get_recent_events(
            start_time=start_time,
            limit=10000  # High limit to get comprehensive data
        )
        
        analytics = analyze_geofence_events(all_events)
        
        return {
            "period": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            },
            "analytics": analytics
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
