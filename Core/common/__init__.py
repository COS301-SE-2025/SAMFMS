"""
Common utilities and shared components for SAMFMS Core Service
"""

from .exceptions import (
    SAMFMSError,
    ValidationError,
    DatabaseError,
    AuthenticationError,
    AuthorizationError,
    ServiceUnavailableError,
    ResourceNotFoundError,
    ServiceTimeoutError,
    MessageQueueError,
    PluginError,
    CorrelationIdMiddleware,
    ComprehensiveErrorHandlingMiddleware,
    ErrorResponseBuilder,
    create_error_handler,
    log_error_with_context
)

from .service_discovery import (
    ServiceDiscovery,
    ServiceInfo,
    ServiceStatus,
    get_service_discovery,
    shutdown_service_discovery,
    register_service,
    discover_service,
    call_service
)

__all__ = [
    # Exceptions
    'SAMFMSError',
    'ValidationError', 
    'DatabaseError',
    'AuthenticationError',
    'AuthorizationError',
    'ServiceUnavailableError',
    'ResourceNotFoundError',
    'ServiceTimeoutError',
    'MessageQueueError',
    'PluginError',
    'CorrelationIdMiddleware',
    'ComprehensiveErrorHandlingMiddleware',
    'ErrorResponseBuilder',
    'create_error_handler',
    'log_error_with_context',
    
    # Service Discovery
    'ServiceDiscovery',
    'ServiceInfo',
    'ServiceStatus',
    'get_service_discovery',
    'shutdown_service_discovery',
    'register_service',
    'discover_service',
    'call_service'
]
