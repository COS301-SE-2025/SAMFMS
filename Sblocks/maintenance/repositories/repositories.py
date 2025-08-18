"""
Repository implementations for Maintenance Service entities
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta

from .base import BaseRepository

logger = logging.getLogger(__name__)


class MaintenanceRecordsRepository(BaseRepository):
    """Repository for maintenance records"""
    
    def __init__(self):
        super().__init__("maintenance_records")
        
    async def get_by_vehicle_id(self, vehicle_id: str, 
                               skip: int = 0, 
                               limit: int = 100) -> List[Dict[str, Any]]:
        """Get maintenance records for a specific vehicle"""
        return await self.find(
            query={"vehicle_id": vehicle_id},
            skip=skip,
            limit=limit,
            sort=[("scheduled_date", -1)]
        )
        
    async def get_by_status(self, status: str, 
                           skip: int = 0, 
                           limit: int = 100) -> List[Dict[str, Any]]:
        """Get maintenance records by status"""
        return await self.find(
            query={"status": status},
            skip=skip,
            limit=limit,
            sort=[("scheduled_date", 1)]
        )
        
    async def get_overdue_maintenance(self) -> List[Dict[str, Any]]:
        """Get overdue maintenance records"""
        now = datetime.utcnow()
        return await self.find(
            query={
                "status": {"$in": ["scheduled", "in_progress"]},
                "scheduled_date": {"$lt": now}
            },
            sort=[("scheduled_date", 1)]
        )
        
    async def get_upcoming_maintenance(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Get maintenance scheduled in the next X days"""
        now = datetime.utcnow()
        future_date = now + timedelta(days=days_ahead)
        
        return await self.find(
            query={
                "status": "scheduled",
                "scheduled_date": {
                    "$gte": now,
                    "$lte": future_date
                }
            },
            sort=[("scheduled_date", 1)]
        )
        
    async def get_maintenance_history(self, vehicle_id: str, 
                                    start_date: Optional[datetime] = None,
                                    end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get maintenance history for a vehicle within date range"""
        query = {"vehicle_id": vehicle_id}
        
        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query["$gte"] = start_date
            if end_date:
                date_query["$lte"] = end_date
            query["scheduled_date"] = date_query
            
        return await self.find(
            query=query,
            sort=[("scheduled_date", -1)]
        )
        
    async def get_cost_summary(self, vehicle_id: Optional[str] = None,
                              start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get cost summary for maintenance"""
        pipeline = []
        
        # Match stage
        match_query = {"status": "completed"}
        if vehicle_id:
            match_query["vehicle_id"] = vehicle_id
        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query["$gte"] = start_date
            if end_date:
                date_query["$lte"] = end_date
            match_query["completed_date"] = date_query
            
        pipeline.append({"$match": match_query})
        
        # Group stage
        pipeline.append({
            "$group": {
                "_id": None,
                "total_cost": {"$sum": "$actual_cost"},
                "total_labor_cost": {"$sum": "$labor_cost"},
                "total_parts_cost": {"$sum": "$parts_cost"},
                "average_cost": {"$avg": "$actual_cost"},
                "maintenance_count": {"$sum": 1}
            }
        })
        
        results = await self.aggregate(pipeline)
        return results[0] if results else {}


class MaintenanceSchedulesRepository(BaseRepository):
    """Repository for maintenance schedules"""
    
    def __init__(self):
        super().__init__("maintenance_schedules")
        
    async def get_active_schedules(self) -> List[Dict[str, Any]]:
        """Get all active maintenance schedules"""
        return await self.find(
            query={"is_active": True},
            sort=[("name", 1)]
        )
        
    async def get_schedules_for_vehicle(self, vehicle_id: str) -> List[Dict[str, Any]]:
        """Get schedules for a specific vehicle"""
        return await self.find(
            query={
                "$or": [
                    {"vehicle_id": vehicle_id},
                    {"vehicle_id": None}  # Global schedules
                ],
                "is_active": True
            },
            sort=[("name", 1)]
        )
        
    async def get_schedules_by_type(self, vehicle_type: str) -> List[Dict[str, Any]]:
        """Get schedules for a vehicle type"""
        return await self.find(
            query={
                "$or": [
                    {"vehicle_type": vehicle_type},
                    {"vehicle_type": None}  # Global schedules
                ],
                "is_active": True
            },
            sort=[("name", 1)]
        )


class LicenseRecordsRepository(BaseRepository):
    """Repository for license records"""
    
    def __init__(self):
        super().__init__("license_records")
        
    async def get_by_entity(self, entity_id: str, entity_type: str) -> List[Dict[str, Any]]:
        """Get license records for an entity"""
        return await self.find(
            query={
                "entity_id": entity_id,
                "entity_type": entity_type,
                "is_active": True
            },
            sort=[("expiry_date", 1)]
        )
        
    async def get_expiring_soon(self, days_ahead: int = 30) -> List[Dict[str, Any]]:
        """Get licenses expiring in the next X days"""
        future_date = date.today() + timedelta(days=days_ahead)
        
        return await self.find(
            query={
                "is_active": True,
                "expiry_date": {"$lte": future_date}
            },
            sort=[("expiry_date", 1)]
        )
        
    async def get_expired_licenses(self) -> List[Dict[str, Any]]:
        """Get expired licenses"""
        today = date.today()
        
        return await self.find(
            query={
                "is_active": True,
                "expiry_date": {"$lt": today}
            },
            sort=[("expiry_date", 1)]
        )
        
    async def get_by_license_type(self, license_type: str) -> List[Dict[str, Any]]:
        """Get licenses by type"""
        return await self.find(
            query={
                "license_type": license_type,
                "is_active": True
            },
            sort=[("expiry_date", 1)]
        )


class MaintenanceVendorsRepository(BaseRepository):
    """Repository for maintenance vendors"""
    
    def __init__(self):
        super().__init__("maintenance_vendors")
        
    async def get_active_vendors(self) -> List[Dict[str, Any]]:
        """Get all active vendors"""
        return await self.find(
            query={"is_active": True},
            sort=[("name", 1)]
        )
        
    async def get_preferred_vendors(self) -> List[Dict[str, Any]]:
        """Get preferred vendors"""
        return await self.find(
            query={
                "is_active": True,
                "is_preferred": True
            },
            sort=[("name", 1)]
        )
        
    async def get_vendors_by_service(self, service: str) -> List[Dict[str, Any]]:
        """Get vendors that offer a specific service"""
        return await self.find(
            query={
                "is_active": True,
                "services_offered": {"$in": [service]}
            },
            sort=[("rating", -1), ("name", 1)]
        )
        
    async def update_vendor_stats(self, vendor_id: str, 
                                 job_cost: float, rating: Optional[float] = None):
        """Update vendor statistics after a job"""
        vendor = await self.get_by_id(vendor_id)
        if not vendor:
            return
            
        total_jobs = vendor.get("total_jobs", 0) + 1
        current_avg = vendor.get("average_cost", 0)
        new_avg = ((current_avg * (total_jobs - 1)) + job_cost) / total_jobs
        
        update_data = {
            "total_jobs": total_jobs,
            "average_cost": new_avg
        }
        
        if rating is not None:
            current_rating = vendor.get("rating", 0)
            if current_rating > 0:
                # Update running average of ratings
                new_rating = ((current_rating * (total_jobs - 1)) + rating) / total_jobs
            else:
                new_rating = rating
            update_data["rating"] = new_rating
            
        await self.update(vendor_id, update_data)


class MaintenanceNotificationsRepository(BaseRepository):
    """Repository for maintenance notifications"""
    
    def __init__(self):
        super().__init__("maintenance_notifications")
        
    async def get_pending_notifications(self) -> List[Dict[str, Any]]:
        """Get notifications that need to be sent"""
        now = datetime.utcnow()
        
        return await self.find(
            query={
                "is_sent": False,
                "$or": [
                    {"scheduled_send_time": None},
                    {"scheduled_send_time": {"$lte": now}}
                ]
            },
            sort=[("created_at", 1)]
        )
        
    async def get_user_notifications(self, user_id: str, 
                                   unread_only: bool = False) -> List[Dict[str, Any]]:
        """Get notifications for a specific user"""
        query = {"recipient_user_ids": {"$in": [user_id]}}
        
        if unread_only:
            query["is_read"] = False
            
        return await self.find(
            query=query,
            sort=[("created_at", -1)]
        )
        
    async def mark_as_sent(self, notification_id: str):
        """Mark notification as sent"""
        await self.update(notification_id, {
            "is_sent": True,
            "sent_at": datetime.utcnow()
        })
        
    async def mark_as_read(self, notification_id: str):
        """Mark notification as read"""
        await self.update(notification_id, {
            "is_read": True,
            "read_at": datetime.utcnow()
        })


# Aliases for backward compatibility
MaintenanceRecordRepository = MaintenanceRecordsRepository
