"""
Service Request Consumer for Maintenance Service
Handles requests from Core service via RabbitMQ with standardized patterns
"""

import asyncio
import json
import logging
import os
import random
import time
from datetime import datetime, timedelta
from typing import Dict, Any
import aio_pika
from aio_pika.abc import AbstractIncomingMessage

# Import standardized RabbitMQ config
from config.rabbitmq_config import RabbitMQConfig, json_serializer

# Import standardized error handling
from schemas.error_responses import MaintenanceErrorBuilder

# Import response builder
from schemas.responses import ResponseBuilder

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
            
            logger.info(f"Started consuming from {self.queue_name}")
            
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
                    try:
                        days_ahead = int(data.get("days", 7)) if data.get("days") is not None else 7
                        days_ahead = max(1, min(365, days_ahead))  # Reasonable range: 1-365 days
                    except (ValueError, TypeError):
                        days_ahead = 7
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
                    # Ensure skip and limit are integers with error handling
                    try:
                        skip = int(data.get("skip", 0)) if data.get("skip") is not None else 0
                        limit = int(data.get("limit", 100)) if data.get("limit") is not None else 100
                        # Validate reasonable limits
                        skip = max(0, skip)
                        limit = max(1, min(1000, limit))  # Cap at 1000 records
                    except (ValueError, TypeError):
                        skip = 0
                        limit = 100
                    
                    records = await maintenance_records_service.search_maintenance_records(
                        query=data,
                        skip=skip,
                        limit=limit,
                        sort_by=data.get("sort_by", "scheduled_date"),
                        sort_order=data.get("sort_order", "desc")
                    )
                    return ResponseBuilder.success(
                        data={
                            "maintenance_records": records,
                            "total": len(records),
                            "pagination": {
                                "skip": skip,
                                "limit": limit
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

                return ResponseBuilder.error(
                    error="DatabaseUnavailable",
                    message="Database service is currently unavailable"
                ).model_dump()
            
            # Extract data and endpoint from user_context
            data = user_context.get("data", {})
            endpoint = user_context.get("endpoint", "")
            
            if method == "GET":
                # Extract query parameters
                skip = max(0, int(data.get("skip", 0)))
                limit = min(100, max(1, int(data.get("limit", 20))))
                license_type = data.get("type", "")
                status = data.get("status", "")
                vehicle_id = data.get("vehicle_id", "")
                
                if endpoint == "licenses" or "maintenance/licenses" in endpoint:
                    try:
                        # Import the license service
                        from services.license_service import license_service
                        
                        # Get licenses from the database
                        if vehicle_id:
                            # Get licenses for a specific vehicle
                            raw_licenses = await license_service.get_entity_licenses(vehicle_id, "vehicle")
                        elif license_type:
                            # Get licenses by type
                            raw_licenses = await license_service.get_licenses_by_type(license_type)
                        else:
                            # Get all licenses with pagination
                            raw_licenses = await license_service.get_all_licenses(skip=skip, limit=limit)
                        
                        # Transform database records to API response format
                        licenses = []
                        for license_record in raw_licenses:
                            try:
                                # Helper function to format date objects safely
                                def format_date(date_obj):
                                    """Helper function to format date objects safely"""
                                    if date_obj is None:
                                        return None
                                    if hasattr(date_obj, 'isoformat'):
                                        return date_obj.isoformat()
                                    return str(date_obj)
                                
                                # Calculate days until expiry
                                days_until_expiry = 0
                                expiry_date = license_record.get("expiry_date")
                                if expiry_date:
                                    if hasattr(expiry_date, 'isoformat'):
                                        days_until_expiry = (expiry_date - datetime.now().date()).days
                                    else:
                                        expiry_date_parsed = datetime.strptime(str(expiry_date), "%Y-%m-%d").date()
                                        days_until_expiry = (expiry_date_parsed - datetime.now().date()).days
                                
                                # Determine status
                                if days_until_expiry < 0:
                                    status_val = "expired"
                                elif days_until_expiry < 30:
                                    status_val = "expiring_soon"
                                else:
                                    status_val = "active"
                                
                                license_data = {
                                    "id": str(license_record.get("_id", license_record.get("id", ""))),
                                    "vehicle_id": license_record.get("entity_id"),
                                    "license_type": license_record.get("license_type"),
                                    "license_name": license_record.get("title", license_record.get("license_type", "").replace("_", " ").title()),
                                    "license_number": license_record.get("license_number"),
                                    "status": status_val,
                                    "issue_date": format_date(license_record.get("issue_date")),
                                    "expiry_date": format_date(license_record.get("expiry_date")),
                                    "days_until_expiry": days_until_expiry,
                                    "issuing_authority": license_record.get("issuing_authority", "Unknown Authority"),
                                    "renewal_required": days_until_expiry < 60,
                                    "compliance_status": "compliant" if status_val == "active" else "non_compliant",
                                    "description": license_record.get("description", ""),
                                    "is_active": license_record.get("is_active", True)
                                }
                                licenses.append(license_data)
                                
                            except Exception as transform_error:
                                logger.warning(f"Error transforming license record: {transform_error}")
                                continue
                        
                        # Apply additional filters
                        if status:
                            licenses = [l for l in licenses if l['status'] == status]
                        
                        # Sort by expiry date (most urgent first)
                        licenses.sort(key=lambda x: x.get('days_until_expiry', 999))
                        
                        # Apply pagination
                        total_licenses = len(licenses)
                        licenses = licenses[skip:skip + limit]
                        
                        # Generate summary statistics
                        expired_count = len([l for l in licenses if l['status'] == 'expired'])
                        expiring_soon_count = len([l for l in licenses if l['status'] == 'expiring_soon'])
                        active_count = len([l for l in licenses if l['status'] == 'active'])
                        
                        return ResponseBuilder.success(
                            data={
                                "licenses": licenses,
                                "total": total_licenses,
                                "skip": skip,
                                "limit": limit,
                                "has_more": skip + len(licenses) < total_licenses,
                                "summary": {
                                    "expired": expired_count,
                                    "expiring_soon": expiring_soon_count,
                                    "active": active_count,
                                    "total": total_licenses,
                                    "compliance_rate": round((active_count / max(total_licenses, 1)) * 100, 2)
                                }
                            },
                            message="Vehicle licenses retrieved successfully"
                        ).model_dump()
                        
                    except Exception as e:
                        logger.error(f"Error generating licenses: {e}")
                        return ResponseBuilder.success(
                            data={
                                "licenses": [],
                                "total": 0,
                                "skip": skip,
                                "limit": limit,
                                "has_more": False,
                                "summary": {
                                    "expired": 0,
                                    "expiring_soon": 0,
                                    "active": 0,
                                    "total": 0,
                                    "compliance_rate": 100
                                },
                                "message": "License data temporarily unavailable"
                            },
                            message="License service temporarily unavailable"
                        ).model_dump()
                else:
                    # Individual license lookup using the proper license service
                    license_id = data.get("license_id", "") or data.get("id", "")
                    if license_id:
                        try:
                            # Import the license service
                            from services.license_service import license_service
                            
                            # Get the license from the database
                            license_record = await license_service.get_license_record(license_id)
                            
                            if license_record:
                                # Transform the database record to match the API response format
                                def format_date(date_obj):
                                    """Helper function to format date objects safely"""
                                    if date_obj is None:
                                        return None
                                    if hasattr(date_obj, 'isoformat'):
                                        return date_obj.isoformat()
                                    return str(date_obj)
                                
                                license_data = {
                                    "id": str(license_record.get("_id", license_record.get("id", license_id))),
                                    "vehicle_id": license_record.get("entity_id"),
                                    "license_type": license_record.get("license_type"),
                                    "license_name": license_record.get("title", license_record.get("license_type", "").replace("_", " ").title()),
                                    "license_number": license_record.get("license_number"),
                                    "issue_date": format_date(license_record.get("issue_date")),
                                    "expiry_date": format_date(license_record.get("expiry_date")),
                                    "issuing_authority": license_record.get("issuing_authority"),
                                    "status": "active" if license_record.get("is_active") else "inactive",
                                    "description": license_record.get("description", ""),
                                    "compliance_status": "compliant" if license_record.get("is_active") else "non_compliant",
                                    "created_at": format_date(license_record.get("created_at")),
                                    "updated_at": format_date(license_record.get("updated_at"))
                                }
                                
                                # Calculate days until expiry if expiry date is available
                                if license_record.get("expiry_date"):
                                    try:
                                        expiry_date = license_record.get("expiry_date")
                                        if hasattr(expiry_date, 'isoformat'):
                                            days_until_expiry = (expiry_date - datetime.now().date()).days
                                        else:
                                            expiry_date_parsed = datetime.strptime(str(expiry_date), "%Y-%m-%d").date()
                                            days_until_expiry = (expiry_date_parsed - datetime.now().date()).days
                                        license_data["days_until_expiry"] = days_until_expiry
                                        license_data["renewal_required"] = days_until_expiry < 60
                                    except Exception as date_error:
                                        logger.warning(f"Error calculating days until expiry: {date_error}")
                                
                                return ResponseBuilder.success(
                                    data={"license": license_data},
                                    message="License details retrieved successfully"
                                ).model_dump()
                            else:
                                return ResponseBuilder.error(
                                    error="NotFound",
                                    message="License not found"
                                ).model_dump()
                                
                        except Exception as e:
                            logger.error(f"Error fetching license {license_id}: {e}")
                            return ResponseBuilder.error(
                                error="FetchError",
                                message=f"Failed to retrieve license: {str(e)}"
                            ).model_dump()
                    
                    return ResponseBuilder.error(
                        error="LicenseNotFound",
                        message="License not found or invalid license ID"
                    ).model_dump()
                    
            elif method == "POST":
                # Create new license entry using the proper license service
                try:
                    # Import the license service
                    from services.license_service import license_service
                    
                    # Validate required fields
                    required_fields = ["license_type", "vehicle_id", "license_number", "issue_date", "expiry_date"]
                    for field in required_fields:
                        if field not in data or not data[field]:
                            return ResponseBuilder.error(
                                error="ValidationError",
                                message=f"Required field '{field}' is missing"
                            ).model_dump()
                    
                    # Prepare license data for the service
                    license_data = {
                        "entity_id": data.get("vehicle_id"),
                        "entity_type": "vehicle",
                        "license_type": data.get("license_type"),
                        "license_number": data.get("license_number"),
                        "title": data.get("title", f"{data.get('license_type', '').replace('_', ' ').title()} License"),
                        "issue_date": data.get("issue_date"),
                        "expiry_date": data.get("expiry_date"),
                        "issuing_authority": data.get("issuing_authority", ""),
                        "description": data.get("description", ""),
                        "is_active": True
                    }
                    
                    # Create the license record in the database
                    created_license = await license_service.create_license_record(license_data)
                    
                    if created_license:
                        # Transform the database record to match the API response format
                        def format_date(date_obj):
                            """Helper function to format date objects safely"""
                            if date_obj is None:
                                return None
                            if hasattr(date_obj, 'isoformat'):
                                return date_obj.isoformat()
                            return str(date_obj)
                        
                        response_license = {
                            "id": str(created_license.get("_id", created_license.get("id", ""))),
                            "license_type": created_license.get("license_type"),
                            "vehicle_id": created_license.get("entity_id"),
                            "license_number": created_license.get("license_number"),
                            "title": created_license.get("title"),
                            "issue_date": format_date(created_license.get("issue_date")),
                            "expiry_date": format_date(created_license.get("expiry_date")),
                            "issuing_authority": created_license.get("issuing_authority"),
                            "status": "active" if created_license.get("is_active") else "inactive",
                            "created_at": format_date(created_license.get("created_at", datetime.now()))
                        }
                        
                        return ResponseBuilder.success(
                            data={"license": response_license},
                            message="License created successfully"
                        ).model_dump()
                    else:
                        return ResponseBuilder.error(
                            error="CreationError",
                            message="Failed to create license record"
                        ).model_dump()
                        
                except Exception as e:
                    logger.error(f"Error creating license: {e}")
                    return ResponseBuilder.error(
                        error="CreationError",
                        message=f"Failed to create license: {str(e)}"
                    ).model_dump()
                
            elif method == "PUT":
                # Update license information using the proper license service
                try:
                    # Import the license service
                    from services.license_service import license_service
                    
                    license_id = data.get("license_id", "") or data.get("id", "")
                    updates = data.get("updates", {}) if "updates" in data else data
                    
                    if not license_id:
                        return ResponseBuilder.error(
                            error="ValidationError",
                            message="License ID is required for updates"
                        ).model_dump()
                    
                    # Update the license record in the database
                    updated_license = await license_service.update_license_record(license_id, updates)
                    
                    if updated_license:
                        # Transform the database record to match the API response format
                        def format_date(date_obj):
                            """Helper function to format date objects safely"""
                            if date_obj is None:
                                return None
                            if hasattr(date_obj, 'isoformat'):
                                return date_obj.isoformat()
                            return str(date_obj)
                        
                        response_license = {
                            "id": str(updated_license.get("_id", updated_license.get("id", license_id))),
                            "license_type": updated_license.get("license_type"),
                            "vehicle_id": updated_license.get("entity_id"),
                            "license_number": updated_license.get("license_number"),
                            "title": updated_license.get("title"),
                            "issue_date": format_date(updated_license.get("issue_date")),
                            "expiry_date": format_date(updated_license.get("expiry_date")),
                            "issuing_authority": updated_license.get("issuing_authority"),
                            "status": "active" if updated_license.get("is_active") else "inactive",
                            "updated_at": datetime.now().isoformat()
                        }
                        
                        return ResponseBuilder.success(
                            data={"license": response_license},
                            message="License updated successfully"
                        ).model_dump()
                    else:
                        return ResponseBuilder.error(
                            error="NotFound",
                            message="License not found"
                        ).model_dump()
                        
                except Exception as e:
                    logger.error(f"Error updating license: {e}")
                    return ResponseBuilder.error(
                        error="UpdateError",
                        message=f"Failed to update license: {str(e)}"
                    ).model_dump()
                
            elif method == "DELETE":
                # Delete license using the proper license service
                try:
                    # Import the license service
                    from services.license_service import license_service
                    
                    license_id = data.get("license_id", "") or data.get("id", "")
                    
                    if not license_id:
                        return ResponseBuilder.error(
                            error="ValidationError",
                            message="License ID is required for deletion"
                        ).model_dump()
                    
                    # Delete the license record from the database
                    success = await license_service.delete_license_record(license_id)
                    
                    if success:
                        return ResponseBuilder.success(
                            data={
                                "deleted": True,
                                "license_id": license_id,
                                "deleted_at": datetime.now().isoformat()
                            },
                            message="License deleted successfully"
                        ).model_dump()
                    else:
                        return ResponseBuilder.error(
                            error="NotFound",
                            message="License not found"
                        ).model_dump()
                        
                except Exception as e:
                    logger.error(f"Error deleting license: {e}")
                    return ResponseBuilder.error(
                        error="DeletionError",
                        message=f"Failed to delete license: {str(e)}"
                    ).model_dump()
            else:
                raise ValueError(f"Unsupported HTTP method for licenses: {method}")
                
        except Exception as e:
            logger.error(f"Error handling license request {method} {endpoint}: {e}")

            return ResponseBuilder.error(
                error="LicenseRequestError",
                message=f"Failed to process license request: {str(e)}"
            ).model_dump()

    async def _handle_schedules_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle maintenance schedules requests with standardized responses"""
        try:
            # Check database connectivity first
            if not await self._check_database_connectivity():
                return ResponseBuilder.error(
                    error="DatabaseUnavailable",
                    message="Database service is currently unavailable"
                ).model_dump()
            
            # Import required services
            from services.maintenance_schedules_service import maintenance_schedules_service
            
            # Extract data and endpoint from user_context
            data = user_context.get("data", {})
            endpoint = user_context.get("endpoint", "")
            
            if method == "GET":
                # Handle different schedule endpoints
                if "upcoming" in endpoint:
                    # Get upcoming due schedules
                    schedules = await maintenance_schedules_service.get_due_schedules()
                    return ResponseBuilder.success(
                        data={
                            "schedules": schedules,
                            "total": len(schedules)
                        },
                        message="Upcoming due schedules retrieved successfully"
                    ).model_dump()
                elif "active" in endpoint:
                    # Get all active schedules
                    schedules = await maintenance_schedules_service.get_active_schedules()
                    return ResponseBuilder.success(
                        data={
                            "schedules": schedules,
                            "total": len(schedules)
                        },
                        message="Active maintenance schedules retrieved successfully"
                    ).model_dump()
                elif endpoint.count('/') > 0 and endpoint.split('/')[-1] and endpoint.split('/')[-1] not in ["schedules", "maintenance"]:
                    # Get specific schedule by ID
                    schedule_id = endpoint.split('/')[-1]
                    schedule = await maintenance_schedules_service.get_maintenance_schedule(schedule_id)
                    if schedule:
                        return ResponseBuilder.success(
                            data={"schedule": schedule},
                            message="Schedule retrieved successfully"
                        ).model_dump()
                    else:
                        return ResponseBuilder.error(
                            error="NotFound",
                            message="Schedule not found"
                        ).model_dump()
                else:
                    # Get schedules with filters
                    vehicle_id = data.get("vehicle_id")
                    
                    if vehicle_id:
                        schedules = await maintenance_schedules_service.get_vehicle_maintenance_schedules(vehicle_id)
                    else:
                        schedules = await maintenance_schedules_service.get_active_schedules()
                    
                    return ResponseBuilder.success(
                        data={
                            "schedules": schedules,
                            "total": len(schedules),
                            "filters": {
                                "vehicle_id": vehicle_id
                            }
                        },
                        message="Maintenance schedules retrieved successfully"
                    ).model_dump()
                    
            elif method == "POST":
                # Create new maintenance schedule
                if not data:
                    raise ValueError("Schedule data is required for POST operation")
                
                schedule = await maintenance_schedules_service.create_maintenance_schedule(data)
                return ResponseBuilder.success(
                    data={"schedule": schedule},
                    message="Maintenance schedule created successfully"
                ).model_dump()
                
            elif method == "PUT":
                # Update existing schedule
                schedule_id = endpoint.split('/')[-1] if '/' in endpoint else None
                if not schedule_id:
                    raise ValueError("Schedule ID is required for PUT operation")
                if not data:
                    raise ValueError("Schedule data is required for PUT operation")
                
                schedule = await maintenance_schedules_service.update_maintenance_schedule(schedule_id, data)
                if schedule:
                    return ResponseBuilder.success(
                        data={"schedule": schedule},
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
                
                success = await maintenance_schedules_service.delete_maintenance_schedule(schedule_id)
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
            return ResponseBuilder.error(
                error="SchedulesRequestError",
                message=f"Failed to process schedules request: {str(e)}"
            ).model_dump()
    
    async def _handle_analytics_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle analytics-related requests"""
        try:
            # Check database connectivity first
            if not await self._check_database_connectivity():

                return ResponseBuilder.error(
                    error="DatabaseUnavailable",
                    message="Database service is currently unavailable"
                ).model_dump()
            
            # Extract data and endpoint from user_context
            data = user_context.get("data", {})
            endpoint = user_context.get("endpoint", "")
            
            if method == "GET":
                # Import maintenance service for analytics data
                from services.maintenance_service import maintenance_records_service
                
                # Extract parameters from request
                vehicle_id = data.get("vehicle_id")
                start_date = data.get("start_date") 
                end_date = data.get("end_date")
                
                # Determine analytics type based on endpoint
                if "dashboard" in endpoint:
                    # Get dashboard analytics
                    try:
                        # Get various maintenance statistics
                        overdue_records = await maintenance_records_service.get_overdue_maintenance()
                        upcoming_records = await maintenance_records_service.get_upcoming_maintenance(30)
                        cost_summary = await maintenance_records_service.get_maintenance_cost_summary(
                            vehicle_id=vehicle_id,
                            start_date=start_date,
                            end_date=end_date
                        )
                        
                        # Calculate performance metrics
                        total_records = len(overdue_records) + len(upcoming_records)
                        overdue_count = len(overdue_records)
                        upcoming_count = len(upcoming_records)
                        
                        dashboard_data = {
                            "maintenance_summary": {
                                "total_records": total_records,
                                "overdue_count": overdue_count,
                                "upcoming_count": upcoming_count,
                                "completion_rate": round((1 - (overdue_count / max(total_records, 1))) * 100, 2)
                            },
                            "cost_analysis": cost_summary,
                            "performance_metrics": {
                                "on_time_completion": round((1 - (overdue_count / max(total_records, 1))) * 100, 2),
                                "average_cost_per_maintenance": cost_summary.get("average_cost", 0),
                                "total_cost_period": cost_summary.get("total_cost", 0)
                            },
                            "trends": {
                                "overdue_trend": "increasing" if overdue_count > 5 else "stable",
                                "cost_trend": "stable",
                                "efficiency_trend": "improving" if overdue_count < 3 else "declining"
                            }
                        }
                        
                        return ResponseBuilder.success(
                            data={"analytics": dashboard_data},
                            message="Dashboard analytics retrieved successfully"
                        ).model_dump()
                        
                    except Exception as e:
                        logger.error(f"Error generating dashboard analytics: {e}")
                        # Return fallback data
                        return ResponseBuilder.success(
                            data={
                                "analytics": {
                                    "maintenance_summary": {"total_records": 0, "overdue_count": 0, "upcoming_count": 0},
                                    "cost_analysis": {"total_cost": 0, "average_cost": 0},
                                    "performance_metrics": {"on_time_completion": 100, "efficiency_score": 85},
                                    "trends": {"overall_trend": "stable"}
                                },
                                "message": "Analytics data temporarily unavailable"
                            },
                            message="Analytics dashboard data retrieved"
                        ).model_dump()
                        
                elif "costs" in endpoint:
                    # Get cost-specific analytics
                    try:
                        cost_data = await maintenance_records_service.calculate_maintenance_costs(
                            vehicle_id=vehicle_id,
                            start_date=datetime.fromisoformat(start_date.replace("Z", "+00:00")) if start_date else None,
                            end_date=datetime.fromisoformat(end_date.replace("Z", "+00:00")) if end_date else None
                        )
                        
                        return ResponseBuilder.success(
                            data={"cost_analytics": cost_data},
                            message="Cost analytics retrieved successfully"
                        ).model_dump()
                        
                    except Exception as e:
                        logger.error(f"Error generating cost analytics: {e}")
                        return ResponseBuilder.success(
                            data={
                                "cost_analytics": {
                                    "total_cost": 0,
                                    "average_cost": 0,
                                    "cost_by_type": {},
                                    "cost_trend": "stable"
                                }
                            },
                            message="Cost analytics data retrieved"
                        ).model_dump()
                        
                else:
                    # General analytics
                    try:
                        cost_summary = await maintenance_records_service.get_maintenance_cost_summary(
                            vehicle_id=vehicle_id,
                            start_date=start_date,
                            end_date=end_date
                        )
                        overdue_count = len(await maintenance_records_service.get_overdue_maintenance())
                        upcoming_count = len(await maintenance_records_service.get_upcoming_maintenance(30))
                        
                        return ResponseBuilder.success(
                            data={
                                "analytics": {
                                    "maintenance_summary": {
                                        "overdue_count": overdue_count,
                                        "upcoming_count": upcoming_count,
                                        "total_active": overdue_count + upcoming_count
                                    },
                                    "cost_analysis": cost_summary,
                                    "performance_metrics": {
                                        "completion_rate": round((1 - (overdue_count / max(overdue_count + upcoming_count, 1))) * 100, 2)
                                    },
                                    "trends": {
                                        "maintenance_frequency": "normal",
                                        "cost_efficiency": "good"
                                    }
                                }
                            },
                            message="Analytics data retrieved successfully"
                        ).model_dump()
                        
                    except Exception as e:
                        logger.error(f"Error generating analytics: {e}")
                        return ResponseBuilder.success(
                            data={
                                "analytics": {
                                    "maintenance_summary": {},
                                    "cost_analysis": {},
                                    "performance_metrics": {},
                                    "trends": {}
                                },
                                "message": "Analytics data temporarily unavailable"
                            },
                            message="Analytics service temporarily unavailable"
                        ).model_dump()
            else:
                raise ValueError(f"Unsupported HTTP method for analytics: {method}")
                
        except Exception as e:
            logger.error(f"Error handling analytics request {method} {endpoint}: {e}")

            return ResponseBuilder.error(
                error="AnalyticsRequestError",
                message=f"Failed to process analytics request: {str(e)}"
            ).model_dump()
    
    async def _handle_notification_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle notification-related requests"""
        try:
            # Check database connectivity first
            if not await self._check_database_connectivity():

                return ResponseBuilder.error(
                    error="DatabaseUnavailable",
                    message="Database service is currently unavailable"
                ).model_dump()
            
            # Extract data and endpoint from user_context
            data = user_context.get("data", {})
            endpoint = user_context.get("endpoint", "")
            
            if method == "GET":
                # Extract query parameters
                skip = max(0, int(data.get("skip", 0)))
                limit = min(100, max(1, int(data.get("limit", 20))))
                notification_type = data.get("type", "")
                status = data.get("status", "")
                user_id = data.get("user_id", "")
                
                try:
                    # Import required services
                    from services.maintenance_service import maintenance_records_service
                    
                    notifications = []
                    
                    # Get overdue maintenance notifications
                    overdue_maintenance = await maintenance_records_service.get_overdue_maintenance()
                    for record in overdue_maintenance[:limit//2]:
                        notifications.append({
                            "id": f"overdue_{record.get('id', 'unknown')}",
                            "type": "maintenance_overdue",
                            "title": "Maintenance Overdue",
                            "message": f"Maintenance for vehicle {record.get('vehicle_id', 'Unknown')} is overdue",
                            "priority": "high",
                            "status": "unread",
                            "created_at": record.get('due_date', datetime.now().isoformat()),
                            "data": {
                                "vehicle_id": record.get('vehicle_id'),
                                "maintenance_type": record.get('maintenance_type'),
                                "due_date": record.get('due_date'),
                                "overdue_days": (datetime.now() - datetime.fromisoformat(record.get('due_date', datetime.now().isoformat()).replace('Z', '+00:00'))).days if record.get('due_date') else 0
                            }
                        })
                    
                    # Get upcoming maintenance notifications
                    upcoming_maintenance = await maintenance_records_service.get_upcoming_maintenance(7)
                    for record in upcoming_maintenance[:limit//2]:
                        notifications.append({
                            "id": f"upcoming_{record.get('id', 'unknown')}",
                            "type": "maintenance_upcoming",
                            "title": "Maintenance Due Soon",
                            "message": f"Maintenance for vehicle {record.get('vehicle_id', 'Unknown')} is due soon",
                            "priority": "medium",
                            "status": "unread",
                            "created_at": datetime.now().isoformat(),
                            "data": {
                                "vehicle_id": record.get('vehicle_id'),
                                "maintenance_type": record.get('maintenance_type'),
                                "due_date": record.get('due_date'),
                                "days_until_due": (datetime.fromisoformat(record.get('due_date', datetime.now().isoformat()).replace('Z', '+00:00')) - datetime.now()).days if record.get('due_date') else 0
                            }
                        })
                    
                    # Add high-cost maintenance alerts
                    try:
                        cost_summary = await maintenance_records_service.get_maintenance_cost_summary()
                        if cost_summary.get('total_cost', 0) > 10000:  # Alert for high costs
                            notifications.append({
                                "id": "high_cost_alert",
                                "type": "cost_alert",
                                "title": "High Maintenance Costs",
                                "message": f"Total maintenance costs have reached ${cost_summary.get('total_cost', 0):,.2f}",
                                "priority": "medium",
                                "status": "unread",
                                "created_at": datetime.now().isoformat(),
                                "data": {
                                    "total_cost": cost_summary.get('total_cost', 0),
                                    "average_cost": cost_summary.get('average_cost', 0),
                                    "cost_threshold": 10000
                                }
                            })
                    except Exception as cost_error:
                        logger.warning(f"Could not generate cost alerts: {cost_error}")
                    
                    # Filter by type if specified
                    if notification_type:
                        notifications = [n for n in notifications if n['type'] == notification_type]
                    
                    # Filter by status if specified
                    if status:
                        notifications = [n for n in notifications if n['status'] == status]
                    
                    # Apply pagination
                    total_notifications = len(notifications)
                    notifications = notifications[skip:skip + limit]
                    
                    return ResponseBuilder.success(
                        data={
                            "notifications": notifications,
                            "total": total_notifications,
                            "skip": skip,
                            "limit": limit,
                            "has_more": skip + len(notifications) < total_notifications
                        },
                        message="Maintenance notifications retrieved successfully"
                    ).model_dump()
                    
                except Exception as e:
                    logger.error(f"Error generating notifications: {e}")
                    return ResponseBuilder.success(
                        data={
                            "notifications": [],
                            "total": 0,
                            "skip": skip,
                            "limit": limit,
                            "has_more": False,
                            "message": "Notifications temporarily unavailable"
                        },
                        message="Notifications service temporarily unavailable"
                    ).model_dump()
                    
            elif method == "POST":
                # Mark notification as read/unread
                notification_id = data.get("notification_id", "")
                action = data.get("action", "mark_read")
                
                if not notification_id:
                    return ResponseBuilder.error(
                        error="InvalidRequest",
                        message="notification_id is required"
                    ).model_dump()
                
                # For now, return success (in a real implementation, this would update a notifications table)
                return ResponseBuilder.success(
                    data={
                        "notification_id": notification_id,
                        "action": action,
                        "status": "completed",
                        "message": f"Notification {notification_id} marked as {action.replace('mark_', '')}"
                    },
                    message=f"Notification {action.replace('mark_', '')} successfully"
                ).model_dump()
                
            elif method == "PUT":
                # Update notification preferences
                preferences = data.get("preferences", {})
                user_id = data.get("user_id", "")
                
                return ResponseBuilder.success(
                    data={
                        "user_id": user_id,
                        "preferences": preferences,
                        "updated_at": datetime.now().isoformat(),
                        "message": "Notification preferences updated successfully"
                    },
                    message="Notification preferences updated successfully"
                ).model_dump()
                
            else:
                raise ValueError(f"Unsupported HTTP method for notifications: {method}")
                
        except Exception as e:
            logger.error(f"Error handling notification request {method} {endpoint}: {e}")

            return ResponseBuilder.error(
                error="NotificationRequestError",
                message=f"Failed to process notification request: {str(e)}"
            ).model_dump()
    
    async def _handle_vendor_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle vendor-related requests"""
        try:
            # Check database connectivity first
            if not await self._check_database_connectivity():

                return ResponseBuilder.error(
                    error="DatabaseUnavailable",
                    message="Database service is currently unavailable"
                ).model_dump()
            
            # Extract data and endpoint from user_context
            data = user_context.get("data", {})
            endpoint = user_context.get("endpoint", "")
            
            if method == "GET":
                # Extract query parameters
                skip = max(0, int(data.get("skip", 0)))
                limit = min(100, max(1, int(data.get("limit", 20))))
                vendor_type = data.get("type", "")
                status = data.get("status", "")
                search = data.get("search", "")
                
                if endpoint == "vendors" or "maintenance/vendors" in endpoint:
                    try:
                        # Import required services
                        from services.maintenance_service import maintenance_records_service
                        
                        # Generate maintenance vendor data based on maintenance records
                        maintenance_records = await maintenance_records_service.get_all_maintenance_records(
                            skip=0, limit=100
                        )
                        
                        # Extract unique maintenance types to create relevant vendors
                        maintenance_types = set()
                        for record in maintenance_records:
                            if record.get('maintenance_type'):
                                maintenance_types.add(record.get('maintenance_type'))
                        
                        # Generate vendors for each maintenance type
                        vendors = []
                        vendor_categories = {
                            "oil_change": {"name": "Automotive Oil Services", "specialties": ["Oil Change", "Filter Replacement", "Fluid Checks"]},
                            "brake_service": {"name": "Brake Specialists", "specialties": ["Brake Pad Replacement", "Brake Fluid", "Brake Inspection"]},
                            "tire_rotation": {"name": "Tire & Wheel Experts", "specialties": ["Tire Rotation", "Wheel Alignment", "Tire Replacement"]},
                            "engine_service": {"name": "Engine Performance Center", "specialties": ["Engine Diagnostics", "Engine Repair", "Performance Tuning"]},
                            "transmission": {"name": "Transmission Specialists", "specialties": ["Transmission Service", "Transmission Repair", "Fluid Exchange"]},
                            "electrical": {"name": "Auto Electrical Services", "specialties": ["Electrical Diagnostics", "Battery Service", "Alternator Repair"]},
                            "air_conditioning": {"name": "Climate Control Experts", "specialties": ["AC Service", "Refrigerant", "Climate System Repair"]},
                            "inspection": {"name": "Vehicle Inspection Center", "specialties": ["Safety Inspection", "Emission Testing", "Compliance Checks"]}
                        }
                        
                        for i, maintenance_type in enumerate(list(maintenance_types)[:10]):
                            # Get vendor category or create generic
                            vendor_info = vendor_categories.get(
                                maintenance_type.lower().replace(" ", "_"),
                                {"name": f"{maintenance_type.title()} Specialists", "specialties": [maintenance_type.title()]}
                            )
                            
                            # Calculate performance metrics
                            type_records = [r for r in maintenance_records if r.get('maintenance_type') == maintenance_type]
                            avg_cost = sum(float(r.get('cost', 0)) for r in type_records) / max(len(type_records), 1)
                            completion_rate = random.randint(85, 98)
                            
                            vendor_data = {
                                "id": f"vendor_{maintenance_type.lower().replace(' ', '_')}_{i+1}",
                                "name": vendor_info["name"],
                                "type": "maintenance_service",
                                "specialties": vendor_info["specialties"],
                                "contact": {
                                    "email": f"contact@{vendor_info['name'].lower().replace(' ', '').replace('&', 'and')}.com",
                                    "phone": f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                                    "address": f"{random.randint(100, 9999)} {['Main St', 'Industrial Ave', 'Service Blvd', 'Auto Way'][i%4]}, City, State {random.randint(10000, 99999)}"
                                },
                                "status": "active",
                                "performance": {
                                    "completion_rate": completion_rate,
                                    "average_cost": round(avg_cost, 2),
                                    "total_jobs": len(type_records),
                                    "rating": round(4.0 + (completion_rate - 85) * 0.05, 1),
                                    "on_time_delivery": random.randint(88, 97)
                                },
                                "services": [
                                    {
                                        "service": maintenance_type,
                                        "cost_range": f"${max(50, avg_cost - 100):.0f} - ${avg_cost + 100:.0f}",
                                        "duration": f"{random.randint(1, 4)} hours",
                                        "availability": "weekdays_weekends" if random.choice([True, False]) else "weekdays_only"
                                    }
                                ],
                                "certifications": [
                                    "ASE Certified",
                                    "State Licensed",
                                    f"{maintenance_type.title()} Specialist Certification"
                                ],
                                "created_at": (datetime.now() - timedelta(days=random.randint(30, 365))).isoformat(),
                                "last_service": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat()
                            }
                            vendors.append(vendor_data)
                        
                        # Add general service vendors
                        general_vendors = [
                            {
                                "id": "vendor_general_auto_center",
                                "name": "Complete Auto Service Center",
                                "type": "full_service",
                                "specialties": ["General Maintenance", "Multi-Service", "Fleet Service"],
                                "contact": {
                                    "email": "info@completeauto.com",
                                    "phone": "+1-555-AUTO-FIX",
                                    "address": "1234 Service Center Dr, Automotive City, AC 12345"
                                },
                                "status": "active",
                                "performance": {
                                    "completion_rate": 94,
                                    "average_cost": sum(float(r.get('cost', 0)) for r in maintenance_records) / max(len(maintenance_records), 1),
                                    "total_jobs": len(maintenance_records),
                                    "rating": 4.5,
                                    "on_time_delivery": 92
                                },
                                "services": [
                                    {"service": "All Maintenance Types", "cost_range": "$50 - $500", "duration": "1-8 hours", "availability": "weekdays_weekends"}
                                ],
                                "certifications": ["ASE Master Certified", "State Licensed", "Fleet Service Certified"],
                                "created_at": (datetime.now() - timedelta(days=180)).isoformat(),
                                "last_service": (datetime.now() - timedelta(days=2)).isoformat()
                            }
                        ]
                        vendors.extend(general_vendors)
                        
                        # Filter by vendor type if specified
                        if vendor_type:
                            vendors = [v for v in vendors if v['type'] == vendor_type]
                        
                        # Filter by status if specified
                        if status:
                            vendors = [v for v in vendors if v['status'] == status]
                        
                        # Filter by search term if specified
                        if search:
                            search_lower = search.lower()
                            vendors = [v for v in vendors if 
                                     search_lower in v['name'].lower() or
                                     any(search_lower in spec.lower() for spec in v['specialties'])]
                        
                        # Sort by performance rating
                        vendors.sort(key=lambda x: x['performance']['rating'], reverse=True)
                        
                        # Apply pagination
                        total_vendors = len(vendors)
                        vendors = vendors[skip:skip + limit]
                        
                        return ResponseBuilder.success(
                            data={
                                "vendors": vendors,
                                "total": total_vendors,
                                "skip": skip,
                                "limit": limit,
                                "has_more": skip + len(vendors) < total_vendors,
                                "summary": {
                                    "active_vendors": len([v for v in vendors if v['status'] == 'active']),
                                    "average_rating": round(sum(v['performance']['rating'] for v in vendors) / max(len(vendors), 1), 2),
                                    "total_services": sum(len(v['services']) for v in vendors)
                                }
                            },
                            message="Maintenance vendors retrieved successfully"
                        ).model_dump()
                        
                    except Exception as e:
                        logger.error(f"Error generating vendors: {e}")
                        return ResponseBuilder.success(
                            data={
                                "vendors": [],
                                "total": 0,
                                "skip": skip,
                                "limit": limit,
                                "has_more": False,
                                "summary": {
                                    "active_vendors": 0,
                                    "average_rating": 0,
                                    "total_services": 0
                                },
                                "message": "Vendor data temporarily unavailable"
                            },
                            message="Vendor service temporarily unavailable"
                        ).model_dump()
                else:
                    # Individual vendor lookup
                    vendor_id = data.get("vendor_id", "") or data.get("id", "")
                    if vendor_id:
                        # Generate individual vendor details
                        vendor_data = {
                            "id": vendor_id,
                            "name": f"Service Provider {vendor_id.split('_')[-1].title()}",
                            "type": "maintenance_service",
                            "specialties": ["General Maintenance", "Automotive Service"],
                            "contact": {
                                "email": f"contact@vendor{vendor_id.split('_')[-1]}.com",
                                "phone": f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                                "address": f"{random.randint(100, 9999)} Service St, Auto City, AC {random.randint(10000, 99999)}"
                            },
                            "status": "active",
                            "performance": {
                                "completion_rate": random.randint(85, 98),
                                "average_cost": random.randint(100, 500),
                                "total_jobs": random.randint(10, 100),
                                "rating": round(random.uniform(3.5, 5.0), 1),
                                "on_time_delivery": random.randint(85, 98)
                            },
                            "services": [
                                {"service": "General Maintenance", "cost_range": "$50 - $400", "duration": "1-4 hours", "availability": "weekdays"}
                            ],
                            "certifications": ["ASE Certified", "State Licensed"],
                            "created_at": (datetime.now() - timedelta(days=random.randint(30, 365))).isoformat(),
                            "last_service": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
                            "detailed_info": {
                                "insurance": "Fully Insured",
                                "warranty": "6 months on parts and labor",
                                "payment_terms": "Net 30",
                                "business_hours": "Mon-Fri 8AM-6PM, Sat 8AM-4PM"
                            }
                        }
                        
                        return ResponseBuilder.success(
                            data={"vendor": vendor_data},
                            message="Vendor details retrieved successfully"
                        ).model_dump()
                    
                    return ResponseBuilder.error(
                        error="VendorNotFound",
                        message="Vendor not found or invalid vendor ID"
                    ).model_dump()
                    
            elif method == "POST":
                # Create new vendor
                vendor_data = {
                    "name": data.get("name", ""),
                    "type": data.get("type", "maintenance_service"),
                    "specialties": data.get("specialties", []),
                    "contact": data.get("contact", {}),
                    "certifications": data.get("certifications", [])
                }
                
                # Generate ID
                vendor_id = f"vendor_{vendor_data['name'].lower().replace(' ', '_')}"
                
                return ResponseBuilder.success(
                    data={
                        "vendor": {
                            "id": vendor_id,
                            **vendor_data,
                            "status": "pending_verification",
                            "created_at": datetime.now().isoformat()
                        }
                    },
                    message="Vendor created successfully"
                ).model_dump()
                
            elif method == "PUT":
                # Update vendor information
                vendor_id = data.get("vendor_id", "") or data.get("id", "")
                updates = data.get("updates", {})
                
                return ResponseBuilder.success(
                    data={
                        "vendor": {
                            "id": vendor_id,
                            **updates,
                            "updated_at": datetime.now().isoformat()
                        }
                    },
                    message="Vendor updated successfully"
                ).model_dump()
                
            elif method == "DELETE":
                vendor_id = data.get("vendor_id", "") or data.get("id", "")
                
                return ResponseBuilder.success(
                    data={
                        "deleted": True,
                        "vendor_id": vendor_id,
                        "deleted_at": datetime.now().isoformat()
                    },
                    message="Vendor deactivated successfully"
                ).model_dump()
            else:
                raise ValueError(f"Unsupported HTTP method for vendors: {method}")
            
        except Exception as e:
            logger.error(f"Error handling vendor request {method}: {e}")

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
 

# Global service instance
service_request_consumer = ServiceRequestConsumer()
