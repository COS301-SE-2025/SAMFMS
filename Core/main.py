"""
SAMFMS Core Service - Enhanced Main Application
Centralized API gateway with comprehensive error handling, logging, and service discovery
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import asyncio
import os
from datetime import datetime

# Import enhanced components
from database import get_database_manager
from config.settings import get_config_manager
from logging_config import setup_logging, get_logger

# Setup logging first
setup_logging()
logger = get_logger(__name__)

# Get configuration
try:
    config_manager = get_config_manager()
    config = config_manager.get_config()
except Exception as e:
    logger.error(f"Failed to load configuration: {e}")
    raise SystemExit(1)

logger.info("🔧 SAMFMS Core Service starting...")
logger.info(f"Environment: {config.environment.value}")
logger.info(f"Database: {config.database.name}")
logger.info(f"Log level: {os.getenv('LOG_LEVEL', 'INFO')}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Enhanced application lifespan manager with comprehensive startup/shutdown"""
    
    startup_start_time = datetime.utcnow()
    logger.info("🚀 Starting SAMFMS Core Service...")
    
    try:
        # Import components here to avoid circular imports
        from common.exceptions import DatabaseError
        from common.service_discovery import get_service_discovery, shutdown_service_discovery
        from auth_service import get_auth_service, shutdown_auth_service
        
        # 1. Initialize Database
        logger.info("📊 Initializing database connection...")
        db_manager = await get_database_manager()
        await db_manager.connect()
        
        # Verify database health
        health = await db_manager.health_check()
        if health["status"] != "healthy":
            raise DatabaseError("Database health check failed", details=health)
        logger.info("✅ Database connection established and healthy")
        
        # 2. Initialize Service Discovery
        logger.info("🔍 Initializing service discovery...")
        service_discovery = await get_service_discovery()
        
        # Register this service
        await service_discovery.register_service(
            name="samfms-core",
            host=config.host,
            port=config.core_port,
            version="1.0.0",
            health_check_url="/health",
            tags=["api", "core", "gateway"],
            metadata={
                "environment": config.environment.value,
                "database": config.database.name,
                "startup_time": startup_start_time.isoformat()
            }
        )
        logger.info("✅ Service discovery initialized and service registered")
        
        # 3. Initialize Authentication Service
        logger.info("🔐 Initializing authentication service...")
        auth_service = await get_auth_service()
        logger.info("✅ Authentication service initialized")
        
        # 4. Initialize RabbitMQ (if needed)
        try:
            logger.info("🐰 Initializing RabbitMQ...")
            from rabbitmq.consumer import consume_messages
            from rabbitmq.admin import create_exchange
            import aio_pika
            
            # Create exchanges if needed
            await create_exchange("service_requests", aio_pika.ExchangeType.DIRECT)
            await create_exchange("core_responses", aio_pika.ExchangeType.DIRECT)
            
            # Start background message consumption for service responses
            consumer_task = asyncio.create_task(consume_messages("core_responses"))
            # Keep a reference to prevent garbage collection
            app.state.consumer_task = consumer_task
            logger.info("✅ RabbitMQ initialized with service response consumer")
        except Exception as e:
            logger.warning(f"⚠️  RabbitMQ initialization failed: {e}")
            logger.exception("RabbitMQ initialization error details:")
            # Continue without RabbitMQ for now
        
        # 5. Initialize startup services (includes response manager)
        try:
            logger.info("⚙️ Initializing startup services...")
            from services.startup import startup_service
            await startup_service.startup()
            logger.info("✅ Startup services initialized")
        except Exception as e:
            logger.warning(f"⚠️  Startup services initialization failed: {e}")
            # Continue without startup services
        
        startup_duration = (datetime.utcnow() - startup_start_time).total_seconds()
        logger.info(f"🎉 SAMFMS Core Service startup completed in {startup_duration:.2f}s")
        
        # Store startup info in app state
        app.state.startup_time = startup_start_time
        app.state.config = config
        app.state.db_manager = db_manager
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown sequence
    shutdown_start_time = datetime.utcnow()
    logger.info("🛑 Shutting down SAMFMS Core Service...")
    
    try:
        # Import shutdown functions
        from common.service_discovery import shutdown_service_discovery
        from auth_service import shutdown_auth_service
        
        # 1. Shutdown services
        logger.info("🔐 Shutting down authentication service...")
        await shutdown_auth_service()
        
        logger.info("🔍 Shutting down service discovery...")
        await shutdown_service_discovery()
        
        # 2. Stop RabbitMQ consumer
        if hasattr(app.state, 'consumer_task'):
            logger.info("🐰 Stopping RabbitMQ consumer...")
            try:
                app.state.consumer_task.cancel()
                await app.state.consumer_task
            except asyncio.CancelledError:
                logger.info("RabbitMQ consumer stopped")
            except Exception as e:
                logger.warning(f"Error stopping RabbitMQ consumer: {e}")
        
        # 3. Close database connections
        if hasattr(app.state, 'db_manager'):
            logger.info("📊 Closing database connections...")
            await app.state.db_manager.close()
        
        shutdown_duration = (datetime.utcnow() - shutdown_start_time).total_seconds()
        logger.info(f"✅ SAMFMS Core Service shutdown completed in {shutdown_duration:.2f}s")
        
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")

# Create FastAPI application
app = FastAPI(
    title="SAMFMS Core Service",
    description="Enhanced Central API Gateway for South African Fleet Management System",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if config.environment.value != "production" else None,
    redoc_url="/redoc" if config.environment.value != "production" else None
)

