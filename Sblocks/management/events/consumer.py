"""
Event consumer for Management service with enhanced reliability and error handling
"""
import aio_pika
import asyncio
import json
import logging
from typing import Dict, Any, Callable, Optional
import os
from datetime import datetime, timedelta
import traceback

from .events import VehicleEvent, UserEvent
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
                return
                
            except Exception as e:
                logger.error(f"Failed to connect to RabbitMQ (attempt {attempt + 1}): {e}")
                
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logger.error("All RabbitMQ connection attempts failed")
                    raise ConnectionError("Unable to connect to RabbitMQ after multiple attempts")
                
                logger.info("Connected to RabbitMQ for event consumption")
                return True
                
            except Exception as e:
                logger.error(f"Failed to connect to RabbitMQ (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
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
            # Temporarily disable dead letter queue to avoid timeout issues
            logger.info("Dead letter queue disabled to avoid timeout issues")
            self.enable_dead_letter_queue = False
            
            # Try to declare queue with better error handling
            queue_name = "management_service_events"
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
    
    async def _setup_bindings(self, queue: aio_pika.Queue):
        """Setup queue bindings to exchanges"""
        # Bind to vehicle events from Vehicles service
        vehicles_exchange = await self.channel.declare_exchange(
            "vehicle_events",
            aio_pika.ExchangeType.TOPIC,
            durable=True
        )
        
        await queue.bind(vehicles_exchange, "vehicle.created")
        await queue.bind(vehicles_exchange, "vehicle.updated")
        await queue.bind(vehicles_exchange, "vehicle.deleted")
        await queue.bind(vehicles_exchange, "vehicle.status_changed")
        await queue.bind()
        
        # Bind to user events from Security service
        security_exchange = await self.channel.declare_exchange(
            "security_events",
            aio_pika.ExchangeType.TOPIC,
            durable=True
        )
        
        await queue.bind(security_exchange, "user.created")
        await queue.bind(security_exchange, "user.updated")
        await queue.bind(security_exchange, "user.role_changed")
        
        logger.info("Setup event bindings")
    
    async def _setup_dead_letter_queue(self):
        """Setup dead letter queue for failed messages with error handling"""
        try:
            # Declare dead letter exchange
            dlx = await self.channel.declare_exchange(
                "management_dlx",
                aio_pika.ExchangeType.DIRECT,
                durable=True
            )
            
            # Declare dead letter queue
            self.dead_letter_queue = await self.channel.declare_queue(
                "management_dlq",
                durable=True
            )
            
            # Bind DLQ to DLX
            await self.dead_letter_queue.bind(dlx, "failed")
            
            logger.info("Setup dead letter queue successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup dead letter queue: {e}")
            logger.warning("Continuing without dead letter queue - failed messages will be logged only")
            self.dead_letter_queue = None
    
    async def _handle_message_with_retry(self, message: aio_pika.IncomingMessage):
        """Handle incoming message with retry logic"""
        retry_count = message.headers.get("x-retry-count", 0) if message.headers else 0
        
        async with message.process(requeue=False):
            try:
                await self._handle_message(message)
                
            except Exception as e:
                logger.error(f"Error handling message (attempt {retry_count + 1}): {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                
                # Retry logic
                if retry_count < self.max_retry_attempts:
                    await self._retry_message(message, retry_count + 1, str(e))
                else:
                    await self._send_to_dead_letter_queue(message, str(e))
                
                # Re-raise to nack the message
                raise
    
    async def _retry_message(self, message: aio_pika.IncomingMessage, retry_count: int, error: str):
        """Retry a failed message"""
        try:
            # Calculate delay with exponential backoff
            delay = self.retry_delay * (2 ** (retry_count - 1))
            
            # Create new message with retry headers
            new_headers = dict(message.headers) if message.headers else {}
            new_headers.update({
                "x-retry-count": retry_count,
                "x-original-error": error,
                "x-retry-timestamp": datetime.utcnow().isoformat()
            })
            
            # Schedule retry after delay
            await asyncio.sleep(delay)
            
            # Re-publish message to original queue
            await self.channel.default_exchange.publish(
                aio_pika.Message(
                    message.body,
                    headers=new_headers,
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key="management_service_events"
            )
            
            logger.info(f"Scheduled retry {retry_count} for message after {delay}s delay")
            
        except Exception as e:
            logger.error(f"Failed to retry message: {e}")
    
    async def _send_to_dead_letter_queue(self, message: aio_pika.IncomingMessage, error: str):
        """Send failed message to dead letter queue or log if DLQ unavailable"""
        try:
            if not self.dead_letter_queue:
                logger.error(f"Dead letter queue not available, logging failed message: {error}")
                logger.error(f"Failed message body: {message.body[:500]}...")  # Log first 500 chars
                logger.error(f"Failed message routing key: {message.routing_key}")
                return
            
            # Create DLQ message with failure information
            dlq_headers = dict(message.headers) if message.headers else {}
            dlq_headers.update({
                "x-failed-timestamp": datetime.utcnow().isoformat(),
                "x-failure-reason": error,
                "x-original-routing-key": message.routing_key,
                "x-max-retries-exceeded": True
            })
            
            dlq_message = aio_pika.Message(
                message.body,
                headers=dlq_headers,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )
            
            # Try to publish to dead letter exchange
            try:
                dlx = await self.channel.get_exchange("management_dlx")
                await dlx.publish(dlq_message, routing_key="failed")
                logger.error(f"Sent message to dead letter queue: {error}")
            except Exception as dlx_error:
                logger.error(f"Failed to publish to dead letter exchange: {dlx_error}")
                # Fallback to logging
                logger.error(f"Failed message (DLX failed): {error}")
                logger.error(f"Message body: {message.body[:500]}")
            
        except Exception as e:
            logger.error(f"Critical error in dead letter queue handling: {e}")
            # Final fallback - just log the failure
            logger.error(f"Failed message (DLQ error): {error}")
            logger.error(f"Message routing key: {message.routing_key}")
            logger.error(f"Message body: {message.body[:500]}")
    
    async def _handle_message(self, message: aio_pika.IncomingMessage):
        """Handle incoming message with enhanced error context"""
        try:
            # Parse message
            body = json.loads(message.body.decode())
            routing_key = message.routing_key
            event_type = message.headers.get("event_type", routing_key) if message.headers else routing_key
            
            logger.info(f"Processing event: {event_type} (routing_key: {routing_key})")
            
            # Validate message structure
            if not isinstance(body, dict):
                raise ValueError(f"Invalid message body format: expected dict, got {type(body)}")
            
            # Find and execute handler
            handler = self._find_handler(routing_key)
            if handler:
                # Add request context for better tracing
                start_time = datetime.utcnow()
                await handler(body, routing_key, message.headers or {})
                duration = (datetime.utcnow() - start_time).total_seconds()
                
                logger.info(f"Successfully processed event {event_type} in {duration:.3f}s")
            else:
                logger.warning(f"No handler found for event: {routing_key}")
                # Don't raise error for missing handlers - just log and ack
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode message JSON: {e}")
            logger.error(f"Raw message body: {message.body}")
            raise ValueError(f"Invalid JSON in message: {e}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            raise
    
    def _find_handler(self, routing_key: str) -> Callable:
        """Find handler for routing key"""
        # Exact match first
        if routing_key in self.handlers:
            return self.handlers[routing_key]
        
        # Pattern matching
        for pattern, handler in self.handlers.items():
            if self._pattern_match(pattern, routing_key):
                return handler
        
        return None
    
    def _pattern_match(self, pattern: str, routing_key: str) -> bool:
        """Simple pattern matching for routing keys"""
        pattern_parts = pattern.split(".")
        key_parts = routing_key.split(".")
        
        if len(pattern_parts) != len(key_parts):
            return False
        
        for pattern_part, key_part in zip(pattern_parts, key_parts):
            if pattern_part != "*" and pattern_part != key_part:
                return False
        
        return True
    
    async def _declare_queue_with_fallback(self, queue_name: str):
        """Declare queue with graceful fallback for existing queues"""
        
        # First, try to connect to existing queue without modification
        try:
            queue = await self.channel.declare_queue(queue_name, passive=True)
            logger.info(f"Connected to existing queue {queue_name}")
            return queue
        except Exception:
            # Queue doesn't exist or we can't access it passively, try to declare it
            pass
        
        # Define simplified queue arguments to avoid timeout issues
        if self.enable_dead_letter_queue and self.dead_letter_queue:
            queue_args = {
                "x-message-ttl": 300000,  # 5 minutes TTL
                "x-dead-letter-exchange": "management_dlx",
                "x-dead-letter-routing-key": "failed"
            }
            logger.info("Attempting to declare queue with dead letter exchange")
        else:
            queue_args = {
                "x-message-ttl": 300000  # Only TTL to minimize conflicts
            }
            logger.info("Attempting to declare queue with minimal arguments")
        
        # Try to declare queue with desired arguments
        try:
            # Use a timeout for the queue declaration
            queue = await asyncio.wait_for(
                self.channel.declare_queue(
                    queue_name,
                    durable=True,
                    arguments=queue_args
                ),
                timeout=10.0  # 10 second timeout
            )
            logger.info(f"Successfully declared queue {queue_name}")
            return queue
            
        except Exception as e:
            if "PRECONDITION_FAILED" in str(e) and "inequivalent arg" in str(e):
                logger.warning(f"Queue {queue_name} exists with different arguments: {e}")
                
                # Recreate channel if it was closed
                if "Channel closed" in str(e) or "ChannelInvalidStateError" in str(e) or "RPC timeout" in str(e):
                    logger.info("Recreating channel after precondition failure")
                    await self._recreate_channel()
                
                # Simply connect to the existing queue as-is
                try:
                    queue = await asyncio.wait_for(
                        self.channel.declare_queue(queue_name, passive=True),
                        timeout=10.0
                    )
                    logger.info(f"Connected to existing queue {queue_name} with its current configuration")
                    return queue
                except Exception as passive_error:
                    logger.error(f"Failed to connect to existing queue: {passive_error}")
                    
                    # Final attempt: just declare without arguments and let RabbitMQ handle it
                    try:
                        queue = await asyncio.wait_for(
                            self.channel.declare_queue(queue_name, durable=True),
                            timeout=10.0
                        )
                        logger.info(f"Connected to queue {queue_name} with default declaration")
                        return queue
                    except Exception as final_error:
                        logger.error(f"All attempts to access queue {queue_name} failed: {final_error}")
                        logger.error("Recommendation: Delete and recreate the queue 'management_service_events' in RabbitMQ")
                        raise
            else:
                logger.error(f"Unexpected error declaring queue {queue_name}: {e}")
                raise
    
    async def _recreate_channel(self):
        """Recreate the channel after it's been closed"""
        try:
            if self.channel and not self.channel.is_closed:
                await self.channel.close()
            
            # Create new channel with better settings
            self.channel = await self.connection.channel(
                publisher_confirms=True,
                on_return_raises=False
            )
            await self.channel.set_qos(prefetch_count=5)
            logger.info("Successfully recreated RabbitMQ channel")
            
        except Exception as e:
            logger.error(f"Failed to recreate channel: {e}")
            raise


# Event handlers
class ManagementEventHandlers:
    """Event handlers for Management service with enhanced error handling"""
    
    def __init__(self):
        # Lazy import to avoid circular dependencies
        self.analytics_service = None
        self.assignment_repo = None
        self.driver_repo = None
    
    def _get_analytics_service(self):
        """Lazy load analytics service to avoid circular imports"""
        if self.analytics_service is None:
            try:
                from ..services.analytics_service import analytics_service
                self.analytics_service = analytics_service
            except ImportError as e:
                logger.error(f"Failed to import analytics service: {e}")
        return self.analytics_service
    
    def _get_assignment_repo(self):
        """Lazy load assignment repository"""
        if self.assignment_repo is None:
            try:
                from ..repositories.repositories import VehicleAssignmentRepository
                self.assignment_repo = VehicleAssignmentRepository()
            except ImportError as e:
                logger.error(f"Failed to import VehicleAssignmentRepository: {e}")
        return self.assignment_repo
    
    def _get_driver_repo(self):
        """Lazy load driver repository"""
        if self.driver_repo is None:
            try:
                from ..repositories.repositories import DriverRepository
                self.driver_repo = DriverRepository()
            except ImportError as e:
                logger.error(f"Failed to import DriverRepository: {e}")
        return self.driver_repo
    
    async def _safe_refresh_analytics(self, reason: str):
        """Safely refresh analytics cache with error handling"""
        try:
            analytics_service = self._get_analytics_service()
            if analytics_service:
                asyncio.create_task(analytics_service.refresh_all_cache())
                logger.info(f"Triggered analytics refresh: {reason}")
        except Exception as e:
            logger.error(f"Failed to refresh analytics ({reason}): {e}")
    
    async def handle_vehicle_created(self, data: Dict[str, Any], routing_key: str, headers: Dict[str, Any]):
        """Handle vehicle created event with validation"""
        try:
            vehicle_id = data.get('vehicle_id')
            if not vehicle_id:
                raise ValueError("Missing vehicle_id in event data")
            
            logger.info(f"Processing vehicle created event: {vehicle_id}")
            
            # Validate required fields
            required_fields = ['vehicle_id', 'status']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                logger.warning(f"Missing fields in vehicle created event: {missing_fields}")
            
            # Refresh analytics cache since fleet composition changed
            await self._safe_refresh_analytics(f"vehicle created: {vehicle_id}")
            
            logger.info(f"Successfully processed vehicle created event: {vehicle_id}")
            
        except Exception as e:
            logger.error(f"Error handling vehicle created event: {e}")
            logger.error(f"Event data: {data}")
            raise
    
    async def handle_vehicle_updated(self, data: Dict[str, Any], routing_key: str, headers: Dict[str, Any]):
        """Handle vehicle updated event with enhanced processing"""
        try:
            vehicle_id = data.get('vehicle_id')
            if not vehicle_id:
                raise ValueError("Missing vehicle_id in event data")
            
            logger.info(f"Processing vehicle updated event: {vehicle_id}")
            
            # Check if status changed - might affect analytics
            changes = data.get("changes", {})
            if "status" in changes:
                old_status = changes["status"].get("old")
                new_status = changes["status"].get("new")
                logger.info(f"Vehicle {vehicle_id} status changed: {old_status} -> {new_status}")
                
                await self._safe_refresh_analytics(f"vehicle status changed: {vehicle_id}")
            
            # Handle other significant changes
            significant_changes = ["department", "type", "capacity"]
            if any(field in changes for field in significant_changes):
                await self._safe_refresh_analytics(f"vehicle configuration changed: {vehicle_id}")
            
            logger.info(f"Successfully processed vehicle updated event: {vehicle_id}")
            
        except Exception as e:
            logger.error(f"Error handling vehicle updated event: {e}")
            logger.error(f"Event data: {data}")
            raise
    
    async def handle_vehicle_deleted(self, data: Dict[str, Any], routing_key: str, headers: Dict[str, Any]):
        """Handle vehicle deleted event with comprehensive cleanup"""
        try:
            vehicle_id = data.get('vehicle_id')
            if not vehicle_id:
                raise ValueError("Missing vehicle_id in event data")
            
            logger.info(f"Processing vehicle deleted event: {vehicle_id}")
            
            # Clean up assignments for deleted vehicle
            assignment_repo = self._get_assignment_repo()
            if assignment_repo:
                try:
                    # Cancel active assignments
                    updated_count = await assignment_repo.update_many(
                        {"vehicle_id": vehicle_id, "status": "active"},
                        {
                            "status": "cancelled", 
                            "notes": "Vehicle deleted",
                            "cancelled_at": datetime.utcnow(),
                            "cancelled_reason": "vehicle_deleted"
                        }
                    )
                    
                    if updated_count > 0:
                        logger.info(f"Cancelled {updated_count} active assignments for deleted vehicle {vehicle_id}")
                    
                except Exception as e:
                    logger.error(f"Failed to cancel assignments for vehicle {vehicle_id}: {e}")
                    # Don't raise - continue with other cleanup
            
            # Refresh analytics
            await self._safe_refresh_analytics(f"vehicle deleted: {vehicle_id}")
            
            logger.info(f"Successfully processed vehicle deleted event: {vehicle_id}")
            
        except Exception as e:
            logger.error(f"Error handling vehicle deleted event: {e}")
            logger.error(f"Event data: {data}")
            raise
    
    async def handle_user_created(self, data: Dict[str, Any], routing_key: str, headers: Dict[str, Any]):
        """Handle user created event with driver integration"""
        try:
            user_id = data.get('user_id')
            if not user_id:
                raise ValueError("Missing user_id in event data")
            
            logger.info(f"Processing user created event: {user_id}")
            
            # Validate user data
            required_fields = ['user_id', 'email']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                logger.warning(f"Missing fields in user created event: {missing_fields}")
            
            # If user has driver role, we might need to create driver record
            user_role = data.get("role")
            if user_role == "driver":
                from ..repositories.repositories import DriverCountRepository
                DriverCountRepository.add_driver()
                logger.info(f"New driver user created: {user_id}")
                
                # TODO: Consider auto-creating driver record based on user data
                # This would require additional validation and business logic
                
                # For now, just log for manual follow-up
                logger.info(f"Driver user {user_id} may need driver record creation")
            
            logger.info(f"Successfully processed user created event: {user_id}")
            
        except Exception as e:
            logger.error(f"Error handling user created event: {e}")
            logger.error(f"Event data: {data}")
            raise
    
    async def handle_user_role_changed(self, data: Dict[str, Any], routing_key: str, headers: Dict[str, Any]):
        """Handle user role changed event with driver status management"""
        try:
            user_id = data.get('user_id')
            old_role = data.get('old_role')
            new_role = data.get('new_role')
            
            if not user_id:
                raise ValueError("Missing user_id in event data")
            
            logger.info(f"Processing user role change: {user_id} from {old_role} to {new_role}")
            
            # Update driver status if role changed to/from driver
            if old_role == "driver" and new_role != "driver":
                # User is no longer a driver - deactivate driver record
                driver_repo = self._get_driver_repo()
                if driver_repo:
                    try:
                        driver = await driver_repo.find_one({"user_id": user_id})
                        if driver:
                            await driver_repo.update(
                                driver["_id"], 
                                {
                                    "status": "inactive",
                                    "deactivated_at": datetime.utcnow(),
                                    "deactivation_reason": "role_changed"
                                }
                            )
                            logger.info(f"Deactivated driver record for user {user_id}")
                        else:
                            logger.warning(f"No driver record found for user {user_id}")
                    except Exception as e:
                        logger.error(f"Failed to deactivate driver record for user {user_id}: {e}")
                        # Don't raise - this is a side effect operation
            
            elif old_role != "driver" and new_role == "driver":
                # User became a driver - log for potential driver record creation
                logger.info(f"User {user_id} became a driver - may need driver record creation")
            
            logger.info(f"Successfully processed user role change event: {user_id}")
            
        except Exception as e:
            logger.error(f"Error handling user role changed event: {e}")
            logger.error(f"Event data: {data}")
            raise


# Global consumer instance
event_consumer = EventConsumer()
event_handlers = ManagementEventHandlers()


async def setup_event_handlers():
    """Setup event handlers"""
    event_consumer.register_handler("vehicle.created", event_handlers.handle_vehicle_created)
    event_consumer.register_handler("vehicle.updated", event_handlers.handle_vehicle_updated)
    event_consumer.register_handler("vehicle.deleted", event_handlers.handle_vehicle_deleted)
    event_consumer.register_handler("user.created", event_handlers.handle_user_created)
    event_consumer.register_handler("user.role_changed", event_handlers.handle_user_role_changed)
