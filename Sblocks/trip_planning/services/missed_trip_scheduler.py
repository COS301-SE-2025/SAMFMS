"""
Scheduler service for marking missed trips
"""
import asyncio
import logging
from datetime import datetime, timedelta

from services.trip_service import trip_service

logger = logging.getLogger(__name__)


class MissedTripScheduler:
    """Service for scheduling missed trip checks"""
    
    def __init__(self, check_interval_minutes: int = 5):
        self.check_interval_minutes = check_interval_minutes
        self.running = False
        self._task = None

    async def start(self):
        """Start the missed trip scheduler"""
        if self.running:
            logger.warning("[MissedTripScheduler] Scheduler is already running")
            return
        
        self.running = True
        logger.info(f"[MissedTripScheduler] Starting missed trip scheduler (check interval: {self.check_interval_minutes} minutes)")
        
        self._task = asyncio.create_task(self._scheduler_loop())

    async def stop(self):
        """Stop the missed trip scheduler"""
        if not self.running:
            return
        
        logger.info("[MissedTripScheduler] Stopping missed trip scheduler")
        self.running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                logger.debug("[MissedTripScheduler] Running missed trip check")
                missed_count = await trip_service.mark_missed_trips()
                
                if missed_count > 0:
                    logger.info(f"[MissedTripScheduler] Processed {missed_count} missed trips")
                
                # Wait for the next check interval
                await asyncio.sleep(self.check_interval_minutes * 60)
                
            except asyncio.CancelledError:
                logger.info("[MissedTripScheduler] Scheduler cancelled")
                break
            except Exception as e:
                logger.error(f"[MissedTripScheduler] Error in scheduler loop: {e}")
                # Continue running even if there's an error
                await asyncio.sleep(60)  # Wait 1 minute before retrying

    async def check_now(self) -> int:
        """Manually trigger a missed trip check"""
        logger.info("[MissedTripScheduler] Manual missed trip check triggered")
        return await trip_service.mark_missed_trips()


# Global instance
missed_trip_scheduler = MissedTripScheduler()
