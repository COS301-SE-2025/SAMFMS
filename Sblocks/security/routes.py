from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models import (
    SignupRequest, InviteUserRequest, LoginRequest, TokenResponse, MessageResponse,
    ChangePasswordRequest, UpdatePermissionsRequest, SecurityUser, UserCreatedMessage,
    UserDeletedMessage, UserResponse
)
from auth_utils import (
    verify_password, get_password_hash, create_access_token,
    verify_access_token, get_current_user, get_role_permissions,
    require_role, require_permission, ROLES, DEFAULT_FIRST_USER_ROLE,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from database import (
    security_users_collection, test_database_connection,
    log_security_event
)
from message_queue import mq_service
from bson import ObjectId
from datetime import datetime, timedelta
from typing import List, Dict
import logging
import uuid
import requests
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()

# Users Dblock service URL
USERS_DBLOCK_URL = os.getenv("USERS_DBLOCK_URL", "http://users_db_service:8009")


async def get_current_user(token: str = Depends(security)):
    """Get current user from JWT token"""
    try:
        # Verify token
        payload = verify_access_token(token.credentials)
        user_id = payload["user_id"]
        
        # Get user from security database
        security_user = await security_users_collection.find_one({"user_id": user_id})
        if not security_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if not security_user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled"
            )
        
        return security_user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


@router.post("/signup", response_model=TokenResponse)
async def signup(user_data: SignupRequest, request: Request):
    """Create a new user account - first user becomes admin, others need invitation"""
    try:
        # Check if user already exists
        existing_user = await security_users_collection.find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Check if this is the first user in the system
        user_count = await security_users_collection.count_documents({})
        is_first_user = user_count == 0
        
        if not is_first_user and not user_data.role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role assignment required. Please contact an administrator for access."
            )
        
        # Generate unique user ID
        user_id = str(uuid.uuid4())
        
        # Hash the password
        hashed_password = get_password_hash(user_data.password)
        
        # Determine role and permissions
        if is_first_user:
            role = DEFAULT_FIRST_USER_ROLE  # "admin"
            permissions = get_role_permissions(role)
        else:
            if user_data.role not in ROLES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid role. Valid roles: {list(ROLES.keys())}"
                )
            role = user_data.role
            permissions = get_role_permissions(role)
            
        user_preferences = {
            "theme": "light",
            "animations": "true",
            "email_alerts": "true",
            "push_notifications": "true",
            "timezone": "UTC-5 (Eastern Time)",
            "date_format": "DD/MM/YYYY",
            "two_factor": "false",
            "activity_log": "true",
            "session_timeout": "30 minutes"
        }
        # Create security user record
        security_user_data = {
            "user_id": user_id,
            "email": user_data.email,
            "password_hash": hashed_password,
            "role": role,
            "is_active": True,
            "failed_login_attempts": 0,
            "two_factor_enabled": False,
            "permissions": permissions,
            "custom_permissions": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "user_preferences": user_data.preferences
        }
        
        # Insert security data
        await security_users_collection.insert_one(security_user_data)
          # Prepare default preferences if none provided
        
            
        # Publish user profile data to Users Dblock via message queue
        profile_message = UserCreatedMessage(
            user_id=user_id,
            full_name=user_data.full_name,
            phoneNo=user_data.phoneNo,
            details=user_data.details,
            preferences=user_preferences
        )
        
        if mq_service.connection:
            mq_service.publish_user_created(profile_message)
        else:
            logger.warning("Message queue not available, user profile not synchronized")
        
        # Create access token with role and permissions
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": user_id,
                "role": role,
                "permissions": permissions
            },
            expires_delta=access_token_expires
        )
        
        # Log security event
        await log_security_event(
            user_id=user_id,
            action="user_signup",
            details={
                "ip_address": str(request.client.host),
                "role": role,
                "is_first_user": is_first_user
            }
        )          
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=user_id,
            role=role,
            permissions=permissions,
            preferences=user_preferences
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )


