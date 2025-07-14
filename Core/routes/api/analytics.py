"""
Analytics Routes
Handles all analytics and reporting operations through service proxy
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials
from typing import Dict, Any
import logging

from .base import security, handle_service_request

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Analytics"])

@router.get("/analytics/fleet-utilization")
async def get_fleet_utilization(
    request: Request,
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
async def get_vehicle_usage(
    request: Request,
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
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get assignment metrics analytics"""
    response = await handle_service_request(
        endpoint="/api/analytics/assignment-metrics",
        method="GET",
        data=dict(request.query_params),
        credentials=credentials,
        auth_endpoint="/api/analytics"
    )
    
    return response

@router.get("/analytics/maintenance")
async def get_maintenance_analytics(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get maintenance analytics"""
    response = await handle_service_request(
        endpoint="/api/analytics/maintenance",
        method="GET",
        data=dict(request.query_params),
        credentials=credentials,
        auth_endpoint="/api/analytics"
    )
    
    return response

@router.get("/analytics/driver-performance")
async def get_driver_performance(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get driver performance analytics"""
    response = await handle_service_request(
        endpoint="/api/analytics/driver-performance",
        method="GET",
        data=dict(request.query_params),
        credentials=credentials,
        auth_endpoint="/api/analytics"
    )
    
    return response

@router.get("/analytics/costs")
async def get_costs_analytics(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get cost analytics"""
    response = await handle_service_request(
        endpoint="/api/analytics/costs",
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
