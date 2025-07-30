"""
Event publisher for GPS service
"""
import aio_pika
import asyncio
import json
import logging
from typing import Dict, Any, Optional
import os
from datetime import datetime

from .events import (
    BaseEvent, EventType, LocationUpdatedEvent, GeofenceCreatedEvent, 
    GeofenceEvent, PlaceCreatedEvent, ServiceStartedEvent
)

logger = logging.getLogger(__name__)


class EventPublisher:
    """Event publisher for RabbitMQ"""
    
    def __init__(self):
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.rabbitmq_url = os.getenv(
            "RABBITMQ_URL", 
            "amqp://samfms_rabbit:RabbitPass2025!@rabbitmq:5672/"
        )
        self.exchange_name = "gps_events"
        self.exchange: Optional[aio_pika.Exchange] = None
        
    async def connect(self):
        """Connect to RabbitMQ"""
        try:
            self.connection = await aio_pika.connect_robust(
                self.rabbitmq_url,
                heartbeat=600,
                blocked_connection_timeout=300,
                connection_attempts=3,
                retry_delay=2
            )
            
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=100)
            
            # Declare exchange
            self.exchange = await self.channel.declare_exchange(
                self.exchange_name,
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )
            
            logger.info("Connected to RabbitMQ for event publishing")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from RabbitMQ"""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logger.info("Disconnected from RabbitMQ")
    
    def is_connected(self) -> bool:
        """Check if connected to RabbitMQ"""
        return (self.connection is not None and 
                not self.connection.is_closed and 
                self.exchange is not None)
    
    async def publish_event(self, event: BaseEvent, routing_key: str = None) -> bool:
        """Publish an event"""
        if not self.exchange:
            logger.error("Not connected to RabbitMQ")
            return False
        
        try:
            # Generate routing key if not provided
            if not routing_key:
                routing_key = f"gps.{event.event_type.value}"
            
            # Serialize event
            message_body = event.model_dump_json()
            
            # Create message
            message = aio_pika.Message(
                message_body.encode(),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                timestamp=datetime.utcnow(),
                headers={
                    "event_type": event.event_type.value,
                    "service": event.service,
                    "correlation_id": event.correlation_id
                }
            )
            
            # Publish message
            await self.exchange.publish(message, routing_key=routing_key)
            
            logger.info(f"Published event {event.event_type.value} with routing key {routing_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish event {event.event_type.value}: {e}")
            return False
    
    async def publish_service_started(self, version: str, data: Dict[str, Any]) -> bool:
        """Publish service started event"""
        event = ServiceStartedEvent(
            version=version,
            features=data
        )
        return await self.publish_event(event)
    
    async def publish_location_created(
        self, 
        vehicle_id: str, 
        latitude: float, 
        longitude: float,
        timestamp: datetime
    ) -> bool:
        """Publish location created event"""
        event = LocationUpdatedEvent(
            vehicle_id=vehicle_id,
            latitude=latitude,
            longitude=longitude,
            timestamp_location=timestamp
        )
        return await self.publish_event(event, f"gps.location.{vehicle_id}")
    
    async def publish_location_updated(
        self, 
        vehicle_id: str, 
        latitude: float, 
        longitude: float,
        timestamp: datetime
    ) -> bool:
        """Publish location updated event"""
        event = LocationUpdatedEvent(
            vehicle_id=vehicle_id,
            latitude=latitude,
            longitude=longitude,
            timestamp_location=timestamp
        )
        return await self.publish_event(event, f"gps.location.{vehicle_id}")
    
    async def publish_geofence_created(
        self, 
        geofence_id: str, 
        name: str, 
        created_by: Optional[str] = None
    ) -> bool:
        """Publish geofence created event"""
        event = GeofenceCreatedEvent(
            geofence_id=geofence_id,
            name=name,
            created_by=created_by
        )
        return await self.publish_event(event, "gps.geofence.created")
    
    async def publish_geofence_event(
        self, 
        vehicle_id: str, 
        geofence_id: str, 
        event_type: str,
        timestamp: datetime
    ) -> bool:
        """Publish geofence event (enter/exit/dwell)"""
        event = GeofenceEvent(
            vehicle_id=vehicle_id,
            geofence_id=geofence_id,
            geofence_event_type=event_type,
            timestamp_event=timestamp
        )
        return await self.publish_event(event, f"gps.geofence.{event_type}")
    
    async def publish_place_created(
        self, 
        place_id: str, 
        user_id: str, 
        name: str
    ) -> bool:
        """Publish place created event"""
        event = PlaceCreatedEvent(
            place_id=place_id,
            user_id=user_id,
            name=name
        )
        return await self.publish_event(event, f"gps.place.created.{user_id}")


# Global event publisher instance
event_publisher = EventPublisher()
