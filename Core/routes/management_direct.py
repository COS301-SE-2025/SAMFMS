"""
Management service routes for Core service
Temporary direct routes to management service (should eventually go through service proxy)
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from services.request_router import request_router

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Management Direct"])

@router.get("/vehicles")
async def get_vehicles_direct(limit: int = 100):
    """Temporary direct vehicles endpoint to test routing"""
    try:
        logger.info(f"Direct vehicles endpoint called with limit: {limit}")
        
        # Try to route to management service directly
        correlation_id = str(uuid.uuid4())
        test_message = {
            "correlation_id": correlation_id,
            "endpoint": "/vehicles",
            "method": "GET",
            "data": {"limit": limit},
            "user_context": {"user_id": "test_user", "permissions": ["*"]},
            "timestamp": datetime.utcnow().isoformat(),
            "service": "management",
            "trace_id": correlation_id
        }
        
        # Test communication with management service
        try:
            response = await asyncio.wait_for(
                request_router.send_request_and_wait("management", test_message, correlation_id),
                timeout=10.0
            )
            logger.info("✅ Got response from management service")
            return response
            
        except asyncio.TimeoutError:
            logger.error("❌ Timeout waiting for management service")
            return {
                "vehicles": [],
                "total": 0,
                "error": "Management service timeout",
                "fallback": True
            }
        except Exception as e:
            logger.error(f"❌ Error communicating with management service: {e}")
            return {
                "vehicles": [
                    {
                        "id": "test-1",
                        "make": "Toyota",
                        "model": "Corolla",
                        "year": "2020",
                        "status": "Active",
                        "driver": "Test Driver"
                    }
                ],
                "total": 1,
                "error": f"Communication error: {str(e)}",
                "fallback": True
            }
            
    except Exception as e:
        logger.error(f"Error in direct vehicles endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/drivers")
async def get_drivers(limit: int = 100):
    """Fetch drivers from the management service"""
    try:
        logger.info(f"Direct drivers endpoint called with limit: {limit}")
        correlation_id = str(uuid.uuid4())
        test_message = {
            "correlation_id": correlation_id,
            "endpoint": "/drivers",
            "method": "GET",
            "data": {"limit": limit},
            "user_context": {"user_id": "test_user", "permissions": ["read:drivers"]},
            "timestamp": datetime.utcnow().isoformat(),
            "service": "management",
            "trace_id": correlation_id
        }
        response = await asyncio.wait_for(
            request_router.send_request_and_wait("management", test_message, correlation_id),
            timeout=10.0
        )
        logger.info("✅ Got response from management service for drivers")
        return response
    except asyncio.TimeoutError:
        logger.error("❌ Timeout waiting for management service (drivers)")
        return {
            "drivers": [],
            "total": 0,
            "error": "Management service timeout",
            "fallback": True
        }
    except Exception as e:
        logger.error(f"❌ Error communicating with management service (drivers): {e}")
        return {
            "drivers": [],
            "total": 0,
            "error": f"Communication error: {str(e)}",
            "fallback": True
        }

@router.put("/drivers/{driver_id}")
async def update_driver(driver_id: str, driver_data: dict):
    """Update a driver by forwarding the request to the management service"""
    try:
        logger.info(f"Update driver endpoint called for driver_id: {driver_id}")
        correlation_id = str(uuid.uuid4())
        test_message = {
            "correlation_id": correlation_id,
            "endpoint": f"/drivers/{driver_id}",
            "method": "PUT",
            "data": driver_data,
            "user_context": {"user_id": "test_user", "permissions": ["edit:drivers"]},
            "timestamp": datetime.utcnow().isoformat(),
            "service": "management",
            "trace_id": correlation_id
        }
        response = await asyncio.wait_for(
            request_router.send_request_and_wait("management", test_message, correlation_id),
            timeout=10.0
        )
        logger.info("✅ Got response from management service for driver update")
        return response
    except asyncio.TimeoutError:
        logger.error("❌ Timeout waiting for management service (driver update)")
        return {
            "status": "error",
            "error": "Management service timeout",
            "fallback": True
        }
    except Exception as e:
        logger.error(f"❌ Error communicating with management service (driver update): {e}")
        return {
            "status": "error",
            "error": f"Communication error: {str(e)}",
            "fallback": True
        }
