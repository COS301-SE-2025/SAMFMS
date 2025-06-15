import motor.motor_asyncio
import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# LEGACY FILE - This file is kept for backward compatibility
# New code should use: from config.database import ...
# For gradual migration, this file imports from new structure

# Import from new structure
from config.database import (
    client, db, security_users_collection, sessions_collection, 
    audit_logs_collection, blacklisted_tokens_collection,
    test_database_connection, create_indexes, cleanup_expired_sessions
)

# Legacy functions redirected to new repositories
from repositories.audit_repository import AuditRepository, TokenRepository

async def log_security_event(user_id: str, action: str, details: dict = None):
    """Legacy function - use AuditRepository.log_security_event instead"""
    return await AuditRepository.log_security_event(user_id, action, details)

async def check_security_alerts(user_id: str, action: str, details: dict = None):
    """Check for security patterns that require alerting"""
    try:
        current_time = datetime.utcnow()
        
        # Check for multiple failed login attempts
        if action == "failed_login_attempt":
            # Count failed attempts in last hour
            failed_count = await AuditRepository.count_failed_attempts(user_id, 1)
            
            if failed_count >= 3:
                logger.warning(f"SECURITY ALERT: Multiple failed login attempts for user {user_id}")
                await AuditRepository.log_security_event(
                    user_id=user_id,
                    action="security_alert_multiple_failed_logins",
                    details={"failed_count": failed_count, "time_window": "1_hour"}
                )
        
        # Check for login from multiple IPs
        elif action == "successful_login":
            # This could be expanded to check for geographic anomalies
            pass
            
    except Exception as e:
        logger.error(f"Failed to check security alerts: {e}")


async def blacklist_token(token_hash: str, expires_at: datetime, user_id: str = None):
    """Legacy function - use TokenRepository.blacklist_token instead"""
    return await TokenRepository.blacklist_token(token_hash, expires_at)


async def is_token_blacklisted(token_hash: str) -> bool:
    """Legacy function - use TokenRepository.is_token_blacklisted instead"""
    return await TokenRepository.is_token_blacklisted(token_hash)


async def blacklist_all_user_tokens(user_id: str):
    """Legacy function - use TokenRepository.blacklist_all_user_tokens instead"""
    return await TokenRepository.blacklist_all_user_tokens(user_id)


async def get_security_metrics():
    """Legacy function - use AuditRepository.get_security_metrics instead"""
    return await AuditRepository.get_security_metrics()


# Keep original constants for compatibility
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://host.docker.internal:27017")
DATABASE_NAME = "security_db"
