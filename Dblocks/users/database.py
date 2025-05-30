import motor.motor_asyncio
import os
import logging

logger = logging.getLogger(__name__)

# Database configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://host.docker.internal:27017")
DATABASE_NAME = "users_db"

# MongoDB connection
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
db = client[DATABASE_NAME]

# Collections
user_profiles_collection = db.user_profiles


async def test_database_connection():
    """Test the database connection"""
    try:
        await client.admin.command('ping')
        logger.info("✅ Successfully connected to Users database")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to connect to Users database: {e}")
        return False


async def create_indexes():
    """Create database indexes for optimal performance"""
    try:
        # Index on user_id for fast user lookups
        await user_profiles_collection.create_index("user_id", unique=True)
        await user_profiles_collection.create_index("full_name")
        await user_profiles_collection.create_index("created_at")
        
        logger.info("✅ Database indexes created successfully")
    except Exception as e:
        logger.error(f"❌ Failed to create database indexes: {e}")
