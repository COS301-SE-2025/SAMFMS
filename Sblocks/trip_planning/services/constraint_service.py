"""
Constraint service for managing trip routing constraints
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId

from repositories.database import db_manager
from schemas.entities import TripConstraint, ConstraintType
from schemas.requests import CreateConstraintRequest, UpdateConstraintRequest

logger = logging.getLogger(__name__)


class ConstraintService:
    """Service for managing trip routing constraints"""
    
    def __init__(self):
        self.db = db_manager
        
    async def add_constraint_to_trip(
        self,
        trip_id: str,
        request: CreateConstraintRequest
    ) -> TripConstraint:
        """Add a routing constraint to a trip"""
        try:
            # Verify trip exists
            trip_doc = await self.db.trips.find_one({"_id": ObjectId(trip_id)})
            if not trip_doc:
                raise ValueError("Trip not found")
            
            # Validate constraint value based on type
            self._validate_constraint_value(request.type, request.value)
            
            # Create constraint
            constraint_data = {
                "trip_id": trip_id,
                "type": request.type,
                "value": request.value,
                "priority": request.priority,
                "is_active": True,
                "created_at": datetime.utcnow()
            }
            
            # Insert into database
            result = await self.db.trip_constraints.insert_one(constraint_data)
            
            # Create constraint object
            constraint_data["_id"] = str(result.inserted_id)
            constraint = TripConstraint(**constraint_data)
            
            # Update trip document to include constraint
            await self.db.trips.update_one(
                {"_id": ObjectId(trip_id)},
                {
                    "$push": {"constraints": constraint_data},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            logger.info(f"Added constraint {constraint.id} to trip {trip_id}")
            return constraint
            
        except Exception as e:
            logger.error(f"Failed to add constraint to trip {trip_id}: {e}")
            raise
    
    async def get_trip_constraints(self, trip_id: str) -> List[TripConstraint]:
        """Get all constraints for a trip"""
        try:
            constraints = []
            async for constraint_doc in self.db.trip_constraints.find({"trip_id": trip_id}):
                constraint_doc["_id"] = str(constraint_doc["_id"])
                constraints.append(TripConstraint(**constraint_doc))
            
            return constraints
            
        except Exception as e:
            logger.error(f"Failed to get constraints for trip {trip_id}: {e}")
            raise
    
    async def get_constraint_by_id(self, constraint_id: str) -> Optional[TripConstraint]:
        """Get a specific constraint by ID"""
        try:
            constraint_doc = await self.db.trip_constraints.find_one({"_id": ObjectId(constraint_id)})
            if constraint_doc:
                constraint_doc["_id"] = str(constraint_doc["_id"])
                return TripConstraint(**constraint_doc)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get constraint {constraint_id}: {e}")
            raise
    
    async def update_constraint(
        self,
        constraint_id: str,
        request: UpdateConstraintRequest
    ) -> Optional[TripConstraint]:
        """Update a trip constraint"""
        try:
            # Get existing constraint
            existing_constraint = await self.get_constraint_by_id(constraint_id)
            if not existing_constraint:
                return None
            
            # Prepare update data
            update_data = request.dict(exclude_unset=True)
            
            # Validate constraint value if provided
            if "value" in update_data:
                self._validate_constraint_value(existing_constraint.type, update_data["value"])
            
            # Update constraint
            result = await self.db.trip_constraints.update_one(
                {"_id": ObjectId(constraint_id)},
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                return None
            
            # Update trip document
            await self._update_trip_constraints(existing_constraint.trip_id)
            
            # Get updated constraint
            updated_constraint = await self.get_constraint_by_id(constraint_id)
            
            logger.info(f"Updated constraint {constraint_id}")
            return updated_constraint
            
        except Exception as e:
            logger.error(f"Failed to update constraint {constraint_id}: {e}")
            raise
    
    async def remove_constraint(self, constraint_id: str) -> bool:
        """Remove a constraint from a trip"""
        try:
            # Get constraint before deletion
            constraint = await self.get_constraint_by_id(constraint_id)
            if not constraint:
                return False
            
            # Delete constraint
            result = await self.db.trip_constraints.delete_one({"_id": ObjectId(constraint_id)})
            
            if result.deleted_count == 0:
                return False
            
            # Update trip document
            await self._update_trip_constraints(constraint.trip_id)
            
            logger.info(f"Removed constraint {constraint_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove constraint {constraint_id}: {e}")
            raise
    
    async def get_active_constraints_for_trip(self, trip_id: str) -> List[TripConstraint]:
        """Get only active constraints for a trip"""
        try:
            constraints = []
            async for constraint_doc in self.db.trip_constraints.find({
                "trip_id": trip_id,
                "is_active": True
            }).sort("priority", -1):  # Sort by priority (highest first)
                constraint_doc["_id"] = str(constraint_doc["_id"])
                constraints.append(TripConstraint(**constraint_doc))
            
            return constraints
            
        except Exception as e:
            logger.error(f"Failed to get active constraints for trip {trip_id}: {e}")
            raise
    
    async def apply_constraints_to_route(
        self,
        trip_id: str,
        route_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply constraints to route calculation"""
        try:
            constraints = await self.get_active_constraints_for_trip(trip_id)
            
            # Start with base route data
            optimized_route = route_data.copy()
            
            # Apply each constraint in priority order
            for constraint in constraints:
                optimized_route = self._apply_single_constraint(constraint, optimized_route)
            
            return optimized_route
            
        except Exception as e:
            logger.error(f"Failed to apply constraints to route for trip {trip_id}: {e}")
            raise
    
    def _validate_constraint_value(self, constraint_type: ConstraintType, value: Optional[Dict[str, Any]]):
        """Validate constraint value based on type"""
        if constraint_type == ConstraintType.AVOID_AREA and value:
            required_fields = ["center", "radius"]
            if not all(field in value for field in required_fields):
                raise ValueError(f"AVOID_AREA constraint requires {required_fields}")
            
            if not isinstance(value["center"], dict) or "coordinates" not in value["center"]:
                raise ValueError("AVOID_AREA center must be a valid location point")
            
            if not isinstance(value["radius"], (int, float)) or value["radius"] <= 0:
                raise ValueError("AVOID_AREA radius must be a positive number")
        
        elif constraint_type == ConstraintType.PREFERRED_ROUTE and value:
            if "waypoints" not in value or not isinstance(value["waypoints"], list):
                raise ValueError("PREFERRED_ROUTE constraint requires waypoints list")
    
    def _apply_single_constraint(
        self,
        constraint: TripConstraint,
        route_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply a single constraint to route data"""
        try:
            if constraint.type == ConstraintType.AVOID_TOLLS:
                route_data["avoid_tolls"] = True
            
            elif constraint.type == ConstraintType.AVOID_HIGHWAYS:
                route_data["avoid_highways"] = True
            
            elif constraint.type == ConstraintType.AVOID_FERRIES:
                route_data["avoid_ferries"] = True
            
            elif constraint.type == ConstraintType.SHORTEST_ROUTE:
                route_data["optimization"] = "distance"
            
            elif constraint.type == ConstraintType.FASTEST_ROUTE:
                route_data["optimization"] = "time"
            
            elif constraint.type == ConstraintType.FUEL_EFFICIENT:
                route_data["optimization"] = "fuel"
            
            elif constraint.type == ConstraintType.AVOID_AREA and constraint.value:
                if "avoid_areas" not in route_data:
                    route_data["avoid_areas"] = []
                route_data["avoid_areas"].append(constraint.value)
            
            elif constraint.type == ConstraintType.PREFERRED_ROUTE and constraint.value:
                if "preferred_waypoints" not in route_data:
                    route_data["preferred_waypoints"] = []
                route_data["preferred_waypoints"].extend(constraint.value.get("waypoints", []))
            
            return route_data
            
        except Exception as e:
            logger.error(f"Failed to apply constraint {constraint.id}: {e}")
            return route_data
    
    async def _update_trip_constraints(self, trip_id: str):
        """Update the constraints array in the trip document"""
        try:
            # Get all constraints for the trip
            constraints = await self.get_trip_constraints(trip_id)
            
            # Convert to dict format
            constraint_dicts = [constraint.dict() for constraint in constraints]
            
            # Update trip document
            await self.db.trips.update_one(
                {"_id": ObjectId(trip_id)},
                {
                    "$set": {
                        "constraints": constraint_dicts,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to update trip constraints for trip {trip_id}: {e}")
    
    async def get_constraint_templates(self) -> List[Dict[str, Any]]:
        """Get predefined constraint templates"""
        templates = [
            {
                "name": "Avoid Toll Roads",
                "type": ConstraintType.AVOID_TOLLS,
                "description": "Route will avoid toll roads when possible",
                "value": None,
                "priority": 5
            },
            {
                "name": "Highway Free Route",
                "type": ConstraintType.AVOID_HIGHWAYS,
                "description": "Route will use local roads instead of highways",
                "value": None,
                "priority": 3
            },
            {
                "name": "Fastest Route",
                "type": ConstraintType.FASTEST_ROUTE,
                "description": "Optimize for minimum travel time",
                "value": None,
                "priority": 7
            },
            {
                "name": "Shortest Distance",
                "type": ConstraintType.SHORTEST_ROUTE,
                "description": "Optimize for minimum distance",
                "value": None,
                "priority": 6
            },
            {
                "name": "Fuel Efficient",
                "type": ConstraintType.FUEL_EFFICIENT,
                "description": "Optimize for fuel consumption",
                "value": None,
                "priority": 4
            },
            {
                "name": "Avoid Ferries",
                "type": ConstraintType.AVOID_FERRIES,
                "description": "Route will avoid ferry crossings",
                "value": None,
                "priority": 2
            }
        ]
        
        return templates


# Global instance
constraint_service = ConstraintService()
