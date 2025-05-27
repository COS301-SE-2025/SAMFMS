from typing import List, Optional, Dict, Any
from bson import ObjectId
from datetime import datetime, timedelta
from ..models.models import Vehicle, VehicleStatus, VehicleType, MaintenanceRecord
from ..database import get_vehicles_collection, get_maintenance_collection
from ..messaging.rabbitmq_client import RabbitMQClient


class VehicleService:
    def __init__(self, messaging_client: RabbitMQClient):
        self.messaging_client = messaging_client
        self.vehicles_collection = get_vehicles_collection()
        self.maintenance_collection = get_maintenance_collection()

    async def create_vehicle(self, vehicle_data: Dict[str, Any]) -> Vehicle:
        """Create a new vehicle"""
        vehicle = Vehicle(**vehicle_data)
        
        # Insert into database
        result = await self.vehicles_collection.insert_one(vehicle.dict(by_alias=True))
        vehicle.id = result.inserted_id
        
        # Publish vehicle created event
        await self.messaging_client.publish_event(
            "vehicle.created",
            {
                "vehicle_id": str(vehicle.id),
                "license_plate": vehicle.license_plate,
                "vehicle_type": vehicle.vehicle_type.value,
                "status": vehicle.status.value,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return vehicle

    async def get_vehicle_by_id(self, vehicle_id: str) -> Optional[Vehicle]:
        """Get vehicle by ID"""
        vehicle_data = await self.vehicles_collection.find_one(
            {"_id": ObjectId(vehicle_id)}
        )
        return Vehicle(**vehicle_data) if vehicle_data else None

    async def get_vehicles(
        self, 
        status: Optional[VehicleStatus] = None,
        vehicle_type: Optional[VehicleType] = None,
        available_only: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[Vehicle]:
        """Get vehicles with optional filters"""
        query = {}
        
        if status:
            query["status"] = status.value
        if vehicle_type:
            query["vehicle_type"] = vehicle_type.value
        if available_only:
            query["status"] = VehicleStatus.AVAILABLE.value
            
        cursor = self.vehicles_collection.find(query).skip(skip).limit(limit)
        vehicles = []
        
        async for vehicle_data in cursor:
            vehicles.append(Vehicle(**vehicle_data))
            
        return vehicles

    async def update_vehicle(self, vehicle_id: str, update_data: Dict[str, Any]) -> Optional[Vehicle]:
        """Update vehicle information"""
        update_data["updated_at"] = datetime.utcnow()
        
        result = await self.vehicles_collection.update_one(
            {"_id": ObjectId(vehicle_id)},
            {"$set": update_data}
        )
        
        if result.modified_count:
            updated_vehicle = await self.get_vehicle_by_id(vehicle_id)
            
            # Publish vehicle updated event
            await self.messaging_client.publish_event(
                "vehicle.updated",
                {
                    "vehicle_id": vehicle_id,
                    "updated_fields": list(update_data.keys()),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            return updated_vehicle
        return None

    async def update_vehicle_status(self, vehicle_id: str, status: VehicleStatus) -> bool:
        """Update vehicle status"""
        result = await self.vehicles_collection.update_one(
            {"_id": ObjectId(vehicle_id)},
            {
                "$set": {
                    "status": status.value,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count:
            # Publish status change event
            await self.messaging_client.publish_event(
                "vehicle.status_changed",
                {
                    "vehicle_id": vehicle_id,
                    "new_status": status.value,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            return True
        return False

    async def update_vehicle_location(
        self, 
        vehicle_id: str, 
        latitude: float, 
        longitude: float,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """Update vehicle's current location"""
        if not timestamp:
            timestamp = datetime.utcnow()
            
        location_data = {
            "current_location": {
                "latitude": latitude,
                "longitude": longitude,
                "timestamp": timestamp
            },
            "updated_at": timestamp
        }
        
        result = await self.vehicles_collection.update_one(
            {"_id": ObjectId(vehicle_id)},
            {"$set": location_data}
        )
        
        if result.modified_count:
            # Publish location update event
            await self.messaging_client.publish_event(
                "vehicle.location_updated",
                {
                    "vehicle_id": vehicle_id,
                    "latitude": latitude,
                    "longitude": longitude,
                    "timestamp": timestamp.isoformat()
                }
            )
            return True
        return False

    async def get_available_vehicles(
        self, 
        vehicle_type: Optional[VehicleType] = None,
        exclude_maintenance: bool = True
    ) -> List[Vehicle]:
        """Get all available vehicles for trip assignment"""
        query = {"status": VehicleStatus.AVAILABLE.value}
        
        if vehicle_type:
            query["vehicle_type"] = vehicle_type.value
            
        if exclude_maintenance:
            # Exclude vehicles due for maintenance
            maintenance_due_date = datetime.utcnow() + timedelta(days=7)
            query["next_maintenance_date"] = {"$gt": maintenance_due_date}
            
        cursor = self.vehicles_collection.find(query)
        vehicles = []
        
        async for vehicle_data in cursor:
            vehicles.append(Vehicle(**vehicle_data))
            
        return vehicles

    async def assign_vehicle_to_trip(self, vehicle_id: str, trip_id: str) -> bool:
        """Assign vehicle to a trip"""
        result = await self.vehicles_collection.update_one(
            {
                "_id": ObjectId(vehicle_id),
                "status": VehicleStatus.AVAILABLE.value
            },
            {
                "$set": {
                    "status": VehicleStatus.IN_USE.value,
                    "current_trip_id": trip_id,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count:
            await self.messaging_client.publish_event(
                "vehicle.assigned_to_trip",
                {
                    "vehicle_id": vehicle_id,
                    "trip_id": trip_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            return True
        return False

    async def release_vehicle_from_trip(self, vehicle_id: str) -> bool:
        """Release vehicle from trip assignment"""
        result = await self.vehicles_collection.update_one(
            {"_id": ObjectId(vehicle_id)},
            {
                "$set": {
                    "status": VehicleStatus.AVAILABLE.value,
                    "updated_at": datetime.utcnow()
                },
                "$unset": {
                    "current_trip_id": ""
                }
            }
        )
        
        if result.modified_count:
            await self.messaging_client.publish_event(
                "vehicle.released_from_trip",
                {
                    "vehicle_id": vehicle_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            return True
        return False

    async def add_maintenance_record(self, vehicle_id: str, maintenance_data: Dict[str, Any]) -> MaintenanceRecord:
        """Add maintenance record for vehicle"""
        maintenance_record = MaintenanceRecord(
            vehicle_id=ObjectId(vehicle_id),
            **maintenance_data
        )
        
        # Insert maintenance record
        result = await self.maintenance_collection.insert_one(
            maintenance_record.dict(by_alias=True)
        )
        maintenance_record.id = result.inserted_id
        
        # Update vehicle's last maintenance date
        await self.vehicles_collection.update_one(
            {"_id": ObjectId(vehicle_id)},
            {
                "$set": {
                    "last_maintenance_date": maintenance_record.date,
                    "mileage": maintenance_record.mileage_at_service,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Publish maintenance event
        await self.messaging_client.publish_event(
            "vehicle.maintenance_completed",
            {
                "vehicle_id": vehicle_id,
                "maintenance_type": maintenance_record.maintenance_type,
                "cost": maintenance_record.cost,
                "date": maintenance_record.date.isoformat(),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return maintenance_record

    async def get_vehicle_maintenance_history(self, vehicle_id: str) -> List[MaintenanceRecord]:
        """Get maintenance history for a vehicle"""
        cursor = self.maintenance_collection.find(
            {"vehicle_id": ObjectId(vehicle_id)}
        ).sort("date", -1)
        
        maintenance_records = []
        async for record_data in cursor:
            maintenance_records.append(MaintenanceRecord(**record_data))
            
        return maintenance_records

    async def check_maintenance_due(self, days_ahead: int = 30) -> List[Vehicle]:
        """Get vehicles due for maintenance within specified days"""
        due_date = datetime.utcnow() + timedelta(days=days_ahead)
        
        cursor = self.vehicles_collection.find({
            "next_maintenance_date": {"$lte": due_date},
            "status": {"$ne": VehicleStatus.MAINTENANCE.value}
        })
        
        vehicles_due = []
        async for vehicle_data in cursor:
            vehicles_due.append(Vehicle(**vehicle_data))
            
        return vehicles_due

    async def delete_vehicle(self, vehicle_id: str) -> bool:
        """Delete a vehicle (soft delete by updating status)"""
        result = await self.vehicles_collection.update_one(
            {"_id": ObjectId(vehicle_id)},
            {
                "$set": {
                    "status": VehicleStatus.OUT_OF_SERVICE.value,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count:
            await self.messaging_client.publish_event(
                "vehicle.deleted",
                {
                    "vehicle_id": vehicle_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            return True
        return False
