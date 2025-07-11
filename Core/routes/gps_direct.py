"""
GPS-specific routes for direct communication with GPS service
These routes handle real-time GPS data requests
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Body, HTTPException
import aio_pika

from rabbitmq.producer import publish_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gps", tags=["GPS Direct"])

@router.post("/request_location")
async def request_gps_location(parameter: dict = Body(...)):
    """Request location data from GPS service"""
    try:
        await publish_message(
            "gps_requests_Direct",
            aio_pika.ExchangeType.DIRECT,
            {
                "operation": "retrieve",
                "type": "location",
                "parameters": parameter
            },
            routing_key="gps_requests_Direct"
        )
        return {"status": "Location request sent to GPS service"}
    except Exception as e:
        logger.error(f"Error requesting GPS location: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send location request: {str(e)}")

@router.post("/request_speed")
async def request_gps_speed(vehicle_id: str):
    """Request speed data from GPS service"""
    try:
        await publish_message(
            "gps_requests_Direct",
            aio_pika.ExchangeType.DIRECT,
            {
                "operation": "retrieve",
                "type": "speed",
                "vehicle_id": vehicle_id
            },
            routing_key="gps_requests_Direct"
        )
        return {"status": "Speed request sent to GPS service"}
    except Exception as e:
        logger.error(f"Error requesting GPS speed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send speed request: {str(e)}")

@router.post("/request_direction")
async def request_gps_direction(vehicle_id: str):
    """Request direction data from GPS service"""
    try:
        await publish_message(
            "gps_requests_Direct",
            aio_pika.ExchangeType.DIRECT,
            {
                "operation": "retrieve",
                "type": "direction",
                "vehicle_id": vehicle_id
            },
            routing_key="gps_requests_Direct"
        )
        return {"status": "Direction request sent to GPS service"}
    except Exception as e:
        logger.error(f"Error requesting GPS direction: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send direction request: {str(e)}")

@router.post("/request_fuel_level")
async def request_gps_fuel_level(vehicle_id: str):
    """Request fuel level data from GPS service"""
    try:
        await publish_message(
            "gps_requests_Direct",
            aio_pika.ExchangeType.DIRECT,
            {
                "operation": "retrieve",
                "type": "fuel_level",
                "vehicle_id": vehicle_id
            },
            routing_key="gps_requests_Direct"
        )
        return {"status": "Fuel level request sent to GPS service"}
    except Exception as e:
        logger.error(f"Error requesting GPS fuel level: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send fuel level request: {str(e)}")

@router.post("/request_last_update")
async def request_gps_last_update(vehicle_id: str):
    """Request last update timestamp from GPS service"""
    try:
        await publish_message(
            "gps_requests_Direct",
            aio_pika.ExchangeType.DIRECT,
            {
                "operation": "retrieve",
                "type": "last_update",
                "vehicle_id": vehicle_id
            },
            routing_key="gps_requests_Direct"
        )
        return {"status": "Last update request sent to GPS service"}
    except Exception as e:
        logger.error(f"Error requesting GPS last update: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send last update request: {str(e)}")
