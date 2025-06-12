import logging
import time
from fastapi import Request, Response, HTTPException
import requests
import os
# Use Starlette BaseHTTPMiddleware directly since FastAPI version might be outdated
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(f"🔵 {request.method} {request.url.path} - Started")
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log response
            logger.info(f"🟢 {request.method} {request.url.path} - {response.status_code} - {process_time:.4f}s")
            
            # Add response headers
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"🔴 {request.method} {request.url.path} - ERROR - {process_time:.4f}s - {str(e)}")
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers to responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response


class CORSMiddleware(BaseHTTPMiddleware):
    """Middleware for handling CORS"""
    
    def __init__(self, app, allow_origins=None, allow_methods=None, allow_headers=None):
        super().__init__(app)
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allow_headers = allow_headers or ["*"]
    
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            response = Response()
        else:
            response = await call_next(request)
        
        # Add CORS headers
        response.headers["Access-Control-Allow-Origin"] = ", ".join(self.allow_origins)
        response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
        response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)
        response.headers["Access-Control-Max-Age"] = "3600"
        
        return response


class HealthCheckMiddleware(BaseHTTPMiddleware):
    """Middleware for handling health checks"""
    
    async def dispatch(self, request: Request, call_next):
        # Quick health check bypass
        if request.url.path in ["/health", "/ping", "/"]:
            start_time = time.time()
            response = await call_next(request)
            process_time = time.time() - start_time
            response.headers["X-Health-Check-Time"] = str(process_time)
            return response
        
        return await call_next(request)


# Define the URL for the Security Sblock
SECURITY_URL = os.getenv("SECURITY_URL", "http://security_service:8000")

class SecurityServiceMiddleware:
    """Middleware to check if the Security service is available"""
    
    def __init__(self):
        self.security_service_available = False
        self.last_check_time = 0
        self.check_interval = 30  # seconds between availability checks
    
    async def __call__(self, request: Request, call_next):
        # Only check auth endpoints
        if request.url.path.startswith("/auth"):
            current_time = time.time()
            
            # Only check availability periodically to avoid constant checks
            if current_time - self.last_check_time > self.check_interval or not self.security_service_available:
                self.last_check_time = current_time
                try:
                    # Simple health check to the security service
                    response = requests.get(f"{SECURITY_URL}/health", timeout=2)
                    if response.status_code == 200:
                        self.security_service_available = True
                        logger.info("Security service is available")
                    else:
                        self.security_service_available = False
                        logger.warning(f"Security service returned status code: {response.status_code}")
                except requests.RequestException as e:
                    self.security_service_available = False
                    logger.warning(f"Security service is not available: {e}")
            
            if not self.security_service_available:
                return HTTPException(
                    status_code=503,
                    detail="Authentication service is currently unavailable. Please try again later."
                )
        
        # Continue processing the request
        response = await call_next(request)
        return response