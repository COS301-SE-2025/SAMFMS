"""
Driver service for managing driver assignments and availability
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId

from repositories.database import db_manager, db_manager_management
from schemas.entities import DriverAssignment, Trip, TripStatus
from schemas.requests import AssignDriverRequest, DriverAvailabilityRequest
from events.publisher import event_publisher

logger = logging.getLogger(__name__)


class DriverService:
    """Service for managing driver assignments and availability"""
    
    def __init__(self):
        self.db = db_manager
        self.db_management = db_manager_management
    
    async def deactivateDriver(self, driver_id: str):
        """Use this function when a driver was assigned to a trip"""
        try:
            driver = await self.db_management.drivers.find_one({"employee_id": driver_id})
            if not driver:
                raise ValueError("Driver not found")

            await self.db_management.drivers.update_one(
                {"employee_id": driver_id},
                {"$set": {"status": "unavailable", "updated_at": datetime.utcnow()}}
            )

            logger.info(f"Driver {driver_id} deactivated successfully")

        except Exception as e:
            logger.error(f"Error deactivating driver {driver_id}: {e}")
            raise
    
    async def activateDriver(self, driver_id: str):
        """Use this function to mark a driver as active/available"""
        try:
            driver = await self.db_management.drivers.find_one({"employee_id": driver_id})
            if not driver:
                raise ValueError("Driver not found")

            await self.db_management.drivers.update_one(
                {"employee_id": driver_id},
                {"$set": {"status": "available", "updated_at": datetime.utcnow()}}
            )

            logger.info(f"Driver {driver_id} activated successfully")

        except Exception as e:
            logger.error(f"Error activating driver {driver_id}: {e}")
            raise
   
    async def assign_driver_to_trip(
        self,
        trip_id: str,
        request: AssignDriverRequest,
        assigned_by: str
    ) -> Optional[DriverAssignment]:
        """Assign a driver to a trip"""
        try:
            # Check if trip exists
            trip_doc = await self.db.trips.find_one({"_id": ObjectId(trip_id)})
            if not trip_doc:
                raise ValueError("Trip not found")
            
            trip = Trip(**{**trip_doc, "_id": str(trip_doc["_id"])})
            
            # Check if trip is in valid status for assignment
            if trip.status not in [TripStatus.SCHEDULED]:
                raise ValueError(f"Cannot assign driver to trip with status: {trip.status}")
            
            # Check driver availability
            is_available = await self.check_driver_availability(
                request.driver_id,
                trip.scheduled_start_time,
                trip.scheduled_end_time or trip.scheduled_start_time + timedelta(hours=8)
            )
            
            if not is_available:
                raise ValueError("Driver is not available for the requested time period")
            
            # Check if driver is already assigned to this trip
            existing_assignment = await self.db.driver_assignments.find_one({
                "trip_id": trip_id,
                "driver_id": request.driver_id
            })
            
            if existing_assignment:
                raise ValueError("Driver is already assigned to this trip")
            
            # Remove any existing assignment for this trip
            await self.db.driver_assignments.delete_many({"trip_id": trip_id})
            
            # Create new assignment
            assignment_data = {
                "trip_id": trip_id,
                "driver_id": request.driver_id,
                "vehicle_id": request.vehicle_id,
                "assigned_at": datetime.utcnow(),
                "assigned_by": assigned_by,
                "notes": request.notes
            }
            
            result = await self.db.driver_assignments.insert_one(assignment_data)
            
            # Also update the trip document
            await self.db.trips.update_one(
                {"_id": ObjectId(trip_id)},
                {
                    "$set": {
                        "driver_assignment": assignment_data,
                        "vehicle_id": request.vehicle_id,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Create assignment object
            assignment_data["_id"] = str(result.inserted_id)
            assignment = DriverAssignment(**assignment_data)
            
            # Publish event
            await event_publisher.publish_driver_assigned(assignment, trip)
            
            logger.info(f"Assigned driver {request.driver_id} to trip {trip_id}")
            return assignment
            
        except Exception as e:
            logger.error(f"Failed to assign driver to trip {trip_id}: {e}")
            raise
    
    async def unassign_driver_from_trip(
        self,
        trip_id: str,
        unassigned_by: str
    ) -> bool:
        """Remove driver assignment from a trip"""
        try:
            # Get existing assignment
            assignment_doc = await self.db.driver_assignments.find_one({"trip_id": trip_id})
            if not assignment_doc:
                return False
            
            assignment = DriverAssignment(**{**assignment_doc, "_id": str(assignment_doc["_id"])})
            
            # Get trip for validation
            trip_doc = await self.db.trips.find_one({"_id": ObjectId(trip_id)})
            if not trip_doc:
                return False
            
            trip = Trip(**{**trip_doc, "_id": str(trip_doc["_id"])})
            
            # Check if trip allows unassignment
            if trip.status == TripStatus.IN_PROGRESS:
                raise ValueError("Cannot unassign driver from trip in progress")
            
            # Remove assignment
            await self.db.driver_assignments.delete_one({"trip_id": trip_id})
            
            # Update trip document
            await self.db.trips.update_one(
                {"_id": ObjectId(trip_id)},
                {
                    "$unset": {"driver_assignment": "", "vehicle_id": ""},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            # Publish event
            await event_publisher.publish_driver_unassigned(assignment, trip)
            
            logger.info(f"Unassigned driver {assignment.driver_id} from trip {trip_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unassign driver from trip {trip_id}: {e}")
            raise
    
    async def check_driver_availability(
        self,
        driver_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> bool:
        """Check if a driver is available for a time period"""
        try:
            # Find conflicting trips
            conflicting_trips = await self.db.trips.find({
                "driver_assignment": driver_id,
                "status": {"$in": [TripStatus.SCHEDULED, TripStatus.IN_PROGRESS]},
                "$or": [
                    {
                        "scheduled_start_time": {"$lt": end_time},
                        "scheduled_end_time": {"$gt": start_time}
                    },
                    {
                        "scheduled_start_time": {"$lt": end_time},
                        "scheduled_end_time": None,
                        "scheduled_start_time": {"$gte": start_time - timedelta(hours=8)}
                    }
                ]
            }).to_list(length=None)
            
            return len(conflicting_trips) == 0
            
        except Exception as e:
            logger.error(f"Failed to check driver availability: {e}")
            raise
    
    async def get_driver_availability(
        self,
        request: DriverAvailabilityRequest
    ) -> List[Dict[str, Any]]:
        """Get detailed availability information for drivers"""
        try:
            driver_ids = request.driver_ids
            if not driver_ids:
                # Get all active drivers (this would typically come from user service)
                driver_ids = await self._get_all_active_drivers()
            
            availability_results = []
            
            for driver_id in driver_ids:
                is_available = await self.check_driver_availability(
                    driver_id,
                    request.start_time,
                    request.end_time
                )
                
                result = {
                    "driver_id": driver_id,
                    "is_available": is_available
                }
                
                if not is_available:
                    # Get conflicting trips
                    conflicting_trips = await self.db.trips.find({
                        "driver_assignment": driver_id,
                        "status": {"$in": [TripStatus.SCHEDULED, TripStatus.IN_PROGRESS]},
                        "$or": [
                            {
                                "scheduled_start_time": {"$lt": request.end_time},
                                "scheduled_end_time": {"$gt": request.start_time}
                            },
                            {
                                "scheduled_start_time": {"$lt": request.end_time},
                                "scheduled_end_time": None
                            }
                        ]
                    }).to_list(length=None)
                    
                    result["conflicting_trips"] = [str(trip["_id"]) for trip in conflicting_trips]
                    
                    # Find next available time
                    next_available = await self._find_next_available_time(driver_id, request.end_time)
                    result["next_available"] = next_available
                
                availability_results.append(result)
            
            return availability_results
            
        except Exception as e:
            logger.error(f"Failed to get driver availability: {e}")
            raise
    
    async def get_driver_assignments(
        self,
        driver_id: Optional[str] = None,
        trip_id: Optional[str] = None,
        active_only: bool = True
    ) -> List[DriverAssignment]:
        """Get driver assignments with optional filtering"""
        try:
            query = {}
            
            if driver_id:
                query["driver_id"] = driver_id
            
            if trip_id:
                query["trip_id"] = trip_id
            
            if active_only:
                # Get only assignments for non-completed trips
                active_trips = await self.db.trips.find({
                    "status": {"$in": [TripStatus.SCHEDULED, TripStatus.IN_PROGRESS]}
                }, {"_id": 1}).to_list(length=None)
                
                active_trip_ids = [str(trip["_id"]) for trip in active_trips]
                query["trip_id"] = {"$in": active_trip_ids}
            
            assignments = []
            async for assignment_doc in self.db.driver_assignments.find(query):
                assignment_doc["_id"] = str(assignment_doc["_id"])
                assignments.append(DriverAssignment(**assignment_doc))
            
            return assignments
            
        except Exception as e:
            logger.error(f"Failed to get driver assignments: {e}")
            raise

    async def get_all_drivers(self, status: Optional[str] = None, department: Optional[str] = None, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Get all drivers from the drivers collection with optional filtering"""
        try:
            # Build filter query
            filter_query = {}
            if status:
                filter_query["status"] = status
            if department:
                filter_query["department"] = department
            
            # Get total count for pagination
            total_count = await self.db_management.drivers.count_documents(filter_query)
            
            # Get drivers with pagination
            cursor = self.db_management.drivers.find(filter_query).skip(skip).limit(limit)
            drivers_docs = await cursor.to_list(length=None)
            
            # Convert ObjectId to string and clean up the data
            drivers = []
            for doc in drivers_docs:
                if "_id" in doc:
                    doc["id"] = str(doc["_id"])
                    del doc["_id"]
                drivers.append(doc)
            
            logger.info(f"Retrieved {len(drivers)} drivers from database")
            
            return {
                "drivers": drivers,
                "total": total_count,
                "skip": skip,
                "limit": limit,
                "has_more": skip + limit < total_count
            }
            
        except Exception as e:
            logger.error(f"Failed to get all drivers: {e}")
            raise

    async def _get_all_active_drivers(self) -> List[str]:
        """Get all active driver IDs"""
        try:
            # This would typically come from the user/driver service
            # For now, return drivers who have had recent assignments
            recent_assignments = await self.db.driver_assignments.find({
                "assigned_at": {"$gte": datetime.utcnow() - timedelta(days=30)}
            }).to_list(length=None)
            
            driver_ids = list(set(assignment["driver_id"] for assignment in recent_assignments))
            return driver_ids
            
        except Exception as e:
            logger.error(f"Failed to get active drivers: {e}")
            return []
    
    async def _find_next_available_time(
        self,
        driver_id: str,
        after_time: datetime
    ) -> Optional[datetime]:
        """Find the next available time for a driver"""
        try:
            # Find the earliest end time of conflicting trips
            conflicting_trips = await self.db.trips.find({
                "driver_assignment": driver_id,
                "status": {"$in": [TripStatus.SCHEDULED, TripStatus.IN_PROGRESS]},
                "scheduled_start_time": {"$gte": after_time}
            }).sort("scheduled_end_time", 1).to_list(length=1)
            
            if conflicting_trips and conflicting_trips[0].get("scheduled_end_time"):
                return conflicting_trips[0]["scheduled_end_time"]
            
            # If no specific end time, assume 8-hour trips
            if conflicting_trips:
                return conflicting_trips[0]["scheduled_start_time"] + timedelta(hours=8)
            
            # Driver is available after the requested time
            return after_time
            
        except Exception as e:
            logger.error(f"Failed to find next available time for driver {driver_id}: {e}")
            return None


# Global instance
driver_service = DriverService()
