"""
Database configuration and connection management for GPS service
"""
import asyncio
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure
import logging

from config import settings, collections

logger = logging.getLogger(__name__)

class Database:
    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None

db = Database()

async def get_database() -> AsyncIOMotorDatabase:
    """Get database instance"""
    if db.database is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongo() first.")
    return db.database

async def connect_to_mongo():
    """Create database connection"""
    try:
        logger.info(f"Connecting to MongoDB at {settings.mongodb_url}")
        
        db.client = AsyncIOMotorClient(
            settings.mongodb_url,
            minPoolSize=settings.mongodb_min_pool_size,
            maxPoolSize=settings.mongodb_max_pool_size,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=30000,
        )
        
        # Test the connection
        await db.client.admin.command('ping')
        
        db.database = db.client[settings.mongodb_database]
        
        # Create indexes
        await create_indexes()
        
        logger.info(f"Successfully connected to MongoDB database: {settings.mongodb_database}")
        
    except ConnectionFailure as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error connecting to MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        logger.info("Closing MongoDB connection")
        db.client.close()
        db.client = None
        db.database = None

async def create_indexes():
    """Create database indexes for optimal performance"""
    if not db.database:
        return
    
    try:
        logger.info("Creating database indexes...")
        
        # Vehicle locations indexes
        locations_collection = db.database[collections.VEHICLE_LOCATIONS]
        await locations_collection.create_index("vehicle_id", unique=True)
        await locations_collection.create_index("timestamp")
        await locations_collection.create_index([("coordinates.latitude", 1), ("coordinates.longitude", 1)])
        await locations_collection.create_index("status")
        
        # Location history indexes
        history_collection = db.database[collections.LOCATION_HISTORY]
        await history_collection.create_index([("vehicle_id", 1), ("timestamp", -1)])
        await history_collection.create_index("timestamp")
        await history_collection.create_index("event_type")
        await history_collection.create_index("geofence_id")
        await history_collection.create_index("trip_id")
        await history_collection.create_index("driver_id")
        await history_collection.create_index([("coordinates.latitude", 1), ("coordinates.longitude", 1)])
        
        # Geofences indexes
        geofences_collection = db.database[collections.GEOFENCES]
        await geofences_collection.create_index("name")
        await geofences_collection.create_index("type")
        await geofences_collection.create_index("status")
        await geofences_collection.create_index([("coordinates.latitude", 1), ("coordinates.longitude", 1)])
        await geofences_collection.create_index("vehicle_ids")
        await geofences_collection.create_index("created_at")
        
        # Geofence events indexes
        geofence_events_collection = db.database[collections.GEOFENCE_EVENTS]
        await geofence_events_collection.create_index([("geofence_id", 1), ("timestamp", -1)])
        await geofence_events_collection.create_index([("vehicle_id", 1), ("timestamp", -1)])
        await geofence_events_collection.create_index("event_type")
        await geofence_events_collection.create_index("timestamp")
        await geofence_events_collection.create_index("trip_id")
        await geofence_events_collection.create_index("driver_id")
        
        # Vehicle routes indexes
        routes_collection = db.database[collections.VEHICLE_ROUTES]
        await routes_collection.create_index([("vehicle_id", 1), ("start_time", -1)])
        await routes_collection.create_index("trip_id")
        await routes_collection.create_index("driver_id")
        await routes_collection.create_index("route_type")
        await routes_collection.create_index("status")
        await routes_collection.create_index("created_at")
        
        # Route segments indexes
        segments_collection = db.database[collections.ROUTE_SEGMENTS]
        await segments_collection.create_index("route_id")
        await segments_collection.create_index("vehicle_id")
        await segments_collection.create_index("created_at")
        
        # Planned routes indexes
        planned_routes_collection = db.database[collections.PLANNED_ROUTES]
        await planned_routes_collection.create_index("vehicle_id")
        await planned_routes_collection.create_index("driver_id")
        await planned_routes_collection.create_index("trip_id")
        await planned_routes_collection.create_index("status")
        await planned_routes_collection.create_index("scheduled_start")
        await planned_routes_collection.create_index("priority")
        await planned_routes_collection.create_index("created_at")
        
        # Compound indexes for complex queries
        await history_collection.create_index([
            ("vehicle_id", 1), 
            ("event_type", 1), 
            ("timestamp", -1)
        ])
        
        await geofence_events_collection.create_index([
            ("geofence_id", 1), 
            ("vehicle_id", 1), 
            ("timestamp", -1)
        ])
        
        # TTL index for location history cleanup (90 days)
        await history_collection.create_index(
            "timestamp", 
            expireAfterSeconds=settings.location_retention_days * 24 * 60 * 60
        )
        
        # 2dsphere indexes for geospatial queries
        await locations_collection.create_index([("coordinates", "2dsphere")])
        await history_collection.create_index([("coordinates", "2dsphere")])
        await geofences_collection.create_index([("coordinates", "2dsphere")])
        
        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")
        # Don't raise here as this is not critical for startup

async def get_collection(collection_name: str):
    """Get a specific collection"""
    database = await get_database()
    return database[collection_name]

# Health check function
async def check_database_health() -> bool:
    """Check if database is healthy and accessible"""
    try:
        if not db.client:
            return False
        
        # Ping the database
        await db.client.admin.command('ping')
        return True
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

# Database utility functions
async def get_database_stats():
    """Get database statistics"""
    try:
        database = await get_database()
        stats = await database.command("dbStats")
        
        return {
            "database": settings.mongodb_database,
            "collections": stats.get("collections", 0),
            "objects": stats.get("objects", 0),
            "dataSize": stats.get("dataSize", 0),
            "storageSize": stats.get("storageSize", 0),
            "indexes": stats.get("indexes", 0),
            "indexSize": stats.get("indexSize", 0)
        }
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return {}

async def cleanup_old_data():
    """Cleanup old data based on retention policies"""
    try:
        database = await get_database()
        
        # This is handled by TTL indexes, but we can add manual cleanup here if needed
        logger.info("Data cleanup completed (handled by TTL indexes)")
        
    except Exception as e:
        logger.error(f"Error during data cleanup: {e}")

# Export main functions
__all__ = [
    "get_database",
    "connect_to_mongo", 
    "close_mongo_connection",
    "get_collection",
    "check_database_health",
    "get_database_stats",
    "cleanup_old_data"
]
