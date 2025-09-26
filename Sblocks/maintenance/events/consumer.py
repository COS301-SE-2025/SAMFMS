"""
Event consumer for Maintenance service with enhanced reliability and error handling
"""
import aio_pika
import asyncio
import json
import logging
from typing import Dict, Any, Callable, Optional
import os
from datetime import datetime, timedelta
import traceback

from .events import MaintenanceEvent, LicenseEvent
# Import standardized config
from config.rabbitmq_config import RabbitMQConfig

logger = logging.getLogger(__name__)


class EventConsumer:
    """Event consumer for RabbitMQ with enhanced reliability"""
    
    def __init__(self):
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://samfms_rabbit:RabbitPass2025!@rabbitmq:5672/")
        self.handlers: Dict[str, Callable] = {}
        self.dead_letter_queue: Optional[aio_pika.Queue] = None
        self.max_retry_attempts = 3
        self.retry_delay = 2.0  # seconds
        self.is_consuming = False
        self.queue = None
        
    async def connect(self):
        """Connect to RabbitMQ"""
        attempt = 0
        try:            
            # Use standardized connection settings
            self.connection = await aio_pika.connect_robust(
                self.rabbitmq_url,
                heartbeat=600,
                blocked_connection_timeout=300,
                connection_attempts=3,
                retry_delay=1.0
            )
            
            # Create channel with better settings
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)
            
            logger.info("Successfully connected to RabbitMQ")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ (attempt {attempt + 1}): {e}")
            return False
        
    async def disconnect(self):
        """Disconnect from RabbitMQ with proper cleanup"""
        self.is_consuming = False
        
        try:
            if self.channel and not self.channel.is_closed:
                await self.channel.close()
                logger.info("Closed RabbitMQ channel")
                
            if self.connection and not self.connection.is_closed:
                await self.connection.close()
                logger.info("Disconnected from RabbitMQ consumer")
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
        finally:
            self.connection = None
            self.channel = None
            self.dead_letter_queue = None
    
    def register_handler(self, event_pattern: str, handler: Callable):
        """Register event handler"""
        self.handlers[event_pattern] = handler
        logger.info(f"Registered handler for {event_pattern}")
    
    async def start_consuming(self):
        """Start consuming events with improved error handling"""
        if not self.connection:
            logger.error("Not connected to RabbitMQ")
            return
        
        if self.is_consuming:
            logger.warning("Already consuming events")
            return
        
        try:
            # Declare exchange
            exchange = await self.channel.declare_exchange(
                "maintenance_events",
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )
            # Declare queue for this service
            queue = await self.channel.declare_queue(
                "gps_service_events",
                durable=True
            )
            patterns = [
                "management.*",  # Listen to management events
                "core.*",        # Listen to core events
                "vehicles.*",    # Listen to vehicle events
                "users.*"        # Listen to user events
            ]

            for pattern in patterns:
                await queue.bind(exchange, routing_key=pattern)


            removed_user_exchange = await self.channel.declare_exchange(
                "removed_user",
                aio_pika.ExchangeType.FANOUT,
                durable=True
            )

            await queue.bind(removed_user_exchange, "")

            self.is_consuming = True
            await queue.consume(self._handle_message)

            logger.info("Started consuming events")

            # Keep consuming
            while self.is_consuming:
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Error starting consumption: {e}")
            self.is_consuming = False

    async def _handle_message(self, message: aio_pika.IncomingMessage):
        """Handle incoming message"""
        async with message.process():
            try:
                # Parse message
                body = json.loads(message.body.decode())
                routing_key = message.routing_key
                
                if routing_key == "":
                    routing_key = "removed_user"

                logger.info(f"Received event with routing key: {routing_key}")
                
                # Find matching handler
                for pattern, handler in self.handlers.items():
                    if self._match_pattern(routing_key, pattern):
                        try:
                            await handler(body, routing_key)
                        except Exception as e:
                            logger.error(f"Error in handler for {pattern}: {e}")
                            logger.error(traceback.format_exc())
                
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                logger.error(traceback.format_exc())

    def _match_pattern(self, routing_key: str, pattern: str) -> bool:
        """Check if routing key matches pattern"""
        # Simple pattern matching (can be enhanced)
        if "*" in pattern:
            prefix = pattern.replace("*", "")
            return routing_key.startswith(prefix)
        return routing_key == pattern
    


    async def _declare_queue_with_fallback(self, queue_name: str) -> aio_pika.Queue:
        """Declare queue with fallback to simple queue if DLQ fails"""
        try:
            if self.enable_dead_letter_queue:
                # Try with dead letter queue first
                return await self.channel.declare_queue(
                    queue_name,
                    durable=True,
                    arguments={
                        "x-dead-letter-exchange": f"{queue_name}.dlx",
                        "x-dead-letter-routing-key": "failed",
                        "x-message-ttl": 3600000  # 1 hour TTL
                    }
                )
            else:
                # Simple queue without DLQ
                return await self.channel.declare_queue(queue_name, durable=True)
                
        except Exception as e:
            logger.warning(f"Failed to declare queue with DLQ, falling back to simple queue: {e}")
            # Fallback to simple queue
            return await self.channel.declare_queue(queue_name, durable=True)
    
    async def _setup_bindings(self, queue: aio_pika.Queue):
        """Setup queue bindings to exchanges"""
        # Bind to vehicle events from Management service (for maintenance scheduling)
        try:
            management_exchange = await self.channel.declare_exchange(
                "management_events",
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )
            await queue.bind(management_exchange, routing_key="vehicle.*")
            logger.info("Bound to management vehicle events")
        except Exception as e:
            logger.warning(f"Failed to bind to management events: {e}")
        
        # Bind to user events from Security service
        try:
            security_exchange = await self.channel.declare_exchange(
                "security_events",
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )
            await queue.bind(security_exchange, routing_key="user.*")
            logger.info("Bound to security user events")
        except Exception as e:
            logger.warning(f"Failed to bind to security events: {e}")



    def _find_handler(self, event_type: str) -> Optional[Callable]:
        """Find handler for event type"""
        # Direct match first
        if event_type in self.handlers:
            return self.handlers[event_type]
        
        # Pattern matching
        for pattern, handler in self.handlers.items():
            if self._matches_pattern(event_type, pattern):
                return handler
        
        return None
    
    def _matches_pattern(self, event_type: str, pattern: str) -> bool:
        """Simple pattern matching for event types"""
        if "*" not in pattern:
            return event_type == pattern
        
        # Simple wildcard matching
        pattern_parts = pattern.split("*")
        if len(pattern_parts) == 2:
            prefix, suffix = pattern_parts
            return event_type.startswith(prefix) and event_type.endswith(suffix)
        
        return False


