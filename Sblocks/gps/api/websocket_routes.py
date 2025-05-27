"""
WebSocket API Routes for GPS Tracking System

Handles real-time WebSocket connections for live tracking.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from fastapi.websockets import WebSocketState
import logging

from ..websocket_manager import WebSocketService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websockets"])

# Initialize WebSocket service
websocket_service = WebSocketService()


@router.websocket("/vehicle/{vehicle_id}")
async def vehicle_tracking_websocket(websocket: WebSocket, vehicle_id: str):
    """
    WebSocket endpoint for real-time vehicle tracking
    
    Args:
        vehicle_id: ID of the vehicle to track
    """
    await websocket_service.handle_vehicle_websocket(websocket, vehicle_id)


@router.websocket("/fleet")
async def fleet_tracking_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time fleet tracking
    Receives updates for all vehicles
    """
    await websocket_service.handle_fleet_websocket(websocket)


@router.websocket("/geofence/{geofence_id}")
async def geofence_alerts_websocket(websocket: WebSocket, geofence_id: str):
    """
    WebSocket endpoint for real-time geofence alerts
    
    Args:
        geofence_id: ID of the geofence to monitor
    """
    await websocket_service.handle_geofence_websocket(websocket, geofence_id)


# REST endpoint to get WebSocket connection statistics
@router.get("/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics"""
    return websocket_service.manager.get_connection_stats()
