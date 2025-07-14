"""
Event-driven RabbitMQ publisher for Management service
"""
import aio_pika
import asyncio
import json
import logging
from typing import Dict, Any, Optional
import os
from datetime import datetime

from .events import BaseEvent, EventType

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
        self.exchange_name = "management_events"
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
    
    async def publish_event(self, event: BaseEvent, routing_key: str = None) -> bool:
        """Publish an event"""
        if not self.exchange:
            logger.error("Not connected to RabbitMQ")
            return False
        
        try:
            # Generate routing key if not provided
            if not routing_key:
                routing_key = f"management.{event.event_type.value}"
            
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
    
    # Specific event publishers
    async def publish_assignment_created(self, assignment_data: Dict[str, Any], user_id: str = None) -> bool:
        """Publish assignment created event"""
        from .events import AssignmentEvent
        
        event = AssignmentEvent(
            event_type=EventType.ASSIGNMENT_CREATED,
            assignment_id=assignment_data["id"],
            vehicle_id=assignment_data["vehicle_id"],
            driver_id=assignment_data["driver_id"],
            assignment_type=assignment_data["assignment_type"],
            status=assignment_data["status"],
            user_id=user_id,
            data=assignment_data
        )
        
        return await self.publish_event(event, "management.assignment.created")
    
    async def publish_assignment_completed(self, assignment_data: Dict[str, Any], user_id: str = None) -> bool:
        """Publish assignment completed event"""
        from .events import AssignmentEvent
        
        event = AssignmentEvent(
            event_type=EventType.ASSIGNMENT_COMPLETED,
            assignment_id=assignment_data["id"],
            vehicle_id=assignment_data["vehicle_id"],
            driver_id=assignment_data["driver_id"],
            assignment_type=assignment_data["assignment_type"],
            status=assignment_data["status"],
            user_id=user_id,
            data=assignment_data
        )
        
        return await self.publish_event(event, "management.assignment.completed")
    
    async def publish_trip_started(self, trip_data: Dict[str, Any], user_id: str = None) -> bool:
        """Publish trip started event"""
        from .events import TripEvent
        
        event = TripEvent(
            event_type=EventType.TRIP_STARTED,
            trip_id=trip_data["id"],
            vehicle_id=trip_data["vehicle_id"],
            driver_id=trip_data["driver_id"],
            assignment_id=trip_data.get("assignment_id"),
            user_id=user_id,
            data=trip_data
        )
        
        return await self.publish_event(event, "management.trip.started")
    
    async def publish_trip_ended(self, trip_data: Dict[str, Any], user_id: str = None) -> bool:
        """Publish trip ended event"""
        from .events import TripEvent
        
        event = TripEvent(
            event_type=EventType.TRIP_ENDED,
            trip_id=trip_data["id"],
            vehicle_id=trip_data["vehicle_id"],
            driver_id=trip_data["driver_id"],
            assignment_id=trip_data.get("assignment_id"),
            user_id=user_id,
            data=trip_data
        )
        
        return await self.publish_event(event, "management.trip.ended")
    
    async def publish_driver_created(self, driver_data: Dict[str, Any], user_id: str = None) -> bool:
        """Publish driver created event"""
        from .events import DriverEvent
        
        event = DriverEvent(
            event_type=EventType.DRIVER_CREATED,
            driver_id=driver_data["id"],
            employee_id=driver_data["employee_id"],
            user_id=user_id,
            data=driver_data
        )
        
        return await self.publish_event(event, "management.driver.created")
    
    async def publish_analytics_refreshed(self, metric_type: str, data: Dict[str, Any] = None) -> bool:
        """Publish analytics refreshed event"""
        from .events import AnalyticsEvent
        
        event = AnalyticsEvent(
            event_type=EventType.ANALYTICS_REFRESHED,
            metric_type=metric_type,
            data=data
        )
        
        return await self.publish_event(event, f"management.analytics.{metric_type}")
    
    async def publish_service_started(self, version: str = "1.0.0", data: Dict[str, Any] = None) -> bool:
        """Publish service started event"""
        from .events import ServiceEvent
        
        event = ServiceEvent(
            event_type=EventType.SERVICE_STARTED,
            service_status="started",
            version=version,
            data=data
        )
        
        return await self.publish_event(event, "management.service.started")
    
    async def publish_service_stopped(self, version: str = "1.0.0", data: Dict[str, Any] = None) -> bool:
        """Publish service stopped event"""
        from .events import ServiceEvent
        
        event = ServiceEvent(
            event_type=EventType.SERVICE_STOPPED,
            service_status="stopped",
            version=version,
            data=data
        )
        
        return await self.publish_event(event, "management.service.stopped")


# Global publisher instance
event_publisher = EventPublisher()
