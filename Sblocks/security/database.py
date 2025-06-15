import motor.motor_asyncio
import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://host.docker.internal:27017")
DATABASE_NAME = "security_db"

client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
db = client[DATABASE_NAME]

security_users_collection = db.security_users
sessions_collection = db.sessions
audit_logs_collection = db.audit_logs
blacklisted_tokens_collection = db.blacklisted_tokens


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
        
        await blacklisted_tokens_collection.create_index("token_hash", unique=True)
        await blacklisted_tokens_collection.create_index("expires_at")
        
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
        
        # Add security alerting for critical events
        await check_security_alerts(user_id, action, details)
        
    except Exception as e:
        logger.error(f"Failed to log security event: {e}")


async def check_security_alerts(user_id: str, action: str, details: dict = None):
    """Check for security patterns that require alerting"""
    try:
        current_time = datetime.utcnow()
        
        # Check for multiple failed login attempts
        if action == "failed_login_attempt":
            # Count failed attempts in last hour
            hour_ago = current_time - timedelta(hours=1)
            failed_count = await audit_logs_collection.count_documents({
                "user_id": user_id,
                "action": "failed_login_attempt",
                "timestamp": {"$gte": hour_ago}
            })
            
            if failed_count >= 3:
                logger.warning(f"SECURITY ALERT: Multiple failed login attempts for user {user_id}")
                await log_security_event(
                    user_id=user_id,
                    action="security_alert_multiple_failed_logins",
                    details={"failed_count": failed_count, "time_window": "1_hour"}
                )
        
        # Check for login from multiple IPs
        elif action == "successful_login":
            ip_address = details.get("ip_address") if details else None
            if ip_address:
                # Check recent logins from different IPs
                day_ago = current_time - timedelta(days=1)
                recent_ips = await audit_logs_collection.distinct(
                    "details.ip_address",
                    {
                        "user_id": user_id,
                        "action": "successful_login",
                        "timestamp": {"$gte": day_ago}
                    }
                )
                
                if len(recent_ips) > 3:
                    logger.warning(f"SECURITY ALERT: User {user_id} logged in from multiple IPs: {recent_ips}")
                    await log_security_event(
                        user_id=user_id,
                        action="security_alert_multiple_ips",
                        details={"ip_addresses": recent_ips, "time_window": "24_hours"}
                    )
                    
    except Exception as e:
        logger.error(f"Failed to check security alerts: {e}")


async def get_security_metrics():
    """Get security metrics for monitoring"""
    try:
        current_time = datetime.utcnow()
        hour_ago = current_time - timedelta(hours=1)
        day_ago = current_time - timedelta(days=1)
        
        metrics = {
            "failed_logins_last_hour": await audit_logs_collection.count_documents({
                "action": "failed_login_attempt",
                "timestamp": {"$gte": hour_ago}
            }),
            "successful_logins_last_hour": await audit_logs_collection.count_documents({
                "action": "successful_login",
                "timestamp": {"$gte": hour_ago}
            }),
            "active_users_last_day": await audit_logs_collection.distinct(
                "user_id",
                {
                    "action": "successful_login",
                    "timestamp": {"$gte": day_ago}
                }
            ),
            "blacklisted_tokens": await blacklisted_tokens_collection.count_documents({}),
            "security_alerts_last_day": await audit_logs_collection.count_documents({
                "action": {"$regex": "^security_alert_"},
                "timestamp": {"$gte": day_ago}
            })
        }
        
        metrics["active_users_count"] = len(metrics["active_users_last_day"])
        del metrics["active_users_last_day"]  # Remove the list, keep just the count
        
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get security metrics: {e}")
        return {}


async def blacklist_token(token_hash: str, expires_at, user_id: str = None):
    """Blacklist a token by storing its hash"""
    try:
        from datetime import datetime
        blacklist_entry = {
            "token_hash": token_hash,
            "expires_at": expires_at,
            "user_id": user_id,
            "blacklisted_at": datetime.utcnow()
        }
        await blacklisted_tokens_collection.insert_one(blacklist_entry)
        logger.info(f"Token blacklisted for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to blacklist token: {e}")
        raise


async def is_token_blacklisted(token_hash: str) -> bool:
    """Check if a token is blacklisted"""
    try:
        result = await blacklisted_tokens_collection.find_one({"token_hash": token_hash})
        return result is not None
    except Exception as e:
        logger.error(f"Failed to check token blacklist: {e}")
        return False


async def blacklist_all_user_tokens(user_id: str):
    """Blacklist all tokens for a user (used during logout from all devices)"""
    try:
        from datetime import datetime, timedelta
        # Since we can't easily enumerate all user tokens, we'll create a user-level blacklist entry
        # This requires checking user_id in token verification
        blacklist_entry = {
            "user_id": user_id,
            "blacklist_all_before": datetime.utcnow(),
            "type": "user_blacklist"
        }
        await blacklisted_tokens_collection.insert_one(blacklist_entry)
        logger.info(f"All tokens blacklisted for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to blacklist all user tokens: {e}")
        raise
