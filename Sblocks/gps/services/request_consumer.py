"""
Service Request Consumer for GPS Service
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

logger = logging.getLogger(__name__)

class ServiceRequestConsumer:
    """Handles service requests from Core via RabbitMQ with standardized patterns"""
    
    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = None
        self.response_exchange = None
        self.queue = None
        # Use standardized config
        self.config = RabbitMQConfig()
        self.queue_name = self.config.QUEUE_NAMES["gps"]
        self.exchange_name = self.config.EXCHANGE_NAMES["requests"]
        self.response_exchange_name = self.config.EXCHANGE_NAMES["responses"]
        # Enhanced request deduplication with content hashing
        self.processed_requests = {}  # correlation_id -> timestamp
        self.request_content_hashes = {}  # content_hash -> correlation_id
        self.is_consuming = False
        # Cleanup old requests every hour
        import asyncio
        self._cleanup_task = None
        # Connection pooling for responses
        self._response_connection = None
        self._response_channel = None
    
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
            
            # Bind to gps routing key (must match Core service routing pattern)
            await self.queue.bind(self.exchange, "gps.requests")
            
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
        """Start consuming requests and cleanup task"""
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
            
        logger.info("GPS service request consumer stopped")
    
    async def disconnect(self):
        """Disconnect from RabbitMQ"""
        self.is_consuming = False
        
        # Close response connection
        if self._response_connection and not self._response_connection.is_closed:
            await self._response_connection.close()
            
        # Close main connection
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            
        logger.info("GPS service disconnected")
    
    async def handle_request(self, message: AbstractIncomingMessage):
        """Handle incoming request message using standardized pattern"""
        request_id = None
        try:
            async with message.process(requeue=False):
                # Parse message body
                request_data = json.loads(message.body.decode())
                logger.info(f"REQUEST_DATA: {request_data}")
                
                # Extract request details
                request_id = request_data.get("correlation_id")
                method = request_data.get("method")
                user_context = request_data.get("user_context", {})
                endpoint = request_data.get("endpoint", "")
                
                # Extract data from top-level and add to user_context for handlers
                data = request_data.get("data", {})
                logger.info(f"Message data: {data}")
                user_context["data"] = data
                
                # Check for duplicate requests by correlation_id
                current_time = datetime.now().timestamp()
                if request_id in self.processed_requests:
                    request_age = current_time - self.processed_requests[request_id]
                    if request_age < 300:  # 5 minutes
                        logger.warning(f"Duplicate request ignored (correlation_id): {request_id}")
                        return
                    
                self.processed_requests[request_id] = current_time
                
                logger.debug(f"Processing request {request_id}: {method} {endpoint}")
                
                # Route and process request with timeout
                import asyncio
                try:
                    response_data = await asyncio.wait_for(
                        self._route_request(method, user_context, endpoint),
                        timeout=self.config.REQUEST_TIMEOUTS.get("default_request_timeout", 25.0)
                    )
                except asyncio.TimeoutError:
                    logger.error(f"Request {request_id} timed out")
                    raise RuntimeError("Request processing timeout")
                
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
            elif "locations" in endpoint:
                return await self._handle_locations_request(method, user_context)
            elif "geofences" in endpoint:
                return await self._handle_geofences_request(method, user_context)
            elif "places" in endpoint:
                return await self._handle_places_request(method, user_context)
            elif "tracking" in endpoint:
                return await self._handle_tracking_request(method, user_context)
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

    async def _handle_locations_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle locations-related requests by calling route logic"""
        try:
            # Check database connectivity first
            if not self.config or not hasattr(self, 'db_manager'):
                # Import here to avoid circular imports
                from repositories.database import db_manager
                if not db_manager.is_connected():
                    raise RuntimeError("Database not connected")
            
            # Import route handlers and extract their business logic
            from services.location_service import location_service
            from schemas.responses import ResponseBuilder
            
            # Extract data and endpoint from user_context
            data = user_context.get("data", {})
            endpoint = user_context.get("endpoint", "")
            
            # Create mock user for service calls
            current_user = {"user_id": user_context.get("user_id", "system")}
            
            # Handle HTTP methods and route to appropriate logic
            if method == "GET":
                # Parse endpoint for specific location operations
                if "locations" in endpoint:
                    logger.info("Still add functionality")
                elif "vehicle" in endpoint and endpoint.count('/') > 0:
                    # locations/vehicle/{vehicle_id} pattern
                    vehicle_id = endpoint.split('/')[-1]
                    location = await location_service.get_vehicle_location(vehicle_id)
                    
                    return ResponseBuilder.success(
                        data=location.model_dump() if location else None,
                        message="Vehicle location retrieved successfully"
                    ).model_dump()
                    
                elif "history" in endpoint:
                    # locations/history with query params
                    vehicle_id = data.get("vehicle_id")
                    start_time = data.get("start_time")
                    end_time = data.get("end_time")
                    limit = data.get("limit", 100)
                    
                    history = await location_service.get_location_history(
                        vehicle_id, start_time, end_time, limit
                    )
                    
                    return ResponseBuilder.success(
                        data=[loc.model_dump() for loc in history],
                        message="Location history retrieved successfully"
                    ).model_dump()
                    
                else:
                    # Get all active vehicle locations
                    vehicle_ids = data.get("vehicle_ids", [])
                    if vehicle_ids:
                        locations = await location_service.get_multiple_vehicle_locations(vehicle_ids)
                    else:
                        locations = await location_service.get_all_vehicle_locations()
                    
                    return ResponseBuilder.success(
                        data=[loc.model_dump() for loc in locations],
                        message="Vehicle locations retrieved successfully"
                    ).model_dump()
                
            elif method == "POST":
                if not data:
                    raise ValueError("Request data is required for POST operation")
                
                # Update vehicle location
                vehicle_id = data.get("vehicle_id")
                latitude = data.get("latitude")
                longitude = data.get("longitude")
                
                if not all([vehicle_id, latitude, longitude]):
                    raise ValueError("vehicle_id, latitude, and longitude are required")
                
                result = await location_service.create_vehicle_location(
                    vehicle_id=vehicle_id,
                    latitude=latitude,
                    longitude=longitude,
                    altitude=data.get("altitude"),
                    speed=data.get("speed"),
                    heading=data.get("heading"),
                    accuracy=data.get("accuracy"),
                    timestamp=data.get("timestamp")
                )
                
                return ResponseBuilder.success(
                    data=result.model_dump() if result else None,
                    message="Vehicle location updated successfully"
                ).model_dump()
                
            else:
                raise ValueError(f"Unsupported HTTP method for locations: {method}")
                
        except Exception as e:
            logger.error(f"Error handling locations request {method} {endpoint}: {e}")
            return ResponseBuilder.error(
                error="LocationRequestError",
                message=f"Failed to process location request: {str(e)}"
            ).model_dump()

    async def _handle_geofences_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle geofences-related requests using unified data format with Pydantic V2"""
        try:
            # Check database connectivity first
            from repositories.database import db_manager
            if not db_manager.is_connected():
                raise RuntimeError("Database not connected")
                
            # Import route handlers and extract their business logic
            from services.geofence_service import geofence_service
            from schemas.responses import ResponseBuilder

            if isinstance(user_context, str):
                user_context = json.loads(user_context)
            
            # Extract data and endpoint from user_context
            data = user_context.get("data", {})
            logger.info(f"Data in user_context: {data}")
            endpoint = user_context.get("endpoint", "")
            
            # Create mock user for service calls
            current_user = {"user_id": user_context.get("user_id", "system")}
            
            # Handle HTTP methods and route to appropriate logic
            if method == "GET":
                # Parse endpoint for specific geofence operations
                if endpoint.count('/') > 0 and endpoint.split('/')[-1] and endpoint.split('/')[-1] != "geofences":
                    # geofences/{id} pattern
                    geofence_id = endpoint.split('/')[-1]
                    geofence = await geofence_service.get_geofence_by_id(geofence_id)
                    
                    if geofence:
                        return ResponseBuilder.success(
                            data=geofence.model_dump(),  # Pydantic V2 syntax
                            message="Geofence retrieved successfully"
                        ).model_dump()  # Pydantic V2 syntax
                    else:
                        return ResponseBuilder.success(
                            data=None,
                            message="Geofence not found"
                        ).model_dump()
                else:
                    # Get all geofences with optional filters
                    active_only = data.get("active_only", False)
                    geofence_type = data.get("type")
                    pagination = data.get("pagination", {"skip": 0, "limit": 50})
                    
                    is_active = active_only if active_only else None
                    geofences = await geofence_service.get_geofences(
                        is_active=is_active,
                        geofence_type=geofence_type,
                        limit=pagination["limit"],
                        offset=pagination["skip"]
                    )
                    
                    # Return geofences in unified format using Pydantic V2
                    geofences_data = [gf.model_dump() for gf in geofences]
                    
                    return ResponseBuilder.success(
                        data=geofences_data,
                        message="Geofences retrieved successfully"
                    ).model_dump()
                
            elif method == "POST":
                if not data:
                    raise ValueError("Request data is required for POST operation")
                
                logger.info(f"Creating geofence with unified format data: {data}")
                
                # Validate required fields
                required_fields = ['name', 'geometry']
                for field in required_fields:
                    if field not in data:
                        raise ValueError(f"'{field}' is required")
                
                # Create geofence using simplified format
                result = await geofence_service.create_geofence(
                    name=data.get("name"),
                    description=data.get("description"),
                    type=data.get("type", "depot"),
                    status=data.get("status", "active"),
                    geometry=data.get("geometry")
                )
                
                if result:
                    return ResponseBuilder.success(
                        data=result.model_dump(),  # Pydantic V2 syntax
                        message="Geofence created successfully"
                    ).model_dump()
                else:
                    raise ValueError("Failed to create geofence")
                
            elif method == "PUT":
                geofence_id = endpoint.split('/')[-1] if '/' in endpoint else None
                if not geofence_id:
                    raise ValueError("Geofence ID is required for PUT operation")
                if not data:
                    raise ValueError("Request data is required for PUT operation")
                
                # Update geofence using unified format
                result = await geofence_service.update_geofence(
                    geofence_id=geofence_id,
                    name=data.get("name"),
                    description=data.get("description"),
                    geometry=data.get("geometry"),
                    status=data.get("status"),
                    metadata=data.get("metadata")
                )
                
                if result:
                    return ResponseBuilder.success(
                        data=result.model_dump(),  # Pydantic V2 syntax
                        message="Geofence updated successfully"
                    ).model_dump()
                else:
                    raise ValueError("Failed to update geofence")
                
            elif method == "DELETE":
                geofence_id = endpoint.split('/')[-1] if '/' in endpoint else None
                if not geofence_id:
                    raise ValueError("Geofence ID is required for DELETE operation")
                
                # Delete geofence
                result = await geofence_service.delete_geofence(geofence_id)
                
                return ResponseBuilder.success(
                    data={"deleted": result, "geofence_id": geofence_id},
                    message="Geofence deleted successfully"
                ).model_dump()
                
            else:
                raise ValueError(f"Unsupported HTTP method for geofences: {method}")
                
        except Exception as e:
            logger.error(f"Error handling geofences request {method} {endpoint}: {e}")
            logger.exception("Full error traceback:")
            return ResponseBuilder.error(
                error="GeofenceRequestError",
                message=f"Failed to process geofence request: {str(e)}"
            ).model_dump()

    async def _handle_places_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle places-related requests by calling route logic"""
        try:
            # Check database connectivity first
            from repositories.database import db_manager
            if not db_manager.is_connected():
                raise RuntimeError("Database not connected")
                
            # Import route handlers and extract their business logic
            from services.places_service import places_service
            from schemas.responses import ResponseBuilder
            
            # Extract data and endpoint from user_context
            data = user_context.get("data", {})
            endpoint = user_context.get("endpoint", "")
            
            # Create mock user for service calls
            current_user = {"user_id": user_context.get("user_id", "system")}
            
            # Handle HTTP methods and route to appropriate logic
            if method == "GET":
                # Parse endpoint for specific place operations
                if "search" in endpoint:
                    # places/search with query
                    query = data.get("query", "")
                    place_type = data.get("type")
                    latitude = data.get("latitude")
                    longitude = data.get("longitude")
                    radius = data.get("radius", 1000)  # Default 1km
                    
                    if latitude and longitude:
                        # Search near location
                        places = await places_service.get_places_near_location(
                            latitude=latitude,
                            longitude=longitude,
                            radius_meters=radius,
                            place_type=place_type,
                            limit=50
                        )
                    elif query:
                        # Text search - need user_id context
                        user_id = user_context.get("user_id", "system")
                        places = await places_service.search_places(
                            user_id=user_id,
                            search_term=query,
                            limit=50
                        )
                    else:
                        # Get all places
                        places = await places_service.get_places(
                            place_type=place_type,
                            limit=50
                        )
                    
                    return ResponseBuilder.success(
                        data=[place.model_dump() for place in places],
                        message="Places search completed successfully"
                    ).model_dump()
                    
                elif endpoint.count('/') > 0 and endpoint.split('/')[-1] and endpoint.split('/')[-1] != "places":
                    # places/{id} pattern
                    place_id = endpoint.split('/')[-1]
                    place = await places_service.get_place_by_id(place_id)
                    
                    return ResponseBuilder.success(
                        data=place.model_dump() if place else None,
                        message="Place retrieved successfully"
                    ).model_dump()
                else:
                    # Get all places with optional filters
                    place_type = data.get("type")
                    pagination = data.get("pagination", {"skip": 0, "limit": 50})
                    
                    places = await places_service.get_places(
                        place_type=place_type,
                        skip=pagination["skip"],
                        limit=pagination["limit"]
                    )
                    
                    return ResponseBuilder.success(
                        data=[place.model_dump() for place in places],
                        message="Places retrieved successfully"
                    ).model_dump()
                
            elif method == "POST":
                if not data:
                    raise ValueError("Request data is required for POST operation")
                
                # Create place
                created_by = current_user["user_id"]
                user_id = data.get("user_id", created_by)  # Use provided user_id or creator
                
                result = await places_service.create_place(
                    user_id=user_id,
                    name=data.get("name"),
                    description=data.get("description"),
                    latitude=data.get("latitude"),
                    longitude=data.get("longitude"),
                    address=data.get("address"),
                    place_type=data.get("place_type", "custom"),
                    metadata=data.get("metadata"),
                    created_by=created_by
                )
                
                return ResponseBuilder.success(
                    data=result.model_dump() if result else None,
                    message="Place created successfully"
                ).model_dump()
                
            elif method == "PUT":
                place_id = endpoint.split('/')[-1] if '/' in endpoint else None
                if not place_id:
                    raise ValueError("Place ID is required for PUT operation")
                if not data:
                    raise ValueError("Request data is required for PUT operation")
                
                # Update place
                updated_by = current_user["user_id"]
                user_id = data.get("user_id", updated_by)  # Use provided user_id or updater
                
                result = await places_service.update_place(
                    place_id=place_id,
                    user_id=user_id,
                    name=data.get("name"),
                    description=data.get("description"),
                    latitude=data.get("latitude"),
                    longitude=data.get("longitude"),
                    address=data.get("address"),
                    place_type=data.get("place_type"),
                    metadata=data.get("metadata")
                )
                
                return ResponseBuilder.success(
                    data=result.model_dump() if result else None,
                    message="Place updated successfully"
                ).model_dump()
                
            elif method == "DELETE":
                place_id = endpoint.split('/')[-1] if '/' in endpoint else None
                if not place_id:
                    raise ValueError("Place ID is required for DELETE operation")
                
                # Delete place
                deleted_by = current_user["user_id"]
                result = await places_service.delete_place(place_id, deleted_by)
                
                return ResponseBuilder.success(
                    data={"deleted": result, "place_id": place_id},
                    message="Place deleted successfully"
                ).model_dump()
                
            else:
                raise ValueError(f"Unsupported HTTP method for places: {method}")
                
        except Exception as e:
            logger.error(f"Error handling places request {method} {endpoint}: {e}")
            return ResponseBuilder.error(
                error="PlaceRequestError",
                message=f"Failed to process place request: {str(e)}"
            ).model_dump()

    async def _handle_tracking_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tracking-related requests"""
        try:
            # Check database connectivity first
            from repositories.database import db_manager
            if not db_manager.is_connected():
                raise RuntimeError("Database not connected")
                
            # Import route handlers and extract their business logic
            from services.location_service import location_service
            from schemas.responses import ResponseBuilder
            
            # Extract data and endpoint from user_context
            data = user_context.get("data", {})
            endpoint = user_context.get("endpoint", "")
            
            # Handle HTTP methods and route to appropriate logic
            if method == "GET":
                # Parse endpoint for specific tracking operations
                if "live" in endpoint:
                    # tracking/live for real-time tracking
                    vehicle_ids = data.get("vehicle_ids", [])
                    
                    if vehicle_ids:
                        locations = await location_service.get_multiple_vehicle_locations(vehicle_ids)
                    else:
                        locations = await location_service.get_all_vehicle_locations()
                    
                    return ResponseBuilder.success(
                        data=[loc.model_dump() for loc in locations],
                        message="Live tracking data retrieved successfully"
                    ).model_dump()
                    
                elif "route" in endpoint:
                    # tracking/route for route tracking
                    vehicle_id = data.get("vehicle_id")
                    start_time = data.get("start_time")
                    end_time = data.get("end_time")
                    
                    if not vehicle_id:
                        raise ValueError("Vehicle ID is required for route tracking")
                    
                    route = await location_service.get_vehicle_route(
                        vehicle_id, start_time, end_time
                    )
                    
                    return ResponseBuilder.success(
                        data=route,
                        message="Vehicle route retrieved successfully"
                    ).model_dump()
                    
                else:
                    # Generic tracking status
                    return ResponseBuilder.success(
                        data={"tracking_active": True, "service": "gps"},
                        message="GPS tracking service is operational"
                    ).model_dump()
                
            elif method == "POST":
                if not data:
                    raise ValueError("Request data is required for POST operation")
                
                # Start/update tracking for vehicle
                vehicle_id = data.get("vehicle_id")
                if not vehicle_id:
                    raise ValueError("Vehicle ID is required to start tracking")
                
                result = await location_service.start_vehicle_tracking(vehicle_id)
                
                return ResponseBuilder.success(
                    data=result,
                    message="Vehicle tracking started successfully"
                ).model_dump()
                
            else:
                raise ValueError(f"Unsupported HTTP method for tracking: {method}")
                
        except Exception as e:
            logger.error(f"Error handling tracking request {method} {endpoint}: {e}")
            return ResponseBuilder.error(
                error="TrackingRequestError",
                message=f"Failed to process tracking request: {str(e)}"
            ).model_dump()

    async def _handle_health_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle health check requests"""
        try:
            from schemas.responses import ResponseBuilder
            
            if method == "GET":
                health_data = {
                    "status": "healthy",
                    "service": "gps",
                    "timestamp": datetime.now().isoformat(),
                    "message": "GPS service is operational",
                    "components": {
                        "location_tracking": "active",
                        "geofencing": "active",
                        "places_management": "active"
                    }
                }
                return ResponseBuilder.success(
                    data=health_data,
                    message="GPS service health check completed"
                ).model_dump()
            else:
                raise ValueError(f"Unsupported method for health endpoint: {method}")
                
        except Exception as e:
            logger.error(f"Error handling health request {method}: {e}")
            return ResponseBuilder.error(
                error="HealthCheckError",
                message=f"Failed to process health check: {str(e)}"
            ).model_dump()

    async def _handle_status_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle status requests"""
        try:
            from schemas.responses import ResponseBuilder
            
            if method == "GET":
                status_data = {
                    "status": "operational",
                    "service": "gps",
                    "uptime": "unknown",  # Could implement actual uptime tracking
                    "connections": {
                        "database": "connected",
                        "rabbitmq": "connected"
                    },
                    "features": [
                        "location_tracking",
                        "geofencing", 
                        "places_management",
                        "real_time_tracking"
                    ],
                    "timestamp": datetime.now().isoformat()
                }
                return ResponseBuilder.success(
                    data=status_data,
                    message="GPS service status retrieved successfully"
                ).model_dump()
            else:
                raise ValueError(f"Unsupported method for status endpoint: {method}")
                
        except Exception as e:
            logger.error(f"Error handling status request {method}: {e}")
            return ResponseBuilder.error(
                error="StatusRequestError",
                message=f"Failed to process status request: {str(e)}"
            ).model_dump()

    async def _handle_docs_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle documentation requests"""
        try:
            from schemas.responses import ResponseBuilder
            
            if method == "GET":
                docs_data = {
                    "message": "API documentation available at /docs",
                    "openapi_url": "/openapi.json",
                    "service": "gps",
                    "endpoints": {
                        "locations": "Location tracking and history",
                        "geofences": "Geofence management",
                        "places": "Places and POI management",
                        "tracking": "Real-time tracking"
                    }
                }
                return ResponseBuilder.success(
                    data=docs_data,
                    message="GPS service documentation retrieved successfully"
                ).model_dump()
            else:
                raise ValueError(f"Unsupported method for docs endpoint: {method}")
                
        except Exception as e:
            logger.error(f"Error handling docs request {method}: {e}")
            return ResponseBuilder.error(
                error="DocsRequestError",
                message=f"Failed to process docs request: {str(e)}"
            ).model_dump()

    async def _handle_metrics_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle metrics requests"""
        try:
            from schemas.responses import ResponseBuilder
            
            if method == "GET":
                metrics_data = {
                    "metrics": {
                        "requests_processed": len(self.processed_requests),
                        "service_status": "healthy",
                        "last_request_time": datetime.now().isoformat(),
                        "tracking_active": True
                    },
                    "service": "gps"
                }
                return ResponseBuilder.success(
                    data=metrics_data,
                    message="GPS service metrics retrieved successfully"
                ).model_dump()
            else:
                raise ValueError(f"Unsupported method for metrics endpoint: {method}")
                
        except Exception as e:
            logger.error(f"Error handling metrics request {method}: {e}")
            return ResponseBuilder.error(
                error="MetricsRequestError",
                message=f"Failed to process metrics request: {str(e)}"
            ).model_dump()
    
    async def _send_response(self, correlation_id: str, response_data: Dict[str, Any]):
        """Send response back to Core via RabbitMQ using dedicated response connection"""
        try:
            await self._setup_response_connection()
            
            # Prepare response message
            response_msg = {
                "correlation_id": correlation_id,
                "status": "success",
                "data": response_data,
                "timestamp": datetime.now().isoformat()
            }
            
            # Send response using dedicated connection
            message = aio_pika.Message(
                json.dumps(response_msg, default=json_serializer).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                content_type="application/json",
                headers={
                    'timestamp': datetime.utcnow().isoformat(),
                    'source': 'gps_service'
                }
            )
            
            await self._response_exchange.publish(message, routing_key=self.config.ROUTING_KEYS["core_responses"])
            
            logger.debug(f"📤 Sent response for correlation_id: {correlation_id}")
            
        except Exception as e:
            logger.error(f"❌ Error sending response for {correlation_id}: {e}")
            raise

    async def _send_error_response(self, correlation_id: str, error_message: str):
        """Send error response back to Core using dedicated response connection"""
        try:
            await self._setup_response_connection()
            
            response_msg = {
                "correlation_id": correlation_id,
                "status": "error",
                "error": {
                    "message": error_message,
                    "type": "ServiceError"
                },
                "timestamp": datetime.now().isoformat()
            }
            
            message = aio_pika.Message(
                json.dumps(response_msg, default=json_serializer).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                content_type="application/json",
                headers={
                    'timestamp': datetime.utcnow().isoformat(),
                    'source': 'gps_service'
                }
            )
            
            await self._response_exchange.publish(message, routing_key=self.config.ROUTING_KEYS["core_responses"])
            
            logger.debug(f"📤 Sent error response for correlation_id: {correlation_id}")
            
        except Exception as e:
            logger.error(f"❌ Error sending error response for {correlation_id}: {e}")
    
    async def _cleanup_old_requests(self):
        """Cleanup old request data to prevent memory leaks"""
        try:
            current_time = time.time()
            cleanup_threshold = 3600  # 1 hour
            
            # Clean up old request hashes
            old_hashes = [
                hash_key for hash_key, timestamp in self._request_hashes.items()
                if current_time - timestamp > cleanup_threshold
            ]
            
            for hash_key in old_hashes:
                del self._request_hashes[hash_key]
            
            # Clean up old pending requests
            old_requests = [
                req_id for req_id, timestamp in self._pending_requests.items()
                if current_time - timestamp > cleanup_threshold
            ]
            
            for req_id in old_requests:
                del self._pending_requests[req_id]
            
            if old_hashes or old_requests:
                logger.info(f"🧹 Cleaned up {len(old_hashes)} old request hashes and {len(old_requests)} old pending requests")
                
        except Exception as e:
            logger.error(f"❌ Error during request cleanup: {e}")
    
    async def _start_cleanup_task(self):
        """Start periodic cleanup task"""
        while True:
            try:
                await asyncio.sleep(1800)  # Run every 30 minutes
                await self._cleanup_old_requests()
            except Exception as e:
                logger.error(f"❌ Error in cleanup task: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    async def stop_consuming(self):
        """Stop consuming messages"""
        self.is_consuming = False
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
        logger.info("GPS service request consumer stopped")


# Global service request consumer instance
service_request_consumer = ServiceRequestConsumer()
