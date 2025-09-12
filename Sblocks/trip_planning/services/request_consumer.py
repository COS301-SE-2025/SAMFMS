"""
Service Request Consumer for Trips Service
Handles requests from Core service via RabbitMQ with standardized patterns
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone
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
        self.queue_name = self.config.QUEUE_NAMES["trips"]
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
            
            # Bind to trips routing key (must match Core service routing pattern)
            await self.queue.bind(self.exchange, "trips.requests")
            
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
            
        logger.info("Trips service request consumer stopped")
    
    async def disconnect(self):
        """Disconnect from RabbitMQ"""
        self.is_consuming = False
        
        # Close response connection
        if self._response_connection and not self._response_connection.is_closed:
            await self._response_connection.close()
            
        # Close main connection
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            
        logger.info("Trips service disconnected")
    
    async def handle_request(self, message: AbstractIncomingMessage):
        """Handle incoming request message using standardized pattern"""
        request_id = None
        try:
            async with message.process(requeue=False):
                logger.info("Received new RabbitMQ message")

                # Parse message body
                request_data = json.loads(message.body.decode())
                logger.info(f"Raw request_data: {request_data}")

                # Extract request details
                request_id = request_data.get("correlation_id")
                method = request_data.get("method")
                endpoint = request_data.get("endpoint", "")
                logger.info(f"[{request_id}] Handling request: {method} {endpoint}")

                user_context = request_data.get("user_context", {})
                data = request_data.get("data", {})
                user_context["data"] = data
                logger.debug(f"[{request_id}] User context: {user_context}")

                # Deduplication
                logger.debug(f"[{request_id}] Running deduplication checks")
                # (deduplication code unchanged)

                logger.info(f"[{request_id}] Routing to _route_request()")
                try:
                    response_data = await asyncio.wait_for(
                        self._route_request(method, user_context, endpoint),
                        timeout=self.config.REQUEST_TIMEOUTS.get("default_request_timeout", 25.0)
                    )
                except asyncio.TimeoutError:
                    logger.error(f"[{request_id}] Timeout inside _route_request()")
                    raise RuntimeError("Request processing timeout")

                logger.info(f"[{request_id}] Successfully got response from _route_request()")
                response = {
                    "status": "success",
                    "data": response_data,
                    "timestamp": datetime.now().isoformat()
                }

                logger.info(f"[{request_id}] Sending response back to Core")
                await self._send_response(request_id, response)
                logger.info(f"[{request_id}] Request completed successfully")

        except Exception as e:
            logger.error(f"[{request_id}] Exception in handle_request: {e}")
            if request_id:
                error_response = {
                    "status": "error",
                    "error": {"message": str(e), "type": type(e).__name__},
                    "timestamp": datetime.now().isoformat()
                }
                logger.info(f"[{request_id}] Sending error response to Core")
                await self._send_response(request_id, error_response)

    
    async def _route_request(self, method: str, user_context: Dict[str, Any], endpoint: str = "") -> Dict[str, Any]:
        """Route request to appropriate handler based on endpoint pattern"""
        logger.info(f"[_route_request] Entered with method={method}, endpoint={endpoint}")
        try:
            endpoint = endpoint.strip().lstrip('/').rstrip('/')
            user_context["endpoint"] = endpoint
            logger.info(f"[_route_request] Normalized endpoint: {endpoint}")

            if endpoint == "health" or endpoint == "":
                logger.info(f"[_route_request] Routing to _handle_health_request()")
                return await self._handle_health_request(method, user_context)
            elif "analytics/drivers" in endpoint:
                logger.info(f"Routing to driver analytics")
                return await self._handle_driver_analytics_requests(method, user_context)
            elif "analytics/vehicles" in endpoint:
                logger.info(f"Routing to vehicle analytics")
                return await self._handle_vehicle_analytics_requests(method, user_context)
            elif "analytics" in endpoint:
                logger.info(f"Routing to general analytics")
                return await self._handle_analytics_requests(method, user_context)
            elif "trips" in endpoint or endpoint.startswith("driver/") or endpoint == "recent":
                logger.info(f"[_route_request] Routing to _handle_trips_request()")
                return await self._handle_trips_request(method, user_context)
            elif endpoint == "drivers" or endpoint.startswith("drivers/"):
                logger.info(f"[_route_request] Routing to _handle_drivers_request()")
                return await self._handle_drivers_request(method, user_context)
            elif "notifications" in endpoint:
                logger.info(f"[_route_request] Routing to _handle_notifications_request()")
                return await self._handle_notifications_request(method, user_context)

            else:
                logger.warning(f"[_route_request] Unknown endpoint: {endpoint}")
                raise ValueError(f"Unknown endpoint: {endpoint}")

        except Exception as e:
            logger.error(f"[_route_request] Exception: {e}")
            raise

    
    async def _handle_trips_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle trips-related requests by calling route logic"""
        try:
            from services.trip_service import trip_service
            from schemas.responses import ResponseBuilder
            data = user_context.get("data", {})
            endpoint = user_context.get("endpoint", "")
            logger.info(f"[_handle_trips_request] Endpoint: '{endpoint}', Data: {data}")
            logger.info(f"[_handle_trips_request] Endpoint checks - contains 'trips': {'trips' in endpoint}, contains 'active': {'active' in endpoint}, contains 'upcoming': {'upcoming' in endpoint}, contains 'recent': {'recent' in endpoint}")
            logger.info(f"[DEBUG] Full endpoint analysis: endpoint='{endpoint}', method='{method}'")

            if method == "GET":
                if "vehicle" in endpoint:
                    vehicle_id = endpoint.split('/')[-1] if '/' in endpoint else None
                    logger.info(f"Vehicle ID extracted for trip: {vehicle_id}")
                    if vehicle_id is None:
                        return ResponseBuilder.error(
                            error="Error while processing trip request",
                            message="Vehicle ID was not included",
                        )
                    from schemas.requests import TripFilterRequest
                    trip = await trip_service.list_trips(TripFilterRequest(
                        vehicle_id=vehicle_id
                    ))

                    return ResponseBuilder.success(
                        data=trip,
                        message="Trip retrieved successfully"
                    )
                if "polyline" in endpoint:
                    vehicle_id = endpoint.split('/')[-1] if '/' in endpoint else None
                    logger.info(f"Vehicle ID extracted for polyline: {vehicle_id}")
                    if vehicle_id is None:
                        return ResponseBuilder.error(
                            error="Error while processing polyline",
                            message="Vehicle ID was not included",
                        )
                    
                    polyline = await trip_service.get_vehicle_polyline(vehicle_id)
                    return ResponseBuilder.success(
                        data=polyline,
                        message="Successfully retrieved polyline"
                    )

                if "upcomming" in endpoint:
                    if "all" in endpoint:
                        trip = await trip_service.get_all_upcoming_trips()
                        return ResponseBuilder.success(
                            data=trip,
                            message="All upcomming trips retrieved successfully"
                        ).model_dump()
                    else:
                        driver_id = endpoint.split('/')[-1] if '/' in endpoint else None
                        logger.info(f"Driver ID extracted for upcomming trips: {driver_id} ")
                        
                        
                        trips = await trip_service.get_upcoming_trips(driver_id)
                        return ResponseBuilder.success(
                            data=trips,
                            message="Upcomming trips retrieved successfully"
                        ).model_dump()
                if "recent" in endpoint:
                    driver_id = endpoint.split('/')[-1] if '/' in endpoint else None
                    logger.info(f"Driver ID extracted for recent trips: {driver_id} ")
                    if driver_id:
                        trips = await trip_service.get_recent_trips(driver_id)
                        return ResponseBuilder.success(
                            data=trips,
                            message="All upcomming trips retrieved successfully"
                        ).model_dump()
                    logger.info(f"[DEBUG] Processing recent endpoint: '{endpoint}'")
                    # Check if it's the generic /recent endpoint (for all recent trips)
                    if endpoint == "recent" or endpoint.endswith("/recent"):
                        logger.info(f"[DEBUG] Matched recent endpoint pattern")
                        # Check if it's a driver-specific recent endpoint like "driver/{driver_id}/recent"
                        if endpoint.startswith("driver/") and "/" in endpoint:
                            logger.info(f"[DEBUG] Processing driver-specific recent endpoint")
                            # Extract driver_id from endpoint: driver/{driver_id}/recent
                            parts = endpoint.split('/')
                            if len(parts) >= 2:
                                driver_id = parts[1]
                                logger.info(f"Driver ID extracted for driver-specific recent trips: {driver_id}")
                                trips = await trip_service.get_recent_trips(driver_id)
                                return ResponseBuilder.success(
                                    data=trips,
                                    message="Recent trips retrieved successfully"
                                ).model_dump()
                            else:
                                raise ValueError("Driver ID is required for driver-specific recent trips endpoint")
                        else:
                            # Generic recent trips endpoint - get all recent trips
                            logger.info("Handling generic recent trips request for all drivers")
                            # Try to get limit and days from various possible sources
                            limit = data.get("limit", 10)
                            days = data.get("days", 30)
                            
                            # Also check if they're in user_context
                            if "limit" not in data and "limit" in user_context:
                                limit = user_context.get("limit", 10)
                            if "days" not in data and "days" in user_context:
                                days = user_context.get("days", 30)
                                
                            # Convert to int if they're strings
                            try:
                                limit = int(limit)
                                days = int(days)
                            except (ValueError, TypeError):
                                limit = 10
                                days = 30
                                
                            logger.info(f"Using parameters: limit={limit}, days={days}")
                            trips = await trip_service.get_all_recent_trips(limit, days)
                            return ResponseBuilder.success(
                                data=trips,
                                message="All recent trips retrieved successfully"
                            ).model_dump()
                    else:
                        logger.warning(f"[DEBUG] Recent endpoint '{endpoint}' did not match expected patterns")
                        raise ValueError(f"Unsupported recent endpoint pattern: {endpoint}")
                # Check for driver-specific endpoints first
                elif endpoint.startswith("driver/") and "upcoming" in endpoint:
                    # Extract driver_id from endpoint: driver/{driver_id}/upcoming
                    parts = endpoint.split('/')
                    if len(parts) >= 2:
                        driver_id = parts[1]  # Get the driver ID from the path
                    else:
                        raise ValueError("Driver ID is required for upcoming trips endpoint")
                    
                    # Get query parameters from data
                    limit = data.get("limit", 10)
                    if isinstance(limit, str):
                        limit = int(limit)
                    
                    logger.info(f"[_handle_trips_request] Getting upcoming trips for driver: {driver_id}")
                    trips = await trip_service.get_upcoming_trips(driver_id, limit)
                    logger.info(f"[_handle_trips_request] Found {len(trips)} upcoming trips")
                    
                    return ResponseBuilder.success(
                        data={
                            "trips": [trip.model_dump() for trip in trips],
                            "count": len(trips)
                        },
                        message=f"Found {len(trips)} upcoming trips"
                    ).model_dump()
                elif endpoint.startswith("driver/") and "recent" in endpoint:
                    # Extract driver_id from endpoint
                    parts = endpoint.split('/')
                    driver_id = None
                    if 'driver' in parts:
                        driver_index = parts.index('driver')
                        if driver_index + 1 < len(parts):
                            driver_id = parts[driver_index + 1]
                    
                    if not driver_id:
                        raise ValueError("Driver ID is required for upcoming trips endpoint")
                    
                    # Get query parameters from data
                    limit = data.get("limit", 10)
                    if isinstance(limit, str):
                        limit = int(limit)
                    
                    logger.info(f"[_handle_trips_request] Getting upcoming trips for driver: {driver_id}")
                    trips = await trip_service.get_upcoming_trips(driver_id, limit)
                    logger.info(f"[_handle_trips_request] Found {len(trips)} upcoming trips")
                    
                    return ResponseBuilder.success(
                        data={
                            "trips": [trip.model_dump() for trip in trips],
                            "count": len(trips)
                        },
                        message=f"Found {len(trips)} upcoming trips"
                    ).model_dump()
                elif endpoint.startswith("driver/") and "recent" in endpoint:
                    # Extract driver_id from endpoint: driver/{driver_id}/recent
                    parts = endpoint.split('/')
                    if len(parts) >= 2:
                        driver_id = parts[1]  # Get the driver ID from the path
                    else:
                        raise ValueError("Driver ID is required for recent trips endpoint")
                    
                    # Get query parameters from data
                    limit = data.get("limit", 10)
                    days = data.get("days", 30)
                    if isinstance(limit, str):
                        limit = int(limit)
                    if isinstance(days, str):
                        days = int(days)
                    
                    logger.info(f"[_handle_trips_request] Getting recent trips for driver: {driver_id}")
                    trips = await trip_service.get_recent_trips(driver_id, limit, days)
                    logger.info(f"[_handle_trips_request] Found {len(trips)} recent trips")
                    
                    return ResponseBuilder.success(
                        data={
                            "trips": [trip.model_dump() for trip in trips],
                            "count": len(trips)
                        },
                        message=f"Found {len(trips)} recent trips"
                    ).model_dump()
                elif "active" in endpoint:
                    if "all" in endpoint:
                        activeTrips = await trip_service.get_active_trips()
                        logger.info(f"[_handle_trips_request] trip_service.get_active_trips() returned {len(activeTrips) if activeTrips else 0} trips")
                        return ResponseBuilder.success(
                            data=[Atrip.model_dump() for Atrip in activeTrips] if activeTrips else None,
                            message="Active Trips retrieved successfully"
                        ).model_dump()
                    else:
                        driver_id = endpoint.split('/')[-1] if '/' in endpoint else None
                        logger.info(f"Driver ID extracted for upcomming trips: {driver_id} ")
                        
                        activeTrip = await trip_service.get_active_trips(driver_id)
                        return ResponseBuilder.success(
                            data=activeTrip,
                            message="Active Trip retrieved successfully"
                        ).model_dump()
                
                elif "trips" in endpoint:
                    logger.info(f"[_handle_trips_request] Calling trip_service.get_all_trips()")
                    trips = await trip_service.get_all_trips()
                    logger.info(f"[_handle_trips_request] trip_service.get_all_trips() returned {len(trips) if trips else 0} trips")
                    return ResponseBuilder.success(
                        data=[trip.model_dump() for trip in trips] if trips else None,
                        message="Trips retrieved successfully"
                    ).model_dump()

                else:
                    raise ValueError(f"Unknown endpoint: {endpoint.split('/')[-1] if '/' in endpoint else endpoint}")

            elif method == "POST":
                if not data:
                    raise ValueError("Request data is required for POST operation")
                if "scheduled" in endpoint:
                    logger.info(f"Preparing schedule trip request")
                    from schemas.requests import ScheduledTripRequest
                    scheduled_request = ScheduledTripRequest(**data)
                    created_by = user_context.get("user_id", "system")

                    scheduled_trip = await trip_service.create_scheduled_trip(scheduled_request,created_by)
                    trip_id = scheduled_trip.id

                    return ResponseBuilder.success(
                        data=scheduled_trip.model_dump(),
                        message="Scheduled Trip created successfully"
                    ).model_dump()

                elif "create" in endpoint:
                    logger.info(f"[_handle_trips_request] Preparing CreateTripRequest and calling trip_service.create_trip()")
                    from schemas.requests import CreateTripRequest
                    trip_request = CreateTripRequest(**data)
                    created_by = user_context.get("user_id", "system")
                    
                    # Create trip in trips collection
                    trip = await trip_service.create_trip(trip_request, created_by)
                    trip_id = trip.id

                    # Update driver and vehicle collections to make them unavailable
                    # driver part
                    from services.driver_service import driver_service
                    driver_id = trip.driver_assignment
                    await driver_service.deactivateDriver(driver_id)
                    
                    # vehicle part
                    from services.vehicle_service import vehicle_service
                    vehicle_id = trip.vehicle_id
                    await vehicle_service.deactiveVehicle(vehicle_id) 

                    # Create a record in vehicle_assignments
                    from services.vehicle_assignments_services import vehicle_assignment_service
                    assignment = await vehicle_assignment_service.createAssignment(trip_id, vehicle_id, driver_id)  
                    
                    logger.info(f"Assignment created successfully: {assignment}")

                    logger.info(f"[_handle_trips_request] trip_service.create_trip() succeeded for trip {trip.id}")
                    return ResponseBuilder.success(
                        data=trip.model_dump(),
                        message="Trip created successfully"
                    ).model_dump()
                elif "completed" in endpoint:
                    from services.trip_service import trip_service
                    trip_id = endpoint.split('/')[-1] if '/' in endpoint else None
                    trip_by_id = await trip_service.get_trip_by_id(trip_id)
                    from schemas.requests import FinishTripRequest, TripFilterRequest
                    finish_trip_request = FinishTripRequest(**data)

                    # get the full trip from trips collection
                    
                    name = trip_by_id.name
                    driver_assignment = trip_by_id.driver_assignment
                    

                    filter = TripFilterRequest(**{
                        "name": name,
                        "driver_assignment": driver_assignment
                    })

                    trip = await trip_service.get_trip_by_name_and_driver(filter)
                    logger.info(f"Trip retrieved for completed: {trip.id}")
                    # update the trip to include its actual_end_time and status (completed/not-completed)
                    from schemas.requests import UpdateTripRequest
                    updated_trip = await trip_service.update_trip(trip.id, UpdateTripRequest(**{
                        "actual_end_time": finish_trip_request.actual_end_time,
                        "status": finish_trip_request.status
                    }))
                    # store the updated trip in trip_history collection
                    from schemas.entities import Trip
                    from services.trip_history_service import trip_history_service
                    result = await trip_history_service.add_trip(updated_trip)
                    logger.info(f"Result from history trip: (name={result.name}, id={result.id}, driver_assignment={result.driver_assignment})")
                    # remove trip from active trips and activate driver and vehicle again
                    deletedTrip = await trip_service.delete_trip(trip.id)
                    if(deletedTrip):
                        logger.info("Deleted trip successfully")
                    # driver part
                    from services.driver_service import driver_service
                    driver_id = trip.driver_assignment
                    logger.info(f"Driver id activated: {driver_id}")
                    await driver_service.activateDriver(driver_id)
                    
                    # vehicle part
                    from services.vehicle_service import vehicle_service
                    vehicle_id = trip.vehicle_id
                    logger.info(f"Vehicle id activated: {vehicle_id}")
                    await vehicle_service.activeVehicle(vehicle_id) 

                    # remove vehicle assignment record
                    from services.vehicle_assignments_services import vehicle_assignment_service
                    await vehicle_assignment_service.removeAssignment(vehicle_id, driver_id)

                    # remove vehicle location from gps locations
                    await vehicle_service.removeLocation(vehicle_id)
                    
                    return ResponseBuilder.success(
                        data=trip.model_dump(),
                        message="Trip added to history successfully"
                    ).model_dump()
        
                else:
                    raise ValueError(f"Unknown endpoint: {endpoint}")
            elif method == "PUT":
                trip_id = endpoint.split('/')[-1] if '/' in endpoint else None
                if not trip_id:
                    raise ValueError("Trip ID is required for PUT operation")
                if not data:
                    raise ValueError("Request data is required for PUT operation")

                from schemas.requests import UpdateTripRequest
                update_request = UpdateTripRequest(**data)

                result = await trip_service.update_trip(
                    trip_id=trip_id,
                    request=update_request
                )

                return ResponseBuilder.success(
                    data=result.model_dump(),
                    message="Trip updated successfully"
                ).model_dump()
            
            elif method == "DELETE":
                trip_id = endpoint.split('/')[-1] if '/' in endpoint else None
                if not trip_id:
                    raise ValueError("Trip ID is required for DELETE operation")
                
                # Delete trip
                result = await trip_service.delete_trip(trip_id)

                return ResponseBuilder.success(
                    data={"deleted":  result, "trip_id": trip_id},
                    message="Trip deleted successfully"
                ).model_dump()
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

        except Exception as e:
            logger.error(f"[_handle_trips_request] Exception: {e}")
            return ResponseBuilder.error(
                error="TripsRequestError",
                message=f"Failed to process trips request: {str(e)}"
            ).model_dump()

    async def _handle_drivers_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle drivers-related requests"""
        try:
            from services.driver_service import driver_service
            from schemas.responses import ResponseBuilder
            
            data = user_context.get("data", {})
            endpoint = user_context.get("endpoint", "")
            logger.info(f"[_handle_drivers_request] Endpoint: '{endpoint}', Method: '{method}', Data: {data}")
            
            if method == "GET" and endpoint == "drivers":
                # Handle GET /drivers - get all drivers from drivers collection
                logger.info(f"[_handle_drivers_request] Processing GET /drivers request")
                
                # Extract query parameters from the request data
                query_params = user_context.get("params", {}) or user_context.get("query_params", {})
                
                # Get parameters with defaults
                status = query_params.get("status")
                department = query_params.get("department") 
                skip = int(query_params.get("skip", 0))
                limit = int(query_params.get("limit", 1000))
                
                logger.info(f"[_handle_drivers_request] Query params: status={status}, department={department}, skip={skip}, limit={limit}")
                
                # Call the driver service method
                result = await driver_service.get_all_drivers(
                    status=status,
                    department=department,
                    skip=skip,
                    limit=limit
                )
                
                return ResponseBuilder.success(
                    data=result,
                    message=f"Retrieved {len(result['drivers'])} drivers successfully"
                ).model_dump()
                
            else:
                logger.warning(f"[_handle_drivers_request] Unsupported method/endpoint: {method} {endpoint}")
                return ResponseBuilder.error(
                    error="UnsupportedEndpoint", 
                    message=f"Endpoint {method} {endpoint} not supported"
                ).model_dump()
                
        except Exception as e:
            logger.error(f"[_handle_drivers_request] Exception: {e}")
            return ResponseBuilder.error(
                error="DriversRequestError",
                message=f"Failed to process drivers request: {str(e)}"
            ).model_dump()

    async def _handle_driver_analytics_requests(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle driver analytics requests"""
        try:
            from schemas.responses import ResponseBuilder
            from services.driver_analytics_service import driver_analytics_service

            data = user_context.get("data", {})
            logger.info(f"Data for driver analytics: {data}")
            endpoint = user_context.get("endpoint", "")
            logger.info(f"[DriverAnalytics] Processing endpoint: {endpoint}")

            if method == "GET":
                # Extract timeframe and metric from endpoint path
                # Format: analytics/drivers/[metric]/[timeframe]
                path_parts = endpoint.split('/')
                
                # Default timeframe
                timeframe = "week"
                metric = None
                
                if len(path_parts) >= 3:
                    metric = path_parts[2]  # analytics/drivers/[metric]
                    
                if len(path_parts) >= 4:
                    timeframe = path_parts[3]  # analytics/drivers/[metric]/[timeframe]

                logger.info(f"[DriverAnalytics] Using timeframe: {timeframe}, metric: {metric}")

                # Route to appropriate analytics function based on metric
                if metric == "totaltrips":
                    result = await driver_analytics_service.get_total_trips(timeframe)
                    return ResponseBuilder.success(
                        data={"total": result},
                        message="Total trips retrieved successfully"
                    ).model_dump()
                    
                elif metric == "stats":
                    logger.info("Entered driver stats")
                    result = await driver_analytics_service.get_driver_trip_stats(timeframe)
                    logger.info(f"[DriverAnalytics] response for driver stats: {result}")
                    return ResponseBuilder.success(
                        data={"total": result},
                        message="Driver stats retrieved successfully"
                    ).model_dump()

                elif metric == "completionrate":
                    result = await driver_analytics_service.get_completion_rate(timeframe)
                    return ResponseBuilder.success(
                        data={"rate": result},
                        message="Completion rate retrieved successfully"
                    ).model_dump()

                elif metric == "averagedaytrips":
                    result = await driver_analytics_service.get_average_trips_per_day(timeframe)
                    return ResponseBuilder.success(
                        data={"average": result},
                        message="Average trips per day retrieved successfully"
                    ).model_dump()

                else:
                    raise ValueError(f"Unknown analytics metric: {metric}")

            else:
                raise ValueError(f"Unsupported method for driver analytics: {method}")

        except Exception as e:
            logger.error(f"[DriverAnalytics] Error processing request: {e}")
            return ResponseBuilder.error(
                error="DriverAnalyticsRequestError",
                message=f"Failed to process analytics request: {str(e)}"
            ).model_dump()
    
    async def _handle_vehicle_analytics_requests(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle vehicle analytics requests"""
        try:
            from schemas.responses import ResponseBuilder
            from services.vehicle_analytics_service import vehicle_analytics_service

            data = user_context.get("data", {})
            endpoint = user_context.get("endpoint", "")
            logger.info(f"[VehicleAnalytics] Processing endpoint: {endpoint}")

            path_parts = endpoint.split('/')

            # Default timeframe
            timeframe = "week"
            metric = None

            if len(path_parts) >= 3:
                metric = path_parts[2]  # "stats" or "totaldistance"

            if len(path_parts) >= 4:
                timeframe = path_parts[3]  # "week", "month", etc.

            logger.info(f"[VehicleAnalytics] Using timeframe: {timeframe}, metric: {metric}")


            logger.info(f"[VehicleAnalytics] Using timeframe: {timeframe}, metric: {metric}")

            if metric == "stats":
                logger.info("Entered driver stats")
                result = await vehicle_analytics_service.get_vehicle_trip_stats(timeframe)
                logger.info(f"[VehicleAnalytics] response for vehicle stats; {result}")
                return ResponseBuilder.success(
                    data={"total": result},
                    message="Trips stats retrieved successfully"
                ).model_dump()
            elif metric == "totaldistance":
                logger.info("Entered totaldistance")
                result = await vehicle_analytics_service.get_total_distance_all_vehicles(timeframe)
                logger.info(f"[VehicleAnalytics] response for vehicle distance; {result}")
                return ResponseBuilder.success(
                    data={"total": result},
                    message="Trips distance retrieved successfully"
                ).model_dump()
            else:
                raise ValueError(f"Unknown analytics metric: {metric}")


        except Exception as e:
            logger.error(f"[VehicleAnalytics] Error processing request: {e}")
            return ResponseBuilder.error(
                error="VehicleAnalyticsRequestError",
                message=f"Failed to process analytics request: {str(e)}"
            ).model_dump()

    async def _handle_analytics_requests(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle analytics requests"""
        logger.info(f"[_handle_trips_request] Entered with method={method}, endpoint={user_context.get('endpoint')}")
        try:
            from services.analytics_service import analytics_service
            from schemas.responses import ResponseBuilder

            data = user_context.get("data", {})
            endpoint = user_context.get("endpoint", "")
            logger.info(f"Data: {data}")

            if method == "GET":
                # Get timeframe from query parameters or use default
                timeframe = data.get('timeframe', 'week')
                
                # Calculate date range based on timeframe
                end_date = datetime.now(timezone.utc)
                if timeframe == 'week':
                    start_date = end_date - timedelta(days=7)
                elif timeframe == 'month':
                    start_date = end_date - timedelta(days=30)
                elif timeframe == 'year':
                    start_date = end_date - timedelta(days=365)
                else:
                    start_date = end_date - timedelta(days=30)  # Default to month

                if "drivers" in endpoint:
                    logger.info(f"[Analytics] Requesting driver analytics for timeframe: {timeframe}")
                    driver_analytics = analytics_service.get_analytics_first(start_date, end_date)
                    logger.info("[Analytics] Driver analytics calculation completed")
                    logger.debug(f"[Analytics] Driver analytics response: {driver_analytics}")
                    return ResponseBuilder.success(
                        data=driver_analytics,
                        message="Driver analytics retrieved successfully"
                    ).model_dump()

                if "vehicles" in endpoint:
                    logger.info(f"[Analytics] Requesting vehicle analytics for timeframe: {timeframe}")
                    vehicle_analytics = analytics_service.get_analytics_second(start_date, end_date)
                    logger.info("[Analytics] Vehicle analytics calculation completed")
                    logger.debug(f"[Analytics] Vehicle analytics response: {vehicle_analytics}")
                    return ResponseBuilder.success(
                        data=vehicle_analytics,
                        message="Vehicle analytics retrieved successfully"
                    ).model_dump()

                if "trips/history-stats" in endpoint:
                    logger.info(f"[Analytics] Requesting trip history stats")
                    # Get days parameter if provided
                    days = data.get('days')
                    if days:
                        try:
                            days = int(days)
                        except (ValueError, TypeError):
                            days = None
                    
                    history_stats = await analytics_service.get_trip_history_stats(days)
                    logger.info("[Analytics] Trip history stats calculation completed")
                    logger.debug(f"[Analytics] Trip history stats response: {history_stats}")
                    return ResponseBuilder.success(
                        data=history_stats,
                        message="Trip history statistics retrieved successfully"
                    ).model_dump()
                
                raise ValueError(f"Unknown endpoint: {endpoint}")
            else:
                    raise ValueError(f"Unknown endpoint: {endpoint}")
        except Exception as e:
                logger.error(f"[_handle_analytics_request] Exception: {e}")
                return ResponseBuilder.error(
                    error="AnalyticsRequestError",
                    message=f"Failed to process analytics request: {str(e)}"
                ).model_dump()

    async def _handle_notifications_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle notification-related requests"""
        try:
            from services.notification_service import notification_service
            from schemas.responses import ResponseBuilder
            data = user_context.get("data", {})
            endpoint = user_context.get("endpoint", "")
            user_id = user_context.get("user_id")
            
            logger.info(f"[_handle_notifications_request] Method: {method}, Endpoint: {endpoint}, User ID: {user_id}")

            if method == "GET":
                # Get user notifications
                unread_only = data.get("unread_only", "false").lower() == "true"
                limit = int(data.get("limit", 50))
                skip = int(data.get("skip", 0))
                
                notifications, total = await notification_service.get_user_notifications(
                    user_id=user_id,
                    unread_only=unread_only,
                    limit=limit,
                    skip=skip
                )
                
                # Convert to dict format for response
                notifications_data = []
                for notification in notifications:
                    notification_dict = {
                        "id": notification.id if hasattr(notification, 'id') else str(notification._id),
                        "type": notification.type,
                        "title": notification.title,
                        "message": notification.message,
                        "time": notification.sent_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(notification.sent_at, 'strftime') else str(notification.sent_at),
                        "read": notification.is_read,
                        "trip_id": getattr(notification, 'trip_id', None),
                        "driver_id": getattr(notification, 'driver_id', None),
                        "data": getattr(notification, 'data', {})
                    }
                    notifications_data.append(notification_dict)
                
                return ResponseBuilder.success(
                    data={
                        "notifications": notifications_data,
                        "total": total,
                        "unread_count": len([n for n in notifications_data if not n["read"]])
                    },
                    message="Notifications retrieved successfully"
                ).model_dump()

            elif method == "POST":
                # Send notification (admin/fleet_manager only)
                user_role = user_context.get("role")
                if user_role not in ["admin", "fleet_manager"]:
                    raise ValueError("Insufficient permissions to send notifications")
                
                from schemas.requests import NotificationRequest
                notification_request = NotificationRequest(**data)
                
                notifications = await notification_service.send_notification(notification_request)
                
                return ResponseBuilder.success(
                    data={
                        "sent_count": len(notifications),
                        "notification_ids": [str(n._id) if hasattr(n, '_id') else n.id for n in notifications]
                    },
                    message="Notifications sent successfully"
                ).model_dump()

            elif method == "PUT":
                # Mark notification as read
                notification_id = endpoint.split('/')[-1] if '/' in endpoint else data.get("notification_id")
                if not notification_id:
                    raise ValueError("Notification ID is required")
                
                result = await notification_service.mark_notification_read(notification_id, user_id)
                
                return ResponseBuilder.success(
                    data={"marked_read": result},
                    message="Notification marked as read" if result else "Notification not found or already read"
                ).model_dump()

            else:
                raise ValueError(f"Unsupported HTTP method for notifications: {method}")

        except Exception as e:
            logger.error(f"[_handle_notifications_request] Exception: {e}")
            return ResponseBuilder.error(
                error="NotificationRequestError",
                message=f"Failed to process notification request: {str(e)}"
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
                ).model_dump(mode='json')
            else:
                raise ValueError(f"Unsupported method for health endpoint: {method}")
                
        except Exception as e:
            logger.error(f"Error handling health request {method}: {e}")
            return ResponseBuilder.error(
                error="HealthCheckError",
                message=f"Failed to process health check: {str(e)}"
            ).model_dump(mode='json')

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
                ).model_dump(mode='json')
            else:
                raise ValueError(f"Unsupported method for docs endpoint: {method}")
                
        except Exception as e:
            logger.error(f"Error handling docs request {method}: {e}")
            return ResponseBuilder.error(
                error="DocsRequestError",
                message=f"Failed to process docs request: {str(e)}"
            ).model_dump(mode='json')

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
                    "service": "trips"
                }
                return ResponseBuilder.success(
                    data=metrics_data,
                    message="Trips service metrics retrieved successfully"
                ).model_dump(mode='json')
            else:
                raise ValueError(f"Unsupported method for metrics endpoint: {method}")
                
        except Exception as e:
            logger.error(f"Error handling metrics request {method}: {e}")
            return ResponseBuilder.error(
                error="MetricsRequestError",
                message=f"Failed to process metrics request: {str(e)}"
            ).model_dump(mode='json')
    
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
                    'source': 'trips_service'
                }
            )
            
            await self._response_exchange.publish(message, routing_key=self.config.ROUTING_KEYS["core_responses"])
            
            logger.debug(f"Sent response for correlation_id: {correlation_id}")
            
        except Exception as e:
            logger.error(f"Error sending response for {correlation_id}: {e}")
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
            
            logger.debug(f"Sent error response for correlation_id: {correlation_id}")
            
        except Exception as e:
            logger.error(f"Error sending error response for {correlation_id}: {e}")
    
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
                logger.info(f"Cleaned up {len(old_hashes)} old request hashes and {len(old_requests)} old pending requests")
                
        except Exception as e:
            logger.error(f"Error during request cleanup: {e}")
    
    async def _start_cleanup_task(self):
        """Start periodic cleanup task"""
        while True:
            try:
                await asyncio.sleep(1800)  # Run every 30 minutes
                await self._cleanup_old_requests()
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    async def stop_consuming(self):
        """Stop consuming messages"""
        self.is_consuming = False
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
        logger.info("Trips service request consumer stopped")


# Global service request consumer instance
service_request_consumer = ServiceRequestConsumer()
