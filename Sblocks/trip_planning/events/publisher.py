"""
Event publisher for Trip Planning service
"""
import aio_pika
import asyncio
import json
import logging
from typing import Dict, Any, Optional
import os
from datetime import datetime

from .events import (
    BaseEvent, EventType, TripCreatedEvent, TripUpdatedEvent, TripDeletedEvent,
    TripStartedEvent, TripCompletedEvent, TripDelayedEvent, DriverAssignedEvent,
    DriverUnassignedEvent, RouteOptimizedEvent, NotificationSentEvent, ServiceStartedEvent
)
from schemas.entities import Trip, DriverAssignment

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
        self.exchange_name = "trip_planning_events"
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
                routing_key = f"trips.{event.event_type.value}"
            
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
    
    # Trip-related event publishers
    async def publish_trip_created(self, trip: Trip):
        """Publish trip created event"""
        event = TripCreatedEvent.from_trip(trip)
        await self.publish_event(event, "trip.created")
    
    async def publish_trip_updated(self, trip: Trip, previous_trip: Trip):
        """Publish trip updated event"""
        event = TripUpdatedEvent.from_trip(trip, previous_trip)
        await self.publish_event(event, "trip.updated")
    
    async def publish_trip_deleted(self, trip: Trip):
        """Publish trip deleted event"""
        event = TripDeletedEvent.from_trip(trip)
        await self.publish_event(event, "trip.deleted")
    
    async def publish_trip_started(self, trip: Trip):
        """Publish trip started event"""
        event = TripStartedEvent.from_trip(trip)
        await self.publish_event(event, "trip.started")
    
    async def publish_trip_completed(self, trip: Trip):
        """Publish trip completed event"""
        event = TripCompletedEvent.from_trip(trip)
        await self.publish_event(event, "trip.completed")
    
    async def publish_trip_delayed(self, trip: Trip, delay_minutes: int, reason: str = None):
        """Publish trip delayed event"""
        event = TripDelayedEvent.from_trip(trip, delay_minutes, reason)
        await self.publish_event(event, "trip.delayed")
    
    # Driver-related event publishers
    async def publish_driver_assigned(self, assignment: DriverAssignment, trip: Trip):
        """Publish driver assigned event"""
        event = DriverAssignedEvent.from_assignment(assignment, trip)
        await self.publish_event(event, "driver.assigned")
    
    async def publish_driver_unassigned(self, assignment: DriverAssignment, trip: Trip):
        """Publish driver unassigned event"""
        event = DriverUnassignedEvent.from_assignment(assignment, trip)
        await self.publish_event(event, "driver.unassigned")
    
    # Route-related event publishers
    async def publish_route_optimized(
        self,
        trip_id: str,
        original_duration: int,
        optimized_duration: int,
        original_distance: float,
        optimized_distance: float
    ):
        """Publish route optimized event"""
        event = RouteOptimizedEvent.from_optimization(
            trip_id, original_duration, optimized_duration,
            original_distance, optimized_distance
        )
        await self.publish_event(event, "route.optimized")
    
    # Notification-related event publishers
    async def publish_notification_sent(self, notification_id: str, user_id: str, notification_type: str):
        """Publish notification sent event"""
        event = NotificationSentEvent.from_notification(notification_id, user_id, notification_type)
        await self.publish_event(event, "notification.sent")
    
    # Service-related event publishers
    async def publish_service_started(self, service_name: str, version: str):
        """Publish service started event"""
        event = ServiceStartedEvent.create(service_name, version)
        await self.publish_event(event, "service.started")
    
    # Batch publishing
    async def publish_multiple_events(self, events: list[tuple[BaseEvent, str]]):
        """Publish multiple events in batch"""
        try:
            if not self.is_connected():
                await self.connect()
            
            async with self.channel.transaction():
                for event, routing_key in events:
                    await self.publish_event(event, routing_key)
            
            logger.info(f"Published {len(events)} events in batch")
            
        except Exception as e:
            logger.error(f"Failed to publish batch events: {e}")
            raise


# Global event publisher instance
event_publisher = EventPublisher()
