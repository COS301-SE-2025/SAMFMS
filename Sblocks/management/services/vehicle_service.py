
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from repositories.repositories import VehicleRepository, VehicleAssignmentRepository
from events.publisher import event_publisher
from schemas.requests import VehicleCreateRequest, VehicleUpdateRequest

logger = logging.getLogger(__name__)


class VehicleService:
    
    
    def __init__(self):
        self.vehicle_repo = VehicleRepository()
        self.assignment_repo = VehicleAssignmentRepository()
    
    async def get_vehicles(
        self, 
        department: Optional[str] = None,
        status: Optional[str] = None, 
        vehicle_type: Optional[str] = None,
        pagination: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        
        try:
            
            filter_query = {}
            if department:
                filter_query["department"] = department
            if status:
                filter_query["status"] = status
            if vehicle_type:
                filter_query["type"] = vehicle_type
            
            
            if not pagination:
                pagination = {"skip": 0, "limit": 50}
            
            
            vehicles = await self.vehicle_repo.find(
                filter_query=filter_query,
                skip=pagination["skip"],
                limit=pagination["limit"],
                sort=[("registration_number", 1)]
            )
            
            
            if vehicles:
                for vehicle in vehicles:
                    if isinstance(vehicle, dict):
                        for key, value in vehicle.items():
                            if isinstance(value, datetime):
                                vehicle[key] = value.isoformat()
            
            
            total = await self.vehicle_repo.count(filter_query)
            total_pages = (total + pagination["limit"] - 1) // pagination["limit"]
            
            return {
                "vehicles": vehicles,
                "pagination": {
                    "total": total,
                    "page": pagination["skip"] // pagination["limit"] + 1,
                    "page_size": pagination["limit"],
                    "total_pages": total_pages
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting vehicles: {e}")
            raise
    
    async def create_vehicle(self, vehicle_request: VehicleCreateRequest, created_by: str) -> Dict[str, Any]:
        
        try:
            
            reg_number = vehicle_request.registration_number or vehicle_request.license_plate
            if not reg_number:
                raise ValueError("Either registration_number or license_plate must be provided")
            
            
            existing = await self.vehicle_repo.get_by_registration_number(reg_number)
            if existing:
                raise ValueError(f"Vehicle with registration number {reg_number} already exists")
            
            
            vehicle_data = vehicle_request.model_dump()
            
            
            vehicle_data["registration_number"] = reg_number
            if not vehicle_data.get("license_plate"):
                vehicle_data["license_plate"] = reg_number
                
            vehicle_data["created_by"] = created_by
            vehicle_data["created_at"] = datetime.utcnow()
            vehicle_data["updated_at"] = datetime.utcnow()
            
            
            if "status" not in vehicle_data:
                vehicle_data["status"] = "available"
            
            
            vehicle_id = await self.vehicle_repo.create(vehicle_data)
            vehicle = await self.vehicle_repo.get_by_id(vehicle_id)
            
            
            await event_publisher.publish_vehicle_created(vehicle, created_by)
            
            
            if vehicle and isinstance(vehicle, dict):
                for key, value in vehicle.items():
                    if isinstance(value, datetime):
                        vehicle[key] = value.isoformat()
            
            logger.info(f"Created vehicle: {vehicle_id}")
            return vehicle
            
        except ValueError as e:
            logger.warning(f"Vehicle creation validation error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error creating vehicle: {e}")
            raise
    
    async def get_vehicle_by_id(self, vehicle_id: str) -> Optional[Dict[str, Any]]:
        
        try:
            vehicle = await self.vehicle_repo.get_by_id(vehicle_id)
            return vehicle
        except Exception as e:
            logger.error(f"Error getting vehicle {vehicle_id}: {e}")
            raise
    
    async def update_vehicle(self, vehicle_id: str, updates: VehicleUpdateRequest, updated_by: str) -> Dict[str, Any]:
        
        try:
            
            existing_vehicle = await self.vehicle_repo.get_by_id(vehicle_id)
            if not existing_vehicle:
                raise ValueError("Vehicle not found")
            
            
            update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
            
            
            if "registration_number" in update_data:
                existing_reg = await self.vehicle_repo.get_by_registration_number(update_data["registration_number"])
                if existing_reg and existing_reg["_id"] != vehicle_id:
                    raise ValueError(f"Registration number {update_data['registration_number']} already in use")
            
            
            update_data["updated_by"] = updated_by
            update_data["updated_at"] = datetime.utcnow()
            
            
            changes = {}
            for key, new_value in update_data.items():
                if key in existing_vehicle and existing_vehicle[key] != new_value:
                    changes[key] = {
                        "old": existing_vehicle[key],
                        "new": new_value
                    }
            
            
            success = await self.vehicle_repo.update(vehicle_id, update_data)
            if not success:
                raise ValueError("Failed to update vehicle")
            
            
            updated_vehicle = await self.vehicle_repo.get_by_id(vehicle_id)
            
            
            if changes:
                await event_publisher.publish_vehicle_updated(
                    updated_vehicle, 
                    updated_by, 
                    changes=changes
                )
            
            logger.info(f"Updated vehicle: {vehicle_id}")
            return updated_vehicle
            
        except ValueError as e:
            logger.warning(f"Vehicle update validation error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error updating vehicle {vehicle_id}: {e}")
            raise
    
    async def delete_vehicle(self, vehicle_id: str, deleted_by: str) -> bool:
        
        try:
            
            existing_vehicle = await self.vehicle_repo.get_by_id(vehicle_id)
            if not existing_vehicle:
                return False
            
            
            active_assignments = await self.assignment_repo.get_by_vehicle_id(vehicle_id, status="active")
            if active_assignments:
                raise ValueError("Cannot delete vehicle with active assignments")
            
            
            success = await self.vehicle_repo.delete(vehicle_id)
            if not success:
                return False
            
            
            await event_publisher.publish_vehicle_deleted(existing_vehicle, deleted_by)
            
            logger.info(f"Deleted vehicle: {vehicle_id}")
            return True
            
        except ValueError as e:
            logger.warning(f"Vehicle deletion validation error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error deleting vehicle {vehicle_id}: {e}")
            raise
    
    async def search_vehicles(self, query: str, pagination: Dict[str, Any] = None) -> Dict[str, Any]:
        
        try:
            
            if not pagination:
                pagination = {"skip": 0, "limit": 50}
            
            
            search_filter = {
                "$or": [
                    {"registration_number": {"$regex": query, "$options": "i"}},
                    {"make": {"$regex": query, "$options": "i"}},
                    {"model": {"$regex": query, "$options": "i"}},
                    {"department": {"$regex": query, "$options": "i"}},
                    {"type": {"$regex": query, "$options": "i"}}
                ]
            }
            
            
            vehicles = await self.vehicle_repo.find(
                filter_query=search_filter,
                skip=pagination["skip"],
                limit=pagination["limit"],
                sort=[("registration_number", 1)]
            )
            
            
            total = await self.vehicle_repo.count(search_filter)
            total_pages = (total + pagination["limit"] - 1) // pagination["limit"]
            
            return {
                "vehicles": vehicles,
                "query": query,
                "pagination": {
                    "total": total,
                    "page": pagination["skip"] // pagination["limit"] + 1,
                    "page_size": pagination["limit"],
                    "total_pages": total_pages
                }
            }
            
        except Exception as e:
            logger.error(f"Error searching vehicles: {e}")
            raise
    
    async def get_vehicle_assignments(self, vehicle_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        
        try:
            assignments = await self.assignment_repo.get_by_vehicle_id(vehicle_id, status=status)
            return assignments
        except Exception as e:
            logger.error(f"Error getting vehicle assignments for {vehicle_id}: {e}")
            raise
    
    async def get_vehicle_usage_stats(
        self, 
        vehicle_id: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        
        try:
            
            
            from repositories.repositories import VehicleUsageLogRepository
            usage_repo = VehicleUsageLogRepository()
            
            
            date_filter = {"vehicle_id": vehicle_id}
            if start_date or end_date:
                date_range = {}
                if start_date:
                    date_range["$gte"] = datetime.fromisoformat(start_date)
                if end_date:
                    date_range["$lte"] = datetime.fromisoformat(end_date)
                date_filter["created_at"] = date_range
            
            
            usage_logs = await usage_repo.find(
                filter_query=date_filter,
                sort=[("created_at", -1)]
            )
            
            
            total_distance = sum(log.get("distance", 0) for log in usage_logs)
            total_fuel = sum(log.get("fuel_consumed", 0) for log in usage_logs)
            trip_count = len(usage_logs)
            
            avg_distance_per_trip = total_distance / trip_count if trip_count > 0 else 0
            fuel_efficiency = total_distance / total_fuel if total_fuel > 0 else 0
            
            return {
                "vehicle_id": vehicle_id,
                "total_distance": total_distance,
                "total_fuel": total_fuel,
                "trip_count": trip_count,
                "avg_distance_per_trip": round(avg_distance_per_trip, 2),
                "fuel_efficiency": round(fuel_efficiency, 2),
                "usage_logs": usage_logs[:10],  
                "date_range": {
                    "start_date": start_date,
                    "end_date": end_date
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting vehicle usage stats for {vehicle_id}: {e}")
            raise
