"""
Messaging package initialization
"""
from messaging.rabbitmq_client import (
    messaging_client,
    publish_location_update,
    publish_geofence_event,
    publish_speed_violation,
    publish_route_event,
    publish_vehicle_idle,
    publish_emergency_alert,
    initialize_messaging,
    cleanup_messaging,
    check_messaging_health
)

__all__ = [
    "messaging_client",
    "publish_location_update",
    "publish_geofence_event",
    "publish_speed_violation", 
    "publish_route_event",
    "publish_vehicle_idle",
    "publish_emergency_alert",
    "initialize_messaging",
    "cleanup_messaging",
    "check_messaging_health"
]
