"""
Standardized RabbitMQ Configuration for SAMFMS
Provides consistent connection parameters and patterns across all services
"""

import os
import logging
import asyncio
import aio_pika
from typing import Dict, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class RabbitMQConfig:
    """Centralized RabbitMQ configuration"""
    
    # Connection settings
    RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://samfms_rabbit:RabbitPass2025!@rabbitmq:5672/")
    
    # Connection parameters
    HEARTBEAT = 60  # seconds
    BLOCKED_CONNECTION_TIMEOUT = 300  # seconds
    CONNECTION_ATTEMPTS = 3
    RETRY_DELAY = 2.0  # seconds
    SOCKET_TIMEOUT = 10  # seconds
    
    # Channel settings
    PREFETCH_COUNT = 10
    
    # Exchange and queue settings
    EXCHANGES = {
        "service_requests": {
            "type": aio_pika.ExchangeType.DIRECT,
            "durable": True
        },
        "service_responses": {
            "type": aio_pika.ExchangeType.DIRECT,
            "durable": True
        },
        "service_events": {
            "type": aio_pika.ExchangeType.TOPIC,
            "durable": True
        }
    }
    
    # Standard queue names
    QUEUE_NAMES = {
        "management": "management.requests",
        "maintenance": "maintenance.requests",
        "security": "security.requests",
        "gps": "gps.requests",
        "trip_planning": "trip_planning.requests",
        "utilities": "utilities.requests"
    }
    
    # Response routing
    RESPONSE_QUEUE = "core.responses"
    RESPONSE_ROUTING_KEY = "core.responses"


