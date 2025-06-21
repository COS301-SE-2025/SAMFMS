"""
Service Request Handler for Vehicle Maintenance Service
Handles incoming requests from Core via RabbitMQ
"""

import asyncio
import json
import logging
from typing import Dict, Any
from datetime import datetime
import aio_pika

logger = logging.getLogger(__name__)

class MaintenanceRequestHandler:
    """Handles RabbitMQ request/response pattern for Maintenance service"""
    
    def __init__(self):
        self.endpoint_handlers = {
            "/api/maintenance": {
                "GET": self._get_maintenance_records,
                "POST": self._create_maintenance_record,
                "PUT": self._update_maintenance_record,
                "DELETE": self._delete_maintenance_record
            },
            "/api/vehicle-maintenance": {
                "GET": self._get_vehicle_maintenance,
                "POST": self._schedule_maintenance
            }
        }
    
    async def initialize(self):
        """Initialize request handler and start consuming"""
        try:
            await self._setup_request_consumption()
            logger.info("Maintenance service request handler initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Maintenance request handler: {e}")
            raise
    
    async def _setup_request_consumption(self):
        """Set up RabbitMQ to consume requests from Core"""
        connection = await aio_pika.connect_robust("amqp://guest:guest@rabbitmq/")
        channel = await connection.channel()
        
        request_queue = await channel.declare_queue("maintenance.requests", durable=True)
        await channel.set_qos(prefetch_count=1)
        
        await request_queue.consume(self._handle_request_message)
        logger.info("Started consuming Maintenance requests")
    
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
                
                logger.info(f"Processing Maintenance request {correlation_id}: {method} {endpoint}")
                
                result = await self.route_to_handler(endpoint, method, data, user_context)
                
                response = {
                    "correlation_id": correlation_id,
                    "status": "success",
                    "data": result,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await self._send_response(response)
                
            except Exception as e:
                logger.error(f"Error processing Maintenance request: {e}")
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
            logger.error(f"Error routing Maintenance request {method} {endpoint}: {e}")
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
            logger.debug(f"Maintenance response sent for correlation_id: {response.get('correlation_id')}")
            
        except Exception as e:
            logger.error(f"Error sending Maintenance response: {e}")
    
    # Maintenance Record handlers
    async def _get_maintenance_records(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle GET /api/maintenance"""
        try:
            # Mock maintenance records
            records = [
                {
                    "id": "maint_001",
                    "vehicle_id": "vehicle_001",
                    "type": "oil_change",
                    "description": "Engine oil and filter replacement",
                    "scheduled_date": "2025-06-25T10:00:00Z",
                    "completed_date": None,
                    "status": "scheduled",
                    "cost": 250.00,
                    "technician": "John Smith"
                },
                {
                    "id": "maint_002",
                    "vehicle_id": "vehicle_002",
                    "type": "tire_rotation",
                    "description": "Rotate tires and check pressure",
                    "scheduled_date": "2025-06-22T14:00:00Z",
                    "completed_date": "2025-06-22T15:30:00Z",
                    "status": "completed",
                    "cost": 120.00,
                    "technician": "Jane Doe"
                }
            ]
            
            # Filter by vehicle_id if specified
            vehicle_id = data.get("vehicle_id")
            if vehicle_id:
                records = [record for record in records if record["vehicle_id"] == vehicle_id]
            
            # Apply user-based filtering
            if user_context.get("role") == "driver":
                # Drivers can only see maintenance for their assigned vehicles
                driver_vehicle_id = data.get("assigned_vehicle_id")
                if driver_vehicle_id:
                    records = [record for record in records if record["vehicle_id"] == driver_vehicle_id]
                else:
                    records = []
            
            return {"maintenance_records": records, "count": len(records)}
            
        except Exception as e:
            logger.error(f"Error getting maintenance records: {e}")
            raise
    
    async def _create_maintenance_record(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle POST /api/maintenance"""
        try:
            # Validate permissions
            allowed_roles = ["admin", "fleet_manager", "maintenance_staff"]
            if user_context.get("role") not in allowed_roles:
                raise ValueError("Insufficient permissions to create maintenance record")
            
            # Validate required fields
            required_fields = ["vehicle_id", "type", "description", "scheduled_date"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Create maintenance record
            maintenance_data = {
                "id": f"maint_{datetime.utcnow().timestamp()}",
                "vehicle_id": data["vehicle_id"],
                "type": data["type"],
                "description": data["description"],
                "scheduled_date": data["scheduled_date"],
                "completed_date": None,
                "status": "scheduled",
                "cost": data.get("cost", 0.0),
                "technician": data.get("technician"),
                "created_by": user_context.get("user_id"),
                "created_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Created maintenance record for vehicle {data['vehicle_id']}")
            
            return maintenance_data
            
        except Exception as e:
            logger.error(f"Error creating maintenance record: {e}")
            raise
    
    async def _update_maintenance_record(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle PUT /api/maintenance/{id}"""
        try:
            maintenance_id = endpoint.split('/')[-1]
            
            allowed_roles = ["admin", "fleet_manager", "maintenance_staff"]
            if user_context.get("role") not in allowed_roles:
                raise ValueError("Insufficient permissions to update maintenance record")
            
            # Mock update
            updated_record = {
                "id": maintenance_id,
                "updated_by": user_context.get("user_id"),
                "updated_at": datetime.utcnow().isoformat(),
                **data
            }
            
            logger.info(f"Updated maintenance record: {maintenance_id}")
            
            return updated_record
            
        except Exception as e:
            logger.error(f"Error updating maintenance record: {e}")
            raise
    
    async def _delete_maintenance_record(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle DELETE /api/maintenance/{id}"""
        try:
            maintenance_id = endpoint.split('/')[-1]
            
            if user_context.get("role") not in ["admin", "maintenance_staff"]:
                raise ValueError("Insufficient permissions to delete maintenance record")
            
            logger.info(f"Deleted maintenance record: {maintenance_id}")
            
            return {"message": f"Maintenance record {maintenance_id} deleted successfully"}
            
        except Exception as e:
            logger.error(f"Error deleting maintenance record: {e}")
            raise
    
    # Vehicle Maintenance handlers
    async def _get_vehicle_maintenance(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle GET /api/vehicle-maintenance"""
        try:
            # Mock vehicle maintenance overview
            maintenance_overview = {
                "total_vehicles": 25,
                "vehicles_due_maintenance": 5,
                "overdue_maintenance": 2,
                "scheduled_this_week": 8,
                "maintenance_cost_this_month": 12500.00,
                "upcoming_maintenance": [
                    {
                        "vehicle_id": "vehicle_001",
                        "license_plate": "CA 123-456",
                        "maintenance_type": "oil_change",
                        "due_date": "2025-06-25",
                        "priority": "normal"
                    },
                    {
                        "vehicle_id": "vehicle_003",
                        "license_plate": "CA 789-012",
                        "maintenance_type": "brake_inspection",
                        "due_date": "2025-06-23",
                        "priority": "high"
                    }
                ]
            }
            
            return maintenance_overview
            
        except Exception as e:
            logger.error(f"Error getting vehicle maintenance overview: {e}")
            raise
    
    async def _schedule_maintenance(self, endpoint: str, data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle POST /api/vehicle-maintenance"""
        try:
            allowed_roles = ["admin", "fleet_manager", "maintenance_staff"]
            if user_context.get("role") not in allowed_roles:
                raise ValueError("Insufficient permissions to schedule maintenance")
            
            # Validate required fields
            required_fields = ["vehicle_id", "maintenance_type", "scheduled_date"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Schedule maintenance
            scheduled_maintenance = {
                "id": f"schedule_{datetime.utcnow().timestamp()}",
                "vehicle_id": data["vehicle_id"],
                "maintenance_type": data["maintenance_type"],
                "scheduled_date": data["scheduled_date"],
                "priority": data.get("priority", "normal"),
                "estimated_duration": data.get("estimated_duration", "2 hours"),
                "estimated_cost": data.get("estimated_cost", 0.0),
                "notes": data.get("notes", ""),
                "scheduled_by": user_context.get("user_id"),
                "scheduled_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Scheduled maintenance for vehicle {data['vehicle_id']}")
            
            return scheduled_maintenance
            
        except Exception as e:
            logger.error(f"Error scheduling maintenance: {e}")
            raise


# Global instance
maintenance_request_handler = MaintenanceRequestHandler()
