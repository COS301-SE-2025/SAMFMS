"""
Middleware module for GPS Service.
Provides request/response logging, performance monitoring, and error tracking.
"""

import time
import traceback
from fastapi import Request, Response
from logging_config import get_logger

logger = get_logger(__name__)


class LoggingMiddleware:
    """HTTP middleware for request/response logging and performance monitoring."""
    
    @staticmethod
    async def logging_middleware(request: Request, call_next):
        """
        Middleware function for logging HTTP requests and responses.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in the chain
            
        Returns:
            HTTP response with added logging
        """
        start_time = time.time()
        request_id = f"req_{int(time.time() * 1000)}_{id(request)}"
        
        # Log incoming request
        logger.info(
            "Incoming request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "query_params": str(request.query_params) if request.query_params else None,
                "user_agent": request.headers.get("user-agent"),
                "remote_addr": request.client.host if request.client else None,
                "content_type": request.headers.get("content-type"),
                "content_length": request.headers.get("content-length")
            }
        )
        
        try:
            # Process request
            response = await call_next(request)
            duration_ms = round((time.time() - start_time) * 1000, 2)
            
            # Log successful response
            logger.info(
                "Request completed successfully",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "method": request.method,
                    "url": str(request.url),
                    "path": request.url.path,
                    "response_size": response.headers.get("content-length")
                }
            )
            
            # Performance monitoring
            LoggingMiddleware._check_performance(request_id, duration_ms, request.url.path)
            
            return response
            
        except Exception as e:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            
            # Log failed request
            logger.error(
                "Request failed with exception",
                extra={
                    "request_id": request_id,
                    "duration_ms": duration_ms,
                    "method": request.method,
                    "url": str(request.url),
                    "path": request.url.path,
                    "exception": str(e),
                    "exception_type": type(e).__name__,
                    "traceback": traceback.format_exc()
                }
            )
            
            # Re-raise the exception to be handled by FastAPI
            raise
    
    @staticmethod
    def _check_performance(request_id: str, duration_ms: float, path: str):
        """
        Check request performance and log warnings for slow requests.
        
        Args:
            request_id: Unique request identifier
            duration_ms: Request duration in milliseconds
            path: Request path
        """
        # Define performance thresholds
        thresholds = {
            "/health": 100,    # Health checks should be very fast
            "/metrics": 200,   # Metrics can be slightly slower
            "default": 1000    # Default threshold for other endpoints
        }
        
        threshold = thresholds.get(path, thresholds["default"])
        
        if duration_ms > threshold:
            severity = "warning" if duration_ms < threshold * 2 else "error"
            
            if severity == "warning":
                logger.warning(
                    "Slow request detected",
                    extra={
                        "request_id": request_id,
                        "duration_ms": duration_ms,
                        "threshold_ms": threshold,
                        "path": path,
                        "performance_category": "slow"
                    }
                )
            else:
                logger.error(
                    "Very slow request detected",
                    extra={
                        "request_id": request_id,
                        "duration_ms": duration_ms,
                        "threshold_ms": threshold,
                        "path": path,
                        "performance_category": "very_slow"
                    }
                )


class SecurityMiddleware:
    """Security-related middleware for headers and request validation."""
    
    @staticmethod
    async def security_headers_middleware(request: Request, call_next):
        """
        Add security headers to responses.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in the chain
            
        Returns:
            HTTP response with security headers
        """
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response


# Convenience function to get the logging middleware
def get_logging_middleware():
    """Get the logging middleware function."""
    return LoggingMiddleware.logging_middleware


def get_security_middleware():
    """Get the security middleware function."""
    return SecurityMiddleware.security_headers_middleware
