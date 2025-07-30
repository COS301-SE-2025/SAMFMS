"""
Maintenance Schedules Service
Handles business logic for maintenance schedule operations
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from schemas.entities import MaintenanceStatus, MaintenancePriority
from repositories import MaintenanceSchedulesRepository
from utils.vehicle_validator import vehicle_validator

logger = logging.getLogger(__name__)


class MaintenanceSchedulesService:
    """Service for maintenance schedules operations"""
    
    def __init__(self):
        self.repository = MaintenanceSchedulesRepository()
        
    async def create_maintenance_schedule(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new maintenance schedule with business logic"""
        try:
            # Validate required fields
            required_fields = ["vehicle_id", "maintenance_type", "scheduled_date", "title"]
            for field in required_fields:
                if field not in data or not data[field]:
                    raise ValueError(f"Required field '{field}' is missing")
            
            # Validate vehicle_id exists in vehicles collection
            vehicle_exists = await vehicle_validator.validate_vehicle_id(data["vehicle_id"])
            if not vehicle_exists:
                raise ValueError(f"Vehicle ID '{data['vehicle_id']}' does not exist in the vehicles collection")
            
            # Set default values
            if "is_active" not in data:
                data["is_active"] = True
            if "created_at" not in data:
                data["created_at"] = datetime.utcnow()
                
            # Parse datetime if it's a string
            if isinstance(data["scheduled_date"], str):
                data["scheduled_date"] = datetime.fromisoformat(data["scheduled_date"].replace("Z", "+00:00"))
            
            # Set interval defaults if not provided
            if "interval_type" not in data:
                data["interval_type"] = "mileage"
            if "interval_value" not in data:
                data["interval_value"] = self._get_default_interval(data["maintenance_type"])
            
            schedule = await self.repository.create(data)
            logger.info(f"Created maintenance schedule {schedule['id']} for vehicle {data['vehicle_id']}")
            
            return schedule
            
        except Exception as e:
            logger.error(f"Error creating maintenance schedule: {e}")
            raise
            
    async def get_maintenance_schedule(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """Get a maintenance schedule by ID"""
        try:
            return await self.repository.get_by_id(schedule_id)
        except Exception as e:
            logger.error(f"Error fetching maintenance schedule {schedule_id}: {e}")
            raise
            
    async def update_maintenance_schedule(self, schedule_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a maintenance schedule"""
        try:
            # Validate vehicle_id if it's being updated
            if "vehicle_id" in data and data["vehicle_id"]:
                vehicle_exists = await vehicle_validator.validate_vehicle_id(data["vehicle_id"])
                if not vehicle_exists:
                    raise ValueError(f"Vehicle ID '{data['vehicle_id']}' does not exist in the vehicles collection")
            
            # Parse datetime fields if they're strings
            datetime_fields = ["scheduled_date", "last_service_date", "next_due_date"]
            for field in datetime_fields:
                if field in data and isinstance(data[field], str):
                    data[field] = datetime.fromisoformat(data[field].replace("Z", "+00:00"))
            
            # Auto-calculate next due dates based on interval
            if any(field in data for field in ["interval_value", "interval_type", "last_service_date", "last_service_mileage"]):
                await self._calculate_next_due(data)
                
            schedule = await self.repository.update(schedule_id, data)
            if schedule:
                logger.info(f"Updated maintenance schedule {schedule_id}")
            
            return schedule
            
        except Exception as e:
            logger.error(f"Error updating maintenance schedule {schedule_id}: {e}")
            raise
            
    async def delete_maintenance_schedule(self, schedule_id: str) -> bool:
        """Delete a maintenance schedule"""
        try:
            success = await self.repository.delete(schedule_id)
            if success:
                logger.info(f"Deleted maintenance schedule {schedule_id}")
            return success
        except Exception as e:
            logger.error(f"Error deleting maintenance schedule {schedule_id}: {e}")
            raise
            
    async def get_vehicle_maintenance_schedules(self, vehicle_id: str) -> List[Dict[str, Any]]:
        """Get maintenance schedules for a vehicle"""
        try:
            # Validate vehicle_id exists
            vehicle_exists = await vehicle_validator.validate_vehicle_id(vehicle_id)
            if not vehicle_exists:
                raise ValueError(f"Vehicle ID '{vehicle_id}' does not exist in the vehicles collection")
                
            return await self.repository.get_schedules_for_vehicle(vehicle_id)
        except Exception as e:
            logger.error(f"Error fetching maintenance schedules for vehicle {vehicle_id}: {e}")
            raise
            
    async def get_active_schedules(self) -> List[Dict[str, Any]]:
        """Get all active maintenance schedules"""
        try:
            return await self.repository.get_active_schedules()
        except Exception as e:
            logger.error(f"Error fetching active maintenance schedules: {e}")
            raise
            
    async def get_schedules_by_type(self, vehicle_type: str) -> List[Dict[str, Any]]:
        """Get schedules for a vehicle type"""
        try:
            return await self.repository.get_schedules_by_type(vehicle_type)
        except Exception as e:
            logger.error(f"Error fetching schedules for vehicle type {vehicle_type}: {e}")
            raise
    
    async def get_due_schedules(self) -> List[Dict[str, Any]]:
        """Get schedules that are due for execution"""
        try:
            schedules = await self.repository.get_active_schedules()
            now = datetime.utcnow()
            due_schedules = []
            
            for schedule in schedules:
                if self._is_schedule_due(schedule, now):
                    due_schedules.append(schedule)
            
            return due_schedules
        except Exception as e:
            logger.error(f"Error fetching due schedules: {e}")
            raise
    
    async def create_record_from_schedule(self, schedule_id: str) -> Dict[str, Any]:
        """Create a maintenance record from a schedule"""
        try:
            from .maintenance_service import maintenance_records_service
            
            schedule = await self.get_maintenance_schedule(schedule_id)
            if not schedule:
                raise ValueError(f"Schedule {schedule_id} not found")
            
            # Create record data from schedule
            record_data = {
                "vehicle_id": schedule["vehicle_id"],
                "maintenance_type": schedule["maintenance_type"],
                "title": schedule.get("title", f"Scheduled {schedule['maintenance_type']}"),
                "description": schedule.get("description", ""),
                "scheduled_date": schedule.get("next_due_date") or schedule.get("scheduled_date"),
                "schedule_id": schedule_id,
                "status": MaintenanceStatus.SCHEDULED,
                "priority": MaintenancePriority.MEDIUM
            }
            
            record = await maintenance_records_service.create_maintenance_record(record_data)
            
            # Update schedule with last execution
            await self.update_maintenance_schedule(schedule_id, {
                "last_executed": datetime.utcnow(),
                "last_record_id": record["id"]
            })
            
            logger.info(f"Created record {record['id']} from schedule {schedule_id}")
            return record
            
        except Exception as e:
            logger.error(f"Error creating record from schedule {schedule_id}: {e}")
            raise
    
    def _get_default_interval(self, maintenance_type: str) -> int:
        """Get default interval for maintenance type"""
        default_intervals = {
            "oil_change": 10000,      # km
            "brake_service": 20000,   # km
            "tire_rotation": 15000,   # km
            "engine_service": 30000,  # km
            "transmission_service": 50000,  # km
            "coolant_service": 40000, # km
            "battery_service": 25000, # km
            "air_filter": 20000,      # km
            "fuel_filter": 30000,     # km
            "spark_plugs": 40000,     # km
            "belt_replacement": 60000, # km
            "suspension": 80000,      # km
            "exhaust_service": 50000, # km
            "electrical": 30000,      # km
            "bodywork": 20000,        # km
            "other": 15000            # km
        }
        return default_intervals.get(maintenance_type.lower(), 15000)
    
    def _is_schedule_due(self, schedule: Dict[str, Any], current_time: datetime) -> bool:
        """Check if a schedule is due for execution"""
        if not schedule.get("is_active"):
            return False
        
        next_due_date = schedule.get("next_due_date")
        if next_due_date and isinstance(next_due_date, datetime):
            return next_due_date <= current_time
        
        # If no next_due_date, check scheduled_date
        scheduled_date = schedule.get("scheduled_date")
        if scheduled_date and isinstance(scheduled_date, datetime):
            return scheduled_date <= current_time
        
        return False
    
    async def _calculate_next_due(self, data: Dict[str, Any]) -> None:
        """Calculate next due date and mileage based on interval"""
        try:
            interval_type = data.get("interval_type", "mileage")
            interval_value = data.get("interval_value", 0)
            
            if interval_type == "time" and "last_service_date" in data:
                last_service_date = data["last_service_date"]
                if isinstance(last_service_date, str):
                    last_service_date = datetime.fromisoformat(last_service_date.replace("Z", "+00:00"))
                
                if last_service_date and interval_value:
                    next_due = last_service_date + timedelta(days=interval_value)
                    data["next_due_date"] = next_due
            
            elif interval_type == "mileage" and "last_service_mileage" in data:
                last_mileage = data.get("last_service_mileage", 0)
                if last_mileage and interval_value:
                    data["next_due_mileage"] = last_mileage + interval_value
            
            elif interval_type == "both":
                # Calculate both time and mileage
                if "last_service_date" in data and interval_value:
                    last_service_date = data["last_service_date"]
                    if isinstance(last_service_date, str):
                        last_service_date = datetime.fromisoformat(last_service_date.replace("Z", "+00:00"))
                    
                    if last_service_date:
                        next_due = last_service_date + timedelta(days=interval_value)
                        data["next_due_date"] = next_due
                
                if "last_service_mileage" in data and interval_value:
                    last_mileage = data.get("last_service_mileage", 0)
                    if last_mileage:
                        data["next_due_mileage"] = last_mileage + interval_value
                        
        except Exception as e:
            logger.error(f"Error calculating next due: {e}")


# Global service instance
maintenance_schedules_service = MaintenanceSchedulesService()
