"""
Service Request Handler for GPS Service
Handles incoming requests from Core via RabbitMQ
"""

import asyncio
import json
import logging
from typing import Dict, Any
from datetime import datetime
import aio_pika

logger = logging.getLogger(__name__)

class GPSServiceRequestHandler:
    """Handles RabbitMQ request/response pattern for GPS service"""
    
    def __init__(self):
        self.endpoint_handlers = {
            "/api/gps/locations": {
                "GET": self._get_gps_locations,
                "POST": self._create_gps_location
            },
            "/api/tracking": {
                "GET": self._get_tracking_data,
                "POST": self._update_tracking_data
            }
        }
    
    async def initialize(self):
        """Initialize request handler and start consuming"""
        try:
            await self._setup_request_consumption()
            logger.info("GPS service request handler initialized")
        except Exception as e:
            logger.error(f"Failed to initialize GPS request handler: {e}")
            raise
    
    async def _setup_request_consumption(self):
        """Set up RabbitMQ to consume requests from Core"""
        connection = await aio_pika.connect_robust("amqp://guest:guest@rabbitmq/")
        channel = await connection.channel()
        
        # Declare request queue
        request_queue = await channel.declare_queue("gps.requests", durable=True)
        await channel.set_qos(prefetch_count=1)
        
        # Start consuming
        await request_queue.consume(self._handle_request_message)
        logger.info("Started consuming GPS requests")
    
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
                
                logger.info(f"Processing GPS request {correlation_id}: {method} {endpoint}")
                
                result = await self.route_to_handler(endpoint, method, data, user_context)
                
                response = {
                    "correlation_id": correlation_id,
                    "status": "success",
                    "data": result,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await self._send_response(response)
                
            except Exception as e:
                logger.error(f"Error processing GPS request: {e}")
                error_response = {
                    "correlation_id": request_data.get("correlation_id", "unknown"),
                    "status": "error",
                    "error": str(e),
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
            logger.error(f"Error routing GPS request {method} {endpoint}: {e}")
            raise
    
    def _get_base_endpoint(self, endpoint: str) -> str:
        """Extract base endpoint from full endpoint path"""
        parts = endpoint.split('/')
        if len(parts) >= 4:  # /api/gps/locations
            return f"/{parts[1]}/{parts[2]}/{parts[3]}"
        elif len(parts) >= 3:  # /api/tracking
            return f"/{parts[1]}/{parts[2]}"
        return endpoint
    
    async def _send_response(self, response: Dict[str, Any]):
        """Send response back to Core via RabbitMQ"""
        try:
            connection = await aio_pika.connect_robust("amqp://guest:guest@rabbitmq/")
            channel = await connection.channel()
            
            exchange = await channel.declare_exchange("service_responses", aio_pika.ExchangeType.DIRECT)
            
            await exchange.publish(
                aio_pika.Message(
                    body=json.dumps(response).encode(),
                    content_type="application/json"
                ),
                routing_key="core.responses"
            )
            
            await connection.close()
            logger.debug(f"GPS response sent for correlation_id: {response.get('correlation_id')}")
            
        except Exception as e:
            logger.error(f"Error sending GPS response: {e}")
    
    # GPS Location handlers
    async def _get_gps_locations(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle GET /api/gps/locations"""
        try:
            # Mock GPS locations data - replace with actual database queries
            locations = [
                {
                    "id": "1",
                    "vehicle_id": "vehicle_001",
                    "latitude": -26.2041,
                    "longitude": 28.0473,
                    "timestamp": datetime.utcnow().isoformat(),
                    "speed": 60.5,
                    "heading": 180
                },
                {
                    "id": "2", 
                    "vehicle_id": "vehicle_002",
                    "latitude": -26.1956,
                    "longitude": 28.0339,
                    "timestamp": datetime.utcnow().isoformat(),
                    "speed": 45.2,
                    "heading": 90
                }
            ]
            
            # Filter by vehicle_id if specified
            vehicle_id = data.get("vehicle_id")
            if vehicle_id:
                locations = [loc for loc in locations if loc["vehicle_id"] == vehicle_id]
            
            # Apply user-based filtering
            if user_context.get("role") == "driver":
                # Drivers only see their assigned vehicle locations
                driver_vehicle_id = data.get("assigned_vehicle_id")  # Would come from user context
                if driver_vehicle_id:
                    locations = [loc for loc in locations if loc["vehicle_id"] == driver_vehicle_id]
            
            return {"locations": locations, "count": len(locations)}
            
        except Exception as e:
            logger.error(f"Error getting GPS locations: {e}")
            raise
    
    async def _create_gps_location(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle POST /api/gps/locations"""
        try:
            # Validate required fields
            required_fields = ["vehicle_id", "latitude", "longitude"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Create location record - replace with actual database insert
            location_data = {
                "id": f"loc_{datetime.utcnow().timestamp()}",
                "vehicle_id": data["vehicle_id"],
                "latitude": data["latitude"],
                "longitude": data["longitude"],
                "timestamp": datetime.utcnow().isoformat(),
                "speed": data.get("speed", 0),
                "heading": data.get("heading", 0),
                "created_by": user_context.get("user_id")
            }
            
            logger.info(f"Created GPS location for vehicle {data['vehicle_id']}")
            
            return location_data
            
        except Exception as e:
            logger.error(f"Error creating GPS location: {e}")
            raise
    
    # Tracking handlers
    async def _get_tracking_data(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle GET /api/tracking"""
        try:
            # Mock tracking data
            tracking_data = {
                "active_vehicles": 15,
                "total_distance_today": 1250.5,
                "average_speed": 52.3,
                "vehicles_on_route": [
                    {
                        "vehicle_id": "vehicle_001",
                        "driver": "John Doe",
                        "route": "Route A",
                        "eta": "14:30",
                        "current_location": {"lat": -26.2041, "lng": 28.0473}
                    },
                    {
                        "vehicle_id": "vehicle_002", 
                        "driver": "Jane Smith",
                        "route": "Route B",
                        "eta": "15:15",
                        "current_location": {"lat": -26.1956, "lng": 28.0339}
                    }
                ]
            }
            
            # Filter data based on user role
            if user_context.get("role") == "driver":
                # Drivers only see their own tracking data
                user_vehicle = next(
                    (v for v in tracking_data["vehicles_on_route"] 
                     if v.get("driver_id") == user_context.get("user_id")), 
                    None
                )
                tracking_data["vehicles_on_route"] = [user_vehicle] if user_vehicle else []
                tracking_data["active_vehicles"] = 1 if user_vehicle else 0
            
            return tracking_data
            
        except Exception as e:
            logger.error(f"Error getting tracking data: {e}")
            raise
    
    async def _update_tracking_data(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle POST /api/tracking"""
        try:
            # Update tracking information - replace with actual implementation
            tracking_update = {
                "vehicle_id": data.get("vehicle_id"),
                "location": data.get("location"),
                "status": data.get("status", "active"),
                "updated_at": datetime.utcnow().isoformat(),
                "updated_by": user_context.get("user_id")
            }
            
            logger.info(f"Updated tracking for vehicle {data.get('vehicle_id')}")
            
            return tracking_update
            
        except Exception as e:
            logger.error(f"Error updating tracking data: {e}")
            raise


# Global instance
gps_request_handler = GPSServiceRequestHandler()
