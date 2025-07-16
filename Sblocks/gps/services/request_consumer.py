"""
Service request consumer for handling requests from Core service
"""
import aio_pika
import asyncio
import json
import logging
from typing import Dict, Any, Optional
import os

logger = logging.getLogger(__name__)


class ServiceRequestConsumer:
    """Consumer for handling service requests from Core"""
    
    def __init__(self):
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.rabbitmq_url = os.getenv(
            "RABBITMQ_URL", 
            "amqp://samfms_rabbit:RabbitPass2025!@rabbitmq:5672/"
        )
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
            
            logger.info("Connected to RabbitMQ for service requests")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ for service requests: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from RabbitMQ"""
        self.is_consuming = False
        
        try:
            if self.channel and not self.channel.is_closed:
                await self.channel.close()
                
            if self.connection and not self.connection.is_closed:
                await self.connection.close()
                logger.info("Disconnected from RabbitMQ service request consumer")
        except Exception as e:
            logger.error(f"Error during service request consumer disconnect: {e}")
        finally:
            self.connection = None
            self.channel = None
    
    async def start_consuming(self):
        """Start consuming service requests"""
        if not self.connection:
            logger.error("Not connected to RabbitMQ")
            return
        
        if self.is_consuming:
            logger.warning("Already consuming service requests")
            return
        
        try:
            # Declare queue for GPS service requests
            queue = await self.channel.declare_queue(
                "gps_service_requests",
                durable=True
            )
            
            # Start consuming
            self.is_consuming = True
            await queue.consume(self._handle_service_request)
            
            logger.info("Started consuming service requests")
            
            # Keep consuming
            while self.is_consuming:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error starting service request consumption: {e}")
            self.is_consuming = False
    
    async def _handle_service_request(self, message: aio_pika.IncomingMessage):
        """Handle incoming service request"""
        async with message.process():
            try:
                # Parse message
                request_data = json.loads(message.body.decode())
                request_type = request_data.get("type")
                
                logger.info(f"Received service request: {request_type}")
                
                # Route to appropriate handler
                if request_type == "get_vehicle_location":
                    await self._handle_get_vehicle_location(request_data)
                elif request_type == "get_vehicle_locations":
                    await self._handle_get_vehicle_locations(request_data)
                elif request_type == "health_check":
                    await self._handle_health_check(request_data)
                else:
                    logger.warning(f"Unknown service request type: {request_type}")
                
            except Exception as e:
                logger.error(f"Error processing service request: {e}")
    
    async def _handle_get_vehicle_location(self, request_data: Dict[str, Any]):
        """Handle get vehicle location request"""
        try:
            from services.location_service import location_service
            
            vehicle_id = request_data.get("vehicle_id")
            location = await location_service.get_vehicle_location(vehicle_id)
            
            # Send response back (implementation depends on your messaging pattern)
            response = {
                "request_id": request_data.get("request_id"),
                "success": location is not None,
                "data": location.model_dump() if location else None
            }
            
            logger.info(f"Handled get_vehicle_location request for {vehicle_id}")
            
        except Exception as e:
            logger.error(f"Error handling get_vehicle_location: {e}")
    
    async def _handle_get_vehicle_locations(self, request_data: Dict[str, Any]):
        """Handle get multiple vehicle locations request"""
        try:
            from services.location_service import location_service
            
            vehicle_ids = request_data.get("vehicle_ids", [])
            locations = await location_service.get_multiple_vehicle_locations(vehicle_ids)
            
            response = {
                "request_id": request_data.get("request_id"),
                "success": True,
                "data": [loc.model_dump() for loc in locations]
            }
            
            logger.info(f"Handled get_vehicle_locations request for {len(vehicle_ids)} vehicles")
            
        except Exception as e:
            logger.error(f"Error handling get_vehicle_locations: {e}")
    
    async def _handle_health_check(self, request_data: Dict[str, Any]):
        """Handle health check request"""
        try:
            from repositories.database import db_manager
            
            db_healthy = await db_manager.health_check()
            
            response = {
                "request_id": request_data.get("request_id"),
                "success": True,
                "data": {
                    "service": "gps",
                    "healthy": db_healthy,
                    "timestamp": "2025-01-16T00:00:00Z"  # Use proper timestamp
                }
            }
            
            logger.info("Handled health_check request")
            
        except Exception as e:
            logger.error(f"Error handling health_check: {e}")


# Global service request consumer instance
service_request_consumer = ServiceRequestConsumer()
