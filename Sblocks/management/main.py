from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import redis
import pika
import logging
import json
import os
import asyncio
from datetime import datetime, timezone

from database import test_database_connection, create_indexes
from routes import router as vehicle_routes
from message_queue import MessageQueueService
from service_request_handler import service_request_handler
from analytics import router as analytics_router
#from logging_config import setup_logging
#from health_metrics import health_metrics

#setup_logging()
logging.basicConfig(level=logging.INFO)
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
# Also include driver routes at the correct path for core service proxy
app.include_router(vehicle_routes, prefix="/api", tags=["drivers"])
app.include_router(analytics_router, prefix="/api/v1", tags=["analytics"])

# Initialize Redis connection
redis_host = os.getenv("REDIS_HOST", "redis")
redis_port = int(os.getenv("REDIS_PORT", "6379"))
redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

# Initialize global message queue service
mq_service = None

# Initialize RabbitMQ connection
def get_rabbitmq_connection():
    try:
        rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://samfms_rabbit:RabbitPass2025!@rabbitmq:5672/")
        connection = pika.BlockingConnection(pika.URLParameters(rabbitmq_url))
        return connection
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}")
        return None

@app.on_event("startup")
async def startup_event():
    """Enhanced startup event with comprehensive error handling and logging"""
    try:
        logger.info("🚀 Management Service Starting Up...")
        
        # Test database connection and create indexes
        try:
            logger.info("🔗 Testing database connection...")
            db_connected = await test_database_connection()
            if db_connected:
                logger.info("✅ Database connection successful")
                await create_indexes()
                logger.info("✅ Database indexes created successfully")
            else:
                logger.error("❌ Database connection failed")
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            logger.exception("Database initialization exception traceback:")
        
        # Test Redis connection
        try:
            logger.info("🔗 Testing Redis connection...")
            redis_client.ping()
            logger.info("✅ Redis connection successful")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
        
        # Test RabbitMQ connection and setup message queue
        global mq_service
        try:
            logger.info("🔗 Setting up RabbitMQ connection...")
            mq_service = MessageQueueService()
            connection_success = mq_service.connect()
            if connection_success:
                logger.info("✅ RabbitMQ connection established successfully")
                logger.info("✅ Message queue service is ready for publishing events")
            else:
                logger.error("❌ RabbitMQ connection failed - service will continue without messaging")
        except Exception as e:
            logger.error(f"❌ RabbitMQ setup failed: {e}")
            logger.exception("Full RabbitMQ setup exception traceback:")
        
        # Initialize service request handler for RabbitMQ consumption
        try:
            logger.info("🔗 Initializing service request handler...")
            # Start the consumer in a background task
            consumer_task = asyncio.create_task(service_request_handler.start_consuming())
            logger.info("✅ Service request handler background task started")
            logger.info("✅ Management service is now consuming requests from Core")
        except Exception as e:
            logger.error(f"❌ Service request handler initialization failed: {e}")
            logger.exception("Service request handler exception traceback:")

        # Send startup notification via message queue
        try:
            logger.info("📤 Sending startup notification...")
            if mq_service:
                startup_success = mq_service.publish_service_event(
                    event_type="startup",
                    service_name="management",
                    message_data={
                        "version": "1.0.0",
                        "port": 8000,
                        "endpoints": [
                            "/api/v1/vehicles",
                            "/api/v1/vehicle-assignments", 
                            "/api/v1/vehicle-usage"
                        ],
                        "status": "ready"
                    }
                )
                if startup_success:
                    logger.info("✅ Management service startup notification sent to message queue")
                else:
                    logger.warning("⚠️ Failed to send startup notification - continuing without messaging")
            else:
                logger.warning("⚠️ No message queue service available for startup notification")
        except Exception as e:
            logger.error(f"❌ Failed to send startup notification: {e}")
            logger.warning("Management service will continue without startup messaging")
        
        #health_metrics["startup_time"] = datetime.now(timezone.utc).isoformat()
        logger.info("🎉 Management Service Startup Completed")

        # Removed erroneous publish_message call
        
    except Exception as startup_error:
        logger.error(f"💥 CRITICAL ERROR DURING STARTUP: {startup_error}")
        logger.exception("Full startup exception traceback:")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Send shutdown notification when service stops"""
    logger.info("Management Service shutting down...")
    
    try:
        if mq_service:
            shutdown_success = mq_service.publish_service_event(
                event_type="shutdown",
                service_name="management",
                message_data={
                    "version": "1.0.0",
                    "status": "shutting_down",
                    "shutdown_reason": "normal"
                }
            )
            if shutdown_success:
                logger.info("Management service shutdown notification sent to message queue")
            else:
                logger.warning("Failed to send shutdown notification")
        else:
            logger.warning("No message queue service available for shutdown notification")
    except Exception as e:
        logger.error(f"Failed to send shutdown notification: {e}")
    
    # Close message queue connection
    try:
        if mq_service:
            mq_service.close()
            logger.info("Message queue connection closed")
    except Exception as e:
        logger.error(f"Error closing message queue connection: {e}")
    
    logger.info("Management Service shutdown completed")

@app.get("/")
def read_root():
    return {
        "message": "Vehicle Management Service", 
        "service": "management",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint with detailed status"""
    try:
        # Test database connection
        db_status = await test_database_connection()
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
            "rabbitmq": "up" #if health_metrics.get("rabbitmq_connected") else "down"
        },
        #"metrics": health_metrics
    }
    
    return health_status

@app.get("/debug/queues")
async def debug_queues():
    """Debug endpoint to check queue consumption status"""
    try:
        return {
            "message": "Management service debug info",
            "service_request_handler": "initialized" if hasattr(service_request_handler, 'endpoint_handlers') else "not_initialized",
            "available_endpoints": list(service_request_handler.endpoint_handlers.keys()) if hasattr(service_request_handler, 'endpoint_handlers') else [],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

@app.get("/debug/test-vehicle-handler")
async def test_vehicle_handler():
    """Test the vehicle handler directly"""
    try:
        # Test the get vehicles method directly
        test_user_context = {
            "user_id": "test-user",
            "role": "admin",
            "permissions": ["*"]
        }
        
        result = await service_request_handler._get_vehicles(
            "/api/vehicles", 
            {"limit": "10"}, 
            test_user_context
        )
        
        return {
            "success": True,
            "result": result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

@app.get("/debug/test-message-queue")
async def test_message_queue():
    """Test the message queue connectivity"""
    try:
        if not mq_service:
            return {
                "success": False,
                "error": "Message queue service not initialized",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        # Test publishing a test message
        test_success = mq_service.publish_service_event(
            event_type="test",
            service_name="management",
            message_data={
                "test_message": "Message queue connectivity test",
                "test_timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return {
            "success": test_success,
            "message": "Test message published successfully" if test_success else "Failed to publish test message",
            "mq_service_available": mq_service is not None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

if __name__ == "__main__":
    port = int(os.getenv("MANAGEMENT_PORT", "21010"))
    uvicorn.run(app, host="0.0.0.0", port=port)
