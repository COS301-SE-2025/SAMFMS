"""
Places service for managing user-saved places
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId

from repositories.database import db_manager
from schemas.entities import Place
from events.publisher import event_publisher

logger = logging.getLogger(__name__)


class PlacesService:
    """Service for managing user places"""
    
    def __init__(self):
        self.db = db_manager
        
    async def create_place(
        self,
        user_id: str,
        name: str,
        description: Optional[str],
        latitude: float,
        longitude: float,
        address: Optional[str] = None,
        place_type: str = "custom",
        metadata: Optional[Dict[str, Any]] = None,
        created_by: Optional[str] = None
    ) -> Place:
        """Create a new place"""
        try:
            place_data = {
                "user_id": user_id,
                "name": name,
                "description": description,
                "location": {
                    "type": "Point",
                    "coordinates": [longitude, latitude]
                },
                "latitude": latitude,
                "longitude": longitude,
                "address": address,
                "place_type": place_type,
                "metadata": metadata or {},
                "created_by": created_by or user_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await self.db.db.places.insert_one(place_data)
            place_data["_id"] = str(result.inserted_id)
            
            # Publish place created event
            try:
                await event_publisher.publish_place_created(
                    place_id=str(result.inserted_id),
                    user_id=user_id,
                    name=name
                )
            except Exception as e:
                logger.warning(f"Failed to publish place created event: {e}")
            
            logger.info(f"Created place: {name} for user {user_id}")
            return Place(**place_data)
            
        except Exception as e:
            logger.error(f"Error creating place: {e}")
            raise
    
    async def get_place(self, place_id: str) -> Optional[Place]:
        """Get a place by ID"""
        try:
            place_doc = await self.db.db.places.find_one(
                {"_id": ObjectId(place_id)}
            )
            
            if place_doc:
                place_doc["_id"] = str(place_doc["_id"])
                return Place(**place_doc)
            return None
            
        except Exception as e:
            logger.error(f"Error getting place: {e}")
            raise
    
    async def get_user_places(
        self,
        user_id: str,
        place_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Place]:
        """Get places for a user"""
        try:
            query = {"user_id": user_id}
            if place_type:
                query["place_type"] = place_type
            
            cursor = self.db.db.places.find(query).sort(
                "created_at", -1
            ).skip(offset).limit(limit)
            
            places = []
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                places.append(Place(**doc))
            
            return places
            
        except Exception as e:
            logger.error(f"Error getting user places: {e}")
            raise
    
    async def search_places(
        self,
        user_id: str,
        search_term: str,
        limit: int = 50
    ) -> List[Place]:
        """Search places by name or description"""
        try:
            query = {
                "user_id": user_id,
                "$or": [
                    {"name": {"$regex": search_term, "$options": "i"}},
                    {"description": {"$regex": search_term, "$options": "i"}},
                    {"address": {"$regex": search_term, "$options": "i"}}
                ]
            }
            
            cursor = self.db.db.places.find(query).sort(
                "name", 1
            ).limit(limit)
            
            places = []
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                places.append(Place(**doc))
            
            return places
            
        except Exception as e:
            logger.error(f"Error searching places: {e}")
            raise
    
    async def get_places_near_location(
        self,
        user_id: str,
        latitude: float,
        longitude: float,
        radius_meters: float = 1000,
        limit: int = 50
    ) -> List[Place]:
        """Get places near a location"""
        try:
            query = {
                "user_id": user_id,
                "location": {
                    "$near": {
                        "$geometry": {
                            "type": "Point",
                            "coordinates": [longitude, latitude]
                        },
                        "$maxDistance": radius_meters
                    }
                }
            }
            
            cursor = self.db.db.places.find(query).limit(limit)
            
            places = []
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                places.append(Place(**doc))
            
            return places
            
        except Exception as e:
            logger.error(f"Error getting places near location: {e}")
            raise
    
    async def update_place(
        self,
        place_id: str,
        user_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        address: Optional[str] = None,
        place_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Place]:
        """Update a place"""
        try:
            update_data = {"updated_at": datetime.utcnow()}
            
            if name is not None:
                update_data["name"] = name
            if description is not None:
                update_data["description"] = description
            if address is not None:
                update_data["address"] = address
            if place_type is not None:
                update_data["place_type"] = place_type
            if metadata is not None:
                update_data["metadata"] = metadata
            
            if latitude is not None and longitude is not None:
                update_data["latitude"] = latitude
                update_data["longitude"] = longitude
                update_data["location"] = {
                    "type": "Point",
                    "coordinates": [longitude, latitude]
                }
            
            result = await self.db.db.places.update_one(
                {"_id": ObjectId(place_id), "user_id": user_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                return await self.get_place(place_id)
            return None
            
        except Exception as e:
            logger.error(f"Error updating place: {e}")
            raise
    
    async def delete_place(self, place_id: str, user_id: str) -> bool:
        """Delete a place"""
        try:
            result = await self.db.db.places.delete_one(
                {"_id": ObjectId(place_id), "user_id": user_id}
            )
            
            success = result.deleted_count > 0
            if success:
                logger.info(f"Deleted place {place_id} for user {user_id}")
            return success
            
        except Exception as e:
            logger.error(f"Error deleting place: {e}")
            raise
    
    async def get_place_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get statistics for user's places"""
        try:
            # Count places by type
            pipeline = [
                {"$match": {"user_id": user_id}},
                {"$group": {
                    "_id": "$place_type",
                    "count": {"$sum": 1}
                }}
            ]
            
            cursor = self.db.db.places.aggregate(pipeline)
            place_counts = {}
            async for doc in cursor:
                place_counts[doc["_id"]] = doc["count"]
            
            # Total places
            total_places = sum(place_counts.values())
            
            return {
                "user_id": user_id,
                "total_places": total_places,
                "place_counts_by_type": place_counts
            }
            
        except Exception as e:
            logger.error(f"Error getting place statistics: {e}")
            raise


# Global places service instance
places_service = PlacesService()
