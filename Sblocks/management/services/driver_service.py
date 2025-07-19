
import logging
from typing import Dict, Any, List, Optional

from repositories.repositories import DriverRepository
from events.publisher import event_publisher
from schemas.requests import DriverCreateRequest, DriverUpdateRequest

logger = logging.getLogger(__name__)


class DriverService:
    
    
    def __init__(self):
        self.driver_repo = DriverRepository()
    
    async def create_driver(self, driver_request: DriverCreateRequest, created_by: str) -> Dict[str, Any]:
        
        try:
            
            existing = await self.driver_repo.get_by_employee_id(driver_request.employee_id)
            if existing:
                raise ValueError(f"Driver with employee ID {driver_request.employee_id} already exists")
            
            
            existing_email = await self.driver_repo.get_by_email(driver_request.email)
            if existing_email:
                raise ValueError(f"Driver with email {driver_request.email} already exists")
            
            
            existing_license = await self.driver_repo.get_by_license_number(driver_request.license_number)
            if existing_license:
                raise ValueError(f"Driver with license number {driver_request.license_number} already exists")
            
            
            driver_data = driver_request.model_dump()
            driver_data["status"] = "active"
            
            
            driver_id = await self.driver_repo.create(driver_data)
            driver = await self.driver_repo.get_by_id(driver_id)
            
            
            await event_publisher.publish_driver_created(driver, created_by)
            
            logger.info(f"Created driver: {driver_id}")
            return driver
            
        except ValueError as e:
            logger.warning(f"Driver creation validation error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error creating driver: {e}")
            raise
    
    async def update_driver(self, driver_id: str, updates: DriverUpdateRequest, updated_by: str) -> Dict[str, Any]:
        
        try:
            
            existing_driver = await self.driver_repo.get_by_id(driver_id)
            if not existing_driver:
                raise ValueError("Driver not found")
            
            
            update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
            
            
            if "email" in update_data:
                existing_email = await self.driver_repo.get_by_email(update_data["email"])
                if existing_email and existing_email["_id"] != driver_id:
                    raise ValueError(f"Email {update_data['email']} already in use")
            
            if "license_number" in update_data:
                existing_license = await self.driver_repo.get_by_license_number(update_data["license_number"])
                if existing_license and existing_license["_id"] != driver_id:
                    raise ValueError(f"License number {update_data['license_number']} already in use")
            
            
            success = await self.driver_repo.update(driver_id, update_data)
            if not success:
                raise ValueError("Failed to update driver")
            
            
            updated_driver = await self.driver_repo.get_by_id(driver_id)
            
            logger.info(f"Updated driver: {driver_id}")
            return updated_driver
            
        except ValueError as e:
            logger.warning(f"Driver update validation error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error updating driver {driver_id}: {e}")
            raise
    
    async def assign_vehicle_to_driver(self, driver_id: str, vehicle_id: str, assigned_by: str) -> bool:
        
        try:
            
            driver = await self.driver_repo.get_by_id(driver_id)
            if not driver:
                raise ValueError("Driver not found")
            
            if driver["status"] != "active":
                raise ValueError("Cannot assign vehicle to inactive driver")
            
            
            if driver.get("current_vehicle_id"):
                raise ValueError(f"Driver already assigned to vehicle {driver['current_vehicle_id']}")
            
            
            success = await self.driver_repo.assign_vehicle(driver_id, vehicle_id)
            if not success:
                raise ValueError("Failed to assign vehicle to driver")
            
            logger.info(f"Assigned vehicle {vehicle_id} to driver {driver_id}")
            return True
            
        except ValueError as e:
            logger.warning(f"Vehicle assignment error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error assigning vehicle to driver: {e}")
            raise
    
    async def unassign_vehicle_from_driver(self, driver_id: str, unassigned_by: str) -> bool:
        
        try:
            
            driver = await self.driver_repo.get_by_id(driver_id)
            if not driver:
                raise ValueError("Driver not found")
            
            if not driver.get("current_vehicle_id"):
                raise ValueError("Driver has no vehicle assigned")
            
            
            success = await self.driver_repo.unassign_vehicle(driver_id)
            if not success:
                raise ValueError("Failed to unassign vehicle from driver")
            
            logger.info(f"Unassigned vehicle from driver {driver_id}")
            return True
            
        except ValueError as e:
            logger.warning(f"Vehicle unassignment error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error unassigning vehicle from driver: {e}")
            raise
    
    async def search_drivers(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        
        try:
            return await self.driver_repo.search_drivers(query)
        except Exception as e:
            logger.error(f"Error searching drivers: {e}")
            raise
    
    async def get_drivers_by_department(self, department: str) -> List[Dict[str, Any]]:
        
        try:
            return await self.driver_repo.get_by_department(department)
        except Exception as e:
            logger.error(f"Error getting drivers by department: {e}")
            raise
    
    async def get_active_drivers(self) -> List[Dict[str, Any]]:
        
        try:
            return await self.driver_repo.get_active_drivers()
        except Exception as e:
            logger.error(f"Error getting active drivers: {e}")
            raise



driver_service = DriverService()
