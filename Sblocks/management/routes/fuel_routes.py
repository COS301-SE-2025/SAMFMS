"""
API routes for fuel management
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime

from services.fuel_service import fuel_service
from schemas.requests import FuelRecordCreateRequest, FuelRecordUpdateRequest

router = APIRouter(prefix="/fuel", tags=["fuel"])


@router.post("/records", response_model=Dict[str, Any])
async def create_fuel_record(
    request: FuelRecordCreateRequest
):
    """Create a new fuel record"""
    try:
        result = await fuel_service.create_fuel_record(request, "system")
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/records/vehicle/{vehicle_id}", response_model=Dict[str, Any])
async def get_fuel_records_by_vehicle(
    vehicle_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    """Get fuel records for a specific vehicle"""
    try:
        records = await fuel_service.get_fuel_records_by_vehicle(
            vehicle_id, start_date, end_date
        )
        return {"success": True, "data": records}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/records/driver/{driver_id}", response_model=Dict[str, Any])
async def get_fuel_records_by_driver(
    driver_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    """Get fuel records for a specific driver"""
    try:
        records = await fuel_service.get_fuel_records_by_driver(
            driver_id, start_date, end_date
        )
        return {"success": True, "data": records}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/records/{fuel_record_id}", response_model=Dict[str, Any])
async def update_fuel_record(
    fuel_record_id: str,
    request: FuelRecordUpdateRequest
):
    """Update a fuel record"""
    try:
        result = await fuel_service.update_fuel_record(
            fuel_record_id, request, "system"
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/records/{fuel_record_id}", response_model=Dict[str, Any])
async def delete_fuel_record(
    fuel_record_id: str
):
    """Delete a fuel record"""
    try:
        success = await fuel_service.delete_fuel_record(
            fuel_record_id, "system"
        )
        return {"success": success, "message": "Fuel record deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/analytics/vehicle/{vehicle_id}", response_model=Dict[str, Any])
async def get_fuel_analytics_by_vehicle(
    vehicle_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    """Get fuel analytics for a specific vehicle"""
    try:
        analytics = await fuel_service.get_fuel_analytics_by_vehicle(
            vehicle_id, start_date, end_date
        )
        return {"success": True, "data": analytics}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/analytics/driver/{driver_id}", response_model=Dict[str, Any])
async def get_fuel_analytics_by_driver(
    driver_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    """Get fuel analytics for a specific driver"""
    try:
        analytics = await fuel_service.get_fuel_analytics_by_driver(
            driver_id, start_date, end_date
        )
        return {"success": True, "data": analytics}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/records/{fuel_record_id}", response_model=Dict[str, Any])
async def get_fuel_record(
    fuel_record_id: str
):
    """Get a specific fuel record by ID"""
    try:
        record = await fuel_service.fuel_repo.get_by_id(fuel_record_id)
        if not record:
            raise HTTPException(status_code=404, detail="Fuel record not found")
        return {"success": True, "data": record}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
