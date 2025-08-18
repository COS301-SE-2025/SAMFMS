"""
Error handling middleware for Core service
Provides consistent error responses and logging
"""

import logging
import traceback
from typing import Union
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from utils.response_utils import APIResponse

logger = logging.getLogger(__name__)

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware to handle errors consistently across the application"""
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except HTTPException as e:
            # Handle FastAPI HTTP exceptions
            return await self._handle_http_exception(request, e)
        except StarletteHTTPException as e:
            # Handle Starlette HTTP exceptions
            return await self._handle_starlette_exception(request, e)
        except Exception as e:
            # Handle unexpected exceptions
            return await self._handle_unexpected_exception(request, e)
    
    async def _handle_http_exception(self, request: Request, exc: HTTPException) -> JSONResponse:
        """Handle FastAPI HTTP exceptions"""
        error_response = APIResponse.error(
            message=exc.detail,
            error_code=f"HTTP_{exc.status_code}"
        )
        
        # Log warning for client errors, error for server errors
        if exc.status_code < 500:
            logger.warning(f"HTTP {exc.status_code} on {request.method} {request.url.path}: {exc.detail}")
        else:
            logger.error(f"HTTP {exc.status_code} on {request.method} {request.url.path}: {exc.detail}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response
        )
    
    async def _handle_starlette_exception(self, request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Handle Starlette HTTP exceptions"""
        error_response = APIResponse.error(
            message=exc.detail,
            error_code=f"HTTP_{exc.status_code}"
        )
        
        logger.warning(f"Starlette HTTP {exc.status_code} on {request.method} {request.url.path}: {exc.detail}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response
        )
    
    async def _handle_unexpected_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions"""
        # Generate correlation ID for tracking
        import uuid
        correlation_id = str(uuid.uuid4())
        
        # Log the full exception with traceback
        logger.error(
            f"Unexpected error [{correlation_id}] on {request.method} {request.url.path}: {str(exc)}",
            exc_info=True
        )
        
        # Return generic error response to avoid leaking sensitive information
        error_response = APIResponse.error(
            message="An unexpected error occurred",
            error_code="INTERNAL_SERVER_ERROR",
            details={"correlation_id": correlation_id}
        )
        
        return JSONResponse(
            status_code=500,
            content=error_response
        )

class ValidationErrorHandler:
    """Handler for validation errors"""
    
    @staticmethod
    def handle_validation_error(errors: list) -> HTTPException:
        """Convert validation errors to HTTPException"""
        error_messages = []
        for error in errors:
            if isinstance(error, dict):
                field = error.get('loc', ['unknown'])[-1]
                message = error.get('msg', 'Invalid value')
                error_messages.append(f"{field}: {message}")
            else:
                error_messages.append(str(error))
        
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Validation failed",
                "errors": error_messages
            }
        )

# Global exception handlers for specific exception types
async def service_unavailable_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle service unavailable exceptions"""
    error_response = APIResponse.error(
        message="Service temporarily unavailable",
        error_code="SERVICE_UNAVAILABLE"
    )
    
    return JSONResponse(
        status_code=503,
        content=error_response
    )

async def timeout_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle timeout exceptions"""
    error_response = APIResponse.error(
        message="Request timeout - service took too long to respond",
        error_code="REQUEST_TIMEOUT"
    )
    
    return JSONResponse(
        status_code=504,
        content=error_response
    )

async def authorization_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle authorization exceptions"""
    error_response = APIResponse.error(
        message="Access denied - insufficient permissions",
        error_code="AUTHORIZATION_FAILED"
    )
    
    return JSONResponse(
        status_code=403,
        content=error_response
    )
