"""
Maintenance API Routes in Core Service
Proxies requests to Maintenance service and provides direct endpoints
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse

from Core.rabbitmq.producer import rabbitmq_producer
from Core.config.settings import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/maintenance", tags=["maintenance"])
settings = get_settings()


async def send_maintenance_request(action: str, endpoint: str, data: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Send request to maintenance service via RabbitMQ"""
    try:
        request_data = {
            "action": action,
            "endpoint": endpoint,
            "data": data or {},
            "params": params or {},
            "request_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        response = await rabbitmq_producer.send_service_request(
            "maintenance_service_requests",
            request_data,
            timeout=30
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error sending maintenance request: {e}")
        raise HTTPException(status_code=500, detail=f"Service communication error: {str(e)}")


# Maintenance Records Endpoints
@router.post("/records")
async def create_maintenance_record(record_data: Dict[str, Any]):
    """Create a new maintenance record"""
    try:
        response = await send_maintenance_request("POST", "/maintenance/records", data=record_data)
        
        if response.get("success"):
            return JSONResponse(
                status_code=201,
                content=response
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=response.get("message", "Failed to create maintenance record")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating maintenance record: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/records")
async def get_maintenance_records(
    vehicle_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    maintenance_type: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    scheduled_from: Optional[str] = Query(None),
    scheduled_to: Optional[str] = Query(None),
    vendor_id: Optional[str] = Query(None),
    technician_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    sort_by: str = Query("scheduled_date"),
    sort_order: str = Query("desc")
):
    """Get maintenance records with filtering and pagination"""
    try:
        params = {
            "vehicle_id": vehicle_id,
            "status": status,
            "maintenance_type": maintenance_type,
            "priority": priority,
            "scheduled_from": scheduled_from,
            "scheduled_to": scheduled_to,
            "vendor_id": vendor_id,
            "technician_id": technician_id,
            "skip": skip,
            "limit": limit,
            "sort_by": sort_by,
            "sort_order": sort_order
        }
        
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        response = await send_maintenance_request("GET", "/maintenance/records", params=params)
        
        if response.get("success"):
            return response
        else:
            raise HTTPException(
                status_code=400,
                detail=response.get("message", "Failed to retrieve maintenance records")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving maintenance records: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/records/{record_id}")
async def get_maintenance_record(record_id: str):
    """Get a specific maintenance record"""
    try:
        response = await send_maintenance_request("GET", f"/maintenance/records/{record_id}")
        
        if response.get("success"):
            return response
        else:
            status_code = 404 if "not found" in response.get("message", "").lower() else 400
            raise HTTPException(
                status_code=status_code,
                detail=response.get("message", "Failed to retrieve maintenance record")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving maintenance record {record_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/records/{record_id}")
async def update_maintenance_record(record_id: str, update_data: Dict[str, Any]):
    """Update a maintenance record"""
    try:
        response = await send_maintenance_request("PUT", f"/maintenance/records/{record_id}", data=update_data)
        
        if response.get("success"):
            return response
        else:
            status_code = 404 if "not found" in response.get("message", "").lower() else 400
            raise HTTPException(
                status_code=status_code,
                detail=response.get("message", "Failed to update maintenance record")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating maintenance record {record_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/records/{record_id}")
async def delete_maintenance_record(record_id: str):
    """Delete a maintenance record"""
    try:
        response = await send_maintenance_request("DELETE", f"/maintenance/records/{record_id}")
        
        if response.get("success"):
            return response
        else:
            status_code = 404 if "not found" in response.get("message", "").lower() else 400
            raise HTTPException(
                status_code=status_code,
                detail=response.get("message", "Failed to delete maintenance record")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting maintenance record {record_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/records/vehicle/{vehicle_id}")
async def get_vehicle_maintenance_records(
    vehicle_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get maintenance records for a specific vehicle"""
    try:
        params = {
            "skip": skip,
            "limit": limit
        }
        
        response = await send_maintenance_request("GET", f"/maintenance/records/vehicle/{vehicle_id}", params=params)
        
        if response.get("success"):
            return response
        else:
            raise HTTPException(
                status_code=400,
                detail=response.get("message", "Failed to retrieve vehicle maintenance records")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving maintenance records for vehicle {vehicle_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/records/status/overdue")
async def get_overdue_maintenance():
    """Get overdue maintenance records"""
    try:
        response = await send_maintenance_request("GET", "/maintenance/records/overdue")
        
        if response.get("success"):
            return response
        else:
            raise HTTPException(
                status_code=400,
                detail=response.get("message", "Failed to retrieve overdue maintenance")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving overdue maintenance: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/records/status/upcoming")
async def get_upcoming_maintenance(
    days: int = Query(7, ge=1, le=30)
):
    """Get upcoming maintenance records"""
    try:
        params = {"days": days}
        
        response = await send_maintenance_request("GET", "/maintenance/records/upcoming", params=params)
        
        if response.get("success"):
            return response
        else:
            raise HTTPException(
                status_code=400,
                detail=response.get("message", "Failed to retrieve upcoming maintenance")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving upcoming maintenance: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# License Management Endpoints
@router.post("/licenses")
async def create_license_record(license_data: Dict[str, Any]):
    """Create a new license record"""
    try:
        response = await send_maintenance_request("POST", "/maintenance/licenses", data=license_data)
        
        if response.get("success"):
            return JSONResponse(
                status_code=201,
                content=response
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=response.get("message", "Failed to create license record")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating license record: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/licenses")
async def get_license_records(
    entity_id: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    license_type: Optional[str] = Query(None),
    expiring_within_days: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    sort_by: str = Query("expiry_date"),
    sort_order: str = Query("asc")
):
    """Get license records with filtering and pagination"""
    try:
        params = {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "license_type": license_type,
            "expiring_within_days": expiring_within_days,
            "is_active": is_active,
            "skip": skip,
            "limit": limit,
            "sort_by": sort_by,
            "sort_order": sort_order
        }
        
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        response = await send_maintenance_request("GET", "/maintenance/licenses", params=params)
        
        if response.get("success"):
            return response
        else:
            raise HTTPException(
                status_code=400,
                detail=response.get("message", "Failed to retrieve license records")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving license records: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/licenses/{record_id}")
async def get_license_record(record_id: str):
    """Get a specific license record"""
    try:
        response = await send_maintenance_request("GET", f"/maintenance/licenses/{record_id}")
        
        if response.get("success"):
            return response
        else:
            status_code = 404 if "not found" in response.get("message", "").lower() else 400
            raise HTTPException(
                status_code=status_code,
                detail=response.get("message", "Failed to retrieve license record")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving license record {record_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/licenses/expiring")
async def get_expiring_licenses(
    days: int = Query(30, ge=1, le=365)
):
    """Get licenses expiring in the next X days"""
    try:
        params = {"days": days}
        
        response = await send_maintenance_request("GET", "/maintenance/licenses/expiring", params=params)
        
        if response.get("success"):
            return response
        else:
            raise HTTPException(
                status_code=400,
                detail=response.get("message", "Failed to retrieve expiring licenses")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving expiring licenses: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Analytics Endpoints
@router.get("/analytics/dashboard")
async def get_maintenance_dashboard():
    """Get maintenance dashboard overview data"""
    try:
        response = await send_maintenance_request("GET", "/maintenance/analytics/dashboard")
        
        if response.get("success"):
            return response
        else:
            raise HTTPException(
                status_code=400,
                detail=response.get("message", "Failed to retrieve maintenance dashboard")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving maintenance dashboard: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/analytics/costs")
async def get_maintenance_cost_analytics(
    vehicle_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    group_by: str = Query("month")
):
    """Get maintenance cost analytics"""
    try:
        params = {
            "vehicle_id": vehicle_id,
            "start_date": start_date,
            "end_date": end_date,
            "group_by": group_by
        }
        
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        response = await send_maintenance_request("GET", "/maintenance/analytics/costs", params=params)
        
        if response.get("success"):
            return response
        else:
            raise HTTPException(
                status_code=400,
                detail=response.get("message", "Failed to retrieve cost analytics")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving cost analytics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/analytics/trends")
async def get_maintenance_trends(
    days: int = Query(90, ge=30, le=365)
):
    """Get maintenance trends over time"""
    try:
        params = {"days": days}
        
        response = await send_maintenance_request("GET", "/maintenance/analytics/trends", params=params)
        
        if response.get("success"):
            return response
        else:
            raise HTTPException(
                status_code=400,
                detail=response.get("message", "Failed to retrieve maintenance trends")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving maintenance trends: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/analytics/licenses")
async def get_license_analytics():
    """Get license expiry and compliance analytics"""
    try:
        response = await send_maintenance_request("GET", "/maintenance/analytics/licenses")
        
        if response.get("success"):
            return response
        else:
            raise HTTPException(
                status_code=400,
                detail=response.get("message", "Failed to retrieve license analytics")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving license analytics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Notification Endpoints
@router.get("/notifications/pending")
async def get_pending_notifications():
    """Get pending maintenance notifications"""
    try:
        response = await send_maintenance_request("GET", "/maintenance/notifications/pending")
        
        if response.get("success"):
            return response
        else:
            raise HTTPException(
                status_code=400,
                detail=response.get("message", "Failed to retrieve pending notifications")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving pending notifications: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/notifications/process")
async def process_pending_notifications():
    """Process and send pending notifications"""
    try:
        response = await send_maintenance_request("POST", "/maintenance/notifications/process")
        
        if response.get("success"):
            return response
        else:
            raise HTTPException(
                status_code=400,
                detail=response.get("message", "Failed to process notifications")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing notifications: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
