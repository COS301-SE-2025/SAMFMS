from fastapi import FastAPI
from contextlib import asynccontextmanager
import redis
import pika
from routes import router as auth_router
from database import test_database_connection, create_indexes, cleanup_expired_sessions
from message_queue import mq_service
from logging_config import setup_logging, get_logger
from middleware import LoggingMiddleware, SecurityHeadersMiddleware
from health_metrics import health_check, metrics_endpoint

# Setup structured logging
setup_logging()
logger = get_logger(__name__)


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
        redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)
        redis_client.ping()
        logger.info("✅ Successfully connected to Redis")
    except Exception as e:
        logger.error(f"❌ Failed to connect to Redis: {e}")
    
    # Connect to RabbitMQ
    if mq_service.connect():
        logger.info("✅ Successfully connected to RabbitMQ")
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
    description="Authentication and authorization service for SAMFMS",
    version="1.0.0",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# Include routers
app.include_router(auth_router)

# Health and metrics endpoints
app.add_api_route("/health", health_check, methods=["GET"], tags=["Health"])
app.add_api_route("/metrics", metrics_endpoint, methods=["GET"], tags=["Metrics"])


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
    uvicorn.run(app, host="0.0.0.0", port=8000)
