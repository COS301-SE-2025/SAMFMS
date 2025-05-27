from fastapi import APIRouter, HTTPException, Depends, Query, Path
from typing import List, Optional
from datetime import datetime
from ..models.models import Vehicle, VehicleStatus, VehicleType, MaintenanceRecord
from ..services.vehicle_service import VehicleService
from ..messaging.rabbitmq_client import RabbitMQClient
from pydantic import BaseModel


# Request/Response models
class VehicleCreateRequest(BaseModel):
    license_plate: str
    make: str
    model: str
    year: int
    vehicle_type: VehicleType
    capacity: int
    fuel_type: str
    vin: Optional[str] = None
    color: Optional[str] = None
    mileage: Optional[float] = 0.0
    fuel_efficiency: Optional[float] = None
    insurance_policy: Optional[str] = None
    registration_expiry: Optional[datetime] = None
    last_maintenance_date: Optional[datetime] = None
    next_maintenance_date: Optional[datetime] = None


class VehicleUpdateRequest(BaseModel):
    license_plate: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    vehicle_type: Optional[VehicleType] = None
    capacity: Optional[int] = None
    fuel_type: Optional[str] = None
    vin: Optional[str] = None
    color: Optional[str] = None
    mileage: Optional[float] = None
    fuel_efficiency: Optional[float] = None
    insurance_policy: Optional[str] = None
    registration_expiry: Optional[datetime] = None
    last_maintenance_date: Optional[datetime] = None
    next_maintenance_date: Optional[datetime] = None


class MaintenanceRequest(BaseModel):
    maintenance_type: str
    description: str
    cost: float
    service_provider: str
    mileage_at_service: float
    date: Optional[datetime] = None
    parts_replaced: Optional[List[str]] = []
    next_service_due: Optional[datetime] = None


class LocationUpdateRequest(BaseModel):
    latitude: float
    longitude: float
    timestamp: Optional[datetime] = None


class VehicleResponse(BaseModel):
    id: str
    license_plate: str
    make: str
    model: str
    year: int
    vehicle_type: VehicleType
    capacity: int
    fuel_type: str
    status: VehicleStatus
    vin: Optional[str]
    color: Optional[str]
    mileage: float
    fuel_efficiency: Optional[float]
    insurance_policy: Optional[str]
    registration_expiry: Optional[datetime]
    last_maintenance_date: Optional[datetime]
    next_maintenance_date: Optional[datetime]
    current_trip_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Dependency to get vehicle service
async def get_vehicle_service() -> VehicleService:
    messaging_client = RabbitMQClient()
    await messaging_client.connect()
    return VehicleService(messaging_client)


router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.post("/", response_model=VehicleResponse)
async def create_vehicle(
    vehicle_data: VehicleCreateRequest,
    vehicle_service: VehicleService = Depends(get_vehicle_service)
):
    """Create a new vehicle"""
    try:
        vehicle = await vehicle_service.create_vehicle(vehicle_data.dict())
        return VehicleResponse(
            id=str(vehicle.id),
            license_plate=vehicle.license_plate,
            make=vehicle.make,
            model=vehicle.model,
            year=vehicle.year,
            vehicle_type=vehicle.vehicle_type,
            capacity=vehicle.capacity,
            fuel_type=vehicle.fuel_type,
            status=vehicle.status,
            vin=vehicle.vin,
            color=vehicle.color,
            mileage=vehicle.mileage,
            fuel_efficiency=vehicle.fuel_efficiency,
            insurance_policy=vehicle.insurance_policy,
            registration_expiry=vehicle.registration_expiry,
            last_maintenance_date=vehicle.last_maintenance_date,
            next_maintenance_date=vehicle.next_maintenance_date,
            current_trip_id=str(vehicle.current_trip_id) if vehicle.current_trip_id else None,
            created_at=vehicle.created_at,
            updated_at=vehicle.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[VehicleResponse])
