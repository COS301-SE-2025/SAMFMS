"""
Driver phone ping tracking service for violation monitoring
"""
import logging
import asyncio
import os
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
        
    async def get_or_create_ping_session(self, trip_id: str, driver_id: str) -> DriverPingSession:
        """Get existing ping session for trip or create new one if it doesn't exist"""
        logger.info(f"[DriverPingService] Getting/creating ping session for trip {trip_id}, driver {driver_id}")
        
        try:
            # Check if session already exists for this trip
            existing_session = await self._get_session_for_trip(trip_id)
            
            if existing_session:
                logger.info(f"[DriverPingService] Found existing ping session {existing_session.id} for trip {trip_id}")
                # Update driver if changed
                if existing_session.driver_id != driver_id:
                    await self.db.driver_ping_sessions.update_one(
                        {"trip_id": trip_id},
                        {
                            "$set": {
                                "driver_id": driver_id,
                                "updated_at": datetime.utcnow()
                            }
                        }
                    )
                    logger.info(f"[DriverPingService] Updated driver for session {existing_session.id} from {existing_session.driver_id} to {driver_id}")
                
                return existing_session
            
            # Create new session - only one per trip ever
            session_data = {
                "trip_id": trip_id,
                "driver_id": driver_id,
                "is_active": False,  # Will be set based on trip status
                "started_at": datetime.utcnow(),
                "ping_count": 0,
                "total_violations": 0,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await self.db.driver_ping_sessions.insert_one(session_data)
            session_data["_id"] = str(result.inserted_id)
            
            session = DriverPingSession(**session_data)
            
            logger.info(f"[DriverPingService] Created new ping session {session.id} for trip {trip_id}")
            return session
            
        except Exception as e:
            logger.error(f"[DriverPingService] Failed to get/create ping session: {e}")
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
            # First, check current trip status to determine if session should be active
            trip_status = await self._get_trip_status(trip_id)
            if not trip_status:
                return {
                    "status": "error",
                    "message": "Trip not found"
                }
            
            # Get trip info for driver assignment
            trip_info = await self._get_trip_info(trip_id)
            if not trip_info or not trip_info.get("driver_assignment"):
                return {
                    "status": "error", 
                    "message": "Trip has no driver assigned"
                }
            
            driver_id = trip_info["driver_assignment"]
            
            # Get or create ping session for this trip
            session = await self.get_or_create_ping_session(trip_id, driver_id)
            
            # Determine if session should be active based on trip status
            should_be_active = (trip_status == "in_progress")
            
            # Update session activity status if needed
            if session.is_active != should_be_active:
                await self._update_session_activity(session.id, should_be_active)
                session.is_active = should_be_active
                logger.info(f"[DriverPingService] Updated session {session.id} active status to {should_be_active} (trip status: {trip_status})")
            
            # If session should not be active, don't process the ping
            if not should_be_active:
                return {
                    "status": "inactive",
                    "message": f"Ping session is inactive because trip status is '{trip_status}' (not 'in_progress')",
                    "trip_status": trip_status,
                    "session_active": False
                }
            
            # Process ping for active session
            logger.info(f"[DriverPingService] Processing ping for active session {session.id}")
            
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
            
            # Prepare response
            response_data = {
                "status": "success",
                "message": "Ping processed successfully",
                "ping_received_at": ping_time,
                "next_ping_expected_at": next_expected,
                "session_active": True,
                "violations_count": session.total_violations
            }
            
            return response_data
            
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
                
                # Convert last_ping_location dict to LocationPoint if needed
                if session_doc.get("last_ping_location") and isinstance(session_doc["last_ping_location"], dict):
                    session_doc["last_ping_location"] = LocationPoint(**session_doc["last_ping_location"])
                
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
                
                # Convert last_ping_location dict to LocationPoint if needed
                if session_doc.get("last_ping_location") and isinstance(session_doc["last_ping_location"], dict):
                    session_doc["last_ping_location"] = LocationPoint(**session_doc["last_ping_location"])
                
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

    async def _get_trip_status(self, trip_id: str) -> Optional[str]:
        """Get current status of a trip"""
        try:
            trip_doc = await self.db.trips.find_one(
                {"_id": ObjectId(trip_id)},
                {"status": 1}
            )
            return trip_doc.get("status") if trip_doc else None
            
        except Exception as e:
            logger.error(f"[DriverPingService] Failed to get trip status: {e}")
            return None
    
    async def _get_trip_info(self, trip_id: str) -> Optional[Dict]:
        """Get trip information including driver assignment"""
        try:
            trip_doc = await self.db.trips.find_one(
                {"_id": ObjectId(trip_id)},
                {"driver_assignment": 1, "status": 1}
            )
            return trip_doc if trip_doc else None
            
        except Exception as e:
            logger.error(f"[DriverPingService] Failed to get trip info: {e}")
            return None
    
    async def _get_session_for_trip(self, trip_id: str) -> Optional[DriverPingSession]:
        """Get ping session for a trip (regardless of active status)"""
        try:
            session_doc = await self.db.driver_ping_sessions.find_one({
                "trip_id": trip_id
            })
            
            if session_doc:
                session_doc["_id"] = str(session_doc["_id"])
                
                # Convert last_ping_location dict to LocationPoint if needed
                if session_doc.get("last_ping_location") and isinstance(session_doc["last_ping_location"], dict):
                    session_doc["last_ping_location"] = LocationPoint(**session_doc["last_ping_location"])
                
                return DriverPingSession(**session_doc)
            return None
            
        except Exception as e:
            logger.error(f"[DriverPingService] Failed to get session for trip: {e}")
            return None
    
    async def _update_session_activity(self, session_id: str, is_active: bool) -> None:
        """Update session activity status"""
        try:
            update_data = {
                "is_active": is_active,
                "updated_at": datetime.utcnow()
            }
            
            if is_active:
                # Start monitoring task if becoming active
                update_data["activated_at"] = datetime.utcnow()
            else:
                # Stop monitoring and end violations if becoming inactive
                update_data["deactivated_at"] = datetime.utcnow()
                
            await self.db.driver_ping_sessions.update_one(
                {"_id": ObjectId(session_id)},
                {"$set": update_data}
            )
            
            # Manage monitoring tasks
            session_doc = await self.db.driver_ping_sessions.find_one({"_id": ObjectId(session_id)})
            if session_doc:
                trip_id = session_doc["trip_id"]
                
                if is_active:
                    # Start monitoring if not already running
                    if trip_id not in self.active_sessions:
                        session_obj = DriverPingSession(**{**session_doc, "_id": str(session_doc["_id"])})
                        task = asyncio.create_task(self._monitor_ping_violations(session_obj))
                        self.active_sessions[trip_id] = task
                        logger.info(f"[DriverPingService] Started monitoring for session {session_id}")
                else:
                    # Stop monitoring and end violations
                    if trip_id in self.active_sessions:
                        task = self.active_sessions.pop(trip_id)
                        task.cancel()
                        logger.info(f"[DriverPingService] Stopped monitoring for session {session_id}")
                    
                    # End active violations
                    await self._end_active_violations(trip_id)
            
        except Exception as e:
            logger.error(f"[DriverPingService] Failed to update session activity: {e}")
            raise


# Singleton instance
driver_ping_service = DriverPingService()