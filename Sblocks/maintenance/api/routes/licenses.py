"""
License Management API Routes
"""

import logging
from typing import Optional
from datetime import datetime, date
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from schemas.requests import (
    CreateLicenseRecordRequest,
    UpdateLicenseRecordRequest,
    LicenseQueryParams
)
from schemas.responses import (
    DataResponse,
    ListResponse,
    ErrorResponse
)
from services.license_service import license_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/maintenance/licenses", tags=["license_management"])


@router.post("/", response_model=DataResponse)
async def create_license_record(request: CreateLicenseRecordRequest):
    """Create a new license record"""
    try:
        data = request.dict()
        record = await license_service.create_license_record(data)
        
        return DataResponse(
            success=True,
            message="License record created successfully",
            data=record
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating license record: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=ListResponse)
async def get_license_records(
    entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type (vehicle/driver)"),
    license_type: Optional[str] = Query(None, description="Filter by license type"),
    expiring_within_days: Optional[int] = Query(None, description="Filter by licenses expiring within X days"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    sort_by: str = Query("expiry_date", description="Field to sort by"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order")
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
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return ListResponse(
            success=True,
            message="License records retrieved successfully",
            data=records,
            total=len(records),
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error retrieving license records: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{record_id}", response_model=DataResponse)
async def get_license_record(record_id: str):
    """Get a specific license record"""
    try:
        record = await license_service.get_license_record(record_id)
        
        if not record:
            raise HTTPException(status_code=404, detail="License record not found")
            
        return DataResponse(
            success=True,
            message="License record retrieved successfully",
            data=record
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving license record {record_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{record_id}", response_model=DataResponse)
async def update_license_record(record_id: str, request: UpdateLicenseRecordRequest):
    """Update a license record"""
    try:
        # Filter out None values
        data = {k: v for k, v in request.dict().items() if v is not None}
        
        if not data:
            raise HTTPException(status_code=400, detail="No update data provided")
            
        record = await license_service.update_license_record(record_id, data)
        
        if not record:
            raise HTTPException(status_code=404, detail="License record not found")
            
        return DataResponse(
            success=True,
            message="License record updated successfully",
            data=record
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating license record {record_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{record_id}", response_model=DataResponse)
async def delete_license_record(record_id: str):
    """Delete a license record"""
    try:
        success = await license_service.delete_license_record(record_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="License record not found")
            
        return DataResponse(
            success=True,
            message="License record deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting license record {record_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/entity/{entity_id}", response_model=ListResponse)
async def get_entity_licenses(
    entity_id: str,
    entity_type: str = Query(..., regex="^(vehicle|driver)$", description="Entity type")
):
    """Get all licenses for an entity (vehicle or driver)"""
    try:
        records = await license_service.get_entity_licenses(entity_id, entity_type)
        
        return ListResponse(
            success=True,
            message=f"License records for {entity_type} {entity_id} retrieved successfully",
            data=records,
            total=len(records)
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving licenses for {entity_type} {entity_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/status/expiring", response_model=ListResponse)
async def get_expiring_licenses(
    days: int = Query(30, ge=1, le=365, description="Number of days ahead to check")
):
    """Get licenses expiring in the next X days"""
    try:
        records = await license_service.get_expiring_licenses(days)
        
        return ListResponse(
            success=True,
            message=f"Licenses expiring in next {days} days retrieved successfully",
            data=records,
            total=len(records)
        )
        
    except Exception as e:
        logger.error(f"Error retrieving expiring licenses: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/status/expired", response_model=ListResponse)
async def get_expired_licenses():
    """Get expired licenses"""
    try:
        records = await license_service.get_expired_licenses()
        
        return ListResponse(
            success=True,
            message="Expired licenses retrieved successfully",
            data=records,
            total=len(records)
        )
        
    except Exception as e:
        logger.error(f"Error retrieving expired licenses: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/type/{license_type}", response_model=ListResponse)
async def get_licenses_by_type(license_type: str):
    """Get licenses by type"""
    try:
        records = await license_service.get_licenses_by_type(license_type)
        
        return ListResponse(
            success=True,
            message=f"Licenses of type {license_type} retrieved successfully",
            data=records,
            total=len(records)
        )
        
    except Exception as e:
        logger.error(f"Error retrieving licenses by type {license_type}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{record_id}/renew", response_model=DataResponse)
async def renew_license(
    record_id: str,
    new_expiry_date: date = Query(..., description="New expiry date"),
    renewal_cost: Optional[float] = Query(None, description="Renewal cost")
):
    """Renew a license"""
    try:
        record = await license_service.renew_license(
            record_id, 
            new_expiry_date.isoformat(), 
            renewal_cost
        )
        
        if not record:
            raise HTTPException(status_code=404, detail="License record not found")
            
        return DataResponse(
            success=True,
            message="License renewed successfully",
            data=record
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error renewing license {record_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{record_id}/deactivate", response_model=DataResponse)
async def deactivate_license(record_id: str):
    """Deactivate a license"""
    try:
        record = await license_service.deactivate_license(record_id)
        
        if not record:
            raise HTTPException(status_code=404, detail="License record not found")
            
        return DataResponse(
            success=True,
            message="License deactivated successfully",
            data=record
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating license {record_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/summary/statistics", response_model=DataResponse)
async def get_license_summary(
    entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type")
):
    """Get license summary statistics"""
    try:
        summary = await license_service.get_license_summary(entity_id, entity_type)
        
        return DataResponse(
            success=True,
            message="License summary retrieved successfully",
            data=summary
        )
        
    except Exception as e:
        logger.error(f"Error retrieving license summary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
