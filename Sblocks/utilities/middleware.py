"""
Middleware for SAMFMS Utilities service
"""
import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"
        request_id = request.headers.get("X-Request-ID", "unknown")
        
        logger.info(f"Request started | {request.method} {request.url.path} | IP: {client_ip} | ID: {request_id}")
        
        try:
            response = await call_next(request)
            
            process_time = time.time() - start_time
            logger.info(
                f"Request completed | {request.method} {request.url.path} | "
                f"Status: {response.status_code} | Time: {process_time:.4f}s | "
                f"IP: {client_ip} | ID: {request_id}"
            )
            
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Request failed | {request.method} {request.url.path} | "
                f"Error: {str(e)} | Time: {process_time:.4f}s | "
                f"IP: {client_ip} | ID: {request_id}"
            )
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers to responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Pragma"] = "no-cache"
        
        return response
