import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId

from repositories.database import db_manager_gps
from schemas.entities import Geofence
from events.publisher import event_publisher

logger = logging.getLogger(__name__)

class GeofenceService:
    """Service for managing geofences with unified data format and Pydantic V2"""
    
    def __init__(self):
      self.db = db_manager_gps
    
    async def get_geofences(
        self,
        is_active: Optional[bool] = None,
        geofence_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Geofence]:
        """Get geofences with optional filters"""
        try:
            query = {}
            if is_active is not None:
                query["is_active"] = is_active
            if geofence_type:
                query["type"] = geofence_type

            cursor = self.db.geofences.find(query).skip(offset).limit(limit)
            geofences = []
            async for doc in cursor:
                # Convert _id to string
                doc["id"] = str(doc.pop("_id"))

                # Keep geometry exactly as in DB
                if "geometry" not in doc or not isinstance(doc["geometry"], dict):
                    doc["geometry"] = {"type": "Polygon", "coordinates": []}  # Default fallback

                geofences.append(Geofence(**doc))
            return geofences
        except Exception as e:
            logger.error(f"Error getting geofences: {e}")
            return []



# Create service instance
geofence_service = GeofenceService()