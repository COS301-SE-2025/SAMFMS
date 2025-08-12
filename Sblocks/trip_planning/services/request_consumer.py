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
            logger.debug(f"[_route_request] Normalized endpoint: {endpoint}")

            if endpoint == "health" or endpoint == "":
                logger.info(f"[_route_request] Routing to _handle_health_request()")
                return await self._handle_health_request(method, user_context)
            elif "trips" in endpoint:
                logger.info(f"[_route_request] Routing to _handle_trips_request()")
                return await self._handle_trips_request(method, user_context)
            elif "analytics" in endpoint:
                logger.inf(f"Routing to analytics")
                return await self._handle_analytics_requests()
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
            logger.info(f"[_handle_trips_request] Data: {data}")

            if method == "GET":
                if "trips" in endpoint:
                    logger.info(f"[_handle_trips_request] Calling trip_service.get_all_trips()")
                    trips = await trip_service.get_all_trips()
                    logger.info(f"[_handle_trips_request] trip_service.get_all_trips() returned {len(trips) if trips else 0} trips")
                    return ResponseBuilder.success(
                        data=[trip.model_dump() for trip in trips] if trips else None,
                        message="Trips retrieved successfully"
                    ).model_dump()
                if "active" in endpoint:
                    activeTrips = await trip_service.get_active_trips()
                    logger.info(f"[_handle_trips_request] trip_service.get_active_trips() returned {len(trips) if trips else 0} trips")
                    return ResponseBuilder.success(
                        data=[Atrip.model_dump() for Atrip in activeTrips] if activeTrips else None,
                        message="Active Trips retrieved successfully"
                    ).model_dump()
                else:
                    raise ValueError(f"Unknown endpoint: {endpoint}")

            elif method == "POST":
                if not data:
                    raise ValueError("Request data is required for POST operation")

                if "create" in endpoint:
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
                    from schemas.requests import FinishTripRequest, TripFilterRequest
                    finish_trip_request = FinishTripRequest(**data)

                    # get the full trip from trips collection
                    from services.trip_service import trip_service
                    name = finish_trip_request.name
                    driver_assignment = finish_trip_request.driver_assignment
                    

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
                    await driver_service.activateDriver(driver_id)
                    
                    # vehicle part
                    from services.vehicle_service import vehicle_service
                    vehicle_id = trip.vehicle_id
                    await vehicle_service.activeVehicle(vehicle_id) 
                    
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
                
                raise ValueError(f"Unknown endpoint: {endpoint}")
            else:
                    raise ValueError(f"Unknown endpoint: {endpoint}")
        except Exception as e:
                logger.error(f"[_handle_analytics_request] Exception: {e}")
                return ResponseBuilder.error(
                    error="AnalyticsRequestError",
                    message=f"Failed to process analytics request: {str(e)}"
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
