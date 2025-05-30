from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

Base = declarative_base()

# SQLAlchemy Models
class Vehicle(Base):
    """Vehicle technical specifications and basic information"""
    __tablename__ = "vehicles"
    
    id = Column(Integer, primary_key=True, index=True)
    vehicle_number = Column(String(50), unique=True, index=True, nullable=False)
    make = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    year = Column(Integer, nullable=False)
    vin = Column(String(17), unique=True, index=True)
    license_plate = Column(String(20), unique=True, index=True)
    
    # Technical specifications
    engine_type = Column(String(100))
    fuel_type = Column(String(50))
    fuel_capacity = Column(Float)  # in liters
    seating_capacity = Column(Integer)
    max_load_capacity = Column(Float)  # in kg
    transmission_type = Column(String(50))
    drive_type = Column(String(50))  # FWD, RWD, AWD, 4WD
    
    # Physical specifications
    length = Column(Float)  # in meters
    width = Column(Float)   # in meters
    height = Column(Float)  # in meters
    weight = Column(Float)  # in kg
    color = Column(String(50))
    
    # Operational data
    current_mileage = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    purchase_date = Column(DateTime)
    purchase_price = Column(Float)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Additional specifications as JSON
    additional_specs = Column(JSON)  # For any additional specifications

class MaintenanceRecord(Base):
    """Vehicle maintenance history"""
    __tablename__ = "maintenance_records"
    
    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, index=True, nullable=False)
    maintenance_type = Column(String(100), nullable=False)  # oil_change, tire_replacement, etc.
    description = Column(Text)
    
    # Maintenance details
    service_date = Column(DateTime, nullable=False)
    service_provider = Column(String(200))
    cost = Column(Float)
    mileage_at_service = Column(Float)
    
    # Parts and labor
    parts_replaced = Column(JSON)  # List of parts replaced
    labor_hours = Column(Float)
    warranty_until = Column(DateTime)
    
    # Next service
    next_service_date = Column(DateTime)
    next_service_mileage = Column(Float)
    
    # Metadata
    recorded_by = Column(Integer)  # User ID who recorded the maintenance
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Additional notes
    notes = Column(Text)

class VehicleSpecification(Base):
    """Detailed vehicle specifications and features"""
    __tablename__ = "vehicle_specifications"
    
    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, index=True, nullable=False)
    
    # Engine specifications
    engine_displacement = Column(Float)  # in liters
    horsepower = Column(Integer)
    torque = Column(Integer)  # in Nm
    compression_ratio = Column(String(20))
    
    # Performance
    top_speed = Column(Integer)  # km/h
    acceleration_0_100 = Column(Float)  # seconds
    fuel_efficiency_city = Column(Float)  # km/l
    fuel_efficiency_highway = Column(Float)  # km/l
    fuel_efficiency_combined = Column(Float)  # km/l
    
    # Safety features
    safety_rating = Column(String(10))
    airbags_count = Column(Integer)
    has_abs = Column(Boolean, default=False)
    has_stability_control = Column(Boolean, default=False)
    has_traction_control = Column(Boolean, default=False)
    
    # Technology features
    infotainment_system = Column(String(100))
    has_gps = Column(Boolean, default=False)
    has_bluetooth = Column(Boolean, default=False)
    has_wifi = Column(Boolean, default=False)
    has_usb_ports = Column(Boolean, default=False)
    usb_ports_count = Column(Integer, default=0)
    
    # Comfort features
    air_conditioning_type = Column(String(50))
    seat_material = Column(String(50))
    has_power_steering = Column(Boolean, default=False)
    has_power_windows = Column(Boolean, default=False)
    has_central_locking = Column(Boolean, default=False)
    
    # Additional features as JSON
    additional_features = Column(JSON)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class VehicleDocument(Base):
    """Vehicle-related documents and certificates"""
    __tablename__ = "vehicle_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, index=True, nullable=False)
    document_type = Column(String(100), nullable=False)  # registration, insurance, etc.
    document_number = Column(String(100))
    
    # Document details
    issuing_authority = Column(String(200))
    issue_date = Column(DateTime)
    expiry_date = Column(DateTime)
    is_valid = Column(Boolean, default=True)
    
    # File information
    file_path = Column(String(500))  # Path to stored document file
    file_name = Column(String(200))
    file_size = Column(Integer)  # in bytes
    file_type = Column(String(50))  # pdf, jpg, etc.
    
    # Metadata
    uploaded_by = Column(Integer)  # User ID who uploaded the document
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Additional notes
    notes = Column(Text)

# Pydantic Models for API
class VehicleBase(BaseModel):
    vehicle_number: str = Field(..., description="Unique vehicle identifier")
    make: str = Field(..., description="Vehicle manufacturer")
    model: str = Field(..., description="Vehicle model")
    year: int = Field(..., description="Manufacturing year")
    vin: Optional[str] = Field(None, description="Vehicle Identification Number")
    license_plate: Optional[str] = Field(None, description="License plate number")
    
    engine_type: Optional[str] = None
    fuel_type: Optional[str] = None
    fuel_capacity: Optional[float] = None
    seating_capacity: Optional[int] = None
    max_load_capacity: Optional[float] = None
    transmission_type: Optional[str] = None
    drive_type: Optional[str] = None
    
    length: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    color: Optional[str] = None
    
    current_mileage: Optional[float] = 0.0
    is_active: Optional[bool] = True
    purchase_date: Optional[datetime] = None
    purchase_price: Optional[float] = None
    
    additional_specs: Optional[Dict[str, Any]] = None

class VehicleCreate(VehicleBase):
    pass

