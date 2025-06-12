from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import redis
import pika
import logging
import json
from datetime import datetime, timezone

from database import init_database, create_vehicle_activity_log, get_db, check_database_health
from routes import router as vehicle_routes
from message_queue_simple import setup_message_consumer
from logging_config import setup_logging
from health_metrics import health_metrics

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Vehicles Data Service", 
    version="1.0.0",
    description="Vehicle Technical Specifications and Maintenance Data Service"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(vehicle_routes, prefix="/api/v1/vehicles", tags=["vehicles"])

# Initialize Redis connection
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

# Initialize RabbitMQ connection
def get_rabbitmq_connection():
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='rabbitmq', 
                                    credentials=pika.PlainCredentials('guest', 'guest'))
        )
        return connection
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}")
        return None

@app.on_event("startup")
async def startup_event():
    logger.info("Vehicles Data Service starting up...")
      # Initialize database
    try:
        await init_database()
        await create_vehicle_activity_log()
        logger.info("Database initialized successfully")
        health_metrics["database_connected"] = True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        health_metrics["database_connected"] = False
    
    # Test Redis connection
    try:
        redis_client.ping()
        logger.info("Redis connection successful")
        health_metrics["redis_connected"] = True
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        health_metrics["redis_connected"] = False
    
    # Setup message queue consumer
    try:
        await setup_message_consumer()
        logger.info("Message queue consumer setup successful")
        health_metrics["rabbitmq_connected"] = True
    except Exception as e:
        logger.error(f"Message queue setup failed: {e}")
        health_metrics["rabbitmq_connected"] = False
    
    health_metrics["startup_time"] = datetime.now(timezone.utc).isoformat()
    logger.info("Vehicles Data Service startup completed")

@app.get("/")
def read_root():
    return {
        "message": "Vehicle Technical Specifications and Maintenance Data Service", 
        "service": "vehicles",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/health")
def health_check():
    """Health check endpoint with detailed status"""
    try:
        # Test database connection
        db_status = check_database_health()
    except Exception:
        db_status = False
    
    # Test Redis connection
    try:
        redis_client.ping()
        redis_status = True
    except Exception:
        redis_status = False
    
    health_status = {
        "status": "healthy" if all([db_status, redis_status]) else "unhealthy",
        "service": "vehicles",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {
            "database": "up" if db_status else "down",
            "redis": "up" if redis_status else "down",
            "rabbitmq": "up" if health_metrics.get("rabbitmq_connected") else "down"
        },
        "metrics": health_metrics
    }
    
    return health_status

@app.get("/stats")
def get_service_stats():
    """Get service statistics"""
    try:
        from .database import get_vehicle_statistics
        stats = get_vehicle_statistics()
        
        return {
            "service": "vehicles",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "statistics": stats,
            "health_metrics": health_metrics
        }
        
    except Exception as e:
        logger.error(f"Error getting service stats: {e}")
        return {
            "service": "vehicles",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": "Failed to get statistics"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
