from typing import List, Optional, Dict, Any
from bson import ObjectId
from datetime import datetime, timedelta
from ..models.models import Driver, DriverStatus, DriverLicense
from ..database import get_drivers_collection
from ..messaging.rabbitmq_client import RabbitMQClient


class DriverService:
    def __init__(self, messaging_client: RabbitMQClient):
        self.messaging_client = messaging_client
        self.drivers_collection = get_drivers_collection()

    async def create_driver(self, driver_data: Dict[str, Any]) -> Driver:
        """Create a new driver"""
        driver = Driver(**driver_data)
        
        # Insert into database
        result = await self.drivers_collection.insert_one(driver.dict(by_alias=True))
        driver.id = result.inserted_id
        
        # Publish driver created event
        await self.messaging_client.publish_event(
            "driver.created",
            {
                "driver_id": str(driver.id),
                "employee_id": driver.employee_id,
                "name": f"{driver.first_name} {driver.last_name}",
                "status": driver.status.value,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return driver

    async def get_driver_by_id(self, driver_id: str) -> Optional[Driver]:
        """Get driver by ID"""
        driver_data = await self.drivers_collection.find_one(
            {"_id": ObjectId(driver_id)}
        )
        return Driver(**driver_data) if driver_data else None

    async def get_driver_by_employee_id(self, employee_id: str) -> Optional[Driver]:
        """Get driver by employee ID"""
        driver_data = await self.drivers_collection.find_one(
            {"employee_id": employee_id}
        )
        return Driver(**driver_data) if driver_data else None

    async def get_drivers(
        self, 
        status: Optional[DriverStatus] = None,
        available_only: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[Driver]:
        """Get drivers with optional filters"""
        query = {}
        
        if status:
            query["status"] = status.value
        if available_only:
            query["status"] = DriverStatus.AVAILABLE.value
            
        cursor = self.drivers_collection.find(query).skip(skip).limit(limit)
        drivers = []
        
        async for driver_data in cursor:
            drivers.append(Driver(**driver_data))
            
        return drivers

    async def update_driver(self, driver_id: str, update_data: Dict[str, Any]) -> Optional[Driver]:
        """Update driver information"""
        update_data["updated_at"] = datetime.utcnow()
        
        result = await self.drivers_collection.update_one(
            {"_id": ObjectId(driver_id)},
            {"$set": update_data}
        )
        
        if result.modified_count:
            updated_driver = await self.get_driver_by_id(driver_id)
            
            # Publish driver updated event
            await self.messaging_client.publish_event(
                "driver.updated",
                {
                    "driver_id": driver_id,
                    "updated_fields": list(update_data.keys()),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            return updated_driver
        return None

    async def update_driver_status(self, driver_id: str, status: DriverStatus) -> bool:
        """Update driver status"""
        result = await self.drivers_collection.update_one(
            {"_id": ObjectId(driver_id)},
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
                "driver.status_changed",
                {
                    "driver_id": driver_id,
                    "new_status": status.value,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            return True
        return False

    async def get_available_drivers(
        self, 
        license_types: Optional[List[DriverLicense]] = None,
        exclude_on_duty: bool = True
    ) -> List[Driver]:
        """Get all available drivers for trip assignment"""
        query = {"status": DriverStatus.AVAILABLE.value}
        
        if exclude_on_duty:
            # Check if driver is not currently on a trip
            query["current_trip_id"] = {"$exists": False}
            
        if license_types:
            # Match drivers with required license types
            license_values = [license.value for license in license_types]
            query["license.license_type"] = {"$in": license_values}
            
        # Check license expiry (valid for at least 30 days)
        min_expiry_date = datetime.utcnow() + timedelta(days=30)
        query["license.expiry_date"] = {"$gt": min_expiry_date}
        
        cursor = self.drivers_collection.find(query)
        drivers = []
        
        async for driver_data in cursor:
            drivers.append(Driver(**driver_data))
            
        return drivers

    async def assign_driver_to_trip(self, driver_id: str, trip_id: str) -> bool:
        """Assign driver to a trip"""
        result = await self.drivers_collection.update_one(
            {
                "_id": ObjectId(driver_id),
                "status": DriverStatus.AVAILABLE.value
            },
            {
                "$set": {
                    "status": DriverStatus.ON_DUTY.value,
                    "current_trip_id": trip_id,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count:
            await self.messaging_client.publish_event(
                "driver.assigned_to_trip",
                {
                    "driver_id": driver_id,
                    "trip_id": trip_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            return True
        return False

    async def release_driver_from_trip(self, driver_id: str) -> bool:
        """Release driver from trip assignment"""
        result = await self.drivers_collection.update_one(
            {"_id": ObjectId(driver_id)},
            {
                "$set": {
                    "status": DriverStatus.AVAILABLE.value,
                    "updated_at": datetime.utcnow()
                },
                "$unset": {
                    "current_trip_id": ""
                }
            }
        )
        
        if result.modified_count:
            await self.messaging_client.publish_event(
                "driver.released_from_trip",
                {
                    "driver_id": driver_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            return True
        return False

    async def check_license_expiry(self, days_ahead: int = 60) -> List[Driver]:
        """Get drivers with licenses expiring within specified days"""
        expiry_threshold = datetime.utcnow() + timedelta(days=days_ahead)
        
        cursor = self.drivers_collection.find({
            "license.expiry_date": {"$lte": expiry_threshold},
            "status": {"$ne": DriverStatus.INACTIVE.value}
        })
        
        drivers_expiring = []
        async for driver_data in cursor:
            drivers_expiring.append(Driver(**driver_data))
            
        return drivers_expiring

    async def update_driver_location(
        self, 
        driver_id: str, 
        latitude: float, 
        longitude: float,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """Update driver's current location"""
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
        
        result = await self.drivers_collection.update_one(
            {"_id": ObjectId(driver_id)},
            {"$set": location_data}
        )
        
        if result.modified_count:
            # Publish location update event
            await self.messaging_client.publish_event(
                "driver.location_updated",
                {
                    "driver_id": driver_id,
                    "latitude": latitude,
                    "longitude": longitude,
                    "timestamp": timestamp.isoformat()
                }
            )
            return True
        return False

    async def add_driver_performance_metric(
        self, 
        driver_id: str, 
        metric_type: str, 
        value: float,
        date: Optional[datetime] = None
    ) -> bool:
        """Add performance metric for driver"""
        if not date:
            date = datetime.utcnow()
            
        performance_metric = {
            "metric_type": metric_type,
            "value": value,
            "date": date
        }
        
        result = await self.drivers_collection.update_one(
            {"_id": ObjectId(driver_id)},
            {
                "$push": {"performance_metrics": performance_metric},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        if result.modified_count:
            await self.messaging_client.publish_event(
                "driver.performance_metric_added",
                {
                    "driver_id": driver_id,
                    "metric_type": metric_type,
                    "value": value,
                    "date": date.isoformat(),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            return True
        return False

    async def get_driver_performance_summary(
        self, 
        driver_id: str, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get driver performance summary"""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
            
        pipeline = [
            {"$match": {"_id": ObjectId(driver_id)}},
            {"$unwind": "$performance_metrics"},
            {
                "$match": {
                    "performance_metrics.date": {
                        "$gte": start_date,
                        "$lte": end_date
                    }
                }
            },
            {
                "$group": {
                    "_id": "$performance_metrics.metric_type",
                    "avg_value": {"$avg": "$performance_metrics.value"},
                    "max_value": {"$max": "$performance_metrics.value"},
                    "min_value": {"$min": "$performance_metrics.value"},
                    "count": {"$sum": 1}
                }
            }
        ]
        
        performance_summary = {}
        async for result in self.drivers_collection.aggregate(pipeline):
            performance_summary[result["_id"]] = {
                "average": result["avg_value"],
                "maximum": result["max_value"],
                "minimum": result["min_value"],
                "count": result["count"]
            }
            
                return performance_summary

    async def search_drivers(self, search_term: str) -> List[Driver]:
        """Search drivers by name, employee ID, or email"""
        query = {
            "$or": [
                {"first_name": {"$regex": search_term, "$options": "i"}},
                {"last_name": {"$regex": search_term, "$options": "i"}},
                {"employee_id": {"$regex": search_term, "$options": "i"}},
                {"email": {"$regex": search_term, "$options": "i"}}
            ]
        }
        
        cursor = self.drivers_collection.find(query)
        drivers = []
        
        async for driver_data in cursor:
            drivers.append(Driver(**driver_data))
            
        return drivers

    async def delete_driver(self, driver_id: str) -> bool:
        """Delete a driver (soft delete by updating status)"""
        result = await self.drivers_collection.update_one(
            {"_id": ObjectId(driver_id)},
            {
                "$set": {
                    "status": DriverStatus.INACTIVE.value,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count:
            await self.messaging_client.publish_event(
                "driver.deleted",
                {
                    "driver_id": driver_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            return True
        return False
