"""
RabbitMQ messaging client for GPS service
"""
import json
import asyncio
from typing import Optional, Dict, Any, Callable
import aio_pika
from aio_pika import Message, DeliveryMode, ExchangeType
import logging

from config import settings, event_types

logger = logging.getLogger(__name__)

class RabbitMQClient:
    def __init__(self):
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.exchange: Optional[aio_pika.Exchange] = None
        self.is_connected = False

    async def connect(self):
        """Establish connection to RabbitMQ"""
        try:
            logger.info(f"Connecting to RabbitMQ at {settings.rabbitmq_url}")
            
            self.connection = await aio_pika.connect_robust(
                settings.rabbitmq_url,
                loop=asyncio.get_event_loop()
            )
            
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=100)
            
            # Declare exchange
            self.exchange = await self.channel.declare_exchange(
                settings.rabbitmq_exchange,
                ExchangeType.TOPIC,
                durable=True
            )
            
            self.is_connected = True
            logger.info("Successfully connected to RabbitMQ")
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def disconnect(self):
        """Close RabbitMQ connection"""
        try:
            if self.connection and not self.connection.is_closed:
                await self.connection.close()
                self.is_connected = False
                logger.info("Disconnected from RabbitMQ")
        except Exception as e:
            logger.error(f"Error disconnecting from RabbitMQ: {e}")

    async def publish_message(self, routing_key: str, message: Dict[str, Any], priority: int = 0):
        """Publish a message to the exchange"""
        if not self.is_connected or not self.exchange:
            logger.error("RabbitMQ not connected. Cannot publish message.")
            return False
        
        try:
            message_body = json.dumps(message, default=str)
            
            await self.exchange.publish(
                Message(
                    message_body.encode(),
                    delivery_mode=DeliveryMode.PERSISTENT,
                    priority=priority,
                    headers={
                        "service": "gps_tracking",
                        "event_type": routing_key,
                        "timestamp": message.get("timestamp")
                    }
                ),
                routing_key=routing_key
            )
            
            logger.debug(f"Published message to {routing_key}: {message}")
            return True
            
        except Exception as e:
            logger.error(f"Error publishing message: {e}")
            return False

    async def create_queue(self, queue_name: str, routing_keys: list, callback: Callable):
        """Create a queue and bind it to routing keys"""
        if not self.is_connected or not self.channel or not self.exchange:
            logger.error("RabbitMQ not connected. Cannot create queue.")
            return
        
        try:
            queue = await self.channel.declare_queue(
                f"{settings.rabbitmq_queue_prefix}_{queue_name}",
                durable=True
            )
            
            # Bind queue to routing keys
            for routing_key in routing_keys:
                await queue.bind(self.exchange, routing_key)
            
            # Set up consumer
            await queue.consume(callback)
            
            logger.info(f"Created queue {queue_name} with routing keys: {routing_keys}")
            
        except Exception as e:
            logger.error(f"Error creating queue {queue_name}: {e}")

# Global messaging client
messaging_client = RabbitMQClient()

# Event publishing functions
async def publish_location_update(vehicle_id: str, location_data: Dict[str, Any]):
    """Publish location update event"""
    message = {
        "event_type": event_types.LOCATION_UPDATED,
        "vehicle_id": vehicle_id,
        "location": location_data,
        "timestamp": location_data.get("timestamp"),
        "service": "gps_tracking"
    }
    
    await messaging_client.publish_message(
        routing_key=f"location.updated.{vehicle_id}",
        message=message,
        priority=5
    )

async def publish_geofence_event(event_type: str, vehicle_id: str, geofence_id: str, event_data: Dict[str, Any]):
    """Publish geofence entry/exit event"""
    message = {
        "event_type": event_type,
        "vehicle_id": vehicle_id,
        "geofence_id": geofence_id,
        "event_data": event_data,
        "timestamp": event_data.get("timestamp"),
        "service": "gps_tracking"
    }
    
    routing_key = f"geofence.{event_type.split('.')[-1]}.{vehicle_id}"
    await messaging_client.publish_message(
        routing_key=routing_key,
        message=message,
        priority=8
    )

async def publish_speed_violation(vehicle_id: str, violation_data: Dict[str, Any]):
    """Publish speed violation event"""
    message = {
        "event_type": event_types.SPEED_VIOLATION,
        "vehicle_id": vehicle_id,
        "violation": violation_data,
        "timestamp": violation_data.get("timestamp"),
        "service": "gps_tracking"
    }
    
    await messaging_client.publish_message(
        routing_key=f"speed.violation.{vehicle_id}",
        message=message,
        priority=9
    )

