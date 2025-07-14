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
        """Create a new maintenance record"""
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
                
            record = await self.repository.create(data)
            logger.info(f"Created maintenance record {record['id']} for vehicle {data['vehicle_id']}")
            
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


# Global service instance
maintenance_records_service = MaintenanceRecordsService()
