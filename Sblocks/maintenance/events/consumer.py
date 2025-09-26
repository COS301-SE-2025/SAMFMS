"""
Event consumer for Maintenance service - simplified for removed_user fanout exchange
"""
import aio_pika
import asyncio
import json
import logging
from typing import Dict, Any, Callable, Optional
import os
import traceback

logger = logging.getLogger(__name__)


class EventConsumer:
    """Event consumer for RabbitMQ focused on removed_user fanout exchange"""
    
    def __init__(self):
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://samfms_rabbit:RabbitPass2025!@rabbitmq:5672/")
        self.handlers: Dict[str, Callable] = {}
        self.is_consuming = False
        logger.info("EventConsumer Initialized")
        
    async def connect(self):
        """Connect to RabbitMQ"""
        try:            
            self.connection = await aio_pika.connect_robust(
                self.rabbitmq_url,
                heartbeat=600,
                blocked_connection_timeout=300,
                connection_attempts=3,
                retry_delay=1.0
            )
            
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)

            logger.info("Successfully connected to RabbitMQ")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
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
    
    def register_handler(self, event_pattern: str, handler: Callable):
        """Register event handler"""
        self.handlers[event_pattern] = handler
        logger.info(f"Registered handler for {event_pattern}")
    
    async def start_consuming(self):
        """Start consuming events - only for removed_user fanout exchange"""
        if not self.connection:
            logger.error("Not connected to RabbitMQ")
            return
        
        if self.is_consuming:
            logger.warning("Already consuming events")
            return
        
        try:
            # Declare the fanout exchange
            fanout_exchange = await self.channel.declare_exchange(
                "removed_user",
                aio_pika.ExchangeType.FANOUT,
                durable=True
            )
            logger.info("Declared removed_user fanout exchange")

            # Declare a unique queue for this service instance
            # Using auto-delete and exclusive for fanout pattern
            queue = await self.channel.declare_queue(
                "gps_service_removed_user",  # Specific queue name for this service
                durable=True,
                auto_delete=False
            )
            logger.info(f"Declared queue: {queue.name}")

            # Bind queue to fanout exchange (no routing key needed for fanout)
            await queue.bind(fanout_exchange)
            logger.info("Bound queue to removed_user fanout exchange")

            # Start consuming
            self.is_consuming = True
            await queue.consume(self._handle_message)
            logger.info("Started consuming removed_user events")

            # Keep consuming
            while self.is_consuming:
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Error starting consumption: {e}")
            logger.error(traceback.format_exc())
            self.is_consuming = False

    async def _handle_message(self, message: aio_pika.IncomingMessage):
        """Handle incoming message"""
        async with message.process():
            try:
                body = json.loads(message.body.decode())
                exchange_name = message.exchange
                
                logger.info(f"Received message from exchange '{exchange_name}': {body}")
                
                # For fanout exchange, we know it's a removed_user event
                if "removed_user" in self.handlers:
                    try:
                        await self.handlers["removed_user"](body, "removed_user")
                        logger.info("Successfully processed removed_user event")
                    except Exception as e:
                        logger.error(f"Error in removed_user handler: {e}")
                        logger.error(traceback.format_exc())
                else:
                    logger.warning("No handler registered for removed_user events")
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse message as JSON: {e}")
                logger.error(f"Raw message: {message.body.decode()}")
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                logger.error(traceback.format_exc())


# Event handler for removed_user
async def handle_removed_user(data: Dict[str, Any], routing_key: str):
    """Handle removed user event"""
    try:
        logger.info(f"Processing removed_user event: {data}")
        
        assigned_to = data.get("assigned_to")
        driver_assignment = data.get("driver_assignment")
        
        if not assigned_to:
            logger.warning("No assigned_to provided in removed user event")
            return
            
        logger.info(f"Processing removal for assigned_to: {assigned_to}, driver_assignment: {driver_assignment}")
        from events.publisher import EventPublisher
        if data["penis"]:
            publisher = EventPublisher()
            publisher.publish_message("removed_user", aio_pika.ExchangeType.FANOUT, {"status": "processed"})

        # Add your business logic here
        # For example:
        # - Remove maintenance assignments
        # - Update vehicle assignments
        # - Clean up related records
        
        # If you need to republish, make sure EventPublisher.publish_message has 'self' parameter
        # from .publisher import EventPublisher
        # publisher = EventPublisher()
        # await publisher.publish_message("some_exchange", aio_pika.ExchangeType.FANOUT, {"status": "processed"})
        
        
        logger.info(f"Successfully processed removed user event for {assigned_to}")
        
    except Exception as e:
        logger.error(f"Error handling removed user event: {e}")
        logger.error(f"Event data: {data}")
        logger.error(traceback.format_exc())
        raise


async def setup_event_handlers():
    """Setup event handlers - only for removed_user"""
    try:
        event_consumer.register_handler("removed_user", handle_removed_user)
        logger.info("Event handlers registered successfully")
        return True
    except Exception as e:
        logger.error(f"Error setting up event handlers: {e}")
        return False


# Global event consumer instance
event_consumer = EventConsumer()