async def publish_route_event(event_type: str, vehicle_id: str, route_data: Dict[str, Any]):
    """Publish route start/completion event"""
    message = {
        "event_type": event_type,
        "vehicle_id": vehicle_id,
        "route": route_data,
        "timestamp": route_data.get("timestamp"),
        "service": "gps_tracking"
    }
    
    routing_key = f"route.{event_type.split('.')[-1]}.{vehicle_id}"
    await messaging_client.publish_message(
        routing_key=routing_key,
        message=message,
        priority=6
    )

async def publish_vehicle_idle(vehicle_id: str, idle_data: Dict[str, Any]):
    """Publish vehicle idle event"""
    message = {
        "event_type": event_types.VEHICLE_IDLE,
        "vehicle_id": vehicle_id,
        "idle_data": idle_data,
        "timestamp": idle_data.get("timestamp"),
        "service": "gps_tracking"
    }
    
    await messaging_client.publish_message(
        routing_key=f"vehicle.idle.{vehicle_id}",
        message=message,
        priority=4
    )

async def publish_emergency_alert(vehicle_id: str, alert_data: Dict[str, Any]):
    """Publish emergency alert"""
    message = {
        "event_type": event_types.EMERGENCY_ALERT,
        "vehicle_id": vehicle_id,
        "alert": alert_data,
        "timestamp": alert_data.get("timestamp"),
        "service": "gps_tracking"
    }
    
    await messaging_client.publish_message(
        routing_key=f"emergency.alert.{vehicle_id}",
        message=message,
        priority=10  # Highest priority
    )

# Message handlers for incoming events
async def handle_trip_planning_event(message: aio_pika.IncomingMessage):
    """Handle events from trip planning service"""
    try:
        async with message.process():
            body = json.loads(message.body.decode())
            event_type = body.get("event_type")
            
            logger.info(f"Received trip planning event: {event_type}")
            
            # Process different event types
            if event_type == "trip.started":
                await handle_trip_started(body)
            elif event_type == "trip.completed":
                await handle_trip_completed(body)
            elif event_type == "route.assigned":
                await handle_route_assigned(body)
            
    except Exception as e:
        logger.error(f"Error handling trip planning event: {e}")

async def handle_trip_started(event_data: Dict[str, Any]):
    """Handle trip started event"""
    vehicle_id = event_data.get("vehicle_id")
    trip_id = event_data.get("trip_id")
    
    logger.info(f"Trip {trip_id} started for vehicle {vehicle_id}")
    # Additional processing as needed

async def handle_trip_completed(event_data: Dict[str, Any]):
    """Handle trip completed event"""
    vehicle_id = event_data.get("vehicle_id")
    trip_id = event_data.get("trip_id")
    
    logger.info(f"Trip {trip_id} completed for vehicle {vehicle_id}")
    # Additional processing as needed

async def handle_route_assigned(event_data: Dict[str, Any]):
    """Handle route assignment event"""
    vehicle_id = event_data.get("vehicle_id")
    route_id = event_data.get("route_id")
    
    logger.info(f"Route {route_id} assigned to vehicle {vehicle_id}")
    # Additional processing as needed

# Health check
async def check_messaging_health() -> bool:
    """Check if messaging system is healthy"""
    try:
        return messaging_client.is_connected
    except Exception:
        return False

# Initialize messaging
async def initialize_messaging():
    """Initialize RabbitMQ connection and queues"""
    try:
        await messaging_client.connect()
        
        # Create queues for incoming events
        await messaging_client.create_queue(
            "trip_events",
            ["trip.*", "route.*"],
            handle_trip_planning_event
        )
        
        logger.info("Messaging system initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize messaging: {e}")
        raise

async def cleanup_messaging():
    """Cleanup messaging connections"""
    await messaging_client.disconnect()

# Export main functions
__all__ = [
    "messaging_client",
    "publish_location_update",
    "publish_geofence_event", 
    "publish_speed_violation",
    "publish_route_event",
    "publish_vehicle_idle",
    "publish_emergency_alert",
    "initialize_messaging",
    "cleanup_messaging",
    "check_messaging_health"
]
