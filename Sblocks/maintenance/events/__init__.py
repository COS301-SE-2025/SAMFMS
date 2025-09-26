"""
Events package for Maintenance service

This package contains the event-driven communication system:
- events.py: Event definitions and schemas
- publisher.py: RabbitMQ event publisher  
- consumer.py: RabbitMQ event consumer and handlers
"""
from .events import (
    EventType,
    BaseEvent,
    MaintenanceEvent,
    LicenseEvent,
    AnalyticsEvent,
    ServiceEvent,
    NotificationEvent
)

from .publisher import event_publisher
#from .consumer import event_consumer, event_handlers, setup_event_handlers

__all__ = [
    # Event types and schemas
    "EventType",
    "BaseEvent", 
    "MaintenanceEvent",
    "LicenseEvent",
    "AnalyticsEvent",
    "ServiceEvent",
    "NotificationEvent",
    
    # Event system components
    "event_publisher",
    "event_consumer", 
    "event_handlers",
    "setup_event_handlers"
]