@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest, request: Request):
    """Authenticate user and return access token"""
    try:
        # Get user by email
        security_user = await security_users_collection.find_one({"email": login_data.email})
        if not security_user:
            await log_security_event(
                user_id="unknown",
                action="failed_login_attempt",
                details={
                    "email": login_data.email,
                    "reason": "user_not_found",
                    "ip_address": str(request.client.host)
                }
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Check if account is active
        if not security_user.get("is_active", True):
            await log_security_event(
                user_id=security_user["user_id"],
                action="failed_login_attempt",
                details={
                    "reason": "account_disabled",
                    "ip_address": str(request.client.host)
                }
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is disabled"
            )
        
        # Verify password
        if not verify_password(login_data.password, security_user["password_hash"]):
            # Increment failed login attempts
            await security_users_collection.update_one(
                {"_id": security_user["_id"]},
                {"$inc": {"failed_login_attempts": 1}}
            )
            
            await log_security_event(
                user_id=security_user["user_id"],
                action="failed_login_attempt",
                details={
                    "reason": "invalid_password",
                    "ip_address": str(request.client.host)
                }
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Reset failed login attempts and update last login
        await security_users_collection.update_one(
            {"_id": security_user["_id"]},
            {
                "$set": {
                    "last_login": datetime.utcnow(),
                    "failed_login_attempts": 0
                }
            }
        )
          # Create access token with role and permissions
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        user_permissions = security_user.get("custom_permissions") or security_user.get("permissions", [])
        access_token = create_access_token(
            data={
                "sub": security_user["user_id"],
                "role": security_user["role"],
                "permissions": user_permissions
            },
            expires_delta=access_token_expires
        )
        
        # Log successful login
        await log_security_event(
            user_id=security_user["user_id"],
            action="successful_login",
            details={"ip_address": str(request.client.host)}
        )
          # Fetch user preferences from Users Dblock
        preferences = await get_user_preferences(security_user["user_id"])
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=security_user["user_id"],
            role=security_user["role"],
            permissions=user_permissions,
            preferences=preferences
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login error: {str(e)}"
        )


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    request: Request = None
):
    """Change user password"""
    try:
        # Verify current password
        if not verify_password(password_data.current_password, current_user["password_hash"]):
            await log_security_event(
                user_id=current_user["user_id"],
                action="failed_password_change",
                details={
                    "reason": "invalid_current_password",
                    "ip_address": str(request.client.host) if request else None
                }
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect"
            )
        
        # Hash new password
        new_hashed_password = get_password_hash(password_data.new_password)
        
        # Update password in database
        result = await security_users_collection.update_one(
            {"user_id": current_user["user_id"]},
            {"$set": {"password_hash": new_hashed_password}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Log password change
        await log_security_event(
            user_id=current_user["user_id"],
            action="password_changed",
            details={"ip_address": str(request.client.host) if request else None}
        )
        
        return MessageResponse(message="Password changed successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error changing password: {str(e)}"
        )


@router.delete("/account", response_model=MessageResponse)
async def delete_account(
    current_user: dict = Depends(get_current_user),
    request: Request = None
):
    """Delete the current user's account"""
    try:
        user_id = current_user["user_id"]
        
        # Delete security user from database
        result = await security_users_collection.delete_one({"user_id": user_id})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Publish user deletion event to Users Dblock
        deletion_message = UserDeletedMessage(user_id=user_id)
        if mq_service.connection:
            mq_service.publish_user_deleted(deletion_message)
        
        # Log account deletion
        await log_security_event(
            user_id=user_id,
            action="account_deleted",
            details={"ip_address": str(request.client.host) if request else None}
        )
        
        return MessageResponse(message="Account deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Account deletion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting account: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information by combining security and profile data"""
    try:
        # Get profile data from Users Dblock service
        try:
            response = requests.get(
                f"{USERS_DBLOCK_URL}/users/{current_user['user_id']}",
                timeout=5
            )
            if response.status_code == 200:
                profile_data = response.json()
            else:
                profile_data = {}
        except Exception as e:
            logger.warning(f"Could not fetch profile data: {e}")
            profile_data = {}
        
        return UserResponse(
            id=current_user["user_id"],
            full_name=profile_data.get("full_name", ""),
            email=current_user["email"],
            role=current_user["role"],
            phoneNo=profile_data.get("phoneNo"),
            details=profile_data.get("details", {}),
            preferences=profile_data.get("preferences", {}),
            is_active=current_user.get("is_active", True),
            last_login=current_user.get("last_login")
        )
        
    except Exception as e:
        logger.error(f"Error fetching user info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user info: {str(e)}"
        )


@router.post("/verify-token")
async def verify_token(current_user: dict = Depends(get_current_user)):
    """Verify if a token is valid (for other services)"""
    return {
        "valid": True,
        "user_id": current_user["user_id"],
        "role": current_user["role"],
        "email": current_user["email"]
    }


@router.post("/invite-user", response_model=MessageResponse)
async def invite_user(
    invite_data: InviteUserRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Admin and Fleet Managers can invite new users to the system"""
    try:
        # Verify current user has permission to invite
        current_user = verify_access_token(credentials.credentials)
        
        # Check if user has permission to invite
        if current_user["role"] == "admin":
            # Admin can invite anyone
            allowed_roles = ["fleet_manager", "driver"]
        elif current_user["role"] == "fleet_manager":
            # Fleet managers can only invite drivers
            allowed_roles = ["driver"]
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to invite users"
            )
        
        if invite_data.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You can only invite users with roles: {allowed_roles}"
            )
        
        # Check if user already exists
        existing_user = await security_users_collection.find_one({"email": invite_data.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Generate temporary password (user will be required to change on first login)
        temp_password = f"temp_{uuid.uuid4().hex[:8]}"
        user_id = str(uuid.uuid4())
        
        # Hash the temporary password
        hashed_password = get_password_hash(temp_password)
        
        # Determine permissions
        if invite_data.custom_permissions and current_user["role"] == "admin":
            # Admin can assign custom permissions
            permissions = invite_data.custom_permissions
        else:
            # Use default role permissions
            permissions = get_role_permissions(invite_data.role)
        
        # Create security user record
        security_user_data = {
            "user_id": user_id,
            "email": invite_data.email,
            "password_hash": hashed_password,
            "role": invite_data.role,
            "is_active": True,
            "failed_login_attempts": 0,
            "two_factor_enabled": False,
            "permissions": permissions,
            "custom_permissions": invite_data.custom_permissions if current_user["role"] == "admin" else None,
            "requires_password_change": True,
            "invited_by": current_user["user_id"],
            "created_at": datetime.utcnow()
        }
        
        # Insert security data
        await security_users_collection.insert_one(security_user_data)
        
        # Publish user profile data to Users Dblock
        profile_message = UserCreatedMessage(
            user_id=user_id,
            full_name=invite_data.full_name,
            phoneNo=invite_data.phoneNo,
            details=invite_data.details,
            preferences=invite_data.preferences
        )
        
        if mq_service.connection:
            mq_service.publish_user_created(profile_message)
        else:
            logger.warning("Message queue not available, user profile not synchronized")
        
        # Log security event
        await log_security_event(
            user_id=current_user["user_id"],
            action="user_invited",
            details={
                "invited_user_id": user_id,
                "invited_email": invite_data.email,
                "invited_role": invite_data.role
            }
        )
        
        # In a real system, you'd send an email with temp password
        # For now, return it in the response (NOT recommended for production)
        return MessageResponse(
            message=f"User invited successfully. Temporary password: {temp_password} (User must change on first login)"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Invite user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inviting user: {str(e)}"
        )


@router.post("/update-permissions", response_model=MessageResponse)
async def update_user_permissions(
    permissions_data: UpdatePermissionsRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Admin can update user permissions and roles"""
    try:
        # Verify current user is admin
        current_user = verify_access_token(credentials.credentials)
        if current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can update user permissions"
            )
        
        # Find target user
        target_user = await security_users_collection.find_one({"user_id": permissions_data.user_id})
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Prepare update data
        update_data = {}
        
        if permissions_data.role:
            if permissions_data.role not in ROLES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid role. Valid roles: {list(ROLES.keys())}"
                )
            update_data["role"] = permissions_data.role
            # Update default permissions for the new role
            update_data["permissions"] = get_role_permissions(permissions_data.role)
        
        if permissions_data.custom_permissions is not None:
            update_data["custom_permissions"] = permissions_data.custom_permissions
        
        # Update user in database
        result = await security_users_collection.update_one(
            {"user_id": permissions_data.user_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Log permission change
        await log_security_event(
            user_id=current_user["user_id"],
            action="permissions_updated",
            details={
                "target_user_id": permissions_data.user_id,
                "changes": update_data
            }
        )
        
        return MessageResponse(message="User permissions updated successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update permissions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating permissions: {str(e)}"
        )


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Admin can list all users with their roles and permissions"""
    try:
        # Verify current user is admin
        current_user = verify_access_token(credentials.credentials)
        if current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can list users"
            )
        
        # Get all users from security collection
        users_cursor = security_users_collection.find({}, {
            "password_hash": 0  # Exclude password hash
        })
        
        users = []
        async for user in users_cursor:
            # Get user profile from Users Dblock (would need API call in real implementation)
            # For now, return basic info
            user_permissions = user.get("custom_permissions") or user.get("permissions", [])
            
            user_response = UserResponse(
                id=user["user_id"],
                full_name="Unknown",  # Would get from Users Dblock
                email=user["email"],
                role=user["role"],
                permissions=user_permissions,
                is_active=user.get("is_active", True),
                last_login=user.get("last_login")
            )
            users.append(user_response)
        
        return users
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List users error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing users: {str(e)}"
        )


@router.get("/roles", response_model=Dict)
async def get_available_roles():
    """Get available roles and their default permissions"""
    return ROLES


@router.post("/verify-permission")
async def verify_user_permission(
    permission: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Verify if current user has specific permission - used by other services"""
    try:
        user_info = verify_access_token(credentials.credentials)
        has_perm = has_permission(user_info["permissions"], permission)
        
        return {
            "user_id": user_info["user_id"],
            "role": user_info["role"],
            "permission": permission,
            "granted": has_perm
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Permission verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error verifying permission: {str(e)}"
        )


async def get_user_preferences(user_id: str) -> Dict:
    """Get user preferences from Users Dblock"""
    try:
        response = requests.get(f"{USERS_DBLOCK_URL}/users/{user_id}")
        if response.status_code == 200:
            user_data = response.json()
            return user_data.get("preferences", {})
        else:
            logger.warning(f"Failed to fetch user preferences from Users Dblock: {response.status_code}")
            return {}
    except Exception as e:
        logger.error(f"Error fetching user preferences: {e}")
        return {}
