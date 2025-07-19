"""
Example Management Service Block Consumer
Shows how service blocks should handle requests from Core via RabbitMQ
"""

import aio_pika
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

# RabbitMQ connection URL (should be configurable)
RABBITMQ_URL = "amqp://guest:guest@localhost:5672/"

class ManagementServiceHandler:
    """Example handler for management service requests"""
    
    async def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming requests from Core service
        
        Args:
            request_data: Request data from Core service
            
        Returns:
            Response data to send back to Core
        """
        request_id = request_data.get("request_id")
        method = request_data.get("method")
        path = request_data.get("path")
        headers = request_data.get("headers", {})
        body = request_data.get("body")
        query_params = request_data.get("query_params", {})
        
        logger.info(f"Processing request {request_id}: {method} {path}")
        
        try:
            # Route to appropriate handler based on path
            if path.startswith("/vehicles"):
                return await self.handle_vehicles_request(method, path, headers, body, query_params)
            elif path.startswith("/drivers"):
                return await self.handle_drivers_request(method, path, headers, body, query_params)
            elif path.startswith("/assignments"):
                return await self.handle_assignments_request(method, path, headers, body, query_params)
            else:
                return {
                    "request_id": request_id,
                    "type": "service_response",
                    "status_code": 404,
                    "body": {"error": "Not found", "message": f"Path {path} not found in management service"},
                    "headers": {"Content-Type": "application/json"},
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error processing request {request_id}: {str(e)}")
            return {
                "request_id": request_id,
                "type": "service_response",
                "status_code": 500,
                "body": {"error": "Internal server error", "message": str(e)},
                "headers": {"Content-Type": "application/json"},
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def handle_vehicles_request(self, method: str, path: str, headers: Dict, body: str, query_params: Dict) -> Dict[str, Any]:
        """Handle vehicles-related requests"""
        if method == "GET":
            if path == "/vehicles":
                # Return list of vehicles
                return {
                    "status_code": 200,
                    "body": {
                        "vehicles": [
                            {"id": "1", "make": "Toyota", "model": "Corolla", "year": 2022},
                            {"id": "2", "make": "Honda", "model": "Civic", "year": 2021}
                        ]
                    },
                    "headers": {"Content-Type": "application/json"}
                }
            elif path.startswith("/vehicles/"):
                vehicle_id = path.split("/vehicles/")[1]
                return {
                    "status_code": 200,
                    "body": {
                        "vehicle": {"id": vehicle_id, "make": "Toyota", "model": "Corolla", "year": 2022}
                    },
                    "headers": {"Content-Type": "application/json"}
                }
        elif method == "POST":
            if path == "/vehicles":
                # Create new vehicle
                vehicle_data = json.loads(body) if body else {}
                return {
                    "status_code": 201,
                    "body": {
                        "message": "Vehicle created successfully",
                        "vehicle": {"id": "3", **vehicle_data}
                    },
                    "headers": {"Content-Type": "application/json"}
                }
        
        return {
            "status_code": 405,
            "body": {"error": "Method not allowed", "message": f"Method {method} not allowed for {path}"},
            "headers": {"Content-Type": "application/json"}
        }
    
    async def handle_drivers_request(self, method: str, path: str, headers: Dict, body: str, query_params: Dict) -> Dict[str, Any]:
        """Handle drivers-related requests"""
        if method == "GET":
            if path == "/drivers":
                return {
                    "status_code": 200,
                    "body": {
                        "drivers": [
                            {"id": "1", "name": "John Doe", "license": "ABC123"},
                            {"id": "2", "name": "Jane Smith", "license": "XYZ789"}
                        ]
                    },
                    "headers": {"Content-Type": "application/json"}
                }
            elif path.startswith("/drivers/"):
                driver_id = path.split("/drivers/")[1]
                return {
                    "status_code": 200,
                    "body": {
                        "driver": {"id": driver_id, "name": "John Doe", "license": "ABC123"}
                    },
                    "headers": {"Content-Type": "application/json"}
                }
        elif method == "POST":
            if path == "/drivers":
                driver_data = json.loads(body) if body else {}
                return {
                    "status_code": 201,
                    "body": {
                        "message": "Driver created successfully",
                        "driver": {"id": "3", **driver_data}
                    },
                    "headers": {"Content-Type": "application/json"}
                }
        
        return {
            "status_code": 405,
            "body": {"error": "Method not allowed", "message": f"Method {method} not allowed for {path}"},
            "headers": {"Content-Type": "application/json"}
        }
    
    async def handle_assignments_request(self, method: str, path: str, headers: Dict, body: str, query_params: Dict) -> Dict[str, Any]:
        """Handle assignments-related requests"""
        if method == "GET":
            if path == "/assignments":
                return {
                    "status_code": 200,
                    "body": {
                        "assignments": [
                            {"id": "1", "driver_id": "1", "vehicle_id": "1", "date": "2024-01-15"},
                            {"id": "2", "driver_id": "2", "vehicle_id": "2", "date": "2024-01-16"}
                        ]
                    },
                    "headers": {"Content-Type": "application/json"}
                }
            elif path.startswith("/assignments/"):
                assignment_id = path.split("/assignments/")[1]
                return {
                    "status_code": 200,
                    "body": {
                        "assignment": {"id": assignment_id, "driver_id": "1", "vehicle_id": "1", "date": "2024-01-15"}
                    },
                    "headers": {"Content-Type": "application/json"}
                }
        elif method == "POST":
            if path == "/assignments":
                assignment_data = json.loads(body) if body else {}
                return {
                    "status_code": 201,
                    "body": {
                        "message": "Assignment created successfully",
                        "assignment": {"id": "3", **assignment_data}
                    },
                    "headers": {"Content-Type": "application/json"}
                }
        
        return {
            "status_code": 405,
            "body": {"error": "Method not allowed", "message": f"Method {method} not allowed for {path}"},
            "headers": {"Content-Type": "application/json"}
        }

async def handle_management_message(message: aio_pika.IncomingMessage):
    """Handle messages from Core service"""
    async with message.process():
        try:
            data = json.loads(message.body.decode())
            logger.info(f"Received management request: {data.get('request_id')}")
            
            # Process the request
            handler = ManagementServiceHandler()
            response = await handler.handle_request(data)
            
            # Add request ID to response
            response["request_id"] = data.get("request_id")
            response["type"] = "service_response"
            response["timestamp"] = datetime.utcnow().isoformat()
            
            # Send response back to Core
            await send_response_to_core(response)
            
        except Exception as e:
            logger.error(f"Error handling management message: {str(e)}")

async def send_response_to_core(response_data: Dict[str, Any]):
    """Send response back to Core service"""
    try:
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        channel = await connection.channel()
        
        # Declare response exchange
        response_exchange = await channel.declare_exchange("core_responses", aio_pika.ExchangeType.DIRECT, durable=True)
        
        # Send response
        await response_exchange.publish(
            aio_pika.Message(body=json.dumps(response_data).encode()),
            routing_key="core.response"
        )
        
        logger.info(f"Sent response for request {response_data.get('request_id')}")
        await connection.close()
        
    except Exception as e:
        logger.error(f"Error sending response to Core: {str(e)}")

async def start_management_service():
    """Start the management service consumer"""
    try:
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        channel = await connection.channel()
        
        # Declare management exchange and queue
        management_exchange = await channel.declare_exchange("management_exchange", aio_pika.ExchangeType.DIRECT, durable=True)
        management_queue = await channel.declare_queue("management_queue", durable=True)
        
        # Bind queue to exchange
        await management_queue.bind(management_exchange, routing_key="management.request")
        
        # Start consuming messages
        await management_queue.consume(handle_management_message)
        
        logger.info("Management service started, waiting for requests...")
        
        # Keep the service running
        try:
            await asyncio.Future()
        finally:
            await connection.close()
            
    except Exception as e:
        logger.error(f"Error starting management service: {str(e)}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(start_management_service())
