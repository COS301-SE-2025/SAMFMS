"""
Ping Session Monitor Service
Ensures that ping sessions exist for trips (will be activated/deactivated automatically based on trip status)
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from bson import ObjectId
from schemas.entities import TripStatus
from services.driver_ping_service import driver_ping_service
from repositories.database import db_manager

logger = logging.getLogger(__name__)


class PingSessionMonitor:
    """
    Monitors and ensures ping sessions exist for trips with drivers.
    Sessions are automatically activated/deactivated based on trip status.
    """
    
    def __init__(self, check_interval_minutes: int = 5):
        """
        Initialize the ping session monitor
        
        Args:
            check_interval_minutes: How often to check for missing sessions (default: 5 minutes)
        """
        self.check_interval_minutes = check_interval_minutes
        self.running = False
        self.monitor_task: Optional[asyncio.Task] = None
        self.last_check_time: Optional[datetime] = None
        
        # Database connection
        self.db = db_manager

    async def start(self):
        """Start the ping session monitor"""
        if self.running:
            logger.warning("[PingSessionMonitor] Monitor is already running")
            return
        
        try:
            self.running = True
            self.monitor_task = asyncio.create_task(self._monitor_loop())
            logger.info(f"[PingSessionMonitor] Started monitor with {self.check_interval_minutes} minute check interval")
            
        except Exception as e:
            logger.error(f"[PingSessionMonitor] Failed to start monitor: {e}")
            self.running = False
            raise

    async def stop(self):
        """Stop the ping session monitor"""
        if not self.running:
            logger.warning("[PingSessionMonitor] Monitor is not running")
            return
        
        self.running = False
        
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                logger.info("[PingSessionMonitor] Monitor task cancelled")
        
        logger.info("[PingSessionMonitor] Monitor stopped")

    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                logger.debug("[PingSessionMonitor] Running ping session existence check")
                
                # Check for missing ping sessions (not about activation, just existence)
                created_count = await self._ensure_ping_sessions_exist()
                
                if created_count > 0:
                    logger.info(f"[PingSessionMonitor] Created {created_count} missing ping sessions")
                else:
                    logger.debug("[PingSessionMonitor] All trips with drivers have ping sessions")
                
                # Update last check time
                self.last_check_time = datetime.utcnow()
                
                # Wait for the next check interval
                await asyncio.sleep(self.check_interval_minutes * 60)
                
            except asyncio.CancelledError:
                logger.info("[PingSessionMonitor] Monitor cancelled")
                break
            except Exception as e:
                logger.error(f"[PingSessionMonitor] Error in monitor loop: {e}")
                # Continue running even if there's an error
                await asyncio.sleep(30)  # Wait 30 seconds before retrying

    async def _ensure_ping_sessions_exist(self) -> int:
        """Ensure ping sessions exist for all trips with drivers (regardless of trip status)"""
        try:
            # Get all trips that have drivers assigned
            trips_with_drivers = await self._get_trips_with_drivers()
            
            if not trips_with_drivers:
                logger.debug("[PingSessionMonitor] No trips with drivers found")
                return 0
            
            logger.debug(f"[PingSessionMonitor] Found {len(trips_with_drivers)} trips with drivers")
            
            created_sessions = 0
            
            for trip in trips_with_drivers:
                trip_id = str(trip["_id"])
                driver_id = trip.get("driver_assignment")
                
                # Check if ping session exists for this trip
                has_session = await self._has_ping_session(trip_id)
                
                if not has_session:
                    logger.info(f"[PingSessionMonitor] Creating ping session for trip {trip_id}, driver {driver_id}")
                    try:
                        session = await driver_ping_service.get_or_create_ping_session(trip_id, driver_id)
                        created_sessions += 1
                        logger.info(f"[PingSessionMonitor] ✓ Created ping session {session.id} for trip {trip_id}")
                    except Exception as e:
                        logger.error(f"[PingSessionMonitor] ✗ Failed to create ping session for trip {trip_id}: {e}")
                else:
                    logger.debug(f"[PingSessionMonitor] ✓ Trip {trip_id} already has ping session")
            
            if created_sessions > 0:
                logger.info(f"[PingSessionMonitor] SUMMARY: Created {created_sessions} new ping sessions")
            
            return created_sessions
            
        except Exception as e:
            logger.error(f"[PingSessionMonitor] Failed to ensure ping sessions exist: {e}")
            return 0

    async def _get_trips_with_drivers(self) -> List[Dict]:
        """Get all trips that have drivers assigned (regardless of status)"""
        try:
            pipeline = [
                {
                    "$match": {
                        "driver_assignment": {"$exists": True, "$ne": None}
                    }
                },
                {
                    "$project": {
                        "_id": 1,
                        "status": 1,
                        "driver_assignment": 1
                    }
                }
            ]
            
            cursor = self.db.trips.aggregate(pipeline)
            trips = await cursor.to_list(length=None)
            return trips
            
        except Exception as e:
            logger.error(f"[PingSessionMonitor] Failed to get trips with drivers: {e}")
            return []

    async def _has_ping_session(self, trip_id: str) -> bool:
        """Check if a ping session exists for the given trip (regardless of active status)"""
        try:
            session = await self.db.driver_ping_sessions.find_one({"trip_id": trip_id})
            return session is not None
        except Exception as e:
            logger.error(f"[PingSessionMonitor] Failed to check if ping session exists for trip {trip_id}: {e}")
            return False

    async def check_now(self) -> int:
        """Manually trigger a ping session existence check"""
        logger.info("[PingSessionMonitor] Manual ping session existence check triggered")
        return await self._ensure_ping_sessions_exist()

    async def get_status(self) -> Dict[str, Any]:
        """Get status overview of ping sessions"""
        try:
            # Get all trips with drivers
            trips_with_drivers = await self._get_trips_with_drivers()
            total_trips_with_drivers = len(trips_with_drivers)
            
            # Get all ping sessions
            ping_sessions = await self.db.driver_ping_sessions.find({}).to_list(length=None)
            total_sessions = len(ping_sessions)
            active_sessions = len([s for s in ping_sessions if s.get("status") == "active"])
            inactive_sessions = len([s for s in ping_sessions if s.get("status") != "active"])
            
            # Get trips by status
            all_trips = await self.db.trips.find({}).to_list(length=None)
            trips_by_status = {}
            for trip in all_trips:
                status = trip.get("status", "unknown")
                if status not in trips_by_status:
                    trips_by_status[status] = 0
                trips_by_status[status] += 1
            
            # Calculate missing sessions (trips with drivers but no session)
            missing_sessions = 0
            for trip in trips_with_drivers:
                trip_id = str(trip["_id"])
                has_session = await self._has_ping_session(trip_id)
                if not has_session:
                    missing_sessions += 1
            
            return {
                "monitor_status": "running" if self.running else "stopped",
                "total_trips_with_drivers": total_trips_with_drivers,
                "ping_sessions": {
                    "total": total_sessions,
                    "active": active_sessions,
                    "inactive": inactive_sessions,
                    "missing": missing_sessions
                },
                "trips_by_status": trips_by_status,
                "last_check": self.last_check_time.isoformat() if self.last_check_time else None
            }
            
        except Exception as e:
            logger.error(f"[PingSessionMonitor] Failed to get status: {e}")
            return {"error": str(e)}


# Global instance
ping_session_monitor = PingSessionMonitor()