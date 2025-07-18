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
        self.request_timeout = int(os.getenv("REQUEST_TIMEOUT", "30"))  # seconds
        self.max_retries = int(os.getenv("MAX_REQUEST_RETRIES", "3"))
        self.rabbitmq_url = os.getenv(
            "RABBITMQ_URL", 
            "amqp://samfms_rabbit:RabbitPass2025!@rabbitmq:5672/"
        )
        
    async def connect(self):
        """Connect to RabbitMQ"""
        try:
            self.connection = await aio_pika.connect_robust(
                self.rabbitmq_url,
                heartbeat=600,
                blocked_connection_timeout=300,
                connection_attempts=3,
            )
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)
            
            logger.info("Connected to RabbitMQ for maintenance service requests")
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
            
    async def disconnect(self):
        """Disconnect from RabbitMQ"""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logger.info("Disconnected from RabbitMQ")
            
    async def start_consuming(self):
        """Start consuming service requests"""
        try:
            if not self.connection or self.connection.is_closed:
                await self.connect()
                
            # Declare the request queue for maintenance service
            request_queue = await self.channel.declare_queue(
                "maintenance_service_requests", 
                durable=True
            )
            
            # Start consuming
            await request_queue.consume(self._handle_request)
            self.is_consuming = True
            
            logger.info("Started consuming maintenance service requests")
            
        except Exception as e:
            logger.error(f"Failed to start consuming: {e}")
            raise
            
    async def stop_consuming(self):
        """Stop consuming requests"""
        self.is_consuming = False
        if self.channel:
            await self.channel.close()
        logger.info("Stopped consuming maintenance service requests")
        
    async def _handle_request(self, message: AbstractIncomingMessage):
        """Handle incoming service request with timeout and validation"""
        request_data = None
        start_time = datetime.utcnow()
        
        async with message.process():
            try:
                # Parse the message with timeout
                try:
                    request_data = json.loads(message.body.decode())
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON in maintenance service request: {e}")
                    error_response = {
                        "success": False,
                        "message": "Invalid JSON format",
                        "error_code": "INVALID_JSON"
                    }
                    await self._send_response(message, error_response, None)
                    return
                
                # Validate required fields
                required_fields = ["action", "endpoint"]
                missing_fields = [field for field in required_fields if field not in request_data]
                if missing_fields:
                    logger.error(f"Missing required fields in request: {missing_fields}")
                    error_response = {
                        "success": False,
                        "message": f"Missing required fields: {', '.join(missing_fields)}",
                        "error_code": "MISSING_FIELDS"
                    }
                    await self._send_response(message, error_response, request_data.get("request_id"))
                    return
                
                logger.info(f"Received maintenance service request: {request_data.get('action', 'unknown')} - {request_data.get('endpoint', 'unknown')}")
                
                # Extract request details
                action = request_data.get("action")
                endpoint = request_data.get("endpoint", "")
                data = request_data.get("data", {})
                params = request_data.get("params", {})
                request_id = request_data.get("request_id")
                
                # Check for timeout
                if hasattr(message, 'timestamp') and message.timestamp:
                    message_age = (datetime.utcnow() - message.timestamp).total_seconds()
                    if message_age > self.request_timeout:
                        logger.warning(f"Request {request_id} timed out (age: {message_age}s)")
                        error_response = {
                            "success": False,
                            "message": "Request timed out",
                            "error_code": "REQUEST_TIMEOUT"
                        }
                        await self._send_response(message, error_response, request_id)
                        return
                
                # Route request to appropriate handler with timeout
                try:
                    response = await asyncio.wait_for(
                        self._route_request(action, endpoint, data, params),
                        timeout=self.request_timeout
                    )
                except asyncio.TimeoutError:
                    logger.error(f"Request {request_id} processing timed out")
                    response = {
                        "success": False,
                        "message": "Request processing timed out",
                        "error_code": "PROCESSING_TIMEOUT"
                    }
                
                # Add processing metadata
                processing_time = (datetime.utcnow() - start_time).total_seconds()
                response["processing_time"] = processing_time
                response["timestamp"] = datetime.utcnow().isoformat()
                
                # Send response back
                await self._send_response(message, response, request_id)
                
                logger.info(f"Processed request {request_id} in {processing_time:.2f}s")
                
            except Exception as e:
                logger.error(f"Error handling maintenance service request: {e}", exc_info=True)
                error_response = {
                    "success": False,
                    "message": f"Internal server error: {str(e)}",
                    "error_code": "INTERNAL_ERROR",
                    "timestamp": datetime.utcnow().isoformat()
                }
                await self._send_response(message, error_response, request_data.get("request_id") if request_data else None)
                
    async def _route_request(self, action: str, endpoint: str, data: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Route request to appropriate service method"""
        try:
            # Maintenance records endpoints
            if endpoint.startswith("/maintenance/records"):
                return await self._handle_maintenance_records_request(action, endpoint, data, params)
            
            # License records endpoints  
            elif endpoint.startswith("/maintenance/licenses"):
                return await self._handle_license_request(action, endpoint, data, params)
            
            # Analytics endpoints
            elif endpoint.startswith("/maintenance/analytics"):
                return await self._handle_analytics_request(action, endpoint, data, params)
            
            # Notification endpoints
            elif endpoint.startswith("/maintenance/notifications"):
                return await self._handle_notification_request(action, endpoint, data, params)
            
            # Vendor endpoints
            elif endpoint.startswith("/maintenance/vendors"):
                return await self._handle_vendor_request(action, endpoint, data, params)
            
            else:
                return {
                    "success": False,
                    "message": f"Unknown endpoint: {endpoint}",
                    "error_code": "UNKNOWN_ENDPOINT"
                }
                
        except Exception as e:
            logger.error(f"Error routing maintenance request: {e}")
            return {
                "success": False,
                "message": f"Error processing request: {str(e)}",
                "error_code": "PROCESSING_ERROR"
            }
            
    async def _handle_maintenance_records_request(self, action: str, endpoint: str, data: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle maintenance records requests"""
        try:
            if action == "GET":
                if endpoint == "/maintenance/records":
                    # List maintenance records with filters
                    records = await maintenance_records_service.search_maintenance_records(
                        query=params,
                        skip=params.get("skip", 0),
                        limit=params.get("limit", 100),
                        sort_by=params.get("sort_by", "scheduled_date"),
                        sort_order=params.get("sort_order", "desc")
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
                    days_ahead = params.get("days", 7)
                    records = await maintenance_records_service.get_upcoming_maintenance(days_ahead)
                    return {"success": True, "message": "Upcoming maintenance retrieved", "data": records}
                
            elif action == "POST":
                if endpoint == "/maintenance/records":
                    record = await maintenance_records_service.create_maintenance_record(data)
                    return {"success": True, "message": "Maintenance record created", "data": record}
                    
            elif action == "PUT":
                if "/records/" in endpoint:
                    record_id = endpoint.split("/records/")[-1]
                    record = await maintenance_records_service.update_maintenance_record(record_id, data)
                    if record:
                        return {"success": True, "message": "Maintenance record updated", "data": record}
                    else:
                        return {"success": False, "message": "Maintenance record not found", "error_code": "NOT_FOUND"}
                        
            elif action == "DELETE":
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
