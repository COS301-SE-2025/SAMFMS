"""
Middleware for Trip Planning service
"""
import time
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Add request context and correlation ID"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate correlation ID
        correlation_id = f"req_{int(time.time() * 1000)}_{id(request)}"
        request.state.correlation_id = correlation_id
        
        # Add correlation ID to response headers
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests and responses"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url} "
            f"- Client: {request.client.host if request.client else 'unknown'}"
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        logger.info(
            f"Response: {response.status_code} "
            f"- Duration: {duration:.3f}s "
            f"- Correlation: {getattr(request.state, 'correlation_id', 'unknown')}"
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
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response


class MetricsMiddleware(BaseHTTPMiddleware):
    """Collect request metrics"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.metrics = {
            "total_requests": 0,
            "total_errors": 0,
            "response_times": [],
            "status_codes": {},
            "endpoints": {},
            "start_time": datetime.utcnow()
        }
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Increment request counter
        self.metrics["total_requests"] += 1
        
        # Track endpoint
        endpoint = f"{request.method} {request.url.path}"
        if endpoint not in self.metrics["endpoints"]:
            self.metrics["endpoints"][endpoint] = {"count": 0, "avg_duration": 0}
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Update metrics
        self.metrics["response_times"].append(duration)
        
        # Keep only last 1000 response times for memory efficiency
        if len(self.metrics["response_times"]) > 1000:
            self.metrics["response_times"] = self.metrics["response_times"][-1000:]
        
        # Track status codes
        status_code = str(response.status_code)
        if status_code not in self.metrics["status_codes"]:
            self.metrics["status_codes"][status_code] = 0
        self.metrics["status_codes"][status_code] += 1
        
        # Track errors
        if response.status_code >= 400:
            self.metrics["total_errors"] += 1
        
        # Update endpoint metrics
        endpoint_metric = self.metrics["endpoints"][endpoint]
        endpoint_metric["count"] += 1
        endpoint_metric["avg_duration"] = (
            (endpoint_metric["avg_duration"] * (endpoint_metric["count"] - 1) + duration) /
            endpoint_metric["count"]
        )
        
        return response
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        response_times = self.metrics["response_times"]
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
        else:
            avg_response_time = max_response_time = min_response_time = 0
        
        uptime = (datetime.utcnow() - self.metrics["start_time"]).total_seconds()
        
        return {
            "total_requests": self.metrics["total_requests"],
            "total_errors": self.metrics["total_errors"],
            "error_rate": (
                self.metrics["total_errors"] / self.metrics["total_requests"] * 100
                if self.metrics["total_requests"] > 0 else 0
            ),
            "avg_response_time": avg_response_time,
            "max_response_time": max_response_time,
            "min_response_time": min_response_time,
            "uptime_seconds": uptime,
            "status_codes": self.metrics["status_codes"],
            "top_endpoints": sorted(
                self.metrics["endpoints"].items(),
                key=lambda x: x[1]["count"],
                reverse=True
            )[:10]
        }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware"""
    
    def __init__(self, app: ASGIApp, calls: int = 1000, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients: Dict[str, Dict[str, Any]] = {}
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/metrics"]:
            return await call_next(request)
        
        current_time = time.time()
        
        # Initialize client tracking
        if client_ip not in self.clients:
            self.clients[client_ip] = {
                "calls": [],
                "blocked_until": 0
            }
        
        client_data = self.clients[client_ip]
        
        # Check if client is currently blocked
        if current_time < client_data["blocked_until"]:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "retry_after": int(client_data["blocked_until"] - current_time)
                }
            )
        
        # Clean old calls
        client_data["calls"] = [
            call_time for call_time in client_data["calls"]
            if current_time - call_time < self.period
        ]
        
        # Check rate limit
        if len(client_data["calls"]) >= self.calls:
            client_data["blocked_until"] = current_time + self.period
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "retry_after": self.period
                }
            )
        
        # Record this call
        client_data["calls"].append(current_time)
        
        return await call_next(request)


class HealthCheckMiddleware(BaseHTTPMiddleware):
    """Add health check capabilities"""
    
    def __init__(self, app: ASGIApp, health_endpoint: str = "/health"):
        super().__init__(app)
        self.health_endpoint = health_endpoint
    
    async def dispatch(self, request: Request, call_next):
        # Quick health check response
        if request.url.path == self.health_endpoint and request.method == "HEAD":
            return Response(status_code=200)
        
        return await call_next(request)
