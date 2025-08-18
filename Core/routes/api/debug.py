"""
Debug and Testing Routes - Consolidated
Contains endpoints for debugging, testing, and service management functionality
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from services.request_router import request_router
from database import db
from common.service_discovery import get_service_discovery

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Debug & Testing"])

class ServiceRegistrationRequest(BaseModel):
    """Service registration request model"""
    name: str
    host: str
    port: int
    version: str = "1.0.0"
    protocol: str = "http"
    health_check_url: str = "/health"
    tags: list = []
    metadata: dict = {}

# =============================================================================
# SERVICE MANAGEMENT ENDPOINTS
# =============================================================================

@router.post("/api/services/register")
async def register_service(registration: ServiceRegistrationRequest):
    """Register a service with the Core's service discovery"""
    try:
        service_discovery = await get_service_discovery()
        
        await service_discovery.register_service(
            name=registration.name,
            host=registration.host,
            port=registration.port,
            version=registration.version,
            protocol=registration.protocol,
            health_check_url=registration.health_check_url,
            tags=registration.tags,
            metadata=registration.metadata
        )
        
        logger.info(f"🔧 Registered service: {registration.name} at {registration.host}:{registration.port}")
        
        return {
            "status": "success",
            "message": f"Service {registration.name} registered successfully",
            "service_info": {
                "name": registration.name,
                "base_url": f"{registration.protocol}://{registration.host}:{registration.port}",
                "registered_at": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to register service {registration.name}: {e}")
        raise HTTPException(status_code=500, detail=f"Service registration failed: {str(e)}")

@router.get("/api/services")
async def get_registered_services():
    """Get list of registered services"""
    try:
        service_discovery = await get_service_discovery()
        services = await service_discovery.get_all_services()
        
        return {
            "status": "success",
            "services": services,
            "total": len(services)
        }
        
    except Exception as e:
        logger.error(f"Failed to get registered services: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get services: {str(e)}")

@router.delete("/api/services/{service_name}")
async def deregister_service(service_name: str):
    """Deregister a service"""
    try:
        service_discovery = await get_service_discovery()
        await service_discovery.deregister_service(service_name)
        
        logger.info(f"🗑️ Deregistered service: {service_name}")
        
        return {
            "status": "success",
            "message": f"Service {service_name} deregistered successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to deregister service {service_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Service deregistration failed: {str(e)}")

@router.get("/service_presence")
async def service_presence():
    """Get list of registered services from database"""
    try:
        services = await db.get_collection("service_presence").find(
            {}, {"service": 1, "_id": 0}
        ).to_list(length=None)
        service_names = [service.get("service", service.get("service_name", "unknown")) for service in services]
        return service_names
    except Exception as e:
        logger.error(f"Error fetching service presence: {e}")
        return {"error": f"Failed to fetch service presence: {str(e)}"}

# =============================================================================
# ROUTING DEBUG ENDPOINTS
# =============================================================================

@router.get("/debug/routing/{endpoint:path}")
async def debug_routing(endpoint: str):
    """Debug endpoint to test routing configuration"""
    try:
        service = request_router.get_service_for_endpoint(f"/{endpoint}")
        return {
            "endpoint": f"/{endpoint}",
            "service": service,
            "routing_map": request_router.routing_map
        }
    except Exception as e:
        return {
            "endpoint": f"/{endpoint}",
            "error": str(e),
            "routing_map": request_router.routing_map
        }

@router.get("/debug/routes")
async def debug_routes(request: Request):
    """Debug endpoint to check what routes are registered"""
    routes_info = []
    app = request.app
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            routes_info.append({
                "path": route.path,
                "methods": list(route.methods) if route.methods else [],
                "name": getattr(route, 'name', 'unknown')
            })
    
    return {
        "total_routes": len(routes_info),
        "routes": routes_info,
        "api_routes": [r for r in routes_info if r["path"].startswith("/api")]
    }

@router.get("/debug/health")
async def debug_health():
    """Debug health check endpoint"""
    return {
        "status": "healthy",
        "service": "core-debug",
        "routing_available": hasattr(request_router, 'routing_map'),
        "services": getattr(request_router, 'routing_map', {})
    }

# =============================================================================
# TESTING ENDPOINTS
# =============================================================================

@router.get("/test/simple")
async def simple_test():
    """Simple test endpoint to verify /api routing works"""
    return {
        "status": "success", 
        "message": "API routing is working", 
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/test/connection")
async def test_service_connection():
    """Test endpoint to verify Core to Management service communication"""
    try:
        correlation_id = str(uuid.uuid4())
        test_message = {
            "correlation_id": correlation_id,
            "endpoint": "/api/drivers",
            "method": "GET",
            "data": {"limit": 1},
            "user_context": {"user_id": "test_user", "permissions": ["read:drivers"]},
            "timestamp": datetime.utcnow().isoformat(),
            "service": "management",
            "trace_id": correlation_id
        }
        
        # Test communication with management service
        response = await asyncio.wait_for(
            request_router.send_request_and_wait("management", test_message, correlation_id),
            timeout=10.0
        )
        
        return {
            "status": "success",
            "message": "Core to Management service communication working",
            "response_received": True,
            "data": response
        }
        
    except asyncio.TimeoutError:
        return {
            "status": "error",
            "message": "Timeout - Management service not responding",
            "response_received": False
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Communication error: {str(e)}",
            "response_received": False
        }

@router.get("/vehicles/direct")
async def get_vehicles_direct():
    """Direct vehicles endpoint for testing without service proxy"""
    try:
        correlation_id = str(uuid.uuid4())
        test_message = {
            "correlation_id": correlation_id,
            "endpoint": "/api/vehicles",
            "method": "GET",
            "data": {"limit": 100},
            "user_context": {"user_id": "direct_test", "permissions": ["read:vehicles"]},
            "timestamp": datetime.utcnow().isoformat(),
            "service": "management",
            "trace_id": correlation_id
        }
        
        # Test direct communication with management service
        response = await asyncio.wait_for(
            request_router.send_request_and_wait("management", test_message, correlation_id),
            timeout=30.0
        )
        
        return response
        
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Management service timeout")
    except Exception as e:
        logger.error(f"Direct vehicles request failed: {e}")
        raise HTTPException(status_code=500, detail=f"Service error: {str(e)}")
