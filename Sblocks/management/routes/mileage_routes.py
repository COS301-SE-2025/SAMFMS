"""
API routes for mileage management
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime

from services.mileage_service import mileage_service
from schemas.requests import MileageUpdateRequest

router = APIRouter(prefix="/mileage", tags=["mileage"])


@router.post("/update", response_model=Dict[str, Any])
async def update_vehicle_mileage(
    request: MileageUpdateRequest
):
    """Update vehicle mileage"""
    try:
        result = await mileage_service.update_vehicle_mileage(request, "system")
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/history/vehicle/{vehicle_id}", response_model=Dict[str, Any])
async def get_mileage_history(
    vehicle_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    """Get mileage history for a specific vehicle"""
    try:
        history = await mileage_service.get_mileage_history(
            vehicle_id, start_date, end_date
        )
        return {"success": True, "data": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/current/vehicle/{vehicle_id}", response_model=Dict[str, Any])
async def get_current_mileage(
    vehicle_id: str
):
    """Get current mileage for a specific vehicle"""
    try:
        mileage = await mileage_service.get_current_vehicle_mileage(vehicle_id)
        return {"success": True, "data": {"vehicle_id": vehicle_id, "current_mileage": mileage}}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/analytics/vehicle/{vehicle_id}", response_model=Dict[str, Any])
async def get_mileage_analytics(
    vehicle_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    """Get mileage analytics for a specific vehicle"""
    try:
        analytics = await mileage_service.get_mileage_analytics(
            vehicle_id, start_date, end_date
        )
        return {"success": True, "data": analytics}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/records/driver/{driver_id}", response_model=Dict[str, Any])
async def get_mileage_records_by_driver(
    driver_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    """Get mileage records by driver"""
    try:
        records = await mileage_service.get_mileage_records_by_driver(
            driver_id, start_date, end_date
        )
        return {"success": True, "data": records}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/records/{mileage_record_id}", response_model=Dict[str, Any])
async def get_mileage_record(
    mileage_record_id: str
):
    """Get a specific mileage record by ID"""
    try:
        record = await mileage_service.mileage_repo.get_by_id(mileage_record_id)
        if not record:
            raise HTTPException(status_code=404, detail="Mileage record not found")
        return {"success": True, "data": record}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/records/{mileage_record_id}", response_model=Dict[str, Any])
async def delete_mileage_record(
    mileage_record_id: str
):
    """Delete a mileage record (admin only)"""
    try:
        # Additional role-based check could be added here
        success = await mileage_service.mileage_repo.delete(mileage_record_id)
        return {"success": success, "message": "Mileage record deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
