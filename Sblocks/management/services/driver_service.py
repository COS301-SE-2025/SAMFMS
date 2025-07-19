"""
Driver management service
"""
import logging
from typing import Dict, Any, List, Optional

from repositories.repositories import DriverRepository, SecurityUserRepository
from events.publisher import event_publisher
from schemas.requests import DriverCreateRequest, DriverUpdateRequest

logger = logging.getLogger(__name__)


class DriverService:
    """Service for driver management business logic"""
    
    def __init__(self):
        self.driver_repo = DriverRepository()
        self.security_user_repo = SecurityUserRepository()
    
    async def get_active_drivers(self) -> List[Dict[str, Any]]:
        """Get all active drivers from security database"""
        try:
            drivers = await self.security_user_repo.get_active_drivers()
            
            # Transform the data to match expected format
            result = {
                "drivers": drivers,
                "total": len(drivers),
                "page": 1,
                "page_size": len(drivers),
                "total_pages": 1
            }
            
            return result
        except Exception as e:
            logger.error(f"Error getting active drivers: {e}")
            raise
    
    async def get_drivers(self, department: str = None, status: str = None, vehicle_type: str = None, pagination: Dict[str, int] = None) -> Dict[str, Any]:
        """Get drivers with optional filters"""
        try:
            if pagination is None:
                pagination = {"skip": 0, "limit": 50}
                
            # Get drivers from security database
            drivers = await self.security_user_repo.get_drivers(
                skip=pagination.get("skip", 0),
                limit=pagination.get("limit", 50)
            )
            
            # Apply filters if provided
            if status:
                if status.lower() == "active":
                    drivers = [d for d in drivers if d.get("is_active", False)]
                elif status.lower() == "inactive":
                    drivers = [d for d in drivers if not d.get("is_active", False)]
            
            if department:
                drivers = [d for d in drivers if d.get("details", {}).get("department") == department]
            
            # Get total count
            total = await self.security_user_repo.count_drivers()
            
            result = {
                "drivers": drivers,
                "total": total,
                "page": (pagination.get("skip", 0) // pagination.get("limit", 50)) + 1,
                "page_size": pagination.get("limit", 50),
                "total_pages": (total + pagination.get("limit", 50) - 1) // pagination.get("limit", 50),
                "pagination": {
                    "skip": pagination.get("skip", 0),
                    "limit": pagination.get("limit", 50),
                    "has_more": pagination.get("skip", 0) + len(drivers) < total
                }
            }
            
            return result
        except Exception as e:
            logger.error(f"Error getting drivers: {e}")
            raise
    
    async def get_driver_by_id(self, driver_id: str) -> Optional[Dict[str, Any]]:
        """Get driver by ID from security database"""
        try:
            driver = await self.security_user_repo.get_driver_by_id(driver_id)
            return driver
        except Exception as e:
            logger.error(f"Error getting driver {driver_id}: {e}")
            raise
    
    async def create_driver(self, driver_request: DriverCreateRequest, created_by: str) -> Dict[str, Any]:
        """Create new driver with validation"""
        try:
            # Check if employee ID already exists
            existing = await self.driver_repo.get_by_employee_id(driver_request.employee_id)
            if existing:
                raise ValueError(f"Driver with employee ID {driver_request.employee_id} already exists")
            
            # Check if email already exists
            existing_email = await self.driver_repo.get_by_email(driver_request.email)
            if existing_email:
                raise ValueError(f"Driver with email {driver_request.email} already exists")
            
            # Check if license number already exists
            existing_license = await self.driver_repo.get_by_license_number(driver_request.license_number)
            if existing_license:
                raise ValueError(f"Driver with license number {driver_request.license_number} already exists")
            
            # Convert to dict and add metadata
            driver_data = driver_request.model_dump()
            driver_data["status"] = "active"
            
            # Create driver
            driver_id = await self.driver_repo.create(driver_data)
            driver = await self.driver_repo.get_by_id(driver_id)
            
            # Publish event
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
        """Update driver with validation"""
        try:
            # Check if driver exists
            existing_driver = await self.driver_repo.get_by_id(driver_id)
            if not existing_driver:
                raise ValueError("Driver not found")
            
            # Convert updates to dict, excluding None values
            update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
            
            # Validate unique fields if being updated
            if "email" in update_data:
                existing_email = await self.driver_repo.get_by_email(update_data["email"])
                if existing_email and existing_email["_id"] != driver_id:
                    raise ValueError(f"Email {update_data['email']} already in use")
            
            if "license_number" in update_data:
                existing_license = await self.driver_repo.get_by_license_number(update_data["license_number"])
                if existing_license and existing_license["_id"] != driver_id:
                    raise ValueError(f"License number {update_data['license_number']} already in use")
            
            # Update driver
            success = await self.driver_repo.update(driver_id, update_data)
            if not success:
                raise ValueError("Failed to update driver")
            
            # Get updated driver
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
        """Assign vehicle to driver"""
        try:
            # Check if driver exists and is active
            driver = await self.driver_repo.get_by_id(driver_id)
            if not driver:
                raise ValueError("Driver not found")
            
            if driver["status"] != "active":
                raise ValueError("Cannot assign vehicle to inactive driver")
            
            # Check if driver already has a vehicle
            if driver.get("current_vehicle_id"):
                raise ValueError(f"Driver already assigned to vehicle {driver['current_vehicle_id']}")
            
            # Assign vehicle
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
        """Remove vehicle assignment from driver"""
        try:
            # Check if driver exists
            driver = await self.driver_repo.get_by_id(driver_id)
            if not driver:
                raise ValueError("Driver not found")
            
            if not driver.get("current_vehicle_id"):
                raise ValueError("Driver has no vehicle assigned")
            
            # Unassign vehicle
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
        """Search drivers by various criteria"""
        try:
            return await self.driver_repo.search_drivers(query)
        except Exception as e:
            logger.error(f"Error searching drivers: {e}")
            raise
    
    async def get_drivers_by_department(self, department: str) -> List[Dict[str, Any]]:
        """Get drivers by department"""
        try:
            return await self.driver_repo.get_by_department(department)
        except Exception as e:
            logger.error(f"Error getting drivers by department: {e}")
            raise
    
    async def get_active_drivers(self) -> List[Dict[str, Any]]:
        """Get all active drivers from security database"""
        try:
            drivers = await self.security_user_repo.get_active_drivers()
            return drivers
        except Exception as e:
            logger.error(f"Error getting active drivers: {e}")
            raise


# Global service instance
driver_service = DriverService()
