"""
Maintenance Records Service
Handles business logic for maintenance record operations
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from schemas.entities import MaintenanceRecord, MaintenanceStatus, MaintenancePriority
from repositories import MaintenanceRecordsRepository

logger = logging.getLogger(__name__)


class MaintenanceRecordsService:
    """Service for maintenance records operations"""
    
    def __init__(self):
        self.repository = MaintenanceRecordsRepository()
        
    async def create_maintenance_record(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new maintenance record with business logic"""
        try:
            # Validate required fields
            required_fields = ["vehicle_id", "maintenance_type", "scheduled_date", "title"]
            for field in required_fields:
                if field not in data or not data[field]:
                    raise ValueError(f"Required field '{field}' is missing")
            
            # Set default values
            if "status" not in data:
                data["status"] = MaintenanceStatus.SCHEDULED
            if "priority" not in data:
                data["priority"] = MaintenancePriority.MEDIUM
            if "created_at" not in data:
                data["created_at"] = datetime.utcnow()
                
            # Parse datetime if it's a string
            if isinstance(data["scheduled_date"], str):
                data["scheduled_date"] = datetime.fromisoformat(data["scheduled_date"].replace("Z", "+00:00"))
            
            # Auto-determine priority based on maintenance type and urgency
            await self._auto_set_priority(data)
            
            # Set next service mileage if not provided
            if "next_service_mileage" not in data and "mileage_at_service" in data:
                data["next_service_mileage"] = await self._calculate_next_service_mileage(
                    data["vehicle_id"], 
                    data["maintenance_type"], 
                    data["mileage_at_service"]
                )
            
            record = await self.repository.create(data)
            logger.info(f"Created maintenance record {record['id']} for vehicle {data['vehicle_id']}")
            
            # Generate automatic notifications if needed
            await self._generate_automatic_notifications(record)
            
            return record
            
        except Exception as e:
            logger.error(f"Error creating maintenance record: {e}")
            raise
            
    async def get_maintenance_record(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Get a maintenance record by ID"""
        try:
            return await self.repository.get_by_id(record_id)
        except Exception as e:
            logger.error(f"Error fetching maintenance record {record_id}: {e}")
            raise
            
    async def update_maintenance_record(self, record_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a maintenance record"""
        try:
            # Parse datetime fields if they're strings
            datetime_fields = ["scheduled_date", "actual_start_date", "actual_completion_date"]
            for field in datetime_fields:
                if field in data and isinstance(data[field], str):
                    data[field] = datetime.fromisoformat(data[field].replace("Z", "+00:00"))
                    
            # Auto-update status based on dates
            if "actual_start_date" in data and data["actual_start_date"]:
                if "status" not in data or data["status"] == MaintenanceStatus.SCHEDULED:
                    data["status"] = MaintenanceStatus.IN_PROGRESS
                    
            if "actual_completion_date" in data and data["actual_completion_date"]:
                data["status"] = MaintenanceStatus.COMPLETED
                
            record = await self.repository.update(record_id, data)
            if record:
                logger.info(f"Updated maintenance record {record_id}")
            
            return record
            
        except Exception as e:
            logger.error(f"Error updating maintenance record {record_id}: {e}")
            raise
            
    async def delete_maintenance_record(self, record_id: str) -> bool:
        """Delete a maintenance record"""
        try:
            success = await self.repository.delete(record_id)
            if success:
                logger.info(f"Deleted maintenance record {record_id}")
            return success
        except Exception as e:
            logger.error(f"Error deleting maintenance record {record_id}: {e}")
            raise
            
    async def get_vehicle_maintenance_records(self, vehicle_id: str, 
                                            skip: int = 0, 
                                            limit: int = 100) -> List[Dict[str, Any]]:
        """Get maintenance records for a vehicle"""
        try:
            return await self.repository.get_by_vehicle_id(vehicle_id, skip, limit)
        except Exception as e:
            logger.error(f"Error fetching maintenance records for vehicle {vehicle_id}: {e}")
            raise
            
    async def get_maintenance_records_by_status(self, status: str, 
                                              skip: int = 0, 
                                              limit: int = 100) -> List[Dict[str, Any]]:
        """Get maintenance records by status"""
        try:
            return await self.repository.get_by_status(status, skip, limit)
        except Exception as e:
            logger.error(f"Error fetching maintenance records by status {status}: {e}")
            raise
            
    async def get_overdue_maintenance(self) -> List[Dict[str, Any]]:
        """Get overdue maintenance records"""
        try:
            records = await self.repository.get_overdue_maintenance()
            
            # Update status to overdue
            for record in records:
                if record["status"] != MaintenanceStatus.OVERDUE:
                    await self.repository.update(record["id"], {"status": MaintenanceStatus.OVERDUE})
                    record["status"] = MaintenanceStatus.OVERDUE
                    
            return records
        except Exception as e:
            logger.error(f"Error fetching overdue maintenance: {e}")
            raise
            
    async def get_upcoming_maintenance(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Get upcoming maintenance in the next X days"""
        try:
            return await self.repository.get_upcoming_maintenance(days_ahead)
        except Exception as e:
            logger.error(f"Error fetching upcoming maintenance: {e}")
            raise
            
    async def get_maintenance_history(self, vehicle_id: str, 
                                    start_date: Optional[str] = None,
                                    end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get maintenance history for a vehicle"""
        try:
            # Parse date strings
            start_dt = None
            end_dt = None
            
            if start_date:
                start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            if end_date:
                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                
            return await self.repository.get_maintenance_history(vehicle_id, start_dt, end_dt)
        except Exception as e:
            logger.error(f"Error fetching maintenance history for vehicle {vehicle_id}: {e}")
            raise
            
    async def get_maintenance_cost_summary(self, vehicle_id: Optional[str] = None,
                                         start_date: Optional[str] = None,
                                         end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get maintenance cost summary"""
        try:
            # Parse date strings
            start_dt = None
            end_dt = None
            
            if start_date:
                start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            if end_date:
                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                
            return await self.repository.get_cost_summary(vehicle_id, start_dt, end_dt)
        except Exception as e:
            logger.error(f"Error fetching maintenance cost summary: {e}")
            raise
            
    async def search_maintenance_records(self, 
                                       query: Dict[str, Any],
                                       skip: int = 0,
                                       limit: int = 100,
                                       sort_by: str = "scheduled_date",
                                       sort_order: str = "desc") -> List[Dict[str, Any]]:
        """Search maintenance records with complex filters"""
        try:
            # Build MongoDB query from search parameters
            db_query = {}
            
            if "vehicle_id" in query:
                db_query["vehicle_id"] = query["vehicle_id"]
            if "status" in query:
                db_query["status"] = query["status"]
            if "maintenance_type" in query:
                db_query["maintenance_type"] = query["maintenance_type"]
            if "priority" in query:
                db_query["priority"] = query["priority"]
            if "vendor_id" in query:
                db_query["vendor_id"] = query["vendor_id"]
            if "technician_id" in query:
                db_query["assigned_technician"] = query["technician_id"]
                
            # Date range filters
            if "scheduled_from" in query or "scheduled_to" in query:
                date_filter = {}
                if "scheduled_from" in query:
                    date_filter["$gte"] = datetime.fromisoformat(query["scheduled_from"].replace("Z", "+00:00"))
                if "scheduled_to" in query:
                    date_filter["$lte"] = datetime.fromisoformat(query["scheduled_to"].replace("Z", "+00:00"))
                db_query["scheduled_date"] = date_filter
                
            # Sorting
            sort_direction = 1 if sort_order == "asc" else -1
            sort = [(sort_by, sort_direction)]
            
            return await self.repository.find(db_query, skip, limit, sort)
            
        except Exception as e:
            logger.error(f"Error searching maintenance records: {e}")
            raise
    
    async def _auto_set_priority(self, data: Dict[str, Any]) -> None:
        """Automatically set priority based on maintenance type and conditions"""
        try:
            maintenance_type = data.get("maintenance_type", "").lower()
            scheduled_date = data.get("scheduled_date")
            
            # High priority for safety-critical maintenance
            if maintenance_type in ["brake", "tire", "steering", "emergency"]:
                data["priority"] = MaintenancePriority.HIGH
            # Critical for emergency repairs
            elif maintenance_type == "emergency":
                data["priority"] = MaintenancePriority.CRITICAL
            # Check if overdue
            elif scheduled_date and scheduled_date < datetime.utcnow():
                data["priority"] = MaintenancePriority.HIGH
            # Default remains as set
            
        except Exception as e:
            logger.error(f"Error auto-setting priority: {e}")
    
    async def _calculate_next_service_mileage(self, vehicle_id: str, maintenance_type: str, current_mileage: int) -> int:
        """Calculate next service mileage based on maintenance type"""
        try:
            # Standard service intervals (in kilometers)
            service_intervals = {
                "oil_change": 10000,
                "brake_check": 20000,
                "tire_rotation": 15000,
                "general_service": 15000,
                "major_service": 50000,
                "inspection": 25000
            }
            
            interval = service_intervals.get(maintenance_type.lower(), 15000)  # Default 15k km
            return current_mileage + interval
            
        except Exception as e:
            logger.error(f"Error calculating next service mileage: {e}")
            return current_mileage + 15000  # Default fallback
    
    async def _generate_automatic_notifications(self, record: Dict[str, Any]) -> None:
        """Generate automatic notifications for maintenance records"""
        try:
            from services.notification_service import notification_service
            
            # Generate notification for upcoming maintenance (3 days before)
            scheduled_date = record.get("scheduled_date")
            if scheduled_date:
                notification_date = scheduled_date - timedelta(days=3)
                
                if notification_date > datetime.utcnow():
                    notification_data = {
                        "vehicle_id": record["vehicle_id"],
                        "maintenance_record_id": record["id"],
                        "type": "upcoming_maintenance",
                        "priority": record.get("priority", "medium"),
                        "scheduled_send_time": notification_date,
                        "message": f"Maintenance '{record['title']}' scheduled for {scheduled_date.strftime('%Y-%m-%d')}"
                    }
                    
                    await notification_service.create_notification(notification_data)
                    
        except Exception as e:
            logger.error(f"Error generating automatic notifications: {e}")
    
    async def update_overdue_statuses(self) -> List[Dict[str, Any]]:
        """Batch update overdue maintenance records"""
        try:
            now = datetime.utcnow()
            
            # Find scheduled maintenance that's now overdue
            overdue_records = await self.repository.find(
                query={
                    "status": MaintenanceStatus.SCHEDULED,
                    "scheduled_date": {"$lt": now}
                }
            )
            
            updated_records = []
            for record in overdue_records:
                updated_record = await self.repository.update(
                    record["_id"], 
                    {
                        "status": MaintenanceStatus.OVERDUE,
                        "priority": MaintenancePriority.HIGH,
                        "updated_at": now
                    }
                )
                if updated_record:
                    updated_records.append(updated_record)
                    
            logger.info(f"Updated {len(updated_records)} records to overdue status")
            return updated_records
            
        except Exception as e:
            logger.error(f"Error updating overdue statuses: {e}")
            raise
    
    async def calculate_maintenance_costs(self, vehicle_id: Optional[str] = None, 
                                        start_date: Optional[datetime] = None,
                                        end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Calculate comprehensive maintenance costs"""
        try:
            query = {"status": MaintenanceStatus.COMPLETED}
            
            if vehicle_id:
                query["vehicle_id"] = vehicle_id
            if start_date or end_date:
                date_filter = {}
                if start_date:
                    date_filter["$gte"] = start_date
                if end_date:
                    date_filter["$lte"] = end_date
                query["actual_completion_date"] = date_filter
            
            records = await self.repository.find(query=query)
            
            total_cost = 0
            labor_cost = 0
            parts_cost = 0
            record_count = len(records)
            
            cost_by_type = {}
            cost_by_month = {}
            
            for record in records:
                actual_cost = record.get("actual_cost", 0) or 0
                labor = record.get("labor_cost", 0) or 0
                parts = record.get("parts_cost", 0) or 0
                
                total_cost += actual_cost
                labor_cost += labor
                parts_cost += parts
                
                # Cost by maintenance type
                maintenance_type = record.get("maintenance_type", "unknown")
                cost_by_type[maintenance_type] = cost_by_type.get(maintenance_type, 0) + actual_cost
                
                # Cost by month
                completion_date = record.get("actual_completion_date")
                if completion_date:
                    month_key = completion_date.strftime("%Y-%m")
                    cost_by_month[month_key] = cost_by_month.get(month_key, 0) + actual_cost
            
            return {
                "total_cost": total_cost,
                "labor_cost": labor_cost,
                "parts_cost": parts_cost,
                "record_count": record_count,
                "average_cost": total_cost / record_count if record_count > 0 else 0,
                "cost_by_type": cost_by_type,
                "cost_by_month": cost_by_month
            }
            
        except Exception as e:
            logger.error(f"Error calculating maintenance costs: {e}")
            raise
    
    # Alias methods for compatibility with request consumer
    async def get_maintenance_by_vehicle(self, vehicle_id: str, 
                                       skip: int = 0, 
                                       limit: int = 100) -> List[Dict[str, Any]]:
        """Alias for get_vehicle_maintenance_records"""
        return await self.get_vehicle_maintenance_records(vehicle_id, skip, limit)
    
    async def get_maintenance_by_status(self, status: str, 
                                      skip: int = 0, 
                                      limit: int = 100) -> List[Dict[str, Any]]:
        """Alias for get_maintenance_records_by_status"""
        return await self.get_maintenance_records_by_status(status, skip, limit)


# Global service instance
maintenance_records_service = MaintenanceRecordsService()
