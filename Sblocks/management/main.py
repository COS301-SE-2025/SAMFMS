"""
Reorganized main application with event-driven architecture
"""
import asyncio
import logging
import os
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import new organized modules
from repositories.database import db_manager
from events.publisher import event_publisher
from events.consumer import event_consumer, setup_event_handlers
from services.analytics_service import analytics_service
from api.routes.analytics import router as analytics_router
from api.routes.assignments import router as assignments_router
from api.routes.drivers import router as drivers_router
from middleware import LoggingMiddleware, SecurityHeadersMiddleware

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("🚀 Management Service Starting Up...")
    
    try:
        # Connect to database
        logger.info("🔗 Connecting to database...")
        await db_manager.connect()
        logger.info("✅ Database connected successfully")
        
        # Connect to RabbitMQ for event publishing
        logger.info("🔗 Connecting to RabbitMQ for event publishing...")
        publisher_connected = await event_publisher.connect()
        if publisher_connected:
            logger.info("✅ Event publisher connected successfully")
        else:
            logger.warning("⚠️ Event publisher connection failed - continuing without events")
        
        # Setup and start event consumer
        logger.info("🔗 Setting up event consumer...")
        consumer_connected = await event_consumer.connect()
        if consumer_connected:
            await setup_event_handlers()
            # Start consuming in background
            asyncio.create_task(event_consumer.start_consuming())
            logger.info("✅ Event consumer started successfully")
        else:
            logger.warning("⚠️ Event consumer connection failed - continuing without event consumption")
        
        # Publish service started event
        if publisher_connected:
            await event_publisher.publish_service_started(
                version="2.0.0",
                data={
                    "reorganized": True,
                    "event_driven": True,
                    "optimized": True,
                    "features": ["analytics_caching", "event_driven_communication", "repository_pattern"]
                }
            )
        
        # Schedule background tasks
        asyncio.create_task(background_tasks())
        
        logger.info("🎉 Management Service Startup Completed")
        
        yield
        
    except Exception as e:
        logger.error(f"💥 CRITICAL ERROR DURING STARTUP: {e}")
        raise
    
    finally:
        # Cleanup on shutdown
        logger.info("🛑 Management Service Shutting Down...")
        
        # Publish service stopped event
        try:
            if event_publisher.connection and not event_publisher.connection.is_closed:
                await event_publisher.publish_service_stopped(version="2.0.0")
        except Exception as e:
            logger.error(f"Error publishing shutdown event: {e}")
        
        # Close connections
        try:
            await event_publisher.disconnect()
            await event_consumer.disconnect()
            await db_manager.disconnect()
            logger.info("✅ All connections closed successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        
        logger.info("👋 Management Service Shutdown Completed")


async def background_tasks():
    """Background tasks for maintenance"""
    while True:
        try:
            # Clean up expired analytics cache every 10 minutes
            await asyncio.sleep(600)  # 10 minutes
            await analytics_service.cleanup_expired_cache()
            
            # Refresh critical analytics every 30 minutes
            await asyncio.sleep(1200)  # 20 more minutes = 30 total
            await analytics_service.get_fleet_utilization(use_cache=False)
            
        except Exception as e:
            logger.error(f"Error in background tasks: {e}")
            await asyncio.sleep(60)  # Wait 1 minute before retrying


# Create FastAPI application
app = FastAPI(
    title="Management Service",
    version="2.0.0",
    description="Reorganized Vehicle Management Service with Event-Driven Architecture",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(analytics_router, prefix="/api/v1", tags=["analytics"])
app.include_router(assignments_router, prefix="/api/v1", tags=["assignments"])
app.include_router(drivers_router, prefix="/api/v1", tags=["drivers"])


@app.get("/")
async def root():
    """Service information"""
    return {
        "service": "management",
        "version": "2.0.0",
        "status": "operational",
        "features": [
            "event_driven_architecture",
            "optimized_analytics_with_caching", 
            "repository_pattern",
            "clean_separation_of_concerns",
            "background_task_processing"
        ],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    try:
        # Check database
        db_healthy = await db_manager.health_check()
        
        # Check event publisher
        publisher_healthy = (
            event_publisher.connection is not None and 
            not event_publisher.connection.is_closed
        )
        
        # Check event consumer
        consumer_healthy = (
            event_consumer.connection is not None and 
            not event_consumer.connection.is_closed
        )
        
        overall_status = "healthy" if all([db_healthy, publisher_healthy, consumer_healthy]) else "degraded"
        
        return {
            "status": overall_status,
            "service": "management",
            "version": "2.0.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "components": {
                "database": "up" if db_healthy else "down",
                "event_publisher": "up" if publisher_healthy else "down", 
                "event_consumer": "up" if consumer_healthy else "down"
            }
        }
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "service": "management", 
            "version": "2.0.0",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@app.get("/info/events")
async def event_info():
    """Information about event system status"""
    return {
        "event_system": {
            "publisher_connected": (
                event_publisher.connection is not None and 
                not event_publisher.connection.is_closed
            ),
            "consumer_connected": (
                event_consumer.connection is not None and 
                not event_consumer.connection.is_closed
            ),
            "supported_events": [
                "assignment.created",
                "assignment.completed", 
                "trip.started",
                "trip.ended",
                "driver.created",
                "analytics.refreshed"
            ],
            "listening_for": [
                "vehicle.*",
                "user.*"
            ]
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_new:app", 
        host="0.0.0.0", 
        port=int(os.getenv("MANAGEMENT_PORT", "8000")),
        reload=True
    )
