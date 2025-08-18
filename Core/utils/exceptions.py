"""
Custom exceptions for SAMFMS Core service
"""

class SAMFMSBaseException(Exception):
    """Base exception for SAMFMS Core service"""
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class ServiceUnavailableError(SAMFMSBaseException):
    """Raised when a service is unavailable"""
    def __init__(self, service_name: str, message: str = None):
        self.service_name = service_name
        message = message or f"Service {service_name} is unavailable"
        super().__init__(message, "SERVICE_UNAVAILABLE")

class AuthorizationError(SAMFMSBaseException):
    """Raised when authorization fails"""
    def __init__(self, message: str = "Authorization failed"):
        super().__init__(message, "AUTHORIZATION_FAILED")

class ValidationError(SAMFMSBaseException):
    """Raised when request validation fails"""
    def __init__(self, message: str = "Request validation failed"):
        super().__init__(message, "VALIDATION_ERROR")

class ServiceTimeoutError(SAMFMSBaseException):
    """Raised when service request times out"""
    def __init__(self, service_name: str, timeout: int):
        self.service_name = service_name
        self.timeout = timeout
        message = f"Service {service_name} timed out after {timeout} seconds"
        super().__init__(message, "SERVICE_TIMEOUT")

class ConfigurationError(SAMFMSBaseException):
    """Raised when configuration is invalid"""
    def __init__(self, message: str = "Configuration error"):
        super().__init__(message, "CONFIGURATION_ERROR")

class DatabaseError(SAMFMSBaseException):
    """Raised when database operations fail"""
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message, "DATABASE_ERROR")

class MessageQueueError(SAMFMSBaseException):
    """Raised when message queue operations fail"""
    def __init__(self, message: str = "Message queue operation failed"):
        super().__init__(message, "MESSAGE_QUEUE_ERROR")

class PluginError(SAMFMSBaseException):
    """Raised when plugin operations fail"""
    def __init__(self, plugin_id: str, operation: str, message: str = None):
        self.plugin_id = plugin_id
        self.operation = operation
        message = message or f"Plugin {plugin_id} failed during {operation}"
        super().__init__(message, "PLUGIN_ERROR")
