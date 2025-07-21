"""
Vehicle Management Routes for Management Service
"""
from fastapi import APIRouter, Depends, Query, Path, Request
from typing import Optional
import logging

from repositories.repositories import VehicleRepository
from schemas.requests import VehicleCreateRequest, VehicleUpdateRequest
from services.vehicle_service import VehicleService
from api.dependencies import (
    get_current_user, 
    require_permission, 
    get_pagination_params,
    validate_object_id,
    get_request_id,
    RequestTimer
)
from schemas.responses import ResponseBuilder

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize vehicle service
vehicle_service = VehicleService()


@router.get("/vehicles")
async def get_vehicles(
    request: Request,
    department: Optional[str] = Query(None, description="Filter by department"),
    status: Optional[str] = Query(None, description="Filter by status"),
    vehicle_type: Optional[str] = Query(None, description="Filter by vehicle type"),
    pagination = Depends(get_pagination_params),
    current_user = Depends(require_permission("vehicles:read"))
):
    """Get vehicles with optional filters and enhanced response format"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            logger.info(f"Vehicles list requested by user {current_user.get('user_id')}")
            
            vehicles = await vehicle_service.get_vehicles(
                department=department,
                status=status,
                vehicle_type=vehicle_type,
                pagination=pagination
            )
            
            return ResponseBuilder.success(
                data=vehicles,
                message="Vehicles retrieved successfully",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
            
        except Exception as e:
            logger.error(f"Error getting vehicles: {e}")
            return ResponseBuilder.error(
                error="VehicleRetrievalError",
                message="Failed to retrieve vehicles",
                details={"error": str(e)},
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()


@router.post("/vehicles")
async def create_vehicle(
    request,
    vehicle_request: VehicleCreateRequest,
    current_user = Depends(require_permission("vehicles:create"))
):
    """Create new vehicle with enhanced validation and response"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            logger.info(f"Vehicle creation requested by user {current_user.get('user_id')}")
            
            vehicle = await vehicle_service.create_vehicle(
                vehicle_request, 
                current_user["user_id"]
            )
            
            return ResponseBuilder.success(
                data={"vehicle": vehicle},
                message="Vehicle created successfully",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
            
        except ValueError as e:
            logger.warning(f"Vehicle creation validation error: {e}")
            return ResponseBuilder.error(
                error="ValidationError",
                message=str(e),
                details={"field_errors": str(e)},
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
        except Exception as e:
            logger.error(f"Error creating vehicle: {e}")
            return ResponseBuilder.error(
                error="VehicleCreationError",
                message="Failed to create vehicle",
                details={"error": str(e)},
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()


@router.get("/vehicles/{vehicle_id}")
async def get_vehicle(
    request,
    vehicle_id: str = Path(..., description="Vehicle ID"),
    current_user = Depends(require_permission("vehicles:read"))
):
    """Get specific vehicle by ID"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            logger.info(f"Vehicle {vehicle_id} requested by user {current_user.get('user_id')}")
            
            vehicle = await vehicle_service.get_vehicle_by_id(vehicle_id)
            
            if not vehicle:
                return ResponseBuilder.error(
                    error="VehicleNotFound",
                    message="Vehicle not found",
                    details={"vehicle_id": vehicle_id},
                    request_id=request_id,
                    execution_time_ms=timer.execution_time_ms
                ).model_dump()
            
            return ResponseBuilder.success(
                data={"vehicle": vehicle},
                message="Vehicle retrieved successfully",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
            
        except Exception as e:
            logger.error(f"Error getting vehicle {vehicle_id}: {e}")
            return ResponseBuilder.error(
                error="VehicleRetrievalError",
                message="Failed to retrieve vehicle",
                details={"vehicle_id": vehicle_id, "error": str(e)},
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()


@router.put("/vehicles/{vehicle_id}")
async def update_vehicle(
    request,
    updates: VehicleUpdateRequest,
    vehicle_id: str = Path(..., description="Vehicle ID"),
    current_user = Depends(require_permission("vehicles:update"))
):
    """Update vehicle with enhanced validation and response"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            logger.info(f"Vehicle {vehicle_id} update requested by user {current_user.get('user_id')}")
            
            vehicle = await vehicle_service.update_vehicle(
                vehicle_id, 
                updates, 
                current_user["user_id"]
            )
            
            return ResponseBuilder.success(
                data={"vehicle": vehicle},
                message="Vehicle updated successfully",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
            
        except ValueError as e:
            logger.warning(f"Vehicle update validation error: {e}")
            return ResponseBuilder.error(
                error="ValidationError",
                message=str(e),
                details={"field_errors": str(e)},
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
        except Exception as e:
            logger.error(f"Error updating vehicle {vehicle_id}: {e}")
            return ResponseBuilder.error(
                error="VehicleUpdateError",
                message="Failed to update vehicle",
                details={"vehicle_id": vehicle_id, "error": str(e)},
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()


@router.delete("/vehicles/{vehicle_id}")
async def delete_vehicle(
    request,
    vehicle_id: str = Path(..., description="Vehicle ID"),
    current_user = Depends(require_permission("vehicles:delete"))
):
    """Delete vehicle with proper cleanup and response"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            logger.info(f"Vehicle {vehicle_id} deletion requested by user {current_user.get('user_id')}")
            
            success = await vehicle_service.delete_vehicle(
                vehicle_id, 
                current_user["user_id"]
            )
            
            if not success:
                return ResponseBuilder.error(
                    error="VehicleNotFound",
                    message="Vehicle not found",
                    details={"vehicle_id": vehicle_id},
                    request_id=request_id,
                    execution_time_ms=timer.execution_time_ms
                ).model_dump()
            
            return ResponseBuilder.success(
                data={"vehicle_id": vehicle_id},
                message="Vehicle deleted successfully",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
            
        except Exception as e:
            logger.error(f"Error deleting vehicle {vehicle_id}: {e}")
            return ResponseBuilder.error(
                error="VehicleDeletionError",
                message="Failed to delete vehicle",
                details={"vehicle_id": vehicle_id, "error": str(e)},
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()


@router.get("/vehicles/search")
async def search_vehicles(
    request,
    q: str = Query(..., description="Search query"),
    pagination = Depends(get_pagination_params),
    current_user = Depends(require_permission("vehicles:read"))
):
    """Search vehicles with enhanced search capabilities"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            logger.info(f"Vehicle search requested by user {current_user.get('user_id')} with query: {q}")
            
            results = await vehicle_service.search_vehicles(q, pagination)
            
            return ResponseBuilder.success(
                data=results,
                message="Vehicle search completed successfully",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
            
        except Exception as e:
            logger.error(f"Error searching vehicles: {e}")
            return ResponseBuilder.error(
                error="VehicleSearchError",
                message="Failed to search vehicles",
                details={"query": q, "error": str(e)},
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()


@router.get("/vehicles/{vehicle_id}/assignments")
async def get_vehicle_assignments(
    request,
    vehicle_id: str = Path(..., description="Vehicle ID"),
    status: Optional[str] = Query(None, description="Filter by assignment status"),
    current_user = Depends(require_permission("assignments:read"))
):
    """Get assignments for a specific vehicle"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            logger.info(f"Vehicle {vehicle_id} assignments requested by user {current_user.get('user_id')}")
            
            assignments = await vehicle_service.get_vehicle_assignments(
                vehicle_id, 
                status=status
            )
            
            return ResponseBuilder.success(
                data={"assignments": assignments},
                message="Vehicle assignments retrieved successfully",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
            
        except Exception as e:
            logger.error(f"Error getting vehicle assignments for {vehicle_id}: {e}")
            return ResponseBuilder.error(
                error="VehicleAssignmentRetrievalError",
                message="Failed to retrieve vehicle assignments",
                details={"vehicle_id": vehicle_id, "error": str(e)},
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()


@router.get("/vehicles/{vehicle_id}/usage")
async def get_vehicle_usage(
    request,
    vehicle_id: str = Path(..., description="Vehicle ID"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    current_user = Depends(require_permission("analytics:read"))
):
    """Get usage statistics for a specific vehicle"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            logger.info(f"Vehicle {vehicle_id} usage requested by user {current_user.get('user_id')}")
            
            usage_data = await vehicle_service.get_vehicle_usage_stats(
                vehicle_id,
                start_date=start_date,
                end_date=end_date
            )
            
            return ResponseBuilder.success(
                data=usage_data,
                message="Vehicle usage statistics retrieved successfully",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
            
        except Exception as e:
            logger.error(f"Error getting vehicle usage for {vehicle_id}: {e}")
            return ResponseBuilder.error(
                error="VehicleUsageRetrievalError",
                message="Failed to retrieve vehicle usage statistics",
                details={"vehicle_id": vehicle_id, "error": str(e)},
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
