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
    return os.getenv("RABBITMQ_URL", "amqp://samfms_rabbit:RabbitPass2025!@rabbitmq:5672/")

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
                "PUT": self._update_driver,
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
        """Enhanced request consumption with better error handling and reconnection logic"""
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                logger.info(f"Connecting to RabbitMQ for request consumption (attempt {retry_count + 1}/{max_retries})...")
                # Using async RabbitMQ for better performance with robust connection
                rabbitmq_url = get_rabbitmq_url()
                connection = await aio_pika.connect_robust(
                    rabbitmq_url,
                    heartbeat=60,
                    blocked_connection_timeout=300,
                )
                logger.info(f"Successfully connected to RabbitMQ at {rabbitmq_url} for request consumption")
                
                channel = await connection.channel()
                await channel.set_qos(prefetch_count=10)  # Allow some parallel processing
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
                
                # Set up message handler with retry logic
                async def handle_request_message(message: aio_pika.IncomingMessage):
                    try:
                        async with message.process(requeue=True):
                            await self._handle_request_message(message)
                    except Exception as e:
                        logger.error(f"Failed to process message: {e}")
                        # Message will be requeued due to requeue=True
                
                # Start consuming
                await request_queue.consume(handle_request_message, consumer_tag="management-consumer")
                logger.info("Started consuming management requests from service_requests exchange")
                logger.info("Management service is now ready to handle requests from Core service")
                
                # Keep connection alive with proper exception handling
                try:
                    while True:
                        await asyncio.sleep(1)
                except asyncio.CancelledError:
                    logger.info("Request consumption cancelled")
                    raise
                finally:
                    try:
                        await connection.close()
                    except Exception as e:
                        logger.warning(f"Error closing RabbitMQ connection: {e}")
                        
                # If we get here, consumption completed successfully
                break
                
            except asyncio.CancelledError:
                logger.info("Request consumption task cancelled")
                raise
            except Exception as e:
                retry_count += 1
                logger.error(f"Failed to setup RabbitMQ request consumption (attempt {retry_count}/{max_retries}): {e}")
                if retry_count >= max_retries:
                    logger.error("Max retries reached for RabbitMQ setup. Service will not be able to handle requests.")
                    raise
                else:
                    logger.info(f"Retrying RabbitMQ setup in 5 seconds...")
                    await asyncio.sleep(5)
    
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
            
        except Exception as e:
            logger.error(f"Error sending response: {e}")
    
    # Vehicle handlers
    async def _get_vehicles(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle GET /api/vehicles and include analytics in the response."""
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
            
            # --- Add analytics ---
            analytics = await self._get_analytics()
            return {"vehicles": vehicles, "count": len(vehicles), "analytics": analytics}
            
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
            # Validate permissions - allow bypass for nginx compatibility routes
            if not user_context.get("bypass_auth", False):
                user_role = user_context.get("role")
                user_permissions = user_context.get("permissions", [])
                # Allow if user is admin, fleet_manager, or has create:vehicles permission
                if user_role not in ["admin", "fleet_manager"] and "create:vehicles" not in user_permissions:
                    raise ValueError("Insufficient permissions to create vehicle")
            
            from database import vehicle_management_collection
            import uuid
            
            # Add metadata and generate vehicle_id
            vehicle_data = data.copy()
            vehicle_data["vehicle_id"] = str(uuid.uuid4())  # Generate unique vehicle_id
            vehicle_data["created_by"] = user_context.get("user_id", "system")
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
                            "created_by": user_context.get("user_id", "system"),
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
            # Validate permissions - allow bypass for nginx compatibility routes
            if not user_context.get("bypass_auth", False):
                user_role = user_context.get("role")
                user_permissions = user_context.get("permissions", [])
                # Allow if user is admin, fleet_manager, or has edit:vehicles permission
                if user_role not in ["admin", "fleet_manager"] and "edit:vehicles" not in user_permissions:
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
            update_data["updated_by"] = user_context.get("user_id", "system")
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
            try:
                if hasattr(self, 'mq_service') and self.mq_service:
                    self.mq_service.publish_service_event(
                        event_type="vehicle_updated",
                        service_name="management",
                        message_data={
                            "vehicle_id": vehicle_id,
                            "updated_by": user_context.get("user_id", "system"),
                            "timestamp": update_data["updated_at"].isoformat()
                        }
                    )
            except Exception as mq_error:
                logger.warning(f"Failed to publish vehicle updated event: {mq_error}")
            
            return updated_vehicle
        except Exception as e:
            logger.error(f"Error updating vehicle: {e}")
            raise
            
    async def _delete_vehicle(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle DELETE /api/vehicles/{id}"""
        try:
            vehicle_id = endpoint.split('/')[-1]
            
            # Validate permissions - allow bypass for nginx compatibility routes
            if not user_context.get("bypass_auth", False):
                # Check both role-based and permission-based access
                user_role = user_context.get("role")
                user_permissions = user_context.get("permissions", [])
                
                # Allow if user is admin OR has delete:vehicles permission
                if user_role != "admin" and "delete:vehicles" not in user_permissions:
                    raise ValueError("Insufficient permissions to delete vehicle")
            
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
            try:
                if hasattr(self, 'mq_service') and self.mq_service:
                    self.mq_service.publish_service_event(
                        event_type="vehicle_deleted",
                        service_name="management",
                        message_data={
                            "vehicle_id": vehicle_id,
                            "deleted_by": user_context.get("user_id", "system"),
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
            except Exception as mq_error:
                logger.warning(f"Failed to publish vehicle deleted event: {mq_error}")
            
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
        """Handle GET /api/vehicles/search/{query} and include analytics in the response."""
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
            
            # --- Add analytics ---
            analytics = await self._get_analytics()
            return {"vehicles": vehicles, "count": len(vehicles), "query": query, "analytics": analytics}
            
        except Exception as e:
            logger.error(f"Error searching vehicles: {e}")
            raise

    async def _get_analytics(self) -> dict:
        """Helper to gather all analytics for vehicles endpoints."""
        try:
            from analytics import (
                fleet_utilization, vehicle_usage, assignment_metrics, maintenance_analytics,
                driver_performance, cost_analytics, status_breakdown, incident_statistics, department_location_analytics
            )
            analytics = {}
            analytics["fleet_utilization"] = await fleet_utilization()
            analytics["vehicle_usage"] = await vehicle_usage()
            analytics["assignment_metrics"] = await assignment_metrics()
            analytics["maintenance_analytics"] = await maintenance_analytics()
            analytics["driver_performance"] = await driver_performance()
            analytics["cost_analytics"] = await cost_analytics()
            analytics["status_breakdown"] = await status_breakdown()
            analytics["incident_statistics"] = await incident_statistics()
            analytics["department_location_analytics"] = await department_location_analytics()
            return analytics
        except Exception as e:
            logger.error(f"Error gathering analytics: {e}")
            return {}
    
    async def _get_drivers(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle GET /api/drivers - Returns a list of drivers only, with sensitive fields removed."""
        try:
            from database import security_users_collection
            query = {"role": "driver"}
            # If the user is a driver, only return their own record
            if user_context.get("role") == "driver":
                query["_id"] = ObjectId(user_context.get("user_id"))
            drivers = await security_users_collection.find(query).to_list(100)
            sanitized_drivers = []
            for driver in drivers:
                driver["_id"] = str(driver["_id"])
                # Remove sensitive fields
                driver.pop("password_hash", None)
                driver.pop("password_reset_token", None)
                driver.pop("two_factor_enabled", None)
                sanitized_drivers.append(driver)
            return {"drivers": sanitized_drivers, "count": len(sanitized_drivers)}
        except Exception as e:
            logger.error(f"Error getting drivers: {e}")
            raise
    
    async def _update_driver(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle PUT /api/drivers/{id} - Update a driver, allowing new fields to be added."""
        try:
            from database import security_users_collection
            driver_id = endpoint.split("/")[-1]
            try:
                if isinstance(driver_id, str) and len(driver_id) == 24:
                    query_id = ObjectId(driver_id)
                else:
                    query_id = driver_id
            except:
                query_id = driver_id
            update_data = data.copy()
            update_data["updated_by"] = user_context.get("user_id", "system")
            update_data["updated_at"] = datetime.utcnow()
            result = await security_users_collection.update_one({"_id": query_id}, {"$set": update_data})
            if result.matched_count == 0:
                raise ValueError(f"Driver {driver_id} not found")
            updated_driver = await security_users_collection.find_one({"_id": query_id})
            updated_driver["_id"] = str(updated_driver["_id"])
            # Remove sensitive fields
            for field in ["password_hash", "password_reset_token", "two_factor_enabled"]:
                updated_driver.pop(field, None)
            return updated_driver
        except Exception as e:
            logger.error(f"Error updating driver: {e}")
            raise

    async def _search_drivers(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle GET /api/drivers/search/{query} - Search for drivers. Stub implementation."""
        try:
            from database import driver_management_collection
            query = endpoint.split("/")[-1] if "/" in endpoint else data.get("query", "")
            if not query:
                raise ValueError("Search query is required")
            search_criteria = {
                "$or": [
                    {"name": {"$regex": query, "$options": "i"}},
                    {"license_number": {"$regex": query, "$options": "i"}},
                    {"department": {"$regex": query, "$options": "i"}}
                ]
            }
            drivers = await driver_management_collection.find(search_criteria).to_list(50)
            for driver in drivers:
                driver["_id"] = str(driver["_id"])
            return {"drivers": drivers, "count": len(drivers), "query": query}
        except Exception as e:
            logger.error(f"Error searching drivers: {e}")
            raise
# Global instance
service_request_handler = ServiceRequestHandler()
