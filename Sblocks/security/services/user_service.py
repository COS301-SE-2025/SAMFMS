from repositories.user_repository import UserRepository
from repositories.audit_repository import AuditRepository
from models.database_models import UserCreatedMessage, UserUpdatedMessage, UserDeletedMessage
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class UserService:
    """Service layer for user management operations"""
    
    @staticmethod
    async def get_all_users() -> List[Dict[str, Any]]:
        """Get all users"""
        try:
            users = await UserRepository.get_all_users()
            # Remove sensitive data
            for user in users:
                user.pop("password_hash", None)
                user.pop("_id", None)
            return users
        except Exception as e:
            logger.error(f"Failed to get all users: {e}")
            raise
    
    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            user = await UserRepository.find_by_user_id(user_id)
            if user:
                user.pop("password_hash", None)
                user.pop("_id", None)
            return user
        except Exception as e:
            logger.error(f"Failed to get user by ID: {e}")
            raise
    
    @staticmethod
    async def update_user_permissions(user_id: str, role: Optional[str] = None, 
                                    custom_permissions: Optional[List[str]] = None) -> bool:
        """Update user permissions"""
        try:
            updates = {}
            if role:
                from utils.auth_utils import get_role_permissions
                updates["role"] = role
                updates["permissions"] = get_role_permissions(role, custom_permissions)
            elif custom_permissions:
                updates["permissions"] = custom_permissions
            
            if updates:
                success = await UserRepository.update_user(user_id, updates)
                if success:
                    await AuditRepository.log_security_event(
                        user_id=user_id,
                        action="permissions_updated",
                        details=updates
                    )
                return success
            return False
        except Exception as e:
            logger.error(f"Failed to update user permissions: {e}")
            raise
    
    @staticmethod
    async def update_user_profile(user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user profile information"""
        try:
            # Remove sensitive fields
            safe_updates = {k: v for k, v in updates.items() 
                          if k not in ["password_hash", "user_id", "_id"]}
            
            if safe_updates:
                success = await UserRepository.update_user(user_id, safe_updates)
                if success:
                    await AuditRepository.log_security_event(
                        user_id=user_id,
                        action="profile_updated",
                        details={"fields": list(safe_updates.keys())}
                    )
                return success
            return False
        except Exception as e:
            logger.error(f"Failed to update user profile: {e}")
            raise
    
    @staticmethod
    async def delete_user(user_id: str, deleted_by: str) -> bool:
        """Delete user"""
        try:
            success = await UserRepository.delete_user(user_id)
            if success:
                await AuditRepository.log_security_event(
                    user_id=user_id,
                    action="user_deleted",
                    details={"deleted_by": deleted_by}
                )
            return success
        except Exception as e:
            logger.error(f"Failed to delete user: {e}")
            raise
    
    @staticmethod
    async def change_user_password(user_id: str, current_password: str, new_password: str) -> bool:
        """Change user password"""
        try:
            from utils.auth_utils import verify_password, get_password_hash
            
            # Get current user
            user = await UserRepository.find_by_user_id(user_id)
            if not user:
                raise ValueError("User not found")
            
            # Verify current password
            if not verify_password(current_password, user["password_hash"]):
                raise ValueError("Current password is incorrect")
            
            # Hash new password
            new_password_hash = get_password_hash(new_password)
            
            # Update password
            success = await UserRepository.update_user(user_id, {
                "password_hash": new_password_hash
            })
            
            if success:
                await AuditRepository.log_security_event(
                    user_id=user_id,
                    action="password_changed",
                    details={}
                )
            
            return success
        except Exception as e:
            logger.error(f"Failed to change password: {e}")
            raise
    
    @staticmethod
    async def toggle_user_status(user_id: str, is_active: bool, modified_by: str) -> bool:
        """Activate or deactivate user"""
        try:
            success = await UserRepository.update_user(user_id, {
                "is_active": is_active
            })
            
            if success:
                action = "user_activated" if is_active else "user_deactivated"
                await AuditRepository.log_security_event(
                    user_id=user_id,
                    action=action,
                    details={"modified_by": modified_by}
                )
            
            return success
        except Exception as e:
            logger.error(f"Failed to toggle user status: {e}")
            raise
