"""
Enhanced main application for Maintenance Service
Following the same patterns as Management service
"""

import asyncio
import logging
import os
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

# Import organized modules
from repositories.database import db_manager
from services.request_consumer import maintenance_service_request_consumer
from api.routes.maintenance_records import router as maintenance_records_router
from api.routes.licenses import router as licenses_router
from api.routes.analytics import router as analytics_router
from api.routes.notifications import router as notifications_router

# Import middleware and exception handlers
from middleware import (
    RequestContextMiddleware, LoggingMiddleware, SecurityHeadersMiddleware,
    MetricsMiddleware, RateLimitMiddleware, HealthCheckMiddleware
)

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Maintenance Service...")
    
    try:
        # Initialize database
        await db_manager.connect()
        await db_manager.create_indexes()
        logger.info("Database connected and indexes created")
        
        # Start RabbitMQ consumer
        await maintenance_service_request_consumer.start_consuming()
        logger.info("RabbitMQ consumer started")
        
        logger.info("Maintenance Service startup completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to start Maintenance Service: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Maintenance Service...")
    
    try:
        # Stop RabbitMQ consumer
        await maintenance_service_request_consumer.stop_consuming()
        await maintenance_service_request_consumer.disconnect()
        logger.info("RabbitMQ consumer stopped")
        
        # Disconnect database
        await db_manager.disconnect()
        logger.info("Database disconnected")
        
        logger.info("Maintenance Service shutdown completed")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title="SAMFMS Maintenance Service",
    description="Comprehensive maintenance management service for SAMFMS fleet management system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on environment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(HealthCheckMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(RateLimitMiddleware)

# Include API routers
app.include_router(maintenance_records_router)
app.include_router(licenses_router)
app.include_router(analytics_router)
app.include_router(notifications_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "maintenance",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        db_status = "healthy"
        try:
            if db_manager.database:
                await db_manager.database.command("ping")
            else:
                db_status = "disconnected"
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"
        
        # Check RabbitMQ connection
        rabbitmq_status = "healthy" if maintenance_service_request_consumer.is_consuming else "not consuming"
        
        health_data = {
            "service": "maintenance",
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "dependencies": {
                "database": db_status,
                "rabbitmq": rabbitmq_status
            }
        }
        
        # Determine overall status
        if db_status != "healthy" or rabbitmq_status != "healthy":
            health_data["status"] = "degraded"
            
        return health_data
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "service": "maintenance",
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@app.get("/metrics")
async def get_metrics():
    """Service metrics endpoint"""
    try:
        # Get basic service metrics
        uptime = datetime.utcnow() - app.state.start_time if hasattr(app.state, 'start_time') else None
        
        metrics = {
            "service": "maintenance",
            "uptime_seconds": uptime.total_seconds() if uptime else 0,
            "timestamp": datetime.utcnow().isoformat(),
            "database_status": "connected" if db_manager.database else "disconnected",
            "rabbitmq_status": "consuming" if maintenance_service_request_consumer.is_consuming else "not consuming"
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error retrieving metrics: {e}")
        return {"error": "Failed to retrieve metrics"}


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    logger.warning(f"Validation error for {request.url}: {exc}")
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "Validation error",
            "details": exc.errors(),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions"""
    logger.warning(f"HTTP error {exc.status_code} for {request.url}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "error_code": f"HTTP_{exc.status_code}",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled error for {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "error_code": "INTERNAL_ERROR", 
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Store start time for uptime calculation
@app.on_event("startup")
async def store_start_time():
    """Store application start time"""
    app.state.start_time = datetime.utcnow()


if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("MAINTENANCE_PORT", "8000"))  # Use MAINTENANCE_PORT from environment
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    logger.info(f"Starting Maintenance Service on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=os.getenv("ENVIRONMENT", "production") == "development"
    )
