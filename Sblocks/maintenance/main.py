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

# Import ResponseBuilder for standardized responses
from schemas.responses import ResponseBuilder

from repositories.database import db_manager
from events.publisher import event_publisher
from events.consumer import event_consumer, setup_event_handlers
from services.request_consumer import service_request_consumer
from services.background_jobs import background_jobs
from api.routes.maintenance_records import router as maintenance_records_router
from api.routes.licenses import router as licenses_router
from api.routes.analytics import router as analytics_router
from api.routes.notifications import router as notifications_router

from middleware import (
    RequestContextMiddleware, LoggingMiddleware, SecurityHeadersMiddleware,
    MetricsMiddleware, RateLimitMiddleware, HealthCheckMiddleware
)

# Global metrics middleware instance for health checks
metrics_middleware = MetricsMiddleware(None)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with event system support"""
    logger.info("🚀 Maintenance Service Starting Up...")
    
    try:
        # Connect to database with error handling
        logger.info("🔗 Connecting to database...")
        try:
            await db_manager.connect()
            await db_manager.create_indexes()
            logger.info("✅ Database connected successfully")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise Exception(f"Failed to connect to database: {e}")
        
        # Connect to RabbitMQ for event publishing
        logger.info("🔗 Connecting to RabbitMQ for event publishing...")
        try:
            publisher_connected = await event_publisher.connect()
            if publisher_connected:
                logger.info("✅ Event publisher connected successfully")
            else:
                logger.warning("⚠️ Event publisher connection failed - continuing without events")
        except Exception as e:
            logger.error(f"❌ Event publisher connection error: {e}")
            publisher_connected = False
        
        # Setup and start event consumer
        logger.info("🔗 Setting up event consumer...")
        try:
            consumer_connected = await event_consumer.connect()
            if consumer_connected:
                await setup_event_handlers()
                # Start consuming in background
                asyncio.create_task(event_consumer.start_consuming())
                logger.info("✅ Event consumer started successfully")
            else:
                logger.warning("⚠️ Event consumer connection failed - continuing without event consumption")
        except Exception as e:
            logger.error(f"❌ Event consumer setup failed: {e}")
            logger.warning("⚠️ Service will continue without event consumption")
        
        # Setup and start service request consumer
        logger.info("🔗 Setting up service request consumer...")
        try:
            request_consumer_connected = await service_request_consumer.connect()
            if request_consumer_connected:
                # Start consuming service requests in background
                consumer_task = asyncio.create_task(service_request_consumer.start_consuming())
                # Keep reference to prevent garbage collection
                app.state.consumer_task = consumer_task
                logger.info("✅ Service request consumer started successfully")
            else:
                logger.warning("⚠️ Service request consumer connection failed - Core communication disabled")
        except Exception as e:
            logger.error(f"❌ Service request consumer setup error: {e}")
        
        # Publish service started event with enhanced error handling
        if publisher_connected:
            try:
                await event_publisher.publish_service_started(
                    version="1.0.0",
                    data={
                        "service": "maintenance",
                        "event_driven": True,
                        "enhanced_features": [
                            "maintenance_records", 
                            "license_management", 
                            "notifications",
                            "analytics",
                            "event_driven_communication",
                            "comprehensive_monitoring"
                        ]
                    }
                )
                logger.info("✅ Service started event published")
            except Exception as e:
                logger.warning(f"Failed to publish service started event: {e}")
        
        # Start background jobs
        await background_jobs.start_background_jobs()
        logger.info("✅ Background jobs started")

        # Store start time for uptime calculation
        app.state.start_time = datetime.now(timezone.utc)
        metrics_middleware.app = app

        logger.info("🎉 Maintenance Service startup completed successfully")
    except Exception as e:
        logger.error(f"Failed to start Maintenance Service: {e}")
        raise

    yield

    logger.info("🛑 Maintenance Service Shutting Down...")
    try:
        # Publish service stopped event
        try:
            await event_publisher.publish_service_stopped(
                version="1.0.0",
                data={"reason": "graceful_shutdown"}
            )
            logger.info("✅ Service stopped event published")
        except Exception as e:
            logger.warning(f"Failed to publish service stopped event: {e}")
        
        await background_jobs.stop_background_jobs()
        logger.info("✅ Background jobs stopped")

        await event_consumer.disconnect()
        logger.info("✅ Event consumer disconnected")
        
        await event_publisher.disconnect()
        logger.info("✅ Event publisher disconnected")

        await service_request_consumer.stop_consuming()
        await service_request_consumer.disconnect()
        logger.info("✅ Service request consumer stopped")

        await db_manager.disconnect()
        logger.info("✅ Database disconnected")

        logger.info("👋 Maintenance Service shutdown completed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")



# Create FastAPI application with enhanced configuration
app = FastAPI(
    title="SAMFMS Maintenance Service",
    version="1.0.0",
    description="Comprehensive maintenance management service for SAMFMS fleet management system",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Store start time for uptime calculation
app.state.start_time = datetime.now(timezone.utc)
metrics_middleware.app = app


# Add enhanced middleware in correct order
app.add_middleware(RequestContextMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=120)
app.add_middleware(HealthCheckMiddleware)
app.add_middleware(LoggingMiddleware, include_request_body=False, include_response_body=False)
app.add_middleware(SecurityHeadersMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers with enhanced error handling
app.include_router(maintenance_records_router, tags=["maintenance_records"])
app.include_router(licenses_router, tags=["licenses"])
app.include_router(analytics_router, tags=["analytics"])
app.include_router(notifications_router, tags=["notifications"])



@app.get("/")
async def root():
    """Enhanced service information endpoint"""
    uptime_seconds = (datetime.now(timezone.utc) - getattr(app.state, 'start_time', datetime.now(timezone.utc))).total_seconds()
    return ResponseBuilder.success(
        data={
            "service": "maintenance",
            "version": "1.0.0",
            "status": "operational",
            "uptime_seconds": uptime_seconds,
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        message="Maintenance Service is operational"
    ).model_dump()



@app.get("/health")
async def health_check():
    """Comprehensive health check with detailed component status"""
    try:
        # Check database
        db_healthy = False
        try:
            if db_manager.database:
                await db_manager.database.command("ping")
                db_healthy = True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")

        # Check RabbitMQ consumer
        rabbitmq_healthy = service_request_consumer.is_consuming

        # Check background jobs
        jobs_healthy = getattr(background_jobs, 'is_running', False)

        # Overall status determination
        critical_components = [db_healthy]
        optional_components = [rabbitmq_healthy, jobs_healthy]

        if all(critical_components):
            if all(optional_components):
                overall_status = "healthy"
            else:
                overall_status = "degraded"
        else:
            overall_status = "unhealthy"

        uptime_seconds = (datetime.now(timezone.utc) - getattr(app.state, 'start_time', datetime.now(timezone.utc))).total_seconds()

        health_data = {
            "status": overall_status,
            "service": "maintenance",
            "version": "1.0.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": uptime_seconds,
            "components": {
                "database": {
                    "status": "up" if db_healthy else "down",
                    "critical": True
                },
                "rabbitmq_consumer": {
                    "status": "up" if rabbitmq_healthy else "down",
                    "critical": False,
                    "consuming": rabbitmq_healthy
                },
                "background_jobs": {
                    "status": "up" if jobs_healthy else "down",
                    "critical": False,
                    "running": jobs_healthy
                }
            }
        }

        return ResponseBuilder.success(
            data=health_data,
            message=f"Service is {overall_status}"
        ).model_dump()

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return ResponseBuilder.error(
            error="HealthCheckError",
            message="Health check failed",
            details={"error": str(e)}
        ).model_dump()



@app.get("/metrics")
async def get_service_metrics():
    """Get service performance metrics"""
    try:
        metrics = metrics_middleware.get_metrics()
        return ResponseBuilder.success(
            data=metrics,
            message="Service metrics retrieved successfully"
        ).model_dump()
    except Exception as e:
        logger.error(f"Metrics collection error: {e}")
        return ResponseBuilder.error(
            error="MetricsError",
            message="Failed to collect metrics",
            details={"error": str(e)}
        ).model_dump()


@app.get("/docs")
async def api_documentation():
    """Maintenance Service API Documentation"""
    return ResponseBuilder.success(
        data={
            "service": "SAMFMS Maintenance Service",
            "version": "1.0.0",
            "description": "Maintenance Records, License Management, and Analytics for SAMFMS Fleet Management System", 
            "base_url": "/maintenance",
            "endpoints": {
                "maintenance_records": {
                    "GET /records": "List maintenance records",
                    "GET /records/{id}": "Get specific record",
                    "POST /records": "Create maintenance record",
                    "PUT /records/{id}": "Update record",
                    "DELETE /records/{id}": "Delete record",
                    "GET /records/vehicle/{vehicle_id}": "Get records for vehicle"
                },
                "license_management": {
                    "GET /licenses": "List licenses",
                    "GET /licenses/{id}": "Get specific license",
                    "POST /licenses": "Create license",
                    "PUT /licenses/{id}": "Update license", 
                    "DELETE /licenses/{id}": "Delete license",
                    "GET /licenses/expiring": "Get expiring licenses"
                },
                "maintenance_analytics": {
                    "GET /analytics": "General maintenance analytics",
                    "GET /analytics/vehicle/{vehicle_id}": "Vehicle-specific analytics",
                    "GET /analytics/costs": "Cost analysis",
                    "GET /analytics/trends": "Maintenance trends"
                },
                "notifications": {
                    "GET /notifications": "List notifications",
                    "POST /notifications": "Create notification",
                    "PUT /notifications/{id}": "Update notification"
                },
                "service_endpoints": {
                    "GET /": "Service information",
                    "GET /health": "Health check", 
                    "GET /metrics": "Service metrics",
                    "GET /docs": "API documentation"
                }
            },
            "features": [
                "Comprehensive maintenance tracking",
                "License expiration monitoring",
                "Cost analysis and reporting",
                "Automated notifications",
                "Background job processing",
                "Enhanced error handling"
            ]
        },
        message="Maintenance Service API documentation"
    ).model_dump()



# Exception handlers using ResponseBuilder for consistency
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error for {request.url}: {exc}")
    return JSONResponse(
        status_code=422,
        content=ResponseBuilder.error(
            error="ValidationError",
            message="Validation error",
            details=exc.errors()
        ).model_dump()
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.warning(f"HTTP error {exc.status_code} for {request.url}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content=ResponseBuilder.error(
            error=f"HTTP_{exc.status_code}",
            message=exc.detail
        ).model_dump()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error for {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ResponseBuilder.error(
            error="INTERNAL_ERROR",
            message="Internal server error"
        ).model_dump()
    )


if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("MAINTENANCE_PORT", "8000"))  # Use MAINTENANCE_PORT from environment
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    logger.info(f"Starting Maintenance Service on {host}:{port}")
    
    # Start services manually before running uvicorn
    from startup import initialize_services
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(initialize_services())
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        exit(1)
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=os.getenv("ENVIRONMENT", "production") == "development"
    )