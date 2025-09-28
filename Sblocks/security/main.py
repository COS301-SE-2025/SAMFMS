from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import redis
import pika
import os
from routes import auth_router, user_router, admin_router
from config.database import test_database_connection, create_indexes, cleanup_expired_sessions
from message_queue import mq_service
from logging_config import setup_logging, get_logger
from middleware import LoggingMiddleware, SecurityHeadersMiddleware
from health_metrics import health_check, metrics_endpoint
from config.settings import settings

# Setup structured logging
setup_logging()
logger = get_logger(__name__)

# Path for profile pictures and static files
PROFILE_PICTURES_DIR = os.path.join(os.getcwd(), "profile_pictures")
STATIC_DIR = os.path.join(os.getcwd(), "static")
os.makedirs(PROFILE_PICTURES_DIR, exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "profile_pictures"), exist_ok=True)


# Application lifespan events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events."""
    # Startup
    logger.info("🔐 Security service starting up...")
    
    # Test database connection
    await test_database_connection()
    
    # Create database indexes
    await create_indexes()
      # Test Redis connection
    try:
        redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)
        redis_client.ping()
        logger.info("✅ Successfully connected to Redis")
    except Exception as e:
        logger.error(f"❌ Failed to connect to Redis: {e}")
      # Connect to RabbitMQ
    if mq_service.connect():
        logger.info("✅ Successfully connected to RabbitMQ")
        
        # Publish service status (will be consumed by Core)
        mq_service.publish_service_status("up")
        logger.info("📤 Published service startup message to Core")
    else:
        logger.error("❌ Failed to connect to RabbitMQ")
    
    # Start periodic cleanup task
    import asyncio
    asyncio.create_task(periodic_cleanup())
    
    logger.info("✅ Security service startup completed")
    
    yield
    
    # Shutdown
    logger.info("🛑 Security service shutting down...")
    mq_service.close()
    logger.info("✅ Security service shutdown completed")
    #publish_message("service_presence", aio_pika.ExchangeType.FANOUT, {"type": "service_presence", "service":"security"}, "")



async def periodic_cleanup():
    """Periodic cleanup of expired sessions"""
    import asyncio
    while True:
        try:
            await asyncio.sleep(3600)  # Run every hour
            await cleanup_expired_sessions()
        except Exception as e:
            logger.error(f"Error in periodic cleanup: {e}")


app = FastAPI(
    title="SAMFMS Security Service",
    description="Authentication and authorization for South African Fleet Management System",
    version="1.0.0",
    lifespan=lifespan
)

# Configure middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# Include routers
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(admin_router)

# Serve static files for profile pictures
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Health check endpoint
@app.get("/health", tags=["Health"])
async def simple_health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "service": "security"}

# Detailed health metrics
@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    return await metrics_endpoint()


@app.get("/", tags=["Root"])
def read_root():
    """Root endpoint for the Security service."""
    logger.info("Root endpoint accessed")
    return {
        "message": "SAMFMS Security Service",
        "service": "security",
        "version": "1.0.0",
        "description": "Authentication and authorization service"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
