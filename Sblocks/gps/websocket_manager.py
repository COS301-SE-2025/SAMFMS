"""
WebSocket Manager for Real-time GPS Tracking

Handles WebSocket connections for live location streaming.
"""

from typing import Dict, List, Set
import json
import asyncio
import logging
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect
from models.location import VehicleLocation
from config.settings import get_settings

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time location updates"""
    
    def __init__(self):
        # Store active connections by vehicle_id
        self.vehicle_connections: Dict[str, Set[WebSocket]] = {}
        # Store connections for all vehicles (admin/fleet view)
        self.fleet_connections: Set[WebSocket] = set()
        # Store connections by geofence_id for geofence alerts
        self.geofence_connections: Dict[str, Set[WebSocket]] = {}
        self.settings = get_settings()
    
    async def connect_vehicle(self, websocket: WebSocket, vehicle_id: str):
        """Connect to receive updates for a specific vehicle"""
        await websocket.accept()
        
        if vehicle_id not in self.vehicle_connections:
            self.vehicle_connections[vehicle_id] = set()
        
        self.vehicle_connections[vehicle_id].add(websocket)
        logger.info(f"Client connected to vehicle {vehicle_id} updates")
        
        # Send initial connection confirmation
        await self.send_to_vehicle(vehicle_id, {
            "type": "connection_established",
            "vehicle_id": vehicle_id,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Connected to vehicle tracking"
        })
    
    async def connect_fleet(self, websocket: WebSocket):
        """Connect to receive updates for all vehicles"""
        await websocket.accept()
        self.fleet_connections.add(websocket)
        logger.info("Client connected to fleet tracking")
        
        # Send initial connection confirmation
        await self.send_to_fleet({
            "type": "connection_established",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Connected to fleet tracking"
        })
    
    async def connect_geofence(self, websocket: WebSocket, geofence_id: str):
        """Connect to receive geofence alerts"""
        await websocket.accept()
        
        if geofence_id not in self.geofence_connections:
            self.geofence_connections[geofence_id] = set()
        
        self.geofence_connections[geofence_id].add(websocket)
        logger.info(f"Client connected to geofence {geofence_id} alerts")
        
        await self.send_to_geofence(geofence_id, {
            "type": "connection_established",
            "geofence_id": geofence_id,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Connected to geofence alerts"
        })
    
    def disconnect_vehicle(self, websocket: WebSocket, vehicle_id: str):
        """Disconnect from vehicle updates"""
        if vehicle_id in self.vehicle_connections:
            self.vehicle_connections[vehicle_id].discard(websocket)
            if not self.vehicle_connections[vehicle_id]:
                del self.vehicle_connections[vehicle_id]
        logger.info(f"Client disconnected from vehicle {vehicle_id} updates")
    
    def disconnect_fleet(self, websocket: WebSocket):
        """Disconnect from fleet updates"""
        self.fleet_connections.discard(websocket)
        logger.info("Client disconnected from fleet tracking")
    
    def disconnect_geofence(self, websocket: WebSocket, geofence_id: str):
        """Disconnect from geofence alerts"""
        if geofence_id in self.geofence_connections:
            self.geofence_connections[geofence_id].discard(websocket)
            if not self.geofence_connections[geofence_id]:
                del self.geofence_connections[geofence_id]
        logger.info(f"Client disconnected from geofence {geofence_id} alerts")
    
    async def send_to_vehicle(self, vehicle_id: str, data: dict):
        """Send data to all clients subscribed to a specific vehicle"""
        if vehicle_id not in self.vehicle_connections:
            return
        
        disconnected = set()
        for websocket in self.vehicle_connections[vehicle_id].copy():
            try:
                await websocket.send_text(json.dumps(data))
            except Exception as e:
                logger.error(f"Error sending to vehicle {vehicle_id} websocket: {e}")
                disconnected.add(websocket)
        
        # Remove disconnected websockets
        for websocket in disconnected:
            self.vehicle_connections[vehicle_id].discard(websocket)
    
    async def send_to_fleet(self, data: dict):
        """Send data to all fleet monitoring clients"""
        disconnected = set()
        for websocket in self.fleet_connections.copy():
            try:
                await websocket.send_text(json.dumps(data))
            except Exception as e:
                logger.error(f"Error sending to fleet websocket: {e}")
                disconnected.add(websocket)
        
        # Remove disconnected websockets
        for websocket in disconnected:
            self.fleet_connections.discard(websocket)
    
    async def send_to_geofence(self, geofence_id: str, data: dict):
        """Send data to all clients subscribed to geofence alerts"""
        if geofence_id not in self.geofence_connections:
            return
        
        disconnected = set()
        for websocket in self.geofence_connections[geofence_id].copy():
            try:
                await websocket.send_text(json.dumps(data))
            except Exception as e:
                logger.error(f"Error sending to geofence {geofence_id} websocket: {e}")
                disconnected.add(websocket)
        
        # Remove disconnected websockets
        for websocket in disconnected:
            self.geofence_connections[geofence_id].discard(websocket)
    
    async def broadcast_location_update(self, location: VehicleLocation):
        """Broadcast location update to relevant subscribers"""
        data = {
            "type": "location_update",
            "vehicle_id": location.vehicle_id,
            "latitude": location.latitude,
            "longitude": location.longitude,
            "speed": location.speed,
            "heading": location.heading,
            "accuracy": location.accuracy,
            "timestamp": location.timestamp.isoformat(),
            "status": location.status
        }
        
        # Send to vehicle-specific subscribers
        await self.send_to_vehicle(location.vehicle_id, data)
        
        # Send to fleet subscribers
        await self.send_to_fleet(data)
    
    async def broadcast_geofence_event(self, geofence_id: str, vehicle_id: str, event_type: str, data: dict):
        """Broadcast geofence event to relevant subscribers"""
        event_data = {
            "type": "geofence_event",
            "geofence_id": geofence_id,
            "vehicle_id": vehicle_id,
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            **data
        }
        
        # Send to geofence subscribers
        await self.send_to_geofence(geofence_id, event_data)
        
        # Send to vehicle subscribers
        await self.send_to_vehicle(vehicle_id, event_data)
        
        # Send to fleet subscribers
        await self.send_to_fleet(event_data)
    
    async def broadcast_route_event(self, route_id: str, vehicle_id: str, event_type: str, data: dict):
        """Broadcast route event to relevant subscribers"""
        event_data = {
            "type": "route_event",
            "route_id": route_id,
            "vehicle_id": vehicle_id,
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            **data
        }
        
        # Send to vehicle subscribers
        await self.send_to_vehicle(vehicle_id, event_data)
        
        # Send to fleet subscribers
        await self.send_to_fleet(event_data)
    
    async def send_emergency_alert(self, vehicle_id: str, alert_data: dict):
        """Send emergency alert to all relevant subscribers"""
        data = {
            "type": "emergency_alert",
            "priority": "high",
            "vehicle_id": vehicle_id,
            "timestamp": datetime.utcnow().isoformat(),
            **alert_data
        }
        
        # Send to vehicle subscribers
        await self.send_to_vehicle(vehicle_id, data)
        
        # Send to fleet subscribers (emergency alerts go to fleet monitoring)
        await self.send_to_fleet(data)
    
    def get_connection_stats(self) -> dict:
        """Get statistics about current connections"""
        return {
            "vehicle_connections": {
                vehicle_id: len(connections) 
                for vehicle_id, connections in self.vehicle_connections.items()
            },
            "fleet_connections": len(self.fleet_connections),
            "geofence_connections": {
                geofence_id: len(connections)
                for geofence_id, connections in self.geofence_connections.items()
            },
            "total_connections": (
                sum(len(connections) for connections in self.vehicle_connections.values()) +
                len(self.fleet_connections) +
                sum(len(connections) for connections in self.geofence_connections.values())
            )
        }


# Global connection manager instance
connection_manager = ConnectionManager()


class WebSocketService:
    """Service for handling WebSocket operations"""
    
    def __init__(self):
        self.manager = connection_manager
    
    async def handle_vehicle_websocket(self, websocket: WebSocket, vehicle_id: str):
        """Handle WebSocket connection for vehicle tracking"""
        await self.manager.connect_vehicle(websocket, vehicle_id)
        try:
            while True:
                # Keep connection alive and handle any incoming messages
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle ping/keepalive
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                
        except WebSocketDisconnect:
            self.manager.disconnect_vehicle(websocket, vehicle_id)
        except Exception as e:
            logger.error(f"Error in vehicle websocket: {e}")
            self.manager.disconnect_vehicle(websocket, vehicle_id)
    
    async def handle_fleet_websocket(self, websocket: WebSocket):
        """Handle WebSocket connection for fleet tracking"""
        await self.manager.connect_fleet(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                
        except WebSocketDisconnect:
            self.manager.disconnect_fleet(websocket)
        except Exception as e:
            logger.error(f"Error in fleet websocket: {e}")
            self.manager.disconnect_fleet(websocket)
    
    async def handle_geofence_websocket(self, websocket: WebSocket, geofence_id: str):
        """Handle WebSocket connection for geofence alerts"""
        await self.manager.connect_geofence(websocket, geofence_id)
        try:
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                
        except WebSocketDisconnect:
            self.manager.disconnect_geofence(websocket, geofence_id)
        except Exception as e:
            logger.error(f"Error in geofence websocket: {e}")
            self.manager.disconnect_geofence(websocket, geofence_id)
