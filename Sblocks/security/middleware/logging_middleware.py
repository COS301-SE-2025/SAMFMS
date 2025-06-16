from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import uuid
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Start timing
        start_time = time.time()
        
        # Get client info
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Log incoming request
        logger.info(
            f"Incoming request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "ip_address": client_ip,
                "user_agent": user_agent,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"Request completed",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "process_time_ms": round(process_time * 1000, 2),
                    "ip_address": client_ip,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            )
            
            # Add response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
            
            return response
            
        except Exception as e:
            # Log error
            process_time = time.time() - start_time
            logger.error(
                f"Request failed",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "process_time_ms": round(process_time * 1000, 2),
                    "ip_address": client_ip,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            )
            raise