# CORS Configuration
origins = [
    "http://localhost:3000",     # React dev server
    "http://127.0.0.1:3000",     # React dev server (alternative)
    "http://localhost:21015",    # Frontend production port
    "http://127.0.0.1:21015",    # Frontend production port (alternative)
    "https://samfms.local",      # Local HTTPS
]

# Add environment-specific origins
if config.environment.value == "development":
    origins.extend([
        "http://localhost:*",
        "http://127.0.0.1:*",
        "https://hoppscotch.io",     # Hoppscotch web app
        "http://localhost:3100",     # Hoppscotch local
        "http://127.0.0.1:3100"      # Hoppscotch local alternative
    ])
    # For development, allow all origins for API testing
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# Setup API routes
logger.info("🛣️  Setting up simplified service routing...")

# Import auth routes (essential)
try:
    from routes.auth import router as auth_router
    app.include_router(auth_router)
    logger.info("✅ Auth routes configured")
except ImportError as e:
    logger.error(f"❌ Failed to import auth routes: {e}")
    # Auth routes are essential, so we should raise an error
    raise SystemExit(f"Critical error: Auth routes are required but could not be imported: {e}")

# Import simplified service routing
try:
    from routes.service_routing import service_router
    app.include_router(service_router)
    logger.info("✅ Simplified service routing configured")
    logger.info("    • /management/* -> Management service block")
    logger.info("    • /maintenance/* -> Maintenance service block")
    logger.info("    • /gps/* -> GPS service block")
    logger.info("    • /trips/* -> Trip planning service block")
except ImportError as e:
    logger.error(f"❌ Failed to import service routing: {e}")
    logger.warning("⚠️  Falling back to direct routes...")
    
    # Fallback to direct routes if service routing fails
    try:
        from routes.gps_direct import router as gps_router
        app.include_router(gps_router)
        logger.info("✅ Direct GPS routes configured as fallback")
    except ImportError as gps_error:
        logger.warning(f"⚠️  Direct GPS routes also failed: {gps_error}")

# Import direct vehicle routes for frontend compatibility
try:
    from routes.api import api_router
    app.include_router(api_router)
    logger.info("✅ Direct vehicle routes configured for frontend compatibility")
    logger.info("    • /vehicles/* -> Vehicle management routes")
except ImportError as e:
    logger.error(f"❌ Failed to import direct vehicle routes: {e}")
    logger.warning("⚠️  Frontend vehicle routes will not be available")

# Import debug routes if in development
if config.environment.value == "development":
    try:
        from routes.debug import router as debug_router
        app.include_router(debug_router)
        logger.info("✅ Debug routes configured for development")
    except ImportError as e:
        logger.warning(f"⚠️  Debug routes could not be imported: {e}")

# Add a simple test route to verify routing works
@app.get("/test-auth")
async def test_auth_route():
    """Simple test route to verify routing works"""
    return {"message": "Test auth route works", "timestamp": datetime.utcnow().isoformat()}

# Basic exception handler for startup
@app.exception_handler(Exception)
async def basic_exception_handler(request: Request, exc: Exception):
    """Basic exception handler until enhanced handlers are loaded"""
    logger.error(f"Unhandled exception: {exc}")
    return {"error": "Internal server error", "message": str(exc)}

# Health check endpoint
@app.get("/health")
async def health_check():
    """Enhanced health check with detailed status"""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "samfms-core",
            "version": "1.0.0",
            "environment": config.environment.value,
            "uptime_seconds": None
        }
        
        # Calculate uptime
        if hasattr(app.state, 'startup_time'):
            uptime = (datetime.utcnow() - app.state.startup_time).total_seconds()
            health_status["uptime_seconds"] = uptime
        
        # Check database health
        if hasattr(app.state, 'db_manager'):
            db_health = await app.state.db_manager.health_check()
            health_status["database"] = db_health
        
        # Check service discovery
        try:
            from common.service_discovery import get_service_discovery
            service_discovery = await get_service_discovery()
            services = await service_discovery.get_healthy_services()
            health_status["service_discovery"] = {
                "status": "healthy",
                "registered_services": len(services)
            }
        except Exception:
            health_status["service_discovery"] = {"status": "unavailable"}
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "SAMFMS Core Service",
        "version": "1.0.0",
        "description": "Enhanced Central API Gateway for South African Fleet Management System",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": config.environment.value,
        "routing": {
            "management": "/management/* -> Management service block",
            "maintenance": "/maintenance/* -> Maintenance service block", 
            "gps": "/gps/* -> GPS service block",
            "trips": "/trips/* -> Trip planning service block"
        },
        "endpoints": {
            "health": "/health",
            "docs": "/docs" if config.environment.value != "production" else "disabled",
            "auth": "/auth",
            "services": "/services",
            "debug": "/debug" if config.environment.value != "production" else "disabled"
        }
    }

# Service information endpoint
@app.get("/info")
async def service_info():
    """Detailed service information"""
    info = {
        "service": "samfms-core",
        "version": "1.0.0",
        "environment": config.environment.value,
        "timestamp": datetime.utcnow().isoformat(),
        "configuration": {
            "database": {
                "name": config.database.name,
                "max_pool_size": config.database.max_pool_size,
                "min_pool_size": config.database.min_pool_size
            },
            "security": {
                "jwt_algorithm": config.security.jwt_algorithm,
                "token_expire_minutes": config.security.access_token_expire_minutes
            }
        }
    }
    
    if hasattr(app.state, 'startup_time'):
        info["startup_time"] = app.state.startup_time.isoformat()
        info["uptime_seconds"] = (datetime.utcnow() - app.state.startup_time).total_seconds()
    
    return info

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.core_port,
        reload=config.environment.value == "development",
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )