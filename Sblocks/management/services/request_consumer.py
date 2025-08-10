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
        """Handle vehicles-related requests by calling route logic"""
        try:
            # Import route handlers and extract their business logic
            from api.routes.vehicles import vehicle_service
            from schemas.requests import VehicleCreateRequest, VehicleUpdateRequest
            from schemas.responses import ResponseBuilder
            
            # Extract data and endpoint from user_context
            data = user_context.get("data", {})
            endpoint = user_context.get("endpoint", "")
            
            # Create mock user for service calls
            current_user = {"user_id": user_context.get("user_id", "system")}
            
            # Handle HTTP methods and route to appropriate logic
            if method == "GET":
                # Parse endpoint for specific vehicle operations
                if "search" in endpoint:
                    query = data.get("query", "")
                    vehicles = await vehicle_service.search_vehicles(query)
                elif endpoint.count('/') > 0 and endpoint.split('/')[-1] and endpoint.split('/')[-1] != "vehicles":
                    # vehicles/{id} pattern
                    vehicle_id = endpoint.split('/')[-1]
                    vehicles = await vehicle_service.get_vehicle_by_id(vehicle_id)
                else:
                    # Get all vehicles with optional filters
                    department = data.get("department")
                    status = data.get("status") 
                    vehicle_type = data.get("vehicle_type")
                    pagination = data.get("pagination", {"skip": 0, "limit": 50})
                    
                    vehicles = await vehicle_service.get_vehicles(
                        department=department,
                        status=status,
                        vehicle_type=vehicle_type,
                        pagination=pagination
                    )
                
                # Transform _id to id for frontend compatibility
                vehicles = self._transform_vehicle_data(vehicles)
                
                return ResponseBuilder.success(
                    data=vehicles,
                    message="Vehicles retrieved successfully"
                ).model_dump()
                
            elif method == "POST":
                if not data:
                    raise ValueError("Request data is required for POST operation")
                
                if "assign-driver" in endpoint:
                    logger.info(f"Data received for driver assignment: {data} ")
                else:
                    # Create vehicle
                    vehicle_request = VehicleCreateRequest(**data)
                    created_by = current_user["user_id"]
                    result = await vehicle_service.create_vehicle(vehicle_request, created_by)
                    
                    # Transform _id to id for frontend compatibility
                    result = self._transform_vehicle_data(result)
                    
                    return ResponseBuilder.success(
                        data=result,
                        message="Vehicle created successfully"
                    ).model_dump()

                
                
            elif method == "PUT":
                vehicle_id = endpoint.split('/')[-1] if '/' in endpoint else None
                if not vehicle_id:
                    raise ValueError("Vehicle ID is required for PUT operation")
                if not data:
                    raise ValueError("Request data is required for PUT operation")
                
                # Update vehicle
                vehicle_update_request = VehicleUpdateRequest(**data)
                updated_by = current_user["user_id"]
                result = await vehicle_service.update_vehicle(vehicle_id, vehicle_update_request, updated_by)
                
                # Transform _id to id for frontend compatibility
                result = self._transform_vehicle_data(result)
                
                return ResponseBuilder.success(
                    data=result,
                    message="Vehicle updated successfully"
                ).model_dump()
                
            elif method == "DELETE":
                vehicle_id = endpoint.split('/')[-1] if '/' in endpoint else None
                if not vehicle_id:
                    raise ValueError("Vehicle ID is required for DELETE operation")
                
                # Delete vehicle
                deleted_by = current_user["user_id"]
                result = await vehicle_service.delete_vehicle(vehicle_id, deleted_by)
                
                return ResponseBuilder.success(
                    data=result,
                    message="Vehicle deleted successfully"
                ).model_dump()
                
            else:
                raise ValueError(f"Unsupported HTTP method for vehicles: {method}")
                
        except Exception as e:
            logger.error(f"Error handling vehicles request {method} {endpoint}: {e}")
            return ResponseBuilder.error(
                error="VehicleRequestError",
                message=f"Failed to process vehicle request: {str(e)}"
            ).model_dump()
    
    async def _handle_drivers_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle drivers-related requests by calling route logic"""
        try:
            # Import route logic
            from services.driver_service import driver_service
            from schemas.requests import DriverCreateRequest, DriverUpdateRequest
            from schemas.responses import ResponseBuilder
            from repositories.repositories import DriverRepository
            
            # Extract data and endpoint from user_context
            data = user_context.get("data", {})
            endpoint = user_context.get("endpoint", "")
            
            # Create mock user for service calls
            current_user = {"user_id": user_context.get("user_id", "system")}
            
            # Handle HTTP methods and route to appropriate logic
            if method == "GET":
                # Parse endpoint for specific driver operations
                if "search" in endpoint:
                    query = data.get("query", "")
                    drivers = await driver_service.search_drivers(query)
                elif endpoint.count('/') > 0 and endpoint.split('/')[-1] and endpoint.split('/')[-1] != "drivers":
                    # drivers/{id} pattern
                    driver_id = endpoint.split('/')[-1]
                    drivers = await driver_service.get_driver_by_id(driver_id)
                else:
                    # Get drivers with optional filters (mimic route logic)
                    department = data.get("department")
                    status = data.get("status")
                    pagination = data.get("pagination", {"skip": 0, "limit": 50})
                    
                    filters = {}

                    # Normalize filters from request
                    if department:
                        filters["department_filter"] = department

                    if status:
                        filters["status_filter"] = status

                    # Handle pagination
                    pagination = data.get("pagination", {})
                    if "skip" in pagination:
                        filters["skip"] = pagination["skip"]
                    if "limit" in pagination:
                        filters["limit"] = pagination["limit"]
                    
                    logger.info(f"Filters: {filters}")

                    # Get drivers using new filter-aware function
                    drivers_result = await driver_service.get_all_drivers(filters)

                
                return ResponseBuilder.success(
                    data=drivers_result,
                    message="Drivers retrieved successfully"
                ).model_dump()

                
            elif method == "POST":
                if not data:
                    raise ValueError("Request data is required for POST operation")
                
                logger.info(f"Data received for POST operation: ")
                
                # Create and employee id based on the last employeeid in the driver collection
                employee_id = await driver_service.generate_next_employee_id()
                logger.info(f"Generated employee_id: {employee_id}")
                # Split full name from data into first and last names
                full_name = data["full_name"]  # Changed from data.full_name to data["full_name"]
                parts = full_name.strip().split()
                first_name = parts[0]
                last_name = " ".join(parts[1:])
                # Create new data
                driver_data = {
                    "employee_id": employee_id,
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": data["email"],
                    "phone": data["phoneNo"]
                }
                # Create driver
                driver_request = DriverCreateRequest(**driver_data)
                created_by = current_user["user_id"]
                result = await driver_service.create_driver(driver_request, created_by)
                
                return ResponseBuilder.success(
                    data=result,
                    message="Driver created successfully"
                ).model_dump()
                
            elif method == "PUT":
                driver_id = endpoint.split('/')[-1] if '/' in endpoint else None
                if not driver_id:
                    raise ValueError("Driver ID is required for PUT operation")
                if not data:
                    raise ValueError("Request data is required for PUT operation")
                
                # Update driver
                driver_update_request = DriverUpdateRequest(**data)
                updated_by = current_user["user_id"]
                result = await driver_service.update_driver(driver_id, driver_update_request, updated_by)
                
                return ResponseBuilder.success(
                    data=result,
                    message="Driver updated successfully"
                ).model_dump()
                
            elif method == "DELETE":
                driver_id = endpoint.split('/')[-1] if '/' in endpoint else None
                if not driver_id:
                    raise ValueError("Driver ID is required for DELETE operation")
                
                # Delete driver
                result = await driver_service.delete_driver(driver_id)
                
                return ResponseBuilder.success(
                    data=result,
                    message="Driver deleted successfully"
                ).model_dump()
                
            else:
                raise ValueError(f"Unsupported HTTP method for drivers: {method}")
                
        except Exception as e:
            logger.error(f"Error handling drivers request {method} {endpoint}: {e}")
            return ResponseBuilder.error(
                error="DriverRequestError",
                message=f"Failed to process driver request: {str(e)}"
            ).model_dump()
    
    async def _handle_assignments_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle assignments-related requests"""
        # Assignment service not implemented yet
        return {
            "message": "Assignment service not yet implemented",
            "method": method
        }
    
    async def _handle_analytics_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle analytics-related requests by calling route logic"""
        try:
            # Import route logic
            from services.analytics_service import analytics_service
            from schemas.responses import ResponseBuilder
            
            # Extract data and endpoint from user_context
            data = user_context.get("data", {})
            endpoint = user_context.get("endpoint", "")
            use_cache = data.get("use_cache", True)
            
            # Create mock user for service calls
            current_user = {"user_id": user_context.get("user_id", "system")}
            
            # Handle HTTP methods and route to appropriate analytics logic
            if method == "GET":
                # Route based on specific analytics endpoint (mimic route structure)
                if "dashboard" in endpoint:
                    dashboard_data = await analytics_service.get_dashboard_summary(use_cache=use_cache)
                    return ResponseBuilder.success(
                        data=dashboard_data,
                        message="Dashboard analytics retrieved successfully"
                    ).model_dump()
                    
                elif "fleet-utilization" in endpoint or "fleet_utilization" in endpoint:
                    utilization_data = await analytics_service.get_fleet_utilization(use_cache=use_cache)
                    return ResponseBuilder.success(
                        data=utilization_data,
                        message="Fleet utilization data retrieved successfully"
                    ).model_dump()
                    
                elif "driver-performance" in endpoint or "driver_performance" in endpoint:
                    performance_data = await analytics_service.get_driver_performance(use_cache=use_cache)
                    return ResponseBuilder.success(
                        data=performance_data,
                        message="Driver performance data retrieved successfully"
                    ).model_dump()
                    
                elif "maintenance-costs" in endpoint or "maintenance_costs" in endpoint:
                    costs_data = await analytics_service.get_maintenance_costs(use_cache=use_cache)
                    return ResponseBuilder.success(
                        data=costs_data,
                        message="Maintenance costs data retrieved successfully"
                    ).model_dump()
                    
                elif "fuel-consumption" in endpoint or "fuel_consumption" in endpoint:
                    fuel_data = await analytics_service.get_fuel_consumption(use_cache=use_cache)
                    return ResponseBuilder.success(
                        data=fuel_data,
                        message="Fuel consumption data retrieved successfully"
                    ).model_dump()
                    
                else:
                    # Default analytics data
                    analytics_data = await analytics_service.get_analytics_data(data)
                    return ResponseBuilder.success(
                        data=analytics_data,
                        message="Analytics data retrieved successfully"
                    ).model_dump()
                    
            elif method == "POST":
                # POST for custom analytics queries
                analytics_data = await analytics_service.get_analytics_data(data)
                return ResponseBuilder.success(
                    data=analytics_data,
                    message="Custom analytics query processed successfully"
                ).model_dump()
                
            else:
                raise ValueError(f"Unsupported HTTP method for analytics: {method}")
                
        except Exception as e:
            logger.error(f"Error handling analytics request {method} {endpoint}: {e}")
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
    
    def _transform_vehicle_data(self, data):
        """Transform vehicle data to convert _id to id for frontend compatibility"""
        if data is None:
            return data
        
        def transform_single_vehicle(vehicle):
            """Transform a single vehicle object"""
            if isinstance(vehicle, dict) and "_id" in vehicle:
                # Create new dict with id field
                transformed = vehicle.copy()
                transformed["id"] = transformed.pop("_id")
                return transformed
            return vehicle
        
        if isinstance(data, dict):
            # Check if it's a vehicle list response
            if "vehicles" in data and isinstance(data["vehicles"], list):
                # Transform list of vehicles
                data["vehicles"] = [transform_single_vehicle(v) for v in data["vehicles"]]
                return data
            else:
                # Single vehicle response
                return transform_single_vehicle(data)
        elif isinstance(data, list):
            # Direct list of vehicles
            return [transform_single_vehicle(v) for v in data]
        
        return data
    
    async def stop_consuming(self):
        """Stop consuming messages"""
        self.is_consuming = False
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
        logger.info("Management service request consumer stopped")

# Global instance
service_request_consumer = ServiceRequestConsumer()