class VehicleUpdate(BaseModel):
    vehicle_number: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    vin: Optional[str] = None
    license_plate: Optional[str] = None
    
    engine_type: Optional[str] = None
    fuel_type: Optional[str] = None
    fuel_capacity: Optional[float] = None
    seating_capacity: Optional[int] = None
    max_load_capacity: Optional[float] = None
    transmission_type: Optional[str] = None
    drive_type: Optional[str] = None
    
    length: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    color: Optional[str] = None
    
    current_mileage: Optional[float] = None
    is_active: Optional[bool] = None
    purchase_date: Optional[datetime] = None
    purchase_price: Optional[float] = None
    
    additional_specs: Optional[Dict[str, Any]] = None

class VehicleResponse(VehicleBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class MaintenanceRecordBase(BaseModel):
    vehicle_id: int
    maintenance_type: str
    description: Optional[str] = None
    service_date: datetime
    service_provider: Optional[str] = None
    cost: Optional[float] = None
    mileage_at_service: Optional[float] = None
    parts_replaced: Optional[Dict[str, Any]] = None
    labor_hours: Optional[float] = None
    warranty_until: Optional[datetime] = None
    next_service_date: Optional[datetime] = None
    next_service_mileage: Optional[float] = None
    recorded_by: Optional[int] = None
    notes: Optional[str] = None

class MaintenanceRecordCreate(MaintenanceRecordBase):
    pass

class MaintenanceRecordUpdate(BaseModel):
    maintenance_type: Optional[str] = None
    description: Optional[str] = None
    service_date: Optional[datetime] = None
    service_provider: Optional[str] = None
    cost: Optional[float] = None
    mileage_at_service: Optional[float] = None
    parts_replaced: Optional[Dict[str, Any]] = None
    labor_hours: Optional[float] = None
    warranty_until: Optional[datetime] = None
    next_service_date: Optional[datetime] = None
    next_service_mileage: Optional[float] = None
    notes: Optional[str] = None

class MaintenanceRecordResponse(MaintenanceRecordBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class VehicleSpecificationBase(BaseModel):
    vehicle_id: int
    engine_displacement: Optional[float] = None
    horsepower: Optional[int] = None
    torque: Optional[int] = None
    compression_ratio: Optional[str] = None
    top_speed: Optional[int] = None
    acceleration_0_100: Optional[float] = None
    fuel_efficiency_city: Optional[float] = None
    fuel_efficiency_highway: Optional[float] = None
    fuel_efficiency_combined: Optional[float] = None
    safety_rating: Optional[str] = None
    airbags_count: Optional[int] = None
    has_abs: Optional[bool] = False
    has_stability_control: Optional[bool] = False
    has_traction_control: Optional[bool] = False
    infotainment_system: Optional[str] = None
    has_gps: Optional[bool] = False
    has_bluetooth: Optional[bool] = False
    has_wifi: Optional[bool] = False
    has_usb_ports: Optional[bool] = False
    usb_ports_count: Optional[int] = 0
    air_conditioning_type: Optional[str] = None
    seat_material: Optional[str] = None
    has_power_steering: Optional[bool] = False
    has_power_windows: Optional[bool] = False
    has_central_locking: Optional[bool] = False
    additional_features: Optional[Dict[str, Any]] = None

class VehicleSpecificationCreate(VehicleSpecificationBase):
    pass

class VehicleSpecificationUpdate(BaseModel):
    engine_displacement: Optional[float] = None
    horsepower: Optional[int] = None
    torque: Optional[int] = None
    compression_ratio: Optional[str] = None
    top_speed: Optional[int] = None
    acceleration_0_100: Optional[float] = None
    fuel_efficiency_city: Optional[float] = None
    fuel_efficiency_highway: Optional[float] = None
    fuel_efficiency_combined: Optional[float] = None
    safety_rating: Optional[str] = None
    airbags_count: Optional[int] = None
    has_abs: Optional[bool] = None
    has_stability_control: Optional[bool] = None
    has_traction_control: Optional[bool] = None
    infotainment_system: Optional[str] = None
    has_gps: Optional[bool] = None
    has_bluetooth: Optional[bool] = None
    has_wifi: Optional[bool] = None
    has_usb_ports: Optional[bool] = None
    usb_ports_count: Optional[int] = None
    air_conditioning_type: Optional[str] = None
    seat_material: Optional[str] = None
    has_power_steering: Optional[bool] = None
    has_power_windows: Optional[bool] = None
    has_central_locking: Optional[bool] = None
    additional_features: Optional[Dict[str, Any]] = None

class VehicleSpecificationResponse(VehicleSpecificationBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class VehicleDocumentBase(BaseModel):
    vehicle_id: int
    document_type: str
    document_number: Optional[str] = None
    issuing_authority: Optional[str] = None
    issue_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    is_valid: Optional[bool] = True
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    uploaded_by: Optional[int] = None
    notes: Optional[str] = None

class VehicleDocumentCreate(VehicleDocumentBase):
    pass

class VehicleDocumentUpdate(BaseModel):
    document_type: Optional[str] = None
    document_number: Optional[str] = None
    issuing_authority: Optional[str] = None
    issue_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    is_valid: Optional[bool] = None
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    notes: Optional[str] = None

class VehicleDocumentResponse(VehicleDocumentBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Message Queue Models
class VehicleEventMessage(BaseModel):
    event_type: str
    vehicle_id: int
    timestamp: str
    data: Dict[str, Any]
    source: str = "management_service"

class MaintenanceEventMessage(BaseModel):
    event_type: str
    vehicle_id: int
    maintenance_id: Optional[int] = None
    timestamp: str
    data: Dict[str, Any]
    source: str = "vehicles_service"
