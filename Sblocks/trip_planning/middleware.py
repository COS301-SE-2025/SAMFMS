"""
Middleware for GPS service
"""
import time
import logging
import uuid
from typing import Dict, Any
from datetime import datetime
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Add request context and correlation ID"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate correlation ID if not present
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        request.state.correlation_id = correlation_id
        
        # Add request ID if not present
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        
        response = await call_next(request)
        
        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Request-ID"] = request_id
        
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Request/response logging middleware"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"- IP: {request.client.host if request.client else 'unknown'} "
            f"- User-Agent: {request.headers.get('user-agent', 'unknown')}"
        )
        
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        logger.info(
            f"Response: {request.method} {request.url.path} "
            f"- Status: {response.status_code} "
            f"- Duration: {duration:.3f}s"
        )
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response


class MetricsMiddleware(BaseHTTPMiddleware):
    """Collect metrics middleware"""
    
    def __init__(self, app):
        super().__init__(app)
        self.start_time = datetime.utcnow()
        self.request_count = 0
        self.error_count = 0
        self.response_times = []
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        self.request_count += 1
        
        response = await call_next(request)
        
        # Calculate response time
        response_time = time.time() - start_time
        self.response_times.append(response_time)
        
        # Keep only last 1000 response times
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]
        
        # Count errors
        if response.status_code >= 400:
            self.error_count += 1
        
        # Add response time header
        response.headers["X-Response-Time"] = f"{response_time:.3f}s"
        
        return response
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        
        return {
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "request_count": self.request_count,
            "error_count": self.error_count,
            "error_rate": self.error_count / self.request_count if self.request_count > 0 else 0,
            "average_response_time": avg_response_time,
            "requests_per_second": self.request_count / (datetime.utcnow() - self.start_time).total_seconds()
        }
    
    def get_uptime_seconds(self) -> float:
        """Get uptime in seconds"""
        return (datetime.utcnow() - self.start_time).total_seconds()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = {}
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Clean old requests
        if client_ip in self.requests:
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if current_time - req_time < 60  # Keep requests from last minute
            ]
        else:
            self.requests[client_ip] = []
        
        # Check rate limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={
                    "status": "error",
                    "error": "rate_limit_exceeded",
                    "message": f"Rate limit exceeded. Maximum {self.requests_per_minute} requests per minute."
                }
            )
        
        # Add current request
        self.requests[client_ip].append(current_time)
        
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = max(0, self.requests_per_minute - len(self.requests[client_ip]))
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(current_time + 60))
        
        return response


class HealthCheckMiddleware(BaseHTTPMiddleware):
    """Health check bypass middleware"""
    
    async def dispatch(self, request: Request, call_next):
        # Skip other middleware for health checks
        if request.url.path in ["/health", "/metrics"]:
            return await call_next(request)
        
        return await call_next(request)
