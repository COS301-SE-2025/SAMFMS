"""
API routes for driver management
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime

from services.drivers_service import drivers_service
from schemas.requests import DailyDriverCount

router = APIRouter(prefix="/drivers", tags=["drivers"])


@router.post("/daily-driver-count", response_model=Dict[str, Any])
async def get_daily_driver_counts(
    request: DailyDriverCount
):
    """Get all count of drivers by day"""
    try:
        result = await drivers_service.get_daily_driver_counts(request.date)
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")