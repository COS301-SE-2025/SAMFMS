"""
Service Request Consumer for Management Service
Handles requests from Core service via RabbitMQ with standardized patterns
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any
import aio_pika
from aio_pika.abc import AbstractIncomingMessage

# Import standardized RabbitMQ config
from config.rabbitmq_config import RabbitMQConfig, json_serializer

from api.routes.vehicles import router as vehicles_router
from api.routes.drivers import router as drivers_router
from api.routes.analytics import router as analytics_router

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
        self.queue_name = self.config.QUEUE_NAMES["management"]
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
            await self.queue.bind(self.exchange, "management.requests")
            
            logger.info(f"Connected to RabbitMQ. Queue: {self.queue_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
    
    async def setup_queues(self):
        """Setup queues and exchanges (already done in connect)"""
        # Queue setup is now handled in connect method
        return self.queue
    
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
                request_payload = request_data.get("data", {})  # Extract the actual request data
                
                # Check for duplicate requests
                if request_id in self.processed_requests:
                    logger.warning(f"Duplicate request ignored: {request_id}")
                    return
                    
                self.processed_requests.add(request_id)
                
                logger.debug(f"Processing request {request_id}: {method} {endpoint}")
                
                # Route and process request
                response_data = await self._route_request(method, user_context, endpoint, request_payload)
                
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
                    "error": {
                        "message": str(e),
                        "type": type(e).__name__
                    },
                    "timestamp": datetime.now().isoformat()
                }
                await self._send_response(request_id, error_response)
    
    async def _route_request(self, method: str, user_context: Dict[str, Any], endpoint: str = "", request_payload: Dict[str, Any] = None) -> Dict[str, Any]:
        """Route request to appropriate handler based on method name"""
        try:
            # Validate inputs
            if not method or not isinstance(method, str):
                raise ValueError("Invalid HTTP method")
            
            if not isinstance(user_context, dict):
                raise ValueError("Invalid user context")
            
            if not isinstance(endpoint, str):
                raise ValueError("Invalid endpoint")
            
            if request_payload is None:
                request_payload = {}
            
            # Normalize endpoint path
            endpoint = endpoint.strip().lstrip('/').rstrip('/')
            
            # Add endpoint and request data to user_context for handlers to use
            user_context["endpoint"] = endpoint
            user_context["data"] = request_payload  # Add the request payload here
            
            logger.debug(f"Routing {method} request to endpoint: {endpoint}")
            
            # Route to appropriate handler based on endpoint pattern
            if endpoint == "health" or endpoint == "":
                # Health check endpoint
                return await self._handle_health_request(method, user_context)
            elif "vehicles" in endpoint or endpoint == "vehicles":
                return await self._handle_vehicles_request(method, user_context)
            elif "drivers" in endpoint:
                return await self._handle_drivers_request(method, user_context)
            elif "assignments" in endpoint or "vehicle-assignments" in endpoint:
                return await self._handle_assignments_request(method, user_context)
            elif "fuel" in endpoint:
                return await self._handle_fuel_request(method, user_context)
            elif "mileage" in endpoint:
                return await self._handle_mileage_request(method, user_context)
            elif "notifications" in endpoint:
                return await self._handle_notifications_request(method, user_context)
            elif "analytics" in endpoint:
                return await self._handle_analytics_request(method, user_context)
            elif "status" in endpoint or endpoint == "status":
                return await self._handle_status_request(method, user_context)
            elif "docs" in endpoint or "openapi" in endpoint:
                return await self._handle_docs_request(method, user_context)
            elif "metrics" in endpoint:
                return await self._handle_metrics_request(method, user_context)
            else:
                raise ValueError(f"Unknown endpoint: {endpoint}")
                
        except Exception as e:
            logger.error(f"Error routing request for {endpoint}: {e}")
            raise
    
    async def _handle_vehicles_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle vehicles-related requests by delegating to vehicle service"""
        try:
            from services.vehicle_service import vehicle_service
            return await vehicle_service.handle_request(method, user_context)
        except Exception as e:
            from schemas.responses import ResponseBuilder
            logger.error(f"Error handling vehicles request: {e}")
            return ResponseBuilder.error(
                error="VehicleRequestError",
                message=f"Failed to process vehicle request: {str(e)}"
            ).model_dump()
    
    async def _handle_drivers_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle drivers-related requests by delegating to driver service"""
        try:
            from services.driver_service import driver_service
            return await driver_service.handle_request(method, user_context)
        except Exception as e:
            from schemas.responses import ResponseBuilder
            logger.error(f"Error handling drivers request: {e}")
            return ResponseBuilder.error(
                error="DriverRequestError",
                message=f"Failed to process driver request: {str(e)}"
            ).model_dump()
    
    async def _handle_assignments_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle assignments-related requests by delegating to assignment service"""
        try:
            from services.assignment_service import assignment_service
            return await assignment_service.handle_request(method, user_context)
        except Exception as e:
            from schemas.responses import ResponseBuilder
            logger.error(f"Error handling assignments request: {e}")
            return ResponseBuilder.error(
                error="AssignmentRequestError",
                message=f"Failed to process assignment request: {str(e)}"
            ).model_dump()
    
    async def _handle_fuel_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle fuel-related requests by delegating to fuel service"""
        try:
            from services.fuel_service import fuel_service
            return await fuel_service.handle_request(method, user_context)
        except Exception as e:
            from schemas.responses import ResponseBuilder
            logger.error(f"Error handling fuel request: {e}")
            return ResponseBuilder.error(
                error="FuelRequestError",
                message=f"Failed to process fuel request: {str(e)}"
            ).model_dump()
    
    async def _handle_mileage_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle mileage-related requests by delegating to mileage service"""
        try:
            from services.mileage_service import mileage_service
            return await mileage_service.handle_request(method, user_context)
        except Exception as e:
            from schemas.responses import ResponseBuilder
            logger.error(f"Error handling mileage request: {e}")
            return ResponseBuilder.error(
                error="MileageRequestError",
                message=f"Failed to process mileage request: {str(e)}"
            ).model_dump()
    
    async def _handle_notifications_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle notifications-related requests by delegating to notification service"""
        try:
            from services.notification_service import notification_service
            return await notification_service.handle_request(method, user_context)
        except Exception as e:
            from schemas.responses import ResponseBuilder
            logger.error(f"Error handling notifications request: {e}")
            return ResponseBuilder.error(
                error="NotificationRequestError",
                message=f"Failed to process notification request: {str(e)}"
            ).model_dump()
    
    async def _handle_analytics_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle analytics-related requests by delegating to analytics service"""
        try:
            from services.analytics_service import analytics_service
            return await analytics_service.handle_request(method, user_context)
        except Exception as e:
            from schemas.responses import ResponseBuilder
            logger.error(f"Error handling analytics request: {e}")
            return ResponseBuilder.error(
                error="AnalyticsRequestError",
                message=f"Failed to process analytics request: {str(e)}"
            ).model_dump()
    
    async def _handle_health_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle health check requests"""
        if method == "GET":
            return {
                "status": "healthy",
                "service": "management",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0"
            }
        else:
            raise ValueError(f"Unsupported method for health endpoint: {method}")
    
    async def _handle_status_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle status requests"""
        if method == "GET":
            return {
                "status": "operational",
                "service": "management",
                "uptime": "unknown",  # Could implement actual uptime tracking
                "connections": {
                    "database": "connected",
                    "rabbitmq": "connected"
                },
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise ValueError(f"Unsupported method for status endpoint: {method}")
    
    async def _handle_docs_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle documentation requests"""
        if method == "GET":
            return {
                "message": "API documentation available at /docs",
                "openapi_url": "/openapi.json",
                "service": "management"
            }
        else:
            raise ValueError(f"Unsupported method for docs endpoint: {method}")
    
    async def _handle_metrics_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle metrics requests"""
        if method == "GET":
            return {
                "metrics": {
                    "requests_processed": len(self.processed_requests),
                    "service_status": "healthy",
                    "last_request_time": datetime.now().isoformat()
                },
                "service": "management"
            }
        else:
            raise ValueError(f"Unsupported method for metrics endpoint: {method}")
    
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
        logger.info("Management service request consumer stopped")

# Global instance
service_request_consumer = ServiceRequestConsumer()
