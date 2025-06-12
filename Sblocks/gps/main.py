"""
GPS Service - SAMFMS Microservice
Enhanced with structured logging, health monitoring, and performance metrics.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from logging_config import setup_logging, get_logger
from connections import ConnectionManager
from middleware import get_logging_middleware, get_security_middleware
from health_metrics import get_health_status, get_metrics

SERVICE_NAME = "gps-service"
SERVICE_VERSION = "1.0.0"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

logger = setup_logging(SERVICE_NAME)

app = FastAPI(
    title="GPS Service",
    version=SERVICE_VERSION,
    description="GPS tracking and location services for SAMFMS",
    docs_url="/docs" if ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if ENVIRONMENT == "development" else None
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.middleware("http")(get_security_middleware())
app.middleware("http")(get_logging_middleware())


# Event handlers
@app.on_event("startup")
async def startup_event():
    """Initialize service on startup."""
    logger.info(
        "GPS Service starting up",
        extra={
            "version": SERVICE_VERSION,
            "environment": ENVIRONMENT,
            "service": SERVICE_NAME
        }
    )
    
    # Test connections during startup
    redis_conn = ConnectionManager.get_redis_connection()
    if redis_conn:
        logger.info("Redis connection established successfully")
    else:
        logger.error("Failed to establish Redis connection")
    
    rabbitmq_conn = ConnectionManager.get_rabbitmq_connection()
    if rabbitmq_conn:
        logger.info("RabbitMQ connection established successfully")
        rabbitmq_conn.close()  # Close test connection
    else:
        logger.error("Failed to establish RabbitMQ connection")
    
    logger.info("GPS Service startup completed")

    from rabbitmq.consumer import consume_messages
    from rabbitmq.admin import create_exchange
    from rabbitmq.producer import publish_message

    


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    logger.info("GPS Service shutting down")
    
    # Close all connections
    ConnectionManager.close_connections()
    
    logger.info("GPS Service shutdown completed")


# API Endpoints
@app.get("/")
def read_root():
    """Root endpoint with service information."""
    logger.info("Root endpoint accessed")
    return {
        "message": "Hello from GPS Service",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "environment": ENVIRONMENT
    }


@app.get("/health")
def health_check():
    """Comprehensive health check endpoint."""
    return get_health_status()


@app.get("/metrics")
def metrics():
    """Performance metrics endpoint."""
    return get_metrics()


@app.get("/gps/locations")
def get_locations():
    """Get GPS location data."""
    logger.info("GPS locations endpoint accessed")
    
    # TODO: Implement actual GPS location retrieval
    # This is a placeholder implementation
    try:
        redis_conn = ConnectionManager.get_redis_connection()
        if redis_conn:
            # Example: Get locations from Redis
            # locations = redis_conn.get("gps:locations")
            logger.debug("Retrieved GPS locations from Redis")
        
        return {
            "locations": [],
            "message": "GPS locations retrieved successfully",
            "count": 0
        }
        
    except Exception as e:
        logger.error(
            "Failed to retrieve GPS locations",
            extra={
                "error": str(e),
                "endpoint": "/gps/locations"
            }
        )
        raise


@app.post("/gps/locations")
def update_location(location_data: dict):
    """Update GPS location data."""
    logger.info("GPS location update endpoint accessed")
    
    # TODO: Implement actual GPS location update
    # This is a placeholder implementation
    try:
        redis_conn = ConnectionManager.get_redis_connection()
        if redis_conn:
            # Example: Store location in Redis
            # redis_conn.set("gps:locations", json.dumps(location_data))
            logger.debug("Stored GPS location data in Redis")
        
        rabbitmq_conn = ConnectionManager.get_rabbitmq_connection()
        if rabbitmq_conn:
            # Example: Publish location update to message queue
            # channel = rabbitmq_conn.channel()
            # channel.basic_publish(exchange='', routing_key='gps_updates', body=json.dumps(location_data))
            logger.debug("Published GPS location update to message queue")
            rabbitmq_conn.close()
        
        return {
            "message": "GPS location updated successfully",
            "location_id": location_data.get("id", "unknown")
        }
        
    except Exception as e:
        logger.error(
            "Failed to update GPS location",
            extra={
                "error": str(e),
                "endpoint": "/gps/locations",
                "location_data": location_data
            }
        )
        raise


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting GPS Service in standalone mode")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_config=None  # Use our custom logging configuration
    )
