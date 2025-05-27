"""
Location tracking service for GPS service
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import logging
from pymongo import ASCENDING, DESCENDING
from bson import ObjectId

from database import get_database, get_collection
from config import collections, settings
from models import (
    VehicleLocation, LocationHistory, LocationUpdate, 
    LocationQuery, LocationResponse, HistoryResponse, GPSCoordinates
)
from messaging import publish_location_update, publish_vehicle_idle
from utils.geospatial import calculate_distance, calculate_heading, determine_direction

logger = logging.getLogger(__name__)

class LocationService:
    def __init__(self):
        self.location_buffer = {}  # In-memory buffer for high-frequency updates
        self.last_update_times = {}  # Track last update times for idle detection
        
    async def update_vehicle_location(self, location_update: LocationUpdate) -> VehicleLocation:
        """Update vehicle location with real-time processing"""
        try:
            # Calculate direction from heading
            direction = determine_direction(location_update.heading) if location_update.heading else None
            
            # Create vehicle location object
            vehicle_location = VehicleLocation(
                vehicle_id=location_update.vehicle_id,
                coordinates=location_update.coordinates,
                timestamp=datetime.utcnow(),
                speed=location_update.speed,
                heading=location_update.heading,
                direction=direction,
                status=location_update.status,
                fuel_level=location_update.fuel_level,
                odometer=location_update.odometer,
                driver_id=location_update.driver_id,
                ignition=location_update.ignition
            )
            
            # Get previous location for comparison
            previous_location = await self.get_current_location(location_update.vehicle_id)
            
            # Update current location in database
            collection = await get_collection(collections.VEHICLE_LOCATIONS)
            await collection.replace_one(
                {"vehicle_id": location_update.vehicle_id},
                vehicle_location.dict(by_alias=True, exclude={"id"}),
                upsert=True
            )
            
            # Create history entry
            await self._create_history_entry(vehicle_location, previous_location, location_update.metadata)
            
            # Check for events (idle, speed violations, etc.)
            await self._process_location_events(vehicle_location, previous_location)
            
            # Publish real-time update
            if settings.real_time_updates:
                await publish_location_update(
                    vehicle_location.vehicle_id,
                    vehicle_location.dict(exclude={"id"})
                )
            
            # Update tracking state
            self.last_update_times[location_update.vehicle_id] = datetime.utcnow()
            
            logger.debug(f"Updated location for vehicle {location_update.vehicle_id}")
            return vehicle_location
            
        except Exception as e:
            logger.error(f"Error updating vehicle location: {e}")
            raise

    async def get_current_location(self, vehicle_id: str) -> Optional[VehicleLocation]:
        """Get current location of a vehicle"""
        try:
            collection = await get_collection(collections.VEHICLE_LOCATIONS)
            doc = await collection.find_one({"vehicle_id": vehicle_id})
            
            if doc:
                return VehicleLocation(**doc)
            return None
            
        except Exception as e:
            logger.error(f"Error getting current location for vehicle {vehicle_id}: {e}")
            return None

    async def get_vehicle_locations(self, vehicle_ids: Optional[List[str]] = None) -> List[VehicleLocation]:
        """Get current locations for multiple vehicles"""
        try:
            collection = await get_collection(collections.VEHICLE_LOCATIONS)
            
            query = {}
            if vehicle_ids:
                query["vehicle_id"] = {"$in": vehicle_ids}
            
            cursor = collection.find(query)
            locations = []
            
            async for doc in cursor:
                locations.append(VehicleLocation(**doc))
            
            return locations
            
        except Exception as e:
            logger.error(f"Error getting vehicle locations: {e}")
            return []

    async def get_location_history(self, query: LocationQuery) -> HistoryResponse:
        """Get historical location data with filtering and pagination"""
        try:
            collection = await get_collection(collections.LOCATION_HISTORY)
            
            # Build query filter
            filter_dict = {}
            
            if query.vehicle_ids:
                filter_dict["vehicle_id"] = {"$in": query.vehicle_ids}
            
            if query.start_time or query.end_time:
                time_filter = {}
                if query.start_time:
                    time_filter["$gte"] = query.start_time
                if query.end_time:
                    time_filter["$lte"] = query.end_time
                filter_dict["timestamp"] = time_filter
            
            if query.event_types:
                filter_dict["event_type"] = {"$in": query.event_types}
            
            if query.geofence_id:
                filter_dict["geofence_id"] = query.geofence_id
            
            if query.trip_id:
                filter_dict["trip_id"] = query.trip_id
            
            if query.driver_id:
                filter_dict["driver_id"] = query.driver_id
            
            # Get total count
            total_count = await collection.count_documents(filter_dict)
            
            # Get paginated results
            cursor = collection.find(filter_dict).sort("timestamp", DESCENDING)
            
            if query.skip:
                cursor = cursor.skip(query.skip)
            if query.limit:
                cursor = cursor.limit(query.limit)
            
            history = []
            async for doc in cursor:
                history.append(LocationHistory(**doc))
            
            # Calculate pagination info
            page = (query.skip // query.limit) + 1 if query.limit else 1
            per_page = query.limit or len(history)
            has_next = (query.skip + len(history)) < total_count
            has_prev = query.skip > 0
            
            return HistoryResponse(
                history=history,
                total_count=total_count,
                page=page,
                per_page=per_page,
                has_next=has_next,
                has_prev=has_prev
            )
            
        except Exception as e:
            logger.error(f"Error getting location history: {e}")
            raise

    async def get_vehicle_route_today(self, vehicle_id: str) -> List[LocationHistory]:
        """Get today's route for a vehicle"""
        try:
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)
            
            query = LocationQuery(
                vehicle_ids=[vehicle_id],
                start_time=today_start,
                end_time=today_end,
                event_types=["location"],
                limit=1000
            )
            
            response = await self.get_location_history(query)
            return response.history
            
        except Exception as e:
            logger.error(f"Error getting today's route for vehicle {vehicle_id}: {e}")
            return []

    async def get_vehicles_in_area(self, center_lat: float, center_lng: float, radius_km: float) -> List[VehicleLocation]:
        """Get vehicles within a specific area"""
        try:
            collection = await get_collection(collections.VEHICLE_LOCATIONS)
            
            # Use MongoDB geospatial query
            vehicles = []
            cursor = collection.find({
                "coordinates": {
                    "$near": {
                        "$geometry": {
                            "type": "Point",
                            "coordinates": [center_lng, center_lat]
                        },
                        "$maxDistance": radius_km * 1000  # Convert to meters
                    }
                }
            })
            
            async for doc in cursor:
                vehicles.append(VehicleLocation(**doc))
            
            return vehicles
            
        except Exception as e:
            logger.error(f"Error getting vehicles in area: {e}")
            return []

    async def _create_history_entry(self, current_location: VehicleLocation, previous_location: Optional[VehicleLocation], metadata: Dict[str, Any]):
        """Create location history entry"""
        try:
            # Determine event type
            event_type = "location"
            event_description = "Location update"
            
            if previous_location:
                # Check for significant events
                if previous_location.status != current_location.status:
                    if current_location.status == "active":
                        event_type = "start"
                        event_description = "Vehicle started"
                    elif current_location.status == "idle":
                        event_type = "idle"
                        event_description = "Vehicle idle"
                    elif current_location.status == "maintenance":
                        event_type = "maintenance"
                        event_description = "Vehicle in maintenance"
                
                # Check for speed violations
                if current_location.speed and current_location.speed > 100:  # Speed limit check
                    event_type = "speeding"
                    event_description = f"Speed violation: {current_location.speed} km/h"
            
            # Create history entry
            history_entry = LocationHistory(
                vehicle_id=current_location.vehicle_id,
                coordinates=current_location.coordinates,
                timestamp=current_location.timestamp,
                speed=current_location.speed,
                heading=current_location.heading,
                event_type=event_type,
                event_description=event_description,
                driver_id=current_location.driver_id,
                metadata=metadata
            )
            
            collection = await get_collection(collections.LOCATION_HISTORY)
            await collection.insert_one(history_entry.dict(by_alias=True, exclude={"id"}))
            
        except Exception as e:
            logger.error(f"Error creating history entry: {e}")

    async def _process_location_events(self, current_location: VehicleLocation, previous_location: Optional[VehicleLocation]):
        """Process location-based events"""
        try:
            # Check for idle detection
            if current_location.speed is not None and current_location.speed < 5:  # Less than 5 km/h
                last_update = self.last_update_times.get(current_location.vehicle_id)
                if last_update:
                    idle_duration = (datetime.utcnow() - last_update).total_seconds()
                    if idle_duration > 300:  # 5 minutes idle
                        await publish_vehicle_idle(
                            current_location.vehicle_id,
                            {
                                "duration_seconds": idle_duration,
                                "location": current_location.dict(exclude={"id"}),
                                "timestamp": datetime.utcnow()
                            }
                        )
            
        except Exception as e:
            logger.error(f"Error processing location events: {e}")

    async def get_location_analytics(self, vehicle_id: str, days: int = 7) -> Dict[str, Any]:
        """Get location analytics for a vehicle"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days)
            
            collection = await get_collection(collections.LOCATION_HISTORY)
            
            # Aggregate data
            pipeline = [
                {
                    "$match": {
                        "vehicle_id": vehicle_id,
                        "timestamp": {"$gte": start_time, "$lte": end_time}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_distance": {"$sum": "$distance"},  # Would need to calculate this
                        "avg_speed": {"$avg": "$speed"},
                        "max_speed": {"$max": "$speed"},
                        "total_records": {"$sum": 1},
                        "speed_violations": {
                            "$sum": {"$cond": [{"$gt": ["$speed", 100]}, 1, 0]}
                        }
                    }
                }
            ]
            
            cursor = collection.aggregate(pipeline)
            result = await cursor.to_list(length=1)
            
            if result:
                analytics = result[0]
                analytics.pop("_id", None)
                return analytics
            
            return {
                "total_distance": 0,
                "avg_speed": 0,
                "max_speed": 0,
                "total_records": 0,
                "speed_violations": 0
            }
            
        except Exception as e:
            logger.error(f"Error getting location analytics: {e}")
            return {}

    async def cleanup_old_locations(self):
        """Cleanup old location data based on retention policy"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=settings.location_retention_days)
            
            collection = await get_collection(collections.LOCATION_HISTORY)
            result = await collection.delete_many({"timestamp": {"$lt": cutoff_date}})
            
            logger.info(f"Cleaned up {result.deleted_count} old location records")
            
        except Exception as e:
            logger.error(f"Error cleaning up old locations: {e}")

# Global service instance
location_service = LocationService()
