"""
Trip service for managing trip CRUD operations
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId

from repositories.database import db_manager, db_manager_gps
from schemas.entities import Trip, TripStatus, TripConstraint, VehicleLocation, ScheduledTrip
from schemas.requests import CreateTripRequest, UpdateTripRequest, TripFilterRequest, ScheduledTripRequest
from events.publisher import event_publisher

logger = logging.getLogger(__name__)


class TripService:
    """Service for managing trips"""
    
    def __init__(self):
        self.db = db_manager
        self.db_gps = db_manager_gps
    
    async def create_scheduled_trip(
        self,
        request: ScheduledTripRequest,
        created_by: str
    ) -> ScheduledTrip:
        """Create a new scheduled trip"""
        try:
            if request.end_time_window:
                if request.end_time_window <= request.start_time_window:
                    logger.warning("[TripService.create_schduled_trip] Invalid schedule: end <= start")
                    raise ValueError("End time must be after start time")
                
            trip_data = request.model_dump(exclude_unset=True)

            if request.route_info:
                trip_data["estimated_distance"] = request.route_info.distance / 1000
                # Convert duration from seconds to minutes for estimated_duration
                trip_data["estimated_duration"] = request.route_info.duration / 60
                logger.debug(f"[TripService.create_trip] Extracted from route_info: distance={trip_data['estimated_distance']}km, duration={trip_data['estimated_duration']}min")

            trip_data.update({
                "created_by": created_by,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "status": TripStatus.SCHEDULED
            })

            result = await self.db.trips_scheduled.insert_one(trip_data)

            trip = await self.get_trip_by_id_scheduled(str(result.inserted_id))
            if not trip:
                logger.error(f"[TripService.create_scheduled] Failed to retrieve trip after insert (ID={result.inserted_id})")
                raise RuntimeError("Failed to retrieve created trip")
            
            return trip
        except Exception as e:
            logger.error(f"[TripService.create_trip_scheduled] Failed: {e}")
            raise

    async def get_scheduled_trips(self) -> list[ScheduledTrip]:
        """Return all scheduled trips"""
        logger.info("Enter get all scheduled trips")
        try:
            cursor = self.db.trips_scheduled.find({})
            scheduled_trips = []
            async for scheduled_trip_doc in cursor:
                scheduled_trip_doc["_id"] = str(scheduled_trip_doc["_id"])
                scheduled_trips.append(ScheduledTrip**(scheduled_trip_doc))
            return scheduled_trips
        except Exception as e:
            logger.error(f"[TripService.get_scheduled_trips] Failed: {e}")
            raise

    async def create_trip(
        self, 
        request: CreateTripRequest,
        created_by: str
    ) -> Trip:
        """Create a new trip"""
        logger.info(f"[TripService.create_trip] Entered with created_by={created_by}")
        try:
            # Validate schedule
            logger.debug(f"[TripService.create_trip] Validating schedule: start={request.scheduled_start_time}, end={request.scheduled_end_time}")
            if request.scheduled_end_time:
                if request.scheduled_end_time <= request.scheduled_start_time:
                    logger.warning("[TripService.create_trip] Invalid schedule: end <= start")
                    raise ValueError("End time must be after start time")

            # Create trip entity
            trip_data = request.dict(exclude_unset=True)
            
            # If route_info is provided, extract estimated distance and duration
            if request.route_info:
                # Convert distance from meters to kilometers for estimated_distance
                trip_data["estimated_distance"] = request.route_info.distance / 1000
                # Convert duration from seconds to minutes for estimated_duration
                trip_data["estimated_duration"] = request.route_info.duration / 60
                logger.debug(f"[TripService.create_trip] Extracted from route_info: distance={trip_data['estimated_distance']}km, duration={trip_data['estimated_duration']}min")
            
            trip_data.update({
                "created_by": created_by,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "status": TripStatus.SCHEDULED
            })
            logger.debug(f"[TripService.create_trip] Prepared trip_data: {trip_data}")

            # Insert into database
            logger.info("[TripService.create_trip] Inserting trip into database")
            result = await self.db.trips.insert_one(trip_data)
            logger.info(f"[TripService.create_trip] Trip inserted with _id={result.inserted_id}")

            # Retrieve created trip
            logger.info(f"[TripService.create_trip] Fetching created trip with ID={result.inserted_id}")
            trip = await self.get_trip_by_id(str(result.inserted_id))
            if not trip:
                logger.error(f"[TripService.create_trip] Failed to retrieve trip after insert (ID={result.inserted_id})")
                raise RuntimeError("Failed to retrieve created trip")

            # Publish event
            logger.info(f"[TripService.create_trip] Publishing trip.created event for ID={trip.id}")
            await event_publisher.publish_trip_created(trip)

            logger.info(f"[TripService.create_trip] Successfully created trip {trip.id} by user {created_by}")
            return trip

        except Exception as e:
            logger.error(f"[TripService.create_trip] Failed: {e}")
            raise

    async def get_all_trips(self) -> List[Trip]:
        """Return all trips in the database"""
        logger.info("[TripService.get_all_trips] Entered")
        try:
            cursor = self.db.trips.find({})
            trips = []
            async for trip_doc in cursor:
                trip_doc["_id"] = str(trip_doc["_id"])
                trips.append(Trip(**trip_doc))
            logger.info(f"[TripService.get_all_trips] Retrieved {len(trips)} trips")
            return trips
        except Exception as e:
            logger.error(f"[TripService.get_all_trips] Failed: {e}")
            raise
    
    async def get_vehicle_route(self, vehicle_id: str) -> Dict[str,Any]:
        try:
            trip = await self.db.trips.find_one(
                {"vehicle_id": vehicle_id}
            )

            if trip:
                route_info = trip["route_info"]
                return route_info
            return None
        except Exception as e:
            logger.error(f"Error retrieving vehicle route: {e}")
            raise

    async def get_vehicle_location(self, vehicle_id: str) -> VehicleLocation:
        try:
            location = await self.db_gps.db.vehicle_locations.find_one(
                {"vehicle_id": vehicle_id}
            )

            if location:
                location["_id"] = str(location["_id"])
                return VehicleLocation(**location)
            return None
        except Exception as e:
            logger.error(f"Error getting vehicle location: {e}")
            raise

    async def get_vehicle_polyline(self, vehicle_id: str) -> Optional[List[List[float]]]:
        """
        Get the polyline coordinates for a vehicle's route, starting from current location if available
        """
        logger.info(f"[TripService.get_vehicle_polyline] Getting polyline for vehicle {vehicle_id}")
        
        try:
            # Find the active trip for this vehicle
            trip_doc = await self.db.trips.find_one({
                "vehicle_id": vehicle_id
            })
            
            if not trip_doc:
                logger.warning(f"[TripService.get_vehicle_polyline] No active trip found for vehicle {vehicle_id}")
                return None
                
            if not trip_doc.get("route_info") or not trip_doc["route_info"].get("coordinates"):
                logger.warning(f"[TripService.get_vehicle_polyline] No route coordinates found for vehicle {vehicle_id}")
                return None
                
            original_coordinates = trip_doc["route_info"]["coordinates"]
            logger.debug(f"[TripService.get_vehicle_polyline] Found {len(original_coordinates)} original coordinates")
            
            try:
                # Try to get current vehicle location
                logger.debug(f"[TripService.get_vehicle_polyline] Attempting to get current location for vehicle {vehicle_id}")
                current_location = await self.get_vehicle_location(vehicle_id)
                
                if current_location and current_location.latitude and current_location.longitude:
                    logger.info(f"[TripService.get_vehicle_polyline] Found current location: [{current_location.latitude}, {current_location.longitude}]")
                    
                    # Create new polyline starting from current location
                    current_coords = [current_location.latitude, current_location.longitude]
                    
                    # Find the closest point in the original route to minimize route deviation
                    min_distance = float('inf')
                    closest_index = 0
                    
                    for i, coord in enumerate(original_coordinates):
                        # Simple Euclidean distance calculation
                        distance = ((current_coords[0] - coord[0]) ** 2 + (current_coords[1] - coord[1]) ** 2) ** 0.5
                        if distance < min_distance:
                            min_distance = distance
                            closest_index = i
                    
                    logger.debug(f"[TripService.get_vehicle_polyline] Closest route point at index {closest_index}, distance: {min_distance}")
                    
                    # Create polyline starting from current location, then continuing from the closest point forward
                    polyline_coordinates = [current_coords]
                    
                    # Add remaining coordinates from the closest point onwards
                    if closest_index < len(original_coordinates):
                        polyline_coordinates.extend(original_coordinates[closest_index:])
                        
                    logger.info(f"[TripService.get_vehicle_polyline] Created modified polyline with {len(polyline_coordinates)} coordinates")
                    return polyline_coordinates
                    
            except Exception as location_error:
                logger.warning(f"[TripService.get_vehicle_polyline] Failed to get current location for vehicle {vehicle_id}: {location_error}")
            
            # Fallback to original route coordinates if current location is unavailable
            logger.info(f"[TripService.get_vehicle_polyline] Using original route coordinates ({len(original_coordinates)} points)")
            return original_coordinates
            
        except Exception as e:
            logger.error(f"[TripService.get_vehicle_polyline] Failed to get polyline for vehicle {vehicle_id}: {e}")
            raise
    
    async def cancel_trip(self, trip_id: str, reason: str = "cancelled"):
        """Cancel a trip and move it to history (for external cancellation handling)"""
        try:
            # Get the original trip document
            trip_doc = await db_manager.trips.find_one({"_id": ObjectId(trip_id)})
            
            if not trip_doc:
                logger.error(f"Trip {trip_id} not found in trips collection")
                return False
            
            # Add cancellation information
            cancellation_time = datetime.utcnow()
            trip_doc.update({
                "actual_end_time": cancellation_time,
                "status": "cancelled",
                "completion_reason": "cancelled",
                "cancellation_reason": reason,
                "moved_to_history_at": cancellation_time
            })
            
            # Insert into trip_history collection
            await db_manager.trip_history.insert_one(trip_doc)
            logger.info(f"Trip {trip_id} moved to trip_history with status 'cancelled'")
            
            # Remove from active trips collection
            await db_manager.trips.delete_one({"_id": ObjectId(trip_id)})
            
            # Stop simulation if running
            if trip_id in self.active_simulators:
                self.active_simulators[trip_id].is_running = False
                del self.active_simulators[trip_id]
                logger.info(f"Stopped simulation for cancelled trip {trip_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel trip {trip_id}: {e}")
            return False
    
    async def get_active_trips(self, driver_id: str = None) -> List[Trip]:
        """
        Return all active trips (current time >= scheduled_start_time and not completed/canceled),
        optionally filtered by driver
        """
        if driver_id:
            logger.info(f"[TripService.get_active_trips] Getting active trips for driver: {driver_id}")
        else:
            logger.info("[TripService.get_active_trips] Getting all active trips")
        
        try:
            now = datetime.utcnow()
            
            # Base query for active trips
            query = {
                "actual_start_time": {"$lte": now},
            }
            # Add driver filter if provided
            if driver_id:
                query["driver_assignment"] = driver_id
            
            logger.info(f"[TripService.get_active_trips] Query: {query}")
            
            cursor = self.db.trips.find(query)
            trips = []
            
            async for trip_doc in cursor:
                trip_doc["_id"] = str(trip_doc["_id"])
                trips.append(Trip(**trip_doc))
            
            if driver_id:
                logger.info(f"[TripService.get_active_trips] Retrieved {len(trips)} active trips for driver {driver_id}")
            else:
                logger.info(f"[TripService.get_active_trips] Retrieved {len(trips)} active trips")
            return trips
            
        except Exception as e:
            logger.error(f"[TripService.get_active_trips] Failed: {e}")
            raise


    
    async def get_trip_by_id(self, trip_id: str) -> Optional[Trip]:
        """Get trip by ID"""
        try:
            trip_doc = await self.db.trips.find_one({"_id": ObjectId(trip_id)})
            if trip_doc:
                trip_doc["_id"] = str(trip_doc["_id"])
                return Trip(**trip_doc)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get trip {trip_id}: {e}")
            raise
    
    async def get_trip_by_id_scheduled(self, trip_id: str) -> Optional[ScheduledTrip]:
        """Get trip by ID"""
        try:
            trip_doc = await self.db.trips_scheduled.find_one({"_id": ObjectId(trip_id)})
            if trip_doc:
                trip_doc["_id"] = str(trip_doc["_id"])
                return ScheduledTrip(**trip_doc)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get trip {trip_id}: {e}")
            raise
    
    async def update_trip(
        self,
        trip_id: str,
        request: UpdateTripRequest
    ) -> Optional[Trip]:
        """Update an existing trip"""
        try:
            # Get existing trip
            existing_trip = await self.get_trip_by_id(trip_id)
            if not existing_trip:
                return None
            
            # Prepare update data
            update_data = request.dict(exclude_unset=True)
            print(f"DEBUG: update_data = {update_data}")
            update_data["updated_at"] = datetime.utcnow()
            
            # Validate schedule changes
            if "scheduled_end_time" in update_data and "scheduled_start_time" in update_data:
                if update_data["scheduled_end_time"] <= update_data["scheduled_start_time"]:
                    raise ValueError("End time must be after start time")

            
            # Update in database
            result = await self.db.trips.update_one(
                {"_id": ObjectId(trip_id)},
                {"$set": update_data}
            )

            print(f"DEBUG: Modified count = {result.modified_count}")  # Add this
            print(f"DEBUG: Matched count = {result.matched_count}")
            
            if result.modified_count == 0:
                return None
            
            # Get updated trip
            updated_trip = await self.get_trip_by_id(trip_id)
            
            # Publish event
            await event_publisher.publish_trip_updated(updated_trip, existing_trip)
            
            logger.info(f"Updated trip {trip_id}")
            return updated_trip
            
        except Exception as e:
            logger.error(f"Failed to update trip {trip_id}: {e}")
            raise
    
    async def delete_trip(self, trip_id: str) -> bool:
        """Delete a trip"""
        try:
            # Get trip before deletion for event
            trip = await self.get_trip_by_id(trip_id)
            if not trip:
                return False
            
            # Delete from database
            result = await self.db.trips.delete_one({"_id": ObjectId(trip_id)})
            
            if result.deleted_count == 0:
                return False
            
            # Publish event
            await event_publisher.publish_trip_deleted(trip)
            
            logger.info(f"Deleted trip {trip_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete trip {trip_id}: {e}")
            raise
    

    async def get_trip_by_name_and_driver(self, filter_request: TripFilterRequest) -> Trip:
        try:
            query = {}
            if filter_request.driver_assignment:
                query["driver_assignment"] = filter_request.driver_assignment
            if filter_request.name:
                query["name"] = filter_request.name

            trip_data = await self.db.trips.find_one(query)
            if not trip_data:
                raise ValueError("Trip not found")

            trip_data["_id"] = str(trip_data["_id"])

            return Trip(**trip_data)

        except Exception as e:
            logger.error(f"Failed to get trip: {e}")
            raise


    async def list_trips(self, filter_request: TripFilterRequest) -> tuple[List[Trip], int]:
        """List trips with filtering and pagination"""
        try:
            # Build query
            query = {}
            
            if filter_request.status:
                query["status"] = {"$in": filter_request.status}
            
            if filter_request.priority:
                query["priority"] = {"$in": filter_request.priority}
            
            if filter_request.driver_assignment:
                query["driver_assignment"] = filter_request.driver_assignment
            
            if filter_request.name:
                query["name"] = filter_request.name
            
            if filter_request.vehicle_id:
                query["vehicle_id"] = filter_request.vehicle_id
            
            if filter_request.created_by:
                query["created_by"] = filter_request.created_by
            
            # Date filters
            if filter_request.start_date or filter_request.end_date:
                date_query = {}
                if filter_request.start_date:
                    date_query["$gte"] = filter_request.start_date
                if filter_request.end_date:
                    date_query["$lte"] = filter_request.end_date
                query["scheduled_start_time"] = date_query
            
            # Location filters (simplified - would need proper geospatial queries)
            if filter_request.origin_area:
                # TODO: Implement proper geospatial query
                pass
            
            # Get total count
            total = await self.db.trips.count_documents(query)
            
            # Build sort
            sort_field = filter_request.sort_by
            sort_direction = 1 if filter_request.sort_order == "asc" else -1
            
            # Execute query
            cursor = self.db.trips.find(query)
            cursor = cursor.sort(sort_field, sort_direction)
            cursor = cursor.skip(filter_request.skip).limit(filter_request.limit)
            
            trips = []
            async for trip_doc in cursor:
                trip_doc["_id"] = str(trip_doc["_id"])
                trips.append(Trip(**trip_doc))
            
            logger.info(f"Listed {len(trips)} trips (total: {total})")
            return trips
            
        except Exception as e:
            logger.error(f"Failed to list trips: {e}")
            raise
    
    async def start_trip(self, trip_id: str, started_by: str) -> Optional[Trip]:
        """Start a trip"""
        try:
            trip = await self.get_trip_by_id(trip_id)
            if not trip:
                return None
            
            if trip.status != TripStatus.SCHEDULED:
                raise ValueError(f"Trip is not in scheduled status (current: {trip.status})")
            
            # Update trip status
            update_data = {
                "status": TripStatus.IN_PROGRESS,
                "actual_start_time": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            await self.db.trips.update_one(
                {"_id": ObjectId(trip_id)},
                {"$set": update_data}
            )
            
            # Get updated trip
            updated_trip = await self.get_trip_by_id(trip_id)
            
            # Publish event
            await event_publisher.publish_trip_started(updated_trip)
            
            logger.info(f"Started trip {trip_id}")
            return updated_trip
            
        except Exception as e:
            logger.error(f"Failed to start trip {trip_id}: {e}")
            raise
    
    async def complete_trip(self, trip_id: str, completed_by: str) -> Optional[Trip]:
        """Complete a trip"""
        try:
            trip = await self.get_trip_by_id(trip_id)
            if not trip:
                return None
            
            if trip.status != TripStatus.IN_PROGRESS:
                raise ValueError(f"Trip is not in progress (current: {trip.status})")
            
            # Update trip status
            update_data = {
                "status": TripStatus.COMPLETED,
                "actual_end_time": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            await self.db.trips.update_one(
                {"_id": ObjectId(trip_id)},
                {"$set": update_data}
            )
            
            # Get updated trip
            updated_trip = await self.get_trip_by_id(trip_id)
            
            # Calculate analytics
            await self._calculate_trip_analytics(updated_trip)
            
            # Publish event
            await event_publisher.publish_trip_completed(updated_trip)
            
            logger.info(f"Completed trip {trip_id}")
            return updated_trip
            
        except Exception as e:
            logger.error(f"Failed to complete trip {trip_id}: {e}")
            raise
    
    async def _calculate_trip_analytics(self, trip: Trip):
        """Calculate analytics for a completed trip"""
        try:
            if not trip.actual_start_time or not trip.actual_end_time:
                return
            
            # Calculate actual duration
            actual_duration = int((trip.actual_end_time - trip.actual_start_time).total_seconds() / 60)
            
            # Calculate delays
            planned_start = trip.scheduled_start_time
            actual_start = trip.actual_start_time
            delay = max(0, int((actual_start - planned_start).total_seconds() / 60))
            
            # Create analytics record
            analytics_data = {
                "trip_id": trip.id,
                "planned_duration": trip.estimated_duration,
                "actual_duration": actual_duration,
                "planned_distance": trip.estimated_distance,
                "delays": delay,
                "calculated_at": datetime.utcnow()
            }
            
            await self.db.trip_analytics.insert_one(analytics_data)
            
        except Exception as e:
            logger.error(f"Failed to calculate analytics for trip {trip.id}: {e}")

    async def get_all_upcoming_trips(self) -> List[Trip]:
        """Get all upcoming trips regardless of driver"""
        logger.info("[TripService.get_all_upcoming_trips] Getting all upcoming trips")
        try:
            # Current UTC time for filtering
            now = datetime.utcnow()
            
            query = {
                "scheduled_start_time": {"$gte": now},
                "actual_start_time": {"$in": [None, ""]}  # not yet started
            }
            
            logger.debug(f"[TripService.get_all_upcoming_trips] Query: {query}")
            
            # Sort by scheduled start time ascending
            cursor = self.db.trips.find(query).sort("scheduled_start_time", 1)
            trips = []
            
            async for trip_doc in cursor:
                trip_doc["_id"] = str(trip_doc["_id"])
                trips.append(Trip(**trip_doc))
            
            logger.info(f"[TripService.get_all_upcoming_trips] Found {len(trips)} upcoming trips")
            return trips

        except Exception as e:
            logger.error(f"[TripService.get_all_upcoming_trips] Error: {e}")
            raise


    async def get_upcoming_trips(self, driver_id: str) -> List[Trip]:
        """Get upcoming trips for a specific driver"""
        logger.info(f"[TripService.get_upcoming_trips] Getting upcoming trips for driver: {driver_id}")
        try:
            # Get current time for filtering
            now = datetime.utcnow()
            
            query = {
                "driver_assignment": driver_id,
                "scheduled_start_time": {"$gte": now},
                "actual_start_time": {"$in": [None, ""]}  # null or empty string
            }
            
            logger.debug(f"[TripService.get_upcoming_trips] Query: {query}")
            
            # Sort by scheduled start time and limit results
            cursor = self.db.trips.find(query).sort("scheduled_start_time", 1)
            trips = []
            
            async for trip_doc in cursor:
                trip_doc["_id"] = str(trip_doc["_id"])
                trips.append(Trip(**trip_doc))
            
            logger.info(f"[TripService.get_upcoming_trips] Found {len(trips)} upcoming trips")
            return trips
        
        except Exception as e:
            logger.error(f"[TripService.get_upcoming_trips] Error: {e}")
            raise

    async def get_recent_trips(self, driver_id: str, limit: int = 10, days: int = 30) -> List[Trip]:
        """Get recent completed trips for a specific driver"""
        logger.info(f"[TripService.get_recent_trips] Getting recent trips for driver: {driver_id}")
        try:
            # Calculate date range for recent trips
            now = datetime.utcnow()
            start_date = now - timedelta(days=days)
            
            # Query for recent completed trips assigned to this driver
            query = {
                "driver_assignment": driver_id,
                "status": TripStatus.COMPLETED.value,
                "actual_end_time": {
                    "$gte": start_date,
                    "$lte": now
                }
            }
            
            logger.debug(f"[TripService.get_recent_trips] Query: {query}")
            
            # Sort by actual end time (most recent first) and limit results
            cursor = self.db.trip_history.find(query).sort("actual_end_time", -1).limit(limit)
            trips = []
            
            async for trip_doc in cursor:
                trip_doc["_id"] = str(trip_doc["_id"])
                trips.append(Trip(**trip_doc))
            
            logger.info(f"[TripService.get_recent_trips] Found {len(trips)} recent trips")
            return trips
            
        except Exception as e:
            logger.error(f"[TripService.get_recent_trips] Error: {e}")
            raise

    async def get_all_recent_trips(self, limit: int = 10, days: int = 30) -> List[Trip]:
        """Get recent completed trips for all drivers"""
        logger.info(f"[TripService.get_all_recent_trips] Getting recent trips for all drivers")
        try:
            # Calculate date range for recent trips
            now = datetime.utcnow()
            start_date = now - timedelta(days=days)
            
            # Query for recent completed trips from all drivers
            query = {
                "status": TripStatus.COMPLETED.value,
                "actual_end_time": {
                    "$gte": start_date,
                    "$lte": now
                }
            }
            
            logger.debug(f"[TripService.get_all_recent_trips] Query: {query}")
            
            # Sort by actual end time (most recent first) and limit results
            cursor = self.db.trip_history.find(query).sort("actual_end_time", -1).limit(limit)
            trips = []
            
            async for trip_doc in cursor:
                trip_doc["_id"] = str(trip_doc["_id"])
                trips.append(Trip(**trip_doc))
            
            logger.info(f"[TripService.get_all_recent_trips] Found {len(trips)} recent trips")
            return trips
            
        except Exception as e:
            logger.error(f"[TripService.get_all_recent_trips] Error: {e}")
            raise


# Global instance
trip_service = TripService()
