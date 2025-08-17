"""
Location service for GPS tracking and history management
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId

from repositories.database import db_manager, db_manager_management
from schemas.entities import VehicleLocation, LocationHistory, TrackingSession
from events.publisher import event_publisher

logger = logging.getLogger(__name__)


class LocationService:
    """Service for managing vehicle locations and tracking"""
    
    def __init__(self):
        self.db = db_manager
        self.db_management = db_manager_management

    def _build_location_doc(self, vehicle_id: str, latitude: float, longitude: float,
                            altitude: Optional[float], speed: Optional[float],
                            heading: Optional[float], accuracy: Optional[float],
                            timestamp: datetime) -> dict:
        return {
            "vehicle_id": vehicle_id,
            "location": {
                "type": "Point",
                "coordinates": [longitude, latitude]
            },
            "latitude": latitude,
            "longitude": longitude,
            "altitude": altitude,
            "speed": speed,
            "heading": heading,
            "accuracy": accuracy,
            "timestamp": timestamp,
            "updated_at": datetime.utcnow()
        }
    
    async def delete_vehicle_location(self, vehicle_id: str) -> bool:
        """Delete a vehicle's current location by vehicle_id."""
        try:
            result = await self.db.db.vehicle_locations.delete_one({"vehicle_id": vehicle_id})
            if result.deleted_count > 0:
                logger.info(f"Deleted location for vehicle {vehicle_id}")
                return True
            else:
                logger.warning(f"No location found to delete for vehicle {vehicle_id}")
                return False
        except Exception as e:
            logger.error(f"Error deleting vehicle location for {vehicle_id}: {e}")
            raise


    async def create_vehicle_location(
        self,
        vehicle_id: str,
        latitude: float,
        longitude: float,
        altitude: Optional[float] = None,
        speed: Optional[float] = None,
        heading: Optional[float] = None,
        accuracy: Optional[float] = None,
        timestamp: Optional[datetime] = None
    ) -> VehicleLocation:
        """Add a vehicle's current location"""
        try:
            if not timestamp:
                timestamp = datetime.utcnow()

            location_data = self._build_location_doc(
                vehicle_id=vehicle_id,
                latitude=latitude,
                longitude=longitude,
                altitude=altitude,
                speed=speed,
                heading=heading,
                accuracy=accuracy,
                timestamp=timestamp
            )

            result = await self.db.db.vehicle_locations.insert_one(location_data)
            location_data["_id"] = str(result.inserted_id)

            history_data = location_data.copy()
            history_data["created_at"] = datetime.utcnow()
            await self.db.db.location_history.insert_one(history_data)

            try:
                await event_publisher.publish_location_created(
                    vehicle_id=vehicle_id,
                    latitude=latitude,
                    longitude=longitude,
                    timestamp=timestamp
                )
            except Exception as e:
                logger.warning(f"Failed to publish location created event: {e}")

            logger.info(f"Created new location for vehicle {vehicle_id}")
            return VehicleLocation(**location_data)


        except Exception as e:
            logger.info(f"Error creating vehicle: {e}")
            raise
            
    
    async def get_all_vehicle_locations(self) -> List[VehicleLocation]:
        """Fetch all current vehicle locations."""
        try:
            cursor = self.db.db.vehicle_locations.find({})
            locations = []
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])  # Convert ObjectId to string for API response
                locations.append(VehicleLocation(**doc))
            return locations
        except Exception as e:
            logger.error(f"Error fetching all vehicle locations: {e}")
            raise

        
    async def update_vehicle_location(
        self, 
        vehicle_id: str, 
        latitude: float, 
        longitude: float,
        altitude: Optional[float] = None,
        speed: Optional[float] = None,
        heading: Optional[float] = None,
        accuracy: Optional[float] = None,
        timestamp: Optional[datetime] = None
    ) -> VehicleLocation:
        """Update vehicle's current location"""
        try:
            if not timestamp:
                timestamp = datetime.utcnow()
            
            location_data = {
                "vehicle_id": vehicle_id,
                "location": {
                    "type": "Point",
                    "coordinates": [longitude, latitude]
                },
                "latitude": latitude,
                "longitude": longitude,
                "altitude": altitude,
                "speed": speed,
                "heading": heading,
                "accuracy": accuracy,
                "timestamp": timestamp,
                "updated_at": datetime.utcnow()
            }
            
            # Update current location (upsert)
            await self.db.db.vehicle_locations.update_one(
                {"vehicle_id": vehicle_id},
                {"$set": location_data},
                upsert=True
            )
            
            # Add to location history
            history_data = location_data.copy()
            history_data["created_at"] = datetime.utcnow()
            await self.db.db.location_history.insert_one(history_data)
            
            # Publish location update event
            try:
                await event_publisher.publish_location_updated(
                    vehicle_id=vehicle_id,
                    latitude=latitude,
                    longitude=longitude,
                    timestamp=timestamp
                )
            except Exception as e:
                logger.warning(f"Failed to publish location update event: {e}")
            
            #logger.info(f"Updated location for vehicle {vehicle_id}")
            return VehicleLocation(**location_data)
            
        except Exception as e:
            logger.error(f"Error updating vehicle location: {e}")
            raise
    
    async def get_vehicle_location(self, vehicle_id: str) -> Optional[VehicleLocation]:
        """Get current location of a vehicle"""
        try:
            location_doc = await self.db.db.vehicle_locations.find_one(
                {"vehicle_id": vehicle_id}
            )
            
            if location_doc:
                location_doc["_id"] = str(location_doc["_id"])
                return VehicleLocation(**location_doc)
            return None
            
        except Exception as e:
            logger.error(f"Error getting vehicle location: {e}")
            raise
    
    async def get_multiple_vehicle_locations(self, vehicle_ids: List[str]) -> List[VehicleLocation]:
        """Get current locations of multiple vehicles"""
        try:
            cursor = self.db.db.vehicle_locations.find(
                {"vehicle_id": {"$in": vehicle_ids}}
            )
            
            locations = []
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                locations.append(VehicleLocation(**doc))
            
            return locations
            
        except Exception as e:
            logger.error(f"Error getting multiple vehicle locations: {e}")
            raise
    
    async def get_location_history(
        self, 
        vehicle_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[LocationHistory]:
        """Get location history for a vehicle"""
        try:
            query = {"vehicle_id": vehicle_id}
            
            if start_time or end_time:
                time_query = {}
                if start_time:
                    time_query["$gte"] = start_time
                if end_time:
                    time_query["$lte"] = end_time
                query["timestamp"] = time_query
            
            cursor = self.db.db.location_history.find(query).sort(
                "timestamp", -1
            ).limit(limit)
            
            history = []
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                history.append(LocationHistory(**doc))
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting location history: {e}")
            raise
    
    async def get_vehicles_in_area(
        self, 
        center_lat: float, 
        center_lng: float, 
        radius_meters: float
    ) -> List[VehicleLocation]:
        """Get all vehicles within a circular area"""
        try:
            query = {
                "location": {
                    "$geoWithin": {
                        "$centerSphere": [
                            [center_lng, center_lat],
                            radius_meters / 6378100  # Convert to radians
                        ]
                    }
                }
            }
            
            cursor = self.db.db.vehicle_locations.find(query)
            
            vehicles = []
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                vehicles.append(VehicleLocation(**doc))
            
            return vehicles
            
        except Exception as e:
            logger.error(f"Error getting vehicles in area: {e}")
            raise
    
    async def start_tracking_session(self, vehicle_id: str, user_id: str) -> TrackingSession:
        """Start a new tracking session for a vehicle"""
        try:
            # End any existing active sessions for this vehicle
            await self.db.db.tracking_sessions.update_many(
                {"vehicle_id": vehicle_id, "is_active": True},
                {"$set": {"is_active": False, "ended_at": datetime.utcnow()}}
            )
            
            session_data = {
                "vehicle_id": vehicle_id,
                "user_id": user_id,
                "started_at": datetime.utcnow(),
                "is_active": True,
                "created_at": datetime.utcnow()
            }
            
            result = await self.db.db.tracking_sessions.insert_one(session_data)
            session_data["_id"] = str(result.inserted_id)
            
            logger.info(f"Started tracking session for vehicle {vehicle_id}")
            return TrackingSession(**session_data)
            
        except Exception as e:
            logger.error(f"Error starting tracking session: {e}")
            raise
    
    async def end_tracking_session(self, session_id: str) -> bool:
        """End a tracking session"""
        try:
            result = await self.db.db.tracking_sessions.update_one(
                {"_id": ObjectId(session_id), "is_active": True},
                {"$set": {"is_active": False, "ended_at": datetime.utcnow()}}
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"Ended tracking session {session_id}")
            return success
            
        except Exception as e:
            logger.error(f"Error ending tracking session: {e}")
            raise
    
    async def get_active_tracking_sessions(self, user_id: Optional[str] = None) -> List[TrackingSession]:
        """Get active tracking sessions"""
        try:
            query = {"is_active": True}
            if user_id:
                query["user_id"] = user_id
            
            cursor = self.db.db.tracking_sessions.find(query).sort("started_at", -1)
            
            sessions = []
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                sessions.append(TrackingSession(**doc))
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error getting active tracking sessions: {e}")
            raise
    
    async def cleanup_old_locations(self, days_to_keep: int = 90):
        """Cleanup old location history (background task)"""
        try:
            # Check database connectivity first
            if not self.db.is_connected():
                logger.warning("Database not connected, skipping location cleanup")
                return
            
            # Additional safety check for database instance
            if self.db._db is None:
                logger.warning("Database instance not available, skipping location cleanup")
                return
                
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            result = await self.db.db.location_history.delete_many(
                {"timestamp": {"$lt": cutoff_date}}
            )
            
            if result.deleted_count > 0:
                logger.info(f"Cleaned up {result.deleted_count} old location records")
            
        except Exception as e:
            logger.error(f"Error cleaning up old locations: {e}")
    
    async def validate_tracking_sessions(self):
        """Validate and cleanup stale tracking sessions (background task)"""
        try:
            # Check database connectivity first
            if not self.db.is_connected():
                logger.warning("Database not connected, skipping session validation")
                return
            
            # Additional safety check for database instance
            if self.db._db is None:
                logger.warning("Database instance not available, skipping session validation")
                return
                
            # End sessions that have been active for more than 24 hours without updates
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            result = await self.db.db.tracking_sessions.update_many(
                {
                    "is_active": True,
                    "started_at": {"$lt": cutoff_time}
                },
                {"$set": {"is_active": False, "ended_at": datetime.utcnow()}}
            )
            
            if result.modified_count > 0:
                logger.info(f"Cleaned up {result.modified_count} stale tracking sessions")
                
        except Exception as e:
            logger.error(f"Error validating tracking sessions: {e}")

    async def get_vehicle_route(self, vehicle_id: str, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Get vehicle route for a specific time period"""
        try:
            # Default to last 24 hours if no time range specified
            if not end_time:
                end_time = datetime.utcnow()
            if not start_time:
                start_time = end_time - timedelta(hours=24)
            
            query = {
                "vehicle_id": vehicle_id,
                "timestamp": {
                    "$gte": start_time,
                    "$lte": end_time
                }
            }
            
            # Get location history ordered by timestamp
            locations = await self.db.db.location_history.find(query).sort("timestamp", 1).to_list(1000)
            
            if not locations:
                return {
                    "vehicle_id": vehicle_id,
                    "route": [],
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "total_points": 0,
                    "distance_km": 0
                }
            
            # Calculate route information
            route_points = []
            total_distance = 0
            
            for i, location in enumerate(locations):
                point = {
                    "latitude": location["latitude"],
                    "longitude": location["longitude"],
                    "timestamp": location["timestamp"].isoformat(),
                    "speed": location.get("speed"),
                    "heading": location.get("heading")
                }
                route_points.append(point)
                
                # Calculate distance between consecutive points
                if i > 0:
                    prev_loc = locations[i-1]
                    distance = self._calculate_distance(
                        prev_loc["latitude"], prev_loc["longitude"],
                        location["latitude"], location["longitude"]
                    )
                    total_distance += distance
            
            return {
                "vehicle_id": vehicle_id,
                "route": route_points,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "total_points": len(route_points),
                "distance_km": round(total_distance, 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting vehicle route for {vehicle_id}: {e}")
            return {
                "vehicle_id": vehicle_id,
                "route": [],
                "start_time": start_time.isoformat() if start_time else None,
                "end_time": end_time.isoformat() if end_time else None,
                "total_points": 0,
                "distance_km": 0,
                "error": str(e)
            }

    async def start_vehicle_tracking(self, vehicle_id: str) -> Dict[str, Any]:
        """Start or resume tracking for a vehicle"""
        try:
            # Check if there's already an active tracking session
            existing_session = await self.db.db.tracking_sessions.find_one({
                "vehicle_id": vehicle_id,
                "is_active": True
            })
            
            if existing_session:
                return {
                    "vehicle_id": vehicle_id,
                    "status": "already_active",
                    "session_id": str(existing_session["_id"]),
                    "started_at": existing_session["started_at"].isoformat(),
                    "message": "Vehicle tracking is already active"
                }
            
            # Create new tracking session
            session_data = {
                "vehicle_id": vehicle_id,
                "started_at": datetime.utcnow(),
                "is_active": True,
                "last_update": datetime.utcnow(),
                "total_distance": 0,
                "total_points": 0
            }
            
            result = await self.db.db.tracking_sessions.insert_one(session_data)
            session_data["_id"] = str(result.inserted_id)
            
            # Publish tracking started event
            try:
                await event_publisher.publish_tracking_event(
                    event_type="tracking_started",
                    vehicle_id=vehicle_id,
                    data={
                        "session_id": session_data["_id"],
                        "started_at": session_data["started_at"].isoformat()
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to publish tracking started event: {e}")
            
            return {
                "vehicle_id": vehicle_id,
                "status": "started",
                "session_id": session_data["_id"],
                "started_at": session_data["started_at"].isoformat(),
                "message": "Vehicle tracking started successfully"
            }
            
        except Exception as e:
            logger.error(f"Error starting vehicle tracking for {vehicle_id}: {e}")
            return {
                "vehicle_id": vehicle_id,
                "status": "error",
                "message": f"Failed to start tracking: {str(e)}"
            }
        
    async def get_all_vehicles(self):
        """
        Get all vehicles from the database without any parameters.
        """
        try:
            return await self.db_management.vehicles.find({}).to_list(length=None)
        except Exception as e:
            print(f"Error fetching vehicles: {e}")
            return []

    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates using Haversine formula (returns km)"""
        import math
        
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat/2) * math.sin(delta_lat/2) + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon/2) * math.sin(delta_lon/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c


# Global location service instance
location_service = LocationService()
