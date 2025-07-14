"""
Optimized Analytics Routes
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
import logging

from services.analytics_service import analytics_service
from api.dependencies import get_current_user, require_permission

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/analytics/dashboard")
async def get_dashboard_analytics(
    use_cache: bool = Query(True, description="Use cached data if available"),
    current_user = Depends(require_permission("analytics:read"))
):
    """Get comprehensive dashboard analytics"""
    try:
        return await analytics_service.get_dashboard_summary(use_cache=use_cache)
    except Exception as e:
        logger.error(f"Error getting dashboard analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard analytics")


@router.get("/analytics/fleet-utilization")
async def get_fleet_utilization(
    use_cache: bool = Query(True, description="Use cached data if available"),
    current_user = Depends(require_permission("analytics:read"))
):
    """Get fleet utilization metrics"""
    try:
        return await analytics_service.get_fleet_utilization(use_cache=use_cache)
    except Exception as e:
        logger.error(f"Error getting fleet utilization: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch fleet utilization")


@router.get("/analytics/vehicle-usage")
async def get_vehicle_usage_analytics(
    use_cache: bool = Query(True, description="Use cached data if available"),
    current_user = Depends(require_permission("analytics:read"))
):
    """Get vehicle usage analytics"""
    try:
        return await analytics_service.get_vehicle_usage_analytics(use_cache=use_cache)
    except Exception as e:
        logger.error(f"Error getting vehicle usage analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch vehicle usage analytics")


@router.get("/analytics/assignment-metrics")
async def get_assignment_metrics(
    use_cache: bool = Query(True, description="Use cached data if available"),
    current_user = Depends(require_permission("analytics:read"))
):
    """Get assignment metrics"""
    try:
        return await analytics_service.get_assignment_metrics(use_cache=use_cache)
    except Exception as e:
        logger.error(f"Error getting assignment metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch assignment metrics")


@router.get("/analytics/driver-performance")
async def get_driver_performance(
    use_cache: bool = Query(True, description="Use cached data if available"),
    current_user = Depends(require_permission("analytics:read"))
):
    """Get driver performance analytics"""
    try:
        return await analytics_service.get_driver_performance(use_cache=use_cache)
    except Exception as e:
        logger.error(f"Error getting driver performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch driver performance")


@router.post("/analytics/refresh")
async def refresh_analytics_cache(
    current_user = Depends(require_permission("analytics:admin"))
):
    """Manually refresh analytics cache"""
    try:
        await analytics_service.refresh_all_cache()
        return {"message": "Analytics cache refreshed successfully"}
    except Exception as e:
        logger.error(f"Error refreshing analytics cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to refresh analytics cache")


@router.delete("/analytics/cache")
async def clear_analytics_cache(
    current_user = Depends(require_permission("analytics:admin"))
):
    """Clear expired analytics cache entries"""
    try:
        await analytics_service.cleanup_expired_cache()
        return {"message": "Expired analytics cache cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing analytics cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear analytics cache")
