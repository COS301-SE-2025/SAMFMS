import motor.motor_asyncio
import os
import logging

logger = logging.getLogger(__name__)

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://host.docker.internal:27017")
DATABASE_NAME = "security_db"

client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
db = client[DATABASE_NAME]

security_users_collection = db.security_users
sessions_collection = db.sessions
audit_logs_collection = db.audit_logs


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
        
        await sessions_collection.create_index("user_id")
        await sessions_collection.create_index("expires_at")
        
        await audit_logs_collection.create_index("user_id")
        
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


async def log_security_event(user_id: str, action: str, details: dict = None):
    """Log security-related events for audit purposes"""
    try:
        from datetime import datetime
        audit_entry = {
            "user_id": user_id,
            "action": action,
            "details": details or {},
            "timestamp": datetime.utcnow(),
            "ip_address": details.get("ip_address") if details else None
        }
        await audit_logs_collection.insert_one(audit_entry)
        logger.info(f"Logged security event: {action} for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to log security event: {e}")
