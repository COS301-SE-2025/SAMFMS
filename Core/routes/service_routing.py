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

# Import standardized error handling
from schemas.error_responses import ErrorResponseBuilder, map_error_to_http_status

# Import request deduplication
from services.request_deduplicator import request_deduplicator

logger = logging.getLogger(__name__)

# Create the service routing router
service_router = APIRouter()

# Define service block mappings (updated to match actual service configurations)
SERVICE_BLOCKS = {
    "management": {
        "exchange": "service_requests",
        "queue": "management.requests",
        "routing_key": "management.requests"
    },
    "maintenance": {
        "exchange": "service_requests", 
        "queue": "maintenance.requests",
        "routing_key": "maintenance.requests"
    },
    "gps": {
        "exchange": "service_requests",
        "queue": "gps.requests",
        "routing_key": "gps.requests"
    },
    "trips": {
        "exchange": "service_requests",
        "queue": "trip_planning.requests",
        "routing_key": "trip_planning.requests"
    }
}

# Response tracking for RabbitMQ communication
pending_responses: Dict[str, asyncio.Future] = {}

def _extract_user_context(headers: dict) -> Dict[str, Any]:
    """Extract user information from request headers"""
    user_context = {}
    
    # Extract common authentication headers
    if "authorization" in headers:
        user_context["authorization"] = headers["authorization"]
    
    if "x-user-id" in headers:
        user_context["user_id"] = headers["x-user-id"]
    
    if "x-user-role" in headers:
        user_context["role"] = headers["x-user-role"]
    
    if "x-user-email" in headers:
        user_context["email"] = headers["x-user-email"]
    
    if "x-tenant-id" in headers:
        user_context["tenant_id"] = headers["x-tenant-id"]
    
    # Extract from JWT if present
    auth_header = headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        user_context["token"] = auth_header[7:]  # Remove "Bearer " prefix
    
    return user_context

def _normalize_path(path: str) -> str:
    """Normalize path for consistent processing"""
    if not path:
        return ""
    
    # Remove leading and trailing slashes, then split and rejoin
    cleaned_path = path.strip().lstrip('/').rstrip('/')
    if not cleaned_path:
        return ""
    
    # Split by slash, filter empty parts, and rejoin
    path_parts = [part for part in cleaned_path.split('/') if part.strip()]
    return '/'.join(path_parts) if path_parts else ""

def _map_error_to_status_code(error_type: str, error_message: str) -> int:
    """Map service error types to appropriate HTTP status codes"""
    error_type_lower = error_type.lower()
    error_message_lower = error_message.lower()
    
    # Authentication/Authorization errors
    if any(keyword in error_type_lower for keyword in ['auth', 'permission', 'unauthorized', 'forbidden']):
        return 403
    
    if any(keyword in error_message_lower for keyword in ['unauthorized', 'not authorized', 'permission denied']):
        return 403
    
    # Validation errors
    if any(keyword in error_type_lower for keyword in ['validation', 'invalid', 'bad_request']):
        return 400
    
    if any(keyword in error_message_lower for keyword in ['required', 'invalid', 'missing', 'malformed']):
        return 400
    
    # Not found errors
    if any(keyword in error_type_lower for keyword in ['notfound', 'not_found']):
        return 404
    
    if any(keyword in error_message_lower for keyword in ['not found', 'does not exist', 'cannot find']):
        return 404
    
    # Database/Service unavailable
    if any(keyword in error_type_lower for keyword in ['database', 'connection', 'unavailable']):
        return 503
    
    if any(keyword in error_message_lower for keyword in ['database', 'connection', 'unavailable', 'service unavailable']):
        return 503
    
    # Conflict errors
    if any(keyword in error_type_lower for keyword in ['conflict', 'duplicate']):
        return 409
    
    # Default to 500 for unknown errors
    return 500

