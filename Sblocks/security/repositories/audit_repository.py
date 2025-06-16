from config.database import audit_logs_collection, blacklisted_tokens_collection
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class AuditRepository:
    """Repository for audit and security logging operations"""
    
    @staticmethod
    async def log_security_event(user_id: str, action: str, details: Dict[str, Any] = None):
        """Log security-related events for audit purposes"""
        try:
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
            raise
    
    @staticmethod
    async def count_failed_attempts(user_id: str, hours: int = 1) -> int:
        """Count failed login attempts for a user in the last X hours"""
        try:
            time_ago = datetime.utcnow() - timedelta(hours=hours)
            count = await audit_logs_collection.count_documents({
                "user_id": user_id,
                "action": "failed_login_attempt",
                "timestamp": {"$gte": time_ago}
            })
            return count
        except Exception as e:
            logger.error(f"Failed to count failed attempts: {e}")
            raise
    
    @staticmethod
    async def get_security_metrics() -> Dict[str, Any]:
        """Get security metrics from audit logs"""
        try:
            pipeline = [
                {
                    "$group": {
                        "_id": "$action",
                        "count": {"$sum": 1},
                        "latest": {"$max": "$timestamp"}
                    }
                }
            ]
            cursor = audit_logs_collection.aggregate(pipeline)
            metrics = {}
            async for doc in cursor:
                metrics[doc["_id"]] = {
                    "count": doc["count"],
                    "latest": doc["latest"]
                }
            return metrics
        except Exception as e:
            logger.error(f"Failed to get security metrics: {e}")
            raise


class TokenRepository:
    """Repository for token blacklist operations"""
    
    @staticmethod
    async def blacklist_token(token_hash: str, expires_at: datetime):
        """Add token to blacklist"""
        try:
            await blacklisted_tokens_collection.insert_one({
                "token_hash": token_hash,
                "expires_at": expires_at,
                "blacklisted_at": datetime.utcnow()
            })
            logger.info(f"Token blacklisted: {token_hash[:8]}...")
        except Exception as e:
            logger.error(f"Failed to blacklist token: {e}")
            raise
    
    @staticmethod
    async def is_token_blacklisted(token_hash: str) -> bool:
        """Check if token is blacklisted"""
        try:
            doc = await blacklisted_tokens_collection.find_one({"token_hash": token_hash})
            return doc is not None
        except Exception as e:
            logger.error(f"Failed to check token blacklist: {e}")
            raise
    
    @staticmethod
    async def blacklist_all_user_tokens(user_id: str):
        """Blacklist all tokens for a user by setting force_logout_after timestamp"""
        try:
            from repositories.user_repository import UserRepository
            await UserRepository.update_user(user_id, {
                "force_logout_after": datetime.utcnow()
            })
            logger.info(f"Force logout set for user: {user_id}")
        except Exception as e:
            logger.error(f"Failed to blacklist all user tokens: {e}")
            raise
    
    @staticmethod
    async def cleanup_expired_tokens():
        """Clean up expired blacklisted tokens"""
        try:
            result = await blacklisted_tokens_collection.delete_many({
                "expires_at": {"$lt": datetime.utcnow()}
            })
            if result.deleted_count > 0:
                logger.info(f"Cleaned up {result.deleted_count} expired blacklisted tokens")
        except Exception as e:
            logger.error(f"Failed to cleanup expired tokens: {e}")
            raise
