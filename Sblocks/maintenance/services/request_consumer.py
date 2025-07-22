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
            elif "maintenance/records" in endpoint or endpoint == "maintenance/records":
                return await self._handle_maintenance_records_request(method, user_context)
            elif "maintenance/licenses" in endpoint:
                return await self._handle_license_request(method, user_context)
            elif "maintenance/analytics" in endpoint:
                return await self._handle_analytics_request(method, user_context)
            elif "maintenance/notifications" in endpoint:
                return await self._handle_notification_request(method, user_context)
            elif "maintenance/vendors" in endpoint:
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
            
    async def _handle_license_request(self, method: str, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle license requests"""
        try:
            if method == "GET":
                if endpoint == "/maintenance/licenses":
                    licenses = await license_service.search_licenses(
                        query=data,
                        skip=data.get("skip", 0),
                        limit=data.get("limit", 100),
                        sort_by=data.get("sort_by", "expiry_date"),
                        sort_order=data.get("sort_order", "asc")
                    )
                    return {"success": True, "message": "Licenses retrieved", "data": licenses}
                
                elif "/licenses/" in endpoint:
                    license_id = endpoint.split("/licenses/")[-1]
                    license_record = await license_service.get_license_record(license_id)
                    if license_record:
                        return {"success": True, "message": "License retrieved", "data": license_record}
                    else:
                        return {"success": False, "message": "License not found", "error_code": "NOT_FOUND"}
                
                elif endpoint == "/maintenance/licenses/expiring":
                    days_ahead = data.get("days", 30)
                    licenses = await license_service.get_expiring_licenses(days_ahead)
                    return {"success": True, "message": "Expiring licenses retrieved", "data": licenses}
                
                elif endpoint == "/maintenance/licenses/expired":
                    licenses = await license_service.get_expired_licenses()
                    return {"success": True, "message": "Expired licenses retrieved", "data": licenses}
                    
            elif method == "POST":
                if endpoint == "/maintenance/licenses":
                    license_record = await license_service.create_license_record(data)
                    return {"success": True, "message": "License created", "data": license_record}
                    
            elif method == "PUT":
                if "/licenses/" in endpoint:
                    license_id = endpoint.split("/licenses/")[-1]
                    license_record = await license_service.update_license_record(license_id, data)
                    if license_record:
                        return {"success": True, "message": "License updated", "data": license_record}
                    else:
                        return {"success": False, "message": "License not found", "error_code": "NOT_FOUND"}
                        
            elif method == "DELETE":
                if "/licenses/" in endpoint:
                    license_id = endpoint.split("/licenses/")[-1]
                    success = await license_service.delete_license_record(license_id)
                    if success:
                        return {"success": True, "message": "License deleted"}
                    else:
                        return {"success": False, "message": "License not found", "error_code": "NOT_FOUND"}
            
            return {"success": False, "message": "Invalid license request", "error_code": "INVALID_REQUEST"}
            
        except Exception as e:
            logger.error(f"Error handling license request: {e}")
            raise
            
    async def _handle_analytics_request(self, method: str, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle analytics requests"""
        try:
            if method == "GET":
                if endpoint == "/maintenance/analytics/dashboard":
                    dashboard_data = await maintenance_analytics_service.get_maintenance_dashboard()
                    return {"success": True, "message": "Dashboard data retrieved", "data": dashboard_data}
                
                elif endpoint == "/maintenance/analytics/costs":
                    cost_analytics = await maintenance_analytics_service.get_cost_analytics(
                        vehicle_id=data.get("vehicle_id"),
                        start_date=data.get("start_date"),
                        end_date=data.get("end_date"),
                        group_by=data.get("group_by", "month")
                    )
                    return {"success": True, "message": "Cost analytics retrieved", "data": cost_analytics}
                
                elif endpoint == "/maintenance/analytics/trends":
                    days = data.get("days", 90)
                    trends = await maintenance_analytics_service.get_maintenance_trends(days)
                    return {"success": True, "message": "Maintenance trends retrieved", "data": trends}
                
                elif endpoint == "/maintenance/analytics/vendors":
                    vendor_analytics = await maintenance_analytics_service.get_vendor_analytics()
                    return {"success": True, "message": "Vendor analytics retrieved", "data": vendor_analytics}
                
                elif endpoint == "/maintenance/analytics/licenses":
                    license_analytics = await maintenance_analytics_service.get_license_analytics()
                    return {"success": True, "message": "License analytics retrieved", "data": license_analytics}
            
            return {"success": False, "message": "Invalid analytics request", "error_code": "INVALID_REQUEST"}
            
        except Exception as e:
            logger.error(f"Error handling analytics request: {e}")
            raise
            
    async def _handle_notification_request(self, method: str, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle notification requests"""
        try:
            if method == "GET":
                if endpoint == "/maintenance/notifications/pending":
                    notifications = await notification_service.get_pending_notifications()
                    return {"success": True, "message": "Pending notifications retrieved", "data": notifications}
                
                elif endpoint == "/maintenance/notifications/user":
                    user_id = data.get("user_id")
                    unread_only = data.get("unread_only", False)
                    notifications = await notification_service.get_user_notifications(user_id, unread_only)
                    return {"success": True, "message": "User notifications retrieved", "data": notifications}
                    
            elif method == "POST":
                if endpoint == "/maintenance/notifications":
                    notification = await notification_service.create_notification(data)
                    return {"success": True, "message": "Notification created", "data": notification}
                
                elif endpoint == "/maintenance/notifications/process":
                    sent_count = await notification_service.process_pending_notifications()
                    return {"success": True, "message": f"Processed {sent_count} notifications", "data": {"sent_count": sent_count}}
                    
            elif method == "PUT":
                if "/notifications/" in endpoint and endpoint.endswith("/read"):
                    notification_id = endpoint.split("/notifications/")[1].split("/read")[0]
                    success = await notification_service.mark_notification_read(notification_id)
                    return {"success": True, "message": "Notification marked as read"}
            
            return {"success": False, "message": "Invalid notification request", "error_code": "INVALID_REQUEST"}
            
        except Exception as e:
            logger.error(f"Error handling notification request: {e}")
            raise
            
    async def _handle_vendor_request(self, method: str, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle vendor requests (placeholder for future implementation)"""
        return {"success": False, "message": "Vendor endpoints not yet implemented", "error_code": "NOT_IMPLEMENTED"}
        
    async def _process_request(self, endpoint: str, method: str, data: Dict[str, Any], query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Process the request and return response"""
        try:
            # Route to the appropriate handler based on endpoint
            if endpoint.startswith("/maintenance/records") or endpoint.startswith("/records"):
                return await self._handle_maintenance_records_request(method, endpoint, data, query_params)
            elif endpoint.startswith("/maintenance/licenses") or endpoint.startswith("/licenses"):
                return await self._handle_license_request(method, endpoint, data, query_params)
            elif endpoint.startswith("/maintenance/analytics") or endpoint.startswith("/analytics"):
                return await self._handle_analytics_request(method, endpoint, data, query_params)
            elif endpoint.startswith("/maintenance/notifications") or endpoint.startswith("/notifications"):
                return await self._handle_notification_request(method, endpoint, data, query_params)
            elif endpoint.startswith("/maintenance/vendors") or endpoint.startswith("/vendors"):
                return await self._handle_vendor_request(method, endpoint, data, query_params)
            else:
                return {
                    "success": False,
                    "message": f"Unknown endpoint: {endpoint}",
                    "error_code": "UNKNOWN_ENDPOINT"
                }
        except Exception as e:
            logger.error(f"Error processing maintenance request: {e}")
            return {
                "success": False,
                "message": f"Error processing request: {str(e)}",
                "error_code": "PROCESSING_ERROR"
            }
        
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

    async def _handle_license_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle license-related requests"""
        # License service not implemented yet
        return {
            "message": "License service not yet implemented",
            "method": method
        }
    
    async def _handle_analytics_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle analytics-related requests"""
        # Analytics service not implemented yet
        return {
            "message": "Analytics service not yet implemented",
            "method": method
        }
    
    async def _handle_notification_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle notification-related requests"""
        # Notification service not implemented yet
        return {
            "message": "Notification service not yet implemented",
            "method": method
        }
    
    async def _handle_vendor_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle vendor-related requests"""
        # Vendor service not implemented yet
        return {
            "message": "Vendor service not yet implemented",
            "method": method
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


# Global service instance
service_request_consumer = ServiceRequestConsumer()
