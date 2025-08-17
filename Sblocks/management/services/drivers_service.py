"""
Driver management service
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import aiohttp

from repositories.repositories import DriverCountRepository
from events.publisher import event_publisher
from schemas.requests import DailyDriverCount
from schemas.entities import DailyDriverCount

logger = logging.getLogger(__name__)


class DriversService:
    """Service for total drivers management"""
    
    def __init__(self):
        self.drivers_repo = DriverCountRepository
    
    async def get_daily_driver_counts(self, start_date: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """Get all daily driver counts from a certain date"""
        try:
            await DriverCountRepository.get_daily_driver_counts(start_date)
            
            
            logger.info(f"Driver daily driver counts requested")
            
        except Exception as e:
            logger.error(f"Error showing driver counts: {e}")
            raise

    async def add_driver(self):
        """Create a user account for the driver in the daily driver counts collection"""
        try:

            await DriverCountRepository.add_driver(self)
            logger.info(f"Driver added successfully")
        except Exception as e:
            logger.error(f"Error adding driver: {e}")
            raise
            


    async def handle_request(self, method: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle driver counts requests from request consumer"""
        try:
            data = user_context.get("data", {})
            endpoint = user_context.get("endpoint", "")
                                    
            if method == "POST":
                if "daily-driver-count" in endpoint or "daily_driver_count" in endpoint:
                    if "start_date" in data:
                        start_date = data.get("start_date")
                        records = await self.get_daily_driver_counts(start_date)
                        return {"success": True, "data": records}
                    else:
                        records = await self.get_daily_driver_counts()
                        return {"success": True, "data": records}

            else:
                return {"success": False, "error": "Unsupported drivers operation", "method" : method, "user_context": user_context}
            
        except Exception as e:
            logger.error(f"Error handling drivers request: {e}")
            return {"success": False, "error": str(e), "method" : method, "user_context": user_context}


# Global service instance
drivers_service = DriversService()