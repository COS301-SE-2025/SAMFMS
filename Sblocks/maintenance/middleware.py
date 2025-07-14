"""
Enhanced middleware for Maintenance service
Following the same patterns as Management service
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any
import json

logger = logging.getLogger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware for adding request context and tracing"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID if not present
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        
        # Add request context to state
        request.state.request_id = request_id
        request.state.start_time = time.time()
        
        # Add request ID to response headers
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Enhanced middleware for comprehensive HTTP request/response logging"""
    
    def __init__(self, app, include_request_body: bool = False, include_response_body: bool = False):
        super().__init__(app)
        self.include_request_body = include_request_body
        self.include_response_body = include_response_body
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Extract request metadata
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Log the incoming request
        request_log = {
            "event": "request_start",
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_ip": client_ip,
            "user_agent": user_agent,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if self.include_request_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    request_log["request_body"] = body.decode("utf-8")
            except Exception as e:
                request_log["request_body_error"] = str(e)
        
        logger.info("Request started", extra=request_log)
        
        # Process the request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log the response
        response_log = {
            "event": "request_complete",
            "request_id": request_id,
            "status_code": response.status_code,
            "process_time": process_time,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Log level based on status code
        if response.status_code >= 500:
            logger.error("Request completed with server error", extra=response_log)
        elif response.status_code >= 400:
            logger.warning("Request completed with client error", extra=response_log)
        else:
            logger.info("Request completed successfully", extra=response_log)
        
        # Add processing time to response headers
        response.headers["X-Process-Time"] = str(process_time)
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        
        return response


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting request metrics"""
    
    def __init__(self, app):
        super().__init__(app)
        self.request_count = 0
        self.error_count = 0
        self.total_time = 0.0
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        # Update metrics
        process_time = time.time() - start_time
        self.request_count += 1
        self.total_time += process_time
        
        if response.status_code >= 400:
            self.error_count += 1
        
        # Add metrics to response headers for debugging
        response.headers["X-Request-Count"] = str(self.request_count)
        response.headers["X-Error-Count"] = str(self.error_count)
        response.headers["X-Average-Time"] = str(self.total_time / self.request_count)
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware"""
    
    def __init__(self, app, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.client_requests = {}
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Clean old entries (older than 1 minute)
        self.client_requests = {
            ip: times for ip, times in self.client_requests.items()
            if any(t > current_time - 60 for t in times)
        }
        
        # Check rate limit for this client
        if client_ip in self.client_requests:
            # Filter to last minute
            recent_requests = [
                t for t in self.client_requests[client_ip] 
                if t > current_time - 60
            ]
            
            if len(recent_requests) >= self.requests_per_minute:
                return Response(
                    content=json.dumps({
                        "success": False,
                        "message": "Rate limit exceeded",
                        "error_code": "RATE_LIMIT_EXCEEDED"
                    }),
                    status_code=429,
                    headers={"Content-Type": "application/json"}
                )
            
            self.client_requests[client_ip] = recent_requests + [current_time]
        else:
            self.client_requests[client_ip] = [current_time]
        
        return await call_next(request)


class HealthCheckMiddleware(BaseHTTPMiddleware):
    """Middleware for health check endpoints"""
    
    async def dispatch(self, request: Request, call_next):
        # Skip processing for health check endpoints
        if request.url.path in ["/health", "/metrics", "/", "/docs", "/redoc"]:
            return await call_next(request)
        
        # For other requests, add health status header
        response = await call_next(request)
        response.headers["X-Service-Health"] = "healthy"
        
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Centralized error handling middleware"""
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(
                f"Unhandled exception in maintenance service: {e}",
                extra={
                    "request_id": getattr(request.state, 'request_id', 'unknown'),
                    "path": request.url.path,
                    "method": request.method,
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            
            return Response(
                content=json.dumps({
                    "success": False,
                    "message": "Internal server error",
                    "error_code": "INTERNAL_ERROR",
                    "timestamp": datetime.utcnow().isoformat()
                }),
                status_code=500,
                headers={"Content-Type": "application/json"}
            )
