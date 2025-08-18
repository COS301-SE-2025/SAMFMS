"""
Repository implementations for Management service entities
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

from .base import BaseRepository
from schemas.entities import VehicleAssignment, VehicleUsageLog, Driver, AnalyticsSnapshot, DailyDriverCount

logger = logging.getLogger(__name__)


class DriverCountRepository(BaseRepository):
    """Repository for driver count"""

    def __init__(self):
        super().__init__("drivers_over_time")

    async def get_daily_driver_counts(self, start_date: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """Get all daily driver counts from a certain date"""
        if start_date is not None:
            return await self.collection.find({"date": {"$gt": start_date}})
        else:
            return await self.collection.find({})
        
        
    async def add_driver(self):
        """Add a new driver record with incremented count"""
        max_record = await self.collection.find_one(sort=[("number_of_drivers", -1)])
        max_count = max_record["number_of_drivers"] if max_record else 0

        new_count = max_count + 1

        new_record = {
            "number_of_drivers": new_count,
            "date": datetime.utcnow()
        }

        await self.collection.insert_one(new_record)

    async def remove_driver(self):
        """Remove a driver record with decremented count"""
        max_record = await self.find_one(sort=[("number_of_drivers", -1)])
        max_count = max_record["number_of_drivers"] if max_record else 0

        new_count = max(0, max_count - 1)

        new_record = {
            "number_of_drivers": new_count,
            "date": datetime.utcnow()
        }

        await self.collection.insert_one(new_record)
        
            
        


class VehicleRepository(BaseRepository):
    """Repository for vehicle management"""
    
    def __init__(self):
        super().__init__("vehicles")
    
    async def get_by_registration_number(self, registration_number: str) -> Optional[Dict[str, Any]]:
        """Get vehicle by registration number"""
        return await self.find_one({"registration_number": registration_number})
    
    async def get_by_department(self, department: str) -> List[Dict[str, Any]]:
        """Get vehicles by department"""
        return await self.find(
            filter_query={"department": department},
            sort=[("registration_number", 1)]
        )
    
    async def get_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get vehicles by status"""
        return await self.find(
            filter_query={"status": status},
            sort=[("registration_number", 1)]
        )
    
    async def get_available_vehicles(self) -> List[Dict[str, Any]]:
        """Get all available vehicles"""
        return await self.find(
            filter_query={"status": "available"},
            sort=[("registration_number", 1)]
        )
    
    async def get_vehicle_metrics(self) -> Dict[str, Any]:
        """Get vehicle analytics"""
        pipeline = [
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        status_counts = await self.aggregate(pipeline)
        
        # Get department breakdown
        dept_pipeline = [
            {
                "$group": {
                    "_id": "$department",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        dept_counts = await self.aggregate(dept_pipeline)
        
        # Get type breakdown
        type_pipeline = [
            {
                "$group": {
                    "_id": "$type",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        type_counts = await self.aggregate(type_pipeline)
        
        return {
            "status_breakdown": {item["_id"]: item["count"] for item in status_counts},
            "department_breakdown": {item["_id"]: item["count"] for item in dept_counts},
            "type_breakdown": {item["_id"]: item["count"] for item in type_counts},
            "total_vehicles": await self.count()
        }


class VehicleAssignmentRepository(BaseRepository):
    """Repository for vehicle assignments"""
    
    def __init__(self):
        super().__init__("vehicle_assignments")
    
    async def get_by_vehicle_id(self, vehicle_id: str, status: str = None) -> List[Dict[str, Any]]:
        """Get assignments for a specific vehicle"""
        filter_query = {"vehicle_id": vehicle_id}
        if status:
            filter_query["status"] = status
        
        return await self.find(
            filter_query=filter_query,
            sort=[("created_at", -1)]
        )
    
    async def get_by_driver_id(self, driver_id: str, status: str = None) -> List[Dict[str, Any]]:
        """Get assignments for a specific driver"""
        filter_query = {"driver_id": driver_id}
        if status:
            filter_query["status"] = status
        
        return await self.find(
            filter_query=filter_query,
            sort=[("created_at", -1)]
        )
    
    async def get_active_assignments(self) -> List[Dict[str, Any]]:
        """Get all active assignments"""
        return await self.find(
            filter_query={"status": "active"},
            sort=[("created_at", -1)]
        )
    
    async def complete_assignment(self, assignment_id: str, end_mileage: float = None) -> bool:
        """Complete an assignment"""
        updates = {
            "status": "completed",
            "end_date": datetime.utcnow()
        }
        if end_mileage:
            updates["end_mileage"] = end_mileage
        
        return await self.update(assignment_id, updates)
    
    async def get_assignment_metrics(self) -> Dict[str, Any]:
        """Get assignment analytics"""
        pipeline = [
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        status_counts = await self.aggregate(pipeline)
        
        # Calculate average assignment duration
        duration_pipeline = [
            {
                "$match": {
                    "status": "completed",
                    "end_date": {"$ne": None},
                    "start_date": {"$ne": None}
                }
            },
            {
                "$project": {
                    "duration": {
                        "$subtract": ["$end_date", "$start_date"]
                    }
                }
            },
            {
                "$group": {
                    "_id": None,
                    "avg_duration_ms": {"$avg": "$duration"},
                    "total_assignments": {"$sum": 1}
                }
            }
        ]
        
        duration_stats = await self.aggregate(duration_pipeline)
        
        return {
            "status_breakdown": {item["_id"]: item["count"] for item in status_counts},
            "duration_stats": duration_stats[0] if duration_stats else {}
        }


class VehicleUsageLogRepository(BaseRepository):
    """Repository for vehicle usage logs"""
    
    def __init__(self):
        super().__init__("vehicle_usage_logs")
    
    async def get_by_vehicle_id(self, vehicle_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get usage logs for a vehicle within date range"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        return await self.find(
            filter_query={
                "vehicle_id": vehicle_id,
                "trip_start": {"$gte": start_date}
            },
            sort=[("trip_start", -1)]
        )
    
    async def get_by_driver_id(self, driver_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get usage logs for a driver within date range"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        return await self.find(
            filter_query={
                "driver_id": driver_id,
                "trip_start": {"$gte": start_date}
            },
            sort=[("trip_start", -1)]
        )
    
    async def end_trip(self, usage_id: str, end_data: Dict[str, Any]) -> bool:
        """End a trip and update usage log"""
        updates = {
            "trip_end": datetime.utcnow(),
            **end_data
        }
        
        return await self.update(usage_id, updates)
    
    async def get_vehicle_usage_stats(self) -> List[Dict[str, Any]]:
        """Get usage statistics per vehicle"""
        pipeline = [
            {
                "$group": {
                    "_id": "$vehicle_id",
                    "total_distance": {"$sum": "$distance_km"},
                    "total_fuel": {"$sum": "$fuel_consumed"},
                    "trip_count": {"$sum": 1},
                    "avg_distance": {"$avg": "$distance_km"}
                }
            },
            {
                "$project": {
                    "vehicle_id": "$_id",
                    "total_distance": 1,
                    "total_fuel": 1,
                    "trip_count": 1,
                    "avg_distance": 1,
                    "fuel_efficiency": {
                        "$cond": {
                            "if": {"$gt": ["$total_distance", 0]},
                            "then": {"$divide": ["$total_fuel", "$total_distance"]},
                            "else": 0
                        }
                    }
                }
            }
        ]
        
        return await self.aggregate(pipeline)
    
    async def get_driver_performance_stats(self) -> List[Dict[str, Any]]:
        """Get performance statistics per driver"""
        pipeline = [
            {
                "$group": {
                    "_id": "$driver_id",
                    "total_distance": {"$sum": "$distance_km"},
                    "total_fuel": {"$sum": "$fuel_consumed"},
                    "trip_count": {"$sum": 1},
                    "avg_distance": {"$avg": "$distance_km"}
                }
            }
        ]
        
        return await self.aggregate(pipeline)


class DriverRepository(BaseRepository):
    """Repository for drivers"""
    
    def __init__(self):
        super().__init__("drivers")
    
    async def get_all(self) -> List[Dict[str, Any]]:
        """Retrieve all drivers without any filter"""
        return await self.find(
            filter_query={}
        )

    
    async def get_by_employee_id(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """Get driver by employee ID"""
        return await self.find_one({"employee_id": employee_id})
    
    async def get_by_security_id(self, security_id: str) -> Optional[Dict[str, Any]]:
        """Get driver by security ID"""
        return await self.find_one({"security_id": security_id})
    
    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get driver by email"""
        return await self.find_one({"email": email})
    
    async def get_by_license_number(self, license_number: str) -> Optional[Dict[str, Any]]:
        """Get driver by license number"""
        return await self.find_one({"license_number": license_number})
    
    async def get_active_drivers(self) -> List[Dict[str, Any]]:
        """Get all active drivers"""
        return await self.find(
            filter_query={"status": "active"},
            sort=[("last_name", 1), ("first_name", 1)]
        )
    
    async def get_by_department(self, department: str) -> List[Dict[str, Any]]:
        """Get drivers by department"""
        return await self.find(
            filter_query={"department": department, "status": "active"},
            sort=[("last_name", 1), ("first_name", 1)]
        )
    
    async def assign_vehicle(self, driver_id: str, vehicle_id: str) -> bool:
        """Assign vehicle to driver"""
        return await self.update(driver_id, {"current_vehicle_id": vehicle_id})
    
    async def unassign_vehicle(self, driver_id: str) -> bool:
        """Remove vehicle assignment from driver"""
        return await self.update(driver_id, {"current_vehicle_id": None})
    
    async def search_drivers(self, query: str) -> List[Dict[str, Any]]:
        """Search drivers by name, employee ID, or email"""
        search_filter = {
            "$or": [
                {"first_name": {"$regex": query, "$options": "i"}},
                {"last_name": {"$regex": query, "$options": "i"}},
                {"employee_id": {"$regex": query, "$options": "i"}},
                {"email": {"$regex": query, "$options": "i"}}
            ]
        }
        
        return await self.find(
            filter_query=search_filter,
            sort=[("last_name", 1), ("first_name", 1)]
        )
    
    async def get_last_employee_id(self) -> str:
        """
        Get the last assigned employee ID to determine next ID in sequence.
        Returns 'EMP000' if no employees exist.
        """
        try:
            # Find the last document sorted by employee_id in descending order
            result = await self.find(
                filter_query={"employee_id": {"$regex": "^EMP\\d{3}$"}},
                sort=[("employee_id", -1)],
                limit=1
            )
            
            if not result:
                return "EMP000"
            
            last_id = result[0]["employee_id"]
            # Extract the numeric part
            last_number = int(last_id[3:])
            return f"EMP{last_number:03d}"
            
        except Exception as e:
            logger.error(f"Error getting last employee ID: {str(e)}")
            return "EMP000"


class AnalyticsRepository(BaseRepository):
    """Repository for cached analytics"""
    
    def __init__(self):
        super().__init__("analytics_snapshots")
    
    async def get_cached_metric(self, metric_type: str) -> Optional[Dict[str, Any]]:
        """Get cached analytics metric"""
        return await self.find_one({
            "metric_type": metric_type,
            "expires_at": {"$gt": datetime.utcnow()}
        })
    
    async def cache_metric(self, metric_type: str, data: Dict[str, Any], ttl_minutes: int = 5) -> str:
        """Cache analytics metric with TTL"""
        expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes)
        
        # Remove old cached data for this metric
        await self.collection.delete_many({"metric_type": metric_type})
        
        # Insert new cached data
        snapshot = {
            "metric_type": metric_type,
            "data": data,
            "generated_at": datetime.utcnow(),
            "expires_at": expires_at
        }
        
        return await self.create(snapshot)
    
    async def cleanup_expired(self) -> int:
        """Clean up expired analytics snapshots"""
        return await self.delete_many({
            "expires_at": {"$lt": datetime.utcnow()}
        })


class FuelRecordRepository(BaseRepository):
    """Repository for fuel records"""
    
    def __init__(self):
        super().__init__("fuel_records")
    
    async def get_by_vehicle_id(self, vehicle_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get fuel records for a vehicle within date range"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        return await self.find(
            filter_query={
                "vehicle_id": vehicle_id,
                "purchase_date": {"$gte": start_date}
            },
            sort=[("purchase_date", -1)]
        )
    
    async def get_by_driver_id(self, driver_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get fuel records for a driver within date range"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        return await self.find(
            filter_query={
                "driver_id": driver_id,
                "purchase_date": {"$gte": start_date}
            },
            sort=[("purchase_date", -1)]
        )
    
    async def get_fuel_analytics(self) -> Dict[str, Any]:
        """Get fuel consumption analytics"""
        pipeline = [
            {
                "$group": {
                    "_id": {
                        "vehicle_id": "$vehicle_id",
                        "driver_id": "$driver_id"
                    },
                    "total_liters": {"$sum": "$liters"},
                    "total_cost": {"$sum": "$cost"},
                    "fuel_records": {"$sum": 1},
                    "avg_cost_per_liter": {"$avg": {"$divide": ["$cost", "$liters"]}}
                }
            }
        ]
        
        return await self.aggregate(pipeline)


class MileageRecordRepository(BaseRepository):
    """Repository for mileage records"""
    
    def __init__(self):
        super().__init__("mileage_records")
    
    async def get_by_vehicle_id(self, vehicle_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get mileage records for a vehicle within date range"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        return await self.find(
            filter_query={
                "vehicle_id": vehicle_id,
                "reading_date": {"$gte": start_date}
            },
            sort=[("reading_date", -1)]
        )
    
    async def get_by_driver_id(self, driver_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get mileage records for a driver within date range"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        return await self.find(
            filter_query={
                "driver_id": driver_id,
                "reading_date": {"$gte": start_date}
            },
            sort=[("reading_date", -1)]
        )
    
    async def get_latest_mileage(self, vehicle_id: str) -> Optional[Dict[str, Any]]:
        """Get the latest mileage record for a vehicle"""
        records = await self.find(
            filter_query={"vehicle_id": vehicle_id},
            sort=[("reading_date", -1)],
            limit=1
        )
        return records[0] if records else None


class NotificationRepository(BaseRepository):
    """Repository for notifications"""
    
    def __init__(self):
        super().__init__("notifications")
    
    async def get_by_recipient_id(self, recipient_id: str, status: str = None) -> List[Dict[str, Any]]:
        """Get notifications for a specific recipient"""
        filter_query = {"recipient_id": recipient_id}
        if status:
            filter_query["status"] = status
        
        return await self.find(
            filter_query=filter_query,
            sort=[("created_at", -1)]
        )
    
    async def get_unread_notifications(self, recipient_id: str) -> List[Dict[str, Any]]:
        """Get unread notifications for a recipient"""
        return await self.find(
            filter_query={
                "recipient_id": recipient_id,
                "is_read": False,
                "is_archived": False
            },
            sort=[("created_at", -1)]
        )
    
    async def mark_as_read(self, notification_id: str) -> bool:
        """Mark notification as read"""
        return await self.update(notification_id, {
            "is_read": True,
            "status": "read",
            "read_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
    
    async def mark_as_archived(self, notification_id: str) -> bool:
        """Archive notification"""
        return await self.update(notification_id, {
            "is_archived": True,
            "status": "archived",
            "updated_at": datetime.utcnow()
        })
    
    async def get_notification_count(self, recipient_id: str) -> Dict[str, int]:
        """Get notification counts by status"""
        pipeline = [
            {"$match": {"recipient_id": recipient_id}},
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        counts = await self.aggregate(pipeline)
        return {item["_id"]: item["count"] for item in counts}
