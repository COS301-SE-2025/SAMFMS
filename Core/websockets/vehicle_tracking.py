"""
WebSocket handler for real-time vehicle tracking
Separated from main.py for better organization
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any

from fastapi import WebSocket, WebSocketDisconnect
import aio_pika

from rabbitmq.producer import publish_message

logger = logging.getLogger(__name__)

class VehicleTrackingWebSocket:
    """Handles WebSocket connections for vehicle tracking"""
    
    def __init__(self):
        self.pending_futures: Dict[str, asyncio.Future] = {}
        self.pending_geofence_futures: Dict[str, asyncio.Future] = {}
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connection accepted. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_vehicle_updates(self, websocket: WebSocket):
        """Send real-time vehicle updates to a WebSocket connection"""
        try:
            while True:
                try:
                    vehicles = await self.get_live_vehicle_data()
                    logger.info(f"Sending to frontend: {vehicles}")
                    await websocket.send_json({"vehicles": vehicles})
                    await asyncio.sleep(2)  # Update every 2 seconds
                except WebSocketDisconnect:
                    logger.info("WebSocket disconnected")
                    self.disconnect(websocket)
                    break
                except Exception as e:
                    logger.error(f"Error in WebSocket loop: {e}")
                    try:
                        await websocket.send_json({"error": str(e)})
                    except Exception:
                        logger.error("Failed to send error message to WebSocket (likely closed).")
                        self.disconnect(websocket)
                        break
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"WebSocket endpoint error: {e}")
            self.disconnect(websocket)
    
    async def get_live_vehicle_data(self) -> list:
        """Request live vehicle data from GPS service"""
        correlation_id = str(uuid.uuid4())
        loop = asyncio.get_event_loop()
        future = loop.create_future()

        # Store the future so response handler can access it
        self.pending_futures[correlation_id] = future

        # Publish the request with the correlation_id
        await publish_message(
            "gps_requests_Direct",
            aio_pika.ExchangeType.DIRECT,
            {
                "operation": "retrieve_live_locations",
                "type": "location",
                "correlation_id": correlation_id
            },
            routing_key="gps_requests_Direct"
        )

        try:
            vehicles = await asyncio.wait_for(future, timeout=5)
            logger.info(f"Vehicle live location data received: {vehicles}")
            return vehicles
        except asyncio.TimeoutError:
            logger.warning("Timeout waiting for GPS SBlock response")
            # Clean up the future if it timed out
            self.pending_futures.pop(correlation_id, None)
            return []
    
    async def handle_vehicle_response(self, message):
        """Handle response from GPS service for vehicle locations"""
        try:
            body = message.body.decode()
            data = json.loads(body)
            logger.info(f"Data from GPS message: {data}")
            
            correlation_id = data.get("correlation_id")
            if correlation_id in self.pending_futures:
                self.pending_futures[correlation_id].set_result(data.get("vehicles", []))
                del self.pending_futures[correlation_id]
        except Exception as e:
            logger.error(f"Error handling vehicle response: {e}")
    
    async def handle_geofence_response(self, message):
        """Handle response from GPS service for geofences"""
        try:
            logger.info(f"Pending geofence futures: {self.pending_geofence_futures.keys()}")
            body = message.body.decode()
            data = json.loads(body)
            logger.info(f"Message received from GPS about Geofence: {data}")
            
            correlation_id = data.get("correlation_id")
            geofence = data.get("geofence")
            
            if geofence == "failed":
                logger.warning("Geofence operation failed")
                if correlation_id in self.pending_geofence_futures:
                    del self.pending_geofence_futures[correlation_id]
            else:
                logger.info("Geofence operation successful")
                if correlation_id in self.pending_geofence_futures:
                    self.pending_geofence_futures[correlation_id].set_result(geofence)
                    del self.pending_geofence_futures[correlation_id]
        except Exception as e:
            logger.error(f"Error handling geofence response: {e}")
    
    async def create_geofence(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new geofence"""
        logger.info(f"Add geofence request received: {parameters}")
        correlation_id = str(uuid.uuid4())
        loop = asyncio.get_event_loop()
        future = loop.create_future()

        self.pending_geofence_futures[correlation_id] = future

        await publish_message(
            "gps_requests_Direct",
            aio_pika.ExchangeType.DIRECT,
            {
                "operation": "add_new_geofence",
                "parameters": parameters,
                "correlation_id": correlation_id
            },
            routing_key="gps_requests_Direct"
        )

        try:
            geofence = await asyncio.wait_for(future, timeout=15)
            logger.info(f"Geofence information received: {geofence}")
            return geofence
        except asyncio.TimeoutError:
            logger.warning("Timeout waiting for GPS SBlock geofence response")
            self.pending_geofence_futures.pop(correlation_id, None)
            return {"error": "Timeout creating geofence"}

# Global instance
vehicle_websocket = VehicleTrackingWebSocket()
