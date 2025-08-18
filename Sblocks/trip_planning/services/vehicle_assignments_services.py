"""
Service for the vehicle_assignments collection in management database
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from bson import ObjectId

from repositories.database import db_manager, db_manager_management
from events.publisher import event_publisher

logger = logging.getLogger(__name__)

class VehicleAssignmenstService:
  """Service for managing vehicle assignments"""

  def __init__(self):
    self.db = db_manager
    self.db_management = db_manager_management
  
  async def createAssignment(self, trip_id: str, vehicle_id: str, driver_id: str):
    """Create a new vehicle assignment"""
    try:
        assignment_data = {
            "trip_id": trip_id,
            "driver_id": driver_id,
            "vehicle_id": vehicle_id,
            "created_at": datetime.utcnow()
        }

        result = await self.db_management.vehicle_assignments.insert_one(assignment_data)
        
        if not result.inserted_id:
            raise ValueError("Assignment failed to create")
        
        # Get the created assignment
        created_assignment = await self.db_management.vehicle_assignments.find_one(
            {"_id": result.inserted_id}
        )
        
        logger.info(f"Created assignment: {created_assignment}")
        return created_assignment

    except Exception as e:
        logger.error(f"Error creating assignment: {str(e)}")
        raise

  async def removeAssignment(self, vehicle_id: str, driver_id: str):
    """Remove assignment by vehicle_id and driver_id"""
    try:
        # Find the assignment first to log what we're removing
        assignment_to_remove = await self.db_management.vehicle_assignments.find_one({
            "vehicle_id": vehicle_id,
            "driver_id": driver_id
        })
                
        if not assignment_to_remove:
            logger.warning(f"No assignment found for vehicle_id: {vehicle_id}, driver_id: {driver_id}")
            return None
                
        # Remove the assignment
        result = await self.db_management.vehicle_assignments.delete_one({
            "vehicle_id": vehicle_id,
            "driver_id": driver_id
        })
                
        if result.deleted_count == 0:
            raise ValueError("Assignment failed to remove")
                
        logger.info(f"Removed assignment: vehicle_id={vehicle_id}, driver_id={driver_id}, trip_id={assignment_to_remove.get('trip_id')}")
        return assignment_to_remove
            
    except Exception as e:
        logger.error(f"Error removing assignment: {str(e)}")
        raise


vehicle_assignment_service = VehicleAssignmenstService()


