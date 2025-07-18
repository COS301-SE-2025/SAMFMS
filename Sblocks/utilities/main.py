from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import redis
import pika
import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Any

# Import local modules
from services.rabbitmq_service import rabbitmq_service
from logging_config import setup_logging, get_logger
from middleware import LoggingMiddleware, SecurityHeadersMiddleware

# Configure logging
setup_logging()
logger = get_logger(__name__)

# Application lifespan for startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events."""
    # Startup
    logger.info("🔧 Utilities Service starting up...")
    
    # Initialize Redis connection
    try:
        redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)
        redis_client.ping()
        logger.info("✅ Redis connection successful")
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
    
    # Start RabbitMQ consumer for email processing
    if rabbitmq_service.connect():
        logger.info("✅ RabbitMQ connection successful")
        rabbitmq_service.start_consumer_thread()
        logger.info("📧 Email service consumer started")
    else:
        logger.error("❌ Failed to connect to RabbitMQ")
    
    logger.info("✅ Utilities Service startup completed")
    
    yield
    
    # Shutdown
    logger.info("🛑 Utilities Service shutting down...")
    rabbitmq_service.close()
    logger.info("✅ RabbitMQ connections closed")
    logger.info("✅ Utilities Service shutdown completed")
    publish_message("service_presence", aio_pika.ExchangeType.FANOUT, {"type": "service_presence", "service":"utilities"}, "")


app = FastAPI(
    title="SAMFMS Utilities Service",
    description="Utility services for South African Fleet Management System",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# Include API routes
from routes import api_router
app.include_router(api_router)

# Routes
@app.get("/")
def read_root():
    return {
        "message": "SAMFMS Utilities Service",
        "version": "1.0.0",
        "services": ["email", "notifications"]
    }

@app.get("/health")
def health_check():
    # Check RabbitMQ connection
    rabbitmq_status = "healthy" if rabbitmq_service.connection and not rabbitmq_service.connection.is_closed else "unhealthy"
    
    # Create health status response
    health_status = {
        "status": "healthy" if rabbitmq_status == "healthy" else "degraded",
        "service": "utilities",
        "components": {
            "rabbitmq": rabbitmq_status,
            "email_consumer": "running" if rabbitmq_service.running else "stopped"
        }
    }
    
    # Set HTTP status code based on health
    return health_status

# Email test endpoint for development/debugging
@app.post("/api/email/test", tags=["Email"])
async def test_email(request: Request):
    try:
        # Get JSON body
        data = await request.json()
        
        # Validate required fields
        required_fields = ["to_email", "full_name", "subject", "message"]
        for field in required_fields:
            if field not in data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Publish test email to RabbitMQ
        message = {
            "email_type": "custom",
            "to_email": data["to_email"],
            "full_name": data["full_name"],
            "subject": data["subject"],
            "message": data["message"]
        }
        
        result = rabbitmq_service.publish_email_request(message)
        
        if result:
            return {"status": "success", "message": "Email request queued successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to queue email request")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in test email endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