async def get_vehicles(
    status: Optional[VehicleStatus] = Query(None, description="Filter by vehicle status"),
    vehicle_type: Optional[VehicleType] = Query(None, description="Filter by vehicle type"),
    available_only: bool = Query(False, description="Show only available vehicles"),
    skip: int = Query(0, ge=0, description="Number of vehicles to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of vehicles to return"),
    vehicle_service: VehicleService = Depends(get_vehicle_service)
):
    """Get vehicles with optional filters"""
    try:
        vehicles = await vehicle_service.get_vehicles(
            status=status,
            vehicle_type=vehicle_type,
            available_only=available_only,
            skip=skip,
            limit=limit
        )
        
        return [
            VehicleResponse(
                id=str(vehicle.id),
                license_plate=vehicle.license_plate,
                make=vehicle.make,
                model=vehicle.model,
                year=vehicle.year,
                vehicle_type=vehicle.vehicle_type,
                capacity=vehicle.capacity,
                fuel_type=vehicle.fuel_type,
                status=vehicle.status,
                vin=vehicle.vin,
                color=vehicle.color,
                mileage=vehicle.mileage,
                fuel_efficiency=vehicle.fuel_efficiency,
                insurance_policy=vehicle.insurance_policy,
                registration_expiry=vehicle.registration_expiry,
                last_maintenance_date=vehicle.last_maintenance_date,
                next_maintenance_date=vehicle.next_maintenance_date,
                current_trip_id=str(vehicle.current_trip_id) if vehicle.current_trip_id else None,
                created_at=vehicle.created_at,
                updated_at=vehicle.updated_at
            )
            for vehicle in vehicles
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/available", response_model=List[VehicleResponse])
async def get_available_vehicles(
    vehicle_type: Optional[VehicleType] = Query(None, description="Filter by vehicle type"),
    exclude_maintenance: bool = Query(True, description="Exclude vehicles due for maintenance"),
    vehicle_service: VehicleService = Depends(get_vehicle_service)
):
    """Get all available vehicles for trip assignment"""
    try:
        vehicles = await vehicle_service.get_available_vehicles(
            vehicle_type=vehicle_type,
            exclude_maintenance=exclude_maintenance
        )
        
        return [
            VehicleResponse(
                id=str(vehicle.id),
                license_plate=vehicle.license_plate,
                make=vehicle.make,
                model=vehicle.model,
                year=vehicle.year,
                vehicle_type=vehicle.vehicle_type,
                capacity=vehicle.capacity,
                fuel_type=vehicle.fuel_type,
                status=vehicle.status,
                vin=vehicle.vin,
                color=vehicle.color,
                mileage=vehicle.mileage,
                fuel_efficiency=vehicle.fuel_efficiency,
                insurance_policy=vehicle.insurance_policy,
                registration_expiry=vehicle.registration_expiry,
                last_maintenance_date=vehicle.last_maintenance_date,
                next_maintenance_date=vehicle.next_maintenance_date,
                current_trip_id=str(vehicle.current_trip_id) if vehicle.current_trip_id else None,
                created_at=vehicle.created_at,
                updated_at=vehicle.updated_at
            )
            for vehicle in vehicles
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(
    vehicle_id: str = Path(..., description="Vehicle ID"),
    vehicle_service: VehicleService = Depends(get_vehicle_service)
):
    """Get a specific vehicle by ID"""
    try:
        vehicle = await vehicle_service.get_vehicle_by_id(vehicle_id)
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")
            
        return VehicleResponse(
            id=str(vehicle.id),
            license_plate=vehicle.license_plate,
            make=vehicle.make,
            model=vehicle.model,
            year=vehicle.year,
            vehicle_type=vehicle.vehicle_type,
            capacity=vehicle.capacity,
            fuel_type=vehicle.fuel_type,
            status=vehicle.status,
            vin=vehicle.vin,
            color=vehicle.color,
            mileage=vehicle.mileage,
            fuel_efficiency=vehicle.fuel_efficiency,
            insurance_policy=vehicle.insurance_policy,
            registration_expiry=vehicle.registration_expiry,
            last_maintenance_date=vehicle.last_maintenance_date,
            next_maintenance_date=vehicle.next_maintenance_date,
            current_trip_id=str(vehicle.current_trip_id) if vehicle.current_trip_id else None,
            created_at=vehicle.created_at,
            updated_at=vehicle.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(
    vehicle_id: str,
    vehicle_data: VehicleUpdateRequest,
    vehicle_service: VehicleService = Depends(get_vehicle_service)
):
    """Update a vehicle"""
    try:
        # Filter out None values
        update_data = {k: v for k, v in vehicle_data.dict().items() if v is not None}
        
        vehicle = await vehicle_service.update_vehicle(vehicle_id, update_data)
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")
            
        return VehicleResponse(
            id=str(vehicle.id),
            license_plate=vehicle.license_plate,
            make=vehicle.make,
            model=vehicle.model,
            year=vehicle.year,
            vehicle_type=vehicle.vehicle_type,
            capacity=vehicle.capacity,
            fuel_type=vehicle.fuel_type,
            status=vehicle.status,
            vin=vehicle.vin,
            color=vehicle.color,
            mileage=vehicle.mileage,
            fuel_efficiency=vehicle.fuel_efficiency,
            insurance_policy=vehicle.insurance_policy,
            registration_expiry=vehicle.registration_expiry,
            last_maintenance_date=vehicle.last_maintenance_date,
            next_maintenance_date=vehicle.next_maintenance_date,
            current_trip_id=str(vehicle.current_trip_id) if vehicle.current_trip_id else None,
            created_at=vehicle.created_at,
            updated_at=vehicle.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{vehicle_id}/status")
async def update_vehicle_status(
    vehicle_id: str,
    status: VehicleStatus,
    vehicle_service: VehicleService = Depends(get_vehicle_service)
):
    """Update vehicle status"""
    try:
        success = await vehicle_service.update_vehicle_status(vehicle_id, status)
        if not success:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        return {"message": "Vehicle status updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{vehicle_id}/location")
async def update_vehicle_location(
    vehicle_id: str,
    location_data: LocationUpdateRequest,
    vehicle_service: VehicleService = Depends(get_vehicle_service)
):
    """Update vehicle location"""
    try:
        success = await vehicle_service.update_vehicle_location(
            vehicle_id=vehicle_id,
            latitude=location_data.latitude,
            longitude=location_data.longitude,
            timestamp=location_data.timestamp
        )
        if not success:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        return {"message": "Vehicle location updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{vehicle_id}/maintenance")
async def add_maintenance_record(
    vehicle_id: str,
    maintenance_data: MaintenanceRequest,
    vehicle_service: VehicleService = Depends(get_vehicle_service)
):
    """Add maintenance record for vehicle"""
    try:
        maintenance_record = await vehicle_service.add_maintenance_record(
            vehicle_id, maintenance_data.dict()
        )
        return {
            "message": "Maintenance record added successfully",
            "maintenance_record_id": str(maintenance_record.id)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{vehicle_id}/maintenance")
async def get_vehicle_maintenance_history(
    vehicle_id: str,
    vehicle_service: VehicleService = Depends(get_vehicle_service)
):
    """Get maintenance history for a vehicle"""
    try:
        maintenance_records = await vehicle_service.get_vehicle_maintenance_history(vehicle_id)
        return {
            "vehicle_id": vehicle_id,
            "maintenance_records": [
                {
                    "id": str(record.id),
                    "maintenance_type": record.maintenance_type,
                    "description": record.description,
                    "cost": record.cost,
                    "service_provider": record.service_provider,
                    "date": record.date,
                    "mileage_at_service": record.mileage_at_service,
                    "parts_replaced": record.parts_replaced,
                    "next_service_due": record.next_service_due
                }
                for record in maintenance_records
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/maintenance/due")
async def get_vehicles_due_for_maintenance(
    days_ahead: int = Query(30, ge=1, le=365, description="Days ahead to check for maintenance"),
    vehicle_service: VehicleService = Depends(get_vehicle_service)
):
    """Get vehicles due for maintenance"""
    try:
        vehicles = await vehicle_service.check_maintenance_due(days_ahead)
        return {
            "vehicles_due_for_maintenance": [
                {
                    "id": str(vehicle.id),
                    "license_plate": vehicle.license_plate,
                    "make": vehicle.make,
                    "model": vehicle.model,
                    "next_maintenance_date": vehicle.next_maintenance_date,
                    "mileage": vehicle.mileage
                }
                for vehicle in vehicles
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{vehicle_id}")
async def delete_vehicle(
    vehicle_id: str,
    vehicle_service: VehicleService = Depends(get_vehicle_service)
):
    """Delete a vehicle (soft delete)"""
    try:
        success = await vehicle_service.delete_vehicle(vehicle_id)
        if not success:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        return {"message": "Vehicle deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
