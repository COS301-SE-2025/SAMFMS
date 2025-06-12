# filepath: c:\Users\user\OneDrive\Documents\capstone\repo\SAMFMS\Sblocks\management\middleware.py
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import time
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log the incoming request
        logger.info(f"🔵 {request.method} {request.url} - Started")
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log the response
            logger.info(
                f"🟢 {request.method} {request.url} - "
                f"Status: {response.status_code} - "
                f"Time: {process_time:.3f}s"
            )
            
            # Add response time header
            response.headers["X-Process-Time"] = str(process_time)
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"🔴 {request.method} {request.url} - "
                f"Error: {str(e)} - "
                f"Time: {process_time:.3f}s"
            )
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response


class CORSMiddleware(BaseHTTPMiddleware):
    """Custom CORS middleware"""
    
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            response = Response()
        else:
            response = await call_next(request)
        
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        
        return response


class HealthCheckMiddleware(BaseHTTPMiddleware):
    """Middleware for health check monitoring"""
    
    async def dispatch(self, request: Request, call_next):
        # Add health check timestamp
        start_time = datetime.now(timezone.utc)
        
        response = await call_next(request)
        
        # Add health check headers
        response.headers["X-Service"] = "management"
        response.headers["X-Timestamp"] = start_time.isoformat()
        response.headers["X-Health-Status"] = "healthy"
        
        return response