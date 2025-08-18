# filepath: c:\Users\user\OneDrive\Documents\capstone\repo\SAMFMS\Sblocks\management\middleware.py
# Enhanced middleware for Management service
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
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Optionally include request body (be careful with sensitive data)
        if self.include_request_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                # Note: This reads the body, which can only be done once
                body = await request.body()
                if body:
                    request_log["body_size"] = len(body)
                    # Only log if it's JSON and not too large
                    if len(body) < 1024:
                        try:
                            request_log["body"] = json.loads(body.decode())
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            request_log["body"] = "non-json-content"
            except Exception as e:
                logger.warning(f"Failed to read request body: {e}")
        
        logger.info(f"🔵 Request started", extra=request_log)
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log the response
            response_log = {
                "event": "request_complete",
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "status_code": response.status_code,
                "process_time_seconds": round(process_time, 3),
                "response_size": response.headers.get("content-length"),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Determine log level based on status code
            if response.status_code >= 500:
                logger.error(f"🔴 Request failed", extra=response_log)
            elif response.status_code >= 400:
                logger.warning(f"🟡 Request error", extra=response_log)
            else:
                logger.info(f"🟢 Request completed", extra=response_log)
            
            # Add performance headers
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Response-Time"] = str(int(process_time * 1000))  # milliseconds
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            error_log = {
                "event": "request_error",
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "error": str(e),
                "error_type": type(e).__name__,
                "process_time_seconds": round(process_time, 3),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            logger.error(f"💥 Request exception", extra=error_log)
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enhanced middleware for security headers with configurable options"""
    
    def __init__(self, app, enable_hsts: bool = True, hsts_max_age: int = 31536000):
        super().__init__(app)
        self.enable_hsts = enable_hsts
        self.hsts_max_age = hsts_max_age
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Essential security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        
        # HSTS (only for HTTPS)
        if self.enable_hsts and request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = f"max-age={self.hsts_max_age}; includeSubDomains"
        
        # Content Security Policy (with Swagger UI support)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://cdn.jsdelivr.net; "
            "connect-src 'self'"
        )
        
        return response


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting API metrics"""
    
    def __init__(self, app):
        super().__init__(app)
        self.request_count = {}
        self.response_times = {}
        self.error_count = {}
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        endpoint = f"{request.method}:{request.url.path}"
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            # Update metrics
            self._update_metrics(endpoint, response.status_code, duration)
            
            # Add metrics headers
            response.headers["X-Endpoint"] = endpoint
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            self._update_error_metrics(endpoint, str(e))
            raise
    
    def _update_metrics(self, endpoint: str, status_code: int, duration: float):
        """Update request metrics"""
        # Request count
        if endpoint not in self.request_count:
            self.request_count[endpoint] = {"total": 0, "by_status": {}}
        
        self.request_count[endpoint]["total"] += 1
        status_str = str(status_code)
        if status_str not in self.request_count[endpoint]["by_status"]:
            self.request_count[endpoint]["by_status"][status_str] = 0
        self.request_count[endpoint]["by_status"][status_str] += 1
        
        # Response times
        if endpoint not in self.response_times:
            self.response_times[endpoint] = []
        self.response_times[endpoint].append(duration)
        
        # Keep only last 100 response times
        if len(self.response_times[endpoint]) > 100:
            self.response_times[endpoint] = self.response_times[endpoint][-100:]
    
    def _update_error_metrics(self, endpoint: str, error: str):
        """Update error metrics"""
        if endpoint not in self.error_count:
            self.error_count[endpoint] = {}
        
        if error not in self.error_count[endpoint]:
            self.error_count[endpoint][error] = 0
        self.error_count[endpoint][error] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics summary"""
        metrics = {
            "request_counts": self.request_count,
            "error_counts": self.error_count,
            "response_time_stats": {}
        }
        
        # Calculate response time statistics
        for endpoint, times in self.response_times.items():
            if times:
                metrics["response_time_stats"][endpoint] = {
                    "count": len(times),
                    "avg": sum(times) / len(times),
                    "min": min(times),
                    "max": max(times),
                    "p95": sorted(times)[int(len(times) * 0.95)] if len(times) > 0 else 0
                }
        
        return metrics


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.client_requests = {}
        self.window_start = time.time()
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Reset window if needed (1 minute windows)
        if current_time - self.window_start > 60:
            self.client_requests = {}
            self.window_start = current_time
        
        # Check rate limit
        if client_ip not in self.client_requests:
            self.client_requests[client_ip] = 0
        
        if self.client_requests[client_ip] >= self.requests_per_minute:
            # Rate limit exceeded
            logger.warning(f"Rate limit exceeded for client {client_ip}")
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={
                    "error": "RateLimitExceeded",
                    "message": f"Rate limit of {self.requests_per_minute} requests per minute exceeded"
                },
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0"
                }
            )
        
        # Increment counter
        self.client_requests[client_ip] += 1
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = self.requests_per_minute - self.client_requests[client_ip]
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response


class HealthCheckMiddleware(BaseHTTPMiddleware):
    """Middleware for basic health monitoring"""
    
    def __init__(self, app):
        super().__init__(app)
        self.start_time = datetime.now(timezone.utc)
        self.healthy = True
        self.last_health_check = None
    
    async def dispatch(self, request: Request, call_next):
        # Add health status to state
        request.state.service_healthy = self.healthy
        request.state.service_uptime = (datetime.now(timezone.utc) - self.start_time).total_seconds()
        
        try:
            response = await call_next(request)
            
            # Update health status based on response
            if response.status_code >= 500:
                self.healthy = False
                logger.warning("Service health degraded due to 5xx response")
            
            # Add health headers
            response.headers["X-Service-Health"] = "healthy" if self.healthy else "degraded"
            response.headers["X-Service-Uptime"] = str(int(request.state.service_uptime))
            
            return response
            
        except Exception as e:
            self.healthy = False
            logger.error(f"Service health degraded due to exception: {e}")
            raise
        start_time = datetime.now(timezone.utc)
        
        response = await call_next(request)
        
        # Add health check headers
        response.headers["X-Service"] = "management"
        response.headers["X-Timestamp"] = start_time.isoformat()
        response.headers["X-Health-Status"] = "healthy"
        
        return response