"""
Mileage management service
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from repositories.repositories import MileageRecordRepository, VehicleRepository, DriverRepository
from events.publisher import event_publisher
from schemas.requests import MileageUpdateRequest
from schemas.entities import MileageRecord

logger = logging.getLogger(__name__)


class MileageService:
    """Service for vehicle mileage management"""
    
    def __init__(self):
        self.mileage_repo = MileageRecordRepository()
        self.vehicle_repo = VehicleRepository()
        self.driver_repo = DriverRepository()
    
    async def update_vehicle_mileage(self, request: MileageUpdateRequest, updated_by: str) -> Dict[str, Any]:
        """Update vehicle mileage"""
        try:
            # Validate vehicle exists
            vehicle = await self.vehicle_repo.get_by_id(request.vehicle_id)
            if not vehicle:
                raise ValueError(f"Vehicle with ID {request.vehicle_id} not found")
            
            # Validate driver exists
            driver = await self.driver_repo.get_by_id(request.driver_id)
            if not driver:
                raise ValueError(f"Driver with ID {request.driver_id} not found")
            
            # Get current vehicle mileage
            current_mileage = vehicle.get("mileage", 0)
            
            # Validate new mileage is greater than current
            if request.new_mileage <= current_mileage:
                raise ValueError(f"New mileage ({request.new_mileage}) must be greater than current mileage ({current_mileage})")
            
            # Create mileage record
            mileage_data = {
                "vehicle_id": request.vehicle_id,
                "driver_id": request.driver_id,
                "previous_mileage": current_mileage,
                "new_mileage": request.new_mileage,
                "mileage_difference": request.new_mileage - current_mileage,
                "reading_date": request.reading_date or datetime.utcnow(),
                "notes": request.notes,
                "created_by": updated_by,
                "created_at": datetime.utcnow()
            }
            
            # Save mileage record
            mileage_record_id = await self.mileage_repo.create(mileage_data)
            
            # Update vehicle's current mileage
            vehicle_update_success = await self.vehicle_repo.update(request.vehicle_id, {
                "mileage": request.new_mileage,
                "updated_at": datetime.utcnow()
            })
            
            if not vehicle_update_success:
                # Rollback mileage record if vehicle update failed
                await self.mileage_repo.delete(mileage_record_id)
                raise Exception("Failed to update vehicle mileage")
            
            # Publish mileage updated event
            await event_publisher.publish_event({
                "event_type": "vehicle_mileage_updated",
                "vehicle_id": request.vehicle_id,
                "driver_id": request.driver_id,
                "previous_mileage": current_mileage,
                "new_mileage": request.new_mileage,
                "mileage_difference": request.new_mileage - current_mileage,
                "updated_by": updated_by,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Get the created mileage record
            created_record = await self.mileage_repo.get_by_id(mileage_record_id)
            
            logger.info(f"Vehicle mileage updated: {request.vehicle_id} from {current_mileage} to {request.new_mileage}")
            
            return created_record
            
        except Exception as e:
            logger.error(f"Error updating vehicle mileage: {e}")
            raise
    
    async def get_mileage_records_by_vehicle(self, vehicle_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get mileage records for a specific vehicle"""
        try:
            return await self.mileage_repo.get_by_vehicle_id(vehicle_id, days)
        except Exception as e:
            logger.error(f"Error getting mileage records for vehicle {vehicle_id}: {e}")
            raise
    
    async def get_mileage_records_by_driver(self, driver_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get mileage records for a specific driver"""
        try:
            return await self.mileage_repo.get_by_driver_id(driver_id, days)
        except Exception as e:
            logger.error(f"Error getting mileage records for driver {driver_id}: {e}")
            raise
    
    async def get_latest_mileage(self, vehicle_id: str) -> Optional[Dict[str, Any]]:
        """Get the latest mileage record for a vehicle"""
        try:
            return await self.mileage_repo.get_latest_mileage(vehicle_id)
        except Exception as e:
            logger.error(f"Error getting latest mileage for vehicle {vehicle_id}: {e}")
            raise
    
    async def validate_mileage_update(self, vehicle_id: str, new_mileage: int) -> Dict[str, Any]:
        """Validate if mileage update is valid"""
        try:
            vehicle = await self.vehicle_repo.get_by_id(vehicle_id)
            if not vehicle:
                return {"valid": False, "reason": "Vehicle not found"}
            
            current_mileage = vehicle.get("mileage", 0)
            
            if new_mileage <= current_mileage:
                return {
                    "valid": False, 
                    "reason": f"New mileage ({new_mileage}) must be greater than current mileage ({current_mileage})"
                }
            
            return {
                "valid": True,
                "current_mileage": current_mileage,
                "new_mileage": new_mileage,
                "difference": new_mileage - current_mileage
            }
            
        except Exception as e:
            logger.error(f"Error validating mileage update: {e}")
            return {"valid": False, "reason": str(e)}
    
    async def handle_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle mileage service requests from request consumer"""
        try:
            endpoint = user_context.get("endpoint", "")
            data = user_context.get("data", {})
            user_id = user_context.get("user_id", "system")
            
            if method == "GET":
                if "current" in endpoint and "vehicle" in endpoint:
                    parts = endpoint.split('/')
                    vehicle_id = parts[parts.index("vehicle") + 1] if "vehicle" in parts else None
                    if vehicle_id:
                        mileage = await self.get_current_vehicle_mileage(vehicle_id)
                        return {"success": True, "data": {"vehicle_id": vehicle_id, "current_mileage": mileage}}
                elif "history" in endpoint and "vehicle" in endpoint:
                    parts = endpoint.split('/')
                    vehicle_id = parts[parts.index("vehicle") + 1] if "vehicle" in parts else None
                    if vehicle_id:
                        days = data.get("days", 30)
                        history = await self.get_mileage_history(vehicle_id, days)
                        return {"success": True, "data": history}
                elif "records" in endpoint and "driver" in endpoint:
                    parts = endpoint.split('/')
                    driver_id = parts[parts.index("driver") + 1] if "driver" in parts else None
                    if driver_id:
                        days = data.get("days", 30)
                        records = await self.get_mileage_records_by_driver(driver_id, days)
                        return {"success": True, "data": records}
                elif "records" in endpoint:
                    parts = endpoint.split('/')
                    if len(parts) > 1 and parts[-1] != "records":
                        # Get specific record by ID
                        mileage_record_id = parts[-1]
                        record = await self.mileage_repo.get_by_id(mileage_record_id)
                        if not record:
                            return {"success": False, "error": "Mileage record not found"}
                        return {"success": True, "data": record}
                        
            elif method == "POST":
                if "update" in endpoint:
                    request = MileageUpdateRequest(**data)
                    record = await self.update_vehicle_mileage(request, user_id)
                    return {"success": True, "data": record}
                        
            elif method == "DELETE":
                if "records" in endpoint:
                    parts = endpoint.split('/')
                    mileage_record_id = parts[-1] if parts else None
                    if mileage_record_id:
                        success = await self.mileage_repo.delete(mileage_record_id)
                        return {"success": success, "message": "Mileage record deleted successfully"}
            
            return {"success": False, "error": "Unsupported mileage operation"}
            
        except Exception as e:
            logger.error(f"Error handling mileage request: {e}")
            return {"success": False, "error": str(e)}


# Global service instance
mileage_service = MileageService()
