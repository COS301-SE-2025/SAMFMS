"""
Vehicle assignment service
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from repositories.repositories import VehicleAssignmentRepository, VehicleRepository, DriverRepository
from events.publisher import event_publisher
from schemas.requests import VehicleAssignmentCreateRequest, VehicleAssignmentUpdateRequest
from schemas.entities import VehicleAssignment, AssignmentStatus

logger = logging.getLogger(__name__)


class VehicleAssignmentService:
    """Service for vehicle assignment management"""
    
    def __init__(self):
        self.assignment_repo = VehicleAssignmentRepository()
        self.vehicle_repo = VehicleRepository()
        self.driver_repo = DriverRepository()
    
    async def assign_vehicle_to_driver(self, request: VehicleAssignmentCreateRequest, created_by: str) -> Dict[str, Any]:
        """Assign vehicle to driver"""
        try:
            # Validate vehicle exists and is available
            vehicle = await self.vehicle_repo.get_by_id(request.vehicle_id)
            if not vehicle:
                raise ValueError(f"Vehicle with ID {request.vehicle_id} not found")
            
            if vehicle.get("status") != "available":
                raise ValueError(f"Vehicle {request.vehicle_id} is not available for assignment")
            
            # Validate driver exists and is active
            driver = await self.driver_repo.get_by_id(request.driver_id)
            if not driver:
                raise ValueError(f"Driver with ID {request.driver_id} not found")
            
            if driver.get("status") != "active":
                raise ValueError(f"Driver {request.driver_id} is not active")
            
            # Check if driver already has an active assignment
            active_assignments = await self.assignment_repo.get_by_driver_id(request.driver_id, status="active")
            if active_assignments:
                raise ValueError(f"Driver {request.driver_id} already has an active vehicle assignment")
            
            # Check if vehicle already has an active assignment
            vehicle_assignments = await self.assignment_repo.get_by_vehicle_id(request.vehicle_id, status="active")
            if vehicle_assignments:
                raise ValueError(f"Vehicle {request.vehicle_id} already has an active assignment")
            
            # Create assignment
            assignment_data = {
                **request.dict(),
                "status": AssignmentStatus.ACTIVE,
                "created_by": created_by,
                "created_at": datetime.utcnow()
            }
            
            assignment_id = await self.assignment_repo.create(assignment_data)
            
            # Update vehicle status
            await self.vehicle_repo.update(request.vehicle_id, {
                "status": "assigned",
                "updated_at": datetime.utcnow()
            })
            
            # Update driver's current vehicle
            await self.driver_repo.update(request.driver_id, {
                "current_vehicle_id": request.vehicle_id,
                "updated_at": datetime.utcnow()
            })
            
            # Publish assignment created event
            await event_publisher.publish_event({
                "event_type": "vehicle_assigned",
                "assignment_id": assignment_id,
                "vehicle_id": request.vehicle_id,
                "driver_id": request.driver_id,
                "assignment_type": request.assignment_type,
                "created_by": created_by,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Get the created assignment
            created_assignment = await self.assignment_repo.get_by_id(assignment_id)
            
            logger.info(f"Vehicle {request.vehicle_id} assigned to driver {request.driver_id}")
            
            return created_assignment
            
        except Exception as e:
            logger.error(f"Error assigning vehicle to driver: {e}")
            raise
    
    async def unassign_vehicle_from_driver(self, assignment_id: str, updated_by: str, end_mileage: Optional[int] = None) -> Dict[str, Any]:
        """Unassign vehicle from driver"""
        try:
            # Get assignment
            assignment = await self.assignment_repo.get_by_id(assignment_id)
            if not assignment:
                raise ValueError(f"Assignment with ID {assignment_id} not found")
            
            if assignment.get("status") != "active":
                raise ValueError(f"Assignment {assignment_id} is not active")
            
            vehicle_id = assignment["vehicle_id"]
            driver_id = assignment["driver_id"]
            
            # Update assignment status
            update_data = {
                "status": AssignmentStatus.COMPLETED,
                "end_date": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            if end_mileage:
                update_data["end_mileage"] = end_mileage
            
            await self.assignment_repo.update(assignment_id, update_data)
            
            # Update vehicle status back to available
            await self.vehicle_repo.update(vehicle_id, {
                "status": "available",
                "updated_at": datetime.utcnow()
            })
            
            # Remove driver's current vehicle
            await self.driver_repo.update(driver_id, {
                "current_vehicle_id": None,
                "updated_at": datetime.utcnow()
            })
            
            # Publish assignment completed event
            await event_publisher.publish_event({
                "event_type": "vehicle_unassigned",
                "assignment_id": assignment_id,
                "vehicle_id": vehicle_id,
                "driver_id": driver_id,
                "updated_by": updated_by,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Get the updated assignment
            updated_assignment = await self.assignment_repo.get_by_id(assignment_id)
            
            logger.info(f"Vehicle {vehicle_id} unassigned from driver {driver_id}")
            
            return updated_assignment
            
        except Exception as e:
            logger.error(f"Error unassigning vehicle from driver: {e}")
            raise
    
    async def get_driver_current_assignment(self, driver_id: str) -> Optional[Dict[str, Any]]:
        """Get driver's current active vehicle assignment"""
        try:
            active_assignments = await self.assignment_repo.get_by_driver_id(driver_id, status="active")
            return active_assignments[0] if active_assignments else None
        except Exception as e:
            logger.error(f"Error getting driver's current assignment: {e}")
            raise

    async def cancel_driver_assignments(self, driver_id: str):
        """Remove all assignments from driver"""
        try:
            await self.assignment_repo.cancel_driver_assignments(driver_id)
        except Exception as e:
            logger.error(f"Error getting driver's current assignment: {e}")
            raise
    
    async def get_vehicle_current_assignment(self, vehicle_id: str) -> Optional[Dict[str, Any]]:
        """Get vehicle's current active assignment"""
        try:
            active_assignments = await self.assignment_repo.get_by_vehicle_id(vehicle_id, status="active")
            return active_assignments[0] if active_assignments else None
        except Exception as e:
            logger.error(f"Error getting vehicle's current assignment: {e}")
            raise
    
    async def get_assignments_by_driver(self, driver_id: str) -> List[Dict[str, Any]]:
        """Get all assignments for a driver"""
        try:
            return await self.assignment_repo.get_by_driver_id(driver_id)
        except Exception as e:
            logger.error(f"Error getting assignments for driver {driver_id}: {e}")
            raise
    
    async def get_assignments_by_vehicle(self, vehicle_id: str) -> List[Dict[str, Any]]:
        """Get all assignments for a vehicle"""
        try:
            return await self.assignment_repo.get_by_vehicle_id(vehicle_id)
        except Exception as e:
            logger.error(f"Error getting assignments for vehicle {vehicle_id}: {e}")
            raise
    
    async def get_all_active_assignments(self) -> List[Dict[str, Any]]:
        """Get all active assignments"""
        try:
            return await self.assignment_repo.get_active_assignments()
        except Exception as e:
            logger.error(f"Error getting active assignments: {e}")
            raise
    
    async def handle_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle assignment service requests from request consumer"""
        try:
            endpoint = user_context.get("endpoint", "")
            data = user_context.get("data", {})
            user_id = user_context.get("user_id", "system")
            
            if method == "GET":
                if "driver" in endpoint and "current" in endpoint:
                    # Extract driver_id from endpoint
                    parts = endpoint.split('/')
                    driver_id = parts[parts.index("driver") + 1] if "driver" in parts else None
                    if driver_id:
                        assignment = await self.get_driver_current_assignment(driver_id)
                        return {"success": True, "data": assignment}
                elif "vehicle" in endpoint and "current" in endpoint:
                    # Extract vehicle_id from endpoint
                    parts = endpoint.split('/')
                    vehicle_id = parts[parts.index("vehicle") + 1] if "vehicle" in parts else None
                    if vehicle_id:
                        assignment = await self.get_vehicle_current_assignment(vehicle_id)
                        return {"success": True, "data": assignment}
                elif "active" in endpoint:
                    assignments = await self.get_all_active_assignments()
                    return {"success": True, "data": assignments}
                elif "driver" in endpoint:
                    parts = endpoint.split('/')
                    driver_id = parts[parts.index("driver") + 1] if "driver" in parts else None
                    if driver_id:
                        assignments = await self.get_assignments_by_driver(driver_id)
                        return {"success": True, "data": assignments}
                elif "vehicle" in endpoint:
                    parts = endpoint.split('/')
                    vehicle_id = parts[parts.index("vehicle") + 1] if "vehicle" in parts else None
                    if vehicle_id:
                        assignments = await self.get_assignments_by_vehicle(vehicle_id)
                        return {"success": True, "data": assignments}
                        
            elif method == "POST":
                if "assignments" in endpoint:
                    request = VehicleAssignmentCreateRequest(**data)
                    assignment = await self.assign_vehicle_to_driver(request, user_id)
                    return {"success": True, "data": assignment}
                    
            elif method == "DELETE":
                if "assignments" in endpoint:
                    parts = endpoint.split('/')
                    assignment_id = parts[-1] if parts else None
                    if assignment_id:
                        end_mileage = data.get("end_mileage")
                        assignment = await self.unassign_vehicle_from_driver(assignment_id, user_id, end_mileage)
                        return {"success": True, "data": assignment}
            
            return {"success": False, "error": "Unsupported assignment operation"}
            
        except Exception as e:
            logger.error(f"Error handling assignment request: {e}")
            return {"success": False, "error": str(e)}


# Global service instance
assignment_service = VehicleAssignmentService()
