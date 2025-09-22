"""
Trip service for managing trip CRUD operations
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId

from repositories.database import db_manager, db_manager_gps, db_manager_management
from schemas.entities import Trip, TripStatus, TripConstraint, VehicleLocation, RouteInfo, TurnByTurnInstruction, RoadDetail, DetailedRouteInfo
from schemas.requests import CreateTripRequest, UpdateTripRequest, TripFilterRequest
from events.publisher import event_publisher
from services.routing_service import routing_service
from services.driver_history_service import DriverHistoryService

logger = logging.getLogger(__name__)


class TripService:
    """Service for managing trips"""
    
    def __init__(self):
        self.db = db_manager
        self.db_gps = db_manager_gps

    async def close(self):
        """Clean up resources"""
        try:
            await routing_service.close()
            logger.info("[TripService] Closed routing service session")
        except Exception as e:
            logger.error(f"[TripService] Error closing routing service: {e}")

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

            # Validate vehicle availability
            logger.debug(f"[TripService.create_trip] Validating vehicle availability for vehicle_id={request.vehicle_id}")
            is_available = await self._check_vehicle_availability(request.vehicle_id, request.scheduled_start_time, request.scheduled_end_time)
            if not is_available:
                logger.warning(f"[TripService.create_trip] Vehicle {request.vehicle_id} is not available for the requested time slot")
                raise ValueError(f"Vehicle {request.vehicle_id} is not available for the requested time period")

            # Create trip entity
            trip_data = request.dict(exclude_unset=True)
            
                        # Always fetch raw route information from Geoapify API for simulation and navigation
            logger.info("[TripService.create_trip] Fetching raw route information from Geoapify API")
            try:
                raw_route_data, basic_route_info = await self._fetch_raw_route_info(request.origin, request.destination, request.waypoints)
                if raw_route_data and basic_route_info:
                    # Store the raw route response for detailed navigation/simulation
                    trip_data["raw_route_response"] = raw_route_data
                    logger.info(f"[TripService.create_trip] Successfully stored raw route response")
                    
                    # Populate route_info from the raw response if not provided
                    if not request.route_info:
                        trip_data["route_info"] = basic_route_info
                        logger.info(f"[TripService.create_trip] Populated route_info from raw response: {basic_route_info['distance']}m, {basic_route_info['duration']}s, {len(basic_route_info['coordinates'])} coordinates")
                else:
                    logger.warning("[TripService.create_trip] Failed to fetch raw route information, continuing without it")
            except Exception as e:
                logger.error(f"[TripService.create_trip] Error fetching raw route info: {e}, continuing without it")
            
            # Extract estimated distance and duration from available route info
            # Handle both object and dict forms of route_info
            route_info = trip_data.get("route_info") or request.route_info
            if route_info:
                # Handle both Pydantic object and dict forms
                if hasattr(route_info, 'distance'):
                    # It's a Pydantic object
                    distance = route_info.distance
                    duration = route_info.duration
                else:
                    # It's a dictionary
                    distance = route_info.get('distance', 0)
                    duration = route_info.get('duration', 0)
                
                # Convert distance from meters to kilometers for estimated_distance
                trip_data["estimated_distance"] = distance / 1000
                # Convert duration from seconds to minutes for estimated_duration
                trip_data["estimated_duration"] = duration / 60
                logger.debug(f"[TripService.create_trip] Extracted estimates: distance={trip_data['estimated_distance']}km, duration={trip_data['estimated_duration']}min")
            
            trip_data.update({
                "created_by": created_by,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "status": TripStatus.SCHEDULED
            })
            logger.debug(f"[TripService.create_trip] Prepared trip_data with keys: {list(trip_data.keys())}")

            # Insert into database
            logger.info("[TripService.create_trip] Inserting trip into database")
            try:
                result = await self.db.trips.insert_one(trip_data)
                logger.info(f"[TripService.create_trip] Trip inserted with _id={result.inserted_id}")
            except Exception as e:
                logger.error(f"[TripService.create_trip] Database insert failed: {e}")
                raise

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
    
    async def update_trip(
        self,
        trip_id: str,
        request: UpdateTripRequest,
        updated_by: str
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
    
    async def delete_trip(self, trip_id: str, deleted_by: str) -> bool:
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
            
            # Set driver status to unavailable when trip starts
            if trip.driver_assignment:
                from repositories.database import db_manager_management
                await db_manager_management.drivers.update_one(
                    {"employee_id": trip.driver_assignment},
                    {"$set": {"status": "unavailable", "updated_at": datetime.utcnow()}}
                )
                logger.info(f"Set driver {trip.driver_assignment} status to unavailable")
            
            # Set vehicle status to unavailable when trip starts
            if trip.vehicle_id:
                from repositories.database import db_manager_management
                await db_manager_management.vehicles.update_one(
                    {"_id": trip.vehicle_id},
                    {"$set": {"status": "unavailable", "updated_at": datetime.utcnow()}}
                )
                logger.info(f"Set vehicle {trip.vehicle_id} status to unavailable")
            
            # Ping sessions are now automatically managed based on trip status
            # No need to manually start/stop sessions - they activate/deactivate based on trip status
            logger.info(f"Trip {trip_id} status set to IN_PROGRESS - ping sessions will auto-activate on next ping")
            
            # Get updated trip
            updated_trip = await self.get_trip_by_id(trip_id)
            
            # Publish event
            await event_publisher.publish_trip_started(updated_trip)
            
            logger.info(f"Started trip {trip_id}")
            return updated_trip
            
        except Exception as e:
            logger.error(f"Failed to start trip {trip_id}: {e}")
            raise

    async def pause_trip(self, trip_id: str, paused_by: str) -> Optional[Trip]:
        """Pause a trip"""
        try:
            trip = await self.get_trip_by_id(trip_id)
            if not trip:
                return None
            
            if trip.status != TripStatus.IN_PROGRESS:
                raise ValueError(f"Trip is not in progress status (current: {trip.status})")
            
            # Update trip status
            update_data = {
                "status": TripStatus.PAUSED,
                "updated_at": datetime.utcnow()
            }
            
            await self.db.trips.update_one(
                {"_id": ObjectId(trip_id)},
                {"$set": update_data}
            )
            
            # Pause the simulation
            from services.simulation_service import simulation_service
            await simulation_service.pause_trip_simulation(trip_id)
            
            # Ping sessions will automatically deactivate when status is not "in_progress"
            logger.info(f"Trip {trip_id} status set to PAUSED - ping sessions will auto-deactivate on next ping")
            
            # Get updated trip
            updated_trip = await self.get_trip_by_id(trip_id)
            
            # Publish event
            await event_publisher.publish_trip_updated(updated_trip, trip)
            
            logger.info(f"Paused trip {trip_id}")
            return updated_trip
            
        except Exception as e:
            logger.error(f"Failed to pause trip {trip_id}: {e}")
            raise

    async def resume_trip(self, trip_id: str, resumed_by: str) -> Optional[Trip]:
        """Resume a paused trip"""
        try:
            trip = await self.get_trip_by_id(trip_id)
            if not trip:
                return None
            
            if trip.status != TripStatus.PAUSED:
                raise ValueError(f"Trip is not in paused status (current: {trip.status})")
            
            # Update trip status
            update_data = {
                "status": TripStatus.IN_PROGRESS,
                "updated_at": datetime.utcnow()
            }
            
            await self.db.trips.update_one(
                {"_id": ObjectId(trip_id)},
                {"$set": update_data}
            )
            
            # Resume the simulation
            from services.simulation_service import simulation_service
            await simulation_service.resume_trip_simulation(trip_id)
            
            # Ping sessions will automatically activate when status is "in_progress" 
            logger.info(f"Trip {trip_id} status set to IN_PROGRESS - ping sessions will auto-activate on next ping")
            
            # Get updated trip
            updated_trip = await self.get_trip_by_id(trip_id)
            
            # Publish event
            await event_publisher.publish_trip_updated(updated_trip, trip)
            
            logger.info(f"Resumed trip {trip_id}")
            return updated_trip
            
        except Exception as e:
            logger.error(f"Failed to resume trip {trip_id}: {e}")
            raise

    async def cancel_trip(self, trip_id: str, cancelled_by: str, reason: str = "cancelled") -> Optional[Trip]:
        """Cancel a trip and move it to history"""
        try:
            trip = await self.get_trip_by_id(trip_id)
            if not trip:
                return None
            
            if trip.status in [TripStatus.COMPLETED, TripStatus.CANCELLED]:
                raise ValueError(f"Trip is already in final status (current: {trip.status})")
            
            # Get the original trip document
            trip_doc = await self.db.trips.find_one({"_id": ObjectId(trip_id)})
            
            if not trip_doc:
                logger.error(f"Trip {trip_id} not found in trips collection")
                return None
            
            # Add cancellation information
            cancellation_time = datetime.utcnow()
            trip_doc.update({
                "actual_end_time": cancellation_time,
                "status": TripStatus.CANCELLED.value,
                "completion_reason": "cancelled",
                "cancellation_reason": reason,
                "moved_to_history_at": cancellation_time,
                "cancelled_by": cancelled_by,
                "updated_at": cancellation_time
            })
            
            # Set driver status back to available when trip is cancelled
            if trip.driver_assignment:
                from repositories.database import db_manager_management
                await db_manager_management.drivers.update_one(
                    {"employee_id": trip.driver_assignment},
                    {"$set": {"status": "available", "updated_at": cancellation_time}}
                )
                logger.info(f"Set driver {trip.driver_assignment} status to available")
            
            # Ping sessions will automatically deactivate when status is not "in_progress"
            logger.info(f"Trip {trip_id} status set to CANCELLED - ping sessions will auto-deactivate")
            
            # Set vehicle status back to available when trip is cancelled
            if trip.vehicle_id:
                from repositories.database import db_manager_management
                await db_manager_management.vehicles.update_one(
                    {"_id": trip.vehicle_id},
                    {"$set": {"status": "available", "updated_at": cancellation_time}}
                )
                logger.info(f"Set vehicle {trip.vehicle_id} status to available")
            
            # Stop the simulation
            from services.simulation_service import simulation_service
            await simulation_service.stop_trip_simulation(trip_id)
            
            # Insert into trip_history collection
            await self.db.trip_history.insert_one(trip_doc)
            logger.info(f"Trip {trip_id} moved to trip_history with status 'cancelled'")
            
            # Remove from active trips collection
            await self.db.trips.delete_one({"_id": ObjectId(trip_id)})
            
            # Update driver history
            if trip.driver_assignment:
                try:
                    driver_history_service = DriverHistoryService(db_manager, db_manager_management)
                    await driver_history_service.update_driver_history_on_trip_completion(
                        driver_id=trip.driver_assignment,
                        trip_id=trip_id,
                        trip_status="cancelled"
                    )
                    logger.info(f"Updated driver history for driver {trip.driver_assignment} after trip cancellation")
                except Exception as e:
                    logger.error(f"Failed to update driver history for cancelled trip {trip_id}: {e}")
            
            # Create trip object for event publishing
            trip_doc["_id"] = str(trip_doc["_id"])
            cancelled_trip = Trip(**trip_doc)
            
            # Publish event
            await event_publisher.publish_trip_updated(cancelled_trip, trip)
            
            logger.info(f"Cancelled trip {trip_id}")
            return cancelled_trip
            
        except Exception as e:
            logger.error(f"Failed to cancel trip {trip_id}: {e}")
            raise
    
    async def complete_trip(self, trip_id: str, completed_by: str) -> Optional[Trip]:
        """Complete a trip and move it to history"""
        try:
            trip = await self.get_trip_by_id(trip_id)
            if not trip:
                return None
            
            if trip.status != TripStatus.IN_PROGRESS:
                raise ValueError(f"Trip is not in progress (current: {trip.status})")
            
            # Get the original trip document
            trip_doc = await self.db.trips.find_one({"_id": ObjectId(trip_id)})
            
            if not trip_doc:
                logger.error(f"Trip {trip_id} not found in trips collection")
                return None
            
            # Add completion information
            completion_time = datetime.utcnow()
            trip_doc.update({
                "status": TripStatus.COMPLETED.value,
                "actual_end_time": completion_time,
                "completion_reason": "completed",
                "completed_by": completed_by,
                "moved_to_history_at": completion_time,
                "updated_at": completion_time
            })
            
            # Set driver status back to available when trip completes
            if trip.driver_assignment:
                from repositories.database import db_manager_management
                await db_manager_management.drivers.update_one(
                    {"employee_id": trip.driver_assignment},
                    {"$set": {"status": "available", "updated_at": completion_time}}
                )
                logger.info(f"Set driver {trip.driver_assignment} status to available")
            
            # Ping sessions will automatically deactivate when status is not "in_progress"
            logger.info(f"Trip {trip_id} status set to COMPLETED - ping sessions will auto-deactivate")
            
            # Set vehicle status back to available when trip completes
            if trip.vehicle_id:
                from repositories.database import db_manager_management
                await db_manager_management.vehicles.update_one(
                    {"_id": trip.vehicle_id},
                    {"$set": {"status": "available", "updated_at": completion_time}}
                )
                logger.info(f"Set vehicle {trip.vehicle_id} status to available")
            
            # Stop the simulation
            from services.simulation_service import simulation_service
            await simulation_service.stop_trip_simulation(trip_id)
            
            # Calculate analytics before moving to history
            completed_trip_temp = Trip(**{**trip_doc, "_id": str(trip_doc["_id"])})
            await self._calculate_trip_analytics(completed_trip_temp)
            
            # Insert into trip_history collection
            await self.db.trip_history.insert_one(trip_doc)
            logger.info(f"Trip {trip_id} moved to trip_history with status 'completed'")
            
            # Remove from active trips collection
            await self.db.trips.delete_one({"_id": ObjectId(trip_id)})
            
            # Update driver history
            if trip.driver_assignment:
                try:
                    driver_history_service = DriverHistoryService(db_manager, db_manager_management)
                    await driver_history_service.update_driver_history_on_trip_completion(
                        driver_id=trip.driver_assignment,
                        trip_id=trip_id,
                        trip_status="completed"
                    )
                    logger.info(f"Updated driver history for driver {trip.driver_assignment} after trip completion")
                except Exception as e:
                    logger.error(f"Failed to update driver history for completed trip {trip_id}: {e}")
            
            # Create trip object for event publishing
            trip_doc["_id"] = str(trip_doc["_id"])
            completed_trip = Trip(**trip_doc)
            
            # Publish event
            await event_publisher.publish_trip_completed(completed_trip)
            
            logger.info(f"Completed trip {trip_id}")
            return completed_trip
            
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
                "status": TripStatus.SCHEDULED.value,
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

    async def _check_vehicle_availability(self, vehicle_id: str, start_time: datetime, end_time: Optional[datetime]) -> bool:
        """Check if a vehicle is available for the given time period"""
        try:
            logger.info(f"[TripService._check_vehicle_availability] Checking availability for vehicle {vehicle_id} from {start_time} to {end_time}")
            
            # Build query to find conflicting trips
            query = {
                "vehicle_id": vehicle_id,
                "status": {"$in": [
                    TripStatus.SCHEDULED.value,
                    TripStatus.IN_PROGRESS.value,
                    TripStatus.PAUSED.value
                ]}
            }
            
            # Check for time conflicts
            if end_time:
                # Check for overlap: new trip starts before existing ends AND new trip ends after existing starts
                time_conflict_query = {
                    "$and": [
                        {"scheduled_start_time": {"$lt": end_time}},
                        {
                            "$or": [
                                {"scheduled_end_time": {"$gt": start_time}},
                                {"scheduled_end_time": None}  # Handle trips without end time
                            ]
                        }
                    ]
                }
                query.update(time_conflict_query)
            else:
                # If no end time provided, check if vehicle has any future trips
                query["scheduled_start_time"] = {"$gte": start_time}
            
            logger.debug(f"[TripService._check_vehicle_availability] Query: {query}")
            
            # Check if any conflicting trips exist
            conflicting_trip = await self.db.trips.find_one(query)
            
            if conflicting_trip:
                logger.warning(f"[TripService._check_vehicle_availability] Vehicle {vehicle_id} has conflicting trip: {conflicting_trip['_id']}")
                return False
            
            logger.info(f"[TripService._check_vehicle_availability] Vehicle {vehicle_id} is available")
            return True
            
        except Exception as e:
            logger.error(f"[TripService._check_vehicle_availability] Error checking vehicle availability: {e}")
            # Default to unavailable on error for safety
            return False

    async def _fetch_route_info(self, origin, destination, waypoints=None) -> Optional[RouteInfo]:
        """
        Fetch detailed route information using the routing service
        
        Args:
            origin: Trip origin waypoint
            destination: Trip destination waypoint  
            waypoints: Optional intermediate waypoints
            
        Returns:
            RouteInfo object with detailed route data or None if failed
        """
        try:
            logger.info("[TripService._fetch_route_info] Fetching route information from Geoapify")
            
            # Convert waypoints to format expected by routing service
            formatted_waypoints = routing_service.format_waypoints_from_trip(
                origin.dict(), 
                destination.dict(), 
                [w.dict() for w in waypoints] if waypoints else None
            )
            
            # Get detailed route information
            route_data = await routing_service.get_detailed_route_info(
                waypoints=formatted_waypoints,
                mode="drive"  # Default to driving mode, could be configurable
            )
            
            # Create RouteInfo object with the fetched data
            route_info = RouteInfo(
                distance=route_data["distance"],
                duration=route_data["duration"],
                coordinates=route_data["coordinates"],
                toll=route_data.get("toll", False),
                ferry=route_data.get("ferry", False),
                instructions=[
                    TurnByTurnInstruction(**instruction) 
                    for instruction in route_data.get("instructions", [])
                ],
                road_details=[
                    RoadDetail(**detail) 
                    for detail in route_data.get("road_details", [])
                ],
                raw_response=route_data.get("raw_response")
            )
            
            logger.info(f"[TripService._fetch_route_info] Successfully fetched route: {route_info.distance}m, {route_info.duration}s")
            return route_info
            
        except Exception as e:
            logger.error(f"[TripService._fetch_route_info] Failed to fetch route information: {e}")
            return None

    async def _fetch_raw_route_info(self, origin, destination, waypoints=None):
        """
        Fetch raw route information from Geoapify API and extract basic route_info
        
        Args:
            origin: Trip origin waypoint
            destination: Trip destination waypoint  
            waypoints: Optional intermediate waypoints
            
        Returns:
            Tuple of (raw_route_data, basic_route_info) or (None, None) if failed
        """
        try:
            logger.info("[TripService._fetch_raw_route_info] Fetching raw route information from Geoapify")
            
            # Convert waypoints to format expected by routing service
            formatted_waypoints = routing_service.format_waypoints_from_trip(
                origin.dict(), 
                destination.dict(), 
                [w.dict() for w in waypoints] if waypoints else None
            )
            
            # Get raw route information
            raw_route_data = await routing_service.get_raw_route_info(
                waypoints=formatted_waypoints,
                mode="drive"  # Default to driving mode, could be configurable
            )
            
            if not raw_route_data or not raw_route_data.get("results"):
                logger.warning("[TripService._fetch_raw_route_info] No route data returned from API")
                return None, None
            
            # Extract basic route info from raw response
            basic_route_info = self._extract_route_info_from_raw(raw_route_data)
            
            logger.info(f"[TripService._fetch_raw_route_info] Successfully fetched raw route data: {basic_route_info.get('distance', 0)}m, {basic_route_info.get('duration', 0)}s")
            return raw_route_data, basic_route_info
            
        except Exception as e:
            logger.error(f"[TripService._fetch_raw_route_info] Failed to fetch raw route information: {e}")
            return None, None

    def _extract_route_info_from_raw(self, raw_route_data):
        """
        Extract basic route_info (bounds, coordinates, distance, duration) from raw API response
        
        Args:
            raw_route_data: Raw Geoapify API response
            
        Returns:
            Dictionary with bounds, coordinates, distance, duration
        """
        try:
            route = raw_route_data["results"][0]
            
            # Extract distance and duration
            distance = route.get("distance", 0)
            duration = route.get("time", 0)
            
            # Extract coordinates from geometry
            coordinates = []
            
            # Check if geometry exists and extract coordinates
            if route.get("geometry") and len(route["geometry"]) > 0:
                # The geometry appears to be an array of coordinate arrays
                geometry_data = route["geometry"][0] if isinstance(route["geometry"], list) else route["geometry"]
                if isinstance(geometry_data, list):
                    # Convert [lon,lat] to [lat,lon] format
                    coordinates = [[coord[1], coord[0]] for coord in geometry_data]
            
            # If no coordinates from geometry, try extracting from legs/steps (fallback)
            if not coordinates and route.get("legs"):
                logger.debug("[TripService._extract_route_info_from_raw] No geometry coordinates, attempting to extract from legs")
                # This is a more complex extraction that would need the step geometry
                # For now, create a simple line between waypoints as fallback
                waypoints = route.get("waypoints", [])
                if len(waypoints) >= 2:
                    first_wp = waypoints[0]
                    last_wp = waypoints[-1]
                    coordinates = [
                        [first_wp.get("lat", 0), first_wp.get("lon", 0)], 
                        [last_wp.get("lat", 0), last_wp.get("lon", 0)]
                    ]
            
            # Calculate bounds from coordinates
            bounds = self._calculate_bounds(coordinates)
            
            logger.debug(f"[TripService._extract_route_info_from_raw] Extracted {len(coordinates)} coordinates")
            
            return {
                "distance": distance,
                "duration": duration, 
                "coordinates": coordinates,
                "bounds": bounds
            }
            
        except Exception as e:
            logger.error(f"[TripService._extract_route_info_from_raw] Failed to extract route info: {e}")
            # Return minimal fallback data
            return {
                "distance": 0,
                "duration": 0,
                "coordinates": [],
                "bounds": {
                    "southWest": {"lat": 0, "lng": 0},
                    "northEast": {"lat": 0, "lng": 0}
                }
            }

    def _calculate_bounds(self, coordinates):
        """
        Calculate bounding box from coordinates
        
        Args:
            coordinates: List of [lat, lon] pairs
            
        Returns:
            Dictionary with southWest and northEast bounds
        """
        if not coordinates:
            return {
                "southWest": {"lat": 0, "lng": 0},
                "northEast": {"lat": 0, "lng": 0}
            }
        
        lats = [coord[0] for coord in coordinates]
        lngs = [coord[1] for coord in coordinates]
        
        return {
            "southWest": {"lat": min(lats), "lng": min(lngs)},
            "northEast": {"lat": max(lats), "lng": max(lngs)}
        }

    async def _fetch_detailed_route_info(self, origin, destination, waypoints=None) -> Optional[DetailedRouteInfo]:
        """
        Fetch comprehensive detailed route information using the routing service
        
        Args:
            origin: Trip origin waypoint
            destination: Trip destination waypoint  
            waypoints: Optional intermediate waypoints
            
        Returns:
            DetailedRouteInfo object with comprehensive route data or None if failed
        """
        try:
            logger.info("[TripService._fetch_detailed_route_info] Fetching detailed route information from Geoapify")
            
            # Convert waypoints to format expected by routing service
            formatted_waypoints = routing_service.format_waypoints_from_trip(
                origin.dict(), 
                destination.dict(), 
                [w.dict() for w in waypoints] if waypoints else None
            )
            
            # Get detailed route information object
            detailed_route_info = await routing_service.get_detailed_route_info_object(
                waypoints=formatted_waypoints,
                mode="drive"  # Default to driving mode, could be configurable
            )
            
            logger.info(f"[TripService._fetch_detailed_route_info] Successfully fetched detailed route: {detailed_route_info.distance}m, {detailed_route_info.duration}s")
            return detailed_route_info
            
        except Exception as e:
            logger.error(f"[TripService._fetch_detailed_route_info] Failed to fetch detailed route information: {e}")
            return None

    async def mark_missed_trips(self) -> int:
        """Mark trips as missed and move them to history"""
        logger.info("[TripService.mark_missed_trips] Checking for missed trips")
        try:
            now = datetime.utcnow()
            missed_count = 0
            
            # Find trips that should be marked as missed
            # 1. Scheduled trips that are 30+ minutes past their scheduled start time
            # 2. Scheduled trips that are past their scheduled end time
            query = {
                "status": TripStatus.SCHEDULED.value,
                "actual_start_time": {"$in": [None, ""]},  # Not started yet
                "$or": [
                    {
                        # 30 minutes past scheduled start time
                        "scheduled_start_time": {"$lte": now - timedelta(minutes=30)}
                    },
                    {
                        # Past scheduled end time (if it exists)
                        "scheduled_end_time": {
                            "$ne": None,
                            "$lte": now
                        }
                    }
                ]
            }
            
            logger.debug(f"[TripService.mark_missed_trips] Query: {query}")
            
            # Find all trips that meet the criteria
            missed_trips_cursor = self.db.trips.find(query)
            
            async for trip_doc in missed_trips_cursor:
                try:
                    trip_id = str(trip_doc["_id"])
                    logger.info(f"[TripService.mark_missed_trips] Marking trip {trip_id} as missed")
                    
                    # Add missed trip information
                    missed_time = now
                    trip_doc.update({
                        "status": TripStatus.MISSED.value,
                        "actual_end_time": missed_time,
                        "completion_reason": "missed",
                        "moved_to_history_at": missed_time,
                        "updated_at": missed_time
                    })
                    
                    # Insert into trip_history collection
                    await self.db.trip_history.insert_one(trip_doc)
                    logger.info(f"Trip {trip_id} moved to trip_history with status 'missed'")
                    
                    # Remove from active trips collection
                    await self.db.trips.delete_one({"_id": trip_doc["_id"]})
                    
                    # Create trip object for event publishing
                    trip_doc["_id"] = str(trip_doc["_id"])
                    missed_trip = Trip(**trip_doc)
                    
                    # Publish event
                    await event_publisher.publish_trip_updated(missed_trip, None)
                    
                    missed_count += 1
                    
                except Exception as e:
                    logger.error(f"[TripService.mark_missed_trips] Failed to mark trip {trip_doc.get('_id')} as missed: {e}")
                    continue
            
            logger.info(f"[TripService.mark_missed_trips] Marked {missed_count} trips as missed")
            return missed_count
            
        except Exception as e:
            logger.error(f"[TripService.mark_missed_trips] Error: {e}")
            raise

    async def get_live_tracking_data(self, trip_id: str) -> Optional[Dict[str, Any]]:
        """
        Get live tracking data for a trip to display on a map
        
        Args:
            trip_id: Trip identifier
            
        Returns:
            Live tracking data including position, route, progress, and navigation info
        """
        try:
            logger.info(f"[TripService.get_live_tracking_data] Getting live data for trip {trip_id}")
            
            # Get trip data
            trip_doc = await self.db.trips.find_one({"_id": ObjectId(trip_id)})
            if not trip_doc:
                logger.warning(f"[TripService.get_live_tracking_data] Trip {trip_id} not found")
                return None
            
            # Get current vehicle position from simulation or GPS
            vehicle_id = trip_doc.get("vehicle_id")
            current_position = None
            is_simulated = False
            
            if vehicle_id:
                # Try to get simulated position first
                from services.simulation_service import simulation_service
                simulated_data = simulation_service.get_vehicle_simulation_data(vehicle_id)
                
                if simulated_data:
                    current_position = {
                        "latitude": simulated_data.get("latitude"),
                        "longitude": simulated_data.get("longitude"),
                        "bearing": simulated_data.get("bearing"),
                        "speed": simulated_data.get("speed"),
                        "accuracy": 5.0,  # Simulated accuracy
                        "timestamp": simulated_data.get("timestamp", datetime.utcnow())
                    }
                    is_simulated = True
                    logger.debug(f"[TripService.get_live_tracking_data] Using simulated position for vehicle {vehicle_id}")
                else:
                    # Fall back to GPS data
                    try:
                        gps_data = await self.db_gps.db.vehicle_locations.find_one(
                            {"vehicle_id": vehicle_id},
                            sort=[("timestamp", -1)]  # Get latest by timestamp
                        )
                        if gps_data:
                            current_position = {
                                "latitude": gps_data.get("latitude"),
                                "longitude": gps_data.get("longitude"),
                                "bearing": gps_data.get("bearing"),
                                "speed": gps_data.get("speed"),
                                "accuracy": gps_data.get("accuracy", 10.0),
                                "timestamp": gps_data.get("timestamp", datetime.utcnow())
                            }
                            logger.debug(f"[TripService.get_live_tracking_data] Using GPS position for vehicle {vehicle_id}")
                    except Exception as e:
                        logger.warning(f"[TripService.get_live_tracking_data] Failed to get GPS data: {e}")
            
            # Default position if none available (use trip origin)
            if not current_position:
                origin_coords = trip_doc.get("origin", {}).get("location", {}).get("coordinates", [0, 0])
                current_position = {
                    "latitude": origin_coords[1] if len(origin_coords) > 1 else 0,
                    "longitude": origin_coords[0] if len(origin_coords) > 0 else 0,
                    "bearing": 0,
                    "speed": 0,
                    "accuracy": 100.0,
                    "timestamp": datetime.utcnow()
                }
                logger.debug(f"[TripService.get_live_tracking_data] Using default origin position")
            
            # Get route information
            route_polyline = []
            remaining_polyline = None
            route_bounds = None
            progress_info = {
                "total_distance": 0,
                "remaining_distance": 0,
                "completed_distance": 0,
                "progress_percentage": 0,
                "estimated_time_remaining": None,
                "current_step_index": None,
                "total_steps": None
            }
            current_instruction = None
            
            # Extract route data from raw_route_response if available
            raw_response = trip_doc.get("raw_route_response")
            if raw_response and raw_response.get("results"):
                route = raw_response["results"][0]
                
                # Get route polyline from geometry
                route_geometry = route.get("geometry")
                if route_geometry and isinstance(route_geometry, list) and len(route_geometry) > 0:
                    # Geometry structure: geometry[0] is an array of coordinate objects
                    # Each coordinate object has {"lon": x, "lat": y} format
                    geometry_coords = route_geometry[0]
                    if isinstance(geometry_coords, list):
                        # Extract all coordinate points and convert to [lat, lon] format
                        route_polyline = []
                        for coord in geometry_coords:
                            if isinstance(coord, dict) and "lat" in coord and "lon" in coord:
                                route_polyline.append([coord["lat"], coord["lon"]])  # [lat, lon]
                        
                        logger.info(f"[TripService.get_live_tracking_data] Extracted {len(route_polyline)} coordinates from geometry")
                    else:
                        logger.warning(f"[TripService.get_live_tracking_data] Geometry[0] is not an array: {type(geometry_coords)}")
                else:
                    logger.warning(f"[TripService.get_live_tracking_data] No valid geometry found")
                
                # Get route bounds from route_info if available
                route_info = trip_doc.get("route_info", {})
                if route_info.get("bounds"):
                    route_bounds = route_info["bounds"]
                
                # Calculate progress based on current position
                total_distance = route.get("distance", 0)
                if total_distance > 0 and route_polyline and current_position:
                    # Extract coordinates safely
                    try:
                        if isinstance(current_position, dict):
                            lat = current_position.get("latitude")
                            lon = current_position.get("longitude")
                        else:
                            logger.warning(f"[TripService.get_live_tracking_data] Unexpected position format: {type(current_position)}")
                            lat, lon = None, None
                        
                        # Validate coordinates are numbers
                        if lat is not None and lon is not None and isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
                            # Find closest point on route to current position
                            closest_index = self._find_closest_point_on_route([lat, lon], route_polyline)
                        else:
                            logger.warning(f"[TripService.get_live_tracking_data] Invalid coordinates: lat={lat}, lon={lon}")
                            closest_index = None
                    except Exception as e:
                        logger.warning(f"[TripService.get_live_tracking_data] Error extracting position: {e}")
                        closest_index = None
                    
                    if closest_index is not None:
                        # Calculate completed and remaining distances
                        completed_distance = self._calculate_distance_along_route(route_polyline, 0, closest_index)
                        remaining_distance = total_distance - completed_distance
                        progress_percentage = (completed_distance / total_distance) * 100
                        
                        progress_info.update({
                            "total_distance": total_distance,
                            "remaining_distance": max(0, remaining_distance),
                            "completed_distance": completed_distance,
                            "progress_percentage": min(100, max(0, progress_percentage))
                        })
                        
                        # Get remaining polyline
                        if closest_index < len(route_polyline) - 1:
                            remaining_polyline = route_polyline[closest_index:]
                
                # Get current navigation instruction from steps
                if route.get("legs") and len(route["legs"]) > 0:
                    steps = route["legs"][0].get("steps", [])
                    if steps:
                        progress_info["total_steps"] = len(steps)
                        
                        # Find current step based on position
                        current_step = self._find_current_step(current_position, steps, route_polyline)
                        if current_step:
                            step_index = current_step.get("index", 0)
                            step_data = current_step.get("step", {})
                            
                            progress_info["current_step_index"] = step_index
                            
                            instruction = step_data.get("instruction", {})
                            current_instruction = {
                                "text": instruction.get("text"),
                                "type": instruction.get("type"),
                                "distance_to_instruction": current_step.get("distance_to_instruction", 0),
                                "road_name": step_data.get("name"),
                                "speed_limit": step_data.get("speed_limit")
                            }
            
            # Fall back to basic route_info if no raw response
            else:
                if trip_doc.get("route_info"):
                    route_info = trip_doc["route_info"]
                    if isinstance(route_info, dict):
                        coords = route_info.get("coordinates", [])
                        # Ensure coordinates are in [lat, lon] format
                        if coords and isinstance(coords[0], dict):
                            # Handle format like [{"lat": x, "lon": y}, ...]
                            route_polyline = [[coord.get("lat", 0), coord.get("lon", 0)] for coord in coords if isinstance(coord, dict)]
                        elif coords and isinstance(coords[0], list) and len(coords[0]) >= 2:
                            # Handle format like [[lon, lat], ...] - convert to [lat, lon]
                            route_polyline = [[coord[1], coord[0]] for coord in coords]
                        else:
                            route_polyline = coords
                        route_bounds = route_info.get("bounds")
                        progress_info["total_distance"] = route_info.get("distance", 0)
            
            # Build response
            tracking_data = {
                "trip_id": trip_id,
                "vehicle_id": vehicle_id,
                "driver_id": trip_doc.get("driver_id"),
                "trip_status": trip_doc.get("status", "unknown"),
                
                "current_position": current_position,
                
                "route_polyline": route_polyline,
                "remaining_polyline": remaining_polyline,
                "route_bounds": route_bounds,
                
                "progress": progress_info,
                "current_instruction": current_instruction,
                
                "origin": trip_doc.get("origin", {}),
                "destination": trip_doc.get("destination", {}),
                "scheduled_time": trip_doc.get("scheduled_time"),
                "actual_start_time": trip_doc.get("actual_start_time"),
                
                "is_simulated": is_simulated,
                "last_updated": datetime.utcnow()
            }
            
            logger.info(f"[TripService.get_live_tracking_data] Successfully generated live data for trip {trip_id}")
            return tracking_data
            
        except Exception as e:
            logger.error(f"[TripService.get_live_tracking_data] Error getting live data for trip {trip_id}: {e}")
            raise

    def _find_closest_point_on_route(self, position: List[float], route_coordinates: List[List[float]]) -> Optional[int]:
        """Find the closest point on the route to a given position"""
        if not route_coordinates or not position:
            return None
        
        min_distance = float('inf')
        closest_index = 0
        
        for i, coord in enumerate(route_coordinates):
            distance = self._calculate_distance(position[0], position[1], coord[0], coord[1])
            if distance < min_distance:
                min_distance = distance
                closest_index = i
        
        logger.debug(f"[_find_closest_point_on_route] Position {position} closest to route index {closest_index} with distance {min_distance:.3f}km")
        
        return closest_index

    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate the haversine distance between two points in kilometers"""
        import math
        
        # Validate inputs are numbers
        try:
            lat1 = float(lat1)
            lon1 = float(lon1)
            lat2 = float(lat2)
            lon2 = float(lon2)
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid coordinates for distance calculation: lat1={lat1}, lon1={lon1}, lat2={lat2}, lon2={lon2}")
            return 0.0
        
        # Convert latitude and longitude from degrees to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in kilometers
        earth_radius = 6371.0
        
        return earth_radius * c

    def _calculate_distance_along_route(self, route_coordinates: List[List[float]], start_index: int, end_index: int) -> float:
        """Calculate distance along a route between two indices"""
        if start_index >= end_index or start_index >= len(route_coordinates) or end_index >= len(route_coordinates):
            return 0.0
        
        total_distance = 0.0
        for i in range(start_index, end_index):
            if i + 1 < len(route_coordinates):
                coord1 = route_coordinates[i]
                coord2 = route_coordinates[i + 1]
                total_distance += self._calculate_distance(coord1[0], coord1[1], coord2[0], coord2[1])
        
        return total_distance

    def _find_current_step(self, position: Dict[str, Any], steps: List[Dict], route_coordinates: List[List[float]]) -> Optional[Dict]:
        """Find the current step based on position and route geometry"""
        if not steps or not position or not route_coordinates:
            return None
        
        # Extract latitude and longitude safely
        try:
            if "latitude" in position and "longitude" in position:
                current_pos = [position["latitude"], position["longitude"]]
            elif isinstance(position, (list, tuple)) and len(position) >= 2:
                current_pos = [position[0], position[1]]
            else:
                logger.warning(f"Invalid position format: {position}")
                return None
                
            # Ensure coordinates are numbers
            if not all(isinstance(coord, (int, float)) for coord in current_pos):
                logger.warning(f"Position coordinates are not numbers: {current_pos}")
                return None
                
        except (KeyError, TypeError, IndexError) as e:
            logger.warning(f"Error extracting position coordinates: {e}, position: {position}")
            return None
        
        closest_coord_index = self._find_closest_point_on_route(current_pos, route_coordinates)
        
        if closest_coord_index is None:
            return None
        
        logger.debug(f"[_find_current_step] Current position: {current_pos}, closest coordinate index: {closest_coord_index}")
        
        # Find which step contains this coordinate index
        coord_index = 0
        for i, step in enumerate(steps):
            from_index = step.get("from_index", 0)
            to_index = step.get("to_index", from_index + 1)
            
            logger.debug(f"[_find_current_step] Step {i}: from_index={from_index}, to_index={to_index}, checking if {closest_coord_index} is in range")
            
            if from_index <= closest_coord_index <= to_index:
                logger.debug(f"[_find_current_step] Found current step: {i}")
                # Calculate distance to end of this step
                if to_index < len(route_coordinates):
                    distance_to_instruction = self._calculate_distance_along_route(
                        route_coordinates, closest_coord_index, to_index
                    )
                else:
                    distance_to_instruction = 0
                
                return {
                    "index": i,
                    "step": step,
                    "distance_to_instruction": distance_to_instruction
                }
        
        # Default to first step if no match found
        return {
            "index": 0,
            "step": steps[0] if steps else {},
            "distance_to_instruction": 0
        } if steps else None


# Global instance
trip_service = TripService()
