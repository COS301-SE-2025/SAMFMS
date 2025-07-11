"""
WebSocket routes for real-time communication
"""

import logging
from fastapi import APIRouter, WebSocket, Body
from websockets.vehicle_tracking import vehicle_websocket

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])

@router.websocket("/ws/vehicles")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time vehicle tracking"""
    logger.info("WebSocket connection requested")
    
    await vehicle_websocket.connect(websocket)
    logger.info("WebSocket connection accepted and ready to send data.")
    
    await vehicle_websocket.send_vehicle_updates(websocket)

@router.get("/test/live_vehicles")
async def test_live_vehicles():
    """Test endpoint to fetch live vehicle data using get_live_vehicle_data()"""
    vehicles = await vehicle_websocket.get_live_vehicle_data()
    return {"vehicles": vehicles}

@router.post("/api/gps/geofences/circle")
async def add_new_geofence(parameter: dict = Body(...)):
    """Create a new circular geofence"""
    geofence = await vehicle_websocket.create_geofence(parameter)
    return geofence
