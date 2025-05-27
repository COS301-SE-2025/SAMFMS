from typing import List, Optional, Dict, Any
from bson import ObjectId
from datetime import datetime, timedelta
from ..models.models import Schedule, ScheduleStatus, TripPriority
from ..database import get_schedules_collection
from ..messaging.rabbitmq_client import RabbitMQClient


class ScheduleService:
    def __init__(self, messaging_client: RabbitMQClient):
        self.messaging_client = messaging_client
        self.schedules_collection = get_schedules_collection()

    async def create_schedule(self, schedule_data: Dict[str, Any]) -> Schedule:
        """Create a new schedule"""
        schedule = Schedule(**schedule_data)
        
        # Insert into database
        result = await self.schedules_collection.insert_one(schedule.dict(by_alias=True))
        schedule.id = result.inserted_id
        
        # Publish schedule created event
        await self.messaging_client.publish_event(
            "schedule.created",
            {
                "schedule_id": str(schedule.id),
                "trip_id": str(schedule.trip_id),
                "scheduled_departure": schedule.scheduled_departure.isoformat(),
                "scheduled_arrival": schedule.scheduled_arrival.isoformat(),
                "status": schedule.status.value,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return schedule

    async def get_schedule_by_id(self, schedule_id: str) -> Optional[Schedule]:
        """Get schedule by ID"""
        schedule_data = await self.schedules_collection.find_one(
            {"_id": ObjectId(schedule_id)}
        )
        return Schedule(**schedule_data) if schedule_data else None

    async def get_schedules_by_trip(self, trip_id: str) -> List[Schedule]:
        """Get all schedules for a specific trip"""
        cursor = self.schedules_collection.find(
            {"trip_id": ObjectId(trip_id)}
        ).sort("scheduled_departure", 1)
        
        schedules = []
        async for schedule_data in cursor:
            schedules.append(Schedule(**schedule_data))
            
        return schedules

    async def get_schedules(
        self,
        status: Optional[ScheduleStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Schedule]:
        """Get schedules with optional filters"""
        query = {}
        
        if status:
            query["status"] = status.value
            
        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query["$gte"] = start_date
            if end_date:
                date_query["$lte"] = end_date
            query["scheduled_departure"] = date_query
            
        cursor = self.schedules_collection.find(query).skip(skip).limit(limit).sort("scheduled_departure", 1)
        schedules = []
        
        async for schedule_data in cursor:
            schedules.append(Schedule(**schedule_data))
            
        return schedules

    async def get_daily_schedule(self, target_date: datetime) -> List[Schedule]:
        """Get all schedules for a specific day"""
        start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        return await self.get_schedules(
            start_date=start_of_day,
            end_date=end_of_day
        )

    async def get_driver_schedule(
        self,
        driver_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Schedule]:
        """Get schedules for a specific driver"""
        if not start_date:
            start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        if not end_date:
            end_date = start_date + timedelta(days=7)
            
        # First get trip IDs for the driver
        from .trip_service import TripService
        trip_service = TripService(self.messaging_client)
        driver_trips = await trip_service.get_trips_by_driver(driver_id)
        trip_ids = [str(trip.id) for trip in driver_trips]
        
        if not trip_ids:
            return []
            
        query = {
            "trip_id": {"$in": [ObjectId(trip_id) for trip_id in trip_ids]},
            "scheduled_departure": {
                "$gte": start_date,
                "$lte": end_date
            }
        }
        
        cursor = self.schedules_collection.find(query).sort("scheduled_departure", 1)
        schedules = []
        
        async for schedule_data in cursor:
            schedules.append(Schedule(**schedule_data))
            
        return schedules

    async def get_vehicle_schedule(
        self,
        vehicle_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Schedule]:
        """Get schedules for a specific vehicle"""
        if not start_date:
            start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        if not end_date:
            end_date = start_date + timedelta(days=7)
            
        # First get trip IDs for the vehicle
        from .trip_service import TripService
        trip_service = TripService(self.messaging_client)
        vehicle_trips = await trip_service.get_trips_by_vehicle(vehicle_id)
        trip_ids = [str(trip.id) for trip in vehicle_trips]
        
        if not trip_ids:
            return []
            
        query = {
            "trip_id": {"$in": [ObjectId(trip_id) for trip_id in trip_ids]},
            "scheduled_departure": {
                "$gte": start_date,
                "$lte": end_date
            }
        }
        
        cursor = self.schedules_collection.find(query).sort("scheduled_departure", 1)
        schedules = []
        
        async for schedule_data in cursor:
            schedules.append(Schedule(**schedule_data))
            
        return schedules

    async def update_schedule(self, schedule_id: str, update_data: Dict[str, Any]) -> Optional[Schedule]:
        """Update schedule information"""
        update_data["updated_at"] = datetime.utcnow()
        
        result = await self.schedules_collection.update_one(
            {"_id": ObjectId(schedule_id)},
            {"$set": update_data}
        )
        
        if result.modified_count:
            updated_schedule = await self.get_schedule_by_id(schedule_id)
            
            # Publish schedule updated event
            await self.messaging_client.publish_event(
                "schedule.updated",
                {
                    "schedule_id": schedule_id,
                    "updated_fields": list(update_data.keys()),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            return updated_schedule
        return None

    async def update_schedule_status(self, schedule_id: str, status: ScheduleStatus) -> bool:
        """Update schedule status"""
        update_data = {
            "status": status.value,
            "updated_at": datetime.utcnow()
        }
        
        # Add timestamps for specific status changes
        if status == ScheduleStatus.IN_PROGRESS:
            update_data["actual_departure"] = datetime.utcnow()
        elif status == ScheduleStatus.COMPLETED:
            update_data["actual_arrival"] = datetime.utcnow()
        elif status == ScheduleStatus.CANCELLED:
            update_data["cancelled_at"] = datetime.utcnow()
            
        result = await self.schedules_collection.update_one(
            {"_id": ObjectId(schedule_id)},
            {"$set": update_data}
        )
        
        if result.modified_count:
            # Publish status change event
            await self.messaging_client.publish_event(
                "schedule.status_changed",
                {
                    "schedule_id": schedule_id,
                    "new_status": status.value,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            return True
        return False

    async def check_schedule_conflicts(
        self,
        driver_id: Optional[str] = None,
        vehicle_id: Optional[str] = None,
        start_time: datetime = None,
        end_time: datetime = None,
        exclude_schedule_id: Optional[str] = None
    ) -> List[Schedule]:
        """Check for scheduling conflicts"""
        if not start_time or not end_time:
            return []
            
        # Build query for overlapping schedules
        time_overlap_query = {
            "$or": [
                {
                    "scheduled_departure": {"$lt": end_time},
                    "scheduled_arrival": {"$gt": start_time}
                }
            ]
        }
        
        # Add resource-specific filters
        resource_queries = []
        if driver_id:
            # Get trips for this driver
            from .trip_service import TripService
            trip_service = TripService(self.messaging_client)
            driver_trips = await trip_service.get_trips_by_driver(driver_id)
            driver_trip_ids = [trip.id for trip in driver_trips]
            if driver_trip_ids:
                resource_queries.append({
                    "trip_id": {"$in": driver_trip_ids}
                })
                
        if vehicle_id:
            # Get trips for this vehicle
            from .trip_service import TripService
            trip_service = TripService(self.messaging_client)
            vehicle_trips = await trip_service.get_trips_by_vehicle(vehicle_id)
            vehicle_trip_ids = [trip.id for trip in vehicle_trips]
            if vehicle_trip_ids:
                resource_queries.append({
                    "trip_id": {"$in": vehicle_trip_ids}
                })
        
        if not resource_queries:
            return []
            
        # Combine queries
        query = {
            "$and": [
                time_overlap_query,
                {"$or": resource_queries},
                {"status": {"$in": [
                    ScheduleStatus.SCHEDULED.value,
                    ScheduleStatus.IN_PROGRESS.value
                ]}}
            ]
        }
        
        # Exclude current schedule if updating
        if exclude_schedule_id:
            query["_id"] = {"$ne": ObjectId(exclude_schedule_id)}
            
        cursor = self.schedules_collection.find(query)
        conflicts = []
        
        async for schedule_data in cursor:
            conflicts.append(Schedule(**schedule_data))
            
        return conflicts

    async def get_upcoming_schedules(self, hours_ahead: int = 24) -> List[Schedule]:
        """Get schedules starting within the specified hours"""
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=hours_ahead)
        
        query = {
            "scheduled_departure": {
                "$gte": start_time,
                "$lte": end_time
            },
            "status": ScheduleStatus.SCHEDULED.value
        }
        
        cursor = self.schedules_collection.find(query).sort("scheduled_departure", 1)
        schedules = []
        
        async for schedule_data in cursor:
            schedules.append(Schedule(**schedule_data))
            
        return schedules

    async def get_overdue_schedules(self) -> List[Schedule]:
        """Get schedules that are overdue (past scheduled departure time but not started)"""
        current_time = datetime.utcnow()
        
        query = {
            "scheduled_departure": {"$lt": current_time},
            "status": ScheduleStatus.SCHEDULED.value
        }
        
        cursor = self.schedules_collection.find(query).sort("scheduled_departure", 1)
        schedules = []
        
        async for schedule_data in cursor:
            schedules.append(Schedule(**schedule_data))
            
        return schedules

    async def calculate_schedule_efficiency(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Calculate schedule efficiency metrics"""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
            
        pipeline = [
            {
                "$match": {
                    "scheduled_departure": {
                        "$gte": start_date,
                        "$lte": end_date
                    },
                    "status": ScheduleStatus.COMPLETED.value
                }
            },
            {
                "$addFields": {
                    "departure_delay": {
                        "$subtract": ["$actual_departure", "$scheduled_departure"]
                    },
                    "arrival_delay": {
                        "$subtract": ["$actual_arrival", "$scheduled_arrival"]
                    }
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_schedules": {"$sum": 1},
                    "avg_departure_delay": {"$avg": "$departure_delay"},
                    "avg_arrival_delay": {"$avg": "$arrival_delay"},
                    "on_time_departures": {
                        "$sum": {
                            "$cond": [
                                {"$lte": ["$departure_delay", 300000]},  # 5 minutes in milliseconds
                                1, 0
                            ]
                        }
                    },
                    "on_time_arrivals": {
                        "$sum": {
                            "$cond": [
                                {"$lte": ["$arrival_delay", 300000]},  # 5 minutes in milliseconds
                                1, 0
                            ]
                        }
                    }
                }
            }
        ]
        
        async for result in self.schedules_collection.aggregate(pipeline):
            total = result["total_schedules"]
            return {
                "total_completed_schedules": total,
                "average_departure_delay_minutes": result["avg_departure_delay"] / 60000 if result["avg_departure_delay"] else 0,
                "average_arrival_delay_minutes": result["avg_arrival_delay"] / 60000 if result["avg_arrival_delay"] else 0,
                "on_time_departure_rate": (result["on_time_departures"] / total * 100) if total > 0 else 0,
                "on_time_arrival_rate": (result["on_time_arrivals"] / total * 100) if total > 0 else 0
            }
        
        return {
            "total_completed_schedules": 0,
            "average_departure_delay_minutes": 0,
            "average_arrival_delay_minutes": 0,
            "on_time_departure_rate": 0,
            "on_time_arrival_rate": 0
        }

    async def reschedule(
        self,
        schedule_id: str,
        new_departure: datetime,
        new_arrival: datetime
    ) -> Optional[Schedule]:
        """Reschedule a trip"""
        # Check for conflicts with new times
        schedule = await self.get_schedule_by_id(schedule_id)
        if not schedule:
            return None
            
        # You would need to implement logic to get driver and vehicle from trip
        conflicts = await self.check_schedule_conflicts(
            start_time=new_departure,
            end_time=new_arrival,
            exclude_schedule_id=schedule_id
        )
        
        if conflicts:
            # Handle conflicts or raise an exception
            await self.messaging_client.publish_event(
                "schedule.reschedule_conflict",
                {
                    "schedule_id": schedule_id,
                    "conflicts": [str(c.id) for c in conflicts],
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            return None
            
        # Update schedule
        update_data = {
            "scheduled_departure": new_departure,
            "scheduled_arrival": new_arrival,
            "status": ScheduleStatus.RESCHEDULED.value
        }
        
        return await self.update_schedule(schedule_id, update_data)

    async def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a schedule"""
        result = await self.schedules_collection.update_one(
            {"_id": ObjectId(schedule_id)},
            {
                "$set": {
                    "status": ScheduleStatus.CANCELLED.value,
                    "cancelled_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count:
            await self.messaging_client.publish_event(
                "schedule.deleted",
                {
                    "schedule_id": schedule_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            return True
        return False
