"""
Service for trip history operations
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId

from repositories.database import db_manager
from schemas.entities import Trip

logger = logging.getLogger(__name__)

class TripHistoryService:
  """Service for managing trip history"""
  def __init__(self):
    self.db = db_manager
  
  async def add_trip(self, request: Trip) -> Trip:
    try:
        trip_data = request.dict(exclude_unset=True)
        logger.info(f"Inserting trip into history collection: {trip_data}")

        result = await self.db.trip_history.insert_one(trip_data)
        inserted_id = str(result.inserted_id)
        logger.info(f"Trip inserted with ID: {inserted_id}")

        trip_data["_id"] = inserted_id
        return Trip(**trip_data)
    
    except Exception as e:
        logger.error(f"Failed to add trip to history: {e}")
        raise

  
  async def get_trip_by_id(self, trip_id: str) -> Optional[Trip]:
        try:
            logger.info(f"Fetching trip from history by ID: {trip_id}")
            trip_doc = await self.db.trip_history.find_one({"_id": ObjectId(trip_id)})
            if trip_doc:
                trip_doc["_id"] = str(trip_doc["_id"])
                logger.info(f"Found trip with ID: {trip_id}")
                return Trip(**trip_doc)
            else:
                logger.warning(f"No trip found with ID: {trip_id}")
                return None
        except Exception as e:
            logger.error(f"Failed to get trip {trip_id} from history: {e}")
            raise

  async def list_trips(self, filter: dict = {}, skip: int = 0, limit: int = 50) -> List[Trip]:
        try:
            logger.info(f"Listing trips from history with filter: {filter}, skip: {skip}, limit: {limit}")
            cursor = self.db.trip_history.find(filter).skip(skip).limit(limit)
            trips = []
            async for trip_doc in cursor:
                trip_doc["_id"] = str(trip_doc["_id"])
                trips.append(Trip(**trip_doc))
            logger.info(f"Listed {len(trips)} trips from history")
            return trips
        except Exception as e:
            logger.error(f"Failed to list trips from history: {e}")
            raise

  async def update_trip(self, trip_id: str, update_data: dict) -> Optional[Trip]:
        try:
            logger.info(f"Updating trip in history with ID: {trip_id}, data: {update_data}")
            result = await self.db.trip_history.update_one(
                {"_id": ObjectId(trip_id)},
                {"$set": update_data}
            )
            if result.modified_count == 1:
                logger.info(f"Successfully updated trip with ID: {trip_id}")
                return await self.get_trip_by_id(trip_id)
            else:
                logger.warning(f"No trip updated for ID: {trip_id} (may not exist or data identical)")
                return None
        except Exception as e:
            logger.error(f"Failed to update trip {trip_id} in history: {e}")
            raise

  async def delete_trip(self, trip_id: str) -> bool:
        try:
            logger.info(f"Deleting trip from history with ID: {trip_id}")
            result = await self.db.trip_history.delete_one({"_id": ObjectId(trip_id)})
            if result.deleted_count == 1:
                logger.info(f"Successfully deleted trip with ID: {trip_id}")
                return True
            else:
                logger.warning(f"No trip found to delete with ID: {trip_id}")
                return False
        except Exception as e:
            logger.error(f"Failed to delete trip {trip_id} from history: {e}")
            raise

trip_history_service = TripHistoryService()