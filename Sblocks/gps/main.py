"""
Main FastAPI Application for GPS Tracking Service

Provides comprehensive GPS tracking, geofencing, and route management
for the SAMFMS trip planning system.
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config.settings import get_settings
from .database import init_database, close_database
from .messaging.rabbitmq_client import RabbitMQClient
from .api import location_router, geofence_router, route_router, websocket_router
from .services import LocationService, GeofenceService, RouteService
from .websocket_manager import connection_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global service instances
location_service = None
geofence_service = None
route_service = None
messaging_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global location_service, geofence_service, route_service, messaging_client
    
    logger.info("Starting GPS Tracking Service...")
    
    try:
        # Initialize database
        await init_database()
        logger.info("Database initialized")
        
        # Initialize messaging
        messaging_client = RabbitMQClient()
        await messaging_client.connect()
        logger.info("RabbitMQ connection established")
        
        # Initialize services
        location_service = LocationService()
        await location_service.initialize()
        logger.info("Location service initialized")
        
        geofence_service = GeofenceService()
        await geofence_service.initialize()
        logger.info("Geofence service initialized")
        
        route_service = RouteService()
        await route_service.initialize()
        logger.info("Route service initialized")
        
        # Set up real-time event handlers
        await setup_event_handlers()
        
        logger.info("GPS Tracking Service startup complete")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to start GPS Tracking Service: {e}")
        raise
    
    finally:
        # Cleanup
        logger.info("Shutting down GPS Tracking Service...")
        
        if messaging_client:
            await messaging_client.disconnect()
            logger.info("RabbitMQ connection closed")
        
        await close_database()
        logger.info("Database connection closed")
        
        logger.info("GPS Tracking Service shutdown complete")


async def setup_event_handlers():
    """Set up event handlers for real-time updates"""
    try:
        # Location update handler
        async def handle_location_update(location_data):
            """Handle real-time location updates"""
            try:
                from .models.location import VehicleLocation
                location = VehicleLocation(**location_data)
                await connection_manager.broadcast_location_update(location)
                
                # Check geofences for this location
                if geofence_service:
                    await geofence_service.check_location_against_geofences(location)
                    
                # Update route progress if applicable
                if route_service:
                    active_routes = await route_service.get_vehicle_routes(
                        vehicle_id=location.vehicle_id,
                        status="in_progress",
                        limit=1
                    )
                    if active_routes:
                        await route_service.add_route_point(active_routes[0].id, location)
                        
            except Exception as e:
                logger.error(f"Error handling location update: {e}")
        
        # Geofence event handler
        async def handle_geofence_event(event_data):
            """Handle geofence events"""
            try:
                await connection_manager.broadcast_geofence_event(
                    geofence_id=event_data.get("geofence_id"),
                    vehicle_id=event_data.get("vehicle_id"),
                    event_type=event_data.get("event_type"),
                    data=event_data
                )
            except Exception as e:
                logger.error(f"Error handling geofence event: {e}")
        
        # Route event handler
        async def handle_route_event(event_data):
            """Handle route events"""
            try:
                await connection_manager.broadcast_route_event(
                    route_id=event_data.get("route_id"),
                    vehicle_id=event_data.get("vehicle_id"),
                    event_type=event_data.get("event_type"),
                    data=event_data
                )
            except Exception as e:
                logger.error(f"Error handling route event: {e}")
        
        logger.info("Event handlers configured")
        
    except Exception as e:
        logger.error(f"Failed to set up event handlers: {e}")


# Create FastAPI application
settings = get_settings()

app = FastAPI(
    title="GPS Tracking Service",
    description="Comprehensive GPS tracking, geofencing, and route management service for SAMFMS",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(location_router, prefix="/api/v1")
app.include_router(geofence_router, prefix="/api/v1")
app.include_router(route_router, prefix="/api/v1")
app.include_router(websocket_router, prefix="/api/v1")


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connectivity
        from .database import get_database
        db = await get_database()
        await db.command("ping")
        
        # Check service status
        services_status = {
            "location_service": location_service is not None,
            "geofence_service": geofence_service is not None,
            "route_service": route_service is not None,
            "messaging": messaging_client is not None and messaging_client.connection is not None
        }
        
        # Get WebSocket connection stats
        ws_stats = connection_manager.get_connection_stats()
        
        return {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z",  # Use actual timestamp
            "services": services_status,
            "websocket_connections": ws_stats,
            "version": "1.0.0"
        }
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


# Service info endpoint
@app.get("/info")
async def service_info():
    """Get service information"""
    return {
        "service": "GPS Tracking Service",
        "version": "1.0.0",
        "description": "Comprehensive GPS tracking, geofencing, and route management",
        "features": [
            "Real-time vehicle location tracking",
            "Geofence management and monitoring",
            "Route planning and progress tracking",
            "WebSocket-based real-time updates",
            "Location history and analytics",
            "Speed monitoring and violations",
            "Dwell time analysis",
            "Emergency alerts"
        ],
        "endpoints": {
            "locations": "/api/v1/locations",
            "geofences": "/api/v1/geofences",
            "routes": "/api/v1/routes",
            "websockets": "/api/v1/ws",
            "health": "/health",
            "docs": "/docs"
        }
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "detail": str(exc) if settings.debug else None
        }
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "GPS Tracking Service",
        "version": "1.0.0",
        "status": "operational",
        "documentation": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    
    # Development server configuration
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8003,  # Different port from trip planning service
        reload=True,
        log_level="info"
    )
