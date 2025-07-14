"""
Analytics Routes
Handles all analytics and reporting operations through service proxy
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from fastapi.security import HTTPAuthorizationCredentials
from typing import Dict, Any, Optional
import logging

from .base import security, handle_service_request

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Analytics"])

@router.get("/analytics/dashboard")
async def get_dashboard_analytics(
    request: Request,
    use_cache: bool = Query(True, description="Use cached data if available"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get comprehensive dashboard analytics via Management service"""
    logger.info(f"Received dashboard analytics request with params: {dict(request.query_params)}")
    
    response = await handle_service_request(
        endpoint="/api/analytics/dashboard",
        method="GET",
        data=dict(request.query_params),
        credentials=credentials,
        auth_endpoint="/api/analytics"
    )
    
    return response

@router.get("/analytics/fleet-utilization")
async def get_fleet_utilization(
    request: Request,
    use_cache: bool = Query(True, description="Use cached data if available"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get fleet utilization analytics"""
    response = await handle_service_request(
        endpoint="/api/analytics/fleet-utilization",
        method="GET",
        data=dict(request.query_params),
        credentials=credentials,
        auth_endpoint="/api/analytics"
    )
    
    return response

@router.get("/analytics/vehicle-usage")
async def get_vehicle_usage_analytics(
    request: Request,
    use_cache: bool = Query(True, description="Use cached data if available"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get vehicle usage analytics"""
    response = await handle_service_request(
        endpoint="/api/analytics/vehicle-usage",
        method="GET",
        data=dict(request.query_params),
        credentials=credentials,
        auth_endpoint="/api/analytics"
    )
    
    return response

@router.get("/analytics/assignment-metrics")
async def get_assignment_metrics(
    request: Request,
    use_cache: bool = Query(True, description="Use cached data if available"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get assignment metrics via Management service"""
    logger.info(f"Received assignment metrics request with params: {dict(request.query_params)}")
    
    response = await handle_service_request(
        endpoint="/api/analytics/assignment-metrics",
        method="GET",
        data=dict(request.query_params),
        credentials=credentials,
        auth_endpoint="/api/analytics"
    )
    
    return response

@router.get("/analytics/driver-performance")
async def get_driver_performance(
    request: Request,
    use_cache: bool = Query(True, description="Use cached data if available"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get driver performance analytics via Management service"""
    logger.info(f"Received driver performance request with params: {dict(request.query_params)}")
    
    response = await handle_service_request(
        endpoint="/api/analytics/driver-performance",
        method="GET",
        data=dict(request.query_params),
        credentials=credentials,
        auth_endpoint="/api/analytics"
    )
    
    return response

@router.get("/analytics/cost-analytics")
async def get_cost_analytics(
    request: Request,
    use_cache: bool = Query(True, description="Use cached data if available"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get cost analytics via Management service"""
    logger.info(f"Received cost analytics request with params: {dict(request.query_params)}")
    
    response = await handle_service_request(
        endpoint="/api/analytics/cost-analytics",
        method="GET",
        data=dict(request.query_params),
        credentials=credentials,
        auth_endpoint="/api/analytics"
    )
    
    return response

@router.get("/analytics/status-breakdown")
async def get_status_breakdown(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get vehicle status breakdown analytics"""
    response = await handle_service_request(
        endpoint="/api/analytics/status-breakdown",
        method="GET",
        data=dict(request.query_params),
        credentials=credentials,
        auth_endpoint="/api/analytics"
    )
    
    return response

@router.get("/analytics/incidents")
async def get_incidents_analytics(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get incident analytics"""
    response = await handle_service_request(
        endpoint="/api/analytics/incidents",
        method="GET",
        data=dict(request.query_params),
        credentials=credentials,
        auth_endpoint="/api/analytics"
    )
    
    return response

@router.get("/analytics/department-location")
async def get_department_location_analytics(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get department location analytics"""
    response = await handle_service_request(
        endpoint="/api/analytics/department-location",
        method="GET",
        data=dict(request.query_params),
        credentials=credentials,
        auth_endpoint="/api/analytics"
    )
    
    return response

@router.get("/analytics/{path:path}")
async def get_custom_analytics(
    path: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Generic analytics endpoint for custom paths"""
    response = await handle_service_request(
        endpoint=f"/analytics/{path}",
        method="GET",
        data=dict(request.query_params),
        credentials=credentials,
        auth_endpoint="/api/analytics"
    )
    
    return response

@router.post("/analytics/{path:path}")
async def post_custom_analytics(
    path: str,
    analytics_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Submit analytics data for custom paths"""
    response = await handle_service_request(
        endpoint=f"/analytics/{path}",
        method="POST",
        data=analytics_data,
        credentials=credentials,
        auth_endpoint="/api/analytics"
    )
    
    return response
