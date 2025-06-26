from fastapi import FastAPI
from contextlib import asynccontextmanager
import redis
import os
from routes import router as users_router
from database import test_database_connection, create_indexes
from message_queue import mq_consumer
from logging_config import setup_logging, get_logger
from middleware import LoggingMiddleware, SecurityHeadersMiddleware
from health_metrics import metrics_router

# Setup structured logging
setup_logging()
logger = get_logger(__name__)


# Application lifespan events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events."""
    # Startup
    logger.info("👥 Users Data service starting up...")
    
    # Test database connection
    await test_database_connection()
    
    # Create database indexes
    await create_indexes()
    
    # Test Redis connection
    try:
        redis_host = os.getenv("REDIS_HOST", "redis")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        redis_client.ping()
        logger.info("✅ Successfully connected to Redis")
    except Exception as e:
        logger.error(f"❌ Failed to connect to Redis: {e}")
    
    # Start message queue consumer
    mq_consumer.start_consuming()
    
    logger.info("✅ Users Data service startup completed")
    
    yield
    
    # Shutdown
    logger.info("🛑 Users Data service shutting down...")
    mq_consumer.stop_consuming()
    logger.info("✅ Users Data service shutdown completed")


app = FastAPI(
    title="SAMFMS Users Data Service",
    description="User profile data management service for SAMFMS",
    version="1.0.0",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# Include routers
app.include_router(users_router)

# Include health and metrics router
app.include_router(metrics_router)


@app.get("/", tags=["Root"])
def read_root():
    """Root endpoint for the Users Data service."""
    logger.info("Root endpoint accessed")
    return {
        "message": "SAMFMS Users Data Service",
        "service": "users_data",
        "version": "1.0.0",
        "description": "User profile data management service"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("USERS_DBLOCK_PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
