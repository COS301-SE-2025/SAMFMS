"""
Maintenance Service Schema Entities
Defines data models for maintenance operations
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class MaintenanceType(str, Enum):
    """Types of maintenance operations"""
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    SCHEDULED = "scheduled"
    EMERGENCY = "emergency"
    INSPECTION = "inspection"


class MaintenanceStatus(str, Enum):
    """Status of maintenance operations"""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"


class MaintenancePriority(str, Enum):
    """Priority levels for maintenance"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class LicenseType(str, Enum):
    """Types of licenses and certifications"""
    VEHICLE_REGISTRATION = "vehicle_registration"
    DRIVERS_LICENSE = "drivers_license"
    COMMERCIAL_LICENSE = "commercial_license"
    INSURANCE = "insurance"
    ROADWORTHY_CERTIFICATE = "roadworthy_certificate"
    EMISSIONS_CERTIFICATE = "emissions_certificate"
    OPERATING_PERMIT = "operating_permit"


class MaintenanceRecord(BaseModel):
    """Maintenance record entity"""
    id: Optional[str] = Field(None, alias="_id")
    vehicle_id: str = Field(..., description="Vehicle identifier")
    maintenance_type: MaintenanceType
    status: MaintenanceStatus = MaintenanceStatus.SCHEDULED
    priority: MaintenancePriority = MaintenancePriority.MEDIUM
    
    # Scheduling information
    scheduled_date: datetime = Field(..., description="When maintenance is scheduled")
    estimated_duration: Optional[int] = Field(None, description="Estimated duration in hours")
    actual_start_date: Optional[datetime] = None
    actual_completion_date: Optional[datetime] = None
    
    # Description and details
    title: str = Field(..., description="Maintenance task title")
    description: Optional[str] = Field(None, description="Detailed description")
    work_performed: Optional[str] = Field(None, description="Work that was performed")
    
    # Cost tracking
    estimated_cost: Optional[float] = Field(None, description="Estimated cost")
    actual_cost: Optional[float] = Field(None, description="Actual cost incurred")
    labor_cost: Optional[float] = Field(None, description="Labor cost")
    parts_cost: Optional[float] = Field(None, description="Parts cost")
    
    # Personnel and vendor information
    assigned_technician: Optional[str] = Field(None, description="Assigned technician ID")
    vendor_id: Optional[str] = Field(None, description="Service vendor ID")
    service_provider: Optional[str] = Field(None, description="Service provider name")
    
    # Mileage information
    mileage_at_service: Optional[int] = Field(None, description="Vehicle mileage at service")
    next_service_mileage: Optional[int] = Field(None, description="Next service due at mileage")
    
    # Parts and materials
    parts_used: Optional[List[Dict[str, Any]]] = Field(None, description="Parts used in maintenance")
    warranty_info: Optional[Dict[str, Any]] = Field(None, description="Warranty information")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = Field(None, description="User who created the record")
    
    # Recurring maintenance
    is_recurring: bool = False
    recurrence_interval: Optional[int] = Field(None, description="Recurrence interval in days")
    parent_schedule_id: Optional[str] = Field(None, description="Parent schedule if recurring")
    
    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MaintenanceSchedule(BaseModel):
    """Maintenance schedule template"""
    id: Optional[str] = Field(None, alias="_id")
    vehicle_id: Optional[str] = Field(None, description="Specific vehicle or None for all vehicles")
    vehicle_type: Optional[str] = Field(None, description="Vehicle type if applicable to multiple vehicles")
    
    # Schedule details
    name: str = Field(..., description="Schedule name")
    description: Optional[str] = Field(None, description="Schedule description")
    maintenance_type: MaintenanceType
    priority: MaintenancePriority = MaintenancePriority.MEDIUM
    
    # Interval settings
    interval_type: str = Field(..., description="time_based, mileage_based, or hybrid")
    interval_days: Optional[int] = Field(None, description="Days between services")
    interval_mileage: Optional[int] = Field(None, description="Mileage between services")
    
    # Cost estimates
    estimated_cost: Optional[float] = Field(None, description="Estimated cost per service")
    estimated_duration: Optional[int] = Field(None, description="Estimated duration in hours")
    
    # Notification settings
    advance_notice_days: int = Field(default=7, description="Days before to send notification")
    
    # Status
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        allow_population_by_field_name = True


class LicenseRecord(BaseModel):
    """License and certification tracking"""
    id: Optional[str] = Field(None, alias="_id")
    entity_id: str = Field(..., description="Vehicle ID or Driver ID")
    entity_type: str = Field(..., description="vehicle or driver")
    
    # License details
    license_type: LicenseType
    license_number: str = Field(..., description="License/certificate number")
    title: str = Field(..., description="License title/name")
    description: Optional[str] = Field(None, description="License description")
    
    # Dates
    issue_date: date = Field(..., description="Date issued")
    expiry_date: date = Field(..., description="Expiry date")
    renewal_date: Optional[date] = Field(None, description="Last renewal date")
    
    # Issuing authority
    issuing_authority: str = Field(..., description="Issuing authority")
    issuing_country: Optional[str] = Field(None, description="Country of issue")
    issuing_state: Optional[str] = Field(None, description="State/province of issue")
    
    # Status and notifications
    is_active: bool = True
    advance_notice_days: int = Field(default=30, description="Days before expiry to notify")
    
    # Cost tracking
    cost: Optional[float] = Field(None, description="License cost")
    renewal_cost: Optional[float] = Field(None, description="Renewal cost")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        allow_population_by_field_name = True


class MaintenanceVendor(BaseModel):
    """Service vendor/provider information"""
    id: Optional[str] = Field(None, alias="_id")
    name: str = Field(..., description="Vendor name")
    contact_person: Optional[str] = Field(None, description="Primary contact person")
    
    # Contact information
    phone: Optional[str] = Field(None, description="Phone number")
    email: Optional[str] = Field(None, description="Email address")
    address: Optional[str] = Field(None, description="Physical address")
    
    # Service details
    services_offered: List[str] = Field(default_factory=list, description="Services they provide")
    specializations: List[str] = Field(default_factory=list, description="Areas of specialization")
    
    # Business information
    business_hours: Optional[str] = Field(None, description="Business hours")
    emergency_contact: Optional[str] = Field(None, description="Emergency contact number")
    
    # Performance tracking
    rating: Optional[float] = Field(None, description="Vendor rating (1-5)")
    total_jobs: int = Field(default=0, description="Total jobs completed")
    average_cost: Optional[float] = Field(None, description="Average job cost")
    
    # Status
    is_active: bool = True
    is_preferred: bool = False
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        allow_population_by_field_name = True


class MaintenanceNotification(BaseModel):
    """Maintenance notification/alert"""
    id: Optional[str] = Field(None, alias="_id")
    
    # Notification details
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    notification_type: str = Field(..., description="Type of notification")
    priority: MaintenancePriority = MaintenancePriority.MEDIUM
    
    # Related entities
    vehicle_id: Optional[str] = Field(None, description="Related vehicle")
    maintenance_record_id: Optional[str] = Field(None, description="Related maintenance record")
    license_record_id: Optional[str] = Field(None, description="Related license record")
    
    # Recipients
    recipient_user_ids: List[str] = Field(default_factory=list, description="User IDs to notify")
    recipient_roles: List[str] = Field(default_factory=list, description="Roles to notify")
    
    # Status
    is_sent: bool = False
    is_read: bool = False
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    
    # Scheduling
    scheduled_send_time: Optional[datetime] = Field(None, description="When to send notification")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        allow_population_by_field_name = True
