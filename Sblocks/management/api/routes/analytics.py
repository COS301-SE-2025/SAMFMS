"""
Enhanced Analytics Routes with standardized responses and improved error handling
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from typing import Optional
import logging
import time

from services.analytics_service import analytics_service
from api.dependencies import get_current_user, require_permission, get_request_id, RequestTimer
from schemas.responses import ResponseBuilder
from api.exception_handlers import BusinessLogicError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/analytics/dashboard")
async def get_dashboard_analytics(
    request: Request,
    use_cache: bool = Query(True, description="Use cached data if available"),
    current_user = Depends(require_permission("analytics:read"))
):
    """Get comprehensive dashboard analytics with enhanced response format"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            logger.info(f"Dashboard analytics requested by user {current_user.get('user_id')}")
            
            dashboard_data = await analytics_service.get_dashboard_summary(use_cache=use_cache)
            
            return ResponseBuilder.success(
                data=dashboard_data,
                message="Dashboard analytics retrieved successfully",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
            
        except Exception as e:
            logger.error(f"Error getting dashboard analytics: {e}")
            raise BusinessLogicError("Failed to retrieve dashboard analytics")


@router.get("/analytics/fleet-utilization")
async def get_fleet_utilization(
    request: Request,
    use_cache: bool = Query(True, description="Use cached data if available"),
    current_user = Depends(require_permission("analytics:read"))
):
    """Get fleet utilization metrics with enhanced error handling"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            logger.info(f"Fleet utilization requested by user {current_user.get('user_id')}")
            
            utilization_data = await analytics_service.get_fleet_utilization(use_cache=use_cache)
            
            return ResponseBuilder.success(
                data=utilization_data,
                message="Fleet utilization metrics retrieved successfully",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
            
        except Exception as e:
            logger.error(f"Error getting fleet utilization: {e}")
            raise BusinessLogicError("Failed to retrieve fleet utilization metrics")


@router.get("/analytics/vehicle-usage")
async def get_vehicle_usage_analytics(
    request: Request,
    use_cache: bool = Query(True, description="Use cached data if available"),
    current_user = Depends(require_permission("analytics:read"))
):
    """Get vehicle usage analytics with enhanced monitoring"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            logger.info(f"Vehicle usage analytics requested by user {current_user.get('user_id')}")
            
            usage_data = await analytics_service.get_vehicle_usage_analytics(use_cache=use_cache)
            
            return ResponseBuilder.success(
                data=usage_data,
                message="Vehicle usage analytics retrieved successfully",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
            
        except Exception as e:
            logger.error(f"Error getting vehicle usage analytics: {e}")
            raise BusinessLogicError("Failed to retrieve vehicle usage analytics")


@router.get("/analytics/assignment-metrics")
async def get_assignment_metrics(
    request: Request,
    use_cache: bool = Query(True, description="Use cached data if available"),
    current_user = Depends(require_permission("analytics:read"))
):
    """Get assignment metrics with standardized response"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            logger.info(f"Assignment metrics requested by user {current_user.get('user_id')}")
            
            metrics_data = await analytics_service.get_assignment_metrics(use_cache=use_cache)
            
            return ResponseBuilder.success(
                data=metrics_data,
                message="Assignment metrics retrieved successfully",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
            
        except Exception as e:
            logger.error(f"Error getting assignment metrics: {e}")
            raise BusinessLogicError("Failed to retrieve assignment metrics")


@router.get("/analytics/driver-performance")
async def get_driver_performance(
    request: Request,
    use_cache: bool = Query(True, description="Use cached data if available"),
    current_user = Depends(require_permission("analytics:read"))
):
    """Get driver performance analytics with comprehensive error handling"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            logger.info(f"Driver performance analytics requested by user {current_user.get('user_id')}")
            
            performance_data = await analytics_service.get_driver_performance(use_cache=use_cache)
            
            return ResponseBuilder.success(
                data=performance_data,
                message="Driver performance analytics retrieved successfully",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
            
        except Exception as e:
            logger.error(f"Error getting driver performance: {e}")
            raise BusinessLogicError("Failed to retrieve driver performance analytics")


@router.post("/analytics/refresh")
async def refresh_analytics_cache(
    request: Request,
    current_user = Depends(require_permission("analytics:admin"))
):
    """Manually refresh analytics cache with audit logging"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            user_id = current_user.get('user_id')
            logger.info(f"Analytics cache refresh initiated by user {user_id}")
            
            await analytics_service.refresh_all_cache()
            
            logger.info(f"Analytics cache successfully refreshed by user {user_id}")
            
            return ResponseBuilder.success(
                data={"cache_refreshed": True, "refreshed_by": user_id},
                message="Analytics cache refreshed successfully",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
            
        except Exception as e:
            logger.error(f"Error refreshing analytics cache: {e}")
            raise BusinessLogicError("Failed to refresh analytics cache")


@router.delete("/analytics/cache")
async def clear_analytics_cache(
    request: Request,
    current_user = Depends(require_permission("analytics:admin"))
):
    """Clear expired analytics cache entries with enhanced logging"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            user_id = current_user.get('user_id')
            logger.info(f"Analytics cache cleanup initiated by user {user_id}")
            
            await analytics_service.cleanup_expired_cache()
            
            logger.info(f"Analytics cache successfully cleaned by user {user_id}")
            
            return ResponseBuilder.success(
                data={"cache_cleaned": True, "cleaned_by": user_id},
                message="Expired analytics cache cleared successfully",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
            
        except Exception as e:
            logger.error(f"Error clearing analytics cache: {e}")
            raise BusinessLogicError("Failed to clear analytics cache")
