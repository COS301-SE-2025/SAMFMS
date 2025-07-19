"""
Service Routing Module
Implements simplified path-based routing to service blocks via RabbitMQ
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
import asyncio
import json
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
import logging

# Import RabbitMQ components
from rabbitmq.producer import publish_message
from rabbitmq.consumer import consume_messages
import aio_pika

logger = logging.getLogger(__name__)

# Create the service routing router
service_router = APIRouter()

# Define service block mappings
SERVICE_BLOCKS = {
    "management": {
        "exchange": "service_requests",
        "queue": "management_queue",
        "routing_key": "management.requests"
    },
    "maintenance": {
        "exchange": "service_requests", 
        "queue": "maintenance_queue",
        "routing_key": "maintenance.requests"
    },
    "gps": {
        "exchange": "service_requests",
        "queue": "gps_queue", 
        "routing_key": "gps.requests"
    },
    "trips": {
        "exchange": "service_requests",
        "queue": "trip_planning_queue",
        "routing_key": "trips.requests"
    }
}

# Response tracking for RabbitMQ communication
pending_responses: Dict[str, asyncio.Future] = {}

async def route_to_service_block(
    service_name: str,
    method: str,
    path: str,
    headers: dict,
    body: Optional[bytes] = None,
    query_params: Optional[dict] = None
) -> Dict[str, Any]:
    """
    Route a request to a service block via RabbitMQ
    
    Args:
        service_name: Name of the service block (management, maintenance, gps, trips)
        method: HTTP method (GET, POST, PUT, DELETE, etc.)
        path: The path after stripping the service prefix
        headers: Request headers
        body: Request body (if any)
        query_params: Query parameters
    
    Returns:
        Dict containing the response from the service block
    """
    if service_name not in SERVICE_BLOCKS:
        raise HTTPException(status_code=404, detail=f"Service block '{service_name}' not found")
    
    service_config = SERVICE_BLOCKS[service_name]
    
    # Generate unique request ID for correlation
    request_id = str(uuid.uuid4())
    
    # Prepare message for service block
    message = {
        "correlation_id": request_id,
        "method": method,
        "endpoint": path,
        "data": query_params or {},
        "user_context": dict(headers),
        "body": body.decode('utf-8') if body else None,
        "timestamp": datetime.utcnow().isoformat(),
        "source": "core-gateway"
    }
    
    # Create future for response tracking
    response_future = asyncio.Future()
    pending_responses[request_id] = response_future
    
    try:
        # Send message to service block
        await publish_message(
            exchange_name=service_config["exchange"],
            exchange_type=aio_pika.ExchangeType.DIRECT,
            message=message,
            routing_key=service_config["routing_key"]
        )
        
        logger.info(f"Sent request {request_id} to {service_name} service: {method} {path}")
        
        # Wait for response with timeout
        try:
            response = await asyncio.wait_for(response_future, timeout=30.0)
            return response
        except asyncio.TimeoutError:
            logger.error(f"Timeout waiting for response from {service_name} service for request {request_id}")
            raise HTTPException(status_code=504, detail=f"Service {service_name} timeout")
        
    except Exception as e:
        logger.error(f"Error routing to {service_name} service: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Service {service_name} error: {str(e)}")
    
    finally:
        # Clean up pending response
        pending_responses.pop(request_id, None)

async def handle_service_response(message_data: Dict[str, Any]):
    """
    Handle responses from service blocks
    
    Args:
        message_data: Response message from service block
    """
    correlation_id = message_data.get("correlation_id")
    
    if correlation_id and correlation_id in pending_responses:
        future = pending_responses[correlation_id]
        if not future.done():
            future.set_result(message_data)
            logger.info(f"Received response for correlation {correlation_id}")
    else:
        logger.warning(f"Received response for unknown correlation ID: {correlation_id}")

# Route handlers for each service block

@service_router.api_route("/management/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def management_route(request: Request, path: str = ""):
    """Route requests to management service block"""
    
    # Get request details
    method = request.method
    headers = dict(request.headers)
    query_params = dict(request.query_params)
    
    # Get request body if present
    body = None
    if method in ["POST", "PUT", "PATCH"]:
        body = await request.body()
    
    # Ensure path starts with /
    if not path.startswith("/"):
        path = "/" + path
    
    logger.info(f"Routing to management service: {method} {path}")
    
    try:
        response = await route_to_service_block(
            service_name="management",
            method=method,
            path=path,
            headers=headers,
            body=body,
            query_params=query_params
        )
        
        # Return response from service block
        return JSONResponse(
            content=response.get("data", {}),
            status_code=response.get("status_code", 200),
            headers=response.get("headers", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Management service routing error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@service_router.api_route("/maintenance/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def maintenance_route(request: Request, path: str = ""):
    """Route requests to maintenance service block"""
    
    # Get request details
    method = request.method
    headers = dict(request.headers)
    query_params = dict(request.query_params)
    
    # Get request body if present
    body = None
    if method in ["POST", "PUT", "PATCH"]:
        body = await request.body()
    
    # Ensure path starts with /
    if not path.startswith("/"):
        path = "/" + path
    
    logger.info(f"Routing to maintenance service: {method} {path}")
    
    try:
        response = await route_to_service_block(
            service_name="maintenance",
            method=method,
            path=path,
            headers=headers,
            body=body,
            query_params=query_params
        )
        
        # Return response from service block
        return JSONResponse(
            content=response.get("data", {}),
            status_code=response.get("status_code", 200),
            headers=response.get("headers", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Maintenance service routing error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@service_router.api_route("/gps/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def gps_route(request: Request, path: str = ""):
    """Route requests to GPS service block"""
    
    # Get request details
    method = request.method
    headers = dict(request.headers)
    query_params = dict(request.query_params)
    
    # Get request body if present
    body = None
    if method in ["POST", "PUT", "PATCH"]:
        body = await request.body()
    
    # Ensure path starts with /
    if not path.startswith("/"):
        path = "/" + path
    
    logger.info(f"Routing to GPS service: {method} {path}")
    
    try:
        response = await route_to_service_block(
            service_name="gps",
            method=method,
            path=path,
            headers=headers,
            body=body,
            query_params=query_params
        )
        
        # Return response from service block
        return JSONResponse(
            content=response.get("data", {}),
            status_code=response.get("status_code", 200),
            headers=response.get("headers", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GPS service routing error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@service_router.api_route("/trips/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def trips_route(request: Request, path: str = ""):
    """Route requests to trip planning service block"""
    
    # Get request details
    method = request.method
    headers = dict(request.headers)
    query_params = dict(request.query_params)
    
    # Get request body if present
    body = None
    if method in ["POST", "PUT", "PATCH"]:
        body = await request.body()
    
    # Ensure path starts with /
    if not path.startswith("/"):
        path = "/" + path
    
    logger.info(f"Routing to trip planning service: {method} {path}")
    
    try:
        response = await route_to_service_block(
            service_name="trips",
            method=method,
            path=path,
            headers=headers,
            body=body,
            query_params=query_params
        )
        
        # Return response from service block
        return JSONResponse(
            content=response.get("data", {}),
            status_code=response.get("status_code", 200),
            headers=response.get("headers", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Trip planning service routing error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Route to show available services
@service_router.get("/services")
async def list_services():
    """List available service blocks"""
    return {
        "services": list(SERVICE_BLOCKS.keys()),
        "routing_info": {
            "management": "/management/* -> Management service block",
            "maintenance": "/maintenance/* -> Maintenance service block",
            "gps": "/gps/* -> GPS service block",
            "trips": "/trips/* -> Trip planning service block"
        },
        "message": "Use these prefixes to route requests to the appropriate service blocks"
    }

__all__ = ["service_router", "handle_service_response", "pending_responses"]
