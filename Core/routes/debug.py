"""
Debug and testing routes for Core service
Contains endpoints for debugging and testing functionality
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from services.request_router import request_router
from database import db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Debug & Testing"])

@router.get("/debug/routes")
async def debug_routes(request):
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

@router.get("/service_presence")
async def service_presence():
    """Get list of registered services"""
    try:
        services = await db.get_collection("service_presence").find(
            {}, {"service": 1, "_id": 0}
        ).to_list(length=None)
        service_names = [service.get("service", service.get("service_name", "unknown")) for service in services]
        return service_names
    except Exception as e:
        logger.error(f"Error fetching service presence: {e}")
        return {"error": f"Failed to fetch service presence: {str(e)}"}
