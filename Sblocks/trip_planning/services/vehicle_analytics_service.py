"""
Vehicle Analytics service for trip planning
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from bson import ObjectId

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