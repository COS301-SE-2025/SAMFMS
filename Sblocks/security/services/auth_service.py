from repositories.user_repository import UserRepository
from repositories.audit_repository import AuditRepository, TokenRepository
from utils.auth_utils import (
    verify_password, get_password_hash, create_access_token, 
    verify_access_token, get_role_permissions, ROLES
)
from config.settings import settings
from models.api_models import TokenResponse
from models.database_models import UserCreatedMessage
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import uuid
import logging
import hashlib

logger = logging.getLogger(__name__)


class AuthService:
    """Service layer for authentication operations"""

    @staticmethod
    async def get_user_role(user_id: str):
        """Retrieve a user's role by user_id"""
        try:
            user = await UserRepository.find_by_user_id(user_id)
            if user and "role" in user:
                return user["role"]
            return None
        except Exception as e:
            logger.error(f"Get user role error: {e}")
            return None

    @staticmethod
    async def update_user_password(user_id: str, new_password: str):
        """Update a user's password"""
        try:
            hashed_password = get_password_hash(new_password)
            return await UserRepository.update_user_password(user_id, hashed_password)
        except Exception as e:
            logger.error(f"Update user password error: {e}")
            return False

    @staticmethod
    async def update_user_role(user_id: str, new_role: str):
        """Update a user's role"""
        try:
            return await UserRepository.update_user_role(user_id, new_role)
        except Exception as e:
            logger.error(f"Update user role error: {e}")
            return False

    @staticmethod
    async def is_token_valid(token: str):
        """Check if a token is valid and not blacklisted"""
        try:
            payload = verify_access_token(token)
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            if await TokenRepository.is_token_blacklisted(token_hash):
                return False
            return True
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return False

    @staticmethod
    async def get_user_by_email(email: str):
        """Retrieve user details by email"""
        try:
            return await UserRepository.find_by_email(email)
        except Exception as e:
            logger.error(f"Get user by email error: {e}")
            return None

    @staticmethod
    async def reset_failed_login_attempts(user_id: str):
        """Reset failed login attempts for a user"""
        try:
            return await UserRepository.reset_failed_attempts(user_id)
        except Exception as e:
            logger.error(f"Reset failed login attempts error: {e}")
            return False

    @staticmethod
    async def force_logout_user(user_id: str):
        """Force logout a user by invalidating all tokens (set force_logout_after)"""
        try:
            from datetime import datetime
            return await UserRepository.set_force_logout_after(user_id, datetime.utcnow())
        except Exception as e:
            logger.error(f"Force logout user error: {e}")
            return False

    @staticmethod
    async def get_all_users():
        """Retrieve all users (admin functionality)"""
        try:
            return await UserRepository.get_all_users()
        except Exception as e:
            logger.error(f"Get all users error: {e}")
            return []

    @staticmethod
    async def get_user_permissions(user_id: str):
        """Retrieve a user's permissions by user_id"""
        try:
            user = await UserRepository.find_by_user_id(user_id)
            if user and "permissions" in user:
                return user["permissions"]
            return []
        except Exception as e:
            logger.error(f"Get user permissions error: {e}")
            return []
    
    @staticmethod
    async def signup_user(user_data: Dict[str, Any]) -> TokenResponse:
        """Handle user signup"""
        try:
            # Generate unique user ID
            user_id = str(uuid.uuid4())
            
            # Check if first user (becomes admin)
            user_count = await UserRepository.count_users()
            is_first_user = user_count == 0
            
            # Determine role
            if is_first_user:
                role = settings.DEFAULT_FIRST_USER_ROLE
                approved = True
            else:
                role = user_data.get("role") or settings.DEFAULT_USER_ROLE
                approved = role == "admin"  # Admin users auto-approved
            
            # Get permissions for role
            permissions = get_role_permissions(role, user_data.get("custom_permissions"))
            
            # Hash password
            hashed_password = get_password_hash(user_data["password"])
              # Get default preferences if not provided
            default_preferences = {
                "theme": "light",
                "animations": "true",
                "email_alerts": "true",
                "push_notifications": "true",
                "two_factor": "false",
                "activity_log": "true",
                "session_timeout": "30 minutes"
            }
            preferences = user_data.get("preferences", {})
            if not preferences:
                preferences = default_preferences
            
            # Prepare user data for database
            db_user_data = {
                "user_id": user_id,
                "email": user_data["email"],
                "phone": user_data["phone"],
                "password_hash": hashed_password,
                "role": role,
                "permissions": permissions,
                "is_active": True,
                "approved": approved,
                "failed_login_attempts": 0,
                "full_name": user_data["full_name"],
                "created_at": datetime.utcnow()
            }
            
            # Create user in database
            await UserRepository.create_user(db_user_data)
            
            # Log security event
            await AuditRepository.log_security_event(
                user_id=user_id,
                action="user_signup",
                details={
                    "email": user_data["email"],
                    "role": role,
                    "is_first_user": is_first_user
                }
            )
            
            # Create access token
            token_data = {
                "sub": user_id,
                "role": role,
                "permissions": permissions,
                "issued_at": datetime.utcnow().timestamp()
            }
            access_token = create_access_token(token_data)
            
            return TokenResponse(
                access_token=access_token,
                token_type="bearer",
                user_id=user_id,
                role=role,
                permissions=permissions,
                preferences=preferences
            )
        except Exception as e:
            logger.error(f"Signup error: {e}")
            raise
    
    @staticmethod
    async def login_user(email: str, password: str, client_ip: str) -> TokenResponse:
        """Handle user login"""
        try:
            # Get user by email
            security_user = await UserRepository.find_by_email(email)
            if not security_user:
                await AuditRepository.log_security_event(
                    user_id="unknown",
                    action="failed_login_attempt",
                    details={
                        "email": email,
                        "reason": "user_not_found",
                        "ip_address": client_ip
                    }
                )
                raise ValueError("Incorrect email or password")
            
            # Check rate limiting
            if security_user.get("failed_login_attempts", 0) >= settings.LOGIN_ATTEMPT_LIMIT:
                await AuditRepository.log_security_event(
                    user_id=security_user["user_id"],
                    action="login_blocked",
                    details={
                        "reason": "too_many_attempts",
                        "ip_address": client_ip
                    }
                )
                raise ValueError("Too many failed login attempts. Please try again later.")
            
            # Check if account is active
            if not security_user.get("is_active", True):
                await AuditRepository.log_security_event(
                    user_id=security_user["user_id"],
                    action="failed_login_attempt",
                    details={
                        "reason": "account_disabled",
                        "ip_address": client_ip
                    }
                )
                raise ValueError("Account is disabled")
            
            # Verify password
            if not verify_password(password, security_user["password_hash"]):
                # Increment failed login attempts
                await UserRepository.increment_failed_attempts(security_user["user_id"])
                
                await AuditRepository.log_security_event(
                    user_id=security_user["user_id"],
                    action="failed_login_attempt",
                    details={
                        "reason": "invalid_password",
                        "ip_address": client_ip
                    }
                )
                raise ValueError("Incorrect email or password")
            
            # Reset failed attempts and update last login
            await UserRepository.reset_failed_attempts(security_user["user_id"])
            
            # Create access token
            token_data = {
                "sub": security_user["user_id"],
                "role": security_user["role"],
                "permissions": security_user["permissions"],
                "issued_at": datetime.utcnow().timestamp()
            }
            access_token = create_access_token(token_data)
              # Get user preferences or use default preferences
            preferences = security_user.get("preferences", {})
            if not preferences:
                # Get default preferences
                preferences = {
                    "theme": "light",
                    "animations": "true",
                    "email_alerts": "true",
                    "push_notifications": "true",
                    "two_factor": "false",
                    "activity_log": "true",
                    "session_timeout": "30 minutes"
                }
            
            # Log successful login
            await AuditRepository.log_security_event(
                user_id=security_user["user_id"],
                action="successful_login",
                details={"ip_address": client_ip}
            )
            
            return TokenResponse(
                access_token=access_token,
                token_type="bearer",
                user_id=security_user["user_id"],
                role=security_user["role"],
                permissions=security_user["permissions"],
                preferences=preferences
            )
        except Exception as e:
            logger.error(f"Login error: {e}")
            raise
    
    @staticmethod
    async def get_current_user_secure(token: str):
        """Get current user with security checks"""
        try:
            # Verify token
            payload = verify_access_token(token)
            user_id = payload["user_id"]
            token_str = payload.get("token", token)
            
            # Check if token is blacklisted
            token_hash = hashlib.sha256(token_str.encode()).hexdigest()
            if await TokenRepository.is_token_blacklisted(token_hash):
                raise ValueError("Token has been revoked")
            
            # Get user from security database
            security_user = await UserRepository.find_by_user_id(user_id)
            if not security_user:
                raise ValueError("User not found")
            
            if not security_user.get("is_active", True):
                raise ValueError("User account is disabled")
            
            # Check if user was force logged out after token was issued
            force_logout_after = security_user.get("force_logout_after")
            if force_logout_after and payload.get("issued_at"):
                token_issued = datetime.fromtimestamp(payload["issued_at"])
                if token_issued < force_logout_after:
                    raise ValueError("Token invalidated due to security action")
            
            # Add token to user data for logout functionality
            security_user["token"] = token_str
            return security_user
            
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            raise
    
    @staticmethod
    async def logout_user(token: str):
        """Handle user logout by blacklisting token"""
        try:
            payload = verify_access_token(token)
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            
            # Calculate token expiry from payload
            exp_timestamp = payload.get("exp")
            if exp_timestamp:
                expires_at = datetime.fromtimestamp(exp_timestamp)
                await TokenRepository.blacklist_token(token_hash, expires_at)
            
            await AuditRepository.log_security_event(
                user_id=payload["user_id"],
                action="user_logout",
                details={}
            )
        except Exception as e:
            logger.error(f"Logout error: {e}")
            raise
