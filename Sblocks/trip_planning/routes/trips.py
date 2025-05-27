from fastapi import APIRouter, HTTPException, Depends, Query, Path
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from ..models.models import Trip, TripStatus, TripPriority, Location
from ..services.trip_service import TripService
from ..messaging.rabbitmq_client import RabbitMQClient
from pydantic import BaseModel


# Request/Response models
class TripCreateRequest(BaseModel):
    origin: Location
    destination: Location
    waypoints: Optional[List[Location]] = []
    driver_id: Optional[str] = None
    vehicle_id: Optional[str] = None
    scheduled_departure: datetime
    scheduled_arrival: datetime
    priority: TripPriority = TripPriority.NORMAL
    passenger_count: Optional[int] = None
    cargo_weight: Optional[float] = None
    special_requirements: Optional[List[str]] = []
    notes: Optional[str] = None


class TripUpdateRequest(BaseModel):
    origin: Optional[Location] = None
    destination: Optional[Location] = None
    waypoints: Optional[List[Location]] = None
    driver_id: Optional[str] = None
    vehicle_id: Optional[str] = None
    scheduled_departure: Optional[datetime] = None
    scheduled_arrival: Optional[datetime] = None
    priority: Optional[TripPriority] = None
    passenger_count: Optional[int] = None
    cargo_weight: Optional[float] = None
    special_requirements: Optional[List[str]] = None
    notes: Optional[str] = None


class LocationUpdateRequest(BaseModel):
    latitude: float
    longitude: float
    timestamp: Optional[datetime] = None


