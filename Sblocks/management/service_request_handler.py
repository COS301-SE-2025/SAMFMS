"""
Service Request Handler for Management Service
Handles incoming requests from Core via RabbitMQ
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any, Callable
from datetime import datetime
import pika
import aio_pika
from bson import ObjectId

from models import VehicleAssignment, VehicleUsageLog, VehicleStatus
from routes import router as management_router
from database import get_mongodb
from message_queue import mq_service

def json_serializer(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, ObjectId):
        return str(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

logger = logging.getLogger(__name__)

def get_rabbitmq_url():
    """Get RabbitMQ URL from environment variable or default"""
    return os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq/")

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
            },            "/api/vehicles/search": {
                "GET": self._search_vehicles
            },
            "/api/drivers": {
                "GET": self._get_drivers,
                "POST": self._create_driver,
                "PUT": self._update_driver,
                "DELETE": self._delete_driver
            },
            "/api/drivers/search": {
                "GET": self._search_drivers
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
    async def start_consuming(self):
        """Start consuming requests from Core in a background task"""
        try:
            logger.info("Starting RabbitMQ request consumption...")
            await self._setup_request_consumption()
        except Exception as e:
            logger.error(f"Error in request consumption loop: {e}")
            logger.exception("Request consumption exception traceback:")
            
    async def initialize(self):
        """Initialize request handler (deprecated - use start_consuming)"""
        logger.info("Management service request handler initialized (old method)")

    # Main HTTP method handlers
    async def _handle_get_request(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Any:
        """Handle GET requests"""
        return await self.route_to_handler(endpoint, "GET", data, user_context)
    
    async def _handle_post_request(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Any:
        """Handle POST requests"""
        return await self.route_to_handler(endpoint, "POST", data, user_context)
    
    async def _handle_put_request(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Any:
        """Handle PUT requests"""
        return await self.route_to_handler(endpoint, "PUT", data, user_context)
        
    async def _handle_delete_request(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Any:
        """Handle DELETE requests"""
        return await self.route_to_handler(endpoint, "DELETE", data, user_context)
        
    async def _setup_request_consumption(self):
        """Set up RabbitMQ to consume requests from Core"""
        try:
            logger.info("Connecting to RabbitMQ for request consumption...")
            # Using async RabbitMQ for better performance
            rabbitmq_url = get_rabbitmq_url()
            connection = await aio_pika.connect_robust(rabbitmq_url)
            logger.info(f"Successfully connected to RabbitMQ at {rabbitmq_url} for request consumption")
            
            channel = await connection.channel()
            logger.info("RabbitMQ channel created for request consumption")
            
            # Declare service requests exchange
            exchange = await channel.declare_exchange("service_requests", aio_pika.ExchangeType.DIRECT, durable=True)
            logger.info("Service requests exchange declared")
            
            # Declare request queue
            request_queue = await channel.declare_queue("management.requests", durable=True)
            logger.info("Management requests queue declared")
            
            # Bind queue to exchange with routing key "management.requests" to match Core routing
            await request_queue.bind(exchange, routing_key="management.requests")
            logger.info("Management requests queue bound to service_requests exchange")
            
            # Set QoS to process one message at a time
            await channel.set_qos(prefetch_count=1)
            
            # Start consuming - this will run continuously
            async with request_queue.iterator() as queue_iter:
                logger.info("Started consuming management requests from service_requests exchange")
                logger.info("Management service is now ready to handle requests from Core service")
                
                async for message in queue_iter:
                    async with message.process():
                        await self._handle_request_message(message)
            
        except Exception as e:
            logger.error(f"Failed to setup RabbitMQ request consumption: {e}")
            logger.exception("Full RabbitMQ setup exception traceback:")
            raise
    
    async def _handle_request_message(self, message: aio_pika.IncomingMessage):
        """Handle incoming request message from Core"""
        logger.info(f"Received message from queue: {message.routing_key}")
        try:
            # Parse request
            request_data = json.loads(message.body.decode())
            logger.info(f"Parsed request data: {request_data}")
            
            correlation_id = request_data.get("correlation_id")
            endpoint = request_data.get("endpoint")
            method = request_data.get("method")
            data = request_data.get("data", {})
            user_context = request_data.get("user_context", {})
            
            logger.info(f"Processing request {correlation_id}: {method} {endpoint}")
            
            # Route to appropriate handler
            result = await self.route_to_handler(endpoint, method, data, user_context)
            logger.info(f"Handler result: {result}")
            
            # Send success response
            response = {
                "correlation_id": correlation_id,
                "status": "success",
                "data": result,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self._send_response(response)
            logger.info(f"Sent response for correlation_id: {correlation_id}")
                
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            logger.exception("Full exception traceback:")
            # Send standardized error response
            error_response = {
                "correlation_id": request_data.get("correlation_id", "unknown"),
                "status": "error",
                "error": {
                    "message": str(e),
                    "type": type(e).__name__,
                    "code": getattr(e, 'code', 'INTERNAL_ERROR')
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            await self._send_response(error_response)
            logger.info(f"Sent error response for correlation_id: {request_data.get('correlation_id', 'unknown')}")
    
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
          # Handle drivers endpoints specially - /api/drivers or /api/drivers/id
        if len(parts) >= 3 and parts[2] == "drivers":
            return f"/{parts[1]}/{parts[2]}"
        
        if len(parts) >= 3:
            return f"/{parts[1]}/{parts[2]}"
        return endpoint
        
    async def _send_response(self, response: Dict[str, Any]):
        """Send response back to Core via RabbitMQ"""
        try:
            rabbitmq_url = get_rabbitmq_url()
            connection = await aio_pika.connect_robust(rabbitmq_url)
            channel = await connection.channel()
            
            # Declare response exchange as durable (must match core's declaration)
            exchange = await channel.declare_exchange("service_responses", aio_pika.ExchangeType.DIRECT, durable=True)
              # Send response to core.responses queue
            await exchange.publish(
                aio_pika.Message(
                    body=json.dumps(response, default=json_serializer).encode(),
                    content_type="application/json"
                ),
                routing_key="core.responses"
            )
            
            await connection.close()
            logger.debug(f"Response sent for correlation_id: {response.get('correlation_id')}")
            
        except Exception as e:            logger.error(f"Error sending response: {e}")
    
    # Vehicle handlers
    async def _get_vehicles(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle GET /api/vehicles"""
        try:
            # Check if this is a drivers request
            if endpoint.endswith('/drivers'):
                return await self._get_drivers(endpoint, data, user_context)
            
            # Extract vehicle ID if present (but not if it's a special endpoint like 'drivers')
            parts = endpoint.split('/')
            if len(parts) > 3 and parts[-1] not in ['drivers', 'search']:
                vehicle_id = parts[-1]
                return await self._get_single_vehicle(vehicle_id, user_context)
            
            # Get all vehicles with filtering
            from database import vehicle_management_collection
            query = {}
            
            # Apply user-based filtering
            if user_context.get("role") == "driver":
                # Drivers only see their assigned vehicles
                query["assigned_driver_id"] = user_context.get("user_id")
            
            vehicles = await vehicle_management_collection.find(query).to_list(100)
            
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
            from database import vehicle_management_collection
            
            # Convert string ID to ObjectId if needed
            try:
                if isinstance(vehicle_id, str) and len(vehicle_id) == 24:
                    query_id = ObjectId(vehicle_id)
                else:
                    query_id = vehicle_id
            except:
                query_id = vehicle_id
            
            vehicle = await vehicle_management_collection.find_one({"_id": query_id})
            
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
            
            from database import vehicle_management_collection
            import uuid
            
            # Add metadata and generate vehicle_id
            vehicle_data = data.copy()
            vehicle_data["vehicle_id"] = str(uuid.uuid4())  # Generate unique vehicle_id
            vehicle_data["created_by"] = user_context.get("user_id")
            vehicle_data["created_at"] = datetime.utcnow().isoformat()  # Convert to string for JSON serialization
            vehicle_data["status"] = "available"
            
            # Insert vehicle
            result = await vehicle_management_collection.insert_one(vehicle_data)
            vehicle_data["_id"] = str(result.inserted_id)
            
            # Publish vehicle created event (using JSON-serializable data)
            try:
                if hasattr(self, 'mq_service') and self.mq_service:
                    self.mq_service.publish_service_event(
                        event_type="vehicle_created",
                        service_name="management",
                        message_data={
                            "vehicle_id": vehicle_data["vehicle_id"],
                            "created_by": user_context.get("user_id"),
                            "timestamp": vehicle_data["created_at"]
                        }
                    )
            except Exception as mq_error:
                logger.warning(f"Failed to publish vehicle created event: {mq_error}")
            
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
            
            from database import vehicle_management_collection
            
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
            
            result = await vehicle_management_collection.update_one(
                {"_id": query_id},
                {"$set": update_data}
            )
            
            if result.matched_count == 0:
                raise ValueError(f"Vehicle {vehicle_id} not found")
            
            # Get updated vehicle
            updated_vehicle = await vehicle_management_collection.find_one({"_id": query_id})
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
            
            from database import vehicle_management_collection
            
            # Convert string ID to ObjectId if needed
            try:
                if isinstance(vehicle_id, str) and len(vehicle_id) == 24:
                    query_id = ObjectId(vehicle_id)
                else:
                    query_id = vehicle_id
            except:
                query_id = vehicle_id
            
            # Get vehicle before deletion
            vehicle = await vehicle_management_collection.find_one({"_id": query_id})
            if not vehicle:
                raise ValueError(f"Vehicle {vehicle_id} not found")
            
            # Delete vehicle
            result = await vehicle_management_collection.delete_one({"_id": query_id})
            
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
            
            # Convert string ID to ObjectId if needed
            try:
                if isinstance(assignment_id, str) and len(assignment_id) == 24:
                    query_id = ObjectId(assignment_id)
                else:
                    query_id = assignment_id
            except:
                query_id = assignment_id
            
            update_data = data.copy()
            update_data["updated_by"] = user_context.get("user_id")
            update_data["updated_at"] = datetime.utcnow()
            
            result = await db.vehicle_assignments.update_one(
                {"_id": query_id},
                {"$set": update_data}
            )
            
            if result.matched_count == 0:
                raise ValueError(f"Assignment {assignment_id} not found")
            
            updated_assignment = await db.vehicle_assignments.find_one({"_id": query_id})
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
            
            # Convert string ID to ObjectId if needed
            try:
                if isinstance(assignment_id, str) and len(assignment_id) == 24:
                    query_id = ObjectId(assignment_id)
                else:
                    query_id = assignment_id
            except:
                query_id = assignment_id
            
            result = await db.vehicle_assignments.delete_one({"_id": query_id})
            
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
            from database import vehicle_usage_logs_collection
            query = {}
            
            # Apply filters from query parameters
            if "vehicle_id" in data:
                query["vehicle_id"] = data["vehicle_id"]
            if "driver_id" in data:
                query["driver_id"] = data["driver_id"]
            
            # Apply user-based filtering
            if user_context.get("role") == "driver":
                query["driver_id"] = user_context.get("user_id")
            
            usage_logs = await vehicle_usage_logs_collection.find(query).to_list(100)
            
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
            
            # Convert string ID to ObjectId if needed
            try:
                if isinstance(usage_id, str) and len(usage_id) == 24:
                    query_id = ObjectId(usage_id)
                else:
                    query_id = usage_id
            except:
                query_id = usage_id
            
            from database import vehicle_usage_logs_collection
            
            # Check if usage log exists and user has permission
            existing_usage = await vehicle_usage_logs_collection.find_one({"_id": query_id})
            if not existing_usage:
                raise ValueError(f"Usage log {usage_id} not found")
            
            # Drivers can only update their own usage logs
            if user_context.get("role") == "driver":
                if existing_usage.get("driver_id") != user_context.get("user_id"):
                    raise ValueError("Access denied to this usage log")
            
            update_data = data.copy()
            update_data["updated_by"] = user_context.get("user_id")
            update_data["updated_at"] = datetime.utcnow()
            
            result = await vehicle_usage_logs_collection.update_one(
                {"_id": query_id},
                {"$set": update_data}
            )
            
            updated_usage = await vehicle_usage_logs_collection.find_one({"_id": query_id})
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
            
            from database import vehicle_management_collection
            vehicles = await vehicle_management_collection.find(search_criteria).to_list(50)
            
            # Convert ObjectId to string
            for vehicle in vehicles:
                vehicle["_id"] = str(vehicle["_id"])
            
            return {"vehicles": vehicles, "count": len(vehicles), "query": query}
            
        except Exception as e:
            logger.error(f"Error searching vehicles: {e}")
            raise    # Driver handlers
    async def _get_drivers(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle GET /api/drivers or /api/vehicles/drivers"""
        try:
            # Check if this is a request for a specific driver (has driver ID in path)
            parts = endpoint.split('/')
            if len(parts) > 3 and parts[-1] not in ['drivers'] and parts[-1] != '':
                # This is a request for a specific driver
                driver_id = parts[-1]
                return await self._get_single_driver(driver_id, user_context)
            
            # Get all drivers
            from database import get_mongodb
            db = get_mongodb()  # No await - this returns the db instance directly
            users_collection = db.users
            
            # Find users with driver role
            query = {"role": "driver"}
            
            # Apply user-based filtering for security
            if user_context.get("role") == "driver":
                # Drivers can only see their own info
                query["_id"] = user_context.get("user_id")
            
            drivers = await users_collection.find(query).to_list(100)
            
            # Convert ObjectId to string and remove sensitive info
            for driver in drivers:
                driver["_id"] = str(driver["_id"])
                # Remove password and other sensitive fields
                driver.pop("password", None)
                driver.pop("password_hash", None)
            
            return {"drivers": drivers, "count": len(drivers)}            
        except Exception as e:
            logger.error(f"Error getting drivers: {e}")
            raise
    
    async def _get_single_driver(self, driver_id: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Get a single driver by ID"""
        try:
            from database import get_mongodb
            db = get_mongodb()
            users_collection = db.users
            
            # Security check
            if user_context.get("role") == "driver" and user_context.get("user_id") != driver_id:
                raise ValueError("Drivers can only access their own information")
            
            # Convert string ID to ObjectId if needed
            try:
                if isinstance(driver_id, str) and len(driver_id) == 24:
                    query_id = ObjectId(driver_id)
                else:
                    query_id = driver_id
            except:
                query_id = driver_id
            
            driver = await users_collection.find_one({"_id": query_id, "role": "driver"})
            
            if not driver:
                raise ValueError(f"Driver not found: {driver_id}")
            
            # Convert ObjectId to string and remove sensitive info
            driver["_id"] = str(driver["_id"])
            driver.pop("password", None)
            driver.pop("password_hash", None)
            
            return driver
            
        except Exception as e:
            logger.error(f"Error getting driver {driver_id}: {e}")
            raise

    async def _create_driver(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle POST /api/drivers"""
        try:
            # Only admins and managers can create drivers
            if user_context.get("role") not in ["admin", "manager"]:
                raise ValueError("Insufficient permissions to create drivers")
            
            from database import get_mongodb
            db = await get_mongodb()
            users_collection = db.users
            
            # Ensure role is set to driver
            data["role"] = "driver"
            data["created_at"] = datetime.utcnow()
            data["updated_at"] = datetime.utcnow()
            
            result = await users_collection.insert_one(data)
            
            return {"driver_id": str(result.inserted_id), "message": "Driver created successfully"}
            
        except Exception as e:
            logger.error(f"Error creating driver: {e}")
            raise

    async def _update_driver(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle PUT /api/drivers"""
        try:
            # Extract driver ID
            driver_id = endpoint.split('/')[-1]
            
            # Security check
            if user_context.get("role") == "driver" and user_context.get("user_id") != driver_id:
                raise ValueError("Drivers can only update their own information")
            elif user_context.get("role") not in ["admin", "manager", "driver"]:
                raise ValueError("Insufficient permissions to update drivers")
            
            from database import get_mongodb
            db = await get_mongodb()
            users_collection = db.users
            
            data["updated_at"] = datetime.utcnow()
            
            # Remove sensitive fields that shouldn't be updated
            data.pop("_id", None)
            data.pop("password", None)
            data.pop("password_hash", None)
            data.pop("role", None)  # Role changes should be handled separately
            
            result = await users_collection.update_one(
                {"_id": ObjectId(driver_id), "role": "driver"},
                {"$set": data}
            )
            
            if result.matched_count == 0:
                raise ValueError(f"Driver not found: {driver_id}")
            
            return {"message": "Driver updated successfully"}
            
        except Exception as e:
            logger.error(f"Error updating driver: {e}")
            raise

    async def _delete_driver(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle DELETE /api/drivers"""
        try:
            # Only admins can delete drivers
            if user_context.get("role") != "admin":
                raise ValueError("Only administrators can delete drivers")
              # Extract driver ID
            driver_id = endpoint.split('/')[-1]
            
            from database import get_mongodb
            db = await get_mongodb()
            users_collection = db.users
            
            result = await users_collection.delete_one({"_id": ObjectId(driver_id), "role": "driver"})
            
            if result.deleted_count == 0:
                raise ValueError(f"Driver not found: {driver_id}")
            
            return {"message": "Driver deleted successfully"}
            
        except Exception as e:
            logger.error(f"Error deleting driver: {e}")
            raise

    async def _search_drivers(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle GET /api/drivers/search"""
        try:
            query = data.get("q", "").strip()
            if not query:
                return {"drivers": [], "count": 0, "message": "No search query provided"}
            
            from database import get_mongodb
            db = await get_mongodb()
            users_collection = db.users
            
            # Build search criteria
            search_criteria = {
                "role": "driver",
                "$or": [
                    {"name": {"$regex": query, "$options": "i"}},
                    {"email": {"$regex": query, "$options": "i"}},
                    {"username": {"$regex": query, "$options": "i"}}
                ]
            }
            
            # Apply user-based filtering
            if user_context.get("role") == "driver":
                search_criteria["_id"] = user_context.get("user_id")
            
            drivers = await users_collection.find(search_criteria).to_list(50)
            
            # Convert ObjectId to string and remove sensitive info
            for driver in drivers:
                driver["_id"] = str(driver["_id"])
                driver.pop("password", None)
                driver.pop("password_hash", None)
            
            return {"drivers": drivers, "count": len(drivers), "query": query}
            
        except Exception as e:
            logger.error(f"Error searching drivers: {e}")
            raise


# Global instance
service_request_handler = ServiceRequestHandler()
