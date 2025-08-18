"""
Vehicle management service with enhanced business logic
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from repositories.repositories import VehicleRepository, VehicleAssignmentRepository
from events.publisher import event_publisher
from schemas.requests import VehicleCreateRequest, VehicleUpdateRequest

logger = logging.getLogger(__name__)


class VehicleService:
    """Service for vehicle management business logic"""
    
    def __init__(self):
        self.vehicle_repo = VehicleRepository()
        self.assignment_repo = VehicleAssignmentRepository()
    
    async def get_vehicles(
        self, 
        department: Optional[str] = None,
        status: Optional[str] = None, 
        vehicle_type: Optional[str] = None,
        pagination: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Get vehicles with optional filters"""
        try:
            # Build filter query
            filter_query = {}
            if department:
                filter_query["department"] = department
            if status:
                filter_query["status"] = status
            if vehicle_type:
                filter_query["type"] = vehicle_type
            
            # Default pagination if not provided
            if not pagination:
                pagination = {"skip": 0, "limit": 50}
            
            # Get vehicles
            vehicles = await self.vehicle_repo.find(
                filter_query=filter_query,
                skip=pagination["skip"],
                limit=pagination["limit"],
                sort=[("registration_number", 1)]
            )
            
            # Convert datetime objects to ISO format for JSON serialization
            if vehicles:
                for vehicle in vehicles:
                    if isinstance(vehicle, dict):
                        for key, value in vehicle.items():
                            if isinstance(value, datetime):
                                vehicle[key] = value.isoformat()
            
            # Get total count
            total = await self.vehicle_repo.count(filter_query)
            total_pages = (total + pagination["limit"] - 1) // pagination["limit"]
            
            return {
                "vehicles": vehicles,
                "pagination": {
                    "total": total,
                    "page": pagination["skip"] // pagination["limit"] + 1,
                    "page_size": pagination["limit"],
                    "total_pages": total_pages
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting vehicles: {e}")
            raise


    async def get_num_vehicles(self, 
        department: Optional[str] = None,
        status: Optional[str] = None, 
        vehicle_type: Optional[str] = None,
        pagination: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        response = await self.get_vehicles(department, status, vehicle_type, pagination)
        total_vehicles = len(response["vehicles"])

        return {
            "Total vehicles": total_vehicles,
        }
    

    async def create_vehicle(self, vehicle_request: VehicleCreateRequest, created_by: str) -> Dict[str, Any]:
        """Create new vehicle with validation"""
        try:
            # Determine the registration number (use license_plate if registration_number not provided)
            reg_number = vehicle_request.registration_number or vehicle_request.license_plate
            if not reg_number:
                raise ValueError("Either registration_number or license_plate must be provided")
            
            # Check if registration number already exists
            existing = await self.vehicle_repo.get_by_registration_number(reg_number)
            if existing:
                raise ValueError(f"Vehicle with registration number {reg_number} already exists")
            
            # Convert to dict and add metadata
            vehicle_data = vehicle_request.model_dump()
            
            # Ensure registration_number is set
            vehicle_data["registration_number"] = reg_number
            if not vehicle_data.get("license_plate"):
                vehicle_data["license_plate"] = reg_number
                
            vehicle_data["created_by"] = created_by
            vehicle_data["created_at"] = datetime.utcnow()
            vehicle_data["updated_at"] = datetime.utcnow()
            
            # Set default status if not provided
            if "status" not in vehicle_data:
                vehicle_data["status"] = "available"
            
            # Create vehicle
            vehicle_id = await self.vehicle_repo.create(vehicle_data)
            vehicle = await self.vehicle_repo.get_by_id(vehicle_id)
            
            # Publish event
            await event_publisher.publish_vehicle_created(vehicle, created_by)
            
            # Convert datetime objects to ISO format for JSON serialization
            if vehicle and isinstance(vehicle, dict):
                for key, value in vehicle.items():
                    if isinstance(value, datetime):
                        vehicle[key] = value.isoformat()
            
            logger.info(f"Created vehicle: {vehicle_id}")
            return vehicle
            
        except ValueError as e:
            logger.warning(f"Vehicle creation validation error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error creating vehicle: {e}")
            raise
    
    async def get_vehicle_by_id(self, vehicle_id: str) -> Optional[Dict[str, Any]]:
        """Get vehicle by ID"""
        try:
            vehicle = await self.vehicle_repo.get_by_id(vehicle_id)
            return vehicle
        except Exception as e:
            logger.error(f"Error getting vehicle {vehicle_id}: {e}")
            raise
    
    async def update_vehicle(self, vehicle_id: str, updates: VehicleUpdateRequest, updated_by: str) -> Dict[str, Any]:
        """Update vehicle with validation"""
        try:
            # Check if vehicle exists
            existing_vehicle = await self.vehicle_repo.get_by_id(vehicle_id)
            if not existing_vehicle:
                raise ValueError("Vehicle not found")
            
            # Convert updates to dict, excluding None values
            update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
            
            # Validate unique fields if being updated
            if "registration_number" in update_data:
                existing_reg = await self.vehicle_repo.get_by_registration_number(update_data["registration_number"])
                if existing_reg and existing_reg["_id"] != vehicle_id:
                    raise ValueError(f"Registration number {update_data['registration_number']} already in use")
            
            # Add metadata
            update_data["updated_by"] = updated_by
            update_data["updated_at"] = datetime.utcnow()
            
            # Track changes for event
            changes = {}
            for key, new_value in update_data.items():
                if key in existing_vehicle and existing_vehicle[key] != new_value:
                    changes[key] = {
                        "old": existing_vehicle[key],
                        "new": new_value
                    }
            
            # Update vehicle
            success = await self.vehicle_repo.update(vehicle_id, update_data)
            if not success:
                raise ValueError("Failed to update vehicle")
            
            # Get updated vehicle
            updated_vehicle = await self.vehicle_repo.get_by_id(vehicle_id)
            
            # Publish event if there were meaningful changes
            if changes:
                await event_publisher.publish_vehicle_updated(
                    updated_vehicle, 
                    updated_by, 
                    changes=changes
                )
            
            logger.info(f"Updated vehicle: {vehicle_id}")
            return updated_vehicle
            
        except ValueError as e:
            logger.warning(f"Vehicle update validation error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error updating vehicle {vehicle_id}: {e}")
            raise
    
    async def delete_vehicle(self, vehicle_id: str, deleted_by: str) -> bool:
        """Delete vehicle with proper cleanup"""
        try:
            # Check if vehicle exists
            existing_vehicle = await self.vehicle_repo.get_by_id(vehicle_id)
            if not existing_vehicle:
                raise ValueError(f"Vehicle with ID {vehicle_id} not found")
            
            # Check for active assignments
            active_assignments = await self.assignment_repo.get_by_vehicle_id(vehicle_id, status="active")
            if active_assignments:
                raise ValueError("Cannot delete vehicle with active assignments")
            
            # Delete vehicle
            success = await self.vehicle_repo.delete(vehicle_id)
            if not success:
                return False
            
            # Publish event
            await event_publisher.publish_vehicle_deleted(existing_vehicle, deleted_by)
            
            logger.info(f"Deleted vehicle: {vehicle_id}")
            return True
            
        except ValueError as e:
            logger.warning(f"Vehicle deletion validation error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error deleting vehicle {vehicle_id}: {e}")
            raise
    
    async def search_vehicles(self, query: str, pagination: Dict[str, Any] = None) -> Dict[str, Any]:
        """Search vehicles by various criteria"""
        try:
            # Default pagination if not provided
            if not pagination:
                pagination = {"skip": 0, "limit": 50}
            
            # Build search filter
            search_filter = {
                "$or": [
                    {"registration_number": {"$regex": query, "$options": "i"}},
                    {"make": {"$regex": query, "$options": "i"}},
                    {"model": {"$regex": query, "$options": "i"}},
                    {"department": {"$regex": query, "$options": "i"}},
                    {"type": {"$regex": query, "$options": "i"}}
                ]
            }
            
            # Get vehicles
            vehicles = await self.vehicle_repo.find(
                filter_query=search_filter,
                skip=pagination["skip"],
                limit=pagination["limit"],
                sort=[("registration_number", 1)]
            )
            
            # Get total count
            total = await self.vehicle_repo.count(search_filter)
            total_pages = (total + pagination["limit"] - 1) // pagination["limit"]
            
            return {
                "vehicles": vehicles,
                "query": query,
                "pagination": {
                    "total": total,
                    "page": pagination["skip"] // pagination["limit"] + 1,
                    "page_size": pagination["limit"],
                    "total_pages": total_pages
                }
            }
            
        except Exception as e:
            logger.error(f"Error searching vehicles: {e}")
            raise
    
    async def get_vehicle_assignments(self, vehicle_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get assignments for a specific vehicle"""
        try:
            assignments = await self.assignment_repo.get_by_vehicle_id(vehicle_id, status=status)
            return assignments
        except Exception as e:
            logger.error(f"Error getting vehicle assignments for {vehicle_id}: {e}")
            raise
    
    async def get_vehicle_usage_stats(
        self, 
        vehicle_id: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get usage statistics for a specific vehicle"""
        try:
            # This would integrate with VehicleUsageLogRepository
            # For now, return basic structure
            from repositories.repositories import VehicleUsageLogRepository
            usage_repo = VehicleUsageLogRepository()
            
            # Build date filter
            date_filter = {"vehicle_id": vehicle_id}
            if start_date or end_date:
                date_range = {}
                if start_date:
                    date_range["$gte"] = datetime.fromisoformat(start_date)
                if end_date:
                    date_range["$lte"] = datetime.fromisoformat(end_date)
                date_filter["created_at"] = date_range
            
            # Get usage logs
            usage_logs = await usage_repo.find(
                filter_query=date_filter,
                sort=[("created_at", -1)]
            )
            
            # Calculate statistics
            total_distance = sum(log.get("distance", 0) for log in usage_logs)
            total_fuel = sum(log.get("fuel_consumed", 0) for log in usage_logs)
            trip_count = len(usage_logs)
            
            avg_distance_per_trip = total_distance / trip_count if trip_count > 0 else 0
            fuel_efficiency = total_distance / total_fuel if total_fuel > 0 else 0
            
            return {
                "vehicle_id": vehicle_id,
                "total_distance": total_distance,
                "total_fuel": total_fuel,
                "trip_count": trip_count,
                "avg_distance_per_trip": round(avg_distance_per_trip, 2),
                "fuel_efficiency": round(fuel_efficiency, 2),
                "usage_logs": usage_logs[:10],  # Return last 10 logs
                "date_range": {
                    "start_date": start_date,
                    "end_date": end_date
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting vehicle usage stats for {vehicle_id}: {e}")
            raise

    async def handle_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle vehicle-related requests from request consumer"""
        try:
            from schemas.requests import VehicleCreateRequest, VehicleUpdateRequest
            from schemas.responses import ResponseBuilder
            
            # Extract data and endpoint from user_context
            data = user_context.get("data", {})
            endpoint = user_context.get("endpoint", "")
            
            # Create mock user for service calls
            current_user = {"user_id": user_context.get("user_id", "system")}
            
            # Handle HTTP methods and route to appropriate logic
            if method == "GET":
                # Parse endpoint for specific vehicle operations
                if "search" in endpoint:
                    query = data.get("query", "")
                    vehicles = await self.search_vehicles(query)
                elif endpoint.count('/') > 0 and endpoint.split('/')[-1] and endpoint.split('/')[-1] != "vehicles":
                    # vehicles/{id} pattern
                    vehicle_id = endpoint.split('/')[-1]
                    vehicles = await self.get_vehicle_by_id(vehicle_id)

                elif "vehicles-total" in endpoint or "vehicles_total" in endpoint:
                    usage_data = await self.get_num_vehicles(
                        department=data.get("department"),
                        status=data.get("status"),
                        vehicle_type=data.get("vehicle_type"),
                        pagination=data.get("pagination", {"skip": 0, "limit": 50})
                    )
                    return ResponseBuilder.success(
                        data=usage_data,
                        message="Total vehicles data retrieved successfully penis"
                    ).model_dump()

                else:
                    # Get all vehicles with optional filters
                    department = data.get("department")
                    status = data.get("status") 
                    vehicle_type = data.get("vehicle_type")
                    pagination = data.get("pagination", {"skip": 0, "limit": 50})
                    
                    vehicles = await self.get_vehicles(
                        department=department,
                        status=status,
                        vehicle_type=vehicle_type,
                        pagination=pagination
                    )
                
                # Transform _id to id for frontend compatibility
                vehicles = self._transform_vehicle_data(vehicles)
                
                return ResponseBuilder.success(
                    data=vehicles,
                    message="Vehicles retrieved successfully"
                ).model_dump()
                
            elif method == "POST":
                if not data:
                    raise ValueError("Request data is required for POST operation")
                
                if "assign-driver" in endpoint:
                    logger.info(f"Data received for driver assignment: {data} ")
                else:
                    # Create vehicle
                    vehicle_request = VehicleCreateRequest(**data)
                    created_by = current_user["user_id"]
                    result = await self.create_vehicle(vehicle_request, created_by)
                    
                    # Transform _id to id for frontend compatibility
                    result = self._transform_vehicle_data(result)
                    
                    return ResponseBuilder.success(
                        data=result,
                        message="Vehicle created successfully"
                    ).model_dump()

                
                
            elif method == "PUT":
                vehicle_id = endpoint.split('/')[-1] if '/' in endpoint else None
                if not vehicle_id:
                    raise ValueError("Vehicle ID is required for PUT operation")
                if not data:
                    raise ValueError("Request data is required for PUT operation")
                
                # Update vehicle
                vehicle_update_request = VehicleUpdateRequest(**data)
                updated_by = current_user["user_id"]
                result = await self.update_vehicle(vehicle_id, vehicle_update_request, updated_by)
                
                # Transform _id to id for frontend compatibility
                result = self._transform_vehicle_data(result)
                
                return ResponseBuilder.success(
                    data=result,
                    message="Vehicle updated successfully"
                ).model_dump()
                
            elif method == "DELETE":
                vehicle_id = endpoint.split('/')[-1] if '/' in endpoint else None
                if not vehicle_id:
                    raise ValueError("Vehicle ID is required for DELETE operation")
                
                # Delete vehicle
                deleted_by = current_user["user_id"]
                result = await self.delete_vehicle(vehicle_id, deleted_by)
                
                return ResponseBuilder.success(
                    data=result,
                    message="Vehicle deleted successfully"
                ).model_dump()
                
            else:
                raise ValueError(f"Unsupported HTTP method for vehicles: {method}")
                
        except Exception as e:
            from schemas.responses import ResponseBuilder
            logger.error(f"Error handling vehicles request {method} {endpoint}: {e}")
            return ResponseBuilder.error(
                error="VehicleRequestError",
                message=f"Failed to process vehicle request: {str(e)}"
            ).model_dump()

    def _transform_vehicle_data(self, data):
        """Transform vehicle data to convert _id to id for frontend compatibility"""
        if data is None:
            return data
        
        def transform_single_vehicle(vehicle):
            """Transform a single vehicle object"""
            if isinstance(vehicle, dict) and "_id" in vehicle:
                # Create new dict with id field
                transformed = vehicle.copy()
                transformed["id"] = transformed.pop("_id")
                return transformed
            return vehicle
        
        if isinstance(data, dict):
            # Check if it's a vehicle list response
            if "vehicles" in data and isinstance(data["vehicles"], list):
                # Transform list of vehicles
                data["vehicles"] = [transform_single_vehicle(v) for v in data["vehicles"]]
                return data
            else:
                # Single vehicle response
                return transform_single_vehicle(data)
        elif isinstance(data, list):
            # Direct list of vehicles
            return [transform_single_vehicle(v) for v in data]
        
        return data


# Global service instance
vehicle_service = VehicleService()
