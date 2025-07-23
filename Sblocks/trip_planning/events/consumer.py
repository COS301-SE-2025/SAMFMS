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
        self.consumer_tags: List[str] = []
        
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
        try:
            await self.stop_consuming()
            
            if self.connection and not self.connection.is_closed:
                await self.connection.close()
            
            logger.info("Disconnected from RabbitMQ")
            
        except Exception as e:
            logger.error(f"Error disconnecting from RabbitMQ: {e}")
    
    async def register_handler(self, event_pattern: str, handler: Callable):
        """Register an event handler for a specific pattern"""
        self.handlers[event_pattern] = handler
        logger.info(f"Registered handler for pattern: {event_pattern}")
    
    async def start_consuming(self, event_patterns: List[str]):
        """Start consuming events for specified patterns"""
        try:
            if not self.connection:
                await self.connect()
            
            self.is_consuming = True
            
            for pattern in event_patterns:
                await self._create_consumer_for_pattern(pattern)
            
            logger.info(f"Started consuming events for patterns: {event_patterns}")
            
        except Exception as e:
            logger.error(f"Failed to start consuming: {e}")
            self.is_consuming = False
            raise
    
    async def stop_consuming(self):
        """Stop consuming events"""
        try:
            self.is_consuming = False
            
            # Cancel all consumers
            for tag in self.consumer_tags:
                try:
                    await self.channel.basic_cancel(tag)
                except Exception as e:
                    logger.warning(f"Error canceling consumer {tag}: {e}")
            
            self.consumer_tags.clear()
            logger.info("Stopped consuming events")
            
        except Exception as e:
            logger.error(f"Error stopping consumers: {e}")
    
    async def _setup_dead_letter_queue(self):
        """Setup dead letter queue for failed messages"""
        try:
            # Declare dead letter exchange
            dl_exchange = await self.channel.declare_exchange(
                "trip_planning_dlx",
                aio_pika.ExchangeType.DIRECT,
                durable=True
            )
            
            # Declare dead letter queue
            self.dead_letter_queue = await self.channel.declare_queue(
                "trip_planning_dlq",
                durable=True,
                arguments={
                    "x-message-ttl": 86400000,  # 24 hours
                }
            )
            
            await self.dead_letter_queue.bind(dl_exchange, "failed")
            
        except Exception as e:
            logger.error(f"Failed to setup dead letter queue: {e}")
    
    async def _create_consumer_for_pattern(self, pattern: str):
        """Create a consumer for a specific event pattern"""
        try:
            # Create queue name based on pattern
            queue_name = f"trip_planning_{pattern.replace('.', '_').replace('*', 'all')}"
            
            # Declare queue with dead letter exchange
            queue = await self.channel.declare_queue(
                queue_name,
                durable=True,
                arguments={
                    "x-dead-letter-exchange": "trip_planning_dlx",
                    "x-dead-letter-routing-key": "failed"
                }
            )
            
            # Bind queue to exchange based on pattern
            exchange_name = self._get_exchange_for_pattern(pattern)
            exchange = await self.channel.declare_exchange(
                exchange_name,
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )
            
            await queue.bind(exchange, pattern)
            
            # Start consuming
            consumer_tag = await queue.consume(
                self._create_message_handler(pattern),
                no_ack=False
            )
            
            self.consumer_tags.append(consumer_tag)
            
        except Exception as e:
            logger.error(f"Failed to create consumer for pattern {pattern}: {e}")
            raise
    
    def _get_exchange_for_pattern(self, pattern: str) -> str:
        """Get the appropriate exchange name for an event pattern"""
        if pattern.startswith("vehicle."):
            return "gps_events"
        elif pattern.startswith("driver."):
            return "user_events"  # Assuming driver events come from user service
        elif pattern.startswith("traffic."):
            return "traffic_events"
        else:
            return "trip_planning_events"
    
    def _create_message_handler(self, pattern: str):
        """Create a message handler for a specific pattern"""
        async def handle_message(message: aio_pika.IncomingMessage):
            async with message.process(requeue=False):
                try:
                    await self._process_message(message, pattern)
                    
                except Exception as e:
                    logger.error(f"Error processing message for pattern {pattern}: {e}")
                    
                    # Check retry count
                    retry_count = message.headers.get("x-retry-count", 0) if message.headers else 0
                    
                    if retry_count < self.max_retry_attempts:
                        # Retry message
                        await self._retry_message(message, pattern, retry_count + 1)
                    else:
                        # Send to dead letter queue
                        logger.error(f"Message exceeded max retries, sending to DLQ: {message.body}")
                        await self._send_to_dlq(message, str(e))
        
        return handle_message
    
    async def _process_message(self, message: aio_pika.IncomingMessage, pattern: str):
        """Process a message"""
        try:
            # Parse message body
            body = json.loads(message.body.decode())
            
            # Extract event type
            event_type = body.get("event_type") or message.headers.get("event_type")
            
            # Find appropriate handler
            handler = None
            
            # Try exact pattern match first
            if pattern in self.handlers:
                handler = self.handlers[pattern]
            else:
                # Try pattern matching
                for handler_pattern, handler_func in self.handlers.items():
                    if self._pattern_matches(event_type, handler_pattern):
                        handler = handler_func
                        break
            
            if handler:
                await handler(body)
                logger.debug(f"Processed event {event_type} with pattern {pattern}")
            else:
                logger.warning(f"No handler found for event {event_type} with pattern {pattern}")
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            logger.error(f"Message body: {message.body}")
            raise
    
    def _pattern_matches(self, event_type: str, pattern: str) -> bool:
        """Check if event type matches pattern"""
        if pattern == "*":
            return True
        
        if "*" not in pattern:
            return event_type == pattern
        
        # Simple wildcard matching
        pattern_parts = pattern.split(".")
        event_parts = event_type.split(".")
        
        if len(pattern_parts) != len(event_parts):
            return False
        
        for pattern_part, event_part in zip(pattern_parts, event_parts):
            if pattern_part != "*" and pattern_part != event_part:
                return False
        
        return True
    
    async def _retry_message(self, message: aio_pika.IncomingMessage, pattern: str, retry_count: int):
        """Retry a failed message"""
        try:
            # Wait before retry
            await asyncio.sleep(self.retry_delay * retry_count)
            
            # Create new message with updated retry count
            new_headers = dict(message.headers) if message.headers else {}
            new_headers["x-retry-count"] = retry_count
            
            retry_message = aio_pika.Message(
                message.body,
                headers=new_headers,
                content_type=message.content_type
            )
            
            # Republish to the same exchange
            exchange_name = self._get_exchange_for_pattern(pattern)
            exchange = await self.channel.declare_exchange(
                exchange_name,
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )
            
            await exchange.publish(retry_message, routing_key=pattern)
            
            logger.info(f"Retried message (attempt {retry_count}) for pattern {pattern}")
            
        except Exception as e:
            logger.error(f"Failed to retry message: {e}")
    
    async def _send_to_dlq(self, message: aio_pika.IncomingMessage, error: str):
        """Send message to dead letter queue"""
        try:
            if self.dead_letter_queue:
                dl_headers = dict(message.headers) if message.headers else {}
                dl_headers["x-original-error"] = error
                dl_headers["x-failed-at"] = datetime.utcnow().isoformat()
                
                dl_message = aio_pika.Message(
                    message.body,
                    headers=dl_headers,
                    content_type=message.content_type
                )
                
                await self.dead_letter_queue.channel.default_exchange.publish(
                    dl_message,
                    routing_key=self.dead_letter_queue.name
                )
                
                logger.info("Sent message to dead letter queue")
            
        except Exception as e:
            logger.error(f"Failed to send message to DLQ: {e}")


