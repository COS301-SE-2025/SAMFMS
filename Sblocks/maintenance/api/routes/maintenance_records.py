"""
Maintenance Records API Routes
"""

import logging
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, Path, Request

from api.dependencies import (
    validate_date_range,
    require_permission,
    RequestTimer,
    get_current_user,
    get_pagination_params,
    validate_object_id,
    get_request_id
)

# Initialize router

from schemas.requests import (
    CreateMaintenanceRecordRequest,
    UpdateMaintenanceRecordRequest,
    MaintenanceQueryParams
)
from schemas.responses import ResponseBuilder
from services.maintenance_service import maintenance_records_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/")
async def create_maintenance_record(
    request: Request,
    maintenance_request: CreateMaintenanceRecordRequest,
    user: dict = Depends(get_current_user),
    _: None = Depends(require_permission("maintenance.records.create"))
):
    """Create a new maintenance record"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            data = maintenance_request.dict()
            data["created_by"] = user["user_id"]
            data["updated_by"] = user["user_id"]
            
            record = await maintenance_records_service.create_maintenance_record(data)
            
            return ResponseBuilder.success(
                data=record,
                message="Maintenance record created successfully",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            )
            
        except ValueError as e:
            return ResponseBuilder.error(
                message=str(e),
                status_code=400,
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            )
        except Exception as e:
            logger.error(f"Error creating maintenance record: {e}")
            return ResponseBuilder.error(
                message="Internal server error",
                status_code=500,
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            )


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
            return ResponseBuilder.error(
                error="MaintenanceRecordRetrievalError",
                message="Failed to retrieve maintenance records",
                details={"error": str(e)},
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()


@router.get("/{record_id}")
async def get_maintenance_record(
    request: Request,
    record_id: str = Path(..., description="Maintenance record ID"),
    current_user = Depends(require_permission("maintenance:read"))
):
    """Get specific maintenance record by ID"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            logger.info(f"Maintenance record {record_id} requested by user {current_user.get('user_id')}")
            
            validate_object_id(record_id, "maintenance record ID")
            
            record = await maintenance_records_service.get_maintenance_record_by_id(record_id)
            if not record:
                return ResponseBuilder.error(
                    error="MaintenanceRecordNotFound",
                    message="Maintenance record not found",
                    details={"record_id": record_id},
                    request_id=request_id,
                    execution_time_ms=timer.execution_time_ms
                ).model_dump()
            
            return ResponseBuilder.success(
                data={"record": record},
                message="Maintenance record retrieved successfully",
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
            logger.error(f"Error retrieving maintenance record {record_id}: {e}")
            return ResponseBuilder.error(
                error="MaintenanceRecordRetrievalError",
                message="Failed to retrieve maintenance record",
                details={"record_id": record_id, "error": str(e)},
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()


@router.put("/{record_id}")
async def update_maintenance_record(
    request: Request,
    updates: UpdateMaintenanceRecordRequest,
    record_id: str = Path(..., description="Maintenance record ID"),
    current_user = Depends(require_permission("maintenance:update"))
):
    """Update maintenance record"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            logger.info(f"Maintenance record {record_id} update requested by user {current_user.get('user_id')}")
            
            validate_object_id(record_id, "maintenance record ID")
            
            update_data = updates.dict(exclude_unset=True)
            if not update_data:
                return ResponseBuilder.error(
                    error="ValidationError",
                    message="No update data provided",
                    details={"record_id": record_id},
                    request_id=request_id,
                    execution_time_ms=timer.execution_time_ms
                ).model_dump()
            
            record = await maintenance_records_service.update_maintenance_record(
                record_id, 
                update_data, 
                current_user["user_id"]
            )
            
            if not record:
                return ResponseBuilder.error(
                    error="MaintenanceRecordNotFound",
                    message="Maintenance record not found",
                    details={"record_id": record_id},
                    request_id=request_id,
                    execution_time_ms=timer.execution_time_ms
                ).model_dump()
            
            return ResponseBuilder.success(
                data={"record": record},
                message="Maintenance record updated successfully",
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
            logger.error(f"Error updating maintenance record {record_id}: {e}")
            return ResponseBuilder.error(
                error="MaintenanceRecordUpdateError",
                message="Failed to update maintenance record",
                details={"record_id": record_id, "error": str(e)},
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()


@router.delete("/{record_id}")
async def delete_maintenance_record(
    request: Request,
    record_id: str = Path(..., description="Maintenance record ID"),
    current_user = Depends(require_permission("maintenance:delete"))
):
    """Delete maintenance record"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            logger.info(f"Maintenance record {record_id} deletion requested by user {current_user.get('user_id')}")
            
            validate_object_id(record_id, "maintenance record ID")
            
            success = await maintenance_records_service.delete_maintenance_record(
                record_id, 
                current_user["user_id"]
            )
            
            if not success:
                return ResponseBuilder.error(
                    error="MaintenanceRecordNotFound",
                    message="Maintenance record not found",
                    details={"record_id": record_id},
                    request_id=request_id,
                    execution_time_ms=timer.execution_time_ms
                ).model_dump()
            
            return ResponseBuilder.success(
                data={"record_id": record_id},
                message="Maintenance record deleted successfully",
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
            logger.error(f"Error deleting maintenance record {record_id}: {e}")
            return ResponseBuilder.error(
                error="MaintenanceRecordDeletionError",
                message="Failed to delete maintenance record",
                details={"record_id": record_id, "error": str(e)},
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()


@router.get("/vehicle/{vehicle_id}")
async def get_vehicle_maintenance_records(
    request: Request,
    vehicle_id: str = Path(..., description="Vehicle ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    pagination = Depends(get_pagination_params),
    current_user = Depends(require_permission("maintenance:read"))
):
    """Get maintenance records for a specific vehicle"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            logger.info(f"Vehicle {vehicle_id} maintenance records requested by user {current_user.get('user_id')}")
            
            validate_object_id(vehicle_id, "vehicle ID")
            
            query_params = {"vehicle_id": vehicle_id}
            if status:
                query_params["status"] = status
            
            records = await maintenance_records_service.search_maintenance_records(
                query=query_params,
                pagination=pagination
            )
            
            return ResponseBuilder.success(
                data=records,
                message="Vehicle maintenance records retrieved successfully",
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
            logger.error(f"Error retrieving vehicle maintenance records for {vehicle_id}: {e}")
            return ResponseBuilder.error(
                error="VehicleMaintenanceRecordsError",
                message="Failed to retrieve vehicle maintenance records",
                details={"vehicle_id": vehicle_id, "error": str(e)},
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()


@router.get("/search")
async def search_maintenance_records(
    request: Request,
    q: str = Query(..., description="Search query"),
    pagination = Depends(get_pagination_params),
    current_user = Depends(require_permission("maintenance:read"))
):
    """Search maintenance records"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            logger.info(f"Maintenance records search requested by user {current_user.get('user_id')} with query: {q}")
            
            results = await maintenance_records_service.search_maintenance_records_text(q, pagination)
            
            return ResponseBuilder.success(
                data=results,
                message="Maintenance records search completed successfully",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
            
        except Exception as e:
            logger.error(f"Error searching maintenance records: {e}")
            return ResponseBuilder.error(
                error="MaintenanceRecordSearchError",
                message="Failed to search maintenance records",
                details={"query": q, "error": str(e)},
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
