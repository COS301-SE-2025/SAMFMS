"""
Location API Routes for GPS Tracking System

Handles location tracking, history, and real-time updates.
"""

from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

from services.location_service import LocationService
from models.location import VehicleLocation, LocationUpdate, LocationQuery, LocationResponse, HistoryResponse
from utils.analytics import calculate_vehicle_metrics, generate_time_series_data

router = APIRouter(prefix="/locations", tags=["locations"])

# Dependency injection
async def get_location_service() -> LocationService:
    service = LocationService()
    await service.initialize()
    return service


# Request/Response models
class LocationUpdateRequest(BaseModel):
    vehicle_id: str
    latitude: float
    longitude: float
    speed: Optional[float] = None
    heading: Optional[float] = None
    accuracy: Optional[float] = None
    altitude: Optional[float] = None
    status: Optional[str] = "active"


class LocationHistoryResponse(BaseModel):
    vehicle_id: str
    locations: List[VehicleLocation]
    total_count: int
    metrics: dict


@router.post("/update", response_model=dict)
async def update_location(
    request: LocationUpdateRequest,
    service: LocationService = Depends(get_location_service)
):
    """Update vehicle location"""
    try:
        location = VehicleLocation(
            vehicle_id=request.vehicle_id,
            latitude=request.latitude,
            longitude=request.longitude,
            speed=request.speed,
            heading=request.heading,
            accuracy=request.accuracy,
            altitude=request.altitude,
            status=request.status,
            timestamp=datetime.utcnow()
        )
        
        success = await service.update_location(location)
        if success:
            return {"message": "Location updated successfully", "timestamp": location.timestamp.isoformat()}
        else:
            raise HTTPException(status_code=500, detail="Failed to update location")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/current/{vehicle_id}", response_model=VehicleLocation)
async def get_current_location(
    vehicle_id: str,
    service: LocationService = Depends(get_location_service)
):
    """Get current location of a vehicle"""
    try:
        location = await service.get_current_location(vehicle_id)
        if location:
            return location
        else:
            raise HTTPException(status_code=404, detail="Vehicle location not found")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{vehicle_id}", response_model=LocationHistoryResponse)
async def get_location_history(
    vehicle_id: str,
    start_time: Optional[datetime] = Query(None, description="Start time for history"),
    end_time: Optional[datetime] = Query(None, description="End time for history"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of locations"),
    include_metrics: bool = Query(True, description="Include analytics metrics"),
    service: LocationService = Depends(get_location_service)
):
    """Get location history for a vehicle"""
    try:
        # Set default time range if not provided
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(hours=24)  # Last 24 hours
        
        locations = await service.get_location_history(
            vehicle_id=vehicle_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        
        response_data = {
            "vehicle_id": vehicle_id,
            "locations": locations,
            "total_count": len(locations),
            "metrics": {}
        }
        
        if include_metrics and locations:
            response_data["metrics"] = calculate_vehicle_metrics(locations)
        
        return response_data
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{vehicle_id}/timeseries")
async def get_location_timeseries(
    vehicle_id: str,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    interval_minutes: int = Query(5, ge=1, le=60, description="Time series interval in minutes"),
    service: LocationService = Depends(get_location_service)
):
    """Get location history as time series data for visualization"""
    try:
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(hours=24)
        
        locations = await service.get_location_history(
            vehicle_id=vehicle_id,
            start_time=start_time,
            end_time=end_time,
            limit=1000
        )
        
        timeseries_data = generate_time_series_data(locations, interval_minutes)
        
        return {
            "vehicle_id": vehicle_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "interval_minutes": interval_minutes,
            "data": timeseries_data
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nearby")
async def get_nearby_vehicles(
    latitude: float = Query(..., description="Center latitude"),
    longitude: float = Query(..., description="Center longitude"),
    radius_km: float = Query(10, ge=0.1, le=100, description="Search radius in kilometers"),
    service: LocationService = Depends(get_location_service)
):
    """Get vehicles near a specific location"""
    try:
        vehicles = await service.get_nearby_vehicles(latitude, longitude, radius_km)
        return {
            "center": {"latitude": latitude, "longitude": longitude},
            "radius_km": radius_km,
            "vehicles": vehicles,
            "count": len(vehicles)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/{vehicle_id}")
async def get_vehicle_analytics(
    vehicle_id: str,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    service: LocationService = Depends(get_location_service)
):
    """Get analytics for a vehicle's movement"""
    try:
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(hours=24)
        
        analytics = await service.get_location_analytics(
            vehicle_id=vehicle_id,
            start_time=start_time,
            end_time=end_time
        )
        
        return {
            "vehicle_id": vehicle_id,
            "period": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            },
            "analytics": analytics
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history/{vehicle_id}")
async def delete_location_history(
    vehicle_id: str,
    before_date: Optional[datetime] = Query(None, description="Delete history before this date"),
    service: LocationService = Depends(get_location_service)
):
    """Delete location history for a vehicle"""
    try:
        if not before_date:
            before_date = datetime.utcnow() - timedelta(days=30)  # Default: older than 30 days
        
        deleted_count = await service.delete_location_history(vehicle_id, before_date)
        
        return {
            "vehicle_id": vehicle_id,
            "deleted_count": deleted_count,
            "before_date": before_date.isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-update")
async def batch_update_locations(
    locations: List[LocationUpdateRequest],
    service: LocationService = Depends(get_location_service)
):
    """Update multiple vehicle locations in batch"""
    try:
        results = []
        
        for location_request in locations:
            location = VehicleLocation(
                vehicle_id=location_request.vehicle_id,
                latitude=location_request.latitude,
                longitude=location_request.longitude,
                speed=location_request.speed,
                heading=location_request.heading,
                accuracy=location_request.accuracy,
                altitude=location_request.altitude,
                status=location_request.status,
                timestamp=datetime.utcnow()
            )
            
            success = await service.update_location(location)
            results.append({
                "vehicle_id": location.vehicle_id,
                "success": success,
                "timestamp": location.timestamp.isoformat()
            })
        
        successful_updates = sum(1 for r in results if r["success"])
        
        return {
            "total_locations": len(locations),
            "successful_updates": successful_updates,
            "failed_updates": len(locations) - successful_updates,
            "results": results
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_location_service_status(
    service: LocationService = Depends(get_location_service)
):
    """Get location service status and statistics"""
    try:
        # Get recent activity
        now = datetime.utcnow()
        recent_updates = await service.get_recent_activity(
            start_time=now - timedelta(hours=1)
        )
        
        return {
            "service": "location_tracking",
            "status": "operational",
            "timestamp": now.isoformat(),
            "recent_activity": {
                "last_hour_updates": len(recent_updates),
                "active_vehicles": len(set(update.vehicle_id for update in recent_updates))
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
