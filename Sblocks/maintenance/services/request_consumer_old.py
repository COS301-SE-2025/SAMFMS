"""
Service Request Consumer for Maintenance Service
Handles requests from Core service via RabbitMQ following the same pattern as Management service
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any
import aio_pika
from aio_pika.abc import AbstractIncomingMessage

from services.maintenance_service import maintenance_records_service
from services.license_service import license_service
from services.analytics_service import maintenance_analytics_service
from services.notification_service import notification_service

logger = logging.getLogger(__name__)

def json_serializer(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


class MaintenanceServiceRequestConsumer:
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
            # Use the same connection parameters as management service
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
            
            logger.info("✅ Maintenance service request consumer connected to RabbitMQ")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect maintenance service request consumer: {e}")
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
            
            # Declare maintenance.requests queue
            queue = await self.channel.declare_queue(
                "maintenance.requests", 
                durable=True
            )
            
            # Bind queue to exchange
            await queue.bind(exchange, routing_key="maintenance.requests")
            
            logger.info("Maintenance service request queues and exchanges setup complete")
            return queue
            
        except Exception as e:
            logger.error(f"Failed to setup maintenance service request queues: {e}")
            raise
            
    async def disconnect(self):
        """Disconnect from RabbitMQ"""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logger.info("Disconnected from RabbitMQ")
            
    async def start_consuming(self):
        """Start consuming service requests"""
        try:
            if self.is_consuming:
                logger.warning("Maintenance service request consumer already consuming")
                return
                
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
        """Stop consuming messages"""
        self.is_consuming = False
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
        logger.info("Maintenance service request consumer stopped")
        
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
                body = request_data.get("body")
                user_context = request_data.get("user_context", {})
                
                logger.info(f"Processing maintenance service request {correlation_id}: {method} {endpoint}")
                
                # Process the request
                response = await self._process_request(endpoint, method, data, body, user_context)
                
                # Send response back to Core
                await self._send_response(correlation_id, response)
                
                logger.info(f"Maintenance service request {correlation_id} processed successfully")
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in maintenance service request: {e}")
        except Exception as e:
            logger.error(f"Error processing maintenance service request: {e}")
            # Try to send error response if we have correlation_id
            try:
                request_data = json.loads(message.body.decode())
                correlation_id = request_data.get("correlation_id")
                if correlation_id:
                    await self._send_error_response(correlation_id, str(e))
            except:
                pass
    
    async def _process_request(self, endpoint: str, method: str, data: Dict[str, Any], body: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Process the actual service request"""
        try:
            # Route to appropriate handler based on endpoint
            if "/maintenance" in endpoint:
                return await self._handle_maintenance_request(endpoint, method, data, body, user_context)
            elif "/licenses" in endpoint:
                return await self._handle_license_request(endpoint, method, data, body, user_context)
            elif "/analytics" in endpoint:
                return await self._handle_analytics_request(endpoint, method, data, body, user_context)
            elif "/notifications" in endpoint:
                return await self._handle_notification_request(endpoint, method, data, body, user_context)
            else:
                raise ValueError(f"Unknown endpoint: {endpoint}")
                
        except Exception as e:
            logger.error(f"Error processing maintenance request for {endpoint}: {e}")
            raise
    
    async def _handle_maintenance_request(self, endpoint: str, method: str, data: Dict[str, Any], body: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle maintenance-related requests"""
        try:
            if method == "GET":
                if endpoint in ["/maintenance", "/api/maintenance", "/api/v1/maintenance"] or endpoint.endswith("/maintenance"):
                    # Get maintenance records with filters
                    records = await maintenance_records_service.search_maintenance_records(
                        query=data,
                        skip=data.get("skip", 0),
                        limit=data.get("limit", 100),
                        sort_by=data.get("sort_by", "scheduled_date"),
                        sort_order=data.get("sort_order", "desc")
                    )
                    return {"success": True, "message": "Maintenance records retrieved", "data": records}
                
                elif "/maintenance/" in endpoint and not endpoint.endswith("/maintenance"):
                    # Get specific maintenance record
                    record_id = endpoint.split("/")[-1]
                    record = await maintenance_records_service.get_maintenance_record(record_id)
                    if record:
                        return {"success": True, "message": "Maintenance record retrieved", "data": record}
                    else:
                        return {"success": False, "message": "Maintenance record not found", "error_code": "NOT_FOUND"}
                
                elif "/maintenance/overdue" in endpoint:
                    records = await maintenance_records_service.get_overdue_maintenance()
                    return {"success": True, "message": "Overdue maintenance records retrieved", "data": records}
                
            elif method == "POST":
                if endpoint in ["/maintenance", "/api/maintenance", "/api/v1/maintenance"] or endpoint.endswith("/maintenance"):
                    # Create new maintenance record
                    import json
                    try:
                        body_data = json.loads(body) if body else {}
                        created_by = user_context.get("user_id", "unknown")
                        record = await maintenance_records_service.create_maintenance_record(body_data, created_by)
                        return {"success": True, "message": "Maintenance record created", "data": record}
                    except json.JSONDecodeError:
                        record = await maintenance_records_service.create_maintenance_record(data, user_context.get("user_id", "unknown"))
                        return {"success": True, "message": "Maintenance record created", "data": record}
                        
            elif method == "PUT":
                if "/maintenance/" in endpoint:
                    record_id = endpoint.split("/")[-1]
                    updated_by = user_context.get("user_id", "unknown")
                    record = await maintenance_records_service.update_maintenance_record(record_id, data, updated_by)
                    return {"success": True, "message": "Maintenance record updated", "data": record}
                    
            elif method == "DELETE":
                if "/maintenance/" in endpoint:
                    record_id = endpoint.split("/")[-1]
                    deleted_by = user_context.get("user_id", "unknown")
                    await maintenance_records_service.delete_maintenance_record(record_id, deleted_by)
                    return {"success": True, "message": "Maintenance record deleted"}
                    
            raise ValueError(f"Unsupported maintenance operation: {method} {endpoint}")
            
        except Exception as e:
            logger.error(f"Error handling maintenance request: {e}")
            raise
    
    async def _handle_license_request(self, endpoint: str, method: str, data: Dict[str, Any], body: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle license-related requests"""
        try:
            if method == "GET":
                if endpoint in ["/licenses", "/api/licenses", "/api/v1/licenses"] or endpoint.endswith("/licenses"):
                    licenses = await license_service.get_licenses(data)
                    return {"success": True, "message": "Licenses retrieved", "data": licenses}
                elif "/licenses/" in endpoint:
                    license_id = endpoint.split("/")[-1]
                    license_record = await license_service.get_license(license_id)
                    if license_record:
                        return {"success": True, "message": "License retrieved", "data": license_record}
                    else:
                        return {"success": False, "message": "License not found", "error_code": "NOT_FOUND"}
                        
            elif method == "POST":
                if endpoint in ["/licenses", "/api/licenses", "/api/v1/licenses"] or endpoint.endswith("/licenses"):
                    import json
                    try:
                        body_data = json.loads(body) if body else {}
                        created_by = user_context.get("user_id", "unknown")
                        license_record = await license_service.create_license(body_data, created_by)
                        return {"success": True, "message": "License created", "data": license_record}
                    except json.JSONDecodeError:
                        license_record = await license_service.create_license(data, user_context.get("user_id", "unknown"))
                        return {"success": True, "message": "License created", "data": license_record}
                        
            elif method == "PUT":
                if "/licenses/" in endpoint:
                    license_id = endpoint.split("/")[-1]
                    updated_by = user_context.get("user_id", "unknown")
                    license_record = await license_service.update_license(license_id, data, updated_by)
                    return {"success": True, "message": "License updated", "data": license_record}
                    
            elif method == "DELETE":
                if "/licenses/" in endpoint:
                    license_id = endpoint.split("/")[-1]
                    await license_service.delete_license(license_id)
                    return {"success": True, "message": "License deleted"}
                    
            raise ValueError(f"Unsupported license operation: {method} {endpoint}")
            
        except Exception as e:
            logger.error(f"Error handling license request: {e}")
            raise
    
    async def _handle_analytics_request(self, endpoint: str, method: str, data: Dict[str, Any], body: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle analytics-related requests"""
        try:
            if method == "GET":
                if endpoint in ["/analytics", "/api/analytics", "/api/v1/analytics"] or endpoint.endswith("/analytics"):
                    use_cache = data.get("use_cache", True)
                    analytics_data = await maintenance_analytics_service.get_analytics_data(data, use_cache)
                    return {"success": True, "message": "Analytics data retrieved", "data": analytics_data}
                    
            raise ValueError(f"Unsupported analytics operation: {method} {endpoint}")
            
        except Exception as e:
            logger.error(f"Error handling analytics request: {e}")
            raise
    
    async def _handle_notification_request(self, endpoint: str, method: str, data: Dict[str, Any], body: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle notification-related requests"""
        try:
            if method == "GET":
                if endpoint in ["/notifications", "/api/notifications", "/api/v1/notifications"] or endpoint.endswith("/notifications"):
                    notifications = await notification_service.get_notifications(data)
                    return {"success": True, "message": "Notifications retrieved", "data": notifications}
                    
            elif method == "POST":
                if endpoint in ["/notifications", "/api/notifications", "/api/v1/notifications"] or endpoint.endswith("/notifications"):
                    import json
                    try:
                        body_data = json.loads(body) if body else {}
                        created_by = user_context.get("user_id", "unknown")
                        notification = await notification_service.create_notification(body_data, created_by)
                        return {"success": True, "message": "Notification created", "data": notification}
                    except json.JSONDecodeError:
                        notification = await notification_service.create_notification(data, user_context.get("user_id", "unknown"))
                        return {"success": True, "message": "Notification created", "data": notification}
                        
            raise ValueError(f"Unsupported notification operation: {method} {endpoint}")
            
        except Exception as e:
            logger.error(f"Error handling notification request: {e}")
            raise
    
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
            
            # Declare core_responses exchange
            exchange = await self.channel.declare_exchange(
                "core_responses", 
                aio_pika.ExchangeType.DIRECT, 
                durable=True
            )
            
            # Send response to core.response queue using custom serializer
            message = aio_pika.Message(
                json.dumps(response_msg, default=json_serializer).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )
            
            await exchange.publish(message, routing_key="core.response")
            
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
                "core_responses", 
                aio_pika.ExchangeType.DIRECT, 
                durable=True
            )
            
            message = aio_pika.Message(
                json.dumps(response_msg).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )
            
            await exchange.publish(message, routing_key="core.response")
            
            logger.debug(f"Sent error response for correlation_id: {correlation_id}")
            
        except Exception as e:
            logger.error(f"Error sending error response for {correlation_id}: {e}")

# Global instance
maintenance_service_request_consumer = MaintenanceServiceRequestConsumer()
            
            return {"success": False, "message": "Invalid maintenance records request", "error_code": "INVALID_REQUEST"}
            
        except Exception as e:
            logger.error(f"Error handling maintenance records request: {e}")
            raise
            
    async def _handle_license_request(self, action: str, endpoint: str, data: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle license requests"""
        try:
            if action == "GET":
                if endpoint == "/maintenance/licenses":
                    licenses = await license_service.search_licenses(
                        query=params,
                        skip=params.get("skip", 0),
                        limit=params.get("limit", 100),
                        sort_by=params.get("sort_by", "expiry_date"),
                        sort_order=params.get("sort_order", "asc")
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
                    days_ahead = params.get("days", 30)
                    licenses = await license_service.get_expiring_licenses(days_ahead)
                    return {"success": True, "message": "Expiring licenses retrieved", "data": licenses}
                
                elif endpoint == "/maintenance/licenses/expired":
                    licenses = await license_service.get_expired_licenses()
                    return {"success": True, "message": "Expired licenses retrieved", "data": licenses}
                    
            elif action == "POST":
                if endpoint == "/maintenance/licenses":
                    license_record = await license_service.create_license_record(data)
                    return {"success": True, "message": "License created", "data": license_record}
                    
            elif action == "PUT":
                if "/licenses/" in endpoint:
                    license_id = endpoint.split("/licenses/")[-1]
                    license_record = await license_service.update_license_record(license_id, data)
                    if license_record:
                        return {"success": True, "message": "License updated", "data": license_record}
                    else:
                        return {"success": False, "message": "License not found", "error_code": "NOT_FOUND"}
                        
            elif action == "DELETE":
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
            
    async def _handle_analytics_request(self, action: str, endpoint: str, data: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle analytics requests"""
        try:
            if action == "GET":
                if endpoint == "/maintenance/analytics/dashboard":
                    dashboard_data = await maintenance_analytics_service.get_maintenance_dashboard()
                    return {"success": True, "message": "Dashboard data retrieved", "data": dashboard_data}
                
                elif endpoint == "/maintenance/analytics/costs":
                    cost_analytics = await maintenance_analytics_service.get_cost_analytics(
                        vehicle_id=params.get("vehicle_id"),
                        start_date=params.get("start_date"),
                        end_date=params.get("end_date"),
                        group_by=params.get("group_by", "month")
                    )
                    return {"success": True, "message": "Cost analytics retrieved", "data": cost_analytics}
                
                elif endpoint == "/maintenance/analytics/trends":
                    days = params.get("days", 90)
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
            
    async def _handle_notification_request(self, action: str, endpoint: str, data: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle notification requests"""
        try:
            if action == "GET":
                if endpoint == "/maintenance/notifications/pending":
                    notifications = await notification_service.get_pending_notifications()
                    return {"success": True, "message": "Pending notifications retrieved", "data": notifications}
                
                elif endpoint == "/maintenance/notifications/user":
                    user_id = params.get("user_id")
                    unread_only = params.get("unread_only", False)
                    notifications = await notification_service.get_user_notifications(user_id, unread_only)
                    return {"success": True, "message": "User notifications retrieved", "data": notifications}
                    
            elif action == "POST":
                if endpoint == "/maintenance/notifications":
                    notification = await notification_service.create_notification(data)
                    return {"success": True, "message": "Notification created", "data": notification}
                
                elif endpoint == "/maintenance/notifications/process":
                    sent_count = await notification_service.process_pending_notifications()
                    return {"success": True, "message": f"Processed {sent_count} notifications", "data": {"sent_count": sent_count}}
                    
            elif action == "PUT":
                if "/notifications/" in endpoint and endpoint.endswith("/read"):
                    notification_id = endpoint.split("/notifications/")[1].split("/read")[0]
                    success = await notification_service.mark_notification_read(notification_id)
                    return {"success": True, "message": "Notification marked as read"}
            
            return {"success": False, "message": "Invalid notification request", "error_code": "INVALID_REQUEST"}
            
        except Exception as e:
            logger.error(f"Error handling notification request: {e}")
            raise
            
    async def _handle_vendor_request(self, action: str, endpoint: str, data: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle vendor requests (placeholder for future implementation)"""
        return {"success": False, "message": "Vendor endpoints not yet implemented", "error_code": "NOT_IMPLEMENTED"}
        
    async def _send_response(self, message: AbstractIncomingMessage, response: Dict[str, Any], request_id: str = None):
        """Send response back to Core service"""
        try:
            # Add request ID to response for correlation
            if request_id:
                response["request_id"] = request_id
                
            # Add timestamp
            response["timestamp"] = datetime.utcnow().isoformat()
            
            # Serialize response
            response_json = json.dumps(response, default=json_serializer)
            
            # Send response
            if message.reply_to:
                await self.channel.default_exchange.publish(
                    aio_pika.Message(
                        response_json.encode(),
                        correlation_id=message.correlation_id
                    ),
                    routing_key=message.reply_to
                )
                
        except Exception as e:
            logger.error(f"Error sending response: {e}")


# Global service instance
maintenance_service_request_consumer = MaintenanceServiceRequestConsumer()
