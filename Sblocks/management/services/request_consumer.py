"""
Service Request Consumer for Management Service
Handles requests from Core service via RabbitMQ
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any
import aio_pika
from aio_pika.abc import AbstractIncomingMessage

from api.routes.vehicles import router as vehicles_router
from api.routes.drivers import router as drivers_router
from api.routes.analytics import router as analytics_router

logger = logging.getLogger(__name__)

def json_serializer(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

class ServiceRequestConsumer:
    """Handles service requests from Core via RabbitMQ"""
    
    def __init__(self):
        self.connection = None
        self.channel = None
        self.is_consuming = False
        self.rabbitmq_url = os.getenv(
            "RABBITMQ_URL", 
            "amqp://samfms_rabbit:RabbitPass2025!@rabbitmq:5672/"
        )
        
    async def connect(self):
        """Connect to RabbitMQ with improved error handling"""
        try:
            # Use the same connection parameters as event consumer
            self.connection = await aio_pika.connect_robust(
                self.rabbitmq_url,
                heartbeat=300,  # Reduced heartbeat
                blocked_connection_timeout=120,  # Reduced timeout
                connection_attempts=3,
                retry_delay=1.0
            )
            
            self.channel = await self.connection.channel(
                publisher_confirms=True,
                on_return_raises=False
            )
            await self.channel.set_qos(prefetch_count=5)
            
            logger.info("✅ Service request consumer connected to RabbitMQ")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect service request consumer: {e}")
            return False
    
    async def setup_queues(self):
        """Setup queues and exchanges for service requests"""
        try:
            # Declare service_requests exchange
            exchange = await self.channel.declare_exchange(
                "service_requests", 
                aio_pika.ExchangeType.DIRECT, 
                durable=True
            )
            
            # Declare management.requests queue
            queue = await self.channel.declare_queue(
                "management.requests", 
                durable=True
            )
            
            # Bind queue to exchange
            await queue.bind(exchange, routing_key="management.requests")
            
            logger.info("Service request queues and exchanges setup complete")
            return queue
            
        except Exception as e:
            logger.error(f"Failed to setup service request queues: {e}")
            raise
    
    async def start_consuming(self):
        """Start consuming service requests"""
        try:
            if self.is_consuming:
                logger.warning("Service request consumer already consuming")
                return
                
            queue = await self.setup_queues()
            
            # Start consuming
            await queue.consume(self._handle_request_message, no_ack=False)
            self.is_consuming = True
            
            logger.info("Started consuming service requests from management.requests queue")
            
            # Keep consuming
            while self.is_consuming:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error in service request consumption: {e}")
            self.is_consuming = False
            raise
    
    async def _handle_request_message(self, message: AbstractIncomingMessage):
        """Handle incoming service request message"""
        try:
            async with message.process(requeue=False):
                # Parse message
                request_data = json.loads(message.body.decode())
                correlation_id = request_data.get("correlation_id")
                endpoint = request_data.get("endpoint")
                method = request_data.get("method")
                data = request_data.get("data", {})
                user_context = request_data.get("user_context", {})
                
                logger.info(f"Processing service request {correlation_id}: {method} {endpoint}")
                
                # Process the request
                response = await self._process_request(endpoint, method, data, user_context)
                
                # Send response back to Core
                await self._send_response(correlation_id, response)
                
                logger.info(f"Service request {correlation_id} processed successfully")
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in service request: {e}")
        except Exception as e:
            logger.error(f"Error processing service request: {e}")
            # Try to send error response if we have correlation_id
            try:
                request_data = json.loads(message.body.decode())
                correlation_id = request_data.get("correlation_id")
                if correlation_id:
                    await self._send_error_response(correlation_id, str(e))
            except:
                pass
    
    async def _process_request(self, endpoint: str, method: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Process the actual service request"""
        try:
            # Core is already sending /api/v1/vehicles, so we don't need to map
            # Just route based on the endpoint pattern
            
            # Route to appropriate handler based on endpoint
            if "/vehicles" in endpoint:
                return await self._handle_vehicles_request(endpoint, method, data, user_context)
            elif "/drivers" in endpoint:
                return await self._handle_drivers_request(endpoint, method, data, user_context)
            elif "/assignments" in endpoint or "/vehicle-assignments" in endpoint:
                return await self._handle_assignments_request(endpoint, method, data, user_context)
            elif "/analytics" in endpoint:
                return await self._handle_analytics_request(endpoint, method, data, user_context)
            else:
                raise ValueError(f"Unknown endpoint: {endpoint}")
                
        except Exception as e:
            logger.error(f"Error processing request for {endpoint}: {e}")
            raise
    
    async def _handle_vehicles_request(self, endpoint: str, method: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle vehicles-related requests"""
        # Import and create service instance
        from services.vehicle_service import VehicleService
        from schemas.requests import VehicleCreateRequest, VehicleUpdateRequest
        vehicle_service = VehicleService()
        
        # Support both /api/vehicles and /api/v1/vehicles endpoints
        if method == "GET":
            if endpoint in ["/api/vehicles", "/api/v1/vehicles"]:
                return await vehicle_service.get_vehicles()
            elif "/vehicles/" in endpoint:
                vehicle_id = endpoint.split("/")[-1]
                return await vehicle_service.get_vehicle_by_id(vehicle_id)
            elif "/vehicles/search" in endpoint:
                query = data.get("query", "")
                return await vehicle_service.search_vehicles(query)
        elif method == "POST":
            if endpoint in ["/api/vehicles", "/api/v1/vehicles"]:
                # Convert dict to VehicleCreateRequest object
                vehicle_request = VehicleCreateRequest(**data)
                # Extract created_by from user_context
                created_by = user_context.get("user_id", "unknown")
                return await vehicle_service.create_vehicle(vehicle_request, created_by)
        elif method == "PUT":
            if "/vehicles/" in endpoint:
                vehicle_id = endpoint.split("/")[-1]
                # Convert dict to VehicleUpdateRequest object
                vehicle_update_request = VehicleUpdateRequest(**data)
                # Extract updated_by from user_context
                updated_by = user_context.get("user_id", "unknown")
                return await vehicle_service.update_vehicle(vehicle_id, vehicle_update_request, updated_by)
        elif method == "DELETE":
            if "/vehicles/" in endpoint:
                vehicle_id = endpoint.split("/")[-1]
                # Extract deleted_by from user_context
                deleted_by = user_context.get("user_id", "unknown")
                return await vehicle_service.delete_vehicle(vehicle_id, deleted_by)
        
        raise ValueError(f"Unsupported vehicles operation: {method} {endpoint}")
    
    async def _handle_drivers_request(self, endpoint: str, method: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle drivers-related requests"""
        from services.driver_service import DriverService
        driver_service = DriverService()
        
        if method == "GET":
            if endpoint == "/api/v1/drivers":
                return await driver_service.get_active_drivers()
            elif "/api/v1/drivers/" in endpoint:
                driver_id = endpoint.split("/")[-1]
                return await driver_service.get_driver_by_id(driver_id)
        elif method == "POST":
            if endpoint == "/api/v1/drivers":
                # Extract created_by from user_context
                created_by = user_context.get("user_id", "unknown")
                return await driver_service.create_driver(data, created_by)
        elif method == "PUT":
            if "/api/v1/drivers/" in endpoint:
                driver_id = endpoint.split("/")[-1]
                # Extract updated_by from user_context
                updated_by = user_context.get("user_id", "unknown")
                return await driver_service.update_driver(driver_id, data, updated_by)
        elif method == "DELETE":
            if "/api/v1/drivers/" in endpoint:
                driver_id = endpoint.split("/")[-1]
                return await driver_service.delete_driver(driver_id)
        
        raise ValueError(f"Unsupported drivers operation: {method} {endpoint}")
    
    async def _handle_assignments_request(self, endpoint: str, method: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle assignments-related requests"""
        # Assignment service not implemented yet
        return {
            "message": "Assignment service not yet implemented",
            "endpoint": endpoint,
            "method": method
        }
    
    async def _handle_analytics_request(self, endpoint: str, method: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle analytics-related requests"""
        from services.analytics_service import analytics_service
        
        if method == "GET":
            use_cache = data.get("use_cache", True)
            
            if endpoint == "/api/v1/analytics":
                return await analytics_service.get_analytics_data(data)
            elif endpoint == "/api/v1/analytics/dashboard":
                return await analytics_service.get_dashboard_analytics(use_cache=use_cache)
            elif endpoint == "/api/v1/analytics/fleet-utilization":
                return await analytics_service.get_fleet_utilization(use_cache=use_cache)
            elif endpoint == "/api/v1/analytics/vehicle-usage":
                return await analytics_service.get_vehicle_usage(use_cache=use_cache)
            elif endpoint == "/api/v1/analytics/assignment-metrics":
                return await analytics_service.get_assignment_metrics(use_cache=use_cache)
            elif endpoint == "/api/v1/analytics/driver-performance":
                return await analytics_service.get_driver_performance(use_cache=use_cache)
            elif endpoint == "/api/v1/analytics/cost-analysis":
                return await analytics_service.get_cost_analysis(use_cache=use_cache)
        
        raise ValueError(f"Unsupported analytics operation: {method} {endpoint}")
    
    async def _send_response(self, correlation_id: str, response_data: Dict[str, Any]):
        """Send response back to Core via RabbitMQ"""
        try:
            # Prepare response message
            response_msg = {
                "correlation_id": correlation_id,
                "status": "success",
                "data": response_data,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            # Declare service_responses exchange
            exchange = await self.channel.declare_exchange(
                "service_responses", 
                aio_pika.ExchangeType.DIRECT, 
                durable=True
            )
            
            # Send response to core.responses queue using custom serializer
            message = aio_pika.Message(
                json.dumps(response_msg, default=json_serializer).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )
            
            await exchange.publish(message, routing_key="core.responses")
            
            logger.debug(f"Sent response for correlation_id: {correlation_id}")
            
        except Exception as e:
            logger.error(f"Error sending response for {correlation_id}: {e}")
            raise
    
    async def _send_error_response(self, correlation_id: str, error_message: str):
        """Send error response back to Core"""
        try:
            response_msg = {
                "correlation_id": correlation_id,
                "status": "error",
                "error": error_message,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            exchange = await self.channel.declare_exchange(
                "service_responses", 
                aio_pika.ExchangeType.DIRECT, 
                durable=True
            )
            
            message = aio_pika.Message(
                json.dumps(response_msg).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )
            
            await exchange.publish(message, routing_key="core.responses")
            
            logger.debug(f"Sent error response for correlation_id: {correlation_id}")
            
        except Exception as e:
            logger.error(f"Error sending error response for {correlation_id}: {e}")
    
    async def stop_consuming(self):
        """Stop consuming messages"""
        self.is_consuming = False
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
        logger.info("Service request consumer stopped")

# Global instance
service_request_consumer = ServiceRequestConsumer()
