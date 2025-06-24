import motor.motor_asyncio
import os
import logging

logger = logging.getLogger(__name__)

# MongoDB connection settings
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://host.docker.internal:27017")
DATABASE_NAME = "gps_db"

# Create MongoDB client and database reference
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
db = client[DATABASE_NAME]

# Collection for GPS locations
gps_locations_collection = db.gps_locations

async def get_gps_location_by_device_id(device_id: str):
    location = await gps_locations_collection.find_one({"device_id": device_id})
    if location:
        location['_id'] = str(location['_id'])  
    return location

async def test_database_connection():
    """Test the database connection."""
    try:
        await client.admin.command('ping')
        logger.info("Successfully connected to GPS database")
        return True
    except Exception as e:
        logger.error(f"Failed to connect to GPS database: {e}")
        return False

async def create_indexes():
    """Create indexes for optimal performance."""
    try:
        await gps_locations_collection.create_index("device_id")
        await gps_locations_collection.create_index("timestamp")
        logger.info("Database indexes created successfully")
    except Exception as e:
        logger.error(f"Failed to create database indexes: {e}")
