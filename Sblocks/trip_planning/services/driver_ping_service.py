"""
Driver phone ping tracking service for violation monitoring
"""
import logging
import asyncio
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from bson import ObjectId

from repositories.database import db_manager
from schemas.entities import (
    DriverPingSession, PhoneUsageViolation, PhoneUsageViolationType,
    LocationPoint, TripStatus
)
from events.publisher import event_publisher

logger = logging.getLogger(__name__)


class DriverPingService:
    """Service for tracking driver phone pings and violations"""
    
    PING_TIMEOUT_SECONDS = 30  # 30 seconds timeout for violations
    
    def __init__(self):
        self.db = db_manager
        self.active_sessions: Dict[str, asyncio.Task] = {}  # trip_id -> monitoring task
        
    async def start_ping_session(self, trip_id: str, driver_id: str) -> DriverPingSession:
        """Start a new ping session for a trip"""
        logger.info(f"[DriverPingService] Starting ping session for trip {trip_id}, driver {driver_id}")
        
        try:
            # End any existing session for this trip
            await self._end_existing_session(trip_id)
            
            # Create new session
            session_data = {
                "trip_id": trip_id,
                "driver_id": driver_id,
                "is_active": True,
                "started_at": datetime.utcnow(),
                "ping_count": 0,
                "total_violations": 0,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await self.db.driver_ping_sessions.insert_one(session_data)
            session_data["_id"] = str(result.inserted_id)
            
            session = DriverPingSession(**session_data)
            
            # Start monitoring task
            task = asyncio.create_task(self._monitor_ping_violations(session))
            self.active_sessions[trip_id] = task
            
            logger.info(f"[DriverPingService] Started ping session {session.id} for trip {trip_id}")
            return session
            
        except Exception as e:
            logger.error(f"[DriverPingService] Failed to start ping session: {e}")
            raise
    
    async def end_ping_session(self, trip_id: str) -> None:
        """End ping session for a trip"""
        logger.info(f"[DriverPingService] Ending ping session for trip {trip_id}")
        
        try:
            # Cancel monitoring task
            if trip_id in self.active_sessions:
                task = self.active_sessions.pop(trip_id)
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            # Update session in database
            await self.db.driver_ping_sessions.update_one(
                {"trip_id": trip_id, "is_active": True},
                {
                    "$set": {
                        "is_active": False,
                        "ended_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # End any active violations for this trip
            await self._end_active_violations(trip_id)
            
            logger.info(f"[DriverPingService] Ended ping session for trip {trip_id}")
            
        except Exception as e:
            logger.error(f"[DriverPingService] Failed to end ping session: {e}")
            raise
    
    async def process_ping(self, trip_id: str, location: LocationPoint, ping_time: datetime) -> Dict:
        """Process driver ping and update violation tracking"""
        logger.info(f"[DriverPingService] Processing ping for trip {trip_id}")
        
        try:
            # Get active session
            session = await self._get_active_session(trip_id)
            if not session:
                return {
                    "status": "error",
                    "message": "No active ping session found for this trip"
                }
            
            # Update session with ping data
            await self._update_session_ping(session.id, location, ping_time)
            
            # Check if there's an active violation to end
            if session.current_violation_id:
                await self._end_violation(session.current_violation_id, location, ping_time)
                # Clear the current violation reference
                await self.db.driver_ping_sessions.update_one(
                    {"_id": ObjectId(session.id)},
                    {"$set": {"current_violation_id": None, "updated_at": datetime.utcnow()}}
                )
            
            next_expected = ping_time + timedelta(seconds=self.PING_TIMEOUT_SECONDS)
            
            return {
                "status": "success",
                "message": "Ping processed successfully",
                "ping_received_at": ping_time,
                "next_ping_expected_at": next_expected,
                "session_active": True,
                "violations_count": session.total_violations
            }
            
        except Exception as e:
            logger.error(f"[DriverPingService] Failed to process ping: {e}")
            return {
                "status": "error",
                "message": f"Failed to process ping: {str(e)}"
            }
    
    async def _monitor_ping_violations(self, session: DriverPingSession) -> None:
        """Monitor ping timeouts and create violations"""
        logger.info(f"[DriverPingService] Starting violation monitoring for session {session.id}")
        
        try:
            while True:
                await asyncio.sleep(self.PING_TIMEOUT_SECONDS)
                
                # Get current session state
                current_session = await self._get_session_by_id(session.id)
                if not current_session or not current_session.is_active:
                    logger.info(f"[DriverPingService] Session {session.id} no longer active, stopping monitoring")
                    break
                
                # Check if we haven't received a ping in the timeout period
                if current_session.last_ping_time:
                    time_since_last_ping = datetime.utcnow() - current_session.last_ping_time
                    if time_since_last_ping.total_seconds() >= self.PING_TIMEOUT_SECONDS:
                        # Only create violation if there isn't already an active one
                        if not current_session.current_violation_id:
                            await self._create_violation(current_session)
                
        except asyncio.CancelledError:
            logger.info(f"[DriverPingService] Monitoring cancelled for session {session.id}")
            raise
        except Exception as e:
            logger.error(f"[DriverPingService] Error in violation monitoring: {e}")
    
    async def _create_violation(self, session: DriverPingSession) -> PhoneUsageViolation:
        """Create a new phone usage violation"""
        logger.info(f"[DriverPingService] Creating violation for session {session.id}")
        
        try:
            # Use last known location or default location
            violation_location = session.last_ping_location or LocationPoint(
                type="Point",
                coordinates=[0.0, 0.0]  # Default coordinates if no location available
            )
            
            violation_data = {
                "trip_id": session.trip_id,
                "driver_id": session.driver_id,
                "violation_type": PhoneUsageViolationType.PHONE_USAGE,
                "start_time": datetime.utcnow(),
                "start_location": violation_location.dict(),
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await self.db.phone_usage_violations.insert_one(violation_data)
            violation_id = str(result.inserted_id)
            
            # Update session with current violation
            await self.db.driver_ping_sessions.update_one(
                {"_id": ObjectId(session.id)},
                {
                    "$set": {
                        "current_violation_id": violation_id,
                        "updated_at": datetime.utcnow()
                    },
                    "$inc": {"total_violations": 1}
                }
            )
            
            # Publish violation event
            await event_publisher.publish("driver.violation_started", {
                "violation_id": violation_id,
                "trip_id": session.trip_id,
                "driver_id": session.driver_id,
                "violation_type": "phone_usage",
                "start_time": violation_data["start_time"].isoformat(),
                "location": violation_location.dict()
            })
            
            violation_data["_id"] = violation_id
            violation = PhoneUsageViolation(**violation_data)
            
            logger.info(f"[DriverPingService] Created violation {violation_id} for trip {session.trip_id}")
            return violation
            
        except Exception as e:
            logger.error(f"[DriverPingService] Failed to create violation: {e}")
            raise
    
    async def _end_violation(self, violation_id: str, end_location: LocationPoint, end_time: datetime) -> None:
        """End an active violation"""
        logger.info(f"[DriverPingService] Ending violation {violation_id}")
        
        try:
            # Get the violation
            violation_doc = await self.db.phone_usage_violations.find_one(
                {"_id": ObjectId(violation_id)}
            )
            
            if not violation_doc:
                logger.warning(f"[DriverPingService] Violation {violation_id} not found")
                return
            
            # Calculate duration
            start_time = violation_doc["start_time"]
            duration_seconds = int((end_time - start_time).total_seconds())
            
            # Update violation
            await self.db.phone_usage_violations.update_one(
                {"_id": ObjectId(violation_id)},
                {
                    "$set": {
                        "end_time": end_time,
                        "end_location": end_location.dict(),
                        "duration_seconds": duration_seconds,
                        "is_active": False,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Publish violation ended event
            await event_publisher.publish("driver.violation_ended", {
                "violation_id": violation_id,
                "trip_id": violation_doc["trip_id"],
                "driver_id": violation_doc["driver_id"],
                "duration_seconds": duration_seconds,
                "end_time": end_time.isoformat(),
                "end_location": end_location.dict()
            })
            
            logger.info(f"[DriverPingService] Ended violation {violation_id}, duration: {duration_seconds}s")
            
        except Exception as e:
            logger.error(f"[DriverPingService] Failed to end violation: {e}")
            raise
    
    async def _get_active_session(self, trip_id: str) -> Optional[DriverPingSession]:
        """Get active ping session for a trip"""
        try:
            session_doc = await self.db.driver_ping_sessions.find_one({
                "trip_id": trip_id,
                "is_active": True
            })
            
            if session_doc:
                session_doc["_id"] = str(session_doc["_id"])
                return DriverPingSession(**session_doc)
            return None
            
        except Exception as e:
            logger.error(f"[DriverPingService] Failed to get active session: {e}")
            raise
    
    async def _get_session_by_id(self, session_id: str) -> Optional[DriverPingSession]:
        """Get session by ID"""
        try:
            session_doc = await self.db.driver_ping_sessions.find_one({
                "_id": ObjectId(session_id)
            })
            
            if session_doc:
                session_doc["_id"] = str(session_doc["_id"])
                return DriverPingSession(**session_doc)
            return None
            
        except Exception as e:
            logger.error(f"[DriverPingService] Failed to get session by ID: {e}")
            raise
    
    async def _update_session_ping(self, session_id: str, location: LocationPoint, ping_time: datetime) -> None:
        """Update session with new ping data"""
        try:
            await self.db.driver_ping_sessions.update_one(
                {"_id": ObjectId(session_id)},
                {
                    "$set": {
                        "last_ping_time": ping_time,
                        "last_ping_location": location.dict(),
                        "updated_at": datetime.utcnow()
                    },
                    "$inc": {"ping_count": 1}
                }
            )
            
        except Exception as e:
            logger.error(f"[DriverPingService] Failed to update session ping: {e}")
            raise
    
    async def _end_existing_session(self, trip_id: str) -> None:
        """End any existing active session for a trip"""
        try:
            await self.db.driver_ping_sessions.update_many(
                {"trip_id": trip_id, "is_active": True},
                {
                    "$set": {
                        "is_active": False,
                        "ended_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"[DriverPingService] Failed to end existing session: {e}")
            raise
    
    async def _end_active_violations(self, trip_id: str) -> None:
        """End all active violations for a trip"""
        try:
            await self.db.phone_usage_violations.update_many(
                {"trip_id": trip_id, "is_active": True},
                {
                    "$set": {
                        "is_active": False,
                        "end_time": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"[DriverPingService] Failed to end active violations: {e}")
            raise
    
    async def get_trip_violations(self, trip_id: str) -> List[PhoneUsageViolation]:
        """Get all violations for a trip"""
        try:
            cursor = self.db.phone_usage_violations.find({"trip_id": trip_id})
            violations = []
            
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                violations.append(PhoneUsageViolation(**doc))
                
            return violations
            
        except Exception as e:
            logger.error(f"[DriverPingService] Failed to get trip violations: {e}")
            raise


# Singleton instance
driver_ping_service = DriverPingService()