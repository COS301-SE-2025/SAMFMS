"""
Vehicle service for managing vehicles
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId

from repositories.database import db_manager, db_manager_management, db_manager_gps
from events.publisher import event_publisher

logger = logging.getLogger(__name__)

class VehicleService:
  """Service for managing vehicles"""
  
  def __init__(self):
    self.db = db_manager
    self.db_management = db_manager_management
    self.db_gps = db_manager_gps

  async def removeLocation(self, vehicle_id: str):
    """Use this function to remove the existing location in gps location collection"""
    try:
      response = await self.db_gps.locations.delete_one({
        "vehicle_id": vehicle_id
      })

      if response.deleted_count > 0:
        logger.info(f"Removed location for vehicle {vehicle_id}")
      else:
        logger.warning(f"No location found for vehicle {vehicle_id} to remove")

    except Exception as e:
      logger.error(f"Error removing location for vehicle {vehicle_id}: {e}")
      raise

      
  
  async def deactiveVehicle(self, vehicle_id: str):
    """Use this function when a vehicle was assigned to a trip"""
    try:
      vehicle = await self.db_management.vehicles.find_one({"_id": ObjectId(vehicle_id)})
      if not vehicle:
        raise ValueError("Vehicle not found")

      await self.db_management.vehicles.update_one(
          {"_id": ObjectId(vehicle_id)},
          {"$set": {"status": "unavailable", "updated_at": datetime.utcnow()}}
      )

      logger.info(f"Vehicle {vehicle_id} deactivated successfully")
    except Exception as e:
      logger.error(f"Error deactivating vehicle {vehicle_id}: {e}")
      raise
  
  async def activeVehicle(self, vehicle_id: str):
    """Use this function when a vehicle was finished with a trip"""
    try:
      vehicle = await self.db_management.vehicles.find_one({"_id": ObjectId(vehicle_id)})
      if not vehicle:
        raise ValueError("Vehicle not found")

      await self.db_management.vehicles.update_one(
          {"_id": ObjectId(vehicle_id)},
          {"$set": {"status": "available", "updated_at": datetime.utcnow()}}
      )

      logger.info(f"Vehicle {vehicle_id} activated successfully")
    except Exception as e:
      logger.error(f"Error activating vehicle {vehicle_id}: {e}")
      raise

vehicle_service = VehicleService()

      