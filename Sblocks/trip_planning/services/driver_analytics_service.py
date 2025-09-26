"""
Driver Analytics service for trip planning
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from bson import ObjectId

from repositories.database import db_manager, db_manager_management
from schemas.entities import TripAnalytics, TripStatus
from schemas.requests import AnalyticsRequest

logger = logging.getLogger(__name__)

class DriverAnalyticsService:
    """Service for driver analytics and performance"""

    def __init__(self):
        self.db = db_manager
        self.db_management = db_manager_management
    
    async def _get_driver_names(self, driver_ids: List[str]) -> Dict[str, str]:
            """
            Get driver names from driver IDs.
            """
            try:
                if not driver_ids:
                    return {}
                    
                # Convert to ObjectIds if they are valid ObjectId strings, otherwise keep as strings
                query_ids = []
                for driver_id in driver_ids:
                    if len(driver_id) == 24:  # Standard ObjectId length
                        try:
                            query_ids.append(ObjectId(driver_id))
                        except:
                            query_ids.append(driver_id)
                    else:
                        query_ids.append(driver_id)
                
                # Query drivers collection - adjust field names based on your schema
                drivers_cursor = db_manager_management.drivers.find(
                    {"_id": {"$in": query_ids}},
                    {"first_name": 1, "last_name": 1}
                )
                
                drivers_data = await drivers_cursor.to_list(None)
                driver_names = {}
                
                for driver in drivers_data:
                    driver_id = str(driver["_id"])
                    
                    # Try different name field combinations based on your schema
                    name = (
                        f"{driver.get('first_name', '')} {driver.get('last_name', '')}".strip()
                    )
                    
                    driver_names[driver_id] = name
                
                # Add default names for drivers not found in the drivers collection
                for original_id in driver_ids:
                    if original_id not in driver_names:
                        driver_names[original_id] = f"Driver {original_id}"
                
                return driver_names
                
            except Exception as e:
                logger.warning(f"Failed to get driver names: {e}")
                # Return default names
                return {driver_id: f"Driver {driver_id}" for driver_id in driver_ids}

    async def get_total_trips(self, timeframe: str) -> int:
        """Get total number of trips within timeframe"""
        try:
            # Calculate date range based on timeframe
            end_date = datetime.now(timezone.utc)
            start_date = self._get_start_date(timeframe, end_date)
            logger.info(f"End date: {end_date}")
            logger.info(f"Start date: {start_date}")

            # Query trip history with date filter
            total = await self.db.trip_history.count_documents({
                "created_at": {"$gte": start_date, "$lte": end_date}
            })
            
            logger.info(f"Total trips for {timeframe}: {total}")
            return total

        except Exception as e:
            logger.error(f"Error getting total trips: {e}")
            raise

    async def get_completion_rate(self, timeframe: str) -> float:
        """Calculate trip completion rate within timeframe"""
        try:
            end_date = datetime.now(timezone.utc)
            start_date = self._get_start_date(timeframe, end_date)

            # Get completed and cancelled counts
            completed = await self.db.trip_history.count_documents({
                "created_at": {"$gte": start_date, "$lte": end_date},
                "status": "completed"
            })
            
            cancelled = await self.db.trip_history.count_documents({
                "created_at": {"$gte": start_date, "$lte": end_date},
                "status": "cancelled"
            })

            total = completed + cancelled
            rate = (completed / total * 100) if total > 0 else 0
            
            logger.info(f"Completion rate for {timeframe}: {rate}%")
            return round(rate, 2)

        except Exception as e:
            logger.error(f"Error calculating completion rate: {e}")
            raise

    async def get_average_trips_per_day(self, timeframe: str) -> float:
        """Calculate average trips per day within timeframe"""
        try:
            end_date = datetime.now(timezone.utc)
            start_date = self._get_start_date(timeframe, end_date)

            # Get trips with actual start and end times
            trips = await self.db.trip_history.find({
                "created_at": {"$gte": start_date, "$lte": end_date},
                "actual_start_time": {"$exists": True},
                "actual_end_time": {"$exists": True}
            }).to_list(None)

            # Calculate days between start and end date
            days = (end_date - start_date).days or 1  # Minimum 1 day
            total_trips = len(trips)
            average = total_trips / days

            logger.info(f"Average trips per day for {timeframe}: {average}")
            return round(average, 2)

        except Exception as e:
            logger.error(f"Error calculating average trips per day: {e}")
            raise


    async def get_driver_trip_stats(self, timeframe: str) -> List[Dict[str, Any]]:
        """Get completed and cancelled trips per driver within timeframe"""
        try:
            end_date = datetime.now(timezone.utc)
            start_date = self._get_start_date(timeframe, end_date)

            # Aggregate trips by driver
            pipeline = [
                {
                    "$match": {
                        "created_at": {"$gte": start_date, "$lte": end_date}
                    }
                },
                {
                    "$group": {
                        "_id": "$driver_assignment",
                        "completed_trips": {
                            "$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}
                        },
                        "cancelled_trips": {
                            "$sum": {"$cond": [{"$eq": ["$status", "cancelled"]}, 1, 0]}
                        }
                    }
                }
            ]

            stats = await self.db.trip_history.aggregate(pipeline).to_list(None)
            
            # Get driver names
            driver_ids = [stat["_id"] for stat in stats]
            driver_names = await self._get_driver_names(driver_ids)

            # Format results
            formatted_stats = []
            for stat in stats:
                driver_id = stat["_id"]
                formatted_stats.append({
                    "driver_id": str(driver_id) if isinstance(driver_id, ObjectId) else driver_id,
                    "driver_name": driver_names.get(driver_id, f"Driver {driver_id}"),
                    "completed_trips": stat["completed_trips"],
                    "cancelled_trips": stat["cancelled_trips"]
                })

            logger.info(f"Driver trip stats for {timeframe}: {formatted_stats}")
            return formatted_stats

        except Exception as e:
            logger.error(f"Error getting driver trip stats: {e}")
            raise

    async def get_driver_trip_stats_by_id(self, driver_id: str, timeframe: str) -> Optional[Dict[str, Any]]:
        """Get completed and cancelled trips for a specific driver within timeframe"""
        try:
            end_date = datetime.now(timezone.utc)
            start_date = self._get_start_date(timeframe, end_date)

            # Convert to ObjectId if needed
            try:
                driver_obj_id = ObjectId(driver_id)
            except:
                driver_obj_id = driver_id  # Use as-is if not a valid ObjectId

            # Aggregate trips for the specific driver
            pipeline = [
                {
                    "$match": {
                        "driver_assignment": driver_obj_id,
                        "created_at": {"$gte": start_date, "$lte": end_date}
                    }
                },
                {
                    "$group": {
                        "_id": "$driver_assignment",
                        "completed_trips": {
                            "$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}
                        },
                        "cancelled_trips": {
                            "$sum": {"$cond": [{"$eq": ["$status", "cancelled"]}, 1, 0]}
                        }
                    }
                }
            ]

            stats = await self.db.trip_history.aggregate(pipeline).to_list(None)
            driver_names = await self._get_driver_names([driver_obj_id])
            if not stats:
                return {
                    "driver_id": driver_id,
                    "driver_name":  driver_names.get(driver_obj_id, f"Driver {driver_id}"),
                    "completed_trips": 0,
                    "cancelled_trips": 0
                }

            stat = stats[0]
            

            # Format result
            result = {
                "driver_id": str(driver_obj_id),
                "driver_name": driver_names.get(driver_obj_id, f"Driver {driver_id}"),
                "completed_trips": stat["completed_trips"],
                "cancelled_trips": stat["cancelled_trips"]
            }

            logger.info(f"Driver trip stats for {driver_id} in {timeframe}: {result}")
            return result

        except Exception as e:
            logger.error(f"Error getting trip stats for driver {driver_id}: {e}")
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


driver_analytics_service = DriverAnalyticsService()