# Event handlers
async def handle_vehicle_location_updated(event_data: Dict[str, Any]):
    """Handle vehicle location updated events"""
    try:
        vehicle_id = event_data.get("vehicle_id")
        location = event_data.get("location")
        
        if vehicle_id and location:
            # Update trip progress if vehicle is on a trip
            from services.trip_service import trip_service
            # Implementation would check for active trips with this vehicle
            logger.info(f"Vehicle {vehicle_id} location updated")
        
    except Exception as e:
        logger.error(f"Error handling vehicle location update: {e}")


async def handle_driver_availability_changed(event_data: Dict[str, Any]):
    """Handle driver availability changed events"""
    try:
        driver_id = event_data.get("driver_id")
        is_available = event_data.get("is_available")
        
        if driver_id is not None:
            # Check if this affects any scheduled trips
            from services.driver_service import driver_service
            # Implementation would validate current assignments
            logger.info(f"Driver {driver_id} availability changed to {is_available}")
        
    except Exception as e:
        logger.error(f"Error handling driver availability change: {e}")


async def handle_traffic_update(event_data: Dict[str, Any]):
    """Handle traffic update events"""
    try:
        affected_area = event_data.get("area")
        severity = event_data.get("severity")
        
        if affected_area and severity:
            # Check if this affects any active trips
            from services.notification_service import notification_service
            # Implementation would notify affected trips
            logger.info(f"Traffic update in area {affected_area} with severity {severity}")
        
    except Exception as e:
        logger.error(f"Error handling traffic update: {e}")


def setup_event_handlers(consumer: EventConsumer):
    """Setup event handlers for the consumer"""
    asyncio.create_task(consumer.register_handler("vehicle.location_updated", handle_vehicle_location_updated))
    asyncio.create_task(consumer.register_handler("driver.availability_changed", handle_driver_availability_changed))
    asyncio.create_task(consumer.register_handler("traffic.update", handle_traffic_update))


# Global event consumer instance
event_consumer = EventConsumer()
