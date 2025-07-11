from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import uvicorn
import asyncio
import aio_pika
import uuid
import os
from datetime import datetime
from contextlib import asynccontextmanager

from database import db
from logging_config import setup_logging, get_logger
from middleware.error_handling import ErrorHandlingMiddleware

setup_logging()
logger = get_logger(__name__)

from rabbitmq.consumer import consume_messages, consume_single_message, consume_messages_Direct, consume_messages_Direct_GEOFENCES
from rabbitmq.admin import create_exchange, addSblock, removeSblock
from rabbitmq.producer import publish_message
from services.request_router import request_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    from services.startup import startup_service
    from services.startup_validator import get_startup_validator
    
    # Startup
    try:
        # Run comprehensive validation first
        logger.info("🔍 Running comprehensive startup validation...")
        validator = get_startup_validator(config)
        validation_results = await validator.validate_all()
        logger.info("✅ Comprehensive validation completed successfully")
        
        # Initialize services
        await startup_service.startup()
        logger.info("🚀 Core service startup completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    try:
        await startup_service.shutdown()
        logger.info("🛑 Core service shutdown completed successfully")
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")

from config.simple_env_validator import validate_and_exit_on_failure, get_validated_config

# Validate environment variables before starting
logger.info("🔍 Validating environment configuration...")
try:
    validate_and_exit_on_failure()
    config = get_validated_config()
    logger.info("✅ Environment validation completed successfully")
    logger.info(f"Environment: {config.ENVIRONMENT}")
    logger.info(f"Core port: {config.CORE_PORT}")
    logger.info(f"Log level: {config.LOG_LEVEL}")
    
    # Run comprehensive startup validation
    from services.startup_validator import get_startup_validator
    validator = get_startup_validator(config)
    # Note: Full validation will run during lifespan startup
    logger.info("🔧 Startup validator initialized")
    
except ImportError as e:
    logger.error(f"❌ Environment validation module import failed: {e}")
    logger.error("Check if all required dependencies are installed")
    raise SystemExit(1)
except AttributeError as e:
    logger.error(f"❌ Environment validation configuration error: {e}")
    logger.error("Check environment variable configuration")
    raise SystemExit(1)
except ValueError as e:
    logger.error(f"❌ Environment validation value error: {e}")
    logger.error("Check environment variable values and formats")
    raise SystemExit(1)
except Exception as e:
    logger.error(f"❌ Environment validation failed with unexpected error: {e}")
    logger.error("Check system configuration and dependencies")
    raise SystemExit(1)

app = FastAPI(
    title="SAMFMS Core Service",
    description="Central API gateway for South African Fleet Management System",
    version="1.0.0",
    lifespan=lifespan
)

origins = [
    "http://localhost:3000",     # React dev server
    "http://127.0.0.1:3000",     # React dev server (alternative)
    "http://localhost:21015",    # Frontend production port
    "http://127.0.0.1:21015",    # Frontend production port (alternative)
    "https://localhost:21015",   # Frontend production port (HTTPS)
    "https://127.0.0.1:21015",   # Frontend production port (HTTPS alternative)
    "http://localhost:5000",     # Additional dev port
    "*",                         # Allow all origins for flexibility (remove in strict production)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],        
    allow_headers=["*"],        
)

# Add error handling middleware
app.add_middleware(ErrorHandlingMiddleware)


from routes.auth import router as auth_router
from routes.plugins import router as plugins_router
from routes.gps_direct import router as gps_router
from routes.websocket import router as websocket_router
from routes.debug import router as debug_router
from routes.management_direct import router as management_router
from routes.sblock import router as sblock_router

# Import service_proxy router with proper error handling
try:
    from routes.service_proxy import router as service_proxy_router
    logger.info("✅ Service proxy router imported successfully")
    service_proxy_available = True
except ImportError as e:
    logger.error(f"❌ Failed to import service proxy router: {e}")
    logger.error("This indicates missing dependencies or configuration issues")
    logger.error("Service proxy functionality will be disabled")
    service_proxy_router = None
    service_proxy_available = False
except Exception as e:
    logger.error(f"❌ Unexpected error importing service proxy router: {e}")
    logger.error("Service proxy functionality will be disabled")
    service_proxy_router = None
    service_proxy_available = False

# Register routers
app.include_router(auth_router)
app.include_router(plugins_router)
app.include_router(gps_router)
app.include_router(websocket_router)
app.include_router(debug_router)
app.include_router(management_router)
app.include_router(sblock_router)

# Include service_proxy router if available
if service_proxy_available and service_proxy_router:
    app.include_router(service_proxy_router)  # service_proxy already has /api prefix
    logger.info("✅ Service proxy router included successfully")
else:
    logger.warning("⚠️ Service proxy router not available - some API functionality may be limited")
    logger.warning("Ensure all dependencies are installed and configured correctly")



@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/health/startup", tags=["Health"])
async def startup_health():
    """Get startup validation results"""
    try:
        from services.startup_validator import get_startup_validator
        validator = get_startup_validator(config)
        
        if hasattr(validator, 'validation_results') and validator.validation_results:
            return {
                "startup_validation": validator.validation_results,
                "overall_status": "healthy",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "message": "Startup validation not yet completed",
                "status": "pending",
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        logger.error(f"Error retrieving startup health: {e}")
        return {
            "error": "Failed to retrieve startup validation results",
            "status": "error",
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/api/health/services", tags=["Health"])
async def check_service_health():
    """Check health of downstream services"""
    services_status = {}
    
    for service in ["management", "gps", "trip_planning", "vehicle_maintenance"]:
        try:
            # Test service communication via RabbitMQ with timeout
            correlation_id = str(uuid.uuid4())
            test_message = {
                "correlation_id": correlation_id,
                "endpoint": "/health",
                "method": "GET",
                "data": {},
                "user_context": {"user_id": "health_check"},
                "timestamp": datetime.utcnow().isoformat(),
                "service": service,
                "trace_id": correlation_id
            }
            
            # Quick health check with short timeout
            start_time = datetime.utcnow()
            response = await asyncio.wait_for(
                request_router.send_request_and_wait(service, test_message, correlation_id),
                timeout=5.0
            )
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds()
            
            services_status[service] = {
                "status": "healthy",
                "response_time_seconds": response_time,
                "last_checked": end_time.isoformat()
            }
            
        except asyncio.TimeoutError:
            services_status[service] = {
                "status": "timeout",
                "error": "Service did not respond within 5 seconds",
                "last_checked": datetime.utcnow().isoformat()
            }
            logger.warning(f"Health check timeout for service: {service}")
            
        except AttributeError as e:
            services_status[service] = {
                "status": "configuration_error", 
                "error": "Request router not properly configured",
                "last_checked": datetime.utcnow().isoformat()
            }
            logger.error(f"Configuration error during health check for {service}: {e}")
            
        except Exception as e:
            services_status[service] = {
                "status": "unhealthy",
                "error": str(e),
                "last_checked": datetime.utcnow().isoformat()
            }
            logger.error(f"Health check failed for service {service}: {e}")
    
    # Determine overall status
    healthy_services = [s for s in services_status.values() if s.get("status") == "healthy"]
    total_services = len(services_status)
    
    if len(healthy_services) == total_services:
        overall_status = "healthy"
    elif len(healthy_services) > total_services // 2:
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"
    
    return {
        "status": overall_status,
        "services": services_status,
        "summary": {
            "total_services": total_services,
            "healthy_services": len(healthy_services),
            "health_percentage": (len(healthy_services) / total_services) * 100 if total_services > 0 else 0
        },
        "timestamp": datetime.utcnow().isoformat()
    }


# - Service proxy routes: routes/service_proxy.py

if __name__ == "__main__":
    logger.info("🚀 Starting Core service...")
    port = int(os.getenv("CORE_PORT", "8000"))
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_config=None  
    )