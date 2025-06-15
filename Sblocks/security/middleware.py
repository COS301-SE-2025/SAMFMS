# Backward compatibility - redirect to new structure
# This file provides backward compatibility for existing imports

from middleware.security_middleware import (
    LoggingMiddleware, SecurityHeadersMiddleware, RateLimitMiddleware
)

# Export all middleware for backward compatibility
__all__ = [
    "LoggingMiddleware",
    "SecurityHeadersMiddleware", 
    "RateLimitMiddleware"
]