def _get_timeout_for_operation(service_name: str, endpoint: str) -> float:
    """Get appropriate timeout for service operation"""
    # Service-specific timeout configurations
    timeout_configs = {
        "maintenance": {
            "records": 45.0,
            "analytics": 60.0,
            "health": 10.0,
            "licenses": 30.0,
            "notifications": 20.0,
            "vendors": 30.0,
            "default": 30.0
        },
        "management": {
            "vehicles": 35.0,
            "drivers": 35.0,
            "analytics": 60.0,
            "health": 10.0,
            "default": 30.0
        },
        "gps": {
            "tracking": 20.0,
            "locations": 25.0,
            "health": 10.0,
            "default": 30.0
        },
        "trips": {
            "planning": 45.0,
            "optimization": 60.0,
            "health": 10.0,
            "default": 30.0
        }
    }
    
    service_config = timeout_configs.get(service_name, {})
    
    # Check for specific endpoint patterns
    endpoint_lower = endpoint.lower()
    for pattern, timeout in service_config.items():
        if pattern != "default" and pattern in endpoint_lower:
            return timeout
    
    # Return default timeout for service or global default
    return service_config.get("default", 30.0)

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
    # Validate inputs
    if not service_name or not isinstance(service_name, str):
        raise HTTPException(status_code=400, detail="Invalid service name")
    
    if not method or not isinstance(method, str):
        raise HTTPException(status_code=400, detail="Invalid HTTP method")
    
    if service_name not in SERVICE_BLOCKS:
        raise HTTPException(status_code=404, detail=f"Service block '{service_name}' not found")
    
    service_config = SERVICE_BLOCKS[service_name]
    
    # Generate unique request ID for correlation
    request_id = str(uuid.uuid4())
    
    # Process and normalize the path using standardized function
    processed_path = _normalize_path(path)
    
    logger.debug(f"Processing request to {service_name} - Original path: {path}, Processed path: {processed_path}")
    
    # Parse JSON body if present and merge with query params
    parsed_body = {}
    if body:
        try:
            parsed_body = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON body for request {request_id}")
            parsed_body = {}
    
    # Merge query params and body data, with body taking precedence
    request_data = {**(query_params or {}), **parsed_body}
    
    # Prepare message for service block (updated to match service expectations)
    message = {
        "correlation_id": request_id,  # Use correlation_id instead of request_id
        "method": method,
        "endpoint": processed_path,  # Use processed path
        "headers": dict(headers),
        "body": body.decode('utf-8') if body else None,
        "data": request_data,  # Merged query params and parsed body
        "user_context": _extract_user_context(headers),  # Extract user info from headers
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
        
        logger.debug(f"Sent request {request_id} to {service_name} service: {method} {path}")
        
        # Wait for response with configurable timeout based on service and operation
        try:
            timeout = _get_timeout_for_operation(service_name, processed_path)
            response = await asyncio.wait_for(response_future, timeout=timeout)
            
            # Check if service returned an error and map to appropriate HTTP status
            if response.get("status") == "error":
                error_detail = response.get("error", {})
                if isinstance(error_detail, dict):
                    error_type = error_detail.get("type", "ServiceError")
                    error_msg = error_detail.get("message", "Service error")
                    error_code = error_detail.get("code")
                else:
                    error_msg = str(error_detail)
                    error_type = "ServiceError"
                    error_code = None
                
                # Map error types to HTTP status codes using standardized mapping
                status_code = map_error_to_http_status(error_type)
                
                # Create standardized error response
                error_response = ErrorResponseBuilder.internal_error(
                    message=error_msg,
                    error_details={
                        "service": service_name,
                        "error_type": error_type,
                        "error_code": error_code
                    },
                    correlation_id=request_id,
                    service="core-gateway"
                )
                
                logger.error(f"Service {service_name} returned error: {error_msg}")
                raise HTTPException(status_code=status_code, detail=error_response)
            
            return response
        except asyncio.TimeoutError:
            error_response = ErrorResponseBuilder.timeout_error(
                message=f"Service {service_name} timeout",
                timeout_seconds=timeout,
                correlation_id=request_id,
                service="core-gateway"
            )
            logger.error(f"Timeout waiting for response from {service_name} service for request {request_id}")
            raise HTTPException(status_code=504, detail=error_response)
        
    except Exception as e:
        error_response = ErrorResponseBuilder.service_unavailable_error(
            message=f"Service {service_name} error: {str(e)}",
            service_name=service_name,
            correlation_id=request_id,
            service="core-gateway"
        )
        logger.error(f"Error routing to {service_name} service: {str(e)}")
        raise HTTPException(status_code=502, detail=error_response)
    
    finally:
        # Clean up pending response
        pending_responses.pop(request_id, None)

async def handle_service_response(message_data: Dict[str, Any]):
    """
    Handle responses from service blocks
    
    Args:
        message_data: Response message from service block
    """
    # Try both correlation_id and request_id for backward compatibility
    request_id = message_data.get("correlation_id") or message_data.get("request_id")
    
    if request_id and request_id in pending_responses:
        future = pending_responses[request_id]
        if not future.done():
            future.set_result(message_data)
            logger.debug(f"Received response for request {request_id}")
    else:
        logger.warning(f"Received response for unknown request ID: {request_id}")

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
        
        # Return response from service block with proper status code handling
        response_data = response.get("data", {})
        response_status = response.get("status_code", 200)
        response_headers = response.get("headers", {})
        
        return JSONResponse(
            content=response_data,
            status_code=response_status,
            headers=response_headers
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
        
        # Return response from service block - standardized format
        response_data = response.get("data", {})
        response_status = response.get("status_code", 200)
        response_headers = response.get("headers", {})
        
        return JSONResponse(
            content=response_data,
            status_code=response_status,
            headers=response_headers
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
        
        # Return response from service block - standardized format
        response_data = response.get("data", {})
        response_status = response.get("status_code", 200)
        response_headers = response.get("headers", {})
        
        return JSONResponse(
            content=response_data,
            status_code=response_status,
            headers=response_headers
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
            content=response.get("body", {}),
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
