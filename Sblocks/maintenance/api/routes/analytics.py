"""
Maintenance Analytics API Routes
"""

import logging
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query

from api.dependencies import (
    get_authenticated_user,
    require_permissions,
    get_request_timer
)
from schemas.responses import ResponseBuilder
from services.analytics_service import maintenance_analytics_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["maintenance_analytics"])


@router.get("/dashboard")
async def get_maintenance_dashboard(
    user: dict = Depends(get_authenticated_user),
    _: None = Depends(require_permissions(["maintenance.analytics.read"])),
    timer: object = Depends(get_request_timer)
):
    """Get maintenance dashboard overview data"""
    try:
        dashboard_data = await maintenance_analytics_service.get_maintenance_dashboard()
        
        return ResponseBuilder.success(
            data=dashboard_data,
            message="Maintenance dashboard data retrieved successfully",
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )
        
    except Exception as e:
        logger.error(f"Error retrieving maintenance dashboard: {e}")
        return ResponseBuilder.error(
            message="Internal server error",
            status_code=500,
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )


@router.get("/costs")
async def get_cost_analytics(
    vehicle_id: Optional[str] = Query(None, description="Filter by vehicle ID"),
    start_date: Optional[datetime] = Query(None, description="Start date for analysis"),
    end_date: Optional[datetime] = Query(None, description="End date for analysis"),
    group_by: str = Query("month", regex="^(day|week|month)$", description="Time grouping"),
    user: dict = Depends(get_authenticated_user),
    _: None = Depends(require_permissions(["maintenance.analytics.read"])),
    timer: object = Depends(get_request_timer)
):
    """Get maintenance cost analytics with time-based grouping"""
    try:
        start_date_str = start_date.isoformat() if start_date else None
        end_date_str = end_date.isoformat() if end_date else None
        
        cost_analytics = await maintenance_analytics_service.get_cost_analytics(
            vehicle_id=vehicle_id,
            start_date=start_date_str,
            end_date=end_date_str,
            group_by=group_by
        )
        
        return ResponseBuilder.success(
            data=cost_analytics,
            message="Cost analytics retrieved successfully",
            request_id=timer.request_id,
            execution_time=timer.elapsed,
            metadata={
                "filters": {
                    "vehicle_id": vehicle_id,
                    "start_date": start_date_str,
                    "end_date": end_date_str,
                    "group_by": group_by
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving cost analytics: {e}")
        return ResponseBuilder.error(
            message="Internal server error",
            status_code=500,
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )


@router.get("/trends")
async def get_maintenance_trends(
    days: int = Query(90, ge=30, le=365, description="Number of days to analyze"),
    user: dict = Depends(get_authenticated_user),
    _: None = Depends(require_permissions(["maintenance.analytics.read"])),
    timer: object = Depends(get_request_timer)
):
    """Get maintenance trends over time"""
    try:
        trends = await maintenance_analytics_service.get_maintenance_trends(days)
        
        return ResponseBuilder.success(
            data=trends,
            message=f"Maintenance trends for last {days} days retrieved successfully",
            request_id=timer.request_id,
            execution_time=timer.elapsed,
            metadata={
                "analysis_period": f"{days} days"
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving maintenance trends: {e}")
        return ResponseBuilder.error(
            message="Internal server error",
            status_code=500,
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )


@router.get("/vendors")
async def get_vendor_analytics(
    user: dict = Depends(get_authenticated_user),
    _: None = Depends(require_permissions(["maintenance.analytics.read"])),
    timer: object = Depends(get_request_timer)
):
    """Get vendor performance analytics"""
    try:
        vendor_analytics = await maintenance_analytics_service.get_vendor_analytics()
        
        return ResponseBuilder.success(
            data=vendor_analytics,
            message="Vendor analytics retrieved successfully",
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )
        
    except Exception as e:
        logger.error(f"Error retrieving vendor analytics: {e}")
        return ResponseBuilder.error(
            message="Internal server error",
            status_code=500,
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )


@router.get("/licenses")
async def get_license_analytics(
    user: dict = Depends(get_authenticated_user),
    _: None = Depends(require_permissions(["maintenance.analytics.read"])),
    timer: object = Depends(get_request_timer)
):
    """Get license expiry and compliance analytics"""
    try:
        license_analytics = await maintenance_analytics_service.get_license_analytics()
        
        return ResponseBuilder.success(
            data=license_analytics,
            message="License analytics retrieved successfully",
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )
        
    except Exception as e:
        logger.error(f"Error retrieving license analytics: {e}")
        return ResponseBuilder.error(
            message="Internal server error",
            status_code=500,
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )


@router.get("/summary/vehicle/{vehicle_id}")
async def get_vehicle_maintenance_summary(
    vehicle_id: str,
    start_date: Optional[datetime] = Query(None, description="Start date for summary"),
    end_date: Optional[datetime] = Query(None, description="End date for summary"),
    user: dict = Depends(get_authenticated_user),
    _: None = Depends(require_permissions(["maintenance.analytics.read"])),
    timer: object = Depends(get_request_timer)
):
    """Get maintenance summary for a specific vehicle"""
    try:
        start_date_str = start_date.isoformat() if start_date else None
        end_date_str = end_date.isoformat() if end_date else None
        
        # Get cost analytics for the vehicle
        cost_data = await maintenance_analytics_service.get_cost_analytics(
            vehicle_id=vehicle_id,
            start_date=start_date_str,
            end_date=end_date_str,
            group_by="month"
        )
        
        # Get license analytics for the vehicle  
        license_data = await maintenance_analytics_service.get_license_analytics()
        
        # Filter license data for this vehicle
        vehicle_licenses = [
            license for license in license_data.get("licenses_by_entity", [])
            if license.get("_id") == "vehicle"
        ]
        
        summary_data = {
            "vehicle_id": vehicle_id,
            "cost_analytics": cost_data,
            "license_info": vehicle_licenses,
            "date_range": {
                "start": start_date_str,
                "end": end_date_str
            }
        }
        
        return ResponseBuilder.success(
            data=summary_data,
            message=f"Maintenance summary for vehicle {vehicle_id} retrieved successfully",
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )
        
    except Exception as e:
        logger.error(f"Error retrieving vehicle maintenance summary for {vehicle_id}: {e}")
        return ResponseBuilder.error(
            message="Internal server error",
            status_code=500,
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )


@router.get("/metrics/kpi")
async def get_maintenance_kpis(
    user: dict = Depends(get_authenticated_user),
    _: None = Depends(require_permissions(["maintenance.analytics.read"])),
    timer: object = Depends(get_request_timer)
):
    """Get key performance indicators for maintenance"""
    try:
        # Get dashboard data which contains most KPIs
        dashboard_data = await maintenance_analytics_service.get_maintenance_dashboard()
        
        # Extract and format KPIs
        overview = dashboard_data.get("overview", {})
        costs = dashboard_data.get("costs", {})
        
        kpis = {
            "operational_kpis": {
                "total_vehicles": overview.get("total_vehicles", 0),
                "overdue_maintenance_count": overview.get("overdue_maintenance", 0),
                "upcoming_maintenance_count": overview.get("upcoming_maintenance", 0),
                "overdue_percentage": (
                    (overview.get("overdue_maintenance", 0) / max(overview.get("total_vehicles", 1), 1)) * 100
                ),
                "maintenance_compliance": (
                    100 - ((overview.get("overdue_maintenance", 0) / max(overview.get("total_vehicles", 1), 1)) * 100)
                )
            },
            "financial_kpis": {
                "total_cost_last_30_days": costs.get("total_cost_last_30_days", 0),
                "average_cost_per_job": costs.get("average_cost", 0),
                "total_jobs_last_30_days": costs.get("total_jobs", 0),
                "cost_per_vehicle": (
                    costs.get("total_cost_last_30_days", 0) / max(overview.get("total_vehicles", 1), 1)
                )
            },
            "compliance_kpis": {
                "expiring_licenses": overview.get("expiring_licenses", 0),
                "expired_licenses": overview.get("expired_licenses", 0),
                "license_compliance_rate": (
                    100 - ((overview.get("expired_licenses", 0) / max(overview.get("total_vehicles", 1), 1)) * 100)
                )
            }
        }
        
        return ResponseBuilder.success(
            data=kpis,
            message="Maintenance KPIs retrieved successfully",
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )
        
    except Exception as e:
        logger.error(f"Error retrieving maintenance KPIs: {e}")
        return ResponseBuilder.error(
            message="Internal server error",
            status_code=500,
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )
