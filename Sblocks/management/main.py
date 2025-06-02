from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import redis
import pika
import logging
import json
from datetime import datetime, timezone

from database import engine, Base, get_db
from routes import router as vehicle_routes
from message_queue import setup_message_queue
from logging_config import setup_logging
from health_metrics import health_metrics

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Management Service", 
    version="1.0.0",
    description="Vehicle Management Service - Handles vehicle assignments, usage, and status"
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
    logger.info("Management Service starting up...")
    
    # Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    
    # Test Redis connection
    try:
        redis_client.ping()
        logger.info("Redis connection successful")
        health_metrics["redis_connected"] = True
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        health_metrics["redis_connected"] = False
    
    # Test RabbitMQ connection and setup message queue
    try:
        await setup_message_queue()
        logger.info("RabbitMQ setup successful")
        health_metrics["rabbitmq_connected"] = True
    except Exception as e:
        logger.error(f"RabbitMQ setup failed: {e}")
        health_metrics["rabbitmq_connected"] = False
    
    health_metrics["startup_time"] = datetime.now(timezone.utc).isoformat()
    logger.info("Management Service startup completed")

@app.get("/")
def read_root():
    return {
        "message": "Vehicle Management Service", 
        "service": "management",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/health")
def health_check():
    """Health check endpoint with detailed status"""
    try:
        # Test database connection
        db = next(get_db())
        db.execute("SELECT 1")
        db_status = True
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
        "service": "management",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {
            "database": "up" if db_status else "down",
            "redis": "up" if redis_status else "down",
            "rabbitmq": "up" if health_metrics.get("rabbitmq_connected") else "down"
        },
        "metrics": health_metrics
    }
    
    return health_status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
