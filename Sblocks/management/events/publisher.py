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
# Import standardized config
from config.rabbitmq_config import RabbitMQConfig
from . import admin

logger = logging.getLogger(__name__)


class EventPublisher:
    """Event publisher for RabbitMQ"""
    
    def __init__(self):
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        # Use standardized config
        self.config = RabbitMQConfig()
        self.rabbitmq_url = self.config.get_rabbitmq_url()
        self.exchange_name = "management_events"
        self.exchange: Optional[aio_pika.Exchange] = None
        
    async def connect(self):
        """Connect to RabbitMQ"""
        try:
            self.connection = await aio_pika.connect_robust(
                self.rabbitmq_url,
                heartbeat=self.config.CONNECTION_PARAMS["heartbeat"],
                blocked_connection_timeout=self.config.CONNECTION_PARAMS["blocked_connection_timeout"],
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
    
    # Vehicle event publishers
    async def publish_vehicle_created(self, vehicle_data: Dict[str, Any], user_id: str = None) -> bool:
        """Publish vehicle created event"""
        from .events import VehicleEvent
        
        event = VehicleEvent(
            event_type=EventType.VEHICLE_CREATED,
            vehicle_id=str(vehicle_data["_id"]),
            registration_number=vehicle_data["registration_number"],
            status=vehicle_data["status"],
            user_id=user_id,
            data=vehicle_data
        )
        
        return await self.publish_event(event, "vehicle.created")
    
    async def publish_vehicle_updated(self, vehicle_data: Dict[str, Any], user_id: str = None, changes: Dict[str, Any] = None) -> bool:
        """Publish vehicle updated event"""
        from .events import VehicleEvent
        
        event = VehicleEvent(
            event_type=EventType.VEHICLE_UPDATED,
            vehicle_id=str(vehicle_data["_id"]),
            registration_number=vehicle_data["registration_number"],
            status=vehicle_data["status"],
            user_id=user_id,
            data={
                **vehicle_data,
                "changes": changes or {}
            }
        )
        
        return await self.publish_event(event, "vehicle.updated")
    
    async def publish_vehicle_deleted(self, vehicle_data: Dict[str, Any], user_id: str = None) -> bool:
        """Publish vehicle deleted event"""
        from .events import VehicleEvent
        
        event = VehicleEvent(
            event_type=EventType.VEHICLE_DELETED,
            vehicle_id=str(vehicle_data["_id"]),
            registration_number=vehicle_data["registration_number"],
            status=vehicle_data["status"],
            user_id=user_id,
            data=vehicle_data
        )
        
        return await self.publish_event(event, "vehicle.deleted")
    
    async def publish_driver_created(self, driver_data: Dict[str, Any], user_id: str = None) -> bool:
        """Publish driver created event"""
        from .events import DriverEvent
        
        event = DriverEvent(
            event_type=EventType.DRIVER_CREATED,
            driver_id=str(driver_data["_id"]),
            employee_id=driver_data["employee_id"],
            status=driver_data["status"],
            user_id=user_id,
            data=driver_data
        )
        
        return await self.publish_event(event, "driver.created")
    
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
    
    

    async def publish_message(
        exchange_name: str,
        exchange_type: aio_pika.ExchangeType,
        message: dict,
        routing_key: str = ""
    ):
        """
        Publishes a message to a specified exchange.

        Args:
            exchange_name (str): The name of the exchange to publish to.
            exchange_type (aio_pika.ExchangeType): eg. aio_pika.ExchangeType.FANOUT
            message (dict): The message to publish.        routing_key (str): The routing key (ignored for fanout exchanges).
        """
        try:
            connection = await aio_pika.connect_robust(RabbitMQConfig.RABBITMQ_URL)
            channel = await connection.channel()

            # Try to declare exchange as durable first, fallback to using existing if conflict
            try:
                exchange = await channel.declare_exchange(exchange_name, exchange_type, durable=True)
            except Exception as e:
                if "inequivalent arg" in str(e) and "durable" in str(e):
                    # Exchange exists with different durability, use passive declaration
                    logger.warning(f"Exchange '{exchange_name}' exists with different durability, using existing exchange")
                    exchange = await channel.declare_exchange(exchange_name, exchange_type, passive=True)
                else:
                    raise

            await exchange.publish(
                aio_pika.Message(body=json.dumps(message).encode()),
                routing_key=routing_key
            )

            logger.info(f"Published message to {exchange_type} exchange '{exchange_name}': {message}")
        except Exception as e:
            logger.error(f"Failed to publish message to exchange '{exchange_name}': {str(e)}")

            raise
        finally:
            await connection.close()


# Global publisher instance
event_publisher = EventPublisher()