# Event handlers
event_handlers = {}

async def handle_vehicle_created(event_data: Dict[str, Any]):
    """Handle vehicle created event"""
    logger.info(f"Vehicle created: {event_data.get('vehicle_id')}")
    # TODO: Create maintenance schedule for new vehicle

async def handle_vehicle_updated(event_data: Dict[str, Any]):
    """Handle vehicle updated event"""
    logger.info(f"Vehicle updated: {event_data.get('vehicle_id')}")
    # TODO: Update maintenance schedules if needed

async def handle_user_created(event_data: Dict[str, Any]):
    """Handle user created event"""
    logger.info(f"User created: {event_data.get('user_id')}")
    # TODO: Setup maintenance notifications for new user


async def handle_removed_user(data: Dict[str, Any], routing_key: str):
        try: 
            assigned_to = data["assigned_to"]
            logger.info(f"Processing removed user event for: {assigned_to}")
            return
            if not assigned_to:
                logger.warning("No security_id provided in removed user event")
                return
            driver_service = DriverService()
            vehicle_assignment_service = VehicleAssignmentService()
            driver = await driver_service.get_driver_id_by_email(email)

            if not driver:
                logger.warning(f"Driver not found for email: {email}")
                return

            ID = driver["_id"]
            EMPID = driver["employee_id"] #for trips driver_assignment is equivalent to employee_id
            security_id = driver["security_id"] #for maintenance_records assigned_to is equivalent to security_id
            await driver_service.delete_driver(ID)
            await vehicle_assignment_service.cancel_driver_assignments(EMPID)
            publisher = EventPublisher()
            message = ({
                    "driver_assignment": EMPID,
                    "assigned_to": security_id,
                })
            await publisher.publish_message(
                            exchange_name="removed_user",
                            exchange_type=aio_pika.ExchangeType.FANOUT,
                            message=message
                        )
            
            
            logger.info(f"Successfully processed removed user event: {email}")
        except Exception as e:
            logger.error(f"Error handling removed user event: {e}")
            logger.error(f"Event data: {data}")
            raise



async def setup_event_handlers():
    """Setup event handlers"""
    event_consumer.register_handler("vehicle.created", handle_vehicle_created)
    event_consumer.register_handler("vehicle.updated", handle_vehicle_updated)
    event_consumer.register_handler("user.created", handle_user_created)
    event_consumer.register_handler("removed_user", handle_removed_user)
    logger.info("Event handlers registered successfully")


# Global event consumer instance
event_consumer = EventConsumer()
