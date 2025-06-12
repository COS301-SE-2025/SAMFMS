import os
import logging
import motor.motor_asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Any
from bson import ObjectId

logger = logging.getLogger(__name__)

# MongoDB configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/vehicles_db")
DATABASE_NAME = MONGODB_URL.split("/")[-1]
mongodb_client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
mongodb_db = mongodb_client[DATABASE_NAME]

# MongoDB Collections
vehicles_collection = mongodb_db.vehicles
maintenance_records_collection = mongodb_db.maintenance_records
vehicle_specifications_collection = mongodb_db.vehicle_specifications
vehicle_documents_collection = mongodb_db.vehicle_documents
vehicle_activity_log_collection = mongodb_db.vehicle_activity_log

# Create indexes
async def create_indexes():
    """Create indexes for better query performance"""
    try:
        # Vehicle indexes
        await vehicles_collection.create_index([("make", 1), ("model", 1)])
        await vehicles_collection.create_index([("year", 1), ("is_active", 1)])
        await vehicles_collection.create_index([("fuel_type", 1)])
        
        # Maintenance records indexes
        await maintenance_records_collection.create_index([("vehicle_id", 1), ("service_date", 1)])
        await maintenance_records_collection.create_index([("maintenance_type", 1), ("service_date", 1)])
        await maintenance_records_collection.create_index([("next_service_date", 1)])
        
        # Vehicle specifications indexes
        await vehicle_specifications_collection.create_index([("vehicle_id", 1)])
        
        # Vehicle documents indexes
        await vehicle_documents_collection.create_index([("vehicle_id", 1), ("document_type", 1)])
        await vehicle_documents_collection.create_index([("expiry_date", 1), ("is_valid", 1)])
        
        # Vehicle activity log indexes
        await vehicle_activity_log_collection.create_index([("vehicle_id", 1)])
        await vehicle_activity_log_collection.create_index([("activity_type", 1), ("timestamp", 1)])
        await vehicle_activity_log_collection.create_index([("user_id", 1), ("timestamp", 1)])
        
        logger.info("Database indexes initialized successfully")
    except Exception as e:
        logger.error(f"Failed to create database indexes: {e}")

def get_mongodb():
    """Dependency to get MongoDB database client"""
    return mongodb_db

def get_db():
    """Dependency to get database client (MongoDB)"""
    return mongodb_db

async def init_database():
    """Initialize the database with collections and indexes"""
    try:
        # Ensure the collections exist by touching them
        await vehicles_collection.find_one({})
        await maintenance_records_collection.find_one({})
        await vehicle_specifications_collection.find_one({})
        await vehicle_documents_collection.find_one({})
        await vehicle_activity_log_collection.find_one({})
        
        # Create indexes
        await create_indexes()
        
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

# Function needed by main.py
async def create_vehicle_activity_log():
    """Create a vehicle activity log collection if it doesn't exist"""
    try:
        # In MongoDB, collections are created automatically when used
        # Just ensure the collection exists by touching it
        await vehicle_activity_log_collection.find_one({})
        
        # Create indexes for the activity log
        await vehicle_activity_log_collection.create_index([("vehicle_id", 1)])
        await vehicle_activity_log_collection.create_index([("timestamp", 1)])
        await vehicle_activity_log_collection.create_index([("activity_type", 1)])
        
        logger.info("Vehicle activity log collection is ready")
        
    except Exception as e:
        logger.error(f"Failed to setup activity log collection: {e}")

async def log_vehicle_activity(
    vehicle_id: str,
    activity_type: str,
    description: Optional[str] = None,
    details: Optional[dict] = None,
    user_id: Optional[str] = None,
    source_service: str = "vehicles_service",
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """Log vehicle-related activities"""
    try:
        log_data = {
            'vehicle_id': vehicle_id,
            'activity_type': activity_type,
            'description': description,
            'details': details,
            'user_id': user_id,
            'timestamp': datetime.now(timezone.utc),
            'source_service': source_service,
            'ip_address': ip_address,
            'user_agent': user_agent
        }
        
        # Insert log entry
        await vehicle_activity_log_collection.insert_one(log_data)
        logger.info(f"Activity logged: {activity_type} for vehicle {vehicle_id}")
        
    except Exception as e:
        logger.error(f"Failed to log activity: {e}")

async def get_vehicle_statistics():
    """Get overall vehicle database statistics"""
    try:
        stats = {}
        
        # Get vehicle count by status
        status_pipeline = [
            {"$group": {"_id": "$is_active", "count": {"$sum": 1}}}
        ]
        status_result = await vehicles_collection.aggregate(status_pipeline).to_list(length=None)
        stats['vehicles_by_status'] = {str(item["_id"]): item["count"] for item in status_result}
        
        # Get vehicle count by fuel type
        fuel_pipeline = [
            {"$match": {"fuel_type": {"$ne": None}}},
            {"$group": {"_id": "$fuel_type", "count": {"$sum": 1}}}
        ]
        fuel_result = await vehicles_collection.aggregate(fuel_pipeline).to_list(length=None)
        stats['vehicles_by_fuel_type'] = {str(item["_id"]): item["count"] for item in fuel_result}
        
        # Get maintenance statistics
        maintenance_pipeline = [
            {"$group": {
                "_id": None,
                "total_records": {"$sum": 1},
                "vehicles_with_maintenance": {"$addToSet": "$vehicle_id"},
                "avg_cost": {"$avg": "$cost"}
            }}
        ]
        maintenance_result = await maintenance_records_collection.aggregate(maintenance_pipeline).to_list(length=1)
        
        if maintenance_result:
            result = maintenance_result[0]
            stats['maintenance_stats'] = {
                'total_records': result.get("total_records", 0),
                'vehicles_with_maintenance': len(result.get("vehicles_with_maintenance", [])),
                'average_cost': float(result.get("avg_cost", 0)) if result.get("avg_cost") else 0.0
            }
        else:
            stats['maintenance_stats'] = {
                'total_records': 0,
                'vehicles_with_maintenance': 0,
                'average_cost': 0.0
            }
        
        # Get recent activity count
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        recent_activity_count = await vehicle_activity_log_collection.count_documents({
            "timestamp": {"$gte": seven_days_ago}
        })
        
        stats['recent_activity_count'] = recent_activity_count
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get vehicle statistics: {e}")
        return {}

async def cleanup_old_activity_logs(days: int = 90):
    """Clean up old activity logs to maintain performance"""
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        result = await vehicle_activity_log_collection.delete_many(
            {"timestamp": {"$lt": cutoff_date}}
        )
        
        deleted_count = result.deleted_count
        logger.info(f"Cleaned up {deleted_count} old activity log entries")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Failed to cleanup activity logs: {e}")
        return 0

async def check_database_health():
    """Check database connectivity and basic functionality"""
    try:
        # Test basic query
        await mongodb_db.command('ping')
        
        # Test collections existence
        collections = ['vehicles', 'maintenance_records', 'vehicle_specifications', 'vehicle_documents']
        for collection_name in collections:
            collection = mongodb_db[collection_name]
            count = await collection.count_documents({})
            logger.debug(f"Collection {collection_name} has {count} documents")
        
        return True
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False