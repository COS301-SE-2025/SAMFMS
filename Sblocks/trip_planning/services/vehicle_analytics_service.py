"""
Vehicle Analytics service for trip planning
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from bson import ObjectId

logger = logging.getLogger(__name__)

from repositories.database import db_manager, db_manager_management

class VehicleAnalyticsService:
  """Service for vehicle analytics and performance"""

  def __init__(self):
    self.db = db_manager
    self.db_management = db_manager_management
  
  async def _get_total_distance(self, timeframe: str):
    """Calculate the total distance traveled by all vehicles from trip_history"""
    end_date = datetime.now(timezone.utc)
    start_date = self._get_start_date(timeframe, end_date)

    trips = await self.db.trip_history.find({
      "actual_start_time": {"$gte": start_date, "$lte": end_date}
    }).to_list(None)

  
  async def get_vehicle_trip_stats(self, timeframe: str) -> List[Dict[str, Any]]:
    """Get trip statistics per vehicle within timeframe"""
    try:
        end_date = datetime.now(timezone.utc)
        start_date = self._get_start_date(timeframe, end_date)

        # Aggregate trips by vehicle
        pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": "$vehicle_id",
                    "total_trips": {"$sum": 1},
                    "total_distance": {"$sum": "$estimated_distance"}
                }
            }
        ]

        stats = await self.db.trip_history.aggregate(pipeline).to_list(None)
        
        # Get vehicle names
        vehicle_ids = [stat["_id"] for stat in stats]
        vehicle_names = await self._get_vehicle_names(vehicle_ids)

        # Format results
        formatted_stats = []
        for stat in stats:
            vehicle_id = stat["_id"]
            formatted_stats.append({
                "vehicleName": vehicle_names.get(vehicle_id, f"Vehicle {vehicle_id}"),
                "totalTrips": stat["total_trips"],
                "totalDistance": round(stat["total_distance"], 2)  # Round to 2 decimal places
            })

        logger.info(f"Vehicle trip stats for {timeframe}: {formatted_stats}")
        return formatted_stats

    except Exception as e:
        logger.error(f"Error getting vehicle trip stats: {e}")
        raise

  async def _get_vehicle_names(self, vehicle_ids: List[str]) -> Dict[str, str]:
    """Get vehicle names for given vehicle IDs"""
    try:
        vehicles = await self.db.vehicles.find(
            {"_id": {"$in": [ObjectId(vid) for vid in vehicle_ids]}},
            {"name": 1}
        ).to_list(None)
        
        return {str(v["_id"]): v.get("name", f"Vehicle {str(v['_id'])}") for v in vehicles}
    except Exception as e:
        logger.error(f"Error getting vehicle names: {e}")
        return {}
  
  async def get_vehicle_trip_stats(self, timeframe: str) -> List[Dict[str, Any]]:
    """Get trip statistics per vehicle within timeframe"""
    try:
        end_date = datetime.now(timezone.utc)
        start_date = self._get_start_date(timeframe, end_date)

        # Aggregate trips by vehicle
        pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": "$vehicle_id",
                    "total_trips": {"$sum": 1},
                    "total_distance": {"$sum": "$estimated_distance"}
                }
            }
        ]

        stats = await self.db.trip_history.aggregate(pipeline).to_list(None)
        
        # Get vehicle names
        vehicle_ids = [stat["_id"] for stat in stats]
        vehicle_names = await self._get_vehicle_names(vehicle_ids)

        # Format results
        formatted_stats = []
        for stat in stats:
            vehicle_id = stat["_id"]
            formatted_stats.append({
                "vehicleName": vehicle_names.get(vehicle_id, f"Vehicle {vehicle_id}"),
                "totalTrips": stat["total_trips"],
                "totalDistance": round(stat["total_distance"], 2)  # Round to 2 decimal places
            })

        logger.info(f"Vehicle trip stats for {timeframe}: {formatted_stats}")
        return formatted_stats

    except Exception as e:
        logger.error(f"Error getting vehicle trip stats: {e}")
        raise

  async def _get_vehicle_names(self, vehicle_ids: List[str]) -> Dict[str, str]:
    """Get vehicle names for given vehicle IDs"""
    try:
        vehicles = await self.db.vehicles.find(
            {"_id": {"$in": [ObjectId(vid) for vid in vehicle_ids]}},
            {"name": 1}
        ).to_list(None)
        
        return {str(v["_id"]): v.get("name", f"Vehicle {str(v['_id'])}") for v in vehicles}
    except Exception as e:
        logger.error(f"Error getting vehicle names: {e}")
        return {}

  async def get_total_distance_all_vehicles(self, timeframe: str) -> float:
    """Get total distance traveled by all vehicles combined within timeframe"""
    try:
        end_date = datetime.now(timezone.utc)
        start_date = self._get_start_date(timeframe, end_date)

        # Aggregate total distance across all vehicles
        pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_distance": {"$sum": "$estimated_distance"}
                }
            }
        ]

        result = await self.db.trip_history.aggregate(pipeline).to_list(1)
        
        total_distance = result[0]["total_distance"] if result else 0.0
        total_distance = round(total_distance, 2)  # Round to 2 decimal places
        
        logger.info(f"Total distance for all vehicles in {timeframe}: {total_distance} km")
        return total_distance

    except Exception as e:
        logger.error(f"Error getting total distance for all vehicles: {e}")
        raise

    
  def _get_start_date(self, timeframe: str, end_date: datetime) -> datetime:
    """Helper to calculate start date based on timeframe"""
    timeframes = {
        "day": timedelta(days=1),
        "week": timedelta(days=7),
        "month": timedelta(days=30),
        "year": timedelta(days=365)
    }
    
    delta = timeframes.get(timeframe.lower(), timeframes["week"])
    return end_date - delta
  
vehicle_analytics_service = VehicleAnalyticsService()