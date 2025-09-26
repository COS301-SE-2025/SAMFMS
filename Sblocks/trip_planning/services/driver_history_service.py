"""
Driver History Service for calculating and managing driver performance metrics
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from schemas.entities import DriverHistory, RiskLevel
from repositories.database import DatabaseManager, DatabaseManagerManagement

logger = logging.getLogger(__name__)


class DriverHistoryService:
    """Service for managing driver performance history and metrics"""
    
    def __init__(self, db_manager: DatabaseManager, db_manager_management: DatabaseManagerManagement = None):
        self.db_manager = db_manager
        self.db_manager_management = db_manager_management
    
    def _convert_objectid_to_string(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Convert ObjectId fields to strings for Pydantic compatibility"""
        if doc and "_id" in doc and isinstance(doc["_id"], ObjectId):
            doc["_id"] = str(doc["_id"])
        return doc
    
    async def update_driver_history_on_trip_completion(
        self, 
        driver_id: str, 
        trip_id: str, 
        trip_status: str
    ) -> Dict[str, Any]:
        """
        Update driver history when a trip is completed
        
        Args:
            driver_id: ID of the driver
            trip_id: ID of the completed trip
            trip_status: Status of the trip ('completed', 'cancelled', etc.)
        
        Returns:
            Updated driver history data
        """
        try:
            # Get existing driver history or create new one
            history = await self._get_or_create_driver_history(driver_id)
            
            # Update trip statistics based on status
            if trip_status.lower() == 'completed':
                history.completed_trips += 1
            elif trip_status.lower() == 'cancelled':
                history.cancelled_trips += 1
            
            # Calculate trip completion rate
            total_finished_trips = history.completed_trips + history.cancelled_trips
            if total_finished_trips > 0:
                history.trip_completion_rate = (history.completed_trips / total_finished_trips) * 100
            
            # Update violation counts
            await self._update_violation_counts(history, driver_id)
            
            # Calculate safety score and risk level
            history.driver_safety_score = await self._calculate_safety_score(history)
            history.driver_risk_level = self._determine_risk_level(history)
            
            # Update timestamp
            history.last_updated = datetime.utcnow()
            
            # Save to database
            await self._save_driver_history(history)
            
            logger.info(f"Updated driver history for driver {driver_id} after trip {trip_id}")
            
            return {
                "driver_id": driver_id,
                "trip_completion_rate": history.trip_completion_rate,
                "safety_score": history.driver_safety_score,
                "risk_level": history.driver_risk_level.value,
                "total_violations": self._get_total_violations(history)
            }
            
        except Exception as e:
            logger.error(f"Error updating driver history for {driver_id}: {str(e)}")
            raise
    
    async def get_driver_history(self, driver_id: str) -> Optional[DriverHistory]:
        """
        Get driver history by driver ID
        
        Args:
            driver_id: ID of the driver
            
        Returns:
            Driver history object or None if not found
        """
        try:
            collection = self.db_manager.driver_history
            history_doc = await collection.find_one({"driver_id": driver_id})
            
            if history_doc:
                # Convert ObjectId to string for Pydantic validation
                history_doc = self._convert_objectid_to_string(history_doc)
                return DriverHistory(**history_doc)
            return None
            
        except Exception as e:
            logger.error(f"Error getting driver history for {driver_id}: {str(e)}")
            raise
    
    async def get_all_driver_histories(
        self, 
        skip: int = 0, 
        limit: int = 100,
        risk_level: Optional[str] = None,
        search: Optional[str] = None
    ) -> Tuple[List[DriverHistory], int]:
        """
        Get all driver histories with optional filtering
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            risk_level: Filter by risk level (low/medium/high)
            search: Search term for driver name, employee ID, or vehicle info
            
        Returns:
            Tuple of (list of driver history objects, total count)
        """
        try:
            collection = self.db_manager.driver_history
            
            # Build query filter
            query = {}
            if risk_level:
                query["driver_risk_level"] = risk_level.lower()
            
            # Add search functionality
            if search:
                search_regex = {"$regex": search, "$options": "i"}  # Case-insensitive search
                query["$or"] = [
                    {"driver_name": search_regex},
                    {"employee_id": search_regex},
                    {"current_vehicle": search_regex},
                    {"driver_id": search_regex}
                ]
            
            # Get total count for pagination
            total_count = await collection.count_documents(query)
            
            # Execute query with pagination
            cursor = collection.find(query).skip(skip).limit(limit).sort("driver_safety_score", -1)
            histories = []
            
            async for doc in cursor:
                # Convert ObjectId to string for Pydantic validation
                doc = self._convert_objectid_to_string(doc)
                histories.append(DriverHistory(**doc))
            
            return histories, total_count
            
        except Exception as e:
            logger.error(f"Error getting driver histories: {str(e)}")
            raise

    async def initialize_driver_histories(self) -> Dict[str, Any]:
        """
        Initialize driver history records for all drivers in the management database
        who don't already have history records. This should be called on startup.
        
        Returns:
            Dictionary with initialization statistics
        """
        try:
            if not self.db_manager_management:
                logger.warning("Management database not available, skipping driver history initialization")
                return {"initialized": 0, "existing": 0, "errors": 0}
            
            # Get all drivers from management database
            drivers_collection = self.db_manager_management.drivers
            all_drivers = []
            
            async for driver in drivers_collection.find({}):
                all_drivers.append(driver)
            
            logger.info(f"Found {len(all_drivers)} drivers in management database")
            
            # Get existing driver histories
            history_collection = self.db_manager.driver_history
            existing_histories = set()
            
            async for history in history_collection.find({}, {"driver_id": 1}):
                existing_histories.add(history["driver_id"])
            
            logger.info(f"Found {len(existing_histories)} existing driver histories")
            
            # Initialize counters
            initialized_count = 0
            existing_count = 0
            error_count = 0
            
            # Process each driver
            for driver in all_drivers:
                try:
                    employee_id = driver.get("employee_id")
                    if not employee_id:
                        logger.warning(f"Driver {driver.get('_id')} has no employee_id, skipping")
                        error_count += 1
                        continue
                    
                    # Check if history already exists
                    if employee_id in existing_histories:
                        existing_count += 1
                        continue
                    
                    # Create new driver history
                    first_name = driver.get("first_name", "")
                    last_name = driver.get("last_name", "")
                    full_name = f"{first_name} {last_name}".strip()
                    
                    if not full_name:
                        full_name = "Unknown Driver"
                    
                    # Count assigned trips for this driver
                    total_assigned = await self._count_assigned_trips(employee_id)
                    
                    new_history = DriverHistory(
                        driver_id=employee_id,
                        driver_name=full_name,
                        employee_id=employee_id,
                        total_assigned_trips=total_assigned,
                        # All other fields will use default values from the schema
                    )
                    
                    # Save to database
                    await self._save_driver_history(new_history)
                    initialized_count += 1
                    
                    logger.debug(f"Initialized history for driver {employee_id}: {full_name}")
                    
                except Exception as e:
                    logger.error(f"Error initializing history for driver {driver.get('employee_id', 'unknown')}: {str(e)}")
                    error_count += 1
            
            result = {
                "initialized": initialized_count,
                "existing": existing_count,
                "errors": error_count,
                "total_drivers": len(all_drivers)
            }
            
            logger.info(f"Driver history initialization completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error during driver history initialization: {str(e)}")
            raise
    
    async def get_driver_statistics(self, driver_id: str) -> Dict[str, Any]:
        """
        Get comprehensive driver statistics
        
        Args:
            driver_id: ID of the driver
            
        Returns:
            Dictionary with driver statistics
        """
        try:
            history = await self.get_driver_history(driver_id)
            
            if not history:
                return {"error": "Driver history not found"}
            
            return {
                "driver_id": driver_id,
                "driver_name": history.driver_name,
                "employee_id": history.employee_id,
                "trip_statistics": {
                    "total_assigned": history.total_assigned_trips,
                    "completed": history.completed_trips,
                    "cancelled": history.cancelled_trips,
                    "completion_rate": history.trip_completion_rate
                },
                "violation_statistics": {
                    "braking": history.braking_violations,
                    "acceleration": history.acceleration_violations,
                    "phone_usage": history.phone_usage_violations,
                    "speeding": history.speeding_violations,
                    "total": self._get_total_violations(history)
                },
                "safety_metrics": {
                    "safety_score": history.driver_safety_score,
                    "risk_level": history.driver_risk_level.value
                },
                "last_updated": history.last_updated.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting driver statistics for {driver_id}: {str(e)}")
            raise
    
    async def recalculate_all_driver_histories(self) -> Dict[str, Any]:
        """
        Recalculate all driver histories from scratch
        This is useful for data migration or fixing inconsistencies
        
        Returns:
            Summary of recalculation results
        """
        try:
            # Get all unique driver IDs from trips - check both possible field names
            trips_collection = self.db_manager.trips
            
            # Get driver IDs from both possible fields
            driver_ids_assignment = await trips_collection.distinct("driver_assignment")
            driver_ids_direct = await trips_collection.distinct("driver_id")
            
            # Combine and remove None values
            all_driver_ids = set()
            all_driver_ids.update([d for d in driver_ids_assignment if d])
            all_driver_ids.update([d for d in driver_ids_direct if d])
            
            driver_ids = list(all_driver_ids)
            
            updated_count = 0
            errors = []
            
            for driver_id in driver_ids:
                try:
                    await self._recalculate_driver_history(driver_id)
                    updated_count += 1
                except Exception as e:
                    errors.append(f"Error updating {driver_id}: {str(e)}")
                    logger.error(f"Error recalculating history for driver {driver_id}: {str(e)}")
            
            return {
                "updated_drivers": updated_count,
                "total_drivers": len(driver_ids),
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Error recalculating all driver histories: {str(e)}")
            raise
    
    async def _get_or_create_driver_history(self, driver_id: str) -> DriverHistory:
        """Get existing driver history or create a new one"""
        history = await self.get_driver_history(driver_id)
        
        if not history:
            # Get driver info from the drivers collection
            driver_info = await self._get_driver_info(driver_id)
            
            history = DriverHistory(
                driver_id=driver_id,
                driver_name=driver_info.get("full_name", "Unknown Driver"),
                employee_id=driver_info.get("employee_id", None),
                total_assigned_trips=await self._count_assigned_trips(driver_id),
            )
        
        return history
    
    async def _get_driver_info(self, driver_id: str) -> Dict[str, Any]:
        """Get driver information from management database drivers collection"""
        try:
            # First try to get driver info from management database
            if self.db_manager_management:
                drivers_collection = self.db_manager_management.drivers
                # Query by employee_id matching the driver_id
                driver = await drivers_collection.find_one({"employee_id": driver_id})
                
                if driver:
                    # Construct full name from first_name and last_name
                    first_name = driver.get("first_name", "")
                    last_name = driver.get("last_name", "")
                    full_name = f"{first_name} {last_name}".strip()
                    
                    # If both names are empty, use a default
                    if not full_name:
                        full_name = "Unknown Driver"
                    
                    return {
                        "full_name": full_name,
                        "employee_id": driver.get("employee_id"),
                        "first_name": first_name,
                        "last_name": last_name,
                        "_id": driver.get("_id")
                    }
            
            # Fallback to trip planning database if management DB is not available
            drivers_collection = self.db_manager.drivers
            driver = await drivers_collection.find_one({"_id": driver_id})
            
            if driver:
                # Try to construct name from available fields
                first_name = driver.get("first_name", "")
                last_name = driver.get("last_name", "")
                full_name = driver.get("full_name", "")
                
                if not full_name and (first_name or last_name):
                    full_name = f"{first_name} {last_name}".strip()
                
                if not full_name:
                    full_name = "Unknown Driver"
                
                return {
                    "full_name": full_name,
                    "employee_id": driver.get("employee_id"),
                    "first_name": first_name,
                    "last_name": last_name,
                    "_id": driver.get("_id")
                }
            
            return {"full_name": "Unknown Driver", "employee_id": None}
            
        except Exception as e:
            logger.error(f"Error getting driver info for {driver_id}: {str(e)}")
            return {"full_name": "Unknown Driver", "employee_id": None}
    
    async def _count_assigned_trips(self, driver_id: str) -> int:
        """Count total assigned trips for a driver"""
        try:
            trips_collection = self.db_manager.trips
            return await trips_collection.count_documents({"driver_id": driver_id})
        except Exception:
            return 0
    
    async def _update_violation_counts(self, history: DriverHistory, driver_id: str):
        """Update violation counts from violation collections"""
        try:
            # Count speeding violations
            speed_violations = self.db_manager.speed_violations
            history.speeding_violations = await speed_violations.count_documents({"driver_id": driver_id})
            
            # Count braking violations
            braking_violations = self.db_manager.excessive_braking_violations
            history.braking_violations = await braking_violations.count_documents({"driver_id": driver_id})
            
            # Count acceleration violations
            acceleration_violations = self.db_manager.excessive_acceleration_violations
            history.acceleration_violations = await acceleration_violations.count_documents({"driver_id": driver_id})
            
            # Count phone usage violations (from driver ping violations)
            phone_violations = self.db_manager.driver_ping_violations
            history.phone_usage_violations = await phone_violations.count_documents({"driver_id": driver_id})
            
        except Exception as e:
            logger.error(f"Error updating violation counts for {driver_id}: {str(e)}")
    
    async def _calculate_safety_score(self, history: DriverHistory) -> float:
        """
        Calculate driver safety score based on various factors
        Score ranges from 0-100, with 100 being the safest
        """
        try:
            base_score = 100.0
            
            # Deduct points for trip completion rate
            completion_penalty = max(0, (100 - history.trip_completion_rate) * 0.3)
            
            # Deduct points for violations
            total_violations = self._get_total_violations(history)
            
            # Calculate violations per trip if there are completed trips
            if history.completed_trips > 0:
                violations_per_trip = total_violations / history.completed_trips
                violation_penalty = min(50, violations_per_trip * 10)  # Max 50 points deduction
            else:
                violation_penalty = 0
            
            # Calculate final score
            final_score = base_score - completion_penalty - violation_penalty
            
            # Ensure score is between 0 and 100
            return max(0, min(100, final_score))
            
        except Exception:
            return 50.0  # Default moderate score if calculation fails
    
    def _determine_risk_level(self, history: DriverHistory) -> RiskLevel:
        """Determine driver risk level based on safety score and violations"""
        try:
            total_violations = self._get_total_violations(history)
            
            # High risk conditions
            if (history.driver_safety_score < 60 or 
                total_violations > 10 or 
                history.trip_completion_rate < 80):
                return RiskLevel.HIGH
            
            # Medium risk conditions  
            if (history.driver_safety_score < 80 or 
                total_violations > 5 or 
                history.trip_completion_rate < 90):
                return RiskLevel.MEDIUM
            
            # Low risk (default)
            return RiskLevel.LOW
            
        except Exception:
            return RiskLevel.MEDIUM  # Default to medium if calculation fails
    
    def _get_total_violations(self, history: DriverHistory) -> int:
        """Calculate total violations across all categories"""
        return (history.speeding_violations + 
                history.braking_violations + 
                history.acceleration_violations + 
                history.phone_usage_violations)
    
    async def _save_driver_history(self, history: DriverHistory):
        """Save driver history to database"""
        try:
            collection = self.db_manager.driver_history
            history_dict = history.model_dump(by_alias=True, exclude_none=True)
            
            # Use upsert to update existing or create new
            await collection.replace_one(
                {"driver_id": history.driver_id},
                history_dict,
                upsert=True
            )
            
        except Exception as e:
            logger.error(f"Error saving driver history: {str(e)}")
            raise
    
    async def _recalculate_driver_history(self, driver_id: str):
        """Recalculate a single driver's history from scratch"""
        try:
            # Get driver info
            driver_info = await self._get_driver_info(driver_id)
            
            # Count trips by status - use $or to check both field names
            trips_collection = self.db_manager.trips
            driver_query = {
                "$or": [
                    {"driver_assignment": driver_id},
                    {"driver_id": driver_id}
                ]
            }
            
            total_assigned = await trips_collection.count_documents(driver_query)
            completed = await trips_collection.count_documents({
                **driver_query,
                "status": "completed"
            })
            cancelled = await trips_collection.count_documents({
                **driver_query,
                "status": "cancelled"
            })
            
            # Create new history record
            history = DriverHistory(
                driver_id=driver_id,
                driver_name=driver_info.get("full_name", "Unknown Driver"),
                employee_id=driver_info.get("employee_id", None),
                total_assigned_trips=total_assigned,
                completed_trips=completed,
                cancelled_trips=cancelled
            )
            
            # Calculate completion rate
            total_finished = completed + cancelled
            if total_finished > 0:
                history.trip_completion_rate = (completed / total_finished) * 100
            
            # Update violations
            await self._update_violation_counts(history, driver_id)
            
            # Calculate safety metrics
            history.driver_safety_score = await self._calculate_safety_score(history)
            history.driver_risk_level = self._determine_risk_level(history)
            
            # Save to database
            await self._save_driver_history(history)
            
        except Exception as e:
            logger.error(f"Error recalculating driver history for {driver_id}: {str(e)}")
            raise
    
    async def get_trip_violation_counts(self, trip_id: str) -> Dict[str, int]:
        """
        Get violation counts for a specific trip
        
        Args:
            trip_id: ID of the trip
            
        Returns:
            Dictionary with violation counts by type
        """
        try:
            violation_counts = {
                "speeding": 0,
                "braking": 0,
                "acceleration": 0,
                "phone_usage": 0
            }
            
            # Count speeding violations for this trip
            speed_violations = self.db_manager.speed_violations
            violation_counts["speeding"] = await speed_violations.count_documents({"trip_id": trip_id})
            
            # Count braking violations for this trip
            braking_violations = self.db_manager.excessive_braking_violations
            violation_counts["braking"] = await braking_violations.count_documents({"trip_id": trip_id})
            
            # Count acceleration violations for this trip
            acceleration_violations = self.db_manager.excessive_acceleration_violations
            violation_counts["acceleration"] = await acceleration_violations.count_documents({"trip_id": trip_id})
            
            # Count phone usage violations for this trip
            phone_violations = self.db_manager.driver_ping_violations
            violation_counts["phone_usage"] = await phone_violations.count_documents({"trip_id": trip_id})
            
            return violation_counts
            
        except Exception as e:
            logger.error(f"Error getting violation counts for trip {trip_id}: {str(e)}")
            # Return zeros on error to avoid breaking the response
            return {
                "speeding": 0,
                "braking": 0,
                "acceleration": 0,
                "phone_usage": 0
            }