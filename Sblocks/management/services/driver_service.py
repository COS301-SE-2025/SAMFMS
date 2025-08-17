"""
Driver management service
"""
import logging
from typing import Dict, Any, List, Optional
import aiohttp
import os

from repositories.repositories import DriverRepository
from repositories.database import db_manager
from events.publisher import event_publisher
from schemas.requests import DriverCreateRequest, DriverUpdateRequest

logger = logging.getLogger(__name__)


class DriverService:
    """Service for driver management business logic"""
    
    def __init__(self):
        self.driver_repo = DriverRepository()
        self.security_service_url = os.getenv("SECURITY_SERVICE_URL", "http://security:21002")


    async def _create_user_account(self, driver_data: Dict[str, Any]) -> bool:
        """Create a user account for the driver in the security service"""
        try:
            # Prepare signup request (uses the public signup endpoint)
            signup_data = {
                "email": driver_data["email"],
                "password": "TempPassword123!",  # Temporary password - should be changed on first login
                "full_name": driver_data["full_name"],
                "role": "driver"
            }
            
            # Make request to security service signup endpoint (no auth required)
            async with aiohttp.ClientSession() as session:
                url = f"{self.security_service_url}/auth/signup"
                headers = {"Content-Type": "application/json"}
                
                async with session.post(url, json=signup_data, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Successfully created user account for driver: {driver_data['email']}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.warning(f"Failed to create user account (driver record still created): {response.status} - {error_text}")
                        # Don't fail the entire driver creation if user account creation fails
                        return False
                        
        except Exception as e:
            logger.error(f"Error creating user account for driver: {e}")
            return False



    
    async def get_all_drivers(self, filters: Dict[str, Any] = {}) -> Dict[str, Any]:
        """Retrieve all drivers with optional filtering and pagination"""
        try:
            query = {}

            # Map status_filter to internal status field
            if "status_filter" in filters:
                status = filters["status_filter"].lower()
                if status in ["active", "inactive"]:
                    query["status"] = status

            # Filter by department
            if "department_filter" in filters:
                query["department"] = filters["department_filter"]

            # Ensure pagination params are integers
            skip = int(str(filters.get("skip", 0)).strip())
            limit = int(str(filters.get("limit", 100)).strip())

            # Query DB with validated integers
            all_drivers = await self.driver_repo.find(
                filter_query=query,
                skip=skip,
                limit=limit if limit > 0 else None
            )

            # Total count without pagination
            total_count = await self.driver_repo.count(query)

            return {
                "drivers": all_drivers,
                "total": total_count,
                "skip": skip,
                "limit": limit if limit > 0 else total_count,
                "has_more": skip + limit < total_count if limit > 0 else False,
            }

        except ValueError as e:
            logger.error(f"Error parsing pagination parameters: {e}")
            raise
        except Exception as e:
            logger.error(f"Error retrieving filtered drivers: {e}")
            raise

    async def get_num_drivers(self, filters: Dict[str, Any] = {}) -> Dict[str, Any]:
        """Retrieve total number of drivers based on filters"""
        response = await self.get_all_drivers(filters)
        return {"total": response["total"]}

    
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
                        
            # Check if license number already exists (only if license number is provided and not empty)
            if (hasattr(driver_request, 'license_number') and 
                driver_request.license_number is not None and 
                str(driver_request.license_number).strip()):
                existing_license = await self.driver_repo.get_by_license_number(driver_request.license_number)
                if existing_license:
                    raise ValueError(f"Driver with license number {driver_request.license_number} already exists")
                                    
            # Convert to dict and add metadata
            driver_data = driver_request.model_dump(exclude_unset=True)
            driver_data["status"] = "available"  # Set initial status 
            
            # Ensure license_number is completely removed if it's empty or None
            if "license_number" in driver_data and (
                driver_data["license_number"] is None or 
                not str(driver_data["license_number"]).strip()
            ):
                driver_data.pop("license_number", None)
                        
            # Create driver
            driver_id = await self.driver_repo.create(driver_data)
            
            logger.info(f"Created driver: {driver_id}")
            


                        
            # Create user account in security service
            user_created = await self._create_user_account(driver_data)
            if not user_created:
                logger.warning(f"Failed to create user account for driver {driver_id}, but driver record was created")
                        
            # Get full driver data for event publishing
            driver = await self.driver_repo.get_by_id(driver_id)
            logger.info(f"Driver returned by id: {driver}")
                        
            # Transform response for API (change _id to id)
            if driver and '_id' in driver:
                driver['id'] = str(driver.pop('_id'))
                    
            logger.info(f"Created driver: {driver_id}")


            from .drivers_service import DriversService
            drivers_service = DriversService()
            await drivers_service.add_driver()
            logger.info(f"Driver analytics addition")

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
            
            #if driver["status"] != "active":
                #raise ValueError("Cannot assign vehicle to inactive driver")
            
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
        """Get all active drivers"""
        try:
            return await self.driver_repo.get_active_drivers()
        except Exception as e:
            logger.error(f"Error getting active drivers: {e}")
            raise
    
    async def get_driver_by_id(self, driver_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific driver by ID"""
        try:
            driver = await self.driver_repo.get_by_id(driver_id)
            if not driver:
                logger.warning(f"Driver not found: {driver_id}")
                return None
            return driver
        except Exception as e:
            logger.error(f"Error getting driver {driver_id}: {e}")
            raise
    
    async def delete_driver(self, driver_id: str) -> bool:
        """Delete a driver by ID"""
        try:
            # Check if driver exists
            driver = await self.driver_repo.get_by_id(driver_id)
            if not driver:
                logger.warning(f"Driver not found for deletion: {driver_id}")
                return False
            
            # Check if driver has active assignments
            if driver.get("status") == "active":
                logger.warning(f"Cannot delete active driver: {driver_id}")
                raise ValueError("Cannot delete an active driver. Please deactivate first.")
            
            # Delete the driver
            success = await self.driver_repo.delete(driver_id)
            if success:
                logger.info(f"Driver deleted successfully: {driver_id}")
            else:
                logger.error(f"Failed to delete driver: {driver_id}")
            
            from .drivers_service import DriversService
            drivers_service = DriversService()
            await drivers_service.remove_driver()
            logger.info(f"Driver analytics removal logged")
            return success
        except Exception as e:
            logger.error(f"Error deleting driver {driver_id}: {e}")
            raise
    
    async def generate_next_employee_id(self) -> str:
        """Generate next sequential employee ID"""
        try:
            last_id = await self.driver_repo.get_last_employee_id()
            logger.debug(f"Last employee ID found: {last_id}")

            if last_id == "EMP000":
                return "EMP001"

            # Extract numeric part and increment
            numeric_part = int(last_id[3:])
            next_id = numeric_part + 1

            # Format with leading zeros to maintain 3 digits
            return f"EMP{next_id:03d}"

        except Exception as e:
            logger.error(f"Error generating next employee ID: {str(e)}")
            return "EMP001"  # Fallback to first ID if error occurs

    async def handle_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle driver-related requests from request consumer"""
        try:
            from schemas.requests import DriverCreateRequest, DriverUpdateRequest
            from schemas.responses import ResponseBuilder
            from repositories.repositories import DriverRepository
            
            # Extract data and endpoint from user_context
            data = user_context.get("data", {})
            endpoint = user_context.get("endpoint", "")
            
            # Create mock user for service calls
            current_user = {"user_id": user_context.get("user_id", "system")}
            
            # Handle HTTP methods and route to appropriate logic
            if method == "GET":
                # Parse endpoint for specific driver operations
                if "search" in endpoint:
                    query = data.get("query", "")
                    drivers = await self.search_drivers(query)
                elif "employee" in endpoint:
                    security_id = endpoint.split('/')[-1] if '/' in endpoint else None
                    logger.info(f"Security ID extracted for employee id: {security_id} ")
                    if security_id is None:
                        logger.info("Failed to extract id in employee id request")
                        return ResponseBuilder.error(
                            error= "Security ID problem",
                            message="Security ID was not extracted from the endpoint"
                        )
                    
                    driver = await self.driver_repo.get_by_security_id(security_id)
                    logger.info(f"Driver data for security id: {security_id}: {driver}")
                    employee_id = driver["employee_id"]
                    return ResponseBuilder.success(
                        data=employee_id,
                        message="Employee id retrieved successfully"
                    ).model_dump()
                    

                elif endpoint.count('/') > 0 and endpoint.split('/')[-1] and endpoint.split('/')[-1] != "drivers":
                    # drivers/{id} pattern
                    driver_id = endpoint.split('/')[-1]
                    drivers = await self.get_driver_by_id(driver_id)
                else:
                    # Get drivers with optional filters (mimic route logic)
                    department = data.get("department")
                    status = data.get("status")
                    pagination = data.get("pagination", {"skip": 0, "limit": 50})
                    
                    filters = {}

                    # Normalize filters from request
                    if department:
                        filters["department_filter"] = department

                    if status:
                        filters["status_filter"] = status

                    # Handle pagination
                    pagination = data.get("pagination", {})
                    if "skip" in pagination:
                        filters["skip"] = pagination["skip"]
                    if "limit" in pagination:
                        filters["limit"] = pagination["limit"]
                    
                    logger.info(f"Filters: {filters}")

                    # Get drivers using new filter-aware function
                    drivers_result = await self.get_all_drivers(filters)

                
                return ResponseBuilder.success(
                    data=drivers_result,
                    message="Drivers retrieved successfully"
                ).model_dump()

                
            elif method == "POST":
                if not data:
                    raise ValueError("Request data is required for POST operation")
                
                logger.info(f"Data received for POST operation: ")
                
                # Create and employee id based on the last employeeid in the driver collection
                employee_id = await self.generate_next_employee_id()
                logger.info(f"Generated employee_id: {employee_id}")
                # Split full name from data into first and last names
                full_name = data["full_name"]  # Changed from data.full_name to data["full_name"]
                parts = full_name.strip().split()
                first_name = parts[0]
                last_name = " ".join(parts[1:])

                security_id = data["security_id"]
                # Create new data
                driver_data = {
                    "employee_id": employee_id,
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": data["email"],
                    "phone": data["phoneNo"],
                    "security_id": security_id,
                }
                # Create driver
                driver_request = DriverCreateRequest(**driver_data)
                created_by = current_user["user_id"]
                result = await self.create_driver(driver_request, created_by)
                
                return ResponseBuilder.success(
                    data=result,
                    message="Driver created successfully"
                ).model_dump()
                
            elif method == "PUT":
                driver_id = endpoint.split('/')[-1] if '/' in endpoint else None
                if not driver_id:
                    raise ValueError("Driver ID is required for PUT operation")
                if not data:
                    raise ValueError("Request data is required for PUT operation")
                
                # Update driver
                driver_update_request = DriverUpdateRequest(**data)
                updated_by = current_user["user_id"]
                result = await self.update_driver(driver_id, driver_update_request, updated_by)
                
                return ResponseBuilder.success(
                    data=result,
                    message="Driver updated successfully"
                ).model_dump()
                
            elif method == "DELETE":
                driver_id = endpoint.split('/')[-1] if '/' in endpoint else None
                if not driver_id:
                    raise ValueError("Driver ID is required for DELETE operation")
                
                # Delete driver
                result = await self.delete_driver(driver_id)
                
                return ResponseBuilder.success(
                    data=result,
                    message="Driver deleted successfully"
                ).model_dump()
                
            else:
                raise ValueError(f"Unsupported HTTP method for drivers: {method}")
                
        except Exception as e:
            from schemas.responses import ResponseBuilder
            logger.error(f"Error handling drivers request {method} {endpoint}: {e}")
            return ResponseBuilder.error(
                error="DriverRequestError",
                message=f"Failed to process driver request: {str(e)}"
            ).model_dump()


# Global service instance
driver_service = DriverService()