class RabbitMQConnectionManager:
    """Manages RabbitMQ connections with health monitoring and circuit breaker"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.is_connected = False
        self.failure_count = 0
        self.max_failures = 5
        self.circuit_open = False
        self.last_failure_time = None
        
    async def connect(self) -> bool:
        """Connect to RabbitMQ with circuit breaker pattern"""
        if self.circuit_open:
            if self._should_attempt_reset():
                logger.info(f"Circuit breaker: Attempting to reset for {self.service_name}")
                self.circuit_open = False
            else:
                logger.warning(f"Circuit breaker open for {self.service_name}, skipping connection attempt")
                return False
                
        try:
            self.connection = await aio_pika.connect_robust(
                RabbitMQConfig.RABBITMQ_URL,
                heartbeat=RabbitMQConfig.HEARTBEAT,
                blocked_connection_timeout=RabbitMQConfig.BLOCKED_CONNECTION_TIMEOUT,
                client_properties={
                    "service_name": self.service_name,
                    "connection_time": datetime.utcnow().isoformat()
                }
            )
            
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=RabbitMQConfig.PREFETCH_COUNT)
            
            self.is_connected = True
            self.failure_count = 0
            
            logger.info(f"✅ {self.service_name} connected to RabbitMQ successfully")
            return True
            
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()
            
            if self.failure_count >= self.max_failures:
                self.circuit_open = True
                logger.error(f"❌ Circuit breaker opened for {self.service_name} after {self.failure_count} failures")
            
            logger.error(f"❌ Failed to connect {self.service_name} to RabbitMQ: {e}")
            return False
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        if not self.last_failure_time:
            return True
        
        reset_timeout = 60  # seconds
        time_since_failure = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return time_since_failure > reset_timeout
    
    async def disconnect(self):
        """Safely disconnect from RabbitMQ"""
        try:
            if self.connection and not self.connection.is_closed:
                await self.connection.close()
            self.is_connected = False
            logger.info(f"✅ {self.service_name} disconnected from RabbitMQ")
        except Exception as e:
            logger.warning(f"⚠️ Error disconnecting {self.service_name} from RabbitMQ: {e}")
    
    async def check_health(self) -> bool:
        """Check RabbitMQ connection health"""
        try:
            if not self.connection or self.connection.is_closed:
                return False
            
            # Simple health check - declare a temporary queue
            temp_queue = await self.channel.declare_queue("", exclusive=True, auto_delete=True)
            await temp_queue.delete()
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ RabbitMQ health check failed for {self.service_name}: {e}")
            return False


class StandardizedServiceConsumer:
    """Standardized service consumer pattern"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.connection_manager = RabbitMQConnectionManager(service_name)
        self.is_consuming = False
        self.processed_messages = set()  # For deduplication
        
    async def setup_service_consumption(self, message_handler):
        """Setup standardized service request consumption"""
        try:
            # Connect to RabbitMQ
            if not await self.connection_manager.connect():
                raise Exception("Failed to connect to RabbitMQ")
            
            channel = self.connection_manager.channel
            
            # Declare service requests exchange
            exchange = await channel.declare_exchange(
                "service_requests",
                RabbitMQConfig.EXCHANGES["service_requests"]["type"],
                durable=RabbitMQConfig.EXCHANGES["service_requests"]["durable"]
            )
            
            # Get queue name for this service
            queue_name = RabbitMQConfig.QUEUE_NAMES.get(self.service_name)
            if not queue_name:
                raise ValueError(f"No queue name configured for service: {self.service_name}")
            
            # Declare and bind queue
            queue = await channel.declare_queue(queue_name, durable=True)
            await queue.bind(exchange, routing_key=queue_name)
            
            # Setup message consumption with deduplication
            async def wrapped_handler(message: aio_pika.IncomingMessage):
                await self._handle_message_with_deduplication(message, message_handler)
            
            await queue.consume(wrapped_handler)
            self.is_consuming = True
            
            logger.info(f"✅ {self.service_name} service consumption setup complete")
            logger.info(f"📝 Consuming from queue: {queue_name}")
            logger.info(f"🔗 Bound to exchange: service_requests")
            
        except Exception as e:
            logger.error(f"❌ Failed to setup service consumption for {self.service_name}: {e}")
            raise
    
    async def _handle_message_with_deduplication(self, message: aio_pika.IncomingMessage, handler):
        """Handle message with deduplication and error handling"""
        try:
            async with message.process(requeue=True):
                # Parse message
                request_data = json.loads(message.body.decode())
                correlation_id = request_data.get("correlation_id")
                
                # Check for duplicates
                if correlation_id in self.processed_messages:
                    logger.warning(f"⚠️ Duplicate message detected: {correlation_id}")
                    return
                
                # Validate request
                if not self._validate_request(request_data):
                    logger.error(f"❌ Invalid request format: {correlation_id}")
                    return
                
                # Process message
                await handler(message)
                
                # Mark as processed
                self.processed_messages.add(correlation_id)
                
                # Cleanup old processed messages (keep last 1000)
                if len(self.processed_messages) > 1000:
                    # Remove oldest half
                    self.processed_messages = set(list(self.processed_messages)[-500:])
                
        except Exception as e:
            logger.error(f"❌ Error handling message in {self.service_name}: {e}")
            raise
    
    def _validate_request(self, request_data: Dict[str, Any]) -> bool:
        """Validate request data format"""
        required_fields = ["correlation_id", "endpoint", "method", "user_context"]
        return all(field in request_data for field in required_fields)
    
    async def send_response(self, response_data: Dict[str, Any]):
        """Send standardized response"""
        try:
            if not self.connection_manager.is_connected:
                await self.connection_manager.connect()
            
            channel = self.connection_manager.channel
            
            # Declare response exchange
            exchange = await channel.declare_exchange(
                "service_responses",
                RabbitMQConfig.EXCHANGES["service_responses"]["type"],
                durable=RabbitMQConfig.EXCHANGES["service_responses"]["durable"]
            )
            
            # Send response
            message = aio_pika.Message(
                body=json.dumps(response_data, default=self._json_serializer).encode(),
                content_type="application/json",
                headers={
                    "service_name": self.service_name,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            await exchange.publish(message, routing_key=RabbitMQConfig.RESPONSE_ROUTING_KEY)
            
            logger.debug(f"📤 Response sent from {self.service_name}: {response_data.get('correlation_id')}")
            
        except Exception as e:
            logger.error(f"❌ Error sending response from {self.service_name}: {e}")
            raise
    
    def _json_serializer(self, obj):
        """JSON serializer for non-serializable objects"""
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        elif hasattr(obj, '__str__'):
            return str(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    async def stop_consuming(self):
        """Stop consuming and cleanup"""
        self.is_consuming = False
        await self.connection_manager.disconnect()
        logger.info(f"✅ {self.service_name} consumer stopped")


def json_serializer(obj):
    """Global JSON serializer for compatibility"""
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    elif hasattr(obj, '__str__'):
        return str(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
