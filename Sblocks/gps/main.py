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

# Import organized modules
from repositories.database import db_manager
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
                    logger.info("✅ Successfully registered with Core service discovery")
                    return True
                else:
                    logger.warning(f"⚠️ Service registration failed with status {response.status}")
                    return False
                    
    except Exception as e:
        logger.warning(f"⚠️ Failed to register with Core service discovery: {e}")
        logger.info("Service will continue without Core registration")
        return False

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("🚀 GPS Service Starting Up...")
    
    try:
        # Connect to database with error handling
        logger.info("🔗 Connecting to database...")
        try:
            await db_manager.connect()
            logger.info("✅ Database connected successfully")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise DatabaseConnectionError(f"Failed to connect to database: {e}")
        
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
            logger.error(f"❌ Event consumer setup error: {e}")
            consumer_connected = False
        
        # Setup and start service request consumer
        logger.info("🔗 Setting up service request consumer...")
        try:
            request_consumer_connected = await service_request_consumer.connect()
            if request_consumer_connected:
                # Start consuming service requests in background
                asyncio.create_task(service_request_consumer.start_consuming())
                logger.info("✅ Service request consumer started successfully")
            else:
                logger.warning("⚠️ Service request consumer connection failed - Core communication disabled")
        except Exception as e:
            logger.error(f"❌ Service request consumer setup error: {e}")
            request_consumer_connected = False
        
        # Publish service started event
        if publisher_connected:
            try:
                await event_publisher.publish_service_started(
                    version="1.0.0",
                    data={
                        "location_tracking": True,
                        "geofencing": True,
                        "places_management": True,
                        "features": [
                            "real_time_location_tracking", 
                            "location_history", 
                            "geofencing",
                            "places_management",
                            "map_provider_agnostic",
                            "leaflet_compatible"
                        ]
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to publish service started event: {e}")
        
        # Register with Core's service discovery
        await register_with_core_service()
        
        # Schedule background tasks
        asyncio.create_task(enhanced_background_tasks())
        
        logger.info("🎉 GPS Service Startup Completed Successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"💥 CRITICAL ERROR DURING STARTUP: {e}")
        raise
    
    finally:
        # Cleanup on shutdown
        logger.info("🔄 GPS Service Shutting Down...")
        try:
            await event_consumer.disconnect()
            await event_publisher.disconnect()
            await service_request_consumer.disconnect()
            await db_manager.disconnect()
            logger.info("✅ GPS Service shutdown completed")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

async def enhanced_background_tasks():
    """Enhanced background tasks for GPS service"""
    while True:
        try:
            # Cleanup old location history (keep last 90 days)
            await location_service.cleanup_old_locations()
            
            # Update geofence statistics
            await geofence_service.update_geofence_statistics()
            
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

# Include routers
app.include_router(locations_router, prefix="/api", tags=["locations"])
app.include_router(geofences_router, prefix="/api", tags=["geofences"])
app.include_router(places_router, prefix="/api", tags=["places"])
app.include_router(tracking_router, prefix="/api", tags=["tracking"])

@app.get("/health")
async def health_check():
    """Enhanced health check endpoint"""
    try:
        # Check database connection
        db_status = "healthy" if db_manager.is_connected() else "unhealthy"
        
        # Check RabbitMQ connections
        publisher_status = "healthy" if event_publisher.is_connected() else "unhealthy"
        consumer_status = "healthy" if event_consumer.is_connected() else "unhealthy"
        
        # Overall status
        overall_status = "healthy" if all([
            db_status == "healthy",
            publisher_status == "healthy",
            consumer_status == "healthy"
        ]) else "degraded"
        
        return {
            "status": overall_status,
            "service": "gps",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "database": db_status,
                "event_publisher": publisher_status,
                "event_consumer": consumer_status
            },
            "uptime_seconds": metrics_middleware.get_uptime_seconds()
        }
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "service": "gps",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

@app.get("/metrics")
async def get_metrics():
    """Get service metrics"""
    return {
        "service": "gps",
        "version": "1.0.0",
        "metrics": metrics_middleware.get_metrics()
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("GPS_PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
