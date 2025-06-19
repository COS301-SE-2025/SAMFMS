from repositories.user_repository import UserRepository
from repositories.audit_repository import AuditRepository
from models.database_models import UserCreatedMessage, UserUpdatedMessage, UserDeletedMessage, SecurityUser
from models.api_models import CreateUserRequest
from typing import Dict, Any, List, Optional
import logging
import uuid
from datetime import datetime

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
                user.pop("_id", None)                # Add 'id' field to match the UserResponse model
                if "user_id" in user and "id" not in user:
                    user["id"] = user["user_id"]
                # Ensure preferences are included, using default if missing
                if "preferences" not in user or not user["preferences"]:
                    user["preferences"] = {
                        "theme": "light",
                        "animations": "true",
                        "email_alerts": "true",
                        "push_notifications": "true",
                        "two_factor": "false",
                        "activity_log": "true",
                        "session_timeout": "30 minutes"
                    }
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
                # Add 'id' field to match the UserResponse model
                if "user_id" in user and "id" not in user:
                    user["id"] = user["user_id"]
                  # Ensure preferences are included, using default if missing
                if "preferences" not in user or not user["preferences"]:
                    user["preferences"] = {
                        "theme": "light",
                        "animations": "true",
                        "email_alerts": "true",
                        "push_notifications": "true",
                        "two_factor": "false",
                        "activity_log": "true",
                        "session_timeout": "30 minutes"
                    }
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
    async def update_user_preferences(user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user preferences"""
        try:
            logger.info(f"UserService.update_user_preferences called for user_id: {user_id}")
            logger.info(f"Preferences received: {preferences}")
              # Validate and sanitize preferences - only allow known preference keys
            valid_preference_keys = {
                "theme", "animations", "email_alerts", "push_notifications", 
                "two_factor", "activity_log", "session_timeout"
            }
            
            safe_preferences = {k: v for k, v in preferences.items() 
                              if k in valid_preference_keys}
            
            logger.info(f"Safe preferences after filtering: {safe_preferences}")
            
            if safe_preferences:
                logger.info(f"Calling UserRepository.update_user with user_id: {user_id}")
                success = await UserRepository.update_user(user_id, {"preferences": safe_preferences})
                logger.info(f"UserRepository.update_user returned: {success}")
                
                if success:
                    await AuditRepository.log_security_event(
                        user_id=user_id,
                        action="preferences_updated",
                        details={"preferences": list(safe_preferences.keys())}
                    )
                
                return success
            else:
                logger.warning(f"No valid preferences to update for user_id: {user_id}")
                return False
        except Exception as e:
            logger.error(f"Failed to update user preferences: {e}")
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

    @staticmethod
    async def create_user_manually(
        user_data: CreateUserRequest, 
        created_by_user_id: str
    ) -> Dict[str, Any]:
        """Admin can manually create a user without invitation flow"""
        try:
            # Add debug logging to see what data we received
            logger.info(f"User service received user_data: {user_data.dict() if user_data else 'None'}")
            
            # Validate that we have the required data
            if not user_data:
                raise ValueError("User data is missing or empty")
            # Check if user already exists
            existing_user = await UserRepository.find_by_email(user_data.email.lower())
            if existing_user:
                raise ValueError("User with this email already exists")            # Generate unique user ID
            user_id = str(uuid.uuid4())
            
            # Hash the password using the same method as regular signup
            from utils.auth_utils import get_password_hash
            password_hash = get_password_hash(user_data.password)
            
            # Create user in security database
            now = datetime.utcnow()
            security_user = SecurityUser(
                user_id=user_id,
                email=user_data.email.lower(),
                password_hash=password_hash,
                role=user_data.role,
                is_active=True,
                approved=True,
                full_name=user_data.full_name
            )
              # Get default preferences directly instead of creating empty UserProfile
            default_preferences = {
                "theme": "light",
                "animations": "true",
                "email_alerts": "true",
                "push_notifications": "true",
                "two_factor": "false",
                "activity_log": "true",
                "session_timeout": "30 minutes"
            }
            
            # Save to database
            await UserRepository.create_user(security_user.dict(exclude={"id"}))
            
            # Publish message for user creation to other services
            user_created_msg = UserCreatedMessage(
                user_id=user_id,
                full_name=user_data.full_name,
                phoneNo=user_data.phoneNo,
                details=user_data.details or {},
                preferences=default_preferences  # Include preferences in message
            )
            
            # Publish to message queue (would be implemented in a real system)
            # await rabbitmq_producer.publish_user_created(user_created_msg)
            
            # Log the creation event
            await AuditRepository.log_security_event(
                user_id=created_by_user_id,
                action="manual_user_created",
                details={
                    "created_user_id": user_id,
                    "email": user_data.email,
                    "role": user_data.role
                }
            )
            
            return {
                "message": "User created successfully",
                "user_id": user_id,
                "email": user_data.email,
                "role": user_data.role,
                "preferences": default_preferences  # Include preferences in response
            }
            
        except ValueError as e:
            logger.warning(f"Validation error creating user: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to create user manually: {str(e)}")
            raise
