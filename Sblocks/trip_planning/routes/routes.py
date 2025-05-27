from fastapi import APIRouter, HTTPException, Depends, Query, Path
from typing import List, Optional
from datetime import datetime
from ..models.models import Route, RouteStatus, Location, RouteOptimization
from ..services.route_service import RouteService
from ..messaging.rabbitmq_client import RabbitMQClient
from pydantic import BaseModel


# Request/Response models
class RouteCreateRequest(BaseModel):
    name: str
    origin: Location
    destination: Location
    waypoints: Optional[List[Location]] = []
    vehicle_type: Optional[str] = None
    description: Optional[str] = None


class RouteUpdateRequest(BaseModel):
    name: Optional[str] = None
    origin: Optional[Location] = None
    destination: Optional[Location] = None
    waypoints: Optional[List[Location]] = None
    vehicle_type: Optional[str] = None
    description: Optional[str] = None


class RouteOptimizationRequest(BaseModel):
    origin: Location
    destination: Location
    waypoints: Optional[List[Location]] = []
    vehicle_type: Optional[str] = None


class RouteResponse(BaseModel):
    id: str
    name: str
    origin: Location
    destination: Location
    waypoints: List[Location]
    total_distance: float
    estimated_duration: int
    status: RouteStatus
    vehicle_type: Optional[str]
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RouteOptimizationResponse(BaseModel):
    optimized_waypoints: List[Location]
    total_distance: float
    estimated_duration: int
    optimization_method: str

    class Config:
        from_attributes = True


# Dependency to get route service
async def get_route_service() -> RouteService:
    messaging_client = RabbitMQClient()
    await messaging_client.connect()
    return RouteService(messaging_client)


router = APIRouter(prefix="/routes", tags=["routes"])


@router.post("/", response_model=RouteResponse)
async def create_route(
    route_data: RouteCreateRequest,
    route_service: RouteService = Depends(get_route_service)
):
    """Create a new route"""
    try:
        route = await route_service.create_route(route_data.dict())
        return RouteResponse(
            id=str(route.id),
            name=route.name,
            origin=route.origin,
            destination=route.destination,
            waypoints=route.waypoints,
            total_distance=route.total_distance,
            estimated_duration=route.estimated_duration,
            status=route.status,
            vehicle_type=route.vehicle_type,
            description=route.description,
            created_at=route.created_at,
            updated_at=route.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[RouteResponse])
