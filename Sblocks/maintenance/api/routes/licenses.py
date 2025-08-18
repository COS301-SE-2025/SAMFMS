"""
License Management API Routes
"""

import logging
from typing import Optional
from datetime import datetime, date
from fastapi import APIRouter, HTTPException, Query, Depends

from api.dependencies import (
    get_authenticated_user,
    require_permissions,
    get_pagination_params,
    validate_object_id,
    get_request_timer
)
from schemas.responses import ResponseBuilder
from schemas.requests import (
    CreateLicenseRecordRequest,
    UpdateLicenseRecordRequest,
    LicenseQueryParams
)
from services.license_service import license_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/licenses", tags=["license_management"])


@router.post("/")
async def create_license_record(
    request: CreateLicenseRecordRequest,
    user: dict = Depends(get_authenticated_user),
    _: None = Depends(require_permissions(["maintenance.licenses.create"])),
    timer: object = Depends(get_request_timer)
):
    """Create a new license record"""
    try:
        data = request.dict()
        data["created_by"] = user["user_id"]
        data["updated_by"] = user["user_id"]
        
        record = await license_service.create_license_record(data)
        
        return ResponseBuilder.success(
            data=record,
            message="License record created successfully",
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )
        
    except ValueError as e:
        return ResponseBuilder.error(
            message=str(e),
            status_code=400,
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )
    except Exception as e:
        logger.error(f"Error creating license record: {e}")
        return ResponseBuilder.error(
            message="Internal server error",
            status_code=500,
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )


