"""
Maintenance Records API Routes
"""

import logging
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, Path, Request

from schemas.requests import (
    CreateMaintenanceRecordRequest,
    UpdateMaintenanceRecordRequest,
    MaintenanceQueryParams
)
from schemas.responses import ResponseBuilder
from services.maintenance_service import maintenance_records_service
from api.dependencies import (
    get_current_user,
    require_permission,
    get_pagination_params,
    validate_object_id,
    get_request_id,
    RequestTimer,
    validate_date_range
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/records", tags=["maintenance_records"])


@router.post("/")
async def create_maintenance_record(
    request: Request,
    maintenance_request: CreateMaintenanceRecordRequest,
    current_user = Depends(require_permission("maintenance:create"))
):
    """Create a new maintenance record"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            logger.info(f"Maintenance record creation requested by user {current_user.get('user_id')}")
            
            data = maintenance_request.dict()
            record = await maintenance_records_service.create_maintenance_record(
                data, 
                current_user["user_id"]
            )
            
            return ResponseBuilder.success(
                data={"record": record},
                message="Maintenance record created successfully",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
            
        except ValueError as e:
            logger.warning(f"Maintenance record creation validation error: {e}")
            return ResponseBuilder.error(
                error="ValidationError",
                message=str(e),
                details={"field_errors": str(e)},
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
        except Exception as e:
            logger.error(f"Error creating maintenance record: {e}")
            return ResponseBuilder.error(
                error="MaintenanceRecordCreationError",
                message="Failed to create maintenance record",
                details={"error": str(e)},
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()


@router.get("/")
async def get_maintenance_records(
    request: Request,
    vehicle_id: Optional[str] = Query(None, description="Filter by vehicle ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    maintenance_type: Optional[str] = Query(None, description="Filter by maintenance type"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    scheduled_from: Optional[str] = Query(None, description="Filter by scheduled date from (ISO format)"),
    scheduled_to: Optional[str] = Query(None, description="Filter by scheduled date to (ISO format)"),
    vendor_id: Optional[str] = Query(None, description="Filter by vendor"),
    technician_id: Optional[str] = Query(None, description="Filter by technician"),
    pagination = Depends(get_pagination_params),
    current_user = Depends(require_permission("maintenance:read"))
):
    """Get maintenance records with filtering and pagination"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            logger.info(f"Maintenance records list requested by user {current_user.get('user_id')}")
            
            # Validate date range if provided
            if scheduled_from or scheduled_to:
                validate_date_range(scheduled_from, scheduled_to)
            
            # Build query parameters
            query_params = {}
            if vehicle_id:
                validate_object_id(vehicle_id, "vehicle ID")
                query_params["vehicle_id"] = vehicle_id
            if status:
                query_params["status"] = status
            if maintenance_type:
                query_params["maintenance_type"] = maintenance_type
            if priority:
                query_params["priority"] = priority
            if vendor_id:
                validate_object_id(vendor_id, "vendor ID")
                query_params["vendor_id"] = vendor_id
            if technician_id:
                validate_object_id(technician_id, "technician ID")
                query_params["technician_id"] = technician_id
            if scheduled_from:
                query_params["scheduled_from"] = scheduled_from
            if scheduled_to:
                query_params["scheduled_to"] = scheduled_to
                
            records = await maintenance_records_service.search_maintenance_records(
                query=query_params,
                pagination=pagination
            )
            
            return ResponseBuilder.success(
                data=records,
                message="Maintenance records retrieved successfully",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
            
        except ValueError as e:
            return ResponseBuilder.error(
                error="ValidationError",
                message=str(e),
                details={"field_errors": str(e)},
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
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
