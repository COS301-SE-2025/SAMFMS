"""
Route Service for GPS Tracking System

Handles route management, tracking, and analytics.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId
import logging

from models.route import VehicleRoute, RoutePoint, RouteStatus, RouteEvent
from models.location import VehicleLocation
from database import get_database
from messaging.rabbitmq_client import RabbitMQClient
from config.settings import get_settings

logger = logging.getLogger(__name__)


class RouteService:
    """Service for managing vehicle routes and route tracking"""
    
    def __init__(self):
        self.settings = get_settings()
        self.db = None
        self.messaging = None
    
    async def initialize(self):
        """Initialize database and messaging connections"""
        self.db = await get_database()
        self.messaging = RabbitMQClient()
        await self.messaging.connect()
    
    async def create_route(self, route_data: Dict[str, Any]) -> VehicleRoute:
        """Create a new vehicle route"""
        try:
            # Create route object
            route = VehicleRoute(**route_data)
            
            # Save to database
            route_dict = route.dict()
            route_dict["_id"] = ObjectId()
            route_dict["created_at"] = datetime.utcnow()
            route_dict["updated_at"] = datetime.utcnow()
            
            result = await self.db.routes.insert_one(route_dict)
            route.id = str(result.inserted_id)
            
            # Publish route created event
            await self.messaging.publish_event(
                "route.created",
                {
                    "route_id": route.id,
                    "vehicle_id": route.vehicle_id,
                    "trip_id": route.trip_id,
                    "status": route.status,
                    "created_at": route_dict["created_at"].isoformat()
                }
            )
            
            logger.info(f"Created route {route.id} for vehicle {route.vehicle_id}")
            return route
            
        except Exception as e:
            logger.error(f"Error creating route: {str(e)}")
            raise
    
    async def get_route(self, route_id: str) -> Optional[VehicleRoute]:
        """Get route by ID"""
        try:
            route_doc = await self.db.routes.find_one({"_id": ObjectId(route_id)})
            if route_doc:
                route_doc["id"] = str(route_doc["_id"])
                return VehicleRoute(**route_doc)
            return None
        except Exception as e:
            logger.error(f"Error getting route {route_id}: {str(e)}")
            return None
    
    async def get_vehicle_routes(
        self, 
        vehicle_id: str, 
        status: Optional[RouteStatus] = None,
        limit: int = 100
    ) -> List[VehicleRoute]:
        """Get routes for a specific vehicle"""
        try:
            query = {"vehicle_id": vehicle_id}
            if status:
                query["status"] = status
            
            cursor = self.db.routes.find(query).sort("created_at", -1).limit(limit)
            routes = []
            
            async for route_doc in cursor:
                route_doc["id"] = str(route_doc["_id"])
                routes.append(VehicleRoute(**route_doc))
            
            return routes
        except Exception as e:
            logger.error(f"Error getting routes for vehicle {vehicle_id}: {str(e)}")
            return []
    
    async def update_route_status(self, route_id: str, status: RouteStatus) -> bool:
        """Update route status"""
        try:
            result = await self.db.routes.update_one(
                {"_id": ObjectId(route_id)},
                {
                    "$set": {
                        "status": status,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                # Get route details for event
                route = await self.get_route(route_id)
                if route:
                    await self.messaging.publish_event(
                        "route.status_updated",
                        {
                            "route_id": route_id,
                            "vehicle_id": route.vehicle_id,
                            "status": status,
                            "updated_at": datetime.utcnow().isoformat()
                        }
                    )
                logger.info(f"Updated route {route_id} status to {status}")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error updating route status: {str(e)}")
            return False
    
    async def add_route_point(self, route_id: str, location: VehicleLocation) -> bool:
        """Add a location point to route tracking"""
        try:
            route_point = RoutePoint(
                latitude=location.latitude,
                longitude=location.longitude,
                timestamp=location.timestamp,
                speed=location.speed,
                heading=location.heading
            )
            
            result = await self.db.routes.update_one(
                {"_id": ObjectId(route_id)},
                {
                    "$push": {"route_points": route_point.dict()},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            if result.modified_count > 0:
                # Update route progress
                await self._update_route_progress(route_id, location)
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error adding route point: {str(e)}")
            return False
    
    async def _update_route_progress(self, route_id: str, location: VehicleLocation):
        """Update route progress based on current location"""
        try:
            route = await self.get_route(route_id)
            if not route or not route.waypoints:
                return
            
            # Calculate distance to destination
            destination = route.waypoints[-1]
            distance_to_destination = self._calculate_distance(
                location.latitude, location.longitude,
                destination.latitude, destination.longitude
            )
            
            # Update progress
            total_distance = route.total_distance or 100  # Default if not set
            progress = max(0, min(100, 100 - (distance_to_destination / total_distance * 100)))
            
            await self.db.routes.update_one(
                {"_id": ObjectId(route_id)},
                {
                    "$set": {
                        "current_progress": progress,
                        "distance_remaining": distance_to_destination,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Check if route is completed
            if distance_to_destination < 0.1:  # Within 100 meters
                await self.update_route_status(route_id, RouteStatus.COMPLETED)
            
        except Exception as e:
            logger.error(f"Error updating route progress: {str(e)}")
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in kilometers using Haversine formula"""
        import math
        
        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        return c * r
    
    async def get_route_analytics(self, route_id: str) -> Dict[str, Any]:
        """Get analytics for a specific route"""
        try:
            route = await self.get_route(route_id)
            if not route or not route.route_points:
                return {}
            
            points = route.route_points
            if len(points) < 2:
                return {"total_distance": 0, "average_speed": 0, "duration": 0}
            
            # Calculate total distance
            total_distance = 0
            for i in range(1, len(points)):
                total_distance += self._calculate_distance(
                    points[i-1].latitude, points[i-1].longitude,
                    points[i].latitude, points[i].longitude
                )
            
            # Calculate duration and average speed
            start_time = points[0].timestamp
            end_time = points[-1].timestamp
            duration = (end_time - start_time).total_seconds() / 3600  # hours
            
            avg_speed = total_distance / duration if duration > 0 else 0
            
            # Get speed statistics
            speeds = [p.speed for p in points if p.speed is not None]
            max_speed = max(speeds) if speeds else 0
            
            return {
                "route_id": route_id,
                "total_distance": round(total_distance, 2),
                "duration_hours": round(duration, 2),
                "average_speed": round(avg_speed, 2),
                "max_speed": max_speed,
                "points_count": len(points),
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting route analytics: {str(e)}")
            return {}
    
    async def add_route_event(self, route_id: str, event_type: str, description: str, data: Dict = None):
        """Add an event to a route"""
        try:
            event = RouteEvent(
                event_type=event_type,
                description=description,
                timestamp=datetime.utcnow(),
                data=data or {}
            )
            
            result = await self.db.routes.update_one(
                {"_id": ObjectId(route_id)},
                {
                    "$push": {"events": event.dict()},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            if result.modified_count > 0:
                # Publish route event
                await self.messaging.publish_event(
                    "route.event",
                    {
                        "route_id": route_id,
                        "event_type": event_type,
                        "description": description,
                        "timestamp": event.timestamp.isoformat(),
                        "data": data
                    }
                )
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error adding route event: {str(e)}")
            return False
    
    async def get_active_routes(self) -> List[VehicleRoute]:
        """Get all currently active routes"""
        try:
            cursor = self.db.routes.find({
                "status": {"$in": [RouteStatus.ACTIVE, RouteStatus.IN_PROGRESS]}
            }).sort("created_at", -1)
            
            routes = []
            async for route_doc in cursor:
                route_doc["id"] = str(route_doc["_id"])
                routes.append(VehicleRoute(**route_doc))
            
            return routes
        except Exception as e:
            logger.error(f"Error getting active routes: {str(e)}")
            return []
    
    async def delete_route(self, route_id: str) -> bool:
        """Delete a route"""
        try:
            route = await self.get_route(route_id)
            if not route:
                return False
            
            result = await self.db.routes.delete_one({"_id": ObjectId(route_id)})
            
            if result.deleted_count > 0:
                await self.messaging.publish_event(
                    "route.deleted",
                    {
                        "route_id": route_id,
                        "vehicle_id": route.vehicle_id,
                        "deleted_at": datetime.utcnow().isoformat()
                    }
                )
                logger.info(f"Deleted route {route_id}")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error deleting route: {str(e)}")
            return False
