"""
Comprehensive Error Handling System for SAMFMS Core
Provides structured error handling, correlation IDs, and consistent error responses
"""

import logging
import traceback
import uuid
from typing import Any, Dict, Optional, List
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class ErrorCode(str, Enum):
    """Standardized error codes"""
    # Client errors (4xx)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    AUTHORIZATION_FAILED = "AUTHORIZATION_FAILED"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    INVALID_REQUEST = "INVALID_REQUEST"
    
    # Server errors (5xx)
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    SERVICE_TIMEOUT = "SERVICE_TIMEOUT"
    DATABASE_ERROR = "DATABASE_ERROR"
    MESSAGE_QUEUE_ERROR = "MESSAGE_QUEUE_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    
    # Business logic errors
    BUSINESS_RULE_VIOLATION = "BUSINESS_RULE_VIOLATION"
    PLUGIN_ERROR = "PLUGIN_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"

@dataclass
class ErrorContext:
    """Error context information"""
    correlation_id: str
    timestamp: str
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    service: Optional[str] = None
    trace_id: Optional[str] = None

@dataclass
class ErrorDetail:
    """Detailed error information"""
    code: ErrorCode
    message: str
    context: ErrorContext
    details: Optional[Dict[str, Any]] = None
    stack_trace: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result['code'] = self.code.value
        result['context'] = asdict(self.context)
        return result

class SAMFMSError(Exception):
    """Base exception class for SAMFMS Core"""
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.timestamp = datetime.utcnow().isoformat()
    
    def get_status_code(self) -> int:
        """Get HTTP status code for this error"""
        status_map = {
            ErrorCode.VALIDATION_ERROR: 400,
            ErrorCode.AUTHENTICATION_REQUIRED: 401,
            ErrorCode.AUTHORIZATION_FAILED: 403,
            ErrorCode.RESOURCE_NOT_FOUND: 404,
            ErrorCode.RESOURCE_CONFLICT: 409,
            ErrorCode.RATE_LIMIT_EXCEEDED: 429,
            ErrorCode.INVALID_REQUEST: 400,
            ErrorCode.BUSINESS_RULE_VIOLATION: 422,
            ErrorCode.INTERNAL_SERVER_ERROR: 500,
            ErrorCode.SERVICE_UNAVAILABLE: 503,
            ErrorCode.SERVICE_TIMEOUT: 504,
            ErrorCode.DATABASE_ERROR: 500,
            ErrorCode.MESSAGE_QUEUE_ERROR: 500,
            ErrorCode.EXTERNAL_SERVICE_ERROR: 502,
            ErrorCode.PLUGIN_ERROR: 500,
            ErrorCode.CONFIGURATION_ERROR: 500,
        }
        return status_map.get(self.code, 500)
    
    def is_client_error(self) -> bool:
        """Check if this is a client error (4xx)"""
        return 400 <= self.get_status_code() < 500
    
    def is_server_error(self) -> bool:
        """Check if this is a server error (5xx)"""
        return self.get_status_code() >= 500
    
    def to_error_detail(self, context: ErrorContext) -> ErrorDetail:
        """Convert to ErrorDetail object"""
        return ErrorDetail(
            code=self.code,
            message=self.message,
            context=context,
            details=self.details,
            stack_trace=traceback.format_exc() if not self.is_client_error() else None
        )

class ValidationError(SAMFMSError):
    """Validation error"""
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        super().__init__(message, ErrorCode.VALIDATION_ERROR, **kwargs)
        if field:
            self.details['field'] = field

class AuthenticationError(SAMFMSError):
    """Authentication error"""
    def __init__(self, message: str = "Authentication required", **kwargs):
        super().__init__(message, ErrorCode.AUTHENTICATION_REQUIRED, **kwargs)

class AuthorizationError(SAMFMSError):
    """Authorization error"""
    def __init__(self, message: str = "Access denied", **kwargs):
        super().__init__(message, ErrorCode.AUTHORIZATION_FAILED, **kwargs)

