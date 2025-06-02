from fastapi import FastAPI, HTTPException
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
    
    logger.info("✅ Core service startup completed")
    
    yield
    
    # Shutdown
    logger.info("🛑 Core service shutting down...")
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

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint for the Core service."""
    logger.info("Root endpoint accessed")
    return {
        "message": "SAMFMS Core API is running",
        "service": "core",
        "version": "1.0.0",
        "status": "healthy"
    }

# Gateway endpoints for microservices
@app.get("/api/gateway/services", tags=["Gateway"])
async def get_microservices():
    """Get available microservices and their endpoints."""
    logger.info("Gateway services endpoint accessed")
    return {
        "services": {
            "security": {
                "description": "Authentication and security management",
                "base_url": "http://security:8000",
                "endpoints": {
                    "login": "/api/v1/auth/login",
                    "register": "/api/v1/auth/register",
                    "change_password": "/api/v1/auth/change-password"
                }
            },
            "users": {
                "description": "User profile data management",
                "base_url": "http://users:8000",
                "endpoints": {
                    "profiles": "/api/v1/users",
                    "preferences": "/api/v1/users/{user_id}/preferences"
                }
            },            "management": {
                "description": "Vehicle assignment, usage management, and driver management",
                "base_url": "http://management:8000",
                "endpoints": {
                    "assignments": "/api/v1/vehicles/assignments",
                    "usage": "/api/v1/vehicles/usage",
                    "status": "/api/v1/vehicles/status",
                    "drivers": "/api/v1/vehicles/drivers",
                    "driver_search": "/api/v1/vehicles/drivers/search/{query}"
                }
            },
            "vehicles": {
                "description": "Vehicle technical specifications and maintenance",
                "base_url": "http://vehicles:8000",
                "endpoints": {
                    "vehicles": "/api/v1/vehicles",
                    "maintenance": "/api/v1/vehicles/{vehicle_id}/maintenance",
                    "specifications": "/api/v1/vehicles/{vehicle_id}/specifications"
                }
            }
        },
        "message": "SAMFMS microservices architecture",
        "version": "2.0.0"
    }

@app.get("/api/gateway/health", tags=["Gateway"])
async def gateway_health_check():
    """Check health of all microservices."""
    import aiohttp
    import asyncio
    
    services = {
        "security": "http://security:8000/health",
        "users": "http://users:8000/health", 
        "management": "http://management:8000/health",
        "vehicles": "http://vehicles:8000/health"
    }
    
    async def check_service(name, url):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        return name, {"status": "healthy", "details": data}
                    else:
                        return name, {"status": "unhealthy", "error": f"HTTP {response.status}"}
        except Exception as e:
            return name, {"status": "unhealthy", "error": str(e)}
    
    # Check all services concurrently
    tasks = [check_service(name, url) for name, url in services.items()]
    results = await asyncio.gather(*tasks)
    
    service_health = dict(results)
    overall_healthy = all(service["status"] == "healthy" for service in service_health.values())
    
    return {
        "overall_status": "healthy" if overall_healthy else "degraded",
        "services": service_health,
        "timestamp": "2025-05-30T00:00:00Z"
    }

if __name__ == "__main__":
    logger.info("🚀 Starting Core service...")
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_config=None  # Use our custom logging configuration
    )
