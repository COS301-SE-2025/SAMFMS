"""
Fuel management service
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from repositories.repositories import FuelRecordRepository, VehicleRepository, DriverRepository
from events.publisher import event_publisher
from schemas.requests import FuelRecordCreateRequest, FuelRecordUpdateRequest
from schemas.entities import FuelRecord

logger = logging.getLogger(__name__)


class FuelService:
    """Service for fuel record management"""
    
    def __init__(self):
        self.fuel_repo = FuelRecordRepository()
        self.vehicle_repo = VehicleRepository()
        self.driver_repo = DriverRepository()
    
    async def create_fuel_record(self, request: FuelRecordCreateRequest, created_by: str) -> Dict[str, Any]:
        """Create new fuel record"""
        try:
            # Validate vehicle exists
            vehicle = await self.vehicle_repo.get_by_id(request.vehicle_id)
            if not vehicle:
                raise ValueError(f"Vehicle with ID {request.vehicle_id} not found")
            
            # Validate driver exists
            driver = await self.driver_repo.get_by_id(request.driver_id)
            if not driver:
                raise ValueError(f"Driver with ID {request.driver_id} not found")
            
            # Create fuel record
            fuel_data = {
                **request.dict(),
                "created_by": created_by,
                "created_at": datetime.utcnow()
            }
            
            fuel_record_id = await self.fuel_repo.create(fuel_data)
            
            # Publish fuel record created event
            await event_publisher.publish_event({
                "event_type": "fuel_record_created",
                "fuel_record_id": fuel_record_id,
                "vehicle_id": request.vehicle_id,
                "driver_id": request.driver_id,
                "liters": request.liters,
                "cost": request.cost,
                "created_by": created_by,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Get the created record
            created_record = await self.fuel_repo.get_by_id(fuel_record_id)
            
            logger.info(f"Fuel record created: {fuel_record_id} for vehicle {request.vehicle_id} by driver {request.driver_id}")
            
            return created_record
            
        except Exception as e:
            logger.error(f"Error creating fuel record: {e}")
            raise
    
    async def get_fuel_record_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Get fuel record by ID"""
        try:
            return await self.fuel_repo.get_by_id(record_id)
        except Exception as e:
            logger.error(f"Error getting fuel record {record_id}: {e}")
            raise
    
    async def get_fuel_records_by_vehicle(self, vehicle_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get fuel records for a specific vehicle"""
        try:
            return await self.fuel_repo.get_by_vehicle_id(vehicle_id, days)
        except Exception as e:
            logger.error(f"Error getting fuel records for vehicle {vehicle_id}: {e}")
            raise
    
    async def get_fuel_records_by_driver(self, driver_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get fuel records for a specific driver"""
        try:
            return await self.fuel_repo.get_by_driver_id(driver_id, days)
        except Exception as e:
            logger.error(f"Error getting fuel records for driver {driver_id}: {e}")
            raise
    
    async def update_fuel_record(self, record_id: str, request: FuelRecordUpdateRequest, updated_by: str) -> Dict[str, Any]:
        """Update fuel record"""
        try:
            # Check if record exists
            existing_record = await self.fuel_repo.get_by_id(record_id)
            if not existing_record:
                raise ValueError(f"Fuel record with ID {record_id} not found")
            
            # Update record
            update_data = {
                **request.dict(exclude_none=True),
                "updated_at": datetime.utcnow()
            }
            
            success = await self.fuel_repo.update(record_id, update_data)
            if not success:
                raise Exception("Failed to update fuel record")
            
            # Get updated record
            updated_record = await self.fuel_repo.get_by_id(record_id)
            
            # Publish fuel record updated event
            await event_publisher.publish_event({
                "event_type": "fuel_record_updated",
                "fuel_record_id": record_id,
                "updated_by": updated_by,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.info(f"Fuel record updated: {record_id}")
            
            return updated_record
            
        except Exception as e:
            logger.error(f"Error updating fuel record {record_id}: {e}")
            raise
    
    async def delete_fuel_record(self, record_id: str, deleted_by: str) -> bool:
        """Delete fuel record"""
        try:
            # Check if record exists
            existing_record = await self.fuel_repo.get_by_id(record_id)
            if not existing_record:
                raise ValueError(f"Fuel record with ID {record_id} not found")
            
            # Delete record
            success = await self.fuel_repo.delete(record_id)
            
            if success:
                # Publish fuel record deleted event
                await event_publisher.publish_event({
                    "event_type": "fuel_record_deleted",
                    "fuel_record_id": record_id,
                    "deleted_by": deleted_by,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                logger.info(f"Fuel record deleted: {record_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting fuel record {record_id}: {e}")
            raise
    
    async def get_fuel_analytics(self) -> Dict[str, Any]:
        """Get fuel consumption analytics"""
        try:
            analytics = await self.fuel_repo.get_fuel_analytics()
            
            return {
                "fuel_analytics": analytics,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting fuel analytics: {e}")
            raise
    
    async def handle_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle fuel service requests from request consumer"""
        try:
            endpoint = user_context.get("endpoint", "")
            data = user_context.get("data", {})
            user_id = user_context.get("user_id", "system")
            
            if method == "GET":
                if "vehicle" in endpoint and "records" in endpoint:
                    parts = endpoint.split('/')
                    vehicle_id = parts[parts.index("vehicle") + 1] if "vehicle" in parts else None
                    if vehicle_id:
                        days = data.get("days", 30)
                        records = await self.get_fuel_records_by_vehicle(vehicle_id, days)
                        return {"success": True, "data": records}
                elif "driver" in endpoint and "records" in endpoint:
                    parts = endpoint.split('/')
                    driver_id = parts[parts.index("driver") + 1] if "driver" in parts else None
                    if driver_id:
                        days = data.get("days", 30)
                        records = await self.get_fuel_records_by_driver(driver_id, days)
                        return {"success": True, "data": records}
                elif "records" in endpoint:
                    parts = endpoint.split('/')
                    if len(parts) > 1 and parts[-1] != "records":
                        # Get specific record by ID
                        fuel_record_id = parts[-1]
                        record = await self.get_fuel_record_by_id(fuel_record_id)
                        if not record:
                            return {"success": False, "error": "Fuel record not found"}
                        return {"success": True, "data": record}
                elif "analytics" in endpoint:
                    analytics = await self.get_fuel_analytics()
                    return {"success": True, "data": analytics}
                        
            elif method == "POST":
                if "records" in endpoint:
                    request = FuelRecordCreateRequest(**data)
                    record = await self.create_fuel_record(request, user_id)
                    return {"success": True, "data": record}
                    
            elif method == "PUT":
                if "records" in endpoint:
                    parts = endpoint.split('/')
                    fuel_record_id = parts[-1] if parts else None
                    if fuel_record_id:
                        request = FuelRecordUpdateRequest(**data)
                        record = await self.update_fuel_record(fuel_record_id, request, user_id)
                        return {"success": True, "data": record}
                        
            elif method == "DELETE":
                if "records" in endpoint:
                    parts = endpoint.split('/')
                    fuel_record_id = parts[-1] if parts else None
                    if fuel_record_id:
                        success = await self.delete_fuel_record(fuel_record_id, user_id)
                        return {"success": success, "message": "Fuel record deleted successfully"}
            
            return {"success": False, "error": "Unsupported fuel operation"}
            
        except Exception as e:
            logger.error(f"Error handling fuel request: {e}")
            return {"success": False, "error": str(e)}


# Global service instance
fuel_service = FuelService()
