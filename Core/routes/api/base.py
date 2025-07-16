"""
Base service proxy functionality
Provides common utilities for all API route modules
Enhanced with RabbitMQ communication and standardized response handling
"""

from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any
from datetime import datetime
import logging

from utils.exceptions import (
    ServiceUnavailableError, 
    AuthorizationError, 
    ValidationError, 
    ServiceTimeoutError
)
from services.request_router import request_router
from services.core_auth_service import core_auth_service

logger = logging.getLogger(__name__)
security = HTTPBearer()

class ServiceProxyError(Exception):
    """Base exception for service proxy errors"""
    pass

async def handle_service_request(
    endpoint: str,
    method: str,
    data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials,
    auth_endpoint: str = None
) -> Dict[str, Any]:
    """
    Enhanced handler for service requests with standardized response format
    Uses RabbitMQ for backend service communication
    """
    try:
        # Use provided auth endpoint or default to the same endpoint
        auth_endpoint = auth_endpoint or endpoint
        
        # Authorize request
        user_context = await core_auth_service.authorize_request(
            credentials.credentials, auth_endpoint, method
        )
        logger.info(f"Authorization successful for user: {user_context.get('user_id', 'unknown')}")
        
        # Determine service type based on endpoint
        service_name = _get_service_name_from_endpoint(endpoint)
        
        # Route to appropriate service
        if service_name in ["maintenance", "management"]:
            # Use RabbitMQ for microservices
            response = await _send_rabbitmq_request(
                service_name=service_name,
                endpoint=endpoint,
                method=method,
                data=data,
                user_context=user_context
            )
        else:
            # Use HTTP proxy for other services
            response = await request_router.route_request(
                endpoint=endpoint,
                method=method,
                data=data,
                user_context=user_context
            )
        
        # Standardize response format
        return _standardize_response(response)
        
    except AuthorizationError as e:
        logger.warning(f"Authorization failed for {endpoint}: {e.message}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)
    except ServiceUnavailableError as e:
        logger.error(f"Service unavailable for {endpoint}: {e.message}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message)
    except ServiceTimeoutError as e:
        logger.error(f"Service timeout for {endpoint}: {e.message}")
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=e.message)
    except ValidationError as e:
        logger.warning(f"Validation error for {endpoint}: {e.message}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error for {endpoint}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

def _get_service_name_from_endpoint(endpoint: str) -> str:
    """Extract service name from endpoint"""
    if "/maintenance/" in endpoint:
        return "maintenance"
    elif "/assignments" in endpoint or "/vehicles" in endpoint or "/drivers" in endpoint:
        return "management"
    elif "/gps/" in endpoint:
        return "gps"
    elif "/security/" in endpoint:
        return "security"
    else:
        return "unknown"

async def _send_rabbitmq_request(
    service_name: str,
    endpoint: str,
    method: str,
    data: Dict[str, Any],
    user_context: Dict[str, Any]
) -> Dict[str, Any]:
    """Send request to microservice via RabbitMQ"""
    import asyncio
    import uuid
    from datetime import datetime
    from Core.rabbitmq.producer import rabbitmq_producer
    
    try:
        request_data = {
            "action": method,
            "endpoint": endpoint,
            "data": data,
            "user_context": user_context,
            "request_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        queue_name = f"{service_name}_service_requests"
        
        response = await rabbitmq_producer.send_service_request(
            queue_name,
            request_data,
            timeout=30
        )
        
        return response
        
    except Exception as e:
        logger.error(f"RabbitMQ request failed for {service_name}: {e}")
        raise ServiceUnavailableError(f"Failed to communicate with {service_name} service")

def _standardize_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """Standardize response format across all services"""
    if not isinstance(response, dict):
        return {
            "success": True,
            "data": response,
            "message": "Request completed successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # If response is already in standard format, return as-is
    if "success" in response:
        return response
    
    # Transform legacy response formats
    if "data" in response:
        return {
            "success": True,
            "data": response["data"],
            "message": response.get("message", "Request completed successfully"),
            "timestamp": response.get("timestamp", datetime.utcnow().isoformat())
        }
    
    # For direct data responses
    return {
        "success": True,
        "data": response,
        "message": "Request completed successfully",
        "timestamp": datetime.utcnow().isoformat()
    }

def validate_required_fields(data: Dict[str, Any], required_fields: list) -> None:
    """
    Validate that required fields are present in the data
    """
    if not data:
        raise ValidationError("Request data is required")
    
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")

async def authorize_and_route(
    credentials: HTTPAuthorizationCredentials,
    endpoint: str,
    method: str,
    data: Dict[str, Any] = None,
    auth_endpoint: str = None
) -> Dict[str, Any]:
    """
    Simplified authorization and routing for common use cases
    """
    return await handle_service_request(
        endpoint=endpoint,
        method=method,
        data=data or {},
        credentials=credentials,
        auth_endpoint=auth_endpoint
    )
