"""
Standardized Error Response Schema for Maintenance Service
Ensures consistent error format across all services
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MaintenanceErrorTypes:
    """Standard error type constants for maintenance service"""
    VALIDATION_ERROR = "ValidationError"
    AUTHENTICATION_ERROR = "AuthenticationError"
    AUTHORIZATION_ERROR = "AuthorizationError"
    NOT_FOUND_ERROR = "NotFoundError"
    CONFLICT_ERROR = "ConflictError"
    DATABASE_ERROR = "DatabaseError"
    SERVICE_UNAVAILABLE_ERROR = "ServiceUnavailableError"
    TIMEOUT_ERROR = "TimeoutError"
    INTERNAL_ERROR = "InternalError"
    MAINTENANCE_ERROR = "MaintenanceError"

class MaintenanceErrorBuilder:
    """Builder for creating standardized error responses in maintenance service"""
    
    @staticmethod
    def create_error_response(
        error_type: str,
        message: str,
        correlation_id: str = None,
        code: str = None,
        field: str = None,
        details: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            "status": "error",
            "error": {
                "type": error_type,
                "message": message,
                "code": code,
                "field": field,
                "details": details
            },
            "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "service": "maintenance"
        }
    
    @staticmethod
    def validation_error(
        message: str,
        field: str = None,
        correlation_id: str = None
    ) -> Dict[str, Any]:
        """Create validation error response"""
        return MaintenanceErrorBuilder.create_error_response(
            error_type=MaintenanceErrorTypes.VALIDATION_ERROR,
            message=message,
            field=field,
            correlation_id=correlation_id,
            code="VALIDATION_FAILED"
        )
    
    @staticmethod
    def authorization_error(
        message: str = "Insufficient permissions",
        correlation_id: str = None
    ) -> Dict[str, Any]:
        """Create authorization error response"""
        return MaintenanceErrorBuilder.create_error_response(
            error_type=MaintenanceErrorTypes.AUTHORIZATION_ERROR,
            message=message,
            correlation_id=correlation_id,
            code="INSUFFICIENT_PERMISSIONS"
        )
    
    @staticmethod
    def not_found_error(
        message: str,
        resource: str = None,
        correlation_id: str = None
    ) -> Dict[str, Any]:
        """Create not found error response"""
        details = {"resource": resource} if resource else None
        return MaintenanceErrorBuilder.create_error_response(
            error_type=MaintenanceErrorTypes.NOT_FOUND_ERROR,
            message=message,
            details=details,
            correlation_id=correlation_id,
            code="RESOURCE_NOT_FOUND"
        )
    
    @staticmethod
    def database_error(
        message: str = "Database operation failed",
        correlation_id: str = None
    ) -> Dict[str, Any]:
        """Create database error response"""
        return MaintenanceErrorBuilder.create_error_response(
            error_type=MaintenanceErrorTypes.DATABASE_ERROR,
            message=message,
            correlation_id=correlation_id,
            code="DATABASE_ERROR"
        )
    
    @staticmethod
    def service_unavailable_error(
        message: str = "Service temporarily unavailable",
        correlation_id: str = None
    ) -> Dict[str, Any]:
        """Create service unavailable error response"""
        return MaintenanceErrorBuilder.create_error_response(
            error_type=MaintenanceErrorTypes.SERVICE_UNAVAILABLE_ERROR,
            message=message,
            correlation_id=correlation_id,
            code="SERVICE_UNAVAILABLE"
        )
    
    @staticmethod
    def internal_error(
        message: str = "Internal server error",
        error_details: Dict[str, Any] = None,
        correlation_id: str = None
    ) -> Dict[str, Any]:
        """Create internal error response"""
        return MaintenanceErrorBuilder.create_error_response(
            error_type=MaintenanceErrorTypes.INTERNAL_ERROR,
            message=message,
            details=error_details,
            correlation_id=correlation_id,
            code="INTERNAL_ERROR"
        )
