
import aio_pika
import asyncio
import json
import logging
from typing import Dict, Any, Callable, Optional
import os
from datetime import datetime, timedelta
import traceback

from .events import VehicleEvent, UserEvent

logger = logging.getLogger(__name__)


class EventConsumer:
    
    
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
        self.enable_dead_letter_queue = os.getenv("ENABLE_DLQ", "true").lower() == "true"
        
    async def connect(self):
        
        max_retries = 3
        for attempt in range(max_retries):
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
                
                logger.info("Connected to RabbitMQ for event consumption")
                return True
                
            except Exception as e:
                logger.error(f"Failed to connect to RabbitMQ (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  
                    continue
                return False
    
    async def disconnect(self):
        
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
        
        self.handlers[event_pattern] = handler
        logger.info(f"Registered handler for {event_pattern}")
    
    async def start_consuming(self):
        
        if not self.connection:
            logger.error("Not connected to RabbitMQ")
            return
        
        if self.is_consuming:
            logger.warning("Already consuming events")
            return
        
        try:
            
            if self.enable_dead_letter_queue:
                await self._setup_dead_letter_queue()
            else:
                logger.info("Dead letter queue disabled via configuration")
            
            
            queue_name = "management_service_events"
            queue = await self._declare_queue_with_fallback(queue_name)
            
            
            await self._setup_bindings(queue)
            
            
            await queue.consume(self._handle_message_with_retry, no_ack=False)
            
            self.is_consuming = True
            logger.info("Started consuming events")
            
        except Exception as e:
            logger.error(f"Failed to start consuming events: {e}")
            self.is_consuming = False
            raise
    
    async def _setup_bindings(self, queue: aio_pika.Queue):
        
        
        vehicles_exchange = await self.channel.declare_exchange(
            "vehicle_events",
            aio_pika.ExchangeType.TOPIC,
            durable=True
        )
        
        await queue.bind(vehicles_exchange, "vehicle.created")
        await queue.bind(vehicles_exchange, "vehicle.updated")
        await queue.bind(vehicles_exchange, "vehicle.deleted")
        await queue.bind(vehicles_exchange, "vehicle.status_changed")
        
        
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
        
        try:
            
            dlx = await self.channel.declare_exchange(
                "management_dlx",
                aio_pika.ExchangeType.DIRECT,
                durable=True
            )
            
            
            self.dead_letter_queue = await self.channel.declare_queue(
                "management_dlq",
                durable=True
            )
            
            
            await self.dead_letter_queue.bind(dlx, "failed")
            
            logger.info("Setup dead letter queue successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup dead letter queue: {e}")
            logger.warning("Continuing without dead letter queue - failed messages will be logged only")
            self.dead_letter_queue = None
    
    async def _handle_message_with_retry(self, message: aio_pika.IncomingMessage):
        
        retry_count = message.headers.get("x-retry-count", 0) if message.headers else 0
        
        async with message.process(requeue=False):
            try:
                await self._handle_message(message)
                
            except Exception as e:
                logger.error(f"Error handling message (attempt {retry_count + 1}): {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                
                
                if retry_count < self.max_retry_attempts:
                    await self._retry_message(message, retry_count + 1, str(e))
                else:
                    await self._send_to_dead_letter_queue(message, str(e))
                
                
                raise
    
    async def _retry_message(self, message: aio_pika.IncomingMessage, retry_count: int, error: str):
        
        try:
            
            delay = self.retry_delay * (2 ** (retry_count - 1))
            
            
            new_headers = dict(message.headers) if message.headers else {}
            new_headers.update({
                "x-retry-count": retry_count,
                "x-original-error": error,
                "x-retry-timestamp": datetime.utcnow().isoformat()
            })
            
            
            await asyncio.sleep(delay)
            
            
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
        
        try:
            if not self.dead_letter_queue:
                logger.error(f"Dead letter queue not available, logging failed message: {error}")
                logger.error(f"Failed message body: {message.body[:500]}...")  
                logger.error(f"Failed message routing key: {message.routing_key}")
                return
            
            
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
            
            
            try:
                dlx = await self.channel.get_exchange("management_dlx")
                await dlx.publish(dlq_message, routing_key="failed")
                logger.error(f"Sent message to dead letter queue: {error}")
            except Exception as dlx_error:
                logger.error(f"Failed to publish to dead letter exchange: {dlx_error}")
                
                logger.error(f"Failed message (DLX failed): {error}")
                logger.error(f"Message body: {message.body[:500]}")
            
        except Exception as e:
            logger.error(f"Critical error in dead letter queue handling: {e}")
            
            logger.error(f"Failed message (DLQ error): {error}")
            logger.error(f"Message routing key: {message.routing_key}")
            logger.error(f"Message body: {message.body[:500]}")
    
    async def _handle_message(self, message: aio_pika.IncomingMessage):
        
        try:
            
            body = json.loads(message.body.decode())
            routing_key = message.routing_key
            event_type = message.headers.get("event_type", routing_key) if message.headers else routing_key
            
            logger.info(f"Processing event: {event_type} (routing_key: {routing_key})")
            
            
            if not isinstance(body, dict):
                raise ValueError(f"Invalid message body format: expected dict, got {type(body)}")
            
            
            handler = self._find_handler(routing_key)
            if handler:
                
                start_time = datetime.utcnow()
                await handler(body, routing_key, message.headers or {})
                duration = (datetime.utcnow() - start_time).total_seconds()
                
                logger.info(f"Successfully processed event {event_type} in {duration:.3f}s")
            else:
                logger.warning(f"No handler found for event: {routing_key}")
                
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode message JSON: {e}")
            logger.error(f"Raw message body: {message.body}")
            raise ValueError(f"Invalid JSON in message: {e}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            raise
    
    def _find_handler(self, routing_key: str) -> Callable:
        
        
        if routing_key in self.handlers:
            return self.handlers[routing_key]
        
        
        for pattern, handler in self.handlers.items():
            if self._pattern_match(pattern, routing_key):
                return handler
        
        return None
    
    def _pattern_match(self, pattern: str, routing_key: str) -> bool:
        
        pattern_parts = pattern.split(".")
        key_parts = routing_key.split(".")
        
        if len(pattern_parts) != len(key_parts):
            return False
        
        for pattern_part, key_part in zip(pattern_parts, key_parts):
            if pattern_part != "*" and pattern_part != key_part:
                return False
        
        return True
    
    async def _declare_queue_with_fallback(self, queue_name: str):
        
        
        
        try:
            queue = await self.channel.declare_queue(queue_name, passive=True)
            logger.info(f"Connected to existing queue {queue_name}")
            return queue
        except Exception:
            
            pass
        
        
        if self.enable_dead_letter_queue and self.dead_letter_queue:
            queue_args = {
                "x-message-ttl": 300000,  
                "x-max-length": 1000,
                "x-overflow": "drop-head",
                "x-dead-letter-exchange": "management_dlx",
                "x-dead-letter-routing-key": "failed"
            }
            logger.info("Attempting to declare queue with dead letter exchange")
        else:
            queue_args = {
                "x-message-ttl": 300000,  
                "x-max-length": 1000,
                "x-overflow": "drop-head"
            }
            logger.info("Attempting to declare queue without dead letter exchange")
        
        
        try:
            queue = await self.channel.declare_queue(
                queue_name,
                durable=True,
                arguments=queue_args
            )
            logger.info(f"Successfully declared queue {queue_name}")
            return queue
            
        except Exception as e:
            if "PRECONDITION_FAILED" in str(e) and "inequivalent arg" in str(e):
                logger.warning(f"Queue {queue_name} exists with different arguments: {e}")
                
                
                if "Channel closed" in str(e) or "ChannelInvalidStateError" in str(e) or "RPC timeout" in str(e):
                    logger.info("Recreating channel after precondition failure")
                    await self._recreate_channel()
                
                
                try:
                    queue = await self.channel.declare_queue(queue_name, passive=True)
                    logger.info(f"Connected to existing queue {queue_name} with its current configuration")
                    return queue
                except Exception as passive_error:
                    logger.error(f"Failed to connect to existing queue: {passive_error}")
                    
                    
                    try:
                        queue = await self.channel.declare_queue(queue_name, durable=True)
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
        
        try:
            if self.channel and not self.channel.is_closed:
                await self.channel.close()
            
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)
            logger.info("Successfully recreated RabbitMQ channel")
            
        except Exception as e:
            logger.error(f"Failed to recreate channel: {e}")
            raise



class ManagementEventHandlers:
    
    
    def __init__(self):
        
        self.analytics_service = None
        self.assignment_repo = None
        self.driver_repo = None
    
    def _get_analytics_service(self):
        
        if self.analytics_service is None:
            try:
                from ..services.analytics_service import analytics_service
                self.analytics_service = analytics_service
            except ImportError as e:
                logger.error(f"Failed to import analytics service: {e}")
        return self.analytics_service
    
    def _get_assignment_repo(self):
        
        if self.assignment_repo is None:
            try:
                from ..repositories.repositories import VehicleAssignmentRepository
                self.assignment_repo = VehicleAssignmentRepository()
            except ImportError as e:
                logger.error(f"Failed to import VehicleAssignmentRepository: {e}")
        return self.assignment_repo
    
    def _get_driver_repo(self):
        
        if self.driver_repo is None:
            try:
                from ..repositories.repositories import DriverRepository
                self.driver_repo = DriverRepository()
            except ImportError as e:
                logger.error(f"Failed to import DriverRepository: {e}")
        return self.driver_repo
    
    async def _safe_refresh_analytics(self, reason: str):
        
        try:
            analytics_service = self._get_analytics_service()
            if analytics_service:
                asyncio.create_task(analytics_service.refresh_all_cache())
                logger.info(f"Triggered analytics refresh: {reason}")
        except Exception as e:
            logger.error(f"Failed to refresh analytics ({reason}): {e}")
    
    async def handle_vehicle_created(self, data: Dict[str, Any], routing_key: str, headers: Dict[str, Any]):
        
        try:
            vehicle_id = data.get('vehicle_id')
            if not vehicle_id:
                raise ValueError("Missing vehicle_id in event data")
            
            logger.info(f"Processing vehicle created event: {vehicle_id}")
            
            
            required_fields = ['vehicle_id', 'status']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                logger.warning(f"Missing fields in vehicle created event: {missing_fields}")
            
            
            await self._safe_refresh_analytics(f"vehicle created: {vehicle_id}")
            
            logger.info(f"Successfully processed vehicle created event: {vehicle_id}")
            
        except Exception as e:
            logger.error(f"Error handling vehicle created event: {e}")
            logger.error(f"Event data: {data}")
            raise
    
    async def handle_vehicle_updated(self, data: Dict[str, Any], routing_key: str, headers: Dict[str, Any]):
        
        try:
            vehicle_id = data.get('vehicle_id')
            if not vehicle_id:
                raise ValueError("Missing vehicle_id in event data")
            
            logger.info(f"Processing vehicle updated event: {vehicle_id}")
            
            
            changes = data.get("changes", {})
            if "status" in changes:
                old_status = changes["status"].get("old")
                new_status = changes["status"].get("new")
                logger.info(f"Vehicle {vehicle_id} status changed: {old_status} -> {new_status}")
                
                await self._safe_refresh_analytics(f"vehicle status changed: {vehicle_id}")
            
            
            significant_changes = ["department", "type", "capacity"]
            if any(field in changes for field in significant_changes):
                await self._safe_refresh_analytics(f"vehicle configuration changed: {vehicle_id}")
            
            logger.info(f"Successfully processed vehicle updated event: {vehicle_id}")
            
        except Exception as e:
            logger.error(f"Error handling vehicle updated event: {e}")
            logger.error(f"Event data: {data}")
            raise
    
    async def handle_vehicle_deleted(self, data: Dict[str, Any], routing_key: str, headers: Dict[str, Any]):
        
        try:
            vehicle_id = data.get('vehicle_id')
            if not vehicle_id:
                raise ValueError("Missing vehicle_id in event data")
            
            logger.info(f"Processing vehicle deleted event: {vehicle_id}")
            
            
            assignment_repo = self._get_assignment_repo()
            if assignment_repo:
                try:
                    
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
                    
            
            
            await self._safe_refresh_analytics(f"vehicle deleted: {vehicle_id}")
            
            logger.info(f"Successfully processed vehicle deleted event: {vehicle_id}")
            
        except Exception as e:
            logger.error(f"Error handling vehicle deleted event: {e}")
            logger.error(f"Event data: {data}")
            raise
    
    async def handle_user_created(self, data: Dict[str, Any], routing_key: str, headers: Dict[str, Any]):
        
        try:
            user_id = data.get('user_id')
            if not user_id:
                raise ValueError("Missing user_id in event data")
            
            logger.info(f"Processing user created event: {user_id}")
            
            
            required_fields = ['user_id', 'email']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                logger.warning(f"Missing fields in user created event: {missing_fields}")
            
            
            user_role = data.get("role")
            if user_role == "driver":
                logger.info(f"New driver user created: {user_id}")
                
                
                
                
                
                logger.info(f"Driver user {user_id} may need driver record creation")
            
            logger.info(f"Successfully processed user created event: {user_id}")
            
        except Exception as e:
            logger.error(f"Error handling user created event: {e}")
            logger.error(f"Event data: {data}")
            raise
    
    async def handle_user_role_changed(self, data: Dict[str, Any], routing_key: str, headers: Dict[str, Any]):
        
        try:
            user_id = data.get('user_id')
            old_role = data.get('old_role')
            new_role = data.get('new_role')
            
            if not user_id:
                raise ValueError("Missing user_id in event data")
            
            logger.info(f"Processing user role change: {user_id} from {old_role} to {new_role}")
            
            
            if old_role == "driver" and new_role != "driver":
                
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
                        
            
            elif old_role != "driver" and new_role == "driver":
                
                logger.info(f"User {user_id} became a driver - may need driver record creation")
            
            logger.info(f"Successfully processed user role change event: {user_id}")
            
        except Exception as e:
            logger.error(f"Error handling user role changed event: {e}")
            logger.error(f"Event data: {data}")
            raise



event_consumer = EventConsumer()
event_handlers = ManagementEventHandlers()


async def setup_event_handlers():
    
    event_consumer.register_handler("vehicle.created", event_handlers.handle_vehicle_created)
    event_consumer.register_handler("vehicle.updated", event_handlers.handle_vehicle_updated)
    event_consumer.register_handler("vehicle.deleted", event_handlers.handle_vehicle_deleted)
    event_consumer.register_handler("user.created", event_handlers.handle_user_created)
    event_consumer.register_handler("user.role_changed", event_handlers.handle_user_role_changed)
