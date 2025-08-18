"""
GPS Service main application with location tracking and geofencing capabilities
"""
import asyncio
import logging
import os
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse

# Import organized modules
from repositories.database import db_manager, db_manager_management
from events.publisher import event_publisher
from events.consumer import event_consumer, setup_event_handlers
from services.location_service import location_service
from services.geofence_service import geofence_service
from services.places_service import places_service
from services.request_consumer import service_request_consumer
from api.routes.locations import router as locations_router
from api.routes.geofences import router as geofences_router
from api.routes.places import router as places_router
from api.routes.tracking import router as tracking_router

# Import middleware and exception handlers
from middleware import (
    RequestContextMiddleware, LoggingMiddleware, SecurityHeadersMiddleware,
    MetricsMiddleware, RateLimitMiddleware, HealthCheckMiddleware
)
from api.exception_handlers import (
    EXCEPTION_HANDLERS, DatabaseConnectionError, EventPublishError, 
    BusinessLogicError
)
from schemas.responses import ResponseBuilder

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global metrics middleware instance for health checks
metrics_middleware = MetricsMiddleware(None)

async def register_with_core_service():
    """Register this service with Core's service discovery"""
    try:
        import aiohttp
        import json
        
        # Try to register with Core service discovery
        core_host = os.getenv("CORE_HOST", "core")
        core_port = int(os.getenv("CORE_PORT", "8000"))
        
        service_info = {
            "name": "gps",
            "host": os.getenv("GPS_HOST", "gps"),
            "port": int(os.getenv("GPS_PORT", "8000")),
            "version": "1.0.0",
            "protocol": "http",
            "health_check_url": "/health",
            "tags": ["gps", "location", "tracking", "geofencing", "places"],
            "metadata": {
                "features": [
                    "location_tracking",
                    "geofencing",
                    "places_management",
                    "location_history",
                    "real_time_tracking",
                    "map_provider_agnostic"
                ],
                "startup_time": datetime.utcnow().isoformat()
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"http://{core_host}:{core_port}/api/services/register",
                json=service_info,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    logger.info("Successfully registered with Core service discovery")
                    return True
                else:
                    logger.warning(f"Service registration failed with status {response.status}")
                    return False
                    
    except Exception as e:
        logger.warning(f"Failed to register with Core service discovery: {e}")
        logger.info("Service will continue without Core registration")
        return False

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("GPS Service Starting Up...")
    
    try:
        # Connect to database with error handling
        logger.info("Connecting to database...")
        try:
            await db_manager.connect()
            logger.info("Database connected successfully")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise DatabaseConnectionError(f"Failed to connect to database: {e}")
        
        # Start database for Management
        logger.info("Connecting to database Management...")
        try:
            await db_manager_management.connect()
            logger.info("Database Management connected successfully")
        except Exception as e:
            logger.error(f"Database Management connection failed: {e}")
            raise DatabaseConnectionError(f"Failed to connect to database Management: {e}")
        
        # Connect to RabbitMQ for event publishing
        logger.info("Connecting to RabbitMQ for event publishing...")
        try:
            publisher_connected = await event_publisher.connect()
            if publisher_connected:
                logger.info("Event publisher connected successfully")
            else:
                logger.warning("Event publisher connection failed - continuing without events")
        except Exception as e:
            logger.error(f"Event publisher connection error: {e}")
            publisher_connected = False
        
        # Setup and start event consumer
        logger.info("Setting up event consumer...")
        try:
            consumer_connected = await event_consumer.connect()
            if consumer_connected:
                await setup_event_handlers()
                # Start consuming in background
                asyncio.create_task(event_consumer.start_consuming())
                logger.info("Event consumer started successfully")
            else:
                logger.warning("Event consumer connection failed - continuing without event consumption")
        except Exception as e:
            logger.error(f"Event consumer setup error: {e}")
            consumer_connected = False
        
        # Setup and start service request consumer
        logger.info("Setting up service request consumer...")
        try:
            request_consumer_connected = await service_request_consumer.connect()
            if request_consumer_connected:
                # Start consuming service requests in background
                consumer_task = asyncio.create_task(service_request_consumer.start_consuming())
                # Keep reference to prevent garbage collection
                app.state.consumer_task = consumer_task
                logger.info("Service request consumer started successfully")
            else:
                logger.warning("Service request consumer connection failed - Core communication disabled")
        except Exception as e:
            logger.error(f"Service request consumer setup error: {e}")
        
        # Publish service started event with enhanced error handling
        if publisher_connected:
            try:
                await event_publisher.publish_service_started(
                    version="1.0.0",
                    data={
                        "service": "gps",
                        "event_driven": True,
                        "enhanced_features": [
                            "location_tracking", 
                            "geofencing", 
                            "places_management",
                            "real_time_tracking",
                            "location_history",
                            "event_driven_communication",
                            "comprehensive_monitoring"
                        ]
                    }
                )
                logger.info("Service started event published")
            except Exception as e:
                logger.warning(f"Failed to publish service started event: {e}")
        
        # Register with Core's service discovery
        await register_with_core_service()
        
        # Schedule background tasks with a delay to ensure database is ready
        async def start_background_tasks():
            await asyncio.sleep(5)  # Wait 5 seconds for database to stabilize
            await enhanced_background_tasks()
        
        asyncio.create_task(start_background_tasks())
        
        # Store start time for uptime calculation
        app.state.start_time = datetime.now(timezone.utc)
        metrics_middleware.app = app

        logger.info("GPS Service Startup Completed Successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"CRITICAL ERROR DURING STARTUP: {e}")
        raise
    
    finally:
        # Cleanup on shutdown
        logger.info("GPS Service Shutting Down...")
        try:
            # Publish service stopped event
            try:
                await event_publisher.publish_service_stopped(
                    version="1.0.0",
                    data={"reason": "graceful_shutdown"}
                )
                logger.info("Service stopped event published")
            except Exception as e:
                logger.warning(f"Failed to publish service stopped event: {e}")
            
            await event_consumer.disconnect()
            logger.info("Event consumer disconnected")
            
            await event_publisher.disconnect()
            logger.info("Event publisher disconnected")

            await service_request_consumer.stop_consuming()
            await service_request_consumer.disconnect()
            logger.info("Service request consumer stopped")

            await db_manager.disconnect()
            logger.info("Database disconnected")

            await db_manager_management.disconnect()
            logger.info("Management Database disconnected")

            logger.info("GPS Service shutdown completed")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

async def enhanced_background_tasks():
    """Enhanced background tasks for GPS service"""
    while True:
        try:
            # Check if database is connected before running tasks
            if not db_manager.is_connected():
                logger.warning("Database not connected, skipping background tasks")
                await asyncio.sleep(300)  # Wait 5 minutes before retry
                continue
                
            # Cleanup old location history (keep last 90 days)
            await location_service.cleanup_old_locations()
            
            # Validate active tracking sessions
            await location_service.validate_tracking_sessions()
            
            await asyncio.sleep(3600)  # Run every hour
            
        except Exception as e:
            logger.error(f"Background task error: {e}")
            await asyncio.sleep(300)  # Wait 5 minutes before retry

# Create FastAPI app
app = FastAPI(
    title="GPS Service",
    description="Location tracking, geofencing, and places management service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware in order
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestContextMiddleware)

# Add exception handlers
for exception_type, handler in EXCEPTION_HANDLERS.items():
    app.add_exception_handler(exception_type, handler)

# Include routers with enhanced error handling
app.include_router(locations_router, tags=["locations"])
app.include_router(geofences_router, tags=["geofences"])
app.include_router(places_router, tags=["places"])
app.include_router(tracking_router, tags=["tracking"])

@app.get("/")
async def root():
    """Enhanced service information endpoint"""
    uptime_seconds = (datetime.now(timezone.utc) - getattr(app.state, 'start_time', datetime.now(timezone.utc))).total_seconds()
    return ResponseBuilder.success(
        data={
            "service": "gps",
            "version": "1.0.0",
            "status": "operational",
            "uptime_seconds": uptime_seconds,
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        message="GPS Service is operational"
    ).model_dump()

@app.get("/health")
async def health_check():
    """Comprehensive health check with detailed component status"""
    try:
        # Check database
        db_healthy = False
        try:
            if db_manager.is_connected():
                await db_manager.health_check()
                db_healthy = True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")

        # Check RabbitMQ consumer
        rabbitmq_healthy = service_request_consumer.is_consuming

        # Check background tasks
        jobs_healthy = True  # Simplified for now

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
            "service": "gps",
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
    """GPS Service API Documentation"""
    return ResponseBuilder.success(
        data={
            "service": "SAMFMS GPS Service",
            "version": "1.0.0",
            "description": "Location Tracking, Geofencing, and Places Management for SAMFMS Fleet Management System",
            "base_url": "/gps",
            "endpoints": {
                "locations": {
                    "GET /locations": "List vehicle locations",
                    "GET /locations/vehicle/{vehicle_id}": "Get specific vehicle location",
                    "GET /locations/history": "Get location history",
                    "POST /locations": "Update vehicle location"
                },
                "geofences": {
                    "GET /geofences": "List geofences",
                    "GET /geofences/{id}": "Get specific geofence",
                    "POST /geofences": "Create geofence",
                    "PUT /geofences/{id}": "Update geofence",
                    "DELETE /geofences/{id}": "Delete geofence"
                },
                "places": {
                    "GET /places": "List places",
                    "GET /places/{id}": "Get specific place",
                    "GET /places/search": "Search places",
                    "POST /places": "Create place",
                    "PUT /places/{id}": "Update place",
                    "DELETE /places/{id}": "Delete place"
                },
                "tracking": {
                    "GET /tracking/live": "Real-time tracking",
                    "GET /tracking/route": "Vehicle route history",
                    "POST /tracking": "Start vehicle tracking"
                },
                "service_endpoints": {
                    "GET /": "Service information",
                    "GET /health": "Health check",
                    "GET /metrics": "Service metrics",
                    "GET /docs": "API documentation"
                }
            },
            "features": [
                "Real-time location tracking",
                "Location history management",
                "Geofence creation and monitoring",
                "Places and POI management",
                "Route tracking and analysis",
                "Event-driven communication",
                "Enhanced error handling"
            ]
        },
        message="GPS Service API documentation"
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
    port = int(os.getenv("GPS_PORT", "8000"))  # Use GPS_PORT from environment
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    logger.info(f"Starting GPS Service on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=os.getenv("ENVIRONMENT", "production") == "development"
    )
