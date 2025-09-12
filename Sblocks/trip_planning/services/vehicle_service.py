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

  async def get_all_vehicles(
      self,
      status: Optional[str] = None,
      skip: int = 0,
      limit: int = 100
  ) -> Dict[str, Any]:
    """Get all vehicles from the vehicles collection"""
    try:
      query = {}
      if status:
        query["status"] = status
        
      # Get total count
      total = await self.db_management.vehicles.count_documents(query)
      
      # Get vehicles with pagination
      cursor = self.db_management.vehicles.find(query).skip(skip).limit(limit)
      vehicles = await cursor.to_list(length=limit)
      
      # Convert ObjectId to string for JSON serialization
      for vehicle in vehicles:
        vehicle["_id"] = str(vehicle["_id"])
      
      return {
        "vehicles": vehicles,
        "total": total,
        "skip": skip,
        "limit": limit
      }
    except Exception as e:
      logger.error(f"Error getting all vehicles: {e}")
      raise

  async def check_vehicle_availability(
      self,
      vehicle_id: str,
      start_time: datetime,
      end_time: datetime
  ) -> bool:
    """Check if a vehicle is available during a specific time period"""
    try:
      # Check if vehicle exists
      vehicle = await self.db_management.vehicles.find_one({"_id": ObjectId(vehicle_id)})
      if not vehicle:
        logger.warning(f"Vehicle {vehicle_id} not found")
        return False
      
      # Check for conflicting trips in the requested time period
      # Look for trips that overlap with the requested timeframe (regardless of trip status)
      conflicting_trips = await self.db.trips.find({
        "vehicle_id": vehicle_id,
        "$or": [
          # Trip starts during our timeframe
          {
            "scheduled_start_time": {"$lt": end_time},
            "scheduled_end_time": {"$gt": start_time}
          },
          # Our timeframe is during the trip
          {
            "scheduled_start_time": {"$lte": start_time},
            "scheduled_end_time": {"$gte": end_time}
          }
        ]
      }).to_list(length=None)
      
      if conflicting_trips:
        logger.info(f"Vehicle {vehicle_id} has {len(conflicting_trips)} conflicting trips")
        return False
      
      return True
      
    except Exception as e:
      logger.error(f"Error checking vehicle {vehicle_id} availability: {e}")
      return False

  async def get_available_vehicles(
      self,
      start_time: datetime,
      end_time: datetime,
      skip: int = 0,
      limit: int = 100
  ) -> Dict[str, Any]:
    """Get all vehicles available during a specific time period"""
    try:
      # Get all vehicles (without status filter)
      all_vehicles_result = await self.get_all_vehicles(skip=0, limit=1000)
      all_vehicles = all_vehicles_result.get("vehicles", [])
      
      available_vehicles = []
      
      # Check each vehicle's availability
      for vehicle in all_vehicles:
        vehicle_id = str(vehicle.get("_id"))
        if not vehicle_id:
          continue
          
        # Check if vehicle is available during the timeframe
        is_available = await self.check_vehicle_availability(
          vehicle_id, start_time, end_time
        )
        
        if is_available:
          available_vehicles.append({
            **vehicle,
            "is_available": True,
            "checked_timeframe": {
              "start_time": start_time,
              "end_time": end_time
            }
          })
      
      # Apply pagination to available vehicles
      total_available = len(available_vehicles)
      paginated_vehicles = available_vehicles[skip:skip + limit]
      
      return {
        "vehicles": paginated_vehicles,
        "total_available": total_available,
        "total_checked": len(all_vehicles),
        "skip": skip,
        "limit": limit,
        "timeframe": {
          "start_time": start_time,
          "end_time": end_time
        }
      }
      
    except Exception as e:
      logger.error(f"Error getting available vehicles: {e}")
      raise

vehicle_service = VehicleService()

      