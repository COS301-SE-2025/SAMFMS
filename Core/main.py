from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import uvicorn
import asyncio
from contextlib import asynccontextmanager
from database import db
from logging_config import setup_logging, get_logger

# Setup structured logging
setup_logging()
logger = get_logger(__name__)

# Import the message consumer
from rabbitmq.consumer import consume_messages

# Application lifespan events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events."""
    # Startup
    logger.info("🚀 Core service starting up...")
    
    # Test database connection
    try:
        # Test MongoDB connection
        client = AsyncIOMotorClient("mongodb://host.docker.internal:27017")
        await client.admin.command('ping')
        logger.info("✅ Successfully connected to MongoDB")
        client.close()
    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
    
    # Start consuming messages from the service_status queue
    consumer_task = asyncio.create_task(consume_messages("service_status"))
    logger.info("Started consuming messages from service_status queue")
    
    logger.info("✅ Core service startup completed")
    
    yield
    
    # Shutdown
    logger.info("🛑 Core service shutting down...")
    # Cancel consumer task if it's still running
    if not consumer_task.done():
        consumer_task.cancel()
    logger.info("✅ Core service shutdown completed")

app = FastAPI(
    title="SAMFMS Core Service",
    description="Central API gateway for South African Fleet Management System",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
origins = [
    "http://localhost:3000",     # React development server
    "http://127.0.0.1:3000",
    "http://localhost:5000",     # Production build if served differently
    "*",                        # Optional: Allow all origins (less secure)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],        # Allow all methods including OPTIONS
    allow_headers=["*"],        # Allow all headers
)

# Import and include the auth router
from routes.auth import router as auth_router
app.include_router(auth_router)

# Add a route for health checks (needed by Security middleware)
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    logger.info("🚀 Starting Core service...")
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_config=None  # Use our custom logging configuration
    )
