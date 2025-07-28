"""
Event consumer for Trip Planning service
"""
import aio_pika
import asyncio
import json
import logging
from typing import Dict, Any, Callable, Optional, List
import os
from datetime import datetime
import traceback

logger = logging.getLogger(__name__)


class EventConsumer:
    """Event consumer for RabbitMQ"""
    
    def __init__(self):
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.rabbitmq_url = os.getenv(
            "RABBITMQ_URL", 
            "amqp://samfms_rabbit:RabbitPass2025!@rabbitmq:5672/"
        )
        self.handlers: Dict[str, Callable] = {}
        self.dead_letter_queue: Optional[aio_pika.Queue] = None
        self.max_retry_attempts = 3
        self.retry_delay = 2.0
        self.is_consuming = False
        
    async def connect(self):
        """Connect to RabbitMQ"""
        try:
            self.connection = await aio_pika.connect_robust(
                self.rabbitmq_url,
                heartbeat=600,
                blocked_connection_timeout=300,
                connection_attempts=3,
                retry_delay=2.0
            )
            
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)
            
            # Setup dead letter queue
            await self._setup_dead_letter_queue()
            
            logger.info("Connected to RabbitMQ for event consumption")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from RabbitMQ"""
        self.is_consuming = False

        try:
            if self.channel and not self.channel.is_closed:
                await self.channel.close()
            
            if self.connection and not self.connection.is_closed:
                await self.connection.close()
                logger.info("Disconnected from RabbitMQ consumer")
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
        finally:
            self.connection = None
            self.channel = None
    
    def is_connected(self) -> bool:
        """Check if connected to RabbitMQ"""
        return (self.connection is not None and 
                not self.connection.is_closed and 
                self.channel is not None)
    
    async def register_handler(self, event_pattern: str, handler: Callable):
        """Register event handler"""
        self.handlers[event_pattern] = handler
        logger.info(f"Registered handler for {event_pattern}")
    
    async def start_consuming(self):
        """Start consuming events"""
        if not self.connection:
            logger.error("Not connected to RabbitMQ");
            return
            
        if self.is_consuming:
            logger.warning("Already consuming events")
            return
            
        try:
            # Declare exchange
            exchange = await self.channel.declare_exchange(
                "trips_events",
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )

            # Declare queue for this service
            queue = await self.channel.declare_queue(
                "trips_service_events",
                durable=True
            )

            # Bind queue to exchange for relevant patterns
            patterns = [
                "core.*",
                "management.*",
                "gps.*"
            ]

            for pattern in patterns:
                await queue.bind(exchange, routing_key=pattern)
                
            # Start consuming
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

async def handle_management_event(event_data: Dict[str, Any], routing_key: str):
    """Handle management-related events"""
    logger.info(f"Handling management event: {routing_key}")
    # Process management events

async def handle_gps_event(event_data: Dict[str, Any], routing_key: str):
    """Handle gps-related events"""
    logger.info(f"Handling gps event: {routing_key}")
    # Process user events that might affect places or permissions

async def setup_event_handlers():
    """Setup event handlers"""
    event_consumer.register_handler("management.*", handle_management_event)
    event_consumer.register_handler("gps.*", handle_gps_event)
    
# Global event consumer instance
event_consumer = EventConsumer()
