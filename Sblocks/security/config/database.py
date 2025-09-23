import motor.motor_asyncio
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

# MongoDB client and database
client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URL)
db = client[settings.DATABASE_NAME]

# Function to get database instance (for services)
def get_database():
    """Get the database instance"""
    return db

# Collections
security_users_collection = db.security_users
sessions_collection = db.sessions
audit_logs_collection = db.audit_logs
blacklisted_tokens_collection = db.blacklisted_tokens
otp_collection = db.otp
removed_users = db.removed_users




async def test_database_connection():
    """Test the database connection"""
    try:
        await client.admin.command('ping')
        logger.info("Successfully connected to Security database")
        return True
    except Exception as e:
        logger.error(f"Failed to connect to Security database: {e}")
        return False


async def create_indexes():
    """Create database indexes for optimal performance"""
    try:
        await security_users_collection.create_index("email", unique=True)
        await security_users_collection.create_index("user_id", unique=True)
        #await security_users_collection.create_index("phone", unique=True)
        await sessions_collection.create_index("user_id")
        
        await audit_logs_collection.create_index("user_id")
        
        await blacklisted_tokens_collection.create_index("token_hash", unique=True)

        await otp_collection.create_index("created_at", expireAfterSeconds=900)  # 15 minutes
        
        logger.info("Database indexes created successfully")
    except Exception as e:
        logger.error(f"Failed to create database indexes: {e}")


async def cleanup_expired_sessions():
    """Clean up expired sessions"""
    try:
        from datetime import datetime
        result = await sessions_collection.delete_many({
            "expires_at": {"$lt": datetime.utcnow()}
        })
        if result.deleted_count > 0:
            logger.info(f"Cleaned up {result.deleted_count} expired sessions")
    except Exception as e:
        logger.error(f"Failed to cleanup expired sessions: {e}")
