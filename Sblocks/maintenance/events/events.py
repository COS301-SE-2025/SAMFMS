"""
Event definitions for Maintenance service
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    """Event types for Maintenance service"""
    # Maintenance events
    MAINTENANCE_RECORD_CREATED = "maintenance.record.created"
    MAINTENANCE_RECORD_UPDATED = "maintenance.record.updated"
    MAINTENANCE_RECORD_DELETED = "maintenance.record.deleted"
    MAINTENANCE_RECORD_COMPLETED = "maintenance.record.completed"
    MAINTENANCE_RECORD_SCHEDULED = "maintenance.record.scheduled"
    
    # License events
    LICENSE_CREATED = "license.created"
    LICENSE_UPDATED = "license.updated"
    LICENSE_DELETED = "license.deleted"
    LICENSE_RENEWED = "license.renewed"
    LICENSE_EXPIRED = "license.expired"
    LICENSE_EXPIRING_SOON = "license.expiring_soon"
    
    # Notification events
    NOTIFICATION_CREATED = "notification.created"
    NOTIFICATION_SENT = "notification.sent"
    NOTIFICATION_READ = "notification.read"
    
    # Analytics events
    ANALYTICS_REFRESHED = "analytics.refreshed"
    MAINTENANCE_ANALYTICS_UPDATED = "maintenance.analytics.updated"
    
    # Service events
    SERVICE_STARTED = "service.started"
    SERVICE_STOPPED = "service.stopped"
    SERVICE_HEALTH_CHECK = "service.health_check"


class BaseEvent(BaseModel):
    """Base event model"""
    event_id: str = Field(default_factory=lambda: str(datetime.utcnow().timestamp()))
    event_type: EventType
    service: str = "maintenance"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None


class MaintenanceEvent(BaseEvent):
    """Maintenance record event"""
    maintenance_id: str
    vehicle_id: str
    maintenance_type: str
    status: str
    data: Optional[Dict[str, Any]] = None


class LicenseEvent(BaseEvent):
    """License event"""
    license_id: str
    license_type: str
    vehicle_id: Optional[str] = None
    driver_id: Optional[str] = None
    status: str
    expiry_date: Optional[datetime] = None
    data: Optional[Dict[str, Any]] = None


class NotificationEvent(BaseEvent):
    """Notification event"""
    notification_id: str
    notification_type: str
    recipient_id: str
    message: str
    status: str
    data: Optional[Dict[str, Any]] = None


class AnalyticsEvent(BaseEvent):
    """Analytics event"""
    metric_type: str
    data: Optional[Dict[str, Any]] = None


class ServiceEvent(BaseEvent):
    """Service lifecycle event"""
    service_status: str
    version: str = "1.0.0"
    data: Optional[Dict[str, Any]] = None
