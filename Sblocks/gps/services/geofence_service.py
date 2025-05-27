"""
Geofence management service for GPS service
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
import logging
from pymongo import ASCENDING, DESCENDING
from bson import ObjectId

from database import get_database, get_collection
from config import collections, settings
from models import (
    Geofence, GeofenceEvent, GeofenceCreate, GeofenceUpdate, 
    GeofenceQuery, GeofenceResponse, GeofenceEventQuery, GeofenceEventResponse,
    VehicleLocation
)
from messaging import publish_geofence_event
from utils.geospatial import calculate_distance, point_in_circle

logger = logging.getLogger(__name__)

class GeofenceService:
    def __init__(self):
        self.vehicle_geofence_states = {}  # Track which geofences vehicles are currently in
        
    async def create_geofence(self, geofence_data: GeofenceCreate, created_by: Optional[str] = None) -> Geofence:
        """Create a new geofence"""
        try:
            geofence = Geofence(
                **geofence_data.dict(),
                created_by=created_by,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            collection = await get_collection(collections.GEOFENCES)
            result = await collection.insert_one(geofence.dict(by_alias=True, exclude={"id"}))
            
            geofence.id = result.inserted_id
            
            logger.info(f"Created geofence {geofence.name} with ID {geofence.id}")
            return geofence
            
        except Exception as e:
            logger.error(f"Error creating geofence: {e}")
            raise

    async def get_geofence(self, geofence_id: str) -> Optional[Geofence]:
        """Get geofence by ID"""
        try:
            collection = await get_collection(collections.GEOFENCES)
            doc = await collection.find_one({"_id": ObjectId(geofence_id)})
            
            if doc:
                return Geofence(**doc)
            return None
            
        except Exception as e:
            logger.error(f"Error getting geofence {geofence_id}: {e}")
            return None

    async def update_geofence(self, geofence_id: str, update_data: GeofenceUpdate) -> Optional[Geofence]:
        """Update an existing geofence"""
        try:
            collection = await get_collection(collections.GEOFENCES)
            
            # Only update fields that are provided
            update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
            update_dict["updated_at"] = datetime.utcnow()
            
            result = await collection.update_one(
                {"_id": ObjectId(geofence_id)},
                {"$set": update_dict}
            )
            
            if result.modified_count > 0:
                return await self.get_geofence(geofence_id)
            return None
            
        except Exception as e:
            logger.error(f"Error updating geofence {geofence_id}: {e}")
            return None

    async def delete_geofence(self, geofence_id: str) -> bool:
        """Delete a geofence"""
        try:
            collection = await get_collection(collections.GEOFENCES)
            result = await collection.delete_one({"_id": ObjectId(geofence_id)})
            
            if result.deleted_count > 0:
                logger.info(f"Deleted geofence {geofence_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error deleting geofence {geofence_id}: {e}")
            return False

    async def get_geofences(self, query: GeofenceQuery) -> GeofenceResponse:
        """Get geofences with filtering and pagination"""
        try:
            collection = await get_collection(collections.GEOFENCES)
            
            # Build query filter
            filter_dict = {}
            
            if query.name:
                filter_dict["name"] = {"$regex": query.name, "$options": "i"}
            
            if query.type:
                filter_dict["type"] = query.type
            
            if query.status:
                filter_dict["status"] = query.status
            
            if query.vehicle_id:
                filter_dict["vehicle_ids"] = {"$in": [query.vehicle_id]}
            
            if query.bounds:
                # Geographic bounds filter
                filter_dict["coordinates.latitude"] = {
                    "$gte": query.bounds.get("south", -90),
                    "$lte": query.bounds.get("north", 90)
                }
                filter_dict["coordinates.longitude"] = {
                    "$gte": query.bounds.get("west", -180),
                    "$lte": query.bounds.get("east", 180)
                }
            
            # Get total count
            total_count = await collection.count_documents(filter_dict)
            
            # Get paginated results
            cursor = collection.find(filter_dict).sort("created_at", DESCENDING)
            
            if query.skip:
                cursor = cursor.skip(query.skip)
            if query.limit:
                cursor = cursor.limit(query.limit)
            
            geofences = []
            async for doc in cursor:
                geofences.append(Geofence(**doc))
            
            # Calculate pagination info
            page = (query.skip // query.limit) + 1 if query.limit else 1
            per_page = query.limit or len(geofences)
            has_next = (query.skip + len(geofences)) < total_count
            has_prev = query.skip > 0
            
            return GeofenceResponse(
                geofences=geofences,
                total_count=total_count,
                page=page,
                per_page=per_page,
                has_next=has_next,
                has_prev=has_prev
            )
            
        except Exception as e:
            logger.error(f"Error getting geofences: {e}")
            raise

    async def check_vehicle_geofences(self, vehicle_location: VehicleLocation):
        """Check if vehicle has entered or exited any geofences"""
        try:
            # Get all active geofences for this vehicle
            geofences = await self._get_vehicle_geofences(vehicle_location.vehicle_id)
            
            current_geofences = set()
            
            for geofence in geofences:
                is_inside = point_in_circle(
                    vehicle_location.coordinates.latitude,
                    vehicle_location.coordinates.longitude,
                    geofence.coordinates.latitude,
                    geofence.coordinates.longitude,
                    geofence.radius
                )
                
                if is_inside:
                    current_geofences.add(str(geofence.id))
            
            # Compare with previous state
            previous_geofences = self.vehicle_geofence_states.get(vehicle_location.vehicle_id, set())
            
            # Check for entries
            entered_geofences = current_geofences - previous_geofences
            for geofence_id in entered_geofences:
                await self._handle_geofence_entry(vehicle_location, geofence_id)
            
            # Check for exits
            exited_geofences = previous_geofences - current_geofences
            for geofence_id in exited_geofences:
                await self._handle_geofence_exit(vehicle_location, geofence_id)
            
            # Update state
            self.vehicle_geofence_states[vehicle_location.vehicle_id] = current_geofences
            
        except Exception as e:
            logger.error(f"Error checking vehicle geofences: {e}")

    async def get_geofence_events(self, query: GeofenceEventQuery) -> GeofenceEventResponse:
        """Get geofence events with filtering and pagination"""
        try:
            collection = await get_collection(collections.GEOFENCE_EVENTS)
            
            # Build query filter
            filter_dict = {}
            
            if query.geofence_ids:
                filter_dict["geofence_id"] = {"$in": query.geofence_ids}
            
            if query.vehicle_ids:
                filter_dict["vehicle_id"] = {"$in": query.vehicle_ids}
            
            if query.event_types:
                filter_dict["event_type"] = {"$in": query.event_types}
            
            if query.start_time or query.end_time:
                time_filter = {}
                if query.start_time:
                    time_filter["$gte"] = query.start_time
                if query.end_time:
                    time_filter["$lte"] = query.end_time
                filter_dict["timestamp"] = time_filter
            
            if query.driver_id:
                filter_dict["driver_id"] = query.driver_id
            
            if query.trip_id:
                filter_dict["trip_id"] = query.trip_id
            
            # Get total count
            total_count = await collection.count_documents(filter_dict)
            
            # Get paginated results
            cursor = collection.find(filter_dict).sort("timestamp", DESCENDING)
            
            if query.skip:
                cursor = cursor.skip(query.skip)
            if query.limit:
                cursor = cursor.limit(query.limit)
            
            events = []
            async for doc in cursor:
                events.append(GeofenceEvent(**doc))
            
            # Calculate pagination info
            page = (query.skip // query.limit) + 1 if query.limit else 1
            per_page = query.limit or len(events)
            has_next = (query.skip + len(events)) < total_count
            has_prev = query.skip > 0
            
            return GeofenceEventResponse(
                events=events,
                total_count=total_count,
                page=page,
                per_page=per_page,
                has_next=has_next,
                has_prev=has_prev
            )
            
        except Exception as e:
            logger.error(f"Error getting geofence events: {e}")
            raise

    async def get_geofence_violations(self, vehicle_id: Optional[str] = None, days: int = 7) -> List[GeofenceEvent]:
        """Get geofence violations (restricted area entries)"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days)
            
            collection = await get_collection(collections.GEOFENCE_EVENTS)
            
            filter_dict = {
                "event_type": "violation",
                "timestamp": {"$gte": start_time, "$lte": end_time}
            }
            
            if vehicle_id:
                filter_dict["vehicle_id"] = vehicle_id
            
            violations = []
            cursor = collection.find(filter_dict).sort("timestamp", DESCENDING)
            
            async for doc in cursor:
                violations.append(GeofenceEvent(**doc))
            
            return violations
            
        except Exception as e:
            logger.error(f"Error getting geofence violations: {e}")
            return []

    async def _get_vehicle_geofences(self, vehicle_id: str) -> List[Geofence]:
        """Get all geofences that apply to a specific vehicle"""
        try:
            collection = await get_collection(collections.GEOFENCES)
            
            # Get geofences that apply to this vehicle or all vehicles
            cursor = collection.find({
                "status": "active",
                "$or": [
                    {"vehicle_ids": {"$in": [vehicle_id]}},
                    {"vehicle_ids": {"$size": 0}}  # Empty array means applies to all vehicles
                ]
            })
            
            geofences = []
            async for doc in cursor:
                geofences.append(Geofence(**doc))
            
            return geofences
            
        except Exception as e:
            logger.error(f"Error getting vehicle geofences: {e}")
            return []

    async def _handle_geofence_entry(self, vehicle_location: VehicleLocation, geofence_id: str):
        """Handle vehicle entering a geofence"""
        try:
            geofence = await self.get_geofence(geofence_id)
            if not geofence:
                return
            
            # Determine event type based on geofence type
            event_type = "violation" if geofence.status == "restricted" else "enter"
            
            # Create geofence event
            geofence_event = GeofenceEvent(
                geofence_id=geofence_id,
                vehicle_id=vehicle_location.vehicle_id,
                event_type=event_type,
                timestamp=datetime.utcnow(),
                coordinates=geofence.coordinates,
                speed=vehicle_location.speed,
                heading=vehicle_location.heading,
                driver_id=vehicle_location.driver_id
            )
            
            collection = await get_collection(collections.GEOFENCE_EVENTS)
            await collection.insert_one(geofence_event.dict(by_alias=True, exclude={"id"}))
            
            # Publish event
            await publish_geofence_event(
                "geofence.entered" if event_type == "enter" else "geofence.violation",
                vehicle_location.vehicle_id,
                geofence_id,
                {
                    "geofence_name": geofence.name,
                    "geofence_type": geofence.type,
                    "event_type": event_type,
                    "location": vehicle_location.dict(exclude={"id"}),
                    "timestamp": datetime.utcnow()
                }
            )
            
            logger.info(f"Vehicle {vehicle_location.vehicle_id} entered geofence {geofence.name}")
            
        except Exception as e:
            logger.error(f"Error handling geofence entry: {e}")

    async def _handle_geofence_exit(self, vehicle_location: VehicleLocation, geofence_id: str):
        """Handle vehicle exiting a geofence"""
        try:
            geofence = await self.get_geofence(geofence_id)
            if not geofence:
                return
            
            # Calculate dwell time
            dwell_time = await self._calculate_dwell_time(vehicle_location.vehicle_id, geofence_id)
            
            # Create geofence event
            geofence_event = GeofenceEvent(
                geofence_id=geofence_id,
                vehicle_id=vehicle_location.vehicle_id,
                event_type="exit",
                timestamp=datetime.utcnow(),
                coordinates=geofence.coordinates,
                speed=vehicle_location.speed,
                heading=vehicle_location.heading,
                driver_id=vehicle_location.driver_id,
                dwell_time=dwell_time
            )
            
            collection = await get_collection(collections.GEOFENCE_EVENTS)
            await collection.insert_one(geofence_event.dict(by_alias=True, exclude={"id"}))
            
            # Publish event
            await publish_geofence_event(
                "geofence.exited",
                vehicle_location.vehicle_id,
                geofence_id,
                {
                    "geofence_name": geofence.name,
                    "geofence_type": geofence.type,
                    "dwell_time": dwell_time,
                    "location": vehicle_location.dict(exclude={"id"}),
                    "timestamp": datetime.utcnow()
                }
            )
            
            logger.info(f"Vehicle {vehicle_location.vehicle_id} exited geofence {geofence.name}")
            
        except Exception as e:
            logger.error(f"Error handling geofence exit: {e}")

    async def _calculate_dwell_time(self, vehicle_id: str, geofence_id: str) -> Optional[int]:
        """Calculate how long a vehicle was in a geofence"""
        try:
            collection = await get_collection(collections.GEOFENCE_EVENTS)
            
            # Find the most recent entry event
            entry_event = await collection.find_one(
                {
                    "vehicle_id": vehicle_id,
                    "geofence_id": geofence_id,
                    "event_type": {"$in": ["enter", "violation"]}
                },
                sort=[("timestamp", DESCENDING)]
            )
            
            if entry_event:
                entry_time = entry_event["timestamp"]
                exit_time = datetime.utcnow()
                dwell_time = int((exit_time - entry_time).total_seconds())
                return dwell_time
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculating dwell time: {e}")
            return None

# Global service instance
geofence_service = GeofenceService()
