"""
Common utilities and shared dependencies for API routes
"""

# Re-export everything from base for backward compatibility
from .base import (
    security,
    handle_service_request,
    validate_required_fields,
    authorize_and_route,
    ServiceProxyError,
    logger
)

__all__ = [
    "security",
    "handle_service_request", 
    "validate_required_fields",
    "authorize_and_route",
    "ServiceProxyError",
    "logger"
]
