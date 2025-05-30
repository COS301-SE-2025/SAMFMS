from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from typing import List, Optional
import logging
import os

from .models import (
    Vehicle, MaintenanceRecord, VehicleSpecification, VehicleDocument,
    VehicleCreate, VehicleUpdate, VehicleResponse,
    MaintenanceRecordCreate, MaintenanceRecordUpdate, MaintenanceRecordResponse,
    VehicleSpecificationCreate, VehicleSpecificationUpdate, VehicleSpecificationResponse,
    VehicleDocumentCreate, VehicleDocumentUpdate, VehicleDocumentResponse
)
from .database import get_db, log_vehicle_activity
from .message_queue import publish_maintenance_event

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

# Vehicle CRUD Routes
@router.post("/", response_model=VehicleResponse)
async def create_vehicle(
    vehicle: VehicleCreate,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a new vehicle record with technical specifications"""
    try:
        # Check if vehicle number already exists
        existing = db.query(Vehicle).filter(Vehicle.vehicle_number == vehicle.vehicle_number).first()
        if existing:
            raise HTTPException(status_code=400, detail="Vehicle number already exists")
        
        # Check if VIN already exists (if provided)
        if vehicle.vin:
            existing_vin = db.query(Vehicle).filter(Vehicle.vin == vehicle.vin).first()
            if existing_vin:
                raise HTTPException(status_code=400, detail="VIN already exists")
        
        # Create vehicle
        db_vehicle = Vehicle(**vehicle.dict())
        db.add(db_vehicle)
        db.commit()
        db.refresh(db_vehicle)
        
        # Log activity
        await log_vehicle_activity(
            vehicle_id=db_vehicle.id,
            activity_type="vehicle_created",
            description="Vehicle technical record created",
            details={"vehicle_number": vehicle.vehicle_number}
        )
        
        return db_vehicle
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating vehicle: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create vehicle")

@router.get("/", response_model=List[VehicleResponse])
async def get_vehicles(
    skip: int = 0,
    limit: int = 100,
    make: Optional[str] = None,
    model: Optional[str] = None,
    year: Optional[int] = None,
    fuel_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get vehicles with optional filters"""
    query = db.query(Vehicle)
    
    if make:
        query = query.filter(Vehicle.make.ilike(f"%{make}%"))
    if model:
        query = query.filter(Vehicle.model.ilike(f"%{model}%"))
    if year:
        query = query.filter(Vehicle.year == year)
    if fuel_type:
        query = query.filter(Vehicle.fuel_type == fuel_type)
    if is_active is not None:
        query = query.filter(Vehicle.is_active == is_active)
    
    vehicles = query.offset(skip).limit(limit).all()
    return vehicles

@router.get("/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get specific vehicle by ID"""
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle

@router.put("/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(
    vehicle_id: int,
    vehicle_update: VehicleUpdate,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update vehicle technical specifications"""
    try:
        db_vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
        if not db_vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        # Update fields
        update_data = vehicle_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_vehicle, field, value)
        
        db_vehicle.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(db_vehicle)
        
        # Log activity
        await log_vehicle_activity(
            vehicle_id=vehicle_id,
            activity_type="vehicle_updated",
            description="Vehicle technical specifications updated",
            details={"changes": update_data}
        )
        
        return db_vehicle
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating vehicle: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update vehicle")

@router.delete("/{vehicle_id}")
async def delete_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Soft delete vehicle (mark as inactive)"""
    try:
        db_vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
        if not db_vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        # Soft delete - mark as inactive
        db_vehicle.is_active = False
        db_vehicle.updated_at = datetime.now(timezone.utc)
        db.commit()
        
        # Log activity
        await log_vehicle_activity(
            vehicle_id=vehicle_id,
            activity_type="vehicle_deleted",
            description="Vehicle marked as inactive"
        )
        
        return {"message": "Vehicle marked as inactive"}
        
    except Exception as e:
        logger.error(f"Error deleting vehicle: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete vehicle")

# Maintenance Records Routes
@router.post("/{vehicle_id}/maintenance", response_model=MaintenanceRecordResponse)
async def create_maintenance_record(
    vehicle_id: int,
    maintenance: MaintenanceRecordCreate,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a new maintenance record"""
    try:
        # Verify vehicle exists
        vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        # Create maintenance record
        maintenance.vehicle_id = vehicle_id
        db_maintenance = MaintenanceRecord(**maintenance.dict())
        db.add(db_maintenance)
        db.commit()
        db.refresh(db_maintenance)
        
        # Update vehicle mileage if provided
        if maintenance.mileage_at_service and maintenance.mileage_at_service > vehicle.current_mileage:
            vehicle.current_mileage = maintenance.mileage_at_service
            vehicle.updated_at = datetime.now(timezone.utc)
            db.commit()
        
        # Log activity
        await log_vehicle_activity(
            vehicle_id=vehicle_id,
            activity_type="maintenance_recorded",
            description=f"Maintenance: {maintenance.maintenance_type}",
            details={"maintenance_type": maintenance.maintenance_type, "cost": maintenance.cost},
            user_id=maintenance.recorded_by
        )
        
        # Publish maintenance event
        publish_maintenance_event({
            "event_type": "maintenance_recorded",
            "vehicle_id": vehicle_id,
            "maintenance_id": db_maintenance.id,
            "maintenance_type": maintenance.maintenance_type,
            "service_date": maintenance.service_date.isoformat(),
            "cost": maintenance.cost,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return db_maintenance
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating maintenance record: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create maintenance record")

@router.get("/{vehicle_id}/maintenance", response_model=List[MaintenanceRecordResponse])
async def get_maintenance_records(
    vehicle_id: int,
    skip: int = 0,
    limit: int = 100,
    maintenance_type: Optional[str] = None,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get maintenance records for a vehicle"""
    query = db.query(MaintenanceRecord).filter(MaintenanceRecord.vehicle_id == vehicle_id)
    
    if maintenance_type:
        query = query.filter(MaintenanceRecord.maintenance_type == maintenance_type)
    
    records = query.order_by(MaintenanceRecord.service_date.desc()).offset(skip).limit(limit).all()
    return records

@router.get("/maintenance/{maintenance_id}", response_model=MaintenanceRecordResponse)
async def get_maintenance_record(
    maintenance_id: int,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get specific maintenance record"""
    record = db.query(MaintenanceRecord).filter(MaintenanceRecord.id == maintenance_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Maintenance record not found")
    return record

@router.put("/maintenance/{maintenance_id}", response_model=MaintenanceRecordResponse)
async def update_maintenance_record(
    maintenance_id: int,
    maintenance_update: MaintenanceRecordUpdate,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update maintenance record"""
    try:
        db_maintenance = db.query(MaintenanceRecord).filter(MaintenanceRecord.id == maintenance_id).first()
        if not db_maintenance:
            raise HTTPException(status_code=404, detail="Maintenance record not found")
        
        # Update fields
        update_data = maintenance_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_maintenance, field, value)
        
        db_maintenance.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(db_maintenance)
        
        # Log activity
        await log_vehicle_activity(
            vehicle_id=db_maintenance.vehicle_id,
            activity_type="maintenance_updated",
            description=f"Maintenance record {maintenance_id} updated",
            details={"changes": update_data}
        )
        
        return db_maintenance
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating maintenance record: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update maintenance record")

# Vehicle Specifications Routes
@router.post("/{vehicle_id}/specifications", response_model=VehicleSpecificationResponse)
async def create_vehicle_specifications(
    vehicle_id: int,
    specifications: VehicleSpecificationCreate,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create detailed vehicle specifications"""
    try:
        # Verify vehicle exists
        vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        # Check if specifications already exist
        existing = db.query(VehicleSpecification).filter(VehicleSpecification.vehicle_id == vehicle_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Specifications already exist for this vehicle")
        
        # Create specifications
        specifications.vehicle_id = vehicle_id
        db_specs = VehicleSpecification(**specifications.dict())
        db.add(db_specs)
        db.commit()
        db.refresh(db_specs)
        
        # Log activity
        await log_vehicle_activity(
            vehicle_id=vehicle_id,
            activity_type="specifications_created",
            description="Detailed vehicle specifications created"
        )
        
        return db_specs
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating specifications: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create specifications")

@router.get("/{vehicle_id}/specifications", response_model=VehicleSpecificationResponse)
async def get_vehicle_specifications(
    vehicle_id: int,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get vehicle specifications"""
    specs = db.query(VehicleSpecification).filter(VehicleSpecification.vehicle_id == vehicle_id).first()
    if not specs:
        raise HTTPException(status_code=404, detail="Specifications not found")
    return specs

@router.put("/{vehicle_id}/specifications", response_model=VehicleSpecificationResponse)
async def update_vehicle_specifications(
    vehicle_id: int,
    specifications_update: VehicleSpecificationUpdate,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update vehicle specifications"""
    try:
        db_specs = db.query(VehicleSpecification).filter(VehicleSpecification.vehicle_id == vehicle_id).first()
        if not db_specs:
            raise HTTPException(status_code=404, detail="Specifications not found")
        
        # Update fields
        update_data = specifications_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_specs, field, value)
        
        db_specs.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(db_specs)
        
        # Log activity
        await log_vehicle_activity(
            vehicle_id=vehicle_id,
            activity_type="specifications_updated",
            description="Vehicle specifications updated",
            details={"changes": update_data}
        )
        
        return db_specs
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating specifications: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update specifications")

# Vehicle Documents Routes
@router.post("/{vehicle_id}/documents", response_model=VehicleDocumentResponse)
async def create_vehicle_document(
    vehicle_id: int,
    document: VehicleDocumentCreate,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a vehicle document record"""
    try:
        # Verify vehicle exists
        vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        # Create document
        document.vehicle_id = vehicle_id
        db_document = VehicleDocument(**document.dict())
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        
        # Log activity
        await log_vehicle_activity(
            vehicle_id=vehicle_id,
            activity_type="document_created",
            description=f"Document created: {document.document_type}",
            details={"document_type": document.document_type},
            user_id=document.uploaded_by
        )
        
        return db_document
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating document: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create document")

@router.get("/{vehicle_id}/documents", response_model=List[VehicleDocumentResponse])
async def get_vehicle_documents(
    vehicle_id: int,
    document_type: Optional[str] = None,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get vehicle documents"""
    query = db.query(VehicleDocument).filter(VehicleDocument.vehicle_id == vehicle_id)
    
    if document_type:
        query = query.filter(VehicleDocument.document_type == document_type)
    
    documents = query.order_by(VehicleDocument.created_at.desc()).all()
    return documents

@router.get("/documents/expiring")
async def get_expiring_documents(
    days: int = 30,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get documents expiring within specified days"""
    cutoff_date = datetime.now(timezone.utc) + timedelta(days=days)
    
    expiring_docs = db.query(VehicleDocument).filter(
        VehicleDocument.expiry_date <= cutoff_date,
        VehicleDocument.is_valid == True
    ).all()
    
    return [
        {
            "vehicle_id": doc.vehicle_id,
            "document_type": doc.document_type,
            "document_number": doc.document_number,
            "expiry_date": doc.expiry_date,
            "days_until_expiry": (doc.expiry_date - datetime.now(timezone.utc)).days
        }
        for doc in expiring_docs
    ]

# Analytics and Reports Routes
@router.get("/{vehicle_id}/maintenance-schedule")
async def get_maintenance_schedule(
    vehicle_id: int,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get upcoming maintenance schedule for a vehicle"""
    try:
        # Get all maintenance records with next service dates
        upcoming_maintenance = db.query(MaintenanceRecord).filter(
            MaintenanceRecord.vehicle_id == vehicle_id,
            MaintenanceRecord.next_service_date.isnot(None),
            MaintenanceRecord.next_service_date >= datetime.now(timezone.utc)
        ).order_by(MaintenanceRecord.next_service_date).all()
        
        # Get vehicle current mileage
        vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
        current_mileage = vehicle.current_mileage if vehicle else 0
        
        schedule = []
        for record in upcoming_maintenance:
            days_until = (record.next_service_date - datetime.now(timezone.utc)).days
            schedule.append({
                "maintenance_type": record.maintenance_type,
                "next_service_date": record.next_service_date,
                "next_service_mileage": record.next_service_mileage,
                "days_until_service": days_until,
                "mileage_until_service": (record.next_service_mileage - current_mileage) if record.next_service_mileage else None,
                "last_service_date": record.service_date,
                "last_service_mileage": record.mileage_at_service
            })
        
        return {
            "vehicle_id": vehicle_id,
            "current_mileage": current_mileage,
            "upcoming_maintenance": schedule
        }
        
    except Exception as e:
        logger.error(f"Error getting maintenance schedule: {e}")
        raise HTTPException(status_code=500, detail="Failed to get maintenance schedule")

@router.get("/{vehicle_id}/maintenance-history")
async def get_maintenance_history(
    vehicle_id: int,
    days: int = 365,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get maintenance history analysis for a vehicle"""
    try:
        from sqlalchemy import func
        
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get maintenance statistics
        maintenance_stats = db.query(
            func.count(MaintenanceRecord.id).label('total_services'),
            func.sum(MaintenanceRecord.cost).label('total_cost'),
            func.avg(MaintenanceRecord.cost).label('avg_cost'),
            func.max(MaintenanceRecord.service_date).label('last_service')
        ).filter(
            MaintenanceRecord.vehicle_id == vehicle_id,
            MaintenanceRecord.service_date >= start_date
        ).first()
        
        # Get maintenance by type
        maintenance_by_type = db.query(
            MaintenanceRecord.maintenance_type,
            func.count(MaintenanceRecord.id).label('count'),
            func.sum(MaintenanceRecord.cost).label('total_cost')
        ).filter(
            MaintenanceRecord.vehicle_id == vehicle_id,
            MaintenanceRecord.service_date >= start_date
        ).group_by(MaintenanceRecord.maintenance_type).all()
        
        return {
            "vehicle_id": vehicle_id,
            "period_days": days,
            "total_services": maintenance_stats.total_services or 0,
            "total_cost": float(maintenance_stats.total_cost or 0),
            "average_cost": float(maintenance_stats.avg_cost or 0),
            "last_service_date": maintenance_stats.last_service,
            "maintenance_breakdown": [
                {
                    "maintenance_type": item.maintenance_type,
                    "count": item.count,
                    "total_cost": float(item.total_cost or 0)
                }
                for item in maintenance_by_type
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting maintenance history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get maintenance history")

@router.get("/fleet/overview")
async def get_fleet_overview(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get fleet overview statistics"""
    try:
        from sqlalchemy import func, distinct
        
        # Vehicle statistics
        total_vehicles = db.query(func.count(Vehicle.id)).filter(Vehicle.is_active == True).scalar()
        vehicles_by_fuel = db.query(
            Vehicle.fuel_type,
            func.count(Vehicle.id).label('count')
        ).filter(Vehicle.is_active == True).group_by(Vehicle.fuel_type).all()
        
        avg_age = db.query(
            func.avg(2024 - Vehicle.year).label('avg_age')
        ).filter(Vehicle.is_active == True).scalar()
        
        # Maintenance statistics
        total_maintenance_cost = db.query(func.sum(MaintenanceRecord.cost)).scalar()
        recent_maintenance = db.query(func.count(MaintenanceRecord.id)).filter(
            MaintenanceRecord.service_date >= datetime.now(timezone.utc) - timedelta(days=30)
        ).scalar()
        
        # Documents expiring soon
        expiring_docs = db.query(func.count(VehicleDocument.id)).filter(
            VehicleDocument.expiry_date <= datetime.now(timezone.utc) + timedelta(days=30),
            VehicleDocument.is_valid == True
        ).scalar()
        
        return {
            "fleet_statistics": {
                "total_active_vehicles": total_vehicles or 0,
                "average_vehicle_age": float(avg_age or 0),
                "vehicles_by_fuel_type": [
                    {"fuel_type": item.fuel_type, "count": item.count}
                    for item in vehicles_by_fuel
                ]
            },
            "maintenance_statistics": {
                "total_lifetime_cost": float(total_maintenance_cost or 0),
                "recent_services_30_days": recent_maintenance or 0
            },
            "alerts": {
                "documents_expiring_30_days": expiring_docs or 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting fleet overview: {e}")
        raise HTTPException(status_code=500, detail="Failed to get fleet overview")
