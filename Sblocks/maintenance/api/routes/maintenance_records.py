"""
Maintenance Records API Routes
"""

import logging
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse

from schemas.requests import (
    CreateMaintenanceRecordRequest,
    UpdateMaintenanceRecordRequest,
    MaintenanceQueryParams
)
from schemas.responses import (
    DataResponse,
    ListResponse,
    ErrorResponse
)
from services.maintenance_service import maintenance_records_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/maintenance/records", tags=["maintenance_records"])


@router.post("/", response_model=DataResponse)
async def create_maintenance_record(request: CreateMaintenanceRecordRequest):
    """Create a new maintenance record"""
    try:
        data = request.dict()
        record = await maintenance_records_service.create_maintenance_record(data)
        
        return DataResponse(
            success=True,
            message="Maintenance record created successfully",
            data=record
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating maintenance record: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=ListResponse)
async def get_maintenance_records(
    vehicle_id: Optional[str] = Query(None, description="Filter by vehicle ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    maintenance_type: Optional[str] = Query(None, description="Filter by maintenance type"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    scheduled_from: Optional[datetime] = Query(None, description="Filter by scheduled date from"),
    scheduled_to: Optional[datetime] = Query(None, description="Filter by scheduled date to"),
    vendor_id: Optional[str] = Query(None, description="Filter by vendor"),
    technician_id: Optional[str] = Query(None, description="Filter by technician"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    sort_by: str = Query("scheduled_date", description="Field to sort by"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order")
):
    """Get maintenance records with filtering and pagination"""
    try:
        # Build query parameters
        query_params = {}
        if vehicle_id:
            query_params["vehicle_id"] = vehicle_id
        if status:
            query_params["status"] = status
        if maintenance_type:
            query_params["maintenance_type"] = maintenance_type
        if priority:
            query_params["priority"] = priority
        if vendor_id:
            query_params["vendor_id"] = vendor_id
        if technician_id:
            query_params["technician_id"] = technician_id
        if scheduled_from:
            query_params["scheduled_from"] = scheduled_from.isoformat()
        if scheduled_to:
            query_params["scheduled_to"] = scheduled_to.isoformat()
            
        records = await maintenance_records_service.search_maintenance_records(
            query=query_params,
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return ListResponse(
            success=True,
            message="Maintenance records retrieved successfully",
            data=records,
            total=len(records),
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error retrieving maintenance records: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{record_id}", response_model=DataResponse)
async def get_maintenance_record(record_id: str):
    """Get a specific maintenance record"""
    try:
        record = await maintenance_records_service.get_maintenance_record(record_id)
        
        if not record:
            raise HTTPException(status_code=404, detail="Maintenance record not found")
            
        return DataResponse(
            success=True,
            message="Maintenance record retrieved successfully",
            data=record
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving maintenance record {record_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{record_id}", response_model=DataResponse)
async def update_maintenance_record(record_id: str, request: UpdateMaintenanceRecordRequest):
    """Update a maintenance record"""
    try:
        # Filter out None values
        data = {k: v for k, v in request.dict().items() if v is not None}
        
        if not data:
            raise HTTPException(status_code=400, detail="No update data provided")
            
        record = await maintenance_records_service.update_maintenance_record(record_id, data)
        
        if not record:
            raise HTTPException(status_code=404, detail="Maintenance record not found")
            
        return DataResponse(
            success=True,
            message="Maintenance record updated successfully",
            data=record
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating maintenance record {record_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{record_id}", response_model=DataResponse)
async def delete_maintenance_record(record_id: str):
    """Delete a maintenance record"""
    try:
        success = await maintenance_records_service.delete_maintenance_record(record_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Maintenance record not found")
            
        return DataResponse(
            success=True,
            message="Maintenance record deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting maintenance record {record_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/vehicle/{vehicle_id}", response_model=ListResponse)
async def get_vehicle_maintenance_records(
    vehicle_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get maintenance records for a specific vehicle"""
    try:
        records = await maintenance_records_service.get_vehicle_maintenance_records(
            vehicle_id, skip, limit
        )
        
        return ListResponse(
            success=True,
            message=f"Maintenance records for vehicle {vehicle_id} retrieved successfully",
            data=records,
            total=len(records),
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error retrieving maintenance records for vehicle {vehicle_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/status/overdue", response_model=ListResponse)
async def get_overdue_maintenance():
    """Get overdue maintenance records"""
    try:
        records = await maintenance_records_service.get_overdue_maintenance()
        
        return ListResponse(
            success=True,
            message="Overdue maintenance records retrieved successfully",
            data=records,
            total=len(records)
        )
        
    except Exception as e:
        logger.error(f"Error retrieving overdue maintenance: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/status/upcoming", response_model=ListResponse)
async def get_upcoming_maintenance(
    days: int = Query(7, ge=1, le=30, description="Number of days ahead to look")
):
    """Get upcoming maintenance records"""
    try:
        records = await maintenance_records_service.get_upcoming_maintenance(days)
        
        return ListResponse(
            success=True,
            message=f"Upcoming maintenance for next {days} days retrieved successfully",
            data=records,
            total=len(records)
        )
        
    except Exception as e:
        logger.error(f"Error retrieving upcoming maintenance: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/vehicle/{vehicle_id}/history", response_model=ListResponse)
async def get_maintenance_history(
    vehicle_id: str,
    start_date: Optional[datetime] = Query(None, description="Start date for history"),
    end_date: Optional[datetime] = Query(None, description="End date for history")
):
    """Get maintenance history for a vehicle"""
    try:
        start_date_str = start_date.isoformat() if start_date else None
        end_date_str = end_date.isoformat() if end_date else None
        
        records = await maintenance_records_service.get_maintenance_history(
            vehicle_id, start_date_str, end_date_str
        )
        
        return ListResponse(
            success=True,
            message=f"Maintenance history for vehicle {vehicle_id} retrieved successfully",
            data=records,
            total=len(records)
        )
        
    except Exception as e:
        logger.error(f"Error retrieving maintenance history for vehicle {vehicle_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/costs/summary", response_model=DataResponse)
async def get_cost_summary(
    vehicle_id: Optional[str] = Query(None, description="Filter by vehicle ID"),
    start_date: Optional[datetime] = Query(None, description="Start date for cost summary"),
    end_date: Optional[datetime] = Query(None, description="End date for cost summary")
):
    """Get maintenance cost summary"""
    try:
        start_date_str = start_date.isoformat() if start_date else None
        end_date_str = end_date.isoformat() if end_date else None
        
        summary = await maintenance_records_service.get_maintenance_cost_summary(
            vehicle_id, start_date_str, end_date_str
        )
        
        return DataResponse(
            success=True,
            message="Cost summary retrieved successfully",
            data=summary
        )
        
    except Exception as e:
        logger.error(f"Error retrieving cost summary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
