
import asyncio
import logging
import os
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


from repositories.database import db_manager
from events.publisher import event_publisher
from events.consumer import event_consumer, setup_event_handlers
from services.analytics_service import analytics_service
from services.request_consumer import service_request_consumer
from api.routes.analytics import router as analytics_router
from api.routes.assignments import router as assignments_router
from api.routes.drivers import router as drivers_router
from api.routes.vehicles import router as vehicles_router


from middleware import (
    RequestContextMiddleware, LoggingMiddleware, SecurityHeadersMiddleware,
    MetricsMiddleware, RateLimitMiddleware, HealthCheckMiddleware
)
from api.exception_handlers import (
    EXCEPTION_HANDLERS, DatabaseConnectionError, EventPublishError, 
    BusinessLogicError
)
from schemas.responses import ResponseBuilder


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


metrics_middleware = MetricsMiddleware(None)


service_discovery_client = None

async def register_with_core_service():
    
    global service_discovery_client
    try:
        import aiohttp
        import json
        
        
        core_host = os.getenv("CORE_HOST", "core")
        core_port = int(os.getenv("CORE_PORT", "8000"))
        
        service_info = {
            "name": "management",
            "host": os.getenv("MANAGEMENT_HOST", "management"),
            "port": int(os.getenv("MANAGEMENT_PORT", "8000")),
            "version": "2.1.0",
            "protocol": "http",
            "health_check_url": "/health",
            "tags": ["management", "analytics", "assignments", "drivers"],
            "metadata": {
                "features": [
                    "event_driven_architecture",
                    "optimized_analytics_with_caching", 
                    "repository_pattern",
                    "enhanced_error_handling"
                ],
                "startup_time": datetime.utcnow().isoformat()
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"http://{core_host}:{core_port}/api/services/register",
                json=service_info,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    logger.info("✅ Successfully registered with Core service discovery")
                    return True
                else:
                    logger.warning(f"⚠️ Service registration failed with status {response.status}")
                    return False
                    
    except Exception as e:
        logger.warning(f"⚠️ Failed to register with Core service discovery: {e}")
        logger.info("Service will continue without Core registration")
        return False

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    logger.info("Management Service Starting Up...")
    
    try:
        
        logger.info("Connecting to database...")
        try:
            await db_manager.connect()
            logger.info("Database connected successfully")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise DatabaseConnectionError(f"Failed to connect to database: {e}")
        
        
        logger.info("🔗 Connecting to RabbitMQ for event publishing...")
        try:
            publisher_connected = await event_publisher.connect()
            if publisher_connected:
                logger.info("Event publisher connected successfully")
            else:
                logger.warning("Event publisher connection failed - continuing without events")
        except Exception as e:
            logger.error(f"Event publisher connection error: {e}")
            publisher_connected = False
        
        
        logger.info("Setting up event consumer...")
        try:
            consumer_connected = await event_consumer.connect()
            if consumer_connected:
                await setup_event_handlers()
                
                asyncio.create_task(event_consumer.start_consuming())
                logger.info("Event consumer started successfully")
            else:
                logger.warning("Event consumer connection failed - continuing without event consumption")
        except Exception as e:
            logger.error(f"Event consumer setup error: {e}")
            consumer_connected = False
        
        
        logger.info("Setting up service request consumer...")
        try:
            request_consumer_connected = await service_request_consumer.connect()
            if request_consumer_connected:
                
                asyncio.create_task(service_request_consumer.start_consuming())
                logger.info("Service request consumer started successfully")
            else:
                logger.warning("Service request consumer connection failed - Core communication disabled")
        except Exception as e:
            logger.error(f"Service request consumer setup error: {e}")
            request_consumer_connected = False
        
        
        if publisher_connected:
            try:
                await event_publisher.publish_service_started(
                    version="2.1.0",
                    data={
                        "reorganized": True,
                        "event_driven": True,
                        "optimized": True,
                        "enhanced_features": [
                            "analytics_caching", 
                            "event_driven_communication", 
                            "repository_pattern",
                            "enhanced_error_handling",
                            "standardized_responses",
                            "comprehensive_monitoring",
                            "rate_limiting",
                            "request_tracing"
                        ]
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to publish service started event: {e}")
        
        
        await register_with_core_service()
        
        
        logger.info("🔍 Registering with Core service discovery...")
        registration_success = await register_with_core_service()
        if registration_success:
            logger.info("Service discovery registration completed")
        else:
            logger.warning("Continuing without Core service discovery registration")
        
        
        asyncio.create_task(enhanced_background_tasks())
        
        logger.info("Management Service Startup Completed Successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"CRITICAL ERROR DURING STARTUP: {e}")
        raise
    
    finally:
        
        logger.info("Management Service Shutting Down...")
        
        
        try:
            if event_publisher.connection and not event_publisher.connection.is_closed:
                await event_publisher.publish_service_stopped(version="2.0.0")
        except Exception as e:
            logger.error(f"Error publishing shutdown event: {e}")
        
        
        try:
            await event_publisher.disconnect()
            await event_consumer.disconnect()
            await db_manager.disconnect()
            logger.info("All connections closed successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        
        logger.info("👋 Management Service Shutdown Completed")


async def enhanced_background_tasks():
    
    logger.info("Starting enhanced background tasks")
    
    while True:
        try:
            
            logger.debug("Running analytics cache cleanup")
            await analytics_service.cleanup_expired_cache()
            
            await asyncio.sleep(600)  
            
            
            logger.debug("Refreshing critical analytics")
            try:
                await analytics_service.get_fleet_utilization(use_cache=False)
                logger.info("Successfully refreshed critical analytics")
            except Exception as e:
                logger.error(f"Failed to refresh critical analytics: {e}")
            
            await asyncio.sleep(1200)  
            
            
            try:
                metrics = metrics_middleware.get_metrics()
                logger.info(f"Service metrics: {metrics}")
            except Exception as e:
                logger.error(f"Failed to collect metrics: {e}")
            
            await asyncio.sleep(300)  
            
        except Exception as e:
            logger.error(f"Error in background tasks: {e}")
            await asyncio.sleep(60)  


async def background_tasks():
    
    await enhanced_background_tasks()



app = FastAPI(
    title="Management Service",
    version="2.1.0",
    description="Enhanced Vehicle Management Service with Event-Driven Architecture and Comprehensive Error Handling",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


for exception_type, handler in EXCEPTION_HANDLERS.items():
    app.add_exception_handler(exception_type, handler)


app.add_middleware(RequestContextMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=120)  
app.add_middleware(HealthCheckMiddleware)
app.add_middleware(LoggingMiddleware, include_request_body=False, include_response_body=False)
app.add_middleware(SecurityHeadersMiddleware, enable_hsts=True)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


metrics_middleware.app = app


app.include_router(analytics_router, prefix="/api/v1", tags=["analytics"])
app.include_router(assignments_router, prefix="/api/v1", tags=["assignments"])
app.include_router(drivers_router, prefix="/api/v1", tags=["drivers"])
app.include_router(vehicles_router, prefix="/api/v1", tags=["vehicles"])


@app.get("/")
async def root():
    
    uptime_seconds = (datetime.now(timezone.utc) - datetime.now(timezone.utc)).total_seconds()
    
    return ResponseBuilder.success(
        data={
            "service": "management",
            "version": "2.1.0",
            "status": "operational",
            "enhanced_features": [
                "event_driven_architecture",
                "optimized_analytics_with_caching", 
                "repository_pattern",
                "clean_separation_of_concerns",
                "background_task_processing",
                "enhanced_error_handling",
                "standardized_responses",
                "comprehensive_monitoring",
                "rate_limiting",
                "request_tracing",
                "dead_letter_queues",
                "retry_mechanisms"
            ],
            "uptime_seconds": uptime_seconds,
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        message="Management Service is operational with enhanced features"
    ).model_dump()


@app.get("/health")
async def health_check():
    
    try:
        
        db_healthy = await db_manager.health_check()
        
        
        publisher_healthy = (
            event_publisher.connection is not None and 
            not event_publisher.connection.is_closed
        )
        
        
        consumer_healthy = (
            event_consumer.connection is not None and 
            not event_consumer.connection.is_closed and
            event_consumer.is_consuming
        )
        
        
        critical_components = [db_healthy]  
        optional_components = [publisher_healthy, consumer_healthy]  
        
        if all(critical_components):
            if all(optional_components):
                overall_status = "healthy"
            else:
                overall_status = "degraded"  
        else:
            overall_status = "unhealthy"  
        
        uptime_seconds = getattr(app.state, 'start_time', datetime.now(timezone.utc))
        if isinstance(uptime_seconds, datetime):
            uptime_seconds = (datetime.now(timezone.utc) - uptime_seconds).total_seconds()
        
        health_data = {
            "status": overall_status,
            "service": "management",
            "version": "2.1.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": uptime_seconds,
            "components": {
                "database": {
                    "status": "up" if db_healthy else "down",
                    "critical": True
                },
                "event_publisher": {
                    "status": "up" if publisher_healthy else "down",
                    "critical": False
                },
                "event_consumer": {
                    "status": "up" if consumer_healthy else "down", 
                    "critical": False,
                    "consuming": getattr(event_consumer, 'is_consuming', False)
                }
            }
        }
        
        return ResponseBuilder.success(
            data=health_data,
            message=f"Service is {overall_status}"
        ).model_dump()
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return ResponseBuilder.error(
            error="HealthCheckError",
            message="Health check failed",
            details={"error": str(e)}
        ).model_dump()


@app.get("/metrics")
async def get_service_metrics():
    
    try:
        metrics = metrics_middleware.get_metrics()
        
        return ResponseBuilder.success(
            data=metrics,
            message="Service metrics retrieved successfully"
        ).model_dump()

        
    except Exception as e:
        logger.error(f"Metrics collection error: {e}")
        return ResponseBuilder.error(
            error="MetricsError",
            message="Failed to collect metrics",
            details={"error": str(e)}
        ).model_dump()


@app.get("/info/events")
async def event_info():
    
    try:
        event_data = {
            "event_system": {
                "publisher_connected": (
                    event_publisher.connection is not None and 
                    not event_publisher.connection.is_closed
                ),
                "consumer_connected": (
                    event_consumer.connection is not None and 
                    not event_consumer.connection.is_closed
                ),
                "consumer_active": getattr(event_consumer, 'is_consuming', False),
                "dead_letter_queue_enabled": True,
                "retry_mechanisms_enabled": True,
                "max_retry_attempts": getattr(event_consumer, 'max_retry_attempts', 3),
                "supported_events": [
                    "assignment.created",
                    "assignment.completed", 
                    "trip.started",
                    "trip.ended",
                    "driver.created",
                    "analytics.refreshed"
                ],
                "listening_for": [
                    "vehicle.created",
                    "vehicle.updated", 
                    "vehicle.deleted",
                    "vehicle.status_changed",
                    "user.created",
                    "user.updated",
                    "user.role_changed"
                ]
            }
        }
        
        return ResponseBuilder.success(
            data=event_data,
            message="Event system information retrieved successfully"
        ).model_dump()
        
    except Exception as e:
        logger.error(f"Event info error: {e}")
        return ResponseBuilder.error(
            error="EventInfoError",
            message="Failed to get event system information",
            details={"error": str(e)}
        ).model_dump()


if __name__ == "__main__":
    try:
        import uvicorn
        uvicorn.run(
            "main:app", 
            host="0.0.0.0", 
            port=int(os.getenv("MANAGEMENT_PORT", "8000")),
            reload=True,
            log_level="info"
        )
    except ImportError:
        logger.error("uvicorn not available - run with: python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload")
