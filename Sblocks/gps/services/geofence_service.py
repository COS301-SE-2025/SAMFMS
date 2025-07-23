"""
Geofence service for managing geofences and geofence events
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId
import json

from repositories.database import db_manager
from schemas.entities import Geofence, GeofenceEvent
from events.publisher import event_publisher

logger = logging.getLogger(__name__)


class GeofenceService:
    """Service for managing geofences and geofence events"""
    
    def __init__(self):
        self.db = db_manager
        
    async def create_geofence(
        self,
        name: str,
        description: Optional[str],
        geometry: Dict[str, Any],  # GeoJSON geometry
        geofence_type: str = "polygon",
        is_active: bool = True,
        created_by: str = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Geofence:
        """Create a new geofence"""
        try:
            geofence_data = {
                "name": name,
                "description": description,
                "geometry": geometry,
                "geofence_type": geofence_type,
                "is_active": is_active,
                "created_by": created_by,
                "metadata": metadata or {},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await self.db.db.geofences.insert_one(geofence_data)
            geofence_data["_id"] = str(result.inserted_id)
            
            # Publish geofence created event
            try:
                await event_publisher.publish_geofence_created(
                    geofence_id=str(result.inserted_id),
                    name=name,
                    created_by=created_by
                )
            except Exception as e:
                logger.warning(f"Failed to publish geofence created event: {e}")
            
            logger.info(f"Created geofence: {name}")
            return Geofence(**geofence_data)
            
        except Exception as e:
            logger.error(f"Error creating geofence: {e}")
            raise
    
    async def get_geofence(self, geofence_id: str) -> Optional[Geofence]:
        """Get a geofence by ID"""
        try:
            geofence_doc = await self.db.db.geofences.find_one(
                {"_id": ObjectId(geofence_id)}
            )
            
            if geofence_doc:
                geofence_doc["_id"] = str(geofence_doc["_id"])
                return Geofence(**geofence_doc)
            return None
            
        except Exception as e:
            logger.error(f"Error getting geofence: {e}")
            raise

    async def get_geofence_by_id(self, geofence_id: str) -> Optional[Geofence]:
        """Get a specific geofence by ID"""
        try:
            if not ObjectId.is_valid(geofence_id):
                return None
                
            geofence_doc = await self.db.db.geofences.find_one(
                {"_id": ObjectId(geofence_id)}
            )
            
            if geofence_doc:
                geofence_doc["_id"] = str(geofence_doc["_id"])
                return Geofence(**geofence_doc)
            return None
            
        except Exception as e:
            logger.error(f"Error getting geofence by ID {geofence_id}: {e}")
            return None
    
    async def get_geofences(
        self,
        is_active: Optional[bool] = None,
        created_by: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Geofence]:
        """Get list of geofences with filters"""
        try:
            query = {}
            if is_active is not None:
                query["is_active"] = is_active
            if created_by:
                query["created_by"] = created_by
            
            cursor = self.db.db.geofences.find(query).sort(
                "created_at", -1
            ).skip(offset).limit(limit)
            
            geofences = []
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                geofences.append(Geofence(**doc))
            
            return geofences
            
        except Exception as e:
            logger.error(f"Error getting geofences: {e}")
            raise
    
    async def update_geofence(
        self,
        geofence_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        geometry: Optional[Dict[str, Any]] = None,
        is_active: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Geofence]:
        """Update a geofence"""
        try:
            update_data = {"updated_at": datetime.utcnow()}
            
            if name is not None:
                update_data["name"] = name
            if description is not None:
                update_data["description"] = description
            if geometry is not None:
                update_data["geometry"] = geometry
            if is_active is not None:
                update_data["is_active"] = is_active
            if metadata is not None:
                update_data["metadata"] = metadata
            
            result = await self.db.db.geofences.update_one(
                {"_id": ObjectId(geofence_id)},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                return await self.get_geofence(geofence_id)
            return None
            
        except Exception as e:
            logger.error(f"Error updating geofence: {e}")
            raise
    
    async def delete_geofence(self, geofence_id: str) -> bool:
        """Delete a geofence"""
        try:
            result = await self.db.db.geofences.delete_one(
                {"_id": ObjectId(geofence_id)}
            )
            
            success = result.deleted_count > 0
            if success:
                logger.info(f"Deleted geofence {geofence_id}")
            return success
            
        except Exception as e:
            logger.error(f"Error deleting geofence: {e}")
            raise
    
    async def check_vehicle_geofences(
        self, 
        vehicle_id: str, 
        latitude: float, 
        longitude: float
    ) -> List[Geofence]:
        """Check which geofences a vehicle location intersects"""
        try:
            point = {
                "type": "Point",
                "coordinates": [longitude, latitude]
            }
            
            query = {
                "is_active": True,
                "geometry": {
                    "$geoIntersects": {
                        "$geometry": point
                    }
                }
            }
            
            cursor = self.db.db.geofences.find(query)
            
            intersecting_geofences = []
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                intersecting_geofences.append(Geofence(**doc))
            
            return intersecting_geofences
            
        except Exception as e:
            logger.error(f"Error checking vehicle geofences: {e}")
            raise
    
    async def record_geofence_event(
        self,
        vehicle_id: str,
        geofence_id: str,
        event_type: str,  # "enter", "exit", "dwell"
        latitude: float,
        longitude: float,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> GeofenceEvent:
        """Record a geofence event"""
        try:
            if not timestamp:
                timestamp = datetime.utcnow()
            
            event_data = {
                "vehicle_id": vehicle_id,
                "geofence_id": geofence_id,
                "event_type": event_type,
                "location": {
                    "type": "Point",
                    "coordinates": [longitude, latitude]
                },
                "latitude": latitude,
                "longitude": longitude,
                "timestamp": timestamp,
                "metadata": metadata or {},
                "created_at": datetime.utcnow()
            }
            
            result = await self.db.db.geofence_events.insert_one(event_data)
            event_data["_id"] = str(result.inserted_id)
            
            # Publish geofence event
            try:
                await event_publisher.publish_geofence_event(
                    vehicle_id=vehicle_id,
                    geofence_id=geofence_id,
                    event_type=event_type,
                    timestamp=timestamp
                )
            except Exception as e:
                logger.warning(f"Failed to publish geofence event: {e}")
            
            logger.info(f"Recorded geofence {event_type} event for vehicle {vehicle_id}")
            return GeofenceEvent(**event_data)
            
        except Exception as e:
            logger.error(f"Error recording geofence event: {e}")
            raise
    
    async def get_geofence_events(
        self,
        vehicle_id: Optional[str] = None,
        geofence_id: Optional[str] = None,
        event_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[GeofenceEvent]:
        """Get geofence events with filters"""
        try:
            query = {}
            
            if vehicle_id:
                query["vehicle_id"] = vehicle_id
            if geofence_id:
                query["geofence_id"] = geofence_id
            if event_type:
                query["event_type"] = event_type
            
            if start_time or end_time:
                time_query = {}
                if start_time:
                    time_query["$gte"] = start_time
                if end_time:
                    time_query["$lte"] = end_time
                query["timestamp"] = time_query
            
            cursor = self.db.db.geofence_events.find(query).sort(
                "timestamp", -1
            ).limit(limit)
            
            events = []
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                events.append(GeofenceEvent(**doc))
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting geofence events: {e}")
            raise
    
    async def get_geofence_statistics(self, geofence_id: str) -> Dict[str, Any]:
        """Get statistics for a geofence"""
        try:
            # Count events by type
            pipeline = [
                {"$match": {"geofence_id": geofence_id}},
                {"$group": {
                    "_id": "$event_type",
                    "count": {"$sum": 1}
                }}
            ]
            
            cursor = self.db.db.geofence_events.aggregate(pipeline)
            event_counts = {}
            async for doc in cursor:
                event_counts[doc["_id"]] = doc["count"]
            
            # Get unique vehicles
            unique_vehicles = await self.db.db.geofence_events.distinct(
                "vehicle_id", 
                {"geofence_id": geofence_id}
            )
            
            # Get recent activity (last 24 hours)
            last_24h = datetime.utcnow() - timedelta(hours=24)
            recent_events = await self.db.db.geofence_events.count_documents({
                "geofence_id": geofence_id,
                "timestamp": {"$gte": last_24h}
            })
            
            return {
                "geofence_id": geofence_id,
                "event_counts": event_counts,
                "unique_vehicles": len(unique_vehicles),
                "recent_events_24h": recent_events,
                "total_events": sum(event_counts.values())
            }
            
        except Exception as e:
            logger.error(f"Error getting geofence statistics: {e}")
            raise
    
    async def update_geofence_statistics(self):
        """Update geofence statistics (background task)"""
        try:
            # This could be expanded to cache frequently accessed statistics
            logger.debug("Geofence statistics update completed")
            
        except Exception as e:
            logger.error(f"Error updating geofence statistics: {e}")


# Global geofence service instance
geofence_service = GeofenceService()
