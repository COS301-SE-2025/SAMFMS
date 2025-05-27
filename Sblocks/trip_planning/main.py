"""Trip Planning Service - Main Application"""

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Import configurations and database
from config import settings
from database import init_database, close_database

# Import services
from services.trip_service import TripService
from services.vehicle_service import VehicleService
from services.driver_service import DriverService
from services.route_service import RouteService
from services.schedule_service import ScheduleService

# Import messaging
from messaging.rabbitmq_client import RabbitMQClient

# Import routes
from routes import api_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format=settings.log_format
)
logger = logging.getLogger(__name__)


# Global service instances
trip_service: TripService = None
vehicle_service: VehicleService = None
driver_service: DriverService = None
route_service: RouteService = None
schedule_service: ScheduleService = None
messaging_client: RabbitMQClient = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Trip Planning Service...")
    
    try:
        # Initialize database
        await init_database()
        logger.info("Database initialized successfully")
        
        # Initialize messaging client
        global messaging_client
        messaging_client = RabbitMQClient(settings.rabbitmq_url)
        await messaging_client.connect()
        logger.info("RabbitMQ connection established")
        
        # Initialize services
        global trip_service, vehicle_service, driver_service, route_service, schedule_service
        trip_service = TripService(messaging_client)
        vehicle_service = VehicleService(messaging_client)
        driver_service = DriverService(messaging_client)
        route_service = RouteService(messaging_client)
        schedule_service = ScheduleService(messaging_client)
        
        # Store services in app state for access in routes
        app.state.trip_service = trip_service
        app.state.vehicle_service = vehicle_service
        app.state.driver_service = driver_service
        app.state.route_service = route_service
        app.state.schedule_service = schedule_service
        app.state.messaging_client = messaging_client
        
        logger.info("All services initialized successfully")
        logger.info(f"Trip Planning Service started on {settings.host}:{settings.port}")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    # Shutdown
    logger.info("Shutting down Trip Planning Service...")
    
    try:
        # Close messaging connection
        if messaging_client:
            await messaging_client.close()
            logger.info("RabbitMQ connection closed")
        
        # Close database connections
        await close_database()
        logger.info("Database connections closed")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
    
    logger.info("Trip Planning Service shut down completed")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Comprehensive trip planning and fleet management service",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        from database import get_database
        db = get_database()
        await db.command("ping")
        
        # Check messaging connection
        if messaging_client and messaging_client.connection and not messaging_client.connection.is_closed:
            messaging_status = "connected"
        else:
            messaging_status = "disconnected"
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "service": settings.app_name,
                "version": settings.app_version,
                "database": "connected",
                "messaging": messaging_status,
                "timestamp": "2025-05-26T00:00:00Z"
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": settings.app_name,
                "version": settings.app_version,
                "error": str(e),
                "timestamp": "2025-05-26T00:00:00Z"
            }
        )


# Root endpoint
@app.get("/", tags=["root"])
async def read_root():
    """Root endpoint with service information"""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "description": "Trip Planning Service for SAMFMS",
        "docs_url": "/docs",
        "health_check": "/health",
        "api_base": settings.api_v1_str
    }


# Include API routes
app.include_router(api_router, prefix=settings.api_v1_str)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "type": type(exc).__name__
        }
    )


# HTTP exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