async def get_routes(
    status: Optional[RouteStatus] = Query(None, description="Filter by route status"),
    skip: int = Query(0, ge=0, description="Number of routes to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of routes to return"),
    route_service: RouteService = Depends(get_route_service)
):
    """Get routes with optional filters"""
    try:
        routes = await route_service.get_routes(
            status=status,
            skip=skip,
            limit=limit
        )
        
        return [
            RouteResponse(
                id=str(route.id),
                name=route.name,
                origin=route.origin,
                destination=route.destination,
                waypoints=route.waypoints,
                total_distance=route.total_distance,
                estimated_duration=route.estimated_duration,
                status=route.status,
                vehicle_type=route.vehicle_type,
                description=route.description,
                created_at=route.created_at,
                updated_at=route.updated_at
            )
            for route in routes
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{route_id}", response_model=RouteResponse)
async def get_route(
    route_id: str = Path(..., description="Route ID"),
    route_service: RouteService = Depends(get_route_service)
):
    """Get a specific route by ID"""
    try:
        route = await route_service.get_route_by_id(route_id)
        if not route:
            raise HTTPException(status_code=404, detail="Route not found")
            
        return RouteResponse(
            id=str(route.id),
            name=route.name,
            origin=route.origin,
            destination=route.destination,
            waypoints=route.waypoints,
            total_distance=route.total_distance,
            estimated_duration=route.estimated_duration,
            status=route.status,
            vehicle_type=route.vehicle_type,
            description=route.description,
            created_at=route.created_at,
            updated_at=route.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{route_id}", response_model=RouteResponse)
async def update_route(
    route_id: str,
    route_data: RouteUpdateRequest,
    route_service: RouteService = Depends(get_route_service)
):
    """Update a route"""
    try:
        # Filter out None values
        update_data = {k: v for k, v in route_data.dict().items() if v is not None}
        
        route = await route_service.update_route(route_id, update_data)
        if not route:
            raise HTTPException(status_code=404, detail="Route not found")
            
        return RouteResponse(
            id=str(route.id),
            name=route.name,
            origin=route.origin,
            destination=route.destination,
            waypoints=route.waypoints,
            total_distance=route.total_distance,
            estimated_duration=route.estimated_duration,
            status=route.status,
            vehicle_type=route.vehicle_type,
            description=route.description,
            created_at=route.created_at,
            updated_at=route.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{route_id}/status")
async def update_route_status(
    route_id: str,
    status: RouteStatus,
    route_service: RouteService = Depends(get_route_service)
):
    """Update route status"""
    try:
        success = await route_service.update_route_status(route_id, status)
        if not success:
            raise HTTPException(status_code=404, detail="Route not found")
        return {"message": "Route status updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/optimize", response_model=RouteOptimizationResponse)
async def optimize_route(
    optimization_request: RouteOptimizationRequest,
    route_service: RouteService = Depends(get_route_service)
):
    """Optimize a route"""
    try:
        optimization = await route_service.optimize_route(
            origin=optimization_request.origin,
            destination=optimization_request.destination,
            waypoints=optimization_request.waypoints,
            vehicle_type=optimization_request.vehicle_type
        )
        
        return RouteOptimizationResponse(
            optimized_waypoints=optimization.optimized_waypoints,
            total_distance=optimization.total_distance,
            estimated_duration=optimization.estimated_duration,
            optimization_method=optimization.optimization_method
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/alternatives", response_model=List[RouteOptimizationResponse])
async def get_route_alternatives(
    optimization_request: RouteOptimizationRequest,
    max_alternatives: int = Query(3, ge=1, le=5, description="Maximum number of alternatives"),
    route_service: RouteService = Depends(get_route_service)
):
    """Get alternative routes"""
    try:
        alternatives = await route_service.calculate_route_alternatives(
            origin=optimization_request.origin,
            destination=optimization_request.destination,
            max_alternatives=max_alternatives
        )
        
        return [
            RouteOptimizationResponse(
                optimized_waypoints=alt.optimized_waypoints,
                total_distance=alt.total_distance,
                estimated_duration=alt.estimated_duration,
                optimization_method=alt.optimization_method
            )
            for alt in alternatives
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/area/search")
async def find_routes_by_area(
    center_lat: float = Query(..., description="Center latitude"),
    center_lng: float = Query(..., description="Center longitude"),
    radius_km: float = Query(..., ge=0.1, le=100, description="Search radius in kilometers"),
    route_service: RouteService = Depends(get_route_service)
):
    """Find routes within a geographical area"""
    try:
        routes = await route_service.find_routes_by_area(
            center_lat=center_lat,
            center_lng=center_lng,
            radius_km=radius_km
        )
        
        return {
            "search_area": {
                "center_latitude": center_lat,
                "center_longitude": center_lng,
                "radius_km": radius_km
            },
            "routes": [
                {
                    "id": str(route.id),
                    "name": route.name,
                    "origin": route.origin,
                    "destination": route.destination,
                    "total_distance": route.total_distance,
                    "status": route.status.value
                }
                for route in routes
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/analytics/usage")
async def get_route_analytics(
    start_date: Optional[datetime] = Query(None, description="Start date for analytics"),
    end_date: Optional[datetime] = Query(None, description="End date for analytics"),
    route_service: RouteService = Depends(get_route_service)
):
    """Get route usage analytics"""
    try:
        analytics = await route_service.get_route_analytics(
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            },
            "analytics": analytics
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{route_id}")
async def delete_route(
    route_id: str,
    route_service: RouteService = Depends(get_route_service)
):
    """Delete a route (soft delete)"""
    try:
        success = await route_service.delete_route(route_id)
        if not success:
            raise HTTPException(status_code=404, detail="Route not found")
        return {"message": "Route deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