@router.get("/")
async def get_license_records(
    entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type (vehicle/driver)"),
    license_type: Optional[str] = Query(None, description="Filter by license type"),
    expiring_within_days: Optional[int] = Query(None, description="Filter by licenses expiring within X days"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    sort_by: str = Query("expiry_date", description="Field to sort by"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order"),
    user: dict = Depends(get_authenticated_user),
    _: None = Depends(require_permissions(["maintenance.licenses.read"])),
    pagination: dict = Depends(get_pagination_params),
    timer: object = Depends(get_request_timer)
):
    """Get license records with filtering and pagination"""
    try:
        # Build query parameters
        query_params = {}
        if entity_id:
            query_params["entity_id"] = entity_id
        if entity_type:
            query_params["entity_type"] = entity_type
        if license_type:
            query_params["license_type"] = license_type
        if expiring_within_days is not None:
            query_params["expiring_within_days"] = expiring_within_days
        if is_active is not None:
            query_params["is_active"] = is_active
            
        records = await license_service.search_licenses(
            query=query_params,
            skip=pagination["skip"],
            limit=pagination["limit"],
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Get total count for pagination
        total_count = await license_service.get_total_count(query_params)
        
        # Get license summary for compliance information
        summary = await license_service.get_license_summary()
        
        # Calculate has_more flag
        has_more = (pagination["skip"] + len(records)) < total_count
        
        # Build response data in expected format
        response_data = {
            "licenses": records,
            "total": total_count,
            "skip": pagination["skip"],
            "limit": pagination["limit"],
            "has_more": has_more,
            "summary": {
                "expired": summary.get("expired", 0),
                "expiring_soon": summary.get("expiring_soon", 0),
                "active": summary.get("active_licenses", 0),
                "total": summary.get("total_licenses", 0),
                "compliance_rate": round(
                    (summary.get("active_licenses", 0) / max(summary.get("total_licenses", 1), 1)) * 100, 1
                ) if summary.get("total_licenses", 0) > 0 else 0.0
            }
        }
        
        return ResponseBuilder.success(
            data=response_data,
            message="Vehicle licenses retrieved successfully",
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )
        
    except Exception as e:
        logger.error(f"Error retrieving license records: {e}")
        return ResponseBuilder.error(
            message="Internal server error",
            status_code=500,
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )


@router.get("/{record_id}")
async def get_license_record(
    record_id: str = Depends(validate_object_id),
    user: dict = Depends(get_authenticated_user),
    _: None = Depends(require_permissions(["maintenance.licenses.read"])),
    timer: object = Depends(get_request_timer)
):
    """Get a specific license record"""
    try:
        record = await license_service.get_license_record(record_id)
        
        if not record:
            return ResponseBuilder.error(
                message="License record not found",
                status_code=404,
                request_id=timer.request_id,
                execution_time=timer.elapsed
            )
            
        return ResponseBuilder.success(
            data=record,
            message="License record retrieved successfully",
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )
        
    except Exception as e:
        logger.error(f"Error retrieving license record {record_id}: {e}")
        return ResponseBuilder.error(
            message="Internal server error",
            status_code=500,
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )


@router.put("/{record_id}")
async def update_license_record(
    request: UpdateLicenseRecordRequest,
    record_id: str = Depends(validate_object_id),
    user: dict = Depends(get_authenticated_user),
    _: None = Depends(require_permissions(["maintenance.licenses.update"])),
    timer: object = Depends(get_request_timer)
):
    """Update a license record"""
    try:
        # Filter out None values
        data = {k: v for k, v in request.dict().items() if v is not None}
        
        if not data:
            return ResponseBuilder.error(
                message="No update data provided",
                status_code=400,
                request_id=timer.request_id,
                execution_time=timer.elapsed
            )
        
        data["updated_by"] = user["user_id"]
        data["updated_at"] = datetime.utcnow().isoformat()
            
        record = await license_service.update_license_record(record_id, data)
        
        if not record:
            return ResponseBuilder.error(
                message="License record not found",
                status_code=404,
                request_id=timer.request_id,
                execution_time=timer.elapsed
            )
            
        return ResponseBuilder.success(
            data=record,
            message="License record updated successfully",
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )
        
    except Exception as e:
        logger.error(f"Error updating license record {record_id}: {e}")
        return ResponseBuilder.error(
            message="Internal server error",
            status_code=500,
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )


@router.delete("/{record_id}")
async def delete_license_record(
    record_id: str = Depends(validate_object_id),
    user: dict = Depends(get_authenticated_user),
    _: None = Depends(require_permissions(["maintenance.licenses.delete"])),
    timer: object = Depends(get_request_timer)
):
    """Delete a license record"""
    try:
        success = await license_service.delete_license_record(record_id)
        
        if not success:
            return ResponseBuilder.error(
                message="License record not found",
                status_code=404,
                request_id=timer.request_id,
                execution_time=timer.elapsed
            )
            
        return ResponseBuilder.success(
            message="License record deleted successfully",
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )
        
    except Exception as e:
        logger.error(f"Error deleting license record {record_id}: {e}")
        return ResponseBuilder.error(
            message="Internal server error",
            status_code=500,
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )


@router.get("/entity/{entity_id}")
async def get_entity_licenses(
    entity_id: str = Depends(validate_object_id),
    entity_type: str = Query(..., regex="^(vehicle|driver)$", description="Entity type"),
    user: dict = Depends(get_authenticated_user),
    _: None = Depends(require_permissions(["maintenance.licenses.read"])),
    timer: object = Depends(get_request_timer)
):
    """Get all licenses for an entity (vehicle or driver)"""
    try:
        records = await license_service.get_entity_licenses(entity_id, entity_type)
        
        return ResponseBuilder.success(
            data=records,
            message=f"License records for {entity_type} {entity_id} retrieved successfully",
            request_id=timer.request_id,
            execution_time=timer.elapsed,
            metadata={
                "total": len(records),
                "entity_id": entity_id,
                "entity_type": entity_type
            }
        )
        
    except ValueError as e:
        return ResponseBuilder.error(
            message=str(e),
            status_code=400,
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )
    except Exception as e:
        logger.error(f"Error retrieving licenses for {entity_type} {entity_id}: {e}")
        return ResponseBuilder.error(
            message="Internal server error",
            status_code=500,
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )


@router.get("/status/expiring")
async def get_expiring_licenses(
    days: int = Query(30, ge=1, le=365, description="Number of days ahead to check"),
    user: dict = Depends(get_authenticated_user),
    _: None = Depends(require_permissions(["maintenance.licenses.read"])),
    timer: object = Depends(get_request_timer)
):
    """Get licenses expiring in the next X days"""
    try:
        records = await license_service.get_expiring_licenses(days)
        
        return ResponseBuilder.success(
            data=records,
            message=f"Licenses expiring in next {days} days retrieved successfully",
            request_id=timer.request_id,
            execution_time=timer.elapsed,
            metadata={
                "total": len(records),
                "days": days
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving expiring licenses: {e}")
        return ResponseBuilder.error(
            message="Internal server error",
            status_code=500,
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )


@router.get("/status/expired")
async def get_expired_licenses(
    user: dict = Depends(get_authenticated_user),
    _: None = Depends(require_permissions(["maintenance.licenses.read"])),
    timer: object = Depends(get_request_timer)
):
    """Get expired licenses"""
    try:
        records = await license_service.get_expired_licenses()
        
        return ResponseBuilder.success(
            data=records,
            message="Expired licenses retrieved successfully",
            request_id=timer.request_id,
            execution_time=timer.elapsed,
            metadata={
                "total": len(records)
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving expired licenses: {e}")
        return ResponseBuilder.error(
            message="Internal server error",
            status_code=500,
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )


@router.get("/type/{license_type}")
async def get_licenses_by_type(
    license_type: str,
    user: dict = Depends(get_authenticated_user),
    _: None = Depends(require_permissions(["maintenance.licenses.read"])),
    timer: object = Depends(get_request_timer)
):
    """Get licenses by type"""
    try:
        records = await license_service.get_licenses_by_type(license_type)
        
        return ResponseBuilder.success(
            data=records,
            message=f"Licenses of type {license_type} retrieved successfully",
            request_id=timer.request_id,
            execution_time=timer.elapsed,
            metadata={
                "total": len(records),
                "license_type": license_type
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving licenses by type {license_type}: {e}")
        return ResponseBuilder.error(
            message="Internal server error",
            status_code=500,
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )


@router.post("/{record_id}/renew")
async def renew_license(
    record_id: str = Depends(validate_object_id),
    new_expiry_date: date = Query(..., description="New expiry date"),
    renewal_cost: Optional[float] = Query(None, description="Renewal cost"),
    user: dict = Depends(get_authenticated_user),
    _: None = Depends(require_permissions(["maintenance.licenses.update"])),
    timer: object = Depends(get_request_timer)
):
    """Renew a license"""
    try:
        record = await license_service.renew_license(
            record_id, 
            new_expiry_date.isoformat(), 
            renewal_cost
        )
        
        if not record:
            return ResponseBuilder.error(
                message="License record not found",
                status_code=404,
                request_id=timer.request_id,
                execution_time=timer.elapsed
            )
            
        return ResponseBuilder.success(
            data=record,
            message="License renewed successfully",
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )
        
    except Exception as e:
        logger.error(f"Error renewing license {record_id}: {e}")
        return ResponseBuilder.error(
            message="Internal server error",
            status_code=500,
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )


@router.post("/{record_id}/deactivate")
async def deactivate_license(
    record_id: str = Depends(validate_object_id),
    user: dict = Depends(get_authenticated_user),
    _: None = Depends(require_permissions(["maintenance.licenses.update"])),
    timer: object = Depends(get_request_timer)
):
    """Deactivate a license"""
    try:
        record = await license_service.deactivate_license(record_id)
        
        if not record:
            return ResponseBuilder.error(
                message="License record not found",
                status_code=404,
                request_id=timer.request_id,
                execution_time=timer.elapsed
            )
            
        return ResponseBuilder.success(
            data=record,
            message="License deactivated successfully",
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )
        
    except Exception as e:
        logger.error(f"Error deactivating license {record_id}: {e}")
        return ResponseBuilder.error(
            message="Internal server error",
            status_code=500,
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )


@router.get("/summary/statistics")
async def get_license_summary(
    entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    user: dict = Depends(get_authenticated_user),
    _: None = Depends(require_permissions(["maintenance.licenses.read"])),
    timer: object = Depends(get_request_timer)
):
    """Get license summary statistics"""
    try:
        summary = await license_service.get_license_summary(entity_id, entity_type)
        
        return ResponseBuilder.success(
            data=summary,
            message="License summary retrieved successfully",
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )
        
    except Exception as e:
        logger.error(f"Error retrieving license summary: {e}")
        return ResponseBuilder.error(
            message="Internal server error",
            status_code=500,
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )
