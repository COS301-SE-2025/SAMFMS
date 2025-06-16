# Backward compatibility - redirect to new structure
# This file provides backward compatibility for existing imports

from middleware.logging_middleware import LoggingMiddleware
from middleware.security_middleware import SecurityHeadersMiddleware, CORSMiddleware

# Export all middleware for backward compatibility
__all__ = [
    "LoggingMiddleware",
    "SecurityHeadersMiddleware", 
    "CORSMiddleware"
]