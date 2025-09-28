"""
Driver History Scheduler Service

This service runs background tasks to periodically update driver history calculations.
It ensures driver statistics are kept up-to-date even when trips are not being completed.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import signal
import sys

from repositories.database import db_manager, db_manager_management
from services.driver_history_service import DriverHistoryService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DriverHistoryScheduler:
    """Background scheduler for driver history updates"""
    
    def __init__(self, update_interval: int = 60):
        """
        Initialize the scheduler
        
        Args:
            update_interval: Interval in seconds between updates (default: 60)
        """
        self.update_interval = update_interval
        self.driver_history_service = DriverHistoryService(db_manager, db_manager_management)
        self.is_running = False
        self.task: Optional[asyncio.Task] = None
        self.stats = {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "last_run": None,
            "last_success": None,
            "last_error": None
        }
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        asyncio.create_task(self.stop())
    
    async def start(self):
        """Start the scheduler"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        logger.info(f"Starting driver history scheduler with {self.update_interval}s interval")
        self.is_running = True
        self.task = asyncio.create_task(self._scheduler_loop())
    
    async def stop(self):
        """Stop the scheduler gracefully"""
        if not self.is_running:
            logger.warning("Scheduler is not running")
            return
        
        logger.info("Stopping driver history scheduler...")
        self.is_running = False
        
        if self.task and not self.task.done():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                logger.info("Scheduler task cancelled successfully")
        
        logger.info("Driver history scheduler stopped")
    
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        logger.info("Driver history scheduler loop started")
        
        while self.is_running:
            try:
                await self._run_update_cycle()
                await asyncio.sleep(self.update_interval)
            except asyncio.CancelledError:
                logger.info("Scheduler loop cancelled")
                break
            except Exception as e:
                logger.error(f"Unexpected error in scheduler loop: {e}")
                self.stats["failed_runs"] += 1
                self.stats["last_error"] = str(e)
                # Continue running even if there's an error
                await asyncio.sleep(self.update_interval)
        
        logger.info("Driver history scheduler loop ended")
    
    async def _run_update_cycle(self):
        """Run a single update cycle"""
        start_time = datetime.now()
        self.stats["total_runs"] += 1
        self.stats["last_run"] = start_time.isoformat()
        
        logger.info(f"Starting driver history update cycle at {start_time}")
        
        try:
            # Get all drivers that need updates
            drivers_updated = await self._update_all_drivers()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.stats["successful_runs"] += 1
            self.stats["last_success"] = end_time.isoformat()
            
            logger.info(
                f"Driver history update cycle completed successfully. "
                f"Updated {drivers_updated} drivers in {duration:.2f}s"
            )
            
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.stats["failed_runs"] += 1
            self.stats["last_error"] = str(e)
            
            logger.error(
                f"Driver history update cycle failed after {duration:.2f}s: {e}"
            )
            raise
    
    async def _update_all_drivers(self) -> int:
        """Update driver history for all drivers"""
        try:
            # Get list of all unique drivers from completed trips
            drivers = await self._get_drivers_needing_updates()
            
            if not drivers:
                logger.debug("No drivers found needing history updates")
                return 0
            
            updated_count = 0
            
            for driver_id in drivers:
                try:
                    # Update driver history for this driver
                    await self.driver_history_service._recalculate_driver_history(driver_id)
                    updated_count += 1
                    logger.debug(f"Updated history for driver {driver_id}")
                    
                except Exception as e:
                    logger.error(f"Failed to update history for driver {driver_id}: {e}")
                    # Continue with other drivers even if one fails
                    continue
            
            return updated_count
            
        except Exception as e:
            logger.error(f"Error getting drivers for updates: {e}")
            raise
    
    async def _get_drivers_needing_updates(self) -> List[str]:
        """Get list of drivers that need history updates"""
        try:
            # Get all unique driver IDs from trips collection
            trips_collection = db_manager.db.trips
            
            # Find unique driver IDs from trips in the last 24 hours
            # This ensures we update active drivers more frequently
            cutoff_time = datetime.now() - timedelta(hours=24)
            
            pipeline = [
                {
                    "$match": {
                        "status": "completed",
                        "end_time": {"$gte": cutoff_time}
                    }
                },
                {
                    "$group": {
                        "_id": "$driver_id"
                    }
                },
                {
                    "$project": {
                        "driver_id": "$_id",
                        "_id": 0
                    }
                }
            ]
            
            result = trips_collection.aggregate(pipeline)
            drivers = [doc["driver_id"] for doc in result if doc.get("driver_id")]
            
            logger.debug(f"Found {len(drivers)} drivers needing updates")
            return drivers
            
        except Exception as e:
            logger.error(f"Error querying drivers from trips: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """Get scheduler statistics"""
        return {
            **self.stats,
            "is_running": self.is_running,
            "update_interval": self.update_interval,
            "success_rate": (
                (self.stats["successful_runs"] / max(self.stats["total_runs"], 1)) * 100
                if self.stats["total_runs"] > 0 else 0
            )
        }
    
    async def force_update(self) -> Dict:
        """Force an immediate update cycle"""
        logger.info("Forcing immediate driver history update cycle")
        
        try:
            await self._run_update_cycle()
            return {"status": "success", "message": "Update cycle completed successfully"}
        except Exception as e:
            logger.error(f"Forced update cycle failed: {e}")
            return {"status": "error", "message": str(e)}


# Global scheduler instance
scheduler_instance: Optional[DriverHistoryScheduler] = None


async def start_scheduler(update_interval: int = 60):
    """Start the global scheduler instance"""
    global scheduler_instance
    
    if scheduler_instance is not None:
        logger.warning("Scheduler is already initialized")
        return scheduler_instance
    
    scheduler_instance = DriverHistoryScheduler(update_interval)
    await scheduler_instance.start()
    
    logger.info("Driver history scheduler started successfully")
    return scheduler_instance


async def stop_scheduler():
    """Stop the global scheduler instance"""
    global scheduler_instance
    
    if scheduler_instance is None:
        logger.warning("No scheduler instance to stop")
        return
    
    await scheduler_instance.stop()
    scheduler_instance = None
    
    logger.info("Driver history scheduler stopped successfully")


def get_scheduler() -> Optional[DriverHistoryScheduler]:
    """Get the current scheduler instance"""
    return scheduler_instance


# Main entry point for testing
async def main():
    """Main function for standalone testing"""
    logger.info("Starting driver history scheduler service...")
    
    try:
        # Start the scheduler
        scheduler = await start_scheduler(update_interval=60)
        
        # Keep the service running
        while True:
            await asyncio.sleep(10)
            
            # Print stats every 10 seconds for monitoring
            stats = scheduler.get_stats()
            logger.info(f"Scheduler stats: {stats}")
            
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
    finally:
        await stop_scheduler()


if __name__ == "__main__":
    asyncio.run(main())