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
        # Use standardized config
        self.config = RabbitMQConfig()
        self.rabbitmq_url = self.config.get_rabbitmq_url()
        self.handlers: Dict[str, Callable] = {}
        self.dead_letter_queue: Optional[aio_pika.Queue] = None
        self.max_retry_attempts = 3
        self.retry_delay = 2.0  # seconds
        self.is_consuming = False
        self.enable_dead_letter_queue = os.getenv("ENABLE_DLQ", "true").lower() == "true"
        
    async def connect(self):
        """Connect to RabbitMQ with retry logic and better error handling"""
        max_retries = 5
        base_delay = 2.0
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to connect to RabbitMQ (attempt {attempt + 1}/{max_retries})")
                
                # Use standardized connection settings
                self.connection = await aio_pika.connect_robust(
                    self.rabbitmq_url,
                    heartbeat=self.config.CONNECTION_PARAMS["heartbeat"],
                    blocked_connection_timeout=self.config.CONNECTION_PARAMS["blocked_connection_timeout"],
                    connection_attempts=3,
                    retry_delay=1.0
                )
                
                # Create channel with better settings
                self.channel = await self.connection.channel(
                    publisher_confirms=True,
                    on_return_raises=False
                )
                
                # Set QoS with lower prefetch to reduce memory usage
                await self.channel.set_qos(prefetch_count=5)
                
                logger.info("Successfully connected to RabbitMQ")
                return True
                
            except Exception as e:
                logger.error(f"Failed to connect to RabbitMQ (attempt {attempt + 1}): {e}")
                
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logger.error("All RabbitMQ connection attempts failed")
                    raise ConnectionError("Unable to connect to RabbitMQ after multiple attempts")
    
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
            # Temporarily disable dead letter queue to avoid timeout issues
            logger.info("Dead letter queue disabled to avoid timeout issues")
            self.enable_dead_letter_queue = False
            
            # Try to declare queue with better error handling
            queue_name = "maintenance_service_events"
            queue = await self._declare_queue_with_fallback(queue_name)
            
            # Bind to relevant exchanges and routing keys
            await self._setup_bindings(queue)
            
            # Start consuming with proper error handling
            await queue.consume(self._handle_message_with_retry, no_ack=False)
            
            self.is_consuming = True
            logger.info("Started consuming events successfully")
            
        except Exception as e:
            logger.error(f"Failed to start consuming events: {e}")
            logger.error(f"Error traceback: {traceback.format_exc()}")
            self.is_consuming = False
            
            # Don't raise - allow service to continue without events
            logger.warning("Service will continue without event consumption")
            return
    
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
    
    async def _handle_message_with_retry(self, message: aio_pika.IncomingMessage):
        """Handle message with retry logic"""
        async with message.process(requeue=False):
            try:
                # Decode message
                body = json.loads(message.body.decode())
                event_type = message.headers.get("event_type", "unknown")
                
                logger.debug(f"Received event: {event_type}")
                
                # Find and execute handler
                handler = self._find_handler(event_type)
                if handler:
                    await handler(body)
                    logger.debug(f"Successfully processed event: {event_type}")
                else:
                    logger.warning(f"No handler found for event type: {event_type}")
                
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                logger.error(f"Message body: {message.body}")
                # Message will be rejected due to requeue=False
    
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

def setup_event_handlers():
    """Setup event handlers"""
    event_consumer.register_handler("vehicle.created", handle_vehicle_created)
    event_consumer.register_handler("vehicle.updated", handle_vehicle_updated)
    event_consumer.register_handler("user.created", handle_user_created)
    logger.info("Event handlers registered successfully")


# Global event consumer instance
event_consumer = EventConsumer()
