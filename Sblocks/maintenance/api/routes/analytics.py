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


@router.get("/overview")
async def get_analytics_overview(
    vehicle_id: Optional[str] = Query(None, description="Filter by vehicle ID"),
    start_date: Optional[datetime] = Query(None, description="Start date for analysis"),
    end_date: Optional[datetime] = Query(None, description="End date for analysis"),
    user: dict = Depends(get_authenticated_user),
    _: None = Depends(require_permissions(["maintenance.analytics.read"])),
    timer: object = Depends(get_request_timer)
):
    """Get unified analytics overview combining dashboard and cost data"""
    try:
        # Get dashboard data
        dashboard_data = await maintenance_analytics_service.get_maintenance_dashboard()
        
        # Get cost analytics with default parameters
        start_date_str = start_date.isoformat() if start_date else None
        end_date_str = end_date.isoformat() if end_date else None
        
        cost_analytics = await maintenance_analytics_service.get_cost_analytics(
            vehicle_id=vehicle_id,
            start_date=start_date_str,
            end_date=end_date_str,
            group_by="month"
        )
        
        # Combine and structure the data for frontend consumption
        overview_data = {
            "analytics": {
                "cost_analysis": {
                    "total_cost": cost_analytics.get("summary", {}).get("total_cost", 0),
                    "average_cost": cost_analytics.get("summary", {}).get("average_cost", 0),
                    "maintenance_count": cost_analytics.get("summary", {}).get("total_maintenance_count", 0)
                }
            },
            "cost_analytics": {
                "periods": [],
                "cost_by_type": {},
                "vehicles": [],
                "total_cost": cost_analytics.get("summary", {}).get("total_cost", 0),
                "average_cost": cost_analytics.get("summary", {}).get("average_cost", 0),
                "record_count": cost_analytics.get("summary", {}).get("total_maintenance_count", 0)
            }
        }
        
        return ResponseBuilder.success(
            data=overview_data,
            message="Analytics overview retrieved successfully",
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )
        
    except Exception as e:
        logger.error(f"Error retrieving analytics overview: {e}")
        return ResponseBuilder.error(
            message="Internal server error",
            status_code=500,
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )


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
    group_by: Optional[str] = Query(None, regex="^(day|week|month)$", description="Time grouping"),
    period: Optional[str] = Query(None, description="Period (for frontend compatibility: monthly, quarterly, yearly)"),
    user: dict = Depends(get_authenticated_user),
    _: None = Depends(require_permissions(["maintenance.analytics.read"])),
    timer: object = Depends(get_request_timer)
):
    """Get maintenance cost analytics with time-based grouping"""
    try:
        start_date_str = start_date.isoformat() if start_date else None
        end_date_str = end_date.isoformat() if end_date else None
        
        # Handle frontend period parameter and convert to group_by
        if period and not group_by:
            if period in ["monthly", "quarterly"]:
                group_by = "month"
            elif period == "yearly":
                group_by = "month"  # We'll group by month and let frontend aggregate yearly
            else:
                group_by = "month"  # default
        elif not group_by:
            group_by = "month"  # default
        
        cost_analytics = await maintenance_analytics_service.get_cost_analytics(
            vehicle_id=vehicle_id,
            start_date=start_date_str,
            end_date=end_date_str,
            group_by=group_by
        )
        
        # Get maintenance records by type for cost_by_type
        maintenance_by_type = await maintenance_analytics_service.get_maintenance_records_by_type(
            start_date=start_date_str,
            end_date=end_date_str
        )
        
        # Transform time series data to cost_by_month format
        cost_by_month = {}
        if cost_analytics.get("time_series"):
            for item in cost_analytics["time_series"]:
                if group_by == "month" and item.get("_id"):
                    year = item["_id"].get("year")
                    month = item["_id"].get("month")
                    if year and month:
                        month_key = f"{year}-{month:02d}"
                        cost_by_month[month_key] = item.get("total_cost", 0)
        
        # Transform maintenance_by_type to cost_by_type format
        cost_by_type = {}
        if maintenance_by_type:
            for item in maintenance_by_type:
                maintenance_type = item.get("maintenance_type") or item.get("_id")
                total_cost = item.get("total_cost", 0)
                if maintenance_type:
                    cost_by_type[maintenance_type] = total_cost
        
        # Format response to match frontend expectations
        response_data = {
            "cost_analytics": {
                "total_cost": cost_analytics.get("summary", {}).get("total_cost", 0),
                "labor_cost": cost_analytics.get("summary", {}).get("total_labor_cost", 0),
                "parts_cost": cost_analytics.get("summary", {}).get("total_parts_cost", 0),
                "record_count": cost_analytics.get("summary", {}).get("total_maintenance_count", 0),
                "average_cost": cost_analytics.get("summary", {}).get("average_cost", 0),
                "cost_by_type": cost_by_type,
                "cost_by_month": cost_by_month
            }
        }
        
        return ResponseBuilder.success(
            data=response_data,
            message="Cost analytics retrieved successfully",
            request_id=timer.request_id,
            execution_time=timer.elapsed,
            metadata={
                "filters": {
                    "vehicle_id": vehicle_id,
                    "start_date": start_date_str,
                    "end_date": end_date_str,
                    "group_by": group_by,
                    "period": period
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


@router.get("/timeframe/total-cost")
async def get_total_cost_timeframe(
    start_date: datetime = Query(..., description="Start date for cost calculation"),
    end_date: datetime = Query(..., description="End date for cost calculation"),
    user: dict = Depends(get_authenticated_user),
    _: None = Depends(require_permissions(["maintenance.analytics.read"])),
    timer: object = Depends(get_request_timer)
):
    """Get total maintenance cost within a specific timeframe"""
    try:
        total_cost = await maintenance_analytics_service.get_total_cost_timeframe(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )
        
        return ResponseBuilder.success(
            data={
                "total_cost": total_cost,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "period_days": (end_date - start_date).days
            },
            message=f"Total cost for period {start_date.date()} to {end_date.date()} retrieved successfully",
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )
        
    except Exception as e:
        logger.error(f"Error retrieving total cost for timeframe: {e}")
        return ResponseBuilder.error(
            message="Internal server error",
            status_code=500,
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )


@router.get("/timeframe/records-count")
async def get_records_count_timeframe(
    start_date: datetime = Query(..., description="Start date for record count"),
    end_date: datetime = Query(..., description="End date for record count"),
    user: dict = Depends(get_authenticated_user),
    _: None = Depends(require_permissions(["maintenance.analytics.read"])),
    timer: object = Depends(get_request_timer)
):
    """Get number of maintenance records within a specific timeframe"""
    try:
        records_count = await maintenance_analytics_service.get_records_count_timeframe(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )
        
        return ResponseBuilder.success(
            data={
                "records_count": records_count,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "period_days": (end_date - start_date).days
            },
            message=f"Records count for period {start_date.date()} to {end_date.date()} retrieved successfully",
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )
        
    except Exception as e:
        logger.error(f"Error retrieving records count for timeframe: {e}")
        return ResponseBuilder.error(
            message="Internal server error",
            status_code=500,
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )


@router.get("/timeframe/vehicles-serviced")
async def get_vehicles_serviced_timeframe(
    start_date: datetime = Query(..., description="Start date for vehicle count"),
    end_date: datetime = Query(..., description="End date for vehicle count"),
    user: dict = Depends(get_authenticated_user),
    _: None = Depends(require_permissions(["maintenance.analytics.read"])),
    timer: object = Depends(get_request_timer)
):
    """Get number of unique vehicles serviced within a specific timeframe"""
    try:
        vehicles_count = await maintenance_analytics_service.get_vehicles_serviced_timeframe(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )
        
        return ResponseBuilder.success(
            data={
                "vehicles_serviced": vehicles_count,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "period_days": (end_date - start_date).days
            },
            message=f"Unique vehicles serviced for period {start_date.date()} to {end_date.date()} retrieved successfully",
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )
        
    except Exception as e:
        logger.error(f"Error retrieving vehicles serviced count for timeframe: {e}")
        return ResponseBuilder.error(
            message="Internal server error",
            status_code=500,
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )


@router.get("/maintenance-by-type")
async def get_maintenance_records_by_type(
    start_date: Optional[datetime] = Query(None, description="Start date filter (optional)"),
    end_date: Optional[datetime] = Query(None, description="End date filter (optional)"),
    user: dict = Depends(get_authenticated_user),
    _: None = Depends(require_permissions(["maintenance.analytics.read"])),
    timer: object = Depends(get_request_timer)
):
    """Get maintenance records grouped by maintenance type"""
    try:
        start_date_str = start_date.isoformat() if start_date else None
        end_date_str = end_date.isoformat() if end_date else None
        
        records_by_type = await maintenance_analytics_service.get_maintenance_records_by_type(
            start_date=start_date_str,
            end_date=end_date_str
        )
        
        return ResponseBuilder.success(
            data={
                "records_by_type": records_by_type,
                "start_date": start_date_str,
                "end_date": end_date_str,
                "total_types": len(records_by_type)
            },
            message="Maintenance records by type retrieved successfully",
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )
        
    except Exception as e:
        logger.error(f"Error retrieving maintenance records by type: {e}")
        return ResponseBuilder.error(
            message="Internal server error",
            status_code=500,
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )


@router.get("/cost-outliers")
async def get_maintenance_cost_outliers(
    start_date: Optional[datetime] = Query(None, description="Start date filter (optional)"),
    end_date: Optional[datetime] = Query(None, description="End date filter (optional)"),
    threshold_multiplier: float = Query(2.0, ge=1.0, le=5.0, description="Outlier threshold multiplier (default: 2.0)"),
    user: dict = Depends(get_authenticated_user),
    _: None = Depends(require_permissions(["maintenance.analytics.read"])),
    timer: object = Depends(get_request_timer)
):
    """Get maintenance records with outlier costs (significantly above average)"""
    try:
        start_date_str = start_date.isoformat() if start_date else None
        end_date_str = end_date.isoformat() if end_date else None
        
        cost_outliers = await maintenance_analytics_service.get_maintenance_cost_outliers(
            start_date=start_date_str,
            end_date=end_date_str,
            threshold_multiplier=threshold_multiplier
        )
        
        return ResponseBuilder.success(
            data=cost_outliers,
            message=f"Maintenance cost outliers (threshold: {threshold_multiplier}x average) retrieved successfully",
            request_id=timer.request_id,
            execution_time=timer.elapsed,
            metadata={
                "threshold_multiplier": threshold_multiplier,
                "start_date": start_date_str,
                "end_date": end_date_str
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving maintenance cost outliers: {e}")
        return ResponseBuilder.error(
            message="Internal server error",
            status_code=500,
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )


@router.get("/timeframe/maintenance-per-vehicle")
async def get_maintenance_per_vehicle_timeframe(
    start_date: datetime = Query(..., description="Start date for maintenance count"),
    end_date: datetime = Query(..., description="End date for maintenance count"),
    user: dict = Depends(get_authenticated_user),
    _: None = Depends(require_permissions(["maintenance.analytics.read"])),
    timer: object = Depends(get_request_timer)
):
    """Get number of maintenance records per vehicle within a specific timeframe"""
    try:
        maintenance_per_vehicle = await maintenance_analytics_service.get_maintenance_per_vehicle_timeframe(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )
        
        return ResponseBuilder.success(
            data={
                "maintenance_per_vehicle": maintenance_per_vehicle,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "period_days": (end_date - start_date).days,
                "total_vehicles": len(maintenance_per_vehicle)
            },
            message=f"Maintenance count per vehicle for period {start_date.date()} to {end_date.date()} retrieved successfully",
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )
        
    except Exception as e:
        logger.error(f"Error retrieving maintenance per vehicle for timeframe: {e}")
        return ResponseBuilder.error(
            message="Internal server error",
            status_code=500,
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )
