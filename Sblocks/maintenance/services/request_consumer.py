"""
Service Request Consumer for Maintenance Service
Handles requests from Core service via RabbitMQ following standardized patterns
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any
import aio_pika
from aio_pika.abc import AbstractIncomingMessage

# Import local RabbitMQ config
from config.rabbitmq_config import RabbitMQConfig, json_serializer

from services.maintenance_service import maintenance_records_service
from services.license_service import license_service
from services.analytics_service import maintenance_analytics_service
from services.notification_service import notification_service

logger = logging.getLogger(__name__)


class ServiceRequestConsumer:
    """Handles service requests from Core via RabbitMQ with standardized patterns"""
    
    def __init__(self):
        self.connection = None
        self.channel = None
        self.is_consuming = False
        self.request_timeout = int(os.getenv("REQUEST_TIMEOUT", "30"))
        self.max_retries = int(os.getenv("MAX_REQUEST_RETRIES", "3"))
        self.processed_messages = set()  # For deduplication
        self.config = RabbitMQConfig()  # Initialize config
        
    async def connect(self):
        """Connect to RabbitMQ with improved error handling and standardized config"""
        try:
            self.connection = await aio_pika.connect_robust(
                RabbitMQConfig.RABBITMQ_URL,
                heartbeat=RabbitMQConfig.HEARTBEAT,
                blocked_connection_timeout=RabbitMQConfig.BLOCKED_CONNECTION_TIMEOUT
            )
            
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=RabbitMQConfig.PREFETCH_COUNT)
            
            logger.info("✅ Maintenance service request consumer connected to RabbitMQ")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect maintenance service request consumer: {e}")
            return False
            
    async def disconnect(self):
        """Disconnect from RabbitMQ"""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logger.info("Disconnected from RabbitMQ")
            
    async def setup_queues(self):
        """Setup queues for service requests with proper exchange declaration and binding"""
        try:
            # Declare exchange using new config structure
            exchange = await self.channel.declare_exchange(
                self.config.EXCHANGE_NAMES["requests"], 
                aio_pika.ExchangeType.DIRECT, 
                durable=True
            )
            logger.info("✅ Service requests exchange declared/connected")
            
            # Declare queue with consistent naming
            queue = await self.channel.declare_queue(
                self.config.QUEUE_NAMES["maintenance"], 
                durable=True
            )
            logger.info(f"✅ Created/connected to {self.config.QUEUE_NAMES['maintenance']} queue")
            
            # Bind queue to exchange with routing key (must match Core service routing pattern)
            await queue.bind(exchange, routing_key="maintenance.requests")
            logger.info(f"✅ Queue bound to {self.config.EXCHANGE_NAMES['requests']} exchange with routing key 'maintenance.requests'")
            
            logger.info("✅ Maintenance service queue setup complete")
            return queue
            
        except Exception as e:
            logger.error(f"❌ Failed to setup queue: {e}")
            raise
    
    async def start_consuming(self):
        """Start consuming service requests"""
        try:
            if not self.connection or self.connection.is_closed:
                await self.connect()
                
            # Setup queues and exchanges
            queue = await self.setup_queues()
            
            # Start consuming
            await queue.consume(self._handle_request_message, no_ack=False)
            self.is_consuming = True
            
            logger.info("Started consuming service requests from maintenance.requests queue")
            
            # Keep consuming
            while self.is_consuming:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error in maintenance service request consumption: {e}")
            self.is_consuming = False
            raise
            
    async def stop_consuming(self):
        """Stop consuming requests"""
        self.is_consuming = False
        if self.channel:
            await self.channel.close()
        logger.info("Stopped consuming maintenance service requests")
        
    async def _handle_request_message(self, message: AbstractIncomingMessage):
        """Handle incoming service request message with deduplication and validation"""
        try:
            async with message.process(requeue=False):
                # Parse message
                request_data = json.loads(message.body.decode())
                
                # Support both old (request_id, path) and new (correlation_id, endpoint) formats
                correlation_id = request_data.get("correlation_id") or request_data.get("request_id")
                endpoint = request_data.get("endpoint") or request_data.get("path")
                method = request_data.get("method")
                data = request_data.get("data") or {}
                user_context = request_data.get("user_context", {})
                
                # Handle body data for legacy format
                if "body" in request_data:
                    body_data = request_data.get("body")
                    if body_data:
                        try:
                            data = json.loads(body_data) if isinstance(body_data, str) else body_data
                        except json.JSONDecodeError:
                            logger.warning(f"Could not parse body data: {body_data}")
                
                # Add query params to data for legacy format
                if "query_params" in request_data:
                    data.update(request_data.get("query_params", {}))
                
                # Validate request
                if not self._validate_request(correlation_id, endpoint, method):
                    return
                
                # Check for duplicates
                if correlation_id in self.processed_messages:
                    logger.warning(f"⚠️ Duplicate message detected: {correlation_id}")
                    return
                
                logger.info(f"🔄 Processing maintenance service request {correlation_id}: {method} {endpoint}")
                
                # Process the request
                response = await self._process_request(endpoint, method, data, user_context)
                
                # Send response back to Core
                await self._send_response(correlation_id, response)
                
                # Mark as processed
                self.processed_messages.add(correlation_id)
                
                # Cleanup old processed messages (keep last 1000)
                if len(self.processed_messages) > 1000:
                    self.processed_messages = set(list(self.processed_messages)[-500:])
                
                logger.info(f"✅ Maintenance service request {correlation_id} processed successfully")
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in maintenance service request: {e}")
        except Exception as e:
            logger.error(f"Error processing maintenance service request: {e}")
            # Try to send error response if we have correlation_id
            try:
                request_data = json.loads(message.body.decode())
                correlation_id = request_data.get("correlation_id") or request_data.get("request_id")
                if correlation_id:
                    await self._send_error_response(correlation_id, str(e))
            except:
                pass
                
    def _validate_request(self, correlation_id: str, endpoint: str, method: str) -> bool:
        """Validate request data format"""
        if not correlation_id:
            logger.error("❌ Missing correlation_id in request")
            return False
        if not endpoint:
            logger.error("❌ Missing endpoint in request")
            return False
        if not method:
            logger.error("❌ Missing method in request")
            return False
        return True
                
    async def _process_request(self, endpoint: str, method: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Process request and route to appropriate service method"""
        try:
            # Maintenance records endpoints
            if endpoint.startswith("/maintenance/records"):
                return await self._handle_maintenance_records_request(method, endpoint, data, user_context)
            
            # License records endpoints  
            elif endpoint.startswith("/maintenance/licenses"):
                return await self._handle_license_request(method, endpoint, data, user_context)
            
            # Analytics endpoints
            elif endpoint.startswith("/maintenance/analytics"):
                return await self._handle_analytics_request(method, endpoint, data, user_context)
            
            # Notification endpoints
            elif endpoint.startswith("/maintenance/notifications"):
                return await self._handle_notification_request(method, endpoint, data, user_context)
            
            # Vendor endpoints
            elif endpoint.startswith("/maintenance/vendors"):
                return await self._handle_vendor_request(method, endpoint, data, user_context)
            
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
            
    async def _handle_maintenance_records_request(self, method: str, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle maintenance records requests"""
        try:
            if method == "GET":
                if endpoint == "/maintenance/records":
                    # List maintenance records with filters
                    records = await maintenance_records_service.search_maintenance_records(
                        query=data,
                        skip=data.get("skip", 0),
                        limit=data.get("limit", 100),
                        sort_by=data.get("sort_by", "scheduled_date"),
                        sort_order=data.get("sort_order", "desc")
                    )
                    return {"success": True, "message": "Maintenance records retrieved", "data": records}
                
                elif "/records/" in endpoint:
                    # Get specific maintenance record
                    record_id = endpoint.split("/records/")[-1]
                    record = await maintenance_records_service.get_maintenance_record(record_id)
                    if record:
                        return {"success": True, "message": "Maintenance record retrieved", "data": record}
                    else:
                        return {"success": False, "message": "Maintenance record not found", "error_code": "NOT_FOUND"}
                
                elif endpoint == "/maintenance/records/overdue":
                    records = await maintenance_records_service.get_overdue_maintenance()
                    return {"success": True, "message": "Overdue maintenance retrieved", "data": records}
                
                elif endpoint == "/maintenance/records/upcoming":
                    days_ahead = data.get("days", 7)
                    records = await maintenance_records_service.get_upcoming_maintenance(days_ahead)
                    return {"success": True, "message": "Upcoming maintenance retrieved", "data": records}
                
            elif method == "POST":
                if endpoint == "/maintenance/records":
                    record = await maintenance_records_service.create_maintenance_record(data)
                    return {"success": True, "message": "Maintenance record created", "data": record}
                    
            elif method == "PUT":
                if "/records/" in endpoint:
                    record_id = endpoint.split("/records/")[-1]
                    record = await maintenance_records_service.update_maintenance_record(record_id, data)
                    if record:
                        return {"success": True, "message": "Maintenance record updated", "data": record}
                    else:
                        return {"success": False, "message": "Maintenance record not found", "error_code": "NOT_FOUND"}
                        
            elif method == "DELETE":
                if "/records/" in endpoint:
                    record_id = endpoint.split("/records/")[-1]
                    success = await maintenance_records_service.delete_maintenance_record(record_id)
                    if success:
                        return {"success": True, "message": "Maintenance record deleted"}
                    else:
                        return {"success": False, "message": "Maintenance record not found", "error_code": "NOT_FOUND"}
            
            return {"success": False, "message": "Invalid maintenance records request", "error_code": "INVALID_REQUEST"}
            
        except Exception as e:
            logger.error(f"Error handling maintenance records request: {e}")
            raise
            
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
                "error": error_message,
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
