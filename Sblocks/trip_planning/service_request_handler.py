"""
Service Request Handler for Trip Planning Service
Handles incoming requests from Core via RabbitMQ
"""

import asyncio
import os
import json
import logging
from typing import Dict, Any
from datetime import datetime
import aio_pika

logger = logging.getLogger(__name__)

class TripPlanningRequestHandler:
    """Handles RabbitMQ request/response pattern for Trip Planning service"""
    
    def __init__(self):
        self.connection = None
        self.channel = None
        self.response_exchange = None
        self.endpoint_handlers = {
            "/api/trips": {
                "GET": self._get_trips,
                "POST": self._create_trip,
                "PUT": self._update_trip,
                "DELETE": self._delete_trip
            },
            "/api/trip-planning": {
                "GET": self._get_trip_plans,
                "POST": self._create_trip_plan
            }
        }
    
    async def initialize(self):
        """Initialize request handler and start consuming"""
        try:
            # Set up persistent connection for responses
            await self._setup_response_connection()
            await self._setup_request_consumption()
            logger.info("Trip Planning service request handler initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Trip Planning request handler: {e}")
            raise
    
    async def _setup_response_connection(self):
        """Set up persistent connection for sending responses"""
        self.connection = await aio_pika.connect_robust(os.getenv("RABBITMQ_URL", "amqp://samfms_rabbit:RabbitPass2025!@rabbitmq:5672/"))
        self.channel = await self.connection.channel()
        self.response_exchange = await self.channel.declare_exchange("service_responses", aio_pika.ExchangeType.DIRECT, durable=True)
    
    async def _setup_request_consumption(self):
        """Set up RabbitMQ to consume requests from Core"""
        connection = await aio_pika.connect_robust(os.getenv("RABBITMQ_URL", "amqp://samfms_rabbit:RabbitPass2025!@rabbitmq:5672/"))
        channel = await connection.channel()
        
        request_queue = await channel.declare_queue("trip_planning.requests", durable=True)
        await channel.set_qos(prefetch_count=1)
        
        await request_queue.consume(self._handle_request_message)
        logger.info("Started consuming Trip Planning requests")
    
    async def _handle_request_message(self, message: aio_pika.IncomingMessage):
        """Handle incoming request message from Core"""
        async with message.process():
            try:
                request_data = json.loads(message.body.decode())
                
                correlation_id = request_data.get("correlation_id")
                endpoint = request_data.get("endpoint")
                method = request_data.get("method")
                data = request_data.get("data", {})
                user_context = request_data.get("user_context", {})
                
                logger.info(f"Processing Trip Planning request {correlation_id}: {method} {endpoint}")
                
                result = await self.route_to_handler(endpoint, method, data, user_context)
                
                response = {
                    "correlation_id": correlation_id,
                    "status": "success",
                    "data": result,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await self._send_response(response)
                
            except Exception as e:
                logger.error(f"Error processing Trip Planning request: {e}")
                error_response = {
                    "correlation_id": request_data.get("correlation_id", "unknown"),
                    "status": "error", 
                    "error": {
                        "message": str(e),
                        "type": type(e).__name__
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                await self._send_response(error_response)
    
    async def route_to_handler(self, endpoint: str, method: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Any:
        """Route request to appropriate handler"""
        try:
            base_endpoint = self._get_base_endpoint(endpoint)
            endpoint_handlers = self.endpoint_handlers.get(base_endpoint, {})
            handler = endpoint_handlers.get(method.upper())
            
            if not handler:
                raise ValueError(f"No handler found for {method} {endpoint}")
            
            result = await handler(endpoint, data, user_context)
            return result
            
        except Exception as e:
            logger.error(f"Error routing Trip Planning request {method} {endpoint}: {e}")
            raise
    
    def _get_base_endpoint(self, endpoint: str) -> str:
        """Extract base endpoint from full endpoint path"""
        parts = endpoint.split('/')
        if len(parts) >= 3:
            return f"/{parts[1]}/{parts[2]}"
        return endpoint
    
    async def _send_response(self, response: Dict[str, Any]):
        """Send response back to Core via RabbitMQ"""
        try:
            await self.response_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(response).encode(),
                    content_type="application/json"
                ),
                routing_key="core.responses"
            )
            
            logger.debug(f"Trip Planning response sent for correlation_id: {response.get('correlation_id')}")
            
        except Exception as e:
            logger.error(f"Error sending Trip Planning response: {e}")
    
    # Trip handlers
    async def _get_trips(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle GET /api/trips"""
        try:
            # Mock trip data
            trips = [
                {
                    "id": "trip_001",
                    "name": "Johannesburg to Cape Town",
                    "driver_id": "driver_001",
                    "vehicle_id": "vehicle_001",
                    "start_location": "Johannesburg",
                    "end_location": "Cape Town",
                    "start_time": "2025-06-20T08:00:00Z",
                    "end_time": "2025-06-20T18:00:00Z",
                    "status": "planned",
                    "distance": 1400
                },
                {
                    "id": "trip_002",
                    "name": "Durban to Pretoria",
                    "driver_id": "driver_002", 
                    "vehicle_id": "vehicle_002",
                    "start_location": "Durban",
                    "end_location": "Pretoria",
                    "start_time": "2025-06-20T06:00:00Z",
                    "end_time": "2025-06-20T14:00:00Z",
                    "status": "in_progress",
                    "distance": 560
                }
            ]
            
            # Filter by user role
            if user_context.get("role") == "driver":
                driver_id = user_context.get("user_id")
                trips = [trip for trip in trips if trip["driver_id"] == driver_id]
            
            return {"trips": trips, "count": len(trips)}
            
        except Exception as e:
            logger.error(f"Error getting trips: {e}")
            raise
    
    async def _create_trip(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle POST /api/trips"""
        try:
            # Validate permissions
            if user_context.get("role") not in ["admin", "fleet_manager"]:
                raise ValueError("Insufficient permissions to create trip")
            
            # Validate required fields
            required_fields = ["name", "start_location", "end_location", "start_time"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Create trip
            trip_data = {
                "id": f"trip_{datetime.utcnow().timestamp()}",
                "name": data["name"],
                "driver_id": data.get("driver_id"),
                "vehicle_id": data.get("vehicle_id"),
                "start_location": data["start_location"],
                "end_location": data["end_location"],
                "start_time": data["start_time"],
                "end_time": data.get("end_time"),
                "status": "planned",
                "distance": data.get("distance", 0),
                "created_by": user_context.get("user_id"),
                "created_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Created trip: {trip_data['name']}")
            
            return trip_data
            
        except Exception as e:
            logger.error(f"Error creating trip: {e}")
            raise
    
    async def _update_trip(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle PUT /api/trips/{id}"""
        try:
            trip_id = endpoint.split('/')[-1]
            
            if user_context.get("role") not in ["admin", "fleet_manager"]:
                raise ValueError("Insufficient permissions to update trip")
            
            # Mock update
            updated_trip = {
                "id": trip_id,
                "updated_by": user_context.get("user_id"),
                "updated_at": datetime.utcnow().isoformat(),
                **data
            }
            
            logger.info(f"Updated trip: {trip_id}")
            
            return updated_trip
            
        except Exception as e:
            logger.error(f"Error updating trip: {e}")
            raise
    
    async def _delete_trip(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle DELETE /api/trips/{id}"""
        try:
            trip_id = endpoint.split('/')[-1]
            
            if user_context.get("role") != "admin":
                raise ValueError("Only administrators can delete trips")
            
            logger.info(f"Deleted trip: {trip_id}")
            
            return {"message": f"Trip {trip_id} deleted successfully"}
            
        except Exception as e:
            logger.error(f"Error deleting trip: {e}")
            raise
    
    # Trip Planning handlers
    async def _get_trip_plans(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle GET /api/trip-planning"""
        try:
            # Mock trip planning data
            planning_data = {
                "upcoming_trips": 5,
                "total_distance": 3500,
                "estimated_fuel_cost": 2800.50,
                "optimization_suggestions": [
                    "Combine trips to Cape Town",
                    "Use Highway N1 for better fuel efficiency",
                    "Schedule maintenance before long distance trips"
                ]
            }
            
            return planning_data
            
        except Exception as e:
            logger.error(f"Error getting trip plans: {e}")
            raise
    
    async def _create_trip_plan(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle POST /api/trip-planning"""
        try:
            if user_context.get("role") not in ["admin", "fleet_manager"]:
                raise ValueError("Insufficient permissions to create trip plan")
            
            plan_data = {
                "id": f"plan_{datetime.utcnow().timestamp()}",
                "name": data.get("name", "New Trip Plan"),
                "routes": data.get("routes", []),
                "optimization_type": data.get("optimization_type", "distance"),
                "created_by": user_context.get("user_id"),
                "created_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Created trip plan: {plan_data['name']}")
            
            return plan_data
            
        except Exception as e:
            logger.error(f"Error creating trip plan: {e}")
            raise


# Global instance
trip_planning_request_handler = TripPlanningRequestHandler()
