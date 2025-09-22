from config.database import security_users_collection, otp_collection
from models.database_models import SecurityUser
from typing import Optional, Dict, Any
from bson import ObjectId
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for user data operations"""
    @staticmethod
    async def create_user(user_data: Dict[str, Any]) -> str:
        """Create a new user and return user_id"""
        try:
            result = await security_users_collection.insert_one(user_data)
            logger.info(f"Created user: {result}")
            return user_data['user_id']
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise
    
    @staticmethod
    async def find_by_email(email: str) -> Optional[Dict[str, Any]]:
        """Find user by email"""
        try:
            return await security_users_collection.find_one({"email": email})
        except Exception as e:
            logger.error(f"Failed to find user by email: {e}")
            raise
    
    @staticmethod
    async def find_by_user_id(user_id: str) -> Optional[Dict[str, Any]]:
        """Find user by user_id"""
        try:
            return await security_users_collection.find_one({"user_id": user_id})
        except Exception as e:
            logger.error(f"Failed to find user by user_id: {e}")
            raise
    
    @staticmethod
    async def update_user(user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user data"""
        try:
            logger.info(f"UserRepository.update_user called with user_id: {user_id}")
            logger.info(f"Updates to apply: {updates}")
            
            result = await security_users_collection.update_one(
                {"user_id": user_id},
                {"$set": updates}
            )
            
            logger.info(f"Update result - matched_count: {result.matched_count}, modified_count: {result.modified_count}")
            
            if result.matched_count == 0:
                logger.warning(f"No user found with user_id: {user_id}")
                return False
                  # Return True if user was found, even if no changes were made (data was identical)
            return result.matched_count > 0
        except Exception as e:
            logger.error(f"Failed to update user: {e}")
            raise
    
    @staticmethod
    async def update_by_filter(filter_dict: Dict[str, Any], updates: Dict[str, Any]) -> bool:
        """Update user by filter"""
        try:
            result = await security_users_collection.update_one(filter_dict, updates)
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update user by filter: {e}")
            raise
    
    @staticmethod
    async def increment_failed_attempts(user_id: str) -> bool:
        """Increment failed login attempts"""
        try:
            result = await security_users_collection.update_one(
                {"user_id": user_id},
                {"$inc": {"failed_login_attempts": 1}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to increment failed attempts: {e}")
            raise
    
    @staticmethod
    async def reset_failed_attempts(user_id: str) -> bool:
        """Reset failed login attempts and update last login"""
        try:
            result = await security_users_collection.update_one(
                {"user_id": user_id},
                {
                    "$set": {"failed_login_attempts": 0, "last_login": datetime.utcnow()}
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to reset failed attempts: {e}")
            raise
    
    @staticmethod
    async def count_users() -> int:
        """Count total users"""
        try:
            return await security_users_collection.count_documents({})
        except Exception as e:
            logger.error(f"Failed to count users: {e}")
            raise

    @staticmethod
    async def count_admins() -> int:
        """Count total users"""
        try:
            return await security_users_collection.count_documents({"role":"admin"})
        except Exception as e:
            logger.error(f"Failed to count admins: {e}")
            raise
    
    @staticmethod
    async def get_all_users() -> list:
        """Get all users"""
        try:
            cursor = security_users_collection.find({})
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"Failed to get all users: {e}")
            raise
    
    @staticmethod
    async def delete_user(user_id: str) -> bool:
        """Delete user by user_id"""
        try:
            result = await security_users_collection.delete_one({"user_id": user_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete user: {e}")
            raise

    @staticmethod
    async def insert_otp(email: str, otp: str) -> bool:
        """Insert OTP for an email and make it expire after 15 minutes."""
        try:
            result = await otp_collection.insert_one({
                "email": email,
                "otp": otp,
                "created_at": datetime.utcnow()
            })
            return result.acknowledged
        except Exception as e:
            logger.error(f"Failed to save OTP: {e}")
            raise

    @staticmethod
    async def verify_otp(email: str, otp: str) -> bool:
        """Verify otp for a specific email address"""
        try:
            result = await otp_collection.find_one({
                "email": email
            })
            if (result and result['otp'] == otp):
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"OTP error: {e}")
            raise

    @staticmethod
    async def delete_otp(email: str) -> bool:
        """Delete used otp"""
        try:
            return otp_collection.delete_one({"email": email})
        except Exception as e:
            logger.error(f"OTP error: {e}")
            raise

    @staticmethod
    async def update_user_password(user_id: str, password: str) -> bool:
        """Delete used otp"""
        try:
            return security_users_collection.update_one(
                {"user_id": user_id},     
                {"$set": {"password_hash": password}}
            )
        except Exception as e:
            logger.error(f"OTP error: {e}")
            raise
