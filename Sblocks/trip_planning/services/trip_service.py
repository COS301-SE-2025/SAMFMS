# Trip Management Service
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId

from ..models.models import Trip, TripStatus, TripPriority, Vehicle, Driver, Route, TripEvent
from ..database import get_trips_collection, get_vehicles_collection, get_drivers_collection, get_routes_collection
from ..messaging.rabbitmq_client import rabbitmq_client
from ..utils.route_optimization import optimize_route
from ..utils.scheduling import find_available_resources

class TripService:
    def __init__(self):
        self.trips_collection = get_trips_collection()
        self.vehicles_collection = get_vehicles_collection()
        self.drivers_collection = get_drivers_collection()
        self.routes_collection = get_routes_collection()

    async def create_trip(self, trip_data: Dict[str, Any]) -> Trip:
        """Create a new trip"""
        try:
            # Validate and create trip object
            trip = Trip(**trip_data)
            
            # Auto-assign resources if not specified
            if not trip.vehicle_id or not trip.driver_id:
                available_resources = await self.find_available_resources(
                    trip.scheduled_start,
                    trip.scheduled_end or (trip.scheduled_start + timedelta(hours=8))
                )
                
                if not trip.vehicle_id and available_resources['vehicles']:
                    trip.vehicle_id = available_resources['vehicles'][0]['_id']
                    
                if not trip.driver_id and available_resources['drivers']:
                    trip.driver_id = available_resources['drivers'][0]['_id']
            
            # Generate route if not provided
            if not trip.route_id and trip.destination:
                route = await self.generate_route(trip.origin, trip.destination, trip.waypoints)
                if route:
                    trip.route_id = route.id
                    trip.distance_planned = route.total_distance
                    trip.duration_planned = route.estimated_duration
            
            # Insert into database
            result = await self.trips_collection.insert_one(trip.dict(by_alias=True))
            trip.id = result.inserted_id
            
            # Create trip event
            await self.create_trip_event(trip.id, "trip_created", "Trip created successfully")
            
            # Notify MCore about new trip
            await self.notify_trip_created(trip)
            
            return trip
            
        except Exception as e:
            raise Exception(f"Failed to create trip: {str(e)}")

    async def get_trip(self, trip_id: str) -> Optional[Trip]:
        """Get trip by ID"""
        try:
            trip_doc = await self.trips_collection.find_one({"_id": ObjectId(trip_id)})
            if trip_doc:
                return Trip(**trip_doc)
            return None
        except Exception as e:
            raise Exception(f"Failed to get trip: {str(e)}")

    async def get_trips(self, 
                       status: Optional[TripStatus] = None,
                       vehicle_id: Optional[str] = None,
                       driver_id: Optional[str] = None,
                       date_from: Optional[datetime] = None,
                       date_to: Optional[datetime] = None,
                       limit: int = 100,
                       offset: int = 0) -> List[Trip]:
        """Get trips with filters"""
        try:
            filter_query = {}
            
            if status:
                filter_query["status"] = status
            if vehicle_id:
                filter_query["vehicle_id"] = ObjectId(vehicle_id)
            if driver_id:
                filter_query["driver_id"] = ObjectId(driver_id)
            if date_from or date_to:
                date_filter = {}
                if date_from:
                    date_filter["$gte"] = date_from
                if date_to:
                    date_filter["$lte"] = date_to
                filter_query["scheduled_start"] = date_filter
            
            cursor = self.trips_collection.find(filter_query).skip(offset).limit(limit)
            trips = []
            async for trip_doc in cursor:
                trips.append(Trip(**trip_doc))
            
            return trips
            
        except Exception as e:
            raise Exception(f"Failed to get trips: {str(e)}")

    async def update_trip(self, trip_id: str, update_data: Dict[str, Any]) -> Trip:
        """Update trip"""
        try:
            update_data["updated_at"] = datetime.utcnow()
            
            result = await self.trips_collection.update_one(
                {"_id": ObjectId(trip_id)},
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                raise Exception("Trip not found or no changes made")
            
            updated_trip = await self.get_trip(trip_id)
            
            # Create trip event for significant updates
            if "status" in update_data:
                await self.create_trip_event(
                    ObjectId(trip_id), 
                    f"status_changed_to_{update_data['status']}", 
                    f"Trip status changed to {update_data['status']}"
                )
                
                # Notify MCore about status change
                await self.notify_trip_updated(updated_trip)
            
            return updated_trip
            
        except Exception as e:
            raise Exception(f"Failed to update trip: {str(e)}")

    async def delete_trip(self, trip_id: str) -> bool:
        """Delete trip"""
        try:
            result = await self.trips_collection.delete_one({"_id": ObjectId(trip_id)})
            
            if result.deleted_count > 0:
                await self.create_trip_event(
                    ObjectId(trip_id), 
                    "trip_deleted", 
                    "Trip deleted"
                )
                return True
            return False
            
        except Exception as e:
            raise Exception(f"Failed to delete trip: {str(e)}")

    async def start_trip(self, trip_id: str, location: Dict[str, float]) -> Trip:
        """Start a trip"""
        try:
            update_data = {
                "status": TripStatus.IN_PROGRESS,
                "actual_start": datetime.utcnow(),
                "current_location": location
            }
            
            trip = await self.update_trip(trip_id, update_data)
            
            await self.create_trip_event(
                ObjectId(trip_id),
                "trip_started",
                f"Trip started at {location}",
                location
            )
            
            return trip
            
        except Exception as e:
            raise Exception(f"Failed to start trip: {str(e)}")

    async def complete_trip(self, trip_id: str, location: Dict[str, float], metrics: Dict[str, Any]) -> Trip:
        """Complete a trip"""
        try:
            update_data = {
                "status": TripStatus.COMPLETED,
                "actual_end": datetime.utcnow(),
                "current_location": location,
                "progress_percentage": 100.0
            }
            
            # Add completion metrics
            if "distance_actual" in metrics:
                update_data["distance_actual"] = metrics["distance_actual"]
            if "fuel_consumed" in metrics:
                update_data["fuel_consumed"] = metrics["fuel_consumed"]
            if "duration_actual" in metrics:
                update_data["duration_actual"] = metrics["duration_actual"]
            
            trip = await self.update_trip(trip_id, update_data)
            
            await self.create_trip_event(
                ObjectId(trip_id),
                "trip_completed",
                f"Trip completed at {location}",
                location
            )
            
            return trip
            
        except Exception as e:
            raise Exception(f"Failed to complete trip: {str(e)}")

    async def update_trip_location(self, trip_id: str, location: Dict[str, float], progress: float) -> bool:
        """Update trip current location and progress"""
        try:
            update_data = {
                "current_location": location,
                "progress_percentage": progress,
                "updated_at": datetime.utcnow()
            }
            
            result = await self.trips_collection.update_one(
                {"_id": ObjectId(trip_id)},
                {"$set": update_data}
            )
            
            # Notify MCore about location update
            if result.modified_count > 0:
                await self.notify_trip_location_update(trip_id, location, progress)
            
            return result.modified_count > 0
            
        except Exception as e:
            raise Exception(f"Failed to update trip location: {str(e)}")

    async def find_available_resources(self, start_time: datetime, end_time: datetime) -> Dict[str, List]:
        """Find available vehicles and drivers for a time period"""
        try:
            # Find vehicles not assigned to trips in the time period
            busy_vehicles = await self.trips_collection.distinct(
                "vehicle_id",
                {
                    "status": {"$in": [TripStatus.SCHEDULED, TripStatus.IN_PROGRESS]},
                    "$or": [
                        {"scheduled_start": {"$lte": end_time}, "scheduled_end": {"$gte": start_time}},
                        {"scheduled_start": {"$lte": end_time}, "scheduled_end": None}
                    ]
                }
            )
            
            available_vehicles = []
            async for vehicle in self.vehicles_collection.find({"_id": {"$nin": busy_vehicles}, "status": "active"}):
                available_vehicles.append(vehicle)
            
            # Find drivers not assigned to trips in the time period
            busy_drivers = await self.trips_collection.distinct(
                "driver_id",
                {
                    "status": {"$in": [TripStatus.SCHEDULED, TripStatus.IN_PROGRESS]},
                    "$or": [
                        {"scheduled_start": {"$lte": end_time}, "scheduled_end": {"$gte": start_time}},
                        {"scheduled_start": {"$lte": end_time}, "scheduled_end": None}
                    ]
                }
            )
            
            available_drivers = []
            async for driver in self.drivers_collection.find({"_id": {"$nin": busy_drivers}, "status": "available"}):
                available_drivers.append(driver)
            
            return {
                "vehicles": available_vehicles,
                "drivers": available_drivers
            }
            
        except Exception as e:
            raise Exception(f"Failed to find available resources: {str(e)}")

    async def generate_route(self, origin: Dict[str, Any], destination: Dict[str, Any], waypoints: Optional[List[Dict[str, Any]]] = None) -> Optional[Route]:
        """Generate optimized route"""
        try:
            # Use route optimization utility
            return await optimize_route(origin, destination, waypoints)
        except Exception as e:
            print(f"Failed to generate route: {str(e)}")
            return None

    async def create_trip_event(self, trip_id: ObjectId, event_type: str, description: str, location: Optional[Dict[str, float]] = None):
        """Create a trip event for tracking"""
        try:
            from ..database import TripPlanningDatabase
            events_collection = TripPlanningDatabase.get_collection("trip_events")
            
            event = TripEvent(
                trip_id=trip_id,
                event_type=event_type,
                timestamp=datetime.utcnow(),
                location=location,
                description=description
            )
            
            await events_collection.insert_one(event.dict(by_alias=True))
            
        except Exception as e:
            print(f"Failed to create trip event: {str(e)}")

    async def notify_trip_created(self, trip: Trip):
        """Notify MCore about new trip creation"""
        try:
            trip_data = trip.dict()
            trip_data['id'] = str(trip.id)
            
            rabbitmq_client.publish_to_mcore("trip_created", trip_data)
            rabbitmq_client.publish_trip_event("created", trip_data)
            
        except Exception as e:
            print(f"Failed to notify trip creation: {str(e)}")

    async def notify_trip_updated(self, trip: Trip):
        """Notify MCore about trip updates"""
        try:
            trip_data = trip.dict()
            trip_data['id'] = str(trip.id)
            
            rabbitmq_client.publish_to_mcore("trip_updated", trip_data)
            rabbitmq_client.publish_trip_event("updated", trip_data)
            
        except Exception as e:
            print(f"Failed to notify trip update: {str(e)}")

    async def notify_trip_location_update(self, trip_id: str, location: Dict[str, float], progress: float):
        """Notify MCore about trip location updates"""
        try:
            data = {
                "trip_id": trip_id,
                "location": location,
                "progress": progress,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            rabbitmq_client.publish_to_mcore("trip_location_update", data)
            
        except Exception as e:
            print(f"Failed to notify trip location update: {str(e)}")

# Global service instance
trip_service = TripService()