class ResourceNotFoundError(SAMFMSError):
    """Resource not found error"""
    def __init__(self, resource: str, identifier: str, **kwargs):
        message = f"{resource} with identifier '{identifier}' not found"
        super().__init__(message, ErrorCode.RESOURCE_NOT_FOUND, **kwargs)
        self.details.update({'resource': resource, 'identifier': identifier})

class ServiceUnavailableError(SAMFMSError):
    """Service unavailable error"""
    def __init__(self, service: str, **kwargs):
        message = f"Service '{service}' is currently unavailable"
        super().__init__(message, ErrorCode.SERVICE_UNAVAILABLE, **kwargs)
        self.details['service'] = service

class ServiceTimeoutError(SAMFMSError):
    """Service timeout error"""
    def __init__(self, service: str, timeout: int, **kwargs):
        message = f"Service '{service}' timed out after {timeout}s"
        super().__init__(message, ErrorCode.SERVICE_TIMEOUT, **kwargs)
        self.details.update({'service': service, 'timeout': timeout})

class DatabaseError(SAMFMSError):
    """Database error"""
    def __init__(self, operation: str, **kwargs):
        message = f"Database error during {operation}"
        super().__init__(message, ErrorCode.DATABASE_ERROR, **kwargs)
        self.details['operation'] = operation

class MessageQueueError(SAMFMSError):
    """Message queue error"""
    def __init__(self, operation: str, queue: str, **kwargs):
        message = f"Message queue error during {operation} on queue '{queue}'"
        super().__init__(message, ErrorCode.MESSAGE_QUEUE_ERROR, **kwargs)
        self.details.update({'operation': operation, 'queue': queue})

class PluginError(SAMFMSError):
    """Plugin error"""
    def __init__(self, plugin_id: str, operation: str, **kwargs):
        message = f"Plugin '{plugin_id}' error during {operation}"
        super().__init__(message, ErrorCode.PLUGIN_ERROR, **kwargs)
        self.details.update({'plugin_id': plugin_id, 'operation': operation})

class ServiceDiscoveryError(SAMFMSError):
    """Service discovery error"""
    pass

class ServiceNotFoundError(ServiceDiscoveryError):
    """Service not found error"""
    pass

class HealthCheckError(ServiceDiscoveryError):
    """Health check error"""
    pass

class ErrorResponseBuilder:
    """Builds standardized error responses"""
    
    @staticmethod
    def build_error_response(
        error: SAMFMSError,
        request: Optional[Request] = None,
        include_stack_trace: bool = False
    ) -> Dict[str, Any]:
        """Build standardized error response"""
        
        # Create error context
        context = ErrorContext(
            correlation_id=error.correlation_id,
            timestamp=error.timestamp,
            request_id=getattr(request, 'state', {}).get('request_id') if request else None,
            user_id=getattr(request, 'state', {}).get('user_id') if request else None,
            endpoint=str(request.url.path) if request else None,
            method=request.method if request else None,
        )
        
        # Create error detail
        error_detail = error.to_error_detail(context)
        
        # Build response
        response = {
            "success": False,
            "error": {
                "code": error_detail.code.value,
                "message": error_detail.message,
                "correlation_id": error_detail.context.correlation_id,
                "timestamp": error_detail.context.timestamp
            }
        }
        
        # Add details if present
        if error_detail.details:
            response["error"]["details"] = error_detail.details
        
        # Add stack trace for server errors in development
        if include_stack_trace and error_detail.stack_trace and error.is_server_error():
            response["error"]["stack_trace"] = error_detail.stack_trace
        
        # Add request context for debugging
        if request:
            response["error"]["request"] = {
                "method": error_detail.context.method,
                "endpoint": error_detail.context.endpoint,
                "request_id": error_detail.context.request_id
            }
        
        return response

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware to add correlation IDs to requests"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        request.state.request_id = str(uuid.uuid4())
        
        # Add to response headers
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Request-ID"] = request.state.request_id
        
        return response

class ComprehensiveErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Comprehensive error handling middleware"""
    
    def __init__(self, app, include_stack_trace: bool = False):
        super().__init__(app)
        self.include_stack_trace = include_stack_trace
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
            
        except SAMFMSError as e:
            # Handle our custom errors
            return await self._handle_samfms_error(request, e)
            
        except HTTPException as e:
            # Handle FastAPI HTTP exceptions
            return await self._handle_http_exception(request, e)
            
        except Exception as e:
            # Handle unexpected exceptions
            return await self._handle_unexpected_exception(request, e)
    
    async def _handle_samfms_error(self, request: Request, exc: SAMFMSError) -> JSONResponse:
        """Handle SAMFMS custom errors"""
        response_data = ErrorResponseBuilder.build_error_response(
            exc, request, self.include_stack_trace
        )
        
        # Log appropriately based on error type
        if exc.is_client_error():
            logger.warning(
                f"Client error [{exc.correlation_id}]: {exc.message}",
                extra={
                    "correlation_id": exc.correlation_id,
                    "error_code": exc.code.value,
                    "endpoint": str(request.url.path),
                    "method": request.method
                }
            )
        else:
            logger.error(
                f"Server error [{exc.correlation_id}]: {exc.message}",
                extra={
                    "correlation_id": exc.correlation_id,
                    "error_code": exc.code.value,
                    "endpoint": str(request.url.path),
                    "method": request.method,
                    "details": exc.details
                },
                exc_info=True
            )
        
        return JSONResponse(
            status_code=exc.get_status_code(),
            content=response_data
        )
    
    async def _handle_http_exception(self, request: Request, exc: HTTPException) -> JSONResponse:
        """Handle FastAPI HTTP exceptions"""
        correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))
        
        # Convert to SAMFMS error
        if exc.status_code == 401:
            error_code = ErrorCode.AUTHENTICATION_REQUIRED
        elif exc.status_code == 403:
            error_code = ErrorCode.AUTHORIZATION_FAILED
        elif exc.status_code == 404:
            error_code = ErrorCode.RESOURCE_NOT_FOUND
        elif exc.status_code == 422:
            error_code = ErrorCode.VALIDATION_ERROR
        else:
            error_code = ErrorCode.INVALID_REQUEST
        
        samfms_error = SAMFMSError(
            message=str(exc.detail),
            code=error_code,
            correlation_id=correlation_id
        )
        
        return await self._handle_samfms_error(request, samfms_error)
    
    async def _handle_unexpected_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions"""
        correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))
        
        # Log the full exception
        logger.error(
            f"Unexpected error [{correlation_id}]: {str(exc)}",
            extra={
                "correlation_id": correlation_id,
                "endpoint": str(request.url.path),
                "method": request.method,
                "exception_type": type(exc).__name__
            },
            exc_info=True
        )
        
        # Create SAMFMS error
        samfms_error = SAMFMSError(
            message="An unexpected error occurred",
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            correlation_id=correlation_id,
            details={"exception_type": type(exc).__name__}
        )
        
        return await self._handle_samfms_error(request, samfms_error)

# Utility functions for error handling
def raise_validation_error(message: str, field: Optional[str] = None, **kwargs):
    """Raise a validation error"""
    raise ValidationError(message, field, **kwargs)

def raise_not_found_error(resource: str, identifier: str, **kwargs):
    """Raise a resource not found error"""
    raise ResourceNotFoundError(resource, identifier, **kwargs)

def raise_service_error(service: str, **kwargs):
    """Raise a service unavailable error"""
    raise ServiceUnavailableError(service, **kwargs)

def create_error_handler(include_stack_trace: bool = False):
    """Create error handling middleware"""
    return ComprehensiveErrorHandlingMiddleware(include_stack_trace=include_stack_trace)

# Error logging utilities
def log_error_with_context(
    message: str,
    correlation_id: Optional[str] = None,
    **context
):
    """Log error with structured context"""
    logger.error(
        message,
        extra={
            "correlation_id": correlation_id or str(uuid.uuid4()),
            **context
        }
    )
