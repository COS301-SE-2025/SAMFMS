"""
Service Proxy Routes for SAMFMS Core
Routes frontend requests to appropriate service blocks
"""

from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, List, Optional
import logging

from utils.exceptions import (
    ServiceUnavailableError, 
    AuthorizationError, 
    ValidationError, 
    ServiceTimeoutError
)
from services.request_router import request_router
from services.core_auth_service import core_auth_service
from utils.response_utils import standardize_vehicle_response, APIResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Service Proxy"])
security = HTTPBearer()

# Vehicle Management Routes
@router.get("/vehicles")
async def get_vehicles(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get all vehicles via Management service"""
    try:
        logger.info(f"Received get_vehicles request with params: {dict(request.query_params)}")
        
        # Authorize request
        user_context = await core_auth_service.authorize_request(
            credentials.credentials, "/api/vehicles", "GET"
        )
        logger.info(f"Authorization successful for user: {user_context.get('user_id', 'unknown')}")
        
        # Route to management service
        logger.info("Routing request to management service")
        response = await request_router.route_request(
            endpoint="/api/vehicles",
            method="GET",
            data=dict(request.query_params),
            user_context=user_context
        )
        logger.info(f"Received response from management service: {type(response)}")
        
        # Standardize field names for frontend compatibility
        standardized_response = standardize_vehicle_response(response)
        logger.info("Response standardized successfully")
        
        return standardized_response
        
    except AuthorizationError as e:
        logger.warning(f"Authorization failed for get_vehicles: {e.message}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)
    except ServiceUnavailableError as e:
        logger.error(f"Service unavailable for get_vehicles: {e.message}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message)
    except ServiceTimeoutError as e:
        logger.error(f"Service timeout for get_vehicles: {e.message}")
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=e.message)
    except ValidationError as e:
        logger.warning(f"Validation error in get_vehicles: {e.message}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_vehicles: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.post("/vehicles")
async def create_vehicle(
    vehicle_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create vehicle via Management service"""
    try:
        # Validate input data
        if not vehicle_data:
            raise ValidationError("Vehicle data is required")
        
        required_fields = ["make", "model", "license_plate"]
        missing_fields = [field for field in required_fields if field not in vehicle_data]
        if missing_fields:
            raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
        
        user_context = await core_auth_service.authorize_request(
            credentials.credentials, "/api/vehicles", "POST"
        )
        
        response = await request_router.route_request(
            endpoint="/api/vehicles",
            method="POST",
            data=vehicle_data,
            user_context=user_context
        )
        
        return response
        
    except AuthorizationError as e:
        logger.warning(f"Authorization failed for create_vehicle: {e.message}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)
    except ServiceUnavailableError as e:
        logger.error(f"Service unavailable for create_vehicle: {e.message}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message)
    except ServiceTimeoutError as e:
        logger.error(f"Service timeout for create_vehicle: {e.message}")
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=e.message)
    except ValidationError as e:
        logger.warning(f"Validation error in create_vehicle: {e.message}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in create_vehicle: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/vehicles/{vehicle_id}")
async def get_vehicle(
    vehicle_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get specific vehicle via Management service"""
    try:
        user_context = await core_auth_service.authorize_request(
            credentials.credentials, "/api/vehicles", "GET"
        )
        
        response = await request_router.route_request(
            endpoint=f"/api/vehicles/{vehicle_id}",
            method="GET",
            data={"vehicle_id": vehicle_id},
            user_context=user_context
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_vehicle: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/vehicles/{vehicle_id}")
async def update_vehicle(
    vehicle_id: str,
    vehicle_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update vehicle via Management service"""
    try:
        user_context = await core_auth_service.authorize_request(
            credentials.credentials, "/api/vehicles", "PUT"
        )
        
        response = await request_router.route_request(
            endpoint=f"/api/vehicles/{vehicle_id}",
            method="PUT",
            data=vehicle_data,
            user_context=user_context
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_vehicle: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/vehicles/{vehicle_id}")
async def delete_vehicle(
    vehicle_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete vehicle via Management service"""
    try:
        user_context = await core_auth_service.authorize_request(
            credentials.credentials, "/api/vehicles", "DELETE"
        )
        
        response = await request_router.route_request(
            endpoint=f"/api/vehicles/{vehicle_id}",
            method="DELETE",
            data={"vehicle_id": vehicle_id},
            user_context=user_context
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete_vehicle: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/vehicles/search/{query}")
async def search_vehicles(
    query: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Search vehicles via Management service"""
    try:
        user_context = await core_auth_service.authorize_request(
            credentials.credentials, "/api/vehicles", "GET"
        )
        
        response = await request_router.route_request(
            endpoint=f"/api/vehicles/search/{query}",
            method="GET",
            data={"query": query},
            user_context=user_context
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in search_vehicles: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Vehicle Assignment Routes
@router.get("/vehicle-assignments")
async def get_vehicle_assignments(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get vehicle assignments via Management service"""
    try:
        user_context = await core_auth_service.authorize_request(
            credentials.credentials, "/api/vehicle-assignments", "GET"
        )
        
        response = await request_router.route_request(
            endpoint="/api/vehicle-assignments",
            method="GET",
            data=dict(request.query_params),
            user_context=user_context
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_vehicle_assignments: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/vehicle-assignments")
async def create_vehicle_assignment(
    assignment_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create vehicle assignment via Management service"""
    try:
        user_context = await core_auth_service.authorize_request(
            credentials.credentials, "/api/vehicle-assignments", "POST"
        )
        
        response = await request_router.route_request(
            endpoint="/api/vehicle-assignments",
            method="POST",
            data=assignment_data,
            user_context=user_context
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_vehicle_assignment: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/vehicle-assignments/{assignment_id}")
async def update_vehicle_assignment(
    assignment_id: str,
    assignment_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update vehicle assignment via Management service"""
    try:
        user_context = await core_auth_service.authorize_request(
            credentials.credentials, "/api/vehicle-assignments", "PUT"
        )
        
        response = await request_router.route_request(
            endpoint=f"/api/vehicle-assignments/{assignment_id}",
            method="PUT",
            data=assignment_data,
            user_context=user_context
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_vehicle_assignment: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/vehicle-assignments/{assignment_id}")
async def delete_vehicle_assignment(
    assignment_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete vehicle assignment via Management service"""
    try:
        user_context = await core_auth_service.authorize_request(
            credentials.credentials, "/api/vehicle-assignments", "DELETE"
        )
        
        response = await request_router.route_request(
            endpoint=f"/api/vehicle-assignments/{assignment_id}",
            method="DELETE",
            data={"assignment_id": assignment_id},
            user_context=user_context
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete_vehicle_assignment: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# GPS and Tracking Routes
@router.get("/gps/locations")
async def get_gps_locations(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get GPS locations via GPS service"""
    try:
        user_context = await core_auth_service.authorize_request(
            credentials.credentials, "/api/gps", "GET"
        )
        
        response = await request_router.route_request(
            endpoint="/api/gps/locations",
            method="GET",
            data=dict(request.query_params),
            user_context=user_context
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_gps_locations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/gps/locations")
async def create_gps_location(
    location_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create GPS location via GPS service"""
    try:
        user_context = await core_auth_service.authorize_request(
            credentials.credentials, "/api/gps", "POST"
        )
        
        response = await request_router.route_request(
            endpoint="/api/gps/locations",
            method="POST",
            data=location_data,
            user_context=user_context
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_gps_location: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Trip Planning Routes
@router.get("/trips")
async def get_trips(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get trips via Trip Planning service"""
    try:
        user_context = await core_auth_service.authorize_request(
            credentials.credentials, "/api/trips", "GET"
        )
        
        response = await request_router.route_request(
            endpoint="/api/trips",
            method="GET",
            data=dict(request.query_params),
            user_context=user_context
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_trips: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/trips")
async def create_trip(
    trip_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create trip via Trip Planning service"""
    try:
        user_context = await core_auth_service.authorize_request(
            credentials.credentials, "/api/trips", "POST"
        )
        
        response = await request_router.route_request(
            endpoint="/api/trips",
            method="POST",
            data=trip_data,
            user_context=user_context
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_trip: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Maintenance Routes
@router.get("/maintenance")
async def get_maintenance_records(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get maintenance records via Maintenance service"""
    try:
        user_context = await core_auth_service.authorize_request(
            credentials.credentials, "/api/maintenance", "GET"
        )
        
        response = await request_router.route_request(
            endpoint="/api/maintenance",
            method="GET",
            data=dict(request.query_params),
            user_context=user_context
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_maintenance_records: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/maintenance")
async def create_maintenance_record(
    maintenance_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create maintenance record via Maintenance service"""
    try:
        user_context = await core_auth_service.authorize_request(
            credentials.credentials, "/api/maintenance", "POST"
        )
        
        response = await request_router.route_request(
            endpoint="/api/maintenance",
            method="POST",
            data=maintenance_data,
            user_context=user_context
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_maintenance_record: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Driver Management Routes
@router.get("/vehicles/drivers")
async def get_drivers(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get all drivers via Management service"""
    try:
        # Authorize request
        user_context = await core_auth_service.authorize_request(
            credentials.credentials, "/api/vehicles/drivers", "GET"
        )
        
        # Route to management service
        response = await request_router.route_request(
            endpoint="/api/drivers",
            method="GET",
            data=dict(request.query_params),
            user_context=user_context
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_drivers: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/vehicles/drivers")
async def create_driver(
    driver_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a new driver via Management service"""
    try:
        # Authorize request
        user_context = await core_auth_service.authorize_request(
            credentials.credentials, "/api/vehicles/drivers", "POST"
        )
        
        # Route to management service
        response = await request_router.route_request(
            endpoint="/api/drivers",
            method="POST",
            data=driver_data,
            user_context=user_context
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_driver: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/vehicles/drivers/{driver_id}")
async def get_driver(
    driver_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get specific driver via Management service"""
    try:
        # Authorize request
        user_context = await core_auth_service.authorize_request(
            credentials.credentials, "/api/vehicles/drivers", "GET"
        )
        
        # Route to management service
        response = await request_router.route_request(
            endpoint=f"/api/drivers/{driver_id}",
            method="GET",
            data={"driver_id": driver_id},
            user_context=user_context
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_driver: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/vehicles/drivers/{driver_id}")
async def update_driver(
    driver_id: str,
    driver_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update driver via Management service"""
    try:
        # Authorize request
        user_context = await core_auth_service.authorize_request(
            credentials.credentials, "/api/vehicles/drivers", "PUT"
        )
        
        # Route to management service
        response = await request_router.route_request(
            endpoint=f"/api/drivers/{driver_id}",
            method="PUT",
            data=driver_data,
            user_context=user_context
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_driver: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/vehicles/drivers/{driver_id}")
async def delete_driver(
    driver_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete driver via Management service"""
    try:
        # Authorize request
        user_context = await core_auth_service.authorize_request(
            credentials.credentials, "/api/vehicles/drivers", "DELETE"
        )
        
        # Route to management service
        response = await request_router.route_request(
            endpoint=f"/api/drivers/{driver_id}",
            method="DELETE",
            data={"driver_id": driver_id},
            user_context=user_context
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete_driver: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Analytics Endpoints (Proxy to Management Service)
@router.get("/analytics/{path:path}")
async def proxy_analytics_get(
    path: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Proxy GET analytics requests to Management service"""
    try:
        user_context = await core_auth_service.authorize_request(
            credentials.credentials, f"/analytics/{path}", "GET"
        )
        response = await request_router.route_request(
            endpoint=f"/analytics/{path}",
            method="GET",
            data=dict(request.query_params),
            user_context=user_context
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error proxying analytics GET /analytics/{path}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/analytics/{path:path}")
async def proxy_analytics_post(
    path: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Proxy POST analytics requests to Management service"""
    try:
        user_context = await core_auth_service.authorize_request(
            credentials.credentials, f"/analytics/{path}", "POST"
        )
        body = await request.json()
        response = await request_router.route_request(
            endpoint=f"/analytics/{path}",
            method="POST",
            data=body,
            user_context=user_context
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error proxying analytics POST /analytics/{path}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/debug/routing/{endpoint:path}")
async def debug_routing(endpoint: str):
    """Debug endpoint to test routing configuration"""
    try:
        service = request_router.get_service_for_endpoint(f"/{endpoint}")
        return {
            "endpoint": f"/{endpoint}",
            "service": service,
            "routing_map": request_router.routing_map
        }
    except Exception as e:
        return {
            "endpoint": f"/{endpoint}",
            "error": str(e),
            "routing_map": request_router.routing_map
        }

def standardize_vehicle_response(response_data):
    """Standardize vehicle response field names for frontend compatibility"""
    if isinstance(response_data, dict):
        if "vehicles" in response_data:
            # Handle list of vehicles
            response_data["vehicles"] = [standardize_single_vehicle(v) for v in response_data["vehicles"]]
        else:
            # Handle single vehicle
            response_data = standardize_single_vehicle(response_data)
    
    return response_data

def standardize_single_vehicle(vehicle):
    """Standardize single vehicle field names"""
    if not isinstance(vehicle, dict):
        return vehicle
        
    # Field mapping from backend to frontend expected names
    field_mappings = {
        "license_plate": "licensePlate",
        "fuel_type": "fuelType", 
        "driver_name": "driver",
        "driver_id": "driverId",
        "last_service": "lastService",
        "next_service": "nextService",
        "insurance_expiry": "insuranceExpiry",
        "acquisition_date": "acquisitionDate",
        "fuel_efficiency": "fuelEfficiency",
        "last_driver": "lastDriver",
        "maintenance_costs": "maintenanceCosts"
    }
    
    # Apply field mappings
    standardized = vehicle.copy()
    for backend_field, frontend_field in field_mappings.items():
        if backend_field in standardized:
            standardized[frontend_field] = standardized.pop(backend_field)
    
    # Ensure status is properly capitalized
    if "status" in standardized:
        status = standardized["status"]
        if isinstance(status, str):
            standardized["status"] = status.capitalize()
    
    return standardized

@router.get("/analytics/fleet-utilization")
async def get_fleet_utilization(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get fleet utilization metrics via Management service"""
    try:
        user_context = await core_auth_service.authorize_request(
            credentials.credentials,
            "/api/analytics/fleet-utilization",
            "GET"
        )
        response = await request_router.route_request(
            endpoint="/api/analytics/fleet-utilization",
            method="GET",
            data=dict(request.query_params),
            user_context=user_context
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_fleet_utilization: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/analytics/vehicle-usage")
async def get_vehicle_usage(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get per-vehicle usage stats via Management service"""
    try:
        user_context = await core_auth_service.authorize_request(
            credentials.credentials,
            "/api/analytics/vehicle-usage",
            "GET"
        )
        response = await request_router.route_request(
            endpoint="/api/analytics/vehicle-usage",
            method="GET",
            data=dict(request.query_params),
            user_context=user_context
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_vehicle_usage: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/analytics/assignment-metrics")
async def get_assignment_metrics(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get assignment metrics via Management service"""
    try:
        user_context = await core_auth_service.authorize_request(
            credentials.credentials,
            "/api/analytics/assignment-metrics",
            "GET"
        )
        response = await request_router.route_request(
            endpoint="/api/analytics/assignment-metrics",
            method="GET",
            data=dict(request.query_params),
            user_context=user_context
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_assignment_metrics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/analytics/maintenance")
async def get_maintenance_analytics(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get maintenance analytics via Management service"""
    try:
        user_context = await core_auth_service.authorize_request(
            credentials.credentials,
            "/api/analytics/maintenance",
            "GET"
        )
        response = await request_router.route_request(
            endpoint="/api/analytics/maintenance",
            method="GET",
            data=dict(request.query_params),
            user_context=user_context
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_maintenance_analytics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/analytics/driver-performance")
async def get_driver_performance(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get driver performance metrics via Management service"""
    try:
        user_context = await core_auth_service.authorize_request(
            credentials.credentials,
            "/api/analytics/driver-performance",
            "GET"
        )
        response = await request_router.route_request(
            endpoint="/api/analytics/driver-performance",
            method="GET",
            data=dict(request.query_params),
            user_context=user_context
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_driver_performance: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/analytics/costs")
async def get_cost_analytics(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get cost analytics via Management service"""
    try:
        user_context = await core_auth_service.authorize_request(
            credentials.credentials,
            "/api/analytics/costs",
            "GET"
        )
        response = await request_router.route_request(
            endpoint="/api/analytics/costs",
            method="GET",
            data=dict(request.query_params),
            user_context=user_context
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_cost_analytics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/analytics/status-breakdown")
async def get_status_breakdown(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get vehicle status breakdown via Management service"""
    try:
        user_context = await core_auth_service.authorize_request(
            credentials.credentials,
            "/api/analytics/status-breakdown",
            "GET"
        )
        response = await request_router.route_request(
            endpoint="/api/analytics/status-breakdown",
            method="GET",
            data=dict(request.query_params),
            user_context=user_context
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_status_breakdown: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/analytics/incidents")
async def get_incident_statistics(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get incident statistics via Management service"""
    try:
        user_context = await core_auth_service.authorize_request(
            credentials.credentials,
            "/api/analytics/incidents",
            "GET"
        )
        response = await request_router.route_request(
            endpoint="/api/analytics/incidents",
            method="GET",
            data=dict(request.query_params),
            user_context=user_context
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_incident_statistics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/analytics/department-location")
async def get_department_location_analytics(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get department/location analytics via Management service"""
    try:
        user_context = await core_auth_service.authorize_request(
            credentials.credentials,
            "/api/analytics/department-location",
            "GET"
        )
        response = await request_router.route_request(
            endpoint="/api/analytics/department-location",
            method="GET",
            data=dict(request.query_params),
            user_context=user_context
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_department_location_analytics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")