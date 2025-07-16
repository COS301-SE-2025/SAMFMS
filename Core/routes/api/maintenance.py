"""
Maintenance Routes
Handles vehicle maintenance operations through service proxy
Enhanced with comprehensive maintenance management endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from fastapi.security import HTTPAuthorizationCredentials
from typing import Dict, Any, Optional
import logging

from .base import security, handle_service_request, validate_required_fields

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Maintenance"])

# ============ MAINTENANCE RECORDS ============
@router.get("/maintenance/records")
async def get_maintenance_records(
    request: Request,
    vehicle_id: Optional[str] = Query(None, description="Filter by vehicle ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    maintenance_type: Optional[str] = Query(None, description="Filter by maintenance type"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get maintenance records via Maintenance service"""
    response = await handle_service_request(
        endpoint="/maintenance/records",
        method="GET",
        data=dict(request.query_params),
        credentials=credentials,
        auth_endpoint="/api/maintenance/records"
    )
    
    return response

@router.post("/maintenance/records")
async def create_maintenance_record(
    maintenance_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create maintenance record via Maintenance service"""
    required_fields = ["vehicle_id", "maintenance_type", "description", "scheduled_date"]
    validate_required_fields(maintenance_data, required_fields)
    
    response = await handle_service_request(
        endpoint="/maintenance/records",
        method="POST",
        data=maintenance_data,
        credentials=credentials,
        auth_endpoint="/api/maintenance/records"
    )
    
    return response

@router.get("/maintenance/records/{record_id}")
async def get_maintenance_record(
    record_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get specific maintenance record via Maintenance service"""
    response = await handle_service_request(
        endpoint=f"/maintenance/records/{record_id}",
        method="GET",
        data={"record_id": record_id},
        credentials=credentials,
        auth_endpoint="/api/maintenance/records"
    )
    
    return response

@router.put("/maintenance/records/{record_id}")
async def update_maintenance_record(
    record_id: str,
    maintenance_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update maintenance record via Maintenance service"""
    response = await handle_service_request(
        endpoint=f"/maintenance/records/{record_id}",
        method="PUT",
        data=maintenance_data,
        credentials=credentials,
        auth_endpoint="/api/maintenance/records"
    )
    
    return response

@router.delete("/maintenance/records/{record_id}")
async def delete_maintenance_record(
    record_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete maintenance record via Maintenance service"""
    response = await handle_service_request(
        endpoint=f"/maintenance/records/{record_id}",
        method="DELETE",
        data={"record_id": record_id},
        credentials=credentials,
        auth_endpoint="/api/maintenance/records"
    )
    
    return response

@router.get("/maintenance/records/vehicle/{vehicle_id}")
async def get_vehicle_maintenance_history(
    vehicle_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get maintenance history for specific vehicle via Maintenance service"""
    response = await handle_service_request(
        endpoint=f"/maintenance/records/vehicle/{vehicle_id}",
        method="GET",
        data={"vehicle_id": vehicle_id},
        credentials=credentials,
        auth_endpoint="/api/maintenance/records"
    )
    
    return response

@router.get("/maintenance/records/overdue")
async def get_overdue_maintenance_records(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get overdue maintenance records via Maintenance service"""
    response = await handle_service_request(
        endpoint="/maintenance/records/overdue",
        method="GET",
        data={},
        credentials=credentials,
        auth_endpoint="/api/maintenance/records"
    )
    
    return response

# ============ MAINTENANCE SCHEDULES ============
@router.get("/maintenance/schedules")
async def get_maintenance_schedules(
    request: Request,
    vehicle_id: Optional[str] = Query(None, description="Filter by vehicle ID"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get maintenance schedules via Maintenance service"""
    response = await handle_service_request(
        endpoint="/maintenance/schedules",
        method="GET",
        data=dict(request.query_params),
        credentials=credentials,
        auth_endpoint="/api/maintenance/schedules"
    )
    
    return response

@router.post("/maintenance/schedules")
async def create_maintenance_schedule(
    schedule_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create maintenance schedule via Maintenance service"""
    required_fields = ["vehicle_id", "maintenance_type", "interval_type", "interval_value"]
    validate_required_fields(schedule_data, required_fields)
    
    response = await handle_service_request(
        endpoint="/maintenance/schedules",
        method="POST",
        data=schedule_data,
        credentials=credentials,
        auth_endpoint="/api/maintenance/schedules"
    )
    
    return response

@router.get("/maintenance/schedules/{schedule_id}")
async def get_maintenance_schedule(
    schedule_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get specific maintenance schedule via Maintenance service"""
    response = await handle_service_request(
        endpoint=f"/maintenance/schedules/{schedule_id}",
        method="GET",
        data={"schedule_id": schedule_id},
        credentials=credentials,
        auth_endpoint="/api/maintenance/schedules"
    )
    
    return response

@router.put("/maintenance/schedules/{schedule_id}")
async def update_maintenance_schedule(
    schedule_id: str,
    schedule_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update maintenance schedule via Maintenance service"""
    response = await handle_service_request(
        endpoint=f"/maintenance/schedules/{schedule_id}",
        method="PUT",
        data=schedule_data,
        credentials=credentials,
        auth_endpoint="/api/maintenance/schedules"
    )
    
    return response

@router.delete("/maintenance/schedules/{schedule_id}")
async def delete_maintenance_schedule(
    schedule_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete maintenance schedule via Maintenance service"""
    response = await handle_service_request(
        endpoint=f"/maintenance/schedules/{schedule_id}",
        method="DELETE",
        data={"schedule_id": schedule_id},
        credentials=credentials,
        auth_endpoint="/api/maintenance/schedules"
    )
    
    return response

# ============ LICENSE MANAGEMENT ============
@router.get("/maintenance/licenses")
async def get_license_records(
    request: Request,
    vehicle_id: Optional[str] = Query(None, description="Filter by vehicle ID"),
    license_type: Optional[str] = Query(None, description="Filter by license type"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get license records via Maintenance service"""
    response = await handle_service_request(
        endpoint="/maintenance/licenses",
        method="GET",
        data=dict(request.query_params),
        credentials=credentials,
        auth_endpoint="/api/maintenance/licenses"
    )
    
    return response

@router.post("/maintenance/licenses")
async def create_license_record(
    license_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create license record via Maintenance service"""
    required_fields = ["entity_id", "entity_type", "license_type", "issue_date", "expiry_date"]
    validate_required_fields(license_data, required_fields)
    
    response = await handle_service_request(
        endpoint="/maintenance/licenses",
        method="POST",
        data=license_data,
        credentials=credentials,
        auth_endpoint="/api/maintenance/licenses"
    )
    
    return response

@router.get("/maintenance/licenses/{license_id}")
async def get_license_record(
    license_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get specific license record via Maintenance service"""
    response = await handle_service_request(
        endpoint=f"/maintenance/licenses/{license_id}",
        method="GET",
        data={"license_id": license_id},
        credentials=credentials,
        auth_endpoint="/api/maintenance/licenses"
    )
    
    return response

@router.put("/maintenance/licenses/{license_id}")
async def update_license_record(
    license_id: str,
    license_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update license record via Maintenance service"""
    response = await handle_service_request(
        endpoint=f"/maintenance/licenses/{license_id}",
        method="PUT",
        data=license_data,
        credentials=credentials,
        auth_endpoint="/api/maintenance/licenses"
    )
    
    return response

@router.delete("/maintenance/licenses/{license_id}")
async def delete_license_record(
    license_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete license record via Maintenance service"""
    response = await handle_service_request(
        endpoint=f"/maintenance/licenses/{license_id}",
        method="DELETE",
        data={"license_id": license_id},
        credentials=credentials,
        auth_endpoint="/api/maintenance/licenses"
    )
    
    return response

@router.get("/maintenance/licenses/expiring")
async def get_expiring_licenses(
    days: int = Query(30, description="Days ahead to check for expiring licenses"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get expiring licenses via Maintenance service"""
    response = await handle_service_request(
        endpoint="/maintenance/licenses/expiring",
        method="GET",
        data={"days": days},
        credentials=credentials,
        auth_endpoint="/api/maintenance/licenses"
    )
    
    return response

# ============ VENDOR MANAGEMENT ============
@router.get("/maintenance/vendors")
async def get_maintenance_vendors(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get maintenance vendors via Maintenance service"""
    response = await handle_service_request(
        endpoint="/maintenance/vendors",
        method="GET",
        data={},
        credentials=credentials,
        auth_endpoint="/api/maintenance/vendors"
    )
    
    return response

@router.post("/maintenance/vendors")
async def create_maintenance_vendor(
    vendor_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create maintenance vendor via Maintenance service"""
    required_fields = ["name", "contact_info"]
    validate_required_fields(vendor_data, required_fields)
    
    response = await handle_service_request(
        endpoint="/maintenance/vendors",
        method="POST",
        data=vendor_data,
        credentials=credentials,
        auth_endpoint="/api/maintenance/vendors"
    )
    
    return response

@router.get("/maintenance/vendors/{vendor_id}")
async def get_maintenance_vendor(
    vendor_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get specific maintenance vendor via Maintenance service"""
    response = await handle_service_request(
        endpoint=f"/maintenance/vendors/{vendor_id}",
        method="GET",
        data={"vendor_id": vendor_id},
        credentials=credentials,
        auth_endpoint="/api/maintenance/vendors"
    )
    
    return response

@router.put("/maintenance/vendors/{vendor_id}")
async def update_maintenance_vendor(
    vendor_id: str,
    vendor_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update maintenance vendor via Maintenance service"""
    response = await handle_service_request(
        endpoint=f"/maintenance/vendors/{vendor_id}",
        method="PUT",
        data=vendor_data,
        credentials=credentials,
        auth_endpoint="/api/maintenance/vendors"
    )
    
    return response

@router.delete("/maintenance/vendors/{vendor_id}")
async def delete_maintenance_vendor(
    vendor_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete maintenance vendor via Maintenance service"""
    response = await handle_service_request(
        endpoint=f"/maintenance/vendors/{vendor_id}",
        method="DELETE",
        data={"vendor_id": vendor_id},
        credentials=credentials,
        auth_endpoint="/api/maintenance/vendors"
    )
    
    return response

# ============ ANALYTICS ============
@router.get("/maintenance/analytics")
async def get_maintenance_analytics(
    request: Request,
    vehicle_id: Optional[str] = Query(None, description="Filter by vehicle ID"),
    start_date: Optional[str] = Query(None, description="Start date for analytics"),
    end_date: Optional[str] = Query(None, description="End date for analytics"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get maintenance analytics via Maintenance service"""
    response = await handle_service_request(
        endpoint="/maintenance/analytics",
        method="GET",
        data=dict(request.query_params),
        credentials=credentials,
        auth_endpoint="/api/maintenance/analytics"
    )
    
    return response

@router.get("/maintenance/analytics/costs")
async def get_maintenance_cost_analytics(
    request: Request,
    period: str = Query("monthly", description="Analytics period"),
    vehicle_id: Optional[str] = Query(None, description="Filter by vehicle ID"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get maintenance cost analytics via Maintenance service"""
    response = await handle_service_request(
        endpoint="/maintenance/analytics/costs",
        method="GET",
        data=dict(request.query_params),
        credentials=credentials,
        auth_endpoint="/api/maintenance/analytics"
    )
    
    return response

@router.get("/maintenance/analytics/dashboard")
async def get_maintenance_dashboard(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get maintenance dashboard analytics via Maintenance service"""
    response = await handle_service_request(
        endpoint="/maintenance/analytics/dashboard",
        method="GET",
        data={},
        credentials=credentials,
        auth_endpoint="/api/maintenance/analytics"
    )
    
    return response

# ============ NOTIFICATIONS ============
@router.get("/maintenance/notifications")
async def get_maintenance_notifications(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get maintenance notifications via Maintenance service"""
    response = await handle_service_request(
        endpoint="/maintenance/notifications",
        method="GET",
        data={"page": page, "size": size},
        credentials=credentials,
        auth_endpoint="/api/maintenance/notifications"
    )
    
    return response

@router.put("/maintenance/notifications/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Mark maintenance notification as read via Maintenance service"""
    response = await handle_service_request(
        endpoint=f"/maintenance/notifications/{notification_id}/read",
        method="PUT",
        data={"notification_id": notification_id},
        credentials=credentials,
        auth_endpoint="/api/maintenance/notifications"
    )
    
    return response

@router.delete("/maintenance/notifications/{notification_id}")
async def delete_maintenance_notification(
    notification_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete maintenance notification via Maintenance service"""
    response = await handle_service_request(
        endpoint=f"/maintenance/notifications/{notification_id}",
        method="DELETE",
        data={"notification_id": notification_id},
        credentials=credentials,
        auth_endpoint="/api/maintenance/notifications"
    )
    
    return response
