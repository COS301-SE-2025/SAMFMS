"""
Standardized Error Response Schema
Ensures consistent error format across all services
"""

from typing import Dict, Any, Optional, Union
from pydantic import BaseModel
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ErrorDetail(BaseModel):
    """Standardized error detail structure"""
    type: str                           # Error type/category
    message: str                        # Human-readable message
    code: Optional[str] = None          # Error code for client handling
    field: Optional[str] = None         # Field name for validation errors
    details: Optional[Dict[str, Any]] = None  # Additional error context

class StandardErrorResponse(BaseModel):
    """Standardized error response structure"""
    status: str = "error"
    error: ErrorDetail
    correlation_id: Optional[str] = None
    timestamp: str
    service: Optional[str] = None
    
    @classmethod
    def create(
        cls,
        error_type: str,
        message: str,
        correlation_id: str = None,
        service: str = None,
        code: str = None,
        field: str = None,
        details: Dict[str, Any] = None
    ) -> "StandardErrorResponse":
        """Create standardized error response"""
        return cls(
            error=ErrorDetail(
                type=error_type,
                message=message,
                code=code,
                field=field,
                details=details
            ),
            correlation_id=correlation_id,
            timestamp=datetime.utcnow().isoformat(),
            service=service
        )

class ErrorTypes:
    """Standard error type constants"""
    VALIDATION_ERROR = "ValidationError"
    AUTHENTICATION_ERROR = "AuthenticationError"
    AUTHORIZATION_ERROR = "AuthorizationError"
    NOT_FOUND_ERROR = "NotFoundError"
    CONFLICT_ERROR = "ConflictError"
    DATABASE_ERROR = "DatabaseError"
    SERVICE_UNAVAILABLE_ERROR = "ServiceUnavailableError"
    TIMEOUT_ERROR = "TimeoutError"
    RATE_LIMIT_ERROR = "RateLimitError"
    INTERNAL_ERROR = "InternalError"
    CIRCUIT_BREAKER_ERROR = "CircuitBreakerError"

class ErrorResponseBuilder:
    """Builder for creating standardized error responses"""
    
    @staticmethod
    def validation_error(
        message: str,
        field: str = None,
        correlation_id: str = None,
        service: str = None
    ) -> Dict[str, Any]:
        """Create validation error response"""
        return StandardErrorResponse.create(
            error_type=ErrorTypes.VALIDATION_ERROR,
            message=message,
            field=field,
            correlation_id=correlation_id,
            service=service,
            code="VALIDATION_FAILED"
        ).model_dump()
    
    @staticmethod
    def authentication_error(
        message: str = "Authentication required",
        correlation_id: str = None,
        service: str = None
    ) -> Dict[str, Any]:
        """Create authentication error response"""
        return StandardErrorResponse.create(
            error_type=ErrorTypes.AUTHENTICATION_ERROR,
            message=message,
            correlation_id=correlation_id,
            service=service,
            code="AUTH_REQUIRED"
        ).model_dump()
    
    @staticmethod
    def authorization_error(
        message: str = "Insufficient permissions",
        correlation_id: str = None,
        service: str = None
    ) -> Dict[str, Any]:
        """Create authorization error response"""
        return StandardErrorResponse.create(
            error_type=ErrorTypes.AUTHORIZATION_ERROR,
            message=message,
            correlation_id=correlation_id,
            service=service,
            code="INSUFFICIENT_PERMISSIONS"
        ).model_dump()
    
    @staticmethod
    def not_found_error(
        message: str,
        resource: str = None,
        correlation_id: str = None,
        service: str = None
    ) -> Dict[str, Any]:
        """Create not found error response"""
        details = {"resource": resource} if resource else None
        return StandardErrorResponse.create(
            error_type=ErrorTypes.NOT_FOUND_ERROR,
            message=message,
            details=details,
            correlation_id=correlation_id,
            service=service,
            code="RESOURCE_NOT_FOUND"
        ).model_dump()
    
    @staticmethod
    def database_error(
        message: str = "Database operation failed",
        correlation_id: str = None,
        service: str = None
    ) -> Dict[str, Any]:
        """Create database error response"""
        return StandardErrorResponse.create(
            error_type=ErrorTypes.DATABASE_ERROR,
            message=message,
            correlation_id=correlation_id,
            service=service,
            code="DATABASE_ERROR"
        ).model_dump()
    
    @staticmethod
    def service_unavailable_error(
        message: str,
        service_name: str = None,
        correlation_id: str = None,
        service: str = None
    ) -> Dict[str, Any]:
        """Create service unavailable error response"""
        details = {"unavailable_service": service_name} if service_name else None
        return StandardErrorResponse.create(
            error_type=ErrorTypes.SERVICE_UNAVAILABLE_ERROR,
            message=message,
            details=details,
            correlation_id=correlation_id,
            service=service,
            code="SERVICE_UNAVAILABLE"
        ).model_dump()
    
    @staticmethod
    def timeout_error(
        message: str = "Request timeout",
        timeout_seconds: float = None,
        correlation_id: str = None,
        service: str = None
    ) -> Dict[str, Any]:
        """Create timeout error response"""
        details = {"timeout_seconds": timeout_seconds} if timeout_seconds else None
        return StandardErrorResponse.create(
            error_type=ErrorTypes.TIMEOUT_ERROR,
            message=message,
            details=details,
            correlation_id=correlation_id,
            service=service,
            code="REQUEST_TIMEOUT"
        ).model_dump()
    
    @staticmethod
    def circuit_breaker_error(
        message: str,
        service_name: str = None,
        correlation_id: str = None,
        service: str = None
    ) -> Dict[str, Any]:
        """Create circuit breaker error response"""
        details = {"circuit_breaker_service": service_name} if service_name else None
        return StandardErrorResponse.create(
            error_type=ErrorTypes.CIRCUIT_BREAKER_ERROR,
            message=message,
            details=details,
            correlation_id=correlation_id,
            service=service,
            code="CIRCUIT_BREAKER_OPEN"
        ).model_dump()
    
    @staticmethod
    def internal_error(
        message: str = "Internal server error",
        error_details: Dict[str, Any] = None,
        correlation_id: str = None,
        service: str = None
    ) -> Dict[str, Any]:
        """Create internal error response"""
        return StandardErrorResponse.create(
            error_type=ErrorTypes.INTERNAL_ERROR,
            message=message,
            details=error_details,
            correlation_id=correlation_id,
            service=service,
            code="INTERNAL_ERROR"
        ).model_dump()

def map_error_to_http_status(error_type: str) -> int:
    """Map error type to appropriate HTTP status code"""
    status_map = {
        ErrorTypes.VALIDATION_ERROR: 400,
        ErrorTypes.AUTHENTICATION_ERROR: 401,
        ErrorTypes.AUTHORIZATION_ERROR: 403,
        ErrorTypes.NOT_FOUND_ERROR: 404,
        ErrorTypes.CONFLICT_ERROR: 409,
        ErrorTypes.RATE_LIMIT_ERROR: 429,
        ErrorTypes.INTERNAL_ERROR: 500,
        ErrorTypes.DATABASE_ERROR: 503,
        ErrorTypes.SERVICE_UNAVAILABLE_ERROR: 503,
        ErrorTypes.CIRCUIT_BREAKER_ERROR: 503,
        ErrorTypes.TIMEOUT_ERROR: 504,
    }
    return status_map.get(error_type, 500)
