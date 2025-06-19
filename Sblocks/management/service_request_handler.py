"""
Service Request Handler for Management Service
Handles incoming requests from Core via RabbitMQ
"""

import asyncio
import json
import logging
from typing import Dict, Any, Callable
from datetime import datetime
import pika
import aio_pika
from bson import ObjectId

from models import VehicleAssignment, VehicleUsageLog, VehicleStatus
from routes import router as management_router
from database import get_mongodb
from message_queue import mq_service

logger = logging.getLogger(__name__)

class ServiceRequestHandler:
    """Handles RabbitMQ request/response pattern for Management service"""
    
    def __init__(self):
        self.handlers = {
            "GET": self._handle_get_request,
            "POST": self._handle_post_request,
            "PUT": self._handle_put_request,
            "DELETE": self._handle_delete_request
        }
        
        self.endpoint_handlers = {
            "/api/vehicles": {
                "GET": self._get_vehicles,
                "POST": self._create_vehicle,
                "PUT": self._update_vehicle,
                "DELETE": self._delete_vehicle
            },
            "/api/vehicles/search": {
                "GET": self._search_vehicles
            },
            "/api/vehicle-assignments": {
                "GET": self._get_vehicle_assignments,
                "POST": self._create_vehicle_assignment,
                "PUT": self._update_vehicle_assignment,
                "DELETE": self._delete_vehicle_assignment
            },
            "/api/vehicle-usage": {
                "GET": self._get_vehicle_usage,
                "POST": self._create_vehicle_usage,
                "PUT": self._update_vehicle_usage
            }
        }
    
    async def initialize(self):
        """Initialize request handler and start consuming"""
        try:
            # Set up RabbitMQ for requests
            await self._setup_request_consumption()
            logger.info("Management service request handler initialized")
        except Exception as e:
            logger.error(f"Failed to initialize request handler: {e}")
            raise
    
    async def _setup_request_consumption(self):
        """Set up RabbitMQ to consume requests from Core"""
        # Using async RabbitMQ for better performance
        connection = await aio_pika.connect_robust("amqp://guest:guest@rabbitmq/")
        channel = await connection.channel()
        
        # Declare request queue
        request_queue = await channel.declare_queue("management.requests", durable=True)
        
        # Set QoS to process one message at a time
        await channel.set_qos(prefetch_count=1)
        
        # Start consuming
        await request_queue.consume(self._handle_request_message)
        logger.info("Started consuming management requests")
    
    async def _handle_request_message(self, message: aio_pika.IncomingMessage):
        """Handle incoming request message from Core"""
        async with message.process():
            try:
                # Parse request
                request_data = json.loads(message.body.decode())
                
                correlation_id = request_data.get("correlation_id")
                endpoint = request_data.get("endpoint")
                method = request_data.get("method")
                data = request_data.get("data", {})
                user_context = request_data.get("user_context", {})
                
                logger.info(f"Processing request {correlation_id}: {method} {endpoint}")
                
                # Route to appropriate handler
                result = await self.route_to_handler(endpoint, method, data, user_context)
                
                # Send success response
                response = {
                    "correlation_id": correlation_id,
                    "status": "success",
                    "data": result,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await self._send_response(response)
                
            except Exception as e:
                logger.error(f"Error processing request: {e}")
                # Send error response
                error_response = {
                    "correlation_id": request_data.get("correlation_id", "unknown"),
                    "status": "error",                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
                await self._send_response(error_response)
    
    async def route_to_handler(self, endpoint: str, method: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Any:
        """Route request to appropriate handler based on endpoint and method"""
        try:
            # Extract base endpoint (remove IDs)
            base_endpoint = self._get_base_endpoint(endpoint)
            
            # Get handler for endpoint and method
            endpoint_handlers = self.endpoint_handlers.get(base_endpoint, {})
            handler = endpoint_handlers.get(method.upper())
            
            if not handler:
                raise ValueError(f"No handler found for {method} {endpoint}")
            
            # Call handler with data and user context
            result = await handler(endpoint, data, user_context)
            return result
            
        except Exception as e:
            logger.error(f"Error routing request {method} {endpoint}: {e}")
            raise
    
    def _get_base_endpoint(self, endpoint: str) -> str:
        """Extract base endpoint from full endpoint path"""
        parts = endpoint.split('/')
        
        # Handle search endpoints specially
        if len(parts) >= 4 and parts[3] == "search":
            return f"/{parts[1]}/{parts[2]}/search"
        
        if len(parts) >= 3:
            return f"/{parts[1]}/{parts[2]}"
        return endpoint
    
    async def _send_response(self, response: Dict[str, Any]):
        """Send response back to Core via RabbitMQ"""
        try:
            connection = await aio_pika.connect_robust("amqp://guest:guest@rabbitmq/")
            channel = await connection.channel()
            
            # Declare response exchange
            exchange = await channel.declare_exchange("service_responses", aio_pika.ExchangeType.DIRECT)
            
            # Send response to core.responses queue
            await exchange.publish(
                aio_pika.Message(
                    body=json.dumps(response).encode(),
                    content_type="application/json"
                ),
                routing_key="core.responses"
            )
            
            await connection.close()
            logger.debug(f"Response sent for correlation_id: {response.get('correlation_id')}")
            
        except Exception as e:
            logger.error(f"Error sending response: {e}")
    
    # Vehicle handlers
    async def _get_vehicles(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle GET /api/vehicles"""
        try:
            # Extract vehicle ID if present
            if len(endpoint.split('/')) > 3:
                vehicle_id = endpoint.split('/')[-1]
                return await self._get_single_vehicle(vehicle_id, user_context)
            
            # Get all vehicles with filtering
            db = await get_mongodb()
            query = {}
            
            # Apply user-based filtering
            if user_context.get("role") == "driver":
                # Drivers only see their assigned vehicles
                query["assigned_driver_id"] = user_context.get("user_id")
            
            vehicles = await db.vehicles.find(query).to_list(100)
            
            # Convert ObjectId to string
            for vehicle in vehicles:
                vehicle["_id"] = str(vehicle["_id"])
            
            return {"vehicles": vehicles, "count": len(vehicles)}
            
        except Exception as e:
            logger.error(f"Error getting vehicles: {e}")
            raise
    async def _get_single_vehicle(self, vehicle_id: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Get single vehicle by ID"""
        try:
            db = await get_mongodb()
            
            # Convert string ID to ObjectId if needed
            try:
                if isinstance(vehicle_id, str) and len(vehicle_id) == 24:
                    query_id = ObjectId(vehicle_id)
                else:
                    query_id = vehicle_id
            except:
                query_id = vehicle_id
            
            vehicle = await db.vehicles.find_one({"_id": query_id})
            
            if not vehicle:
                raise ValueError(f"Vehicle {vehicle_id} not found")
            
            # Check access permissions
            if user_context.get("role") == "driver":
                if vehicle.get("assigned_driver_id") != user_context.get("user_id"):
                    raise ValueError("Access denied to this vehicle")
            
            vehicle["_id"] = str(vehicle["_id"])
            return vehicle
            
        except Exception as e:
            logger.error(f"Error getting vehicle {vehicle_id}: {e}")
            raise
    
    async def _create_vehicle(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle POST /api/vehicles"""
        try:
            # Validate permissions
            if user_context.get("role") not in ["admin", "fleet_manager"]:
                raise ValueError("Insufficient permissions to create vehicle")
            
            db = await get_mongodb()
            
            # Add metadata
            vehicle_data = data.copy()
            vehicle_data["created_by"] = user_context.get("user_id")
            vehicle_data["created_at"] = datetime.utcnow()
            vehicle_data["status"] = "available"
            
            # Insert vehicle
            result = await db.vehicles.insert_one(vehicle_data)
            vehicle_data["_id"] = str(result.inserted_id)
            
            # Publish vehicle created event
            mq_service.publish_vehicle_created({
                "vehicle_id": str(result.inserted_id),
                "vehicle_data": vehicle_data,
                "created_by": user_context.get("user_id")
            })
            
            return vehicle_data
            
        except Exception as e:
            logger.error(f"Error creating vehicle: {e}")
            raise
    async def _update_vehicle(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle PUT /api/vehicles/{id}"""
        try:
            vehicle_id = endpoint.split('/')[-1]
            
            # Validate permissions
            if user_context.get("role") not in ["admin", "fleet_manager"]:
                raise ValueError("Insufficient permissions to update vehicle")
            
            db = await get_mongodb()
            
            # Convert string ID to ObjectId if needed
            try:
                if isinstance(vehicle_id, str) and len(vehicle_id) == 24:
                    query_id = ObjectId(vehicle_id)
                else:
                    query_id = vehicle_id
            except:
                query_id = vehicle_id
            
            # Update vehicle
            update_data = data.copy()
            update_data["updated_by"] = user_context.get("user_id")
            update_data["updated_at"] = datetime.utcnow()
            
            result = await db.vehicles.update_one(
                {"_id": query_id},
                {"$set": update_data}
            )
            
            if result.matched_count == 0:
                raise ValueError(f"Vehicle {vehicle_id} not found")
            
            # Get updated vehicle
            updated_vehicle = await db.vehicles.find_one({"_id": query_id})
            updated_vehicle["_id"] = str(updated_vehicle["_id"])
            
            # Publish vehicle updated event
            mq_service.publish_vehicle_updated({
                "vehicle_id": vehicle_id,
                "vehicle_data": updated_vehicle,
                "updated_by": user_context.get("user_id")
            })
            
            return updated_vehicle
            
        except Exception as e:
            logger.error(f"Error updating vehicle: {e}")
            raise
    async def _delete_vehicle(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle DELETE /api/vehicles/{id}"""
        try:
            vehicle_id = endpoint.split('/')[-1]
            
            # Validate permissions
            if user_context.get("role") != "admin":
                raise ValueError("Only administrators can delete vehicles")
            
            db = await get_mongodb()
            
            # Convert string ID to ObjectId if needed
            try:
                if isinstance(vehicle_id, str) and len(vehicle_id) == 24:
                    query_id = ObjectId(vehicle_id)
                else:
                    query_id = vehicle_id
            except:
                query_id = vehicle_id
            
            # Get vehicle before deletion
            vehicle = await db.vehicles.find_one({"_id": query_id})
            if not vehicle:
                raise ValueError(f"Vehicle {vehicle_id} not found")
            
            # Delete vehicle
            result = await db.vehicles.delete_one({"_id": query_id})
            
            if result.deleted_count == 0:
                raise ValueError(f"Failed to delete vehicle {vehicle_id}")
            
            # Publish vehicle deleted event
            mq_service.publish_vehicle_deleted({
                "vehicle_id": vehicle_id,
                "deleted_by": user_context.get("user_id")
            })
            
            return {"message": f"Vehicle {vehicle_id} deleted successfully"}
            
        except Exception as e:
            logger.error(f"Error deleting vehicle: {e}")
            raise
    
    # Vehicle Assignment handlers
    async def _get_vehicle_assignments(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle GET /api/vehicle-assignments"""
        try:
            db = await get_mongodb()
            query = {}
            
            # Apply user-based filtering
            if user_context.get("role") == "driver":
                query["driver_id"] = user_context.get("user_id")
            
            assignments = await db.vehicle_assignments.find(query).to_list(100)
            
            for assignment in assignments:
                assignment["_id"] = str(assignment["_id"])
            
            return {"assignments": assignments, "count": len(assignments)}
            
        except Exception as e:
            logger.error(f"Error getting vehicle assignments: {e}")
            raise
    
    async def _create_vehicle_assignment(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle POST /api/vehicle-assignments"""
        try:
            # Validate permissions
            if user_context.get("role") not in ["admin", "fleet_manager"]:
                raise ValueError("Insufficient permissions to create assignment")
            
            db = await get_mongodb()
            
            assignment_data = data.copy()
            assignment_data["created_by"] = user_context.get("user_id")
            assignment_data["created_at"] = datetime.utcnow()
            assignment_data["status"] = "active"
            
            result = await db.vehicle_assignments.insert_one(assignment_data)
            assignment_data["_id"] = str(result.inserted_id)
            
            return assignment_data
            
        except Exception as e:
            logger.error(f"Error creating vehicle assignment: {e}")
            raise
    
    async def _update_vehicle_assignment(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle PUT /api/vehicle-assignments/{id}"""
        try:
            assignment_id = endpoint.split('/')[-1]
            
            if user_context.get("role") not in ["admin", "fleet_manager"]:
                raise ValueError("Insufficient permissions to update assignment")
            
            db = await get_mongodb()
            
            update_data = data.copy()
            update_data["updated_by"] = user_context.get("user_id")
            update_data["updated_at"] = datetime.utcnow()
            
            result = await db.vehicle_assignments.update_one(
                {"_id": assignment_id},
                {"$set": update_data}
            )
            
            if result.matched_count == 0:
                raise ValueError(f"Assignment {assignment_id} not found")
            
            updated_assignment = await db.vehicle_assignments.find_one({"_id": assignment_id})
            updated_assignment["_id"] = str(updated_assignment["_id"])
            
            return updated_assignment
            
        except Exception as e:
            logger.error(f"Error updating vehicle assignment: {e}")
            raise
    
    async def _delete_vehicle_assignment(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle DELETE /api/vehicle-assignments/{id}"""
        try:
            assignment_id = endpoint.split('/')[-1]
            
            if user_context.get("role") not in ["admin", "fleet_manager"]:
                raise ValueError("Insufficient permissions to delete assignment")
            
            db = await get_mongodb()
            
            result = await db.vehicle_assignments.delete_one({"_id": assignment_id})
            
            if result.deleted_count == 0:
                raise ValueError(f"Assignment {assignment_id} not found")
            
            return {"message": f"Assignment {assignment_id} deleted successfully"}
            
        except Exception as e:
            logger.error(f"Error deleting vehicle assignment: {e}")
            raise
    
    # Vehicle Usage handlers
    async def _get_vehicle_usage(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle GET /api/vehicle-usage"""
        try:
            db = await get_mongodb()
            query = {}
            
            # Apply filters from query parameters
            if "vehicle_id" in data:
                query["vehicle_id"] = data["vehicle_id"]
            if "driver_id" in data:
                query["driver_id"] = data["driver_id"]
            
            # Apply user-based filtering
            if user_context.get("role") == "driver":
                query["driver_id"] = user_context.get("user_id")
            
            usage_logs = await db.vehicle_usage.find(query).to_list(100)
            
            for log in usage_logs:
                log["_id"] = str(log["_id"])
            
            return {"usage_logs": usage_logs, "count": len(usage_logs)}
            
        except Exception as e:
            logger.error(f"Error getting vehicle usage: {e}")
            raise
    
    async def _create_vehicle_usage(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle POST /api/vehicle-usage"""
        try:
            db = await get_mongodb()
            
            usage_data = data.copy()
            usage_data["created_by"] = user_context.get("user_id")
            usage_data["created_at"] = datetime.utcnow()
            
            # If driver is creating usage log, ensure it's for themselves
            if user_context.get("role") == "driver":
                usage_data["driver_id"] = user_context.get("user_id")
            
            result = await db.vehicle_usage.insert_one(usage_data)
            usage_data["_id"] = str(result.inserted_id)
            
            return usage_data
            
        except Exception as e:
            logger.error(f"Error creating vehicle usage: {e}")
            raise
    
    async def _update_vehicle_usage(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle PUT /api/vehicle-usage/{id}"""
        try:
            usage_id = endpoint.split('/')[-1]
            
            db = await get_mongodb()
            
            # Check if usage log exists and user has permission
            existing_usage = await db.vehicle_usage.find_one({"_id": usage_id})
            if not existing_usage:
                raise ValueError(f"Usage log {usage_id} not found")
            
            # Drivers can only update their own usage logs
            if user_context.get("role") == "driver":
                if existing_usage.get("driver_id") != user_context.get("user_id"):
                    raise ValueError("Access denied to this usage log")
            
            update_data = data.copy()
            update_data["updated_by"] = user_context.get("user_id")
            update_data["updated_at"] = datetime.utcnow()
            
            result = await db.vehicle_usage.update_one(
                {"_id": usage_id},
                {"$set": update_data}
            )
            
            updated_usage = await db.vehicle_usage.find_one({"_id": usage_id})
            updated_usage["_id"] = str(updated_usage["_id"])
            
            return updated_usage
            
        except Exception as e:
            logger.error(f"Error updating vehicle usage: {e}")
            raise
    
    async def _search_vehicles(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle GET /api/vehicles/search/{query}"""
        try:
            # Extract search query from endpoint
            query = endpoint.split('/')[-1] if '/' in endpoint else data.get("query", "")
            
            if not query:
                raise ValueError("Search query is required")
            
            db = await get_mongodb()
            
            # Build search criteria
            search_criteria = {
                "$or": [
                    {"make": {"$regex": query, "$options": "i"}},
                    {"model": {"$regex": query, "$options": "i"}},
                    {"license_plate": {"$regex": query, "$options": "i"}},
                    {"vin": {"$regex": query, "$options": "i"}},
                    {"status": {"$regex": query, "$options": "i"}},
                    {"driver_name": {"$regex": query, "$options": "i"}},
                    {"department": {"$regex": query, "$options": "i"}}
                ]
            }
            
            # Apply user-based filtering
            if user_context.get("role") == "driver":
                search_criteria["assigned_driver_id"] = user_context.get("user_id")
            
            vehicles = await db.vehicles.find(search_criteria).to_list(50)
            
            # Convert ObjectId to string
            for vehicle in vehicles:
                vehicle["_id"] = str(vehicle["_id"])
            
            return {"vehicles": vehicles, "count": len(vehicles), "query": query}
            
        except Exception as e:
            logger.error(f"Error searching vehicles: {e}")
            raise


# Global instance
service_request_handler = ServiceRequestHandler()
