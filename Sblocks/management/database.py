import motor.motor_asyncio
import os
import logging

logger = logging.getLogger(__name__)

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://host.docker.internal:27017")
DATABASE_NAME = "management_db"

client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
db = client[DATABASE_NAME]

vehicle_management_collection = db.vehicle_management
vehicle_assignments_collection = db.vehicle_assignments
vehicle_usage_logs_collection = db.vehicle_usage_logs
fleet_analytics_collection = db.fleet_analytics
drivers_collection = db.drivers


def get_driver_collection():
    """Get the driver collection for driver management"""
    return drivers_collection


async def test_database_connection():
    """Test the database connection"""
    try:
        await client.admin.command('ping')
        logger.info("Successfully connected to Management database")
        return True
    except Exception as e:
        logger.error(f"Failed to connect to Management database: {e}")
        return False


async def create_indexes():
    """Create database indexes for optimal performance"""
    try:
        await vehicle_management_collection.create_index("vehicle_id", unique=True)
        
        await vehicle_assignments_collection.create_index("vehicle_id")
        await vehicle_assignments_collection.create_index("driver_id")
        
        await vehicle_usage_logs_collection.create_index("vehicle_id")
        await vehicle_usage_logs_collection.create_index("driver_id")
        
        await drivers_collection.create_index("employee_id", unique=True)
        await drivers_collection.create_index("user_id")
        await drivers_collection.create_index("current_vehicle_id")
        
        await fleet_analytics_collection.create_index("vehicle_id")
        
        logger.info("Database indexes created successfully")
    except Exception as e:
        logger.error(f"Failed to create database indexes: {e}")


async def log_management_event(vehicle_id: str, action: str, details: dict = None):
    """Log management-related events for audit purposes"""
    try:
        from datetime import datetime
        log_entry = {
            "vehicle_id": vehicle_id,
            "action": action,
            "details": details or {},
            "timestamp": datetime.utcnow()
        }
        await fleet_analytics_collection.insert_one(log_entry)
        logger.info(f"Logged management event: {action} for vehicle {vehicle_id}")
    except Exception as e:
        logger.error(f"Failed to log management event: {e}")


async def get_vehicle_utilization_stats(vehicle_id: str = None, days: int = 30):
    """Get vehicle utilization statistics"""
    try:
        from datetime import datetime, timedelta
        
        start_date = datetime.utcnow() - timedelta(days=days)
        match_query = {"trip_start": {"$gte": start_date}}
        
        if vehicle_id:
            match_query["vehicle_id"] = vehicle_id
        
        pipeline = [
            {"$match": match_query},
            {"$group": {
                "_id": "$vehicle_id",
                "total_trips": {"$sum": 1},
                "total_distance": {"$sum": "$distance_km"},
                "total_fuel": {"$sum": "$fuel_consumed"},
                "avg_trip_distance": {"$avg": "$distance_km"}
            }}
        ]
        
        cursor = vehicle_usage_logs_collection.aggregate(pipeline)
        results = await cursor.to_list(length=None)
        return results
        
    except Exception as e:
        logger.error(f"Failed to get utilization stats: {e}")
        return []
