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
    
    # Startup
    await startup_service.startup()
    
    yield
    
    # Shutdown
    await startup_service.shutdown()

from config.simple_env_validator import validate_and_exit_on_failure, get_validated_config

# Validate environment variables before starting
logger.info("🔍 Validating environment configuration...")
try:
    validate_and_exit_on_failure()
    config = get_validated_config()
    logger.info("✅ Environment validation completed successfully")
except Exception as e:
    logger.error(f"❌ Environment validation failed: {e}")
    raise SystemExit(1)

app = FastAPI(
    title="SAMFMS Core Service",
    description="Central API gateway for South African Fleet Management System",
    version="1.0.0",
    lifespan=lifespan
)

origins = [
    "http://localhost:3000",     
    "http://127.0.0.1:3000",
    "http://localhost:5000",     
    "*",                        
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],        
    allow_headers=["*"],        
)


from routes.auth import router as auth_router
from routes.plugins import router as plugins_router
from routes.gps_direct import router as gps_router
from routes.websocket import router as websocket_router
from routes.debug import router as debug_router
from routes.management_direct import router as management_router
from routes.sblock import router as sblock_router

# Try to import service_proxy router with error handling
try:
    from routes.service_proxy import router as service_proxy_router
    logger.info("✅ Service proxy router imported successfully")
    service_proxy_available = True
except Exception as e:
    logger.error(f"❌ Failed to import service proxy router: {e}")
    service_proxy_router = None
    service_proxy_available = False

app.include_router(auth_router)
app.include_router(plugins_router)
app.include_router(gps_router)
app.include_router(websocket_router)
app.include_router(debug_router)
app.include_router(management_router)
app.include_router(sblock_router)

# Only include service_proxy if it imported successfully
if service_proxy_available and service_proxy_router:
    app.include_router(service_proxy_router)  # service_proxy already has /api prefix
    logger.info("✅ Service proxy router included successfully")
else:
    logger.error("❌ Service proxy router not available - using fallback routes")



@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}

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
            response = await asyncio.wait_for(
                request_router.send_request_and_wait(service, test_message, correlation_id),
                timeout=5.0
            )
            services_status[service] = "healthy"
        except asyncio.TimeoutError:
            services_status[service] = "timeout - service may be unavailable"
        except Exception as e:
            services_status[service] = f"unhealthy: {str(e)}"
    
    overall_status = "healthy" if all("healthy" in status for status in services_status.values()) else "degraded"
    
    return {
        "status": overall_status,
        "services": services_status,
        "timestamp": datetime.utcnow().isoformat()
    }

# All route handlers have been moved to appropriate router modules:
# - Debug/testing routes: routes/debug.py
# - Management routes: routes/management_direct.py  
# - SBlock routes: routes/sblock.py
# - GPS routes: routes/gps_direct.py
# - WebSocket routes: routes/websocket.py
# - Auth routes: routes/auth.py
# - Plugin routes: routes/plugins.py
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