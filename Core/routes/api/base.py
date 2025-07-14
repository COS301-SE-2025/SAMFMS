"""
Base service proxy functionality
Provides common utilities for all API route modules
"""

from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any
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
    Common handler for service requests with authentication and error handling
    """
    try:
        # Use provided auth endpoint or default to the same endpoint
        auth_endpoint = auth_endpoint or endpoint
        
        # Authorize request
        user_context = await core_auth_service.authorize_request(
            credentials.credentials, auth_endpoint, method
        )
        logger.info(f"Authorization successful for user: {user_context.get('user_id', 'unknown')}")
        
        # Route to appropriate service
        response = await request_router.route_request(
            endpoint=endpoint,
            method=method,
            data=data,
            user_context=user_context
        )
        
        return response
        
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
