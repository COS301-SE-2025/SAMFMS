"""
Vehicle availability API routes
"""
import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime

from schemas.responses import ResponseBuilder
from services.vehicle_service import vehicle_service
from api.dependencies import get_current_user_legacy as get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=Dict[str, Any])
async def get_all_vehicles(
    status: Optional[str] = Query(None, description="Filter by vehicle status"),
    skip: int = Query(0, ge=0, description="Number of vehicles to skip"),
    limit: int = Query(100, ge=1, le=500, description="Number of vehicles to return"),
    current_user: str = Depends(get_current_user)
):
    """Get all vehicles from the vehicles collection"""
    try:
        result = await vehicle_service.get_all_vehicles(
            status=status,
            skip=skip,
            limit=limit
        )
        
        return ResponseBuilder.success(
            data=result,
            message=f"Retrieved {len(result['vehicles'])} vehicles successfully"
        )
    
    except Exception as e:
        logger.error(f"Error getting all vehicles: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve vehicles")


@router.get("/{vehicle_id}/availability", response_model=Dict[str, Any])
async def check_single_vehicle_availability(
    vehicle_id: str,
    start_time: datetime = Query(..., description="Start of time period"),
    end_time: datetime = Query(..., description="End of time period"),
    current_user: str = Depends(get_current_user)
):
    """Check if a specific vehicle is available in a given timeframe"""
    try:
        if end_time <= start_time:
            raise HTTPException(status_code=400, detail="End time must be after start time")
        
        # Check vehicle availability using the vehicle service method
        is_available = await vehicle_service.check_vehicle_availability(
            vehicle_id, start_time, end_time
        )
        
        return ResponseBuilder.success(
            data={
                "vehicle_id": vehicle_id,
                "is_available": is_available,
                "start_time": start_time,
                "end_time": end_time
            },
            message=f"Vehicle availability checked successfully"
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error checking vehicle {vehicle_id} availability: {e}")
        raise HTTPException(status_code=500, detail="Failed to check vehicle availability")


@router.get("/available", response_model=Dict[str, Any])
async def get_available_vehicles(
    start_time: datetime = Query(..., description="Start of time period"),
    end_time: datetime = Query(..., description="End of time period"),
    skip: int = Query(0, ge=0, description="Number of vehicles to skip"),
    limit: int = Query(100, ge=1, le=500, description="Number of vehicles to return"),
    current_user: str = Depends(get_current_user)
):
    """Get all vehicles that are available within a given timeframe"""
    try:
        if end_time <= start_time:
            raise HTTPException(status_code=400, detail="End time must be after start time")
        
        result = await vehicle_service.get_available_vehicles(
            start_time, end_time, skip, limit
        )
        
        return ResponseBuilder.success(
            data={
                "vehicles": result["vehicles"],
                "total_available": result["total_available"],
                "total_checked": result["total_checked"],
                "skip": result["skip"],
                "limit": result["limit"],
                "timeframe": result["timeframe"]
            },
            message=f"Retrieved {len(result['vehicles'])} available vehicles successfully"
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting available vehicles: {e}")
        raise HTTPException(status_code=500, detail="Failed to get available vehicles")