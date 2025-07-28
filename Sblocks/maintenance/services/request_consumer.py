"""
Service Request Consumer for Maintenance Service
Handles requests from Core service via RabbitMQ with standardized patterns
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, Any
import aio_pika
from aio_pika.abc import AbstractIncomingMessage

# Import standardized RabbitMQ config
from config.rabbitmq_config import RabbitMQConfig, json_serializer

# Import standardized error handling
from schemas.error_responses import MaintenanceErrorBuilder

logger = logging.getLogger(__name__)

class ServiceRequestConsumer:
    """Handles service requests from Core via RabbitMQ with standardized patterns"""
    
    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = None
        self.queue = None
        # Connection pooling for responses
        self._response_connection = None
        self._response_channel = None
        self._response_exchange = None
        # Use standardized config
        self.config = RabbitMQConfig()
        self.queue_name = self.config.QUEUE_NAMES["maintenance"]
        self.exchange_name = self.config.EXCHANGE_NAMES["requests"]
        self.response_exchange_name = self.config.EXCHANGE_NAMES["responses"]
        # Enhanced request deduplication with timestamps
        self.processed_requests = {}  # correlation_id -> timestamp
        self.request_content_hashes = {}  # content_hash -> correlation_id
        self.is_consuming = False
        
        # Database connectivity caching
        self._db_status_cache = {
            "status": None,
            "last_check": 0,
            "cache_ttl": 30.0  # 30 seconds cache TTL
        }
        
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
            
            # Setup dedicated response connection for better performance
            await self._setup_response_connection()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
    
    async def _setup_response_connection(self):
        """Setup dedicated connection for responses to improve performance"""
        try:
            if not self._response_connection or self._response_connection.is_closed:
                self._response_connection = await aio_pika.connect_robust(
                    url=self.config.get_rabbitmq_url(),
                    heartbeat=self.config.CONNECTION_PARAMS["heartbeat"],
                    blocked_connection_timeout=self.config.CONNECTION_PARAMS["blocked_connection_timeout"]
                )
                self._response_channel = await self._response_connection.channel()
                
                # Declare response exchange
                self._response_exchange = await self._response_channel.declare_exchange(
                    self.response_exchange_name,
                    aio_pika.ExchangeType.DIRECT,
                    durable=True
                )
                
                logger.info("Response connection established")
                
        except Exception as e:
            logger.error(f"Failed to setup response connection: {e}")
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
            
            # Start cleanup task in background
            asyncio.create_task(self._start_cleanup_task())
            
            logger.info(f"Started consuming from {self.queue_name} with cleanup task")
            
        except Exception as e:
            logger.error(f"Error starting consumer: {e}")
            raise
    
    async def stop_consuming(self):
        """Stop consuming messages and close connections"""
        self.is_consuming = False
        
        # Close response connection
        if self._response_connection and not self._response_connection.is_closed:
            await self._response_connection.close()
            
        # Close main connection
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            
        logger.info("Maintenance service request consumer stopped")

    async def disconnect(self):
        """Disconnect from RabbitMQ"""
        self.is_consuming = False
        
        # Close response connection
        if self._response_connection and not self._response_connection.is_closed:
            await self._response_connection.close()
            
        # Close main connection
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
                
                logger.info(f"📨 Received request {request_id}: {method} {endpoint}")
                
                # Extract data from top-level and add to user_context for handlers
                data = request_data.get("data", {})
                user_context["data"] = data
                
                # Enhanced duplicate request checking
                import hashlib
                import json as json_module
                           
                # Create content hash for deduplication
                content_for_hash = {
                    "method": method,
                    "endpoint": endpoint,
                    "data": data,
                    "user_context": {k: v for k, v in user_context.items() if k != "data"}
                }
                content_hash = hashlib.md5(
                    json_module.dumps(content_for_hash, sort_keys=True).encode()
                ).hexdigest()

                # Check for duplicate requests with timestamp tracking
                current_time = time.time()
                if request_id in self.processed_requests:
                    request_age = current_time - self.processed_requests[request_id]
                    if request_age < 300:  # 5 minutes
                        logger.warning(f"Duplicate request ignored (correlation_id): {request_id}")
                        return
                    
                if content_hash in self.request_content_hashes:
                    existing_correlation_id = self.request_content_hashes[content_hash]
                    if existing_correlation_id in self.processed_requests:
                        request_age = current_time - self.processed_requests[existing_correlation_id]
                        if request_age < 60:  # 1 minute for content-based deduplication
                            logger.warning(f"Duplicate request ignored (content hash): {request_id}")
                            return
                    
                self.processed_requests[request_id] = current_time
                self.request_content_hashes[content_hash] = request_id
                
                logger.debug(f"Processing request {request_id}: {method} {endpoint}")
                
                # Route and process request with timeout
                import asyncio
                try:
                    logger.debug(f"🔄 Processing request {request_id}: {method} {endpoint}")
                    response_data = await asyncio.wait_for(
                        self._route_request(method, user_context, endpoint),
                        timeout=self.config.REQUEST_TIMEOUTS.get("default_request_timeout", 25.0)
                    )
                    logger.debug(f"✅ Request {request_id} processed successfully")
                except asyncio.TimeoutError:
                    logger.error(f"⏰ Request {request_id} timed out")
                    raise RuntimeError("Request processing timeout")
                
                # Send successful response
                response = {
                    "status": "success",
                    "data": response_data,
                    "timestamp": datetime.now().isoformat()
                }
                
                logger.debug(f"📤 Sending response for {request_id}")
                await self._send_response(request_id, response)
                logger.info(f"✅ Request {request_id} completed successfully")

        except Exception as e:
            logger.error(f"Error processing request {request_id}: {e}")
            if request_id:
                # Use standardized error response format
                error_response = MaintenanceErrorBuilder.internal_error(
                    message=str(e),
                    error_details={"error_type": type(e).__name__},
                    correlation_id=request_id
                )
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
            
            # Robust endpoint path normalization
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
            elif "schedules" in endpoint:
                return await self._handle_schedules_request(method, user_context)
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
            # Check database connectivity first
            from repositories.database import db_manager
            if not await self._check_database_connectivity():
                return ResponseBuilder.error(
                    error="DatabaseUnavailable",
                    message="Database service is currently unavailable"
                ).model_dump()
            
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
                        data={
                            "maintenance_records": records,
                            "total": len(records),
                            "filter": "overdue"
                        },
                        message="Overdue maintenance retrieved successfully"
                    ).model_dump()
                elif "upcoming" in endpoint:
                    days_ahead = data.get("days", 7)
                    records = await maintenance_records_service.get_upcoming_maintenance(days_ahead)
                    return ResponseBuilder.success(
                        data={
                            "maintenance_records": records,
                            "total": len(records),
                            "days_ahead": days_ahead,
                            "filter": "upcoming"
                        },
                        message="Upcoming maintenance retrieved successfully"
                    ).model_dump()
                elif endpoint.count('/') > 0 and endpoint.split('/')[-1] and endpoint.split('/')[-1] not in ["records", "maintenance"]:
                    # maintenance/records/{id} pattern
                    record_id = endpoint.split('/')[-1]
                    record = await maintenance_records_service.get_maintenance_record(record_id)
                    if record:
                        return ResponseBuilder.success(
                            data={
                                "maintenance_record": record
                            },
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
                        data={
                            "maintenance_records": records,
                            "total": len(records),
                            "pagination": {
                                "skip": data.get("skip", 0),
                                "limit": data.get("limit", 100)
                            },
                            "filters": data
                        },
                        message="Maintenance records retrieved successfully"
                    ).model_dump()
                    
            elif method == "POST":
                if not data:
                    raise ValueError("Request data is required for POST operation")
                
                record = await maintenance_records_service.create_maintenance_record(data)
                return ResponseBuilder.success(
                    data={
                        "maintenance_record": record
                    },
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
                        data={
                            "maintenance_record": record
                        },
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
            # Check database connectivity first
            if not await self._check_database_connectivity():
                from schemas.responses import ResponseBuilder
                return ResponseBuilder.error(
                    error="DatabaseUnavailable",
                    message="Database service is currently unavailable"
                ).model_dump()
            
            # Extract data and endpoint from user_context
            data = user_context.get("data", {})
            endpoint = user_context.get("endpoint", "")
            
            if method == "GET":
                if endpoint == "licenses" or "maintenance/licenses" in endpoint:
                    # License service not implemented yet, return standardized placeholder
                    return ResponseBuilder.success(
                        data={
                            "licenses": [],
                            "total": 0,
                            "message": "License service not yet implemented"
                        },
                        message="License service not yet implemented - GET"
                    ).model_dump()
                else:
                    return ResponseBuilder.success(
                        data={
                            "license": {},
                            "message": "License service not yet implemented"
                        },
                        message="License service not yet implemented - GET specific"
                    ).model_dump()
            elif method == "POST":
                return ResponseBuilder.success(
                    data={
                        "license": {},
                        "message": "License service not yet implemented"
                    },
                    message="License service not yet implemented - POST"
                ).model_dump()
            elif method == "PUT":
                return ResponseBuilder.success(
                    data={
                        "license": {},
                        "message": "License service not yet implemented"
                    },
                    message="License service not yet implemented - PUT"
                ).model_dump()
            elif method == "DELETE":
                return ResponseBuilder.success(
                    data={
                        "deleted": True,
                        "message": "License service not yet implemented"
                    },
                    message="License service not yet implemented - DELETE"
                ).model_dump()
            else:
                raise ValueError(f"Unsupported HTTP method for licenses: {method}")
                
        except Exception as e:
            logger.error(f"Error handling license request {method} {endpoint}: {e}")
            from schemas.responses import ResponseBuilder
            return ResponseBuilder.error(
                error="LicenseRequestError",
                message=f"Failed to process license request: {str(e)}"
            ).model_dump()

    async def _handle_schedules_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle maintenance schedules requests with standardized responses"""
        try:
            # Check database connectivity first
            if not await self._check_database_connectivity():
                from schemas.responses import ResponseBuilder
                return ResponseBuilder.error(
                    error="DatabaseUnavailable",
                    message="Database service is currently unavailable"
                ).model_dump()
            
            # Import required services
            from services.maintenance_service import maintenance_records_service
            from schemas.responses import ResponseBuilder
            
            # Extract data and endpoint from user_context
            data = user_context.get("data", {})
            endpoint = user_context.get("endpoint", "")
            
            if method == "GET":
                # Handle different schedule endpoints
                if "upcoming" in endpoint:
                    # Get upcoming scheduled maintenance
                    days_ahead = data.get("days", 30)  # Default 30 days ahead
                    records = await maintenance_records_service.get_upcoming_maintenance(days_ahead)
                    return ResponseBuilder.success(
                        data={
                            "schedules": records,
                            "total": len(records),
                            "days_ahead": days_ahead
                        },
                        message="Upcoming maintenance schedules retrieved successfully"
                    ).model_dump()
                elif "overdue" in endpoint:
                    # Get overdue scheduled maintenance
                    records = await maintenance_records_service.get_overdue_maintenance()
                    return ResponseBuilder.success(
                        data={
                            "schedules": records,
                            "total": len(records)
                        },
                        message="Overdue maintenance schedules retrieved successfully"
                    ).model_dump()
                elif endpoint.count('/') > 0 and endpoint.split('/')[-1] and endpoint.split('/')[-1] not in ["schedules", "maintenance"]:
                    # Get specific schedule by ID
                    schedule_id = endpoint.split('/')[-1]
                    record = await maintenance_records_service.get_maintenance_record(schedule_id)
                    if record:
                        return ResponseBuilder.success(
                            data={"schedule": record},
                            message="Schedule retrieved successfully"
                        ).model_dump()
                    else:
                        return ResponseBuilder.error(
                            error="NotFound",
                            message="Schedule not found"
                        ).model_dump()
                else:
                    # Get all scheduled maintenance with filters
                    vehicle_id = data.get("vehicle_id")
                    status_filter = data.get("status", "scheduled")
                    
                    # Use maintenance service to get filtered records
                    if vehicle_id:
                        records = await maintenance_records_service.get_maintenance_by_vehicle(vehicle_id)
                    else:
                        records = await maintenance_records_service.get_maintenance_by_status(status_filter)
                    
                    return ResponseBuilder.success(
                        data={
                            "schedules": records,
                            "total": len(records),
                            "filters": {
                                "vehicle_id": vehicle_id,
                                "status": status_filter
                            }
                        },
                        message="Maintenance schedules retrieved successfully"
                    ).model_dump()
                    
            elif method == "POST":
                # Create new maintenance schedule
                if not data:
                    raise ValueError("Schedule data is required for POST operation")
                
                record = await maintenance_records_service.create_maintenance_record(data)
                return ResponseBuilder.success(
                    data={"schedule": record},
                    message="Maintenance schedule created successfully"
                ).model_dump()
                
            elif method == "PUT":
                # Update existing schedule
                schedule_id = endpoint.split('/')[-1] if '/' in endpoint else None
                if not schedule_id:
                    raise ValueError("Schedule ID is required for PUT operation")
                if not data:
                    raise ValueError("Schedule data is required for PUT operation")
                
                record = await maintenance_records_service.update_maintenance_record(schedule_id, data)
                if record:
                    return ResponseBuilder.success(
                        data={"schedule": record},
                        message="Maintenance schedule updated successfully"
                    ).model_dump()
                else:
                    return ResponseBuilder.error(
                        error="NotFound",
                        message="Schedule not found"
                    ).model_dump()
                    
            elif method == "DELETE":
                # Delete schedule
                schedule_id = endpoint.split('/')[-1] if '/' in endpoint else None
                if not schedule_id:
                    raise ValueError("Schedule ID is required for DELETE operation")
                
                success = await maintenance_records_service.delete_maintenance_record(schedule_id)
                if success:
                    return ResponseBuilder.success(
                        data={"deleted": True, "schedule_id": schedule_id},
                        message="Maintenance schedule deleted successfully"
                    ).model_dump()
                else:
                    return ResponseBuilder.error(
                        error="NotFound",
                        message="Schedule not found"
                    ).model_dump()
                    
            else:
                raise ValueError(f"Unsupported HTTP method for schedules: {method}")
                
        except Exception as e:
            logger.error(f"Error handling schedules request {method} {endpoint}: {e}")
            from schemas.responses import ResponseBuilder
            return ResponseBuilder.error(
                error="SchedulesRequestError",
                message=f"Failed to process schedules request: {str(e)}"
            ).model_dump()
    
    async def _handle_analytics_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle analytics-related requests"""
        try:
            # Check database connectivity first
            if not await self._check_database_connectivity():
                from schemas.responses import ResponseBuilder
                return ResponseBuilder.error(
                    error="DatabaseUnavailable",
                    message="Database service is currently unavailable"
                ).model_dump()
            
            # Extract data and endpoint from user_context
            data = user_context.get("data", {})
            endpoint = user_context.get("endpoint", "")
            
            if method == "GET":
                # Standardized analytics response structure
                return ResponseBuilder.success(
                    data={
                        "analytics": {
                            "maintenance_summary": {},
                            "cost_analysis": {},
                            "performance_metrics": {},
                            "trends": {}
                        },
                        "message": "Analytics service not yet implemented"
                    },
                    message="Analytics service not yet implemented"
                ).model_dump()
            else:
                raise ValueError(f"Unsupported HTTP method for analytics: {method}")
                
        except Exception as e:
            logger.error(f"Error handling analytics request {method} {endpoint}: {e}")
            from schemas.responses import ResponseBuilder
            return ResponseBuilder.error(
                error="AnalyticsRequestError",
                message=f"Failed to process analytics request: {str(e)}"
            ).model_dump()
    
    async def _handle_notification_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle notification-related requests"""
        try:
            # Check database connectivity first
            if not await self._check_database_connectivity():
                from schemas.responses import ResponseBuilder
                return ResponseBuilder.error(
                    error="DatabaseUnavailable",
                    message="Database service is currently unavailable"
                ).model_dump()
            
            # Extract data and endpoint from user_context
            data = user_context.get("data", {})
            endpoint = user_context.get("endpoint", "")
            
            if method == "GET":
                return ResponseBuilder.success(
                    data={
                        "notifications": [],
                        "total": 0,
                        "message": "Notification service not yet implemented"
                    },
                    message="Notification service not yet implemented"
                ).model_dump()
            elif method == "POST":
                return ResponseBuilder.success(
                    data={
                        "notification": {},
                        "message": "Notification service not yet implemented"
                    },
                    message="Notification service not yet implemented - POST"
                ).model_dump()
            elif method == "PUT":
                return ResponseBuilder.success(
                    data={
                        "notification": {},
                        "message": "Notification service not yet implemented"
                    },
                    message="Notification service not yet implemented - PUT"
                ).model_dump()
            else:
                raise ValueError(f"Unsupported HTTP method for notifications: {method}")
                
        except Exception as e:
            logger.error(f"Error handling notification request {method} {endpoint}: {e}")
            from schemas.responses import ResponseBuilder
            return ResponseBuilder.error(
                error="NotificationRequestError",
                message=f"Failed to process notification request: {str(e)}"
            ).model_dump()
    
    async def _handle_vendor_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle vendor-related requests"""
        try:
            # Check database connectivity first
            if not await self._check_database_connectivity():
                from schemas.responses import ResponseBuilder
                return ResponseBuilder.error(
                    error="DatabaseUnavailable",
                    message="Database service is currently unavailable"
                ).model_dump()
            
            # Extract data and endpoint from user_context
            data = user_context.get("data", {})
            endpoint = user_context.get("endpoint", "")
            
            # Vendor endpoints not yet implemented - return standardized placeholder
            return ResponseBuilder.error(
                error="NotImplemented",
                message="Vendor endpoints not yet implemented",
                status_code=501
            ).model_dump()
            
        except Exception as e:
            logger.error(f"Error handling vendor request {method}: {e}")
            from schemas.responses import ResponseBuilder
            return ResponseBuilder.error(
                error="VendorRequestError",
                message=f"Failed to process vendor request: {str(e)}"
            ).model_dump()
    
    async def _handle_health_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle health check requests"""
        logger.debug(f"Handling health request: {method}")
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
        """Send response back to Core via RabbitMQ using main connection to avoid event loop issues"""
        try:
            # Use main connection and exchange to avoid event loop issues
            # Prepare response message
            response_msg = {
                "correlation_id": correlation_id,
                "status": "success",
                "data": response_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Send response using main channel and exchange
            message = aio_pika.Message(
                json.dumps(response_msg, default=json_serializer).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                content_type="application/json",
                headers={
                    'timestamp': datetime.utcnow().isoformat(),
                    'source': 'maintenance_service'
                }
            )
            
            await self.response_exchange.publish(message, routing_key=self.config.ROUTING_KEYS["core_responses"])
            
            logger.debug(f"📤 Sent response for correlation_id: {correlation_id}")
            
        except Exception as e:
            logger.error(f"❌ Error sending response for {correlation_id}: {e}")
            raise
    
    async def _send_error_response(self, correlation_id: str, error_message: str):
        """Send error response back to Core using main connection to avoid event loop issues"""
        try:
            # Use main connection and exchange to avoid event loop issues
            response_msg = {
                "correlation_id": correlation_id,
                "status": "error",
                "error": {
                    "message": error_message,
                    "type": "ServiceError"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            message = aio_pika.Message(
                json.dumps(response_msg, default=json_serializer).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                content_type="application/json",
                headers={
                    'timestamp': datetime.utcnow().isoformat(),
                    'source': 'maintenance_service'
                }
            )
            
            await self.response_exchange.publish(message, routing_key=self.config.ROUTING_KEYS["core_responses"])
            
            logger.debug(f"📤 Sent error response for correlation_id: {correlation_id}")
            
        except Exception as e:
            logger.error(f"❌ Error sending error response for {correlation_id}: {e}")
    
    async def _check_database_connectivity(self) -> bool:
        """Check database connectivity with caching to improve performance"""
        current_time = time.time()
        
        # Check if we have a cached result that's still valid
        if (self._db_status_cache["status"] is not None and 
            current_time - self._db_status_cache["last_check"] < self._db_status_cache["cache_ttl"]):
            return self._db_status_cache["status"]
        
        try:
            from repositories.database import db_manager
            
            # Perform database health check with timeout
            await asyncio.wait_for(
                db_manager.client.admin.command('ping'),
                timeout=5.0  # Quick timeout for health check
            )
            
            # Cache successful result
            self._db_status_cache.update({
                "status": True,
                "last_check": current_time
            })
            return True
                
        except Exception as e:
            logger.warning(f"Database connectivity check failed: {e}")
            # Cache failed result
            self._db_status_cache.update({
                "status": False,
                "last_check": current_time
            })
            return False
    
    async def _cleanup_old_requests(self):
        """Cleanup old request data to prevent memory leaks"""
        try:
            current_time = time.time()
            cleanup_threshold = 3600  # 1 hour
            
            # Clean up old processed requests
            old_requests = [
                req_id for req_id, timestamp in self.processed_requests.items()
                if current_time - timestamp > cleanup_threshold
            ]
            
            for req_id in old_requests:
                del self.processed_requests[req_id]
            
            if old_requests:
                logger.info(f"🧹 Cleaned up {len(old_requests)} old processed requests")
                
        except Exception as e:
            logger.error(f"❌ Error during request cleanup: {e}")
    
    async def _start_cleanup_task(self):
        """Start periodic cleanup task"""
        while self.is_consuming:
            try:
                await asyncio.sleep(1800)  # Run every 30 minutes
                await self._cleanup_old_requests()
            except Exception as e:
                logger.error(f"❌ Error in cleanup task: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
 

# Global service instance
service_request_consumer = ServiceRequestConsumer()
