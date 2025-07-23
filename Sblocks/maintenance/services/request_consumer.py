"""
Service Request Consumer for Maintenance Service
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
        self.queue_name = self.config.QUEUE_NAMES["maintenance"]
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
            
            # Bind to maintenance routing key (must match Core service routing pattern)
            await self.queue.bind(self.exchange, "maintenance.requests")
            
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
            self.is_consuming = True
            logger.info(f"Started consuming from {self.queue_name}")
            
        except Exception as e:
            logger.error(f"Error starting consumer: {e}")
            raise
    
    async def stop_consuming(self):
        """Stop consuming messages"""
        self.is_consuming = False
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
        logger.info("Maintenance service request consumer stopped")

    async def disconnect(self):
        """Disconnect from RabbitMQ"""
        self.is_consuming = False
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
        logger.info("Maintenance service disconnected")
    
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
                
                # Extract data from top-level and add to user_context for handlers
                data = request_data.get("data", {})
                user_context["data"] = data
                
                # Check for duplicate requests
                if request_id in self.processed_requests:
                    logger.warning(f"Duplicate request ignored: {request_id}")
                    return
                    
                self.processed_requests.add(request_id)
                
                logger.debug(f"Processing request {request_id}: {method} {endpoint}")
                
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
                    "error": {
                        "message": str(e),
                        "type": type(e).__name__
                    },
                    "timestamp": datetime.now().isoformat()
                }
                await self._send_response(request_id, error_response)
    
    async def _route_request(self, method: str, user_context: Dict[str, Any], endpoint: str = "") -> Dict[str, Any]:
        """Route request to appropriate handler based on endpoint pattern"""
        try:
            # Validate inputs
            if not method or not isinstance(method, str):
                raise ValueError("Invalid HTTP method")
            
            if not isinstance(user_context, dict):
                raise ValueError("Invalid user context")
            
            if not isinstance(endpoint, str):
                raise ValueError("Invalid endpoint")
            
            # Normalize endpoint path
            endpoint = endpoint.strip().lstrip('/').rstrip('/')
            
            # Add endpoint to user_context for handlers to use
            user_context["endpoint"] = endpoint
            
            logger.debug(f"Routing {method} request to endpoint: {endpoint}")
            
            # Route to appropriate handler based on endpoint pattern
            if endpoint == "health" or endpoint == "":
                # Health check endpoint
                return await self._handle_health_request(method, user_context)
            elif "records" in endpoint or endpoint == "/records":
                return await self._handle_maintenance_records_request(method, user_context)
            elif "licenses" in endpoint:
                return await self._handle_license_request(method, user_context)
            elif "analytics" in endpoint:
                return await self._handle_analytics_request(method, user_context)
            elif "notifications" in endpoint:
                return await self._handle_notification_request(method, user_context)
            elif "vendors" in endpoint:
                return await self._handle_vendor_request(method, user_context)
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
    
    async def _handle_maintenance_records_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle maintenance records requests by calling route logic"""
        try:
            # Import route logic
            from services.maintenance_service import maintenance_records_service
            from schemas.responses import ResponseBuilder
            
            # Extract data and endpoint from user_context
            data = user_context.get("data", {})
            endpoint = user_context.get("endpoint", "")
            
            # Create mock user for service calls
            current_user = {"user_id": user_context.get("user_id", "system")}
            
            # Handle HTTP methods and route to appropriate logic
            if method == "GET":
                if "overdue" in endpoint:
                    records = await maintenance_records_service.get_overdue_maintenance()
                    return ResponseBuilder.success(
                        data=records,
                        message="Overdue maintenance retrieved successfully"
                    ).model_dump()
                elif "upcoming" in endpoint:
                    days_ahead = data.get("days", 7)
                    records = await maintenance_records_service.get_upcoming_maintenance(days_ahead)
                    return ResponseBuilder.success(
                        data=records,
                        message="Upcoming maintenance retrieved successfully"
                    ).model_dump()
                elif endpoint.count('/') > 0 and endpoint.split('/')[-1] and endpoint.split('/')[-1] not in ["records", "maintenance"]:
                    # maintenance/records/{id} pattern
                    record_id = endpoint.split('/')[-1]
                    record = await maintenance_records_service.get_maintenance_record(record_id)
                    if record:
                        return ResponseBuilder.success(
                            data=record,
                            message="Maintenance record retrieved successfully"
                        ).model_dump()
                    else:
                        return ResponseBuilder.error(
                            error="NotFound",
                            message="Maintenance record not found"
                        ).model_dump()
                else:
                    # List maintenance records with filters
                    records = await maintenance_records_service.search_maintenance_records(
                        query=data,
                        skip=data.get("skip", 0),
                        limit=data.get("limit", 100),
                        sort_by=data.get("sort_by", "scheduled_date"),
                        sort_order=data.get("sort_order", "desc")
                    )
                    return ResponseBuilder.success(
                        data=records,
                        message="Maintenance records retrieved successfully"
                    ).model_dump()
                    
            elif method == "POST":
                if not data:
                    raise ValueError("Request data is required for POST operation")
                
                record = await maintenance_records_service.create_maintenance_record(data)
                return ResponseBuilder.success(
                    data=record,
                    message="Maintenance record created successfully"
                ).model_dump()
                
            elif method == "PUT":
                record_id = endpoint.split('/')[-1] if '/' in endpoint else None
                if not record_id:
                    raise ValueError("Record ID is required for PUT operation")
                if not data:
                    raise ValueError("Request data is required for PUT operation")
                
                record = await maintenance_records_service.update_maintenance_record(record_id, data)
                if record:
                    return ResponseBuilder.success(
                        data=record,
                        message="Maintenance record updated successfully"
                    ).model_dump()
                else:
                    return ResponseBuilder.error(
                        error="NotFound",
                        message="Maintenance record not found"
                    ).model_dump()
                    
            elif method == "DELETE":
                record_id = endpoint.split('/')[-1] if '/' in endpoint else None
                if not record_id:
                    raise ValueError("Record ID is required for DELETE operation")
                
                success = await maintenance_records_service.delete_maintenance_record(record_id)
                if success:
                    return ResponseBuilder.success(
                        data={"deleted": True},
                        message="Maintenance record deleted successfully"
                    ).model_dump()
                else:
                    return ResponseBuilder.error(
                        error="NotFound",
                        message="Maintenance record not found"
                    ).model_dump()
                    
            else:
                raise ValueError(f"Unsupported HTTP method for maintenance records: {method}")
                
        except Exception as e:
            logger.error(f"Error handling maintenance records request {method} {endpoint}: {e}")
            return ResponseBuilder.error(
                error="MaintenanceRecordsRequestError",
                message=f"Failed to process maintenance records request: {str(e)}"
            ).model_dump()
            
    async def _handle_license_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle license-related requests"""
        try:
            # Extract data and endpoint from user_context
            data = user_context.get("data", {})
            endpoint = user_context.get("endpoint", "")
            
            if method == "GET":
                if endpoint == "licenses" or "maintenance/licenses" in endpoint:
                    # License service not implemented yet, return placeholder
                    return {
                        "success": True,
                        "message": "License service not yet implemented - GET",
                        "data": [],
                        "method": method,
                        "endpoint": endpoint
                    }
                else:
                    return {
                        "success": True,
                        "message": "License service not yet implemented - GET specific",
                        "data": {},
                        "method": method,
                        "endpoint": endpoint
                    }
            elif method == "POST":
                return {
                    "success": True,
                    "message": "License service not yet implemented - POST",
                    "data": {},
                    "method": method
                }
            elif method == "PUT":
                return {
                    "success": True,
                    "message": "License service not yet implemented - PUT",
                    "data": {},
                    "method": method
                }
            elif method == "DELETE":
                return {
                    "success": True,
                    "message": "License service not yet implemented - DELETE",
                    "data": {"deleted": True},
                    "method": method
                }
            else:
                raise ValueError(f"Unsupported HTTP method for licenses: {method}")
                
        except Exception as e:
            logger.error(f"Error handling license request {method} {endpoint}: {e}")
            return {
                "success": False,
                "message": f"Failed to process license request: {str(e)}",
                "error_code": "LICENSE_REQUEST_ERROR"
            }
    
    async def _handle_analytics_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle analytics-related requests"""
        try:
            # Extract data and endpoint from user_context
            data = user_context.get("data", {})
            endpoint = user_context.get("endpoint", "")
            
            if method == "GET":
                return {
                    "success": True,
                    "message": "Analytics service not yet implemented",
                    "data": {},
                    "method": method,
                    "endpoint": endpoint
                }
            else:
                raise ValueError(f"Unsupported HTTP method for analytics: {method}")
                
        except Exception as e:
            logger.error(f"Error handling analytics request {method} {endpoint}: {e}")
            return {
                "success": False,
                "message": f"Failed to process analytics request: {str(e)}",
                "error_code": "ANALYTICS_REQUEST_ERROR"
            }
    
    async def _handle_notification_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle notification-related requests"""
        try:
            # Extract data and endpoint from user_context
            data = user_context.get("data", {})
            endpoint = user_context.get("endpoint", "")
            
            if method == "GET":
                return {
                    "success": True,
                    "message": "Notification service not yet implemented",
                    "data": [],
                    "method": method,
                    "endpoint": endpoint
                }
            elif method == "POST":
                return {
                    "success": True,
                    "message": "Notification service not yet implemented - POST",
                    "data": {},
                    "method": method
                }
            elif method == "PUT":
                return {
                    "success": True,
                    "message": "Notification service not yet implemented - PUT",
                    "data": {},
                    "method": method
                }
            else:
                raise ValueError(f"Unsupported HTTP method for notifications: {method}")
                
        except Exception as e:
            logger.error(f"Error handling notification request {method} {endpoint}: {e}")
            return {
                "success": False,
                "message": f"Failed to process notification request: {str(e)}",
                "error_code": "NOTIFICATION_REQUEST_ERROR"
            }
    
    async def _handle_vendor_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle vendor-related requests"""
        try:
            # Extract data and endpoint from user_context  
            data = user_context.get("data", {})
            endpoint = user_context.get("endpoint", "")
            
            return {
                "success": False,
                "message": "Vendor endpoints not yet implemented",
                "error_code": "NOT_IMPLEMENTED",
                "method": method,
                "endpoint": endpoint
            }
        except Exception as e:
            logger.error(f"Error handling vendor request {method}: {e}")
            return {
                "success": False,
                "message": f"Failed to process vendor request: {str(e)}",
                "error_code": "VENDOR_REQUEST_ERROR"
            }
    
    async def _handle_health_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle health check requests"""
        if method == "GET":
            return {
                "status": "healthy",
                "service": "maintenance",
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
                "service": "maintenance",
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
                "service": "maintenance"
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
                "service": "maintenance"
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
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Declare service_responses exchange
            exchange = await self.channel.declare_exchange(
                self.config.EXCHANGE_NAMES["responses"], 
                aio_pika.ExchangeType.DIRECT, 
                durable=True
            )
            
            # Send response to core.responses queue using custom serializer
            message = aio_pika.Message(
                json.dumps(response_msg, default=json_serializer).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                content_type="application/json"
            )
            
            await exchange.publish(message, routing_key=self.config.ROUTING_KEYS["core_responses"])
            
            logger.debug(f"📤 Sent response for correlation_id: {correlation_id}")
            
        except Exception as e:
            logger.error(f"❌ Error sending response for {correlation_id}: {e}")
            raise
    
    async def _send_error_response(self, correlation_id: str, error_message: str):
        """Send error response back to Core"""
        try:
            response_msg = {
                "correlation_id": correlation_id,
                "status": "error",
                "error": {
                    "message": error_message,
                    "type": "ServiceError"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            exchange = await self.channel.declare_exchange(
                self.config.EXCHANGE_NAMES["responses"], 
                aio_pika.ExchangeType.DIRECT, 
                durable=True
            )
            
            message = aio_pika.Message(
                json.dumps(response_msg, default=json_serializer).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                content_type="application/json"
            )
            
            await exchange.publish(message, routing_key=self.config.ROUTING_KEYS["core_responses"])
            
            logger.debug(f"📤 Sent error response for correlation_id: {correlation_id}")
            
        except Exception as e:
            logger.error(f"❌ Error sending error response for {correlation_id}: {e}")


# Global service instance
service_request_consumer = ServiceRequestConsumer()