class TripResponse(BaseModel):
    id: str
    origin: Location
    destination: Location
    waypoints: List[Location]
    driver_id: Optional[str]
    vehicle_id: Optional[str]
    route_id: Optional[str]
    status: TripStatus
    priority: TripPriority
    scheduled_departure: datetime
    scheduled_arrival: datetime
    actual_departure: Optional[datetime]
    actual_arrival: Optional[datetime]
    distance: Optional[float]
    estimated_duration: Optional[int]
    passenger_count: Optional[int]
    cargo_weight: Optional[float]
    special_requirements: List[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Dependency to get trip service
async def get_trip_service() -> TripService:
    messaging_client = RabbitMQClient()
    await messaging_client.connect()
    return TripService(messaging_client)


router = APIRouter(prefix="/trips", tags=["trips"])


@router.post("/", response_model=TripResponse)
async def create_trip(
    trip_data: TripCreateRequest,
    trip_service: TripService = Depends(get_trip_service)
):
    """Create a new trip"""
    try:
        trip = await trip_service.create_trip(trip_data.dict())
        return TripResponse(
            id=str(trip.id),
            origin=trip.origin,
            destination=trip.destination,
            waypoints=trip.waypoints,
            driver_id=str(trip.driver_id) if trip.driver_id else None,
            vehicle_id=str(trip.vehicle_id) if trip.vehicle_id else None,
            route_id=str(trip.route_id) if trip.route_id else None,
            status=trip.status,
            priority=trip.priority,
            scheduled_departure=trip.scheduled_departure,
            scheduled_arrival=trip.scheduled_arrival,
            actual_departure=trip.actual_departure,
            actual_arrival=trip.actual_arrival,
            distance=trip.distance,
            estimated_duration=trip.estimated_duration,
            passenger_count=trip.passenger_count,
            cargo_weight=trip.cargo_weight,
            special_requirements=trip.special_requirements,
            notes=trip.notes,
            created_at=trip.created_at,
            updated_at=trip.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[TripResponse])
async def get_trips(
    status: Optional[TripStatus] = Query(None, description="Filter by trip status"),
    driver_id: Optional[str] = Query(None, description="Filter by driver ID"),
    vehicle_id: Optional[str] = Query(None, description="Filter by vehicle ID"),
    start_date: Optional[datetime] = Query(None, description="Filter trips from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter trips until this date"),
    skip: int = Query(0, ge=0, description="Number of trips to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of trips to return"),
    trip_service: TripService = Depends(get_trip_service)
):
    """Get trips with optional filters"""
    try:
        trips = await trip_service.get_trips(
            status=status,
            driver_id=driver_id,
            vehicle_id=vehicle_id,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit
        )
        
        return [
            TripResponse(
                id=str(trip.id),
                origin=trip.origin,
                destination=trip.destination,
                waypoints=trip.waypoints,
                driver_id=str(trip.driver_id) if trip.driver_id else None,
                vehicle_id=str(trip.vehicle_id) if trip.vehicle_id else None,
                route_id=str(trip.route_id) if trip.route_id else None,
                status=trip.status,
                priority=trip.priority,
                scheduled_departure=trip.scheduled_departure,
                scheduled_arrival=trip.scheduled_arrival,
                actual_departure=trip.actual_departure,
                actual_arrival=trip.actual_arrival,
                distance=trip.distance,
                estimated_duration=trip.estimated_duration,
                passenger_count=trip.passenger_count,
                cargo_weight=trip.cargo_weight,
                special_requirements=trip.special_requirements,
                notes=trip.notes,
                created_at=trip.created_at,
                updated_at=trip.updated_at
            )
            for trip in trips
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{trip_id}", response_model=TripResponse)
async def get_trip(
    trip_id: str = Path(..., description="Trip ID"),
    trip_service: TripService = Depends(get_trip_service)
):
    """Get a specific trip by ID"""
    try:
        trip = await trip_service.get_trip_by_id(trip_id)
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")
            
        return TripResponse(
            id=str(trip.id),
            origin=trip.origin,
            destination=trip.destination,
            waypoints=trip.waypoints,
            driver_id=str(trip.driver_id) if trip.driver_id else None,
            vehicle_id=str(trip.vehicle_id) if trip.vehicle_id else None,
            route_id=str(trip.route_id) if trip.route_id else None,
            status=trip.status,
            priority=trip.priority,
            scheduled_departure=trip.scheduled_departure,
            scheduled_arrival=trip.scheduled_arrival,
            actual_departure=trip.actual_departure,
            actual_arrival=trip.actual_arrival,
            distance=trip.distance,
            estimated_duration=trip.estimated_duration,
            passenger_count=trip.passenger_count,
            cargo_weight=trip.cargo_weight,
            special_requirements=trip.special_requirements,
            notes=trip.notes,
            created_at=trip.created_at,
            updated_at=trip.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{trip_id}", response_model=TripResponse)
async def update_trip(
    trip_id: str,
    trip_data: TripUpdateRequest,
    trip_service: TripService = Depends(get_trip_service)
):
    """Update a trip"""
    try:
        # Filter out None values
        update_data = {k: v for k, v in trip_data.dict().items() if v is not None}
        
        trip = await trip_service.update_trip(trip_id, update_data)
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")
            
        return TripResponse(
            id=str(trip.id),
            origin=trip.origin,
            destination=trip.destination,
            waypoints=trip.waypoints,
            driver_id=str(trip.driver_id) if trip.driver_id else None,
            vehicle_id=str(trip.vehicle_id) if trip.vehicle_id else None,
            route_id=str(trip.route_id) if trip.route_id else None,
            status=trip.status,
            priority=trip.priority,
            scheduled_departure=trip.scheduled_departure,
            scheduled_arrival=trip.scheduled_arrival,
            actual_departure=trip.actual_departure,
            actual_arrival=trip.actual_arrival,
            distance=trip.distance,
            estimated_duration=trip.estimated_duration,
            passenger_count=trip.passenger_count,
            cargo_weight=trip.cargo_weight,
            special_requirements=trip.special_requirements,
            notes=trip.notes,
            created_at=trip.created_at,
            updated_at=trip.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{trip_id}/status")
async def update_trip_status(
    trip_id: str,
    status: TripStatus,
    trip_service: TripService = Depends(get_trip_service)
):
    """Update trip status"""
    try:
        success = await trip_service.update_trip_status(trip_id, status)
        if not success:
            raise HTTPException(status_code=404, detail="Trip not found")
        return {"message": "Trip status updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{trip_id}/assign-driver")
async def assign_driver_to_trip(
    trip_id: str,
    driver_id: str,
    trip_service: TripService = Depends(get_trip_service)
):
    """Assign a driver to a trip"""
    try:
        success = await trip_service.assign_driver_to_trip(trip_id, driver_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to assign driver to trip")
        return {"message": "Driver assigned successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{trip_id}/assign-vehicle")
async def assign_vehicle_to_trip(
    trip_id: str,
    vehicle_id: str,
    trip_service: TripService = Depends(get_trip_service)
):
    """Assign a vehicle to a trip"""
    try:
        success = await trip_service.assign_vehicle_to_trip(trip_id, vehicle_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to assign vehicle to trip")
        return {"message": "Vehicle assigned successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{trip_id}/start")
async def start_trip(
    trip_id: str,
    trip_service: TripService = Depends(get_trip_service)
):
    """Start a trip"""
    try:
        success = await trip_service.start_trip(trip_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to start trip")
        return {"message": "Trip started successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{trip_id}/complete")
async def complete_trip(
    trip_id: str,
    trip_service: TripService = Depends(get_trip_service)
):
    """Complete a trip"""
    try:
        success = await trip_service.complete_trip(trip_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to complete trip")
        return {"message": "Trip completed successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{trip_id}/cancel")
async def cancel_trip(
    trip_id: str,
    reason: Optional[str] = None,
    trip_service: TripService = Depends(get_trip_service)
):
    """Cancel a trip"""
    try:
        success = await trip_service.cancel_trip(trip_id, reason)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to cancel trip")
        return {"message": "Trip cancelled successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{trip_id}/location")
async def update_trip_location(
    trip_id: str,
    location_data: LocationUpdateRequest,
    trip_service: TripService = Depends(get_trip_service)
):
    """Update trip location"""
    try:
        success = await trip_service.update_trip_location(
            trip_id=trip_id,
            latitude=location_data.latitude,
            longitude=location_data.longitude,
            timestamp=location_data.timestamp
        )
        if not success:
            raise HTTPException(status_code=404, detail="Trip not found")
        return {"message": "Trip location updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{trip_id}/events")
async def get_trip_events(
    trip_id: str,
    trip_service: TripService = Depends(get_trip_service)
):
    """Get trip events/history"""
    try:
        events = await trip_service.get_trip_events(trip_id)
        return {"events": events}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{trip_id}")
async def delete_trip(
    trip_id: str,
    trip_service: TripService = Depends(get_trip_service)
):
    """Delete a trip"""
    try:
        success = await trip_service.delete_trip(trip_id)
        if not success:
            raise HTTPException(status_code=404, detail="Trip not found")
        return {"message": "Trip deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
