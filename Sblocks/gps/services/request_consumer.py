"""
Service request consumer for handling requests from Core service
"""
import aio_pika
import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import os
from aio_pika.abc import AbstractIncomingMessage

# Import standardized RabbitMQ config
from config.rabbitmq_config import RabbitMQConfig, json_serializer

from api.routes.geofences import router as geofences_router
from api.routes.locations import router as locations_router
from api.routes.places import router as places_router
from api.routes.tracking import router as tracking_router

logger = logging.getLogger(__name__)


class ServiceRequestConsumer:
    """Handles service requests from Core via RabbitMQ with standardized patterns"""
    
    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = None
        self.queue = None
        # Use standardized config
        self.config = RabbitMQConfig()
        self.queue_name = self.config.QUEUE_NAMES["gps"]
        self.exchange_name = self.config.EXCHANGE_NAMES["requests"]
        self.response_exchange_name = self.config.EXCHANGE_NAMES["responses"]
        # Request deduplication
        self.processed_requests = set()
        self.is_consuming = False
    
    async def connect(self):
        """Establish connection to RabbitMQ using standardized config"""
        try:
            self.connection = await aio_pika.connect_robust(
                url=self.config.get_rabbitmq_url(),
                heartbeat=self.config.CONNECTION_PARAMS["heartbeat"],
                blocked_connection_timeout=self.config.CONNECTION_PARAMS["blocked_connection_timeout"]
            )
            self.channel = await self.connection.channel()

            # Declare exchanges
            self.exchange = await self.channel.declare_exchange(
                self.exchange_name,
                aio_pika.ExchangeType.DIRECT,
                durable=True
            )

            self.response_exchange = await self.channel.declare_exchange(
                self.response_exchange_name,
                aio_pika.ExchangeType.DIRECT,
                durable=True
            )

            # Declare and bind queue
            self.queue = await self.channel.declare_queue(
                self.queue_name,
                durable=True
            )
            
            # Bind to management routing key (must match Core service routing pattern)
            await self.queue.bind(self.exchange, "gps.requests")

            logger.info(f"Connected to RabbitMQ. Queue: {self.queue_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
    
    async def start_consuming(self):
        """Start consuming requests"""
        try:
            if not self.connection or self.connection.is_closed:
                await self.connect()
                
            await self.queue.consume(self.handle_request, no_ack=False)
            logger.info(f"Started consuming from {self.queue_name}")
            
        except Exception as e:
            logger.error(f"Error starting consumer: {e}")
            raise
    
    async def handle_request(self, message: AbstractIncomingMessage):
        """Handle incoming request message using standardized pattern"""
        request_id = None
        try:
            async with message.process(requeue=False):
                # Parse message body
                request_data = json.loads(message.body.decode())
                
                # Extract request details
                request_id = request_data.get("correlation_id")
                method = request_data.get("method")
                user_context = request_data.get("user_context", {})
                endpoint = request_data.get("endpoint", "")
                
                # Check for duplicate requests
                if request_id in self.processed_requests:
                    logger.warning(f"Duplicate request ignored: {request_id}")
                    return
                    
                self.processed_requests.add(request_id)
                
                logger.info(f"Processing request {request_id}: {method} {endpoint}")
                
                # Route and process request
                response_data = await self._route_request(method, user_context, endpoint)
                
                # Send successful response
                response = {
                    "status": "success",
                    "data": response_data,
                    "timestamp": datetime.now().isoformat()
                }
                
                await self._send_response(request_id, response)
                logger.info(f"Request {request_id} completed successfully")
        except Exception as e:
            logger.error(f"Error processing request {request_id}: {e}")
            if request_id:
                error_response = {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                await self._send_response(request_id, error_response)
    
    async def _route_request(self, method: str, user_context: Dict[str, Any], endpoint: str = "") -> Dict[str, Any]:
        """Route request to appropriate handler based on method name"""
        try:
            # Route to appropriate handler based on enpoint pattern
            if "/health" in endpoint:
                return await self._handle_health_check(method, user_context)
            else:
                raise ValueError(f"Unknown endpoint: {endpoint}")
        except Exception as e:
            logger.error(f"Error routing request for {endpoint}: {e}")
            raise

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
        """Handle health check requests"""
        return {
            "status": "healthy",
            "service": "management",
            "timestamp": datetime.now().isoformat(),
            "message": "Management service is operational"
        }
    
    async def _send_response(self, correlation_id: str, response_data: Dict[str, Any]):
        """Send response back to Core via RabbitMQ using standardized config"""
        try:
            # Prepare response message
            response_msg = {
                "correlation_id": correlation_id,
                "status": "success", 
                "data": response_data,
                "timestamp": datetime.now().isoformat()
            }
            
            # Send response using standardized response exchange
            message = aio_pika.Message(
                json.dumps(response_msg, default=json_serializer).encode(),
                correlation_id=correlation_id
            )
            
            await self.response_exchange.publish(
                message, 
                routing_key=self.config.ROUTING_KEYS["core_responses"]
            )
            
            logger.debug(f"Response sent for correlation_id: {correlation_id}")
            
        except Exception as e:
            logger.error(f"Failed to send response for {correlation_id}: {e}")
            raise
    async def stop_consuming(self):
        """Stop consuming messages"""
        self.is_consuming = False
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
        logger.info("GPS service request consumer stopped")


# Global service request consumer instance
service_request_consumer = ServiceRequestConsumer()
