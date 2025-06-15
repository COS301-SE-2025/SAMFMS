from fastapi import APIRouter, HTTPException, Depends, status, Request, File, UploadFile, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models import (
    SignupRequest, InviteUserRequest, LoginRequest, TokenResponse, MessageResponse,
    ChangePasswordRequest, UpdatePermissionsRequest, SecurityUser, UserCreatedMessage,
    UserDeletedMessage, UserResponse, ProfileUpdateRequest, ProfilePictureResponse,
    PreferencesUpdateRequest
)
from auth_utils import (
    verify_password, get_password_hash, create_access_token,
    verify_access_token, get_current_user, get_role_permissions,
    require_role, require_permission, has_permission, ROLES, DEFAULT_FIRST_USER_ROLE,
    ACCESS_TOKEN_EXPIRE_MINUTES, create_refresh_token, verify_refresh_token,
    LOGIN_ATTEMPT_LIMIT, SECRET_KEY, ALGORITHM
)
from database import (
    security_users_collection, test_database_connection,
    log_security_event, blacklist_token, is_token_blacklisted,
    blacklist_all_user_tokens, get_security_metrics, audit_logs_collection
)
from message_queue import mq_service
from bson import ObjectId
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from jose import jwt
import logging
import uuid
import requests
import os
import shutil

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()

# User profile data is now stored directly in the security_users_collection
# No need for a separate Users Dblock service URL

# Path for storing profile pictures
PROFILE_PICTURES_DIR = os.path.join(os.getcwd(), "profile_pictures")
# Create directory if it doesn't exist
os.makedirs(PROFILE_PICTURES_DIR, exist_ok=True)

# Public URL for accessing profile pictures
# Use relative URL instead of absolute URL for better compatibility
PROFILE_PICTURES_URL = os.getenv("PROFILE_PICTURES_URL", "/static/profile_pictures")


async def get_current_user(token: str = Depends(security)):
    """Get current user from JWT token with blacklist checking"""
    try:
        # Verify token
        payload = verify_access_token(token.credentials)
        user_id = payload["user_id"]
        token_str = payload.get("token", token.credentials)
        
        # Check if token is blacklisted
        import hashlib
        token_hash = hashlib.sha256(token_str.encode()).hexdigest()
        if await is_token_blacklisted(token_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked"
            )
        
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
        
        # Check if user was force logged out after token was issued
        force_logout_after = security_user.get("force_logout_after")
        if force_logout_after and payload.get("issued_at"):
            token_issued = datetime.fromtimestamp(payload["issued_at"])
            if token_issued < force_logout_after:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token invalidated due to security action"
                )
        
        # Add token to payload for logout functionality
        security_user["token"] = token_str
        return security_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


@router.post("/signup", response_model=TokenResponse)
async def signup(user_data: SignupRequest, request: Request):
    """Create a new user account - only allows first user to become admin"""
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
        
        # Only allow signup for the first user
        if not is_first_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Direct signup is not allowed. Please contact an administrator to create an account."
            )
        
        # Generate unique user ID
        user_id = str(uuid.uuid4())
        
        # Hash the password
        hashed_password = get_password_hash(user_data.password)
          # First user is always admin
        role = DEFAULT_FIRST_USER_ROLE  # "admin"
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
            }        # Create security user record
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
            "preferences": user_preferences,
            "full_name": user_data.full_name  # Add full_name to the security user data
        }
        
        # Insert security data
        await security_users_collection.insert_one(security_user_data)
          # Prepare default preferences if none provided
        user_preferences = user_data.preferences
            
            
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


LOGIN_ATTEMPT_LIMIT = 5  # Maximum failed login attempts before blocking

@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest, request: Request):
    """Authenticate user and return access token"""
    try:
        # Rate limiting check
        client_ip = str(request.client.host)
        
        # Get user by email
        security_user = await security_users_collection.find_one({"email": login_data.email})
        if not security_user:
            await log_security_event(
                user_id="unknown",
                action="failed_login_attempt",
                details={
                    "email": login_data.email,
                    "reason": "user_not_found",
                    "ip_address": client_ip
                }
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Check rate limiting - if too many failed attempts
        failed_attempts = security_user.get("failed_login_attempts", 0)
        if failed_attempts >= LOGIN_ATTEMPT_LIMIT:
            await log_security_event(
                user_id=security_user["user_id"],
                action="login_blocked",
                details={
                    "reason": "too_many_attempts",
                    "ip_address": client_ip
                }
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many failed login attempts. Please try again later."
            )

        # Check if account is active
        if not security_user.get("is_active", True):
            await log_security_event(
                user_id=security_user["user_id"],
                action="failed_login_attempt",
                details={
                    "reason": "account_disabled",
                    "ip_address": client_ip
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
                    "ip_address": client_ip
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
        
        # Create refresh token
        refresh_token = create_refresh_token(security_user["user_id"])
        
        # Log successful login
        await log_security_event(
            user_id=security_user["user_id"],
            action="successful_login",
            details={"ip_address": client_ip}
        )
        
        # Fetch user preferences
        preferences = await get_user_preferences(security_user["user_id"])
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=security_user["user_id"],
            role=security_user["role"],
            permissions=user_permissions,
            preferences=preferences,
            refresh_token=refresh_token
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login error: {str(e)}"
        )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: dict = Depends(get_current_user),
    request: Request = None
):
    """Logout user and invalidate token"""
    try:
        user_id = current_user["user_id"]
        token = current_user.get("token")
        
        if token:
            # Hash the token for blacklist storage
            import hashlib
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            
            # Get token expiration from JWT payload
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
            exp_timestamp = payload.get("exp")
            expires_at = datetime.fromtimestamp(exp_timestamp) if exp_timestamp else datetime.utcnow() + timedelta(hours=1)
            
            # Add token to blacklist
            await blacklist_token(token_hash, expires_at, user_id)
        
        # Log logout event
        await log_security_event(
            user_id=user_id,
            action="user_logout",
            details={"ip_address": str(request.client.host) if request else None}
        )
        
        return MessageResponse(message="Successfully logged out")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout error: {str(e)}"
        )


@router.post("/logout-all", response_model=MessageResponse)
async def logout_all_devices(
    current_user: dict = Depends(get_current_user),
    request: Request = None
):
    """Logout user from all devices"""
    try:
        user_id = current_user["user_id"]
        
        # Blacklist all tokens for this user
        await blacklist_all_user_tokens(user_id)
        
        # Log logout all event
        await log_security_event(
            user_id=user_id,
            action="user_logout_all_devices",
            details={"ip_address": str(request.client.host) if request else None}
        )
        
        return MessageResponse(message="Successfully logged out from all devices")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout all error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout all error: {str(e)}"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(refresh_token_data: dict):
    """Refresh access token using refresh token"""
    try:
        refresh_token = refresh_token_data.get("refresh_token")
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refresh token is required"
            )
        
        # Verify refresh token
        user_id = verify_refresh_token(refresh_token)
        
        # Check if refresh token is blacklisted
        import hashlib
        refresh_token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        if await is_token_blacklisted(refresh_token_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked"
            )
        
        # Get user data
        security_user = await security_users_collection.find_one({"user_id": user_id})
        if not security_user or not security_user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new access token
        user_permissions = security_user.get("custom_permissions") or security_user.get("permissions", [])
        access_token = create_access_token(
            data={
                "sub": user_id,
                "role": security_user["role"],
                "permissions": user_permissions
            }
        )
        
        # Create new refresh token and blacklist the old one
        new_refresh_token = create_refresh_token(user_id)
        
        # Blacklist old refresh token
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
        exp_timestamp = payload.get("exp")
        expires_at = datetime.fromtimestamp(exp_timestamp) if exp_timestamp else datetime.utcnow() + timedelta(days=7)
        await blacklist_token(refresh_token_hash, expires_at, user_id)
        
        # Log token refresh
        await log_security_event(
            user_id=user_id,
            action="token_refreshed",
            details={}
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=user_id,
            role=security_user["role"],
            permissions=user_permissions,
            refresh_token=new_refresh_token
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh error: {str(e)}"
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


@router.post("/add-user", response_model=MessageResponse)
async def add_user(
    invite_data: InviteUserRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Admin can add any user, Fleet Managers can add only drivers"""
    try:
        # Verify current user has permission to add users
        current_user = verify_access_token(credentials.credentials)
        
        # Check if user has permission to add users
        if current_user["role"] == "admin":
            # Admin can add admins, fleet managers and drivers
            allowed_roles = ["admin", "fleet_manager", "driver"]
        elif current_user["role"] == "fleet_manager":
            # Fleet managers can only add drivers
            allowed_roles = ["driver"]
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to add users"
            )
        
        if invite_data.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You can only add users with roles: {allowed_roles}"
            )
        
        # Check if user already exists
        existing_user = await security_users_collection.find_one({"email": invite_data.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Use the provided password
        password = invite_data.password
        user_id = str(uuid.uuid4())
        
        # Hash the password
        hashed_password = get_password_hash(password)
        
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
            "requires_password_change": False,
            "created_by": current_user["user_id"],
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
            action="user_added",
            details={
                "added_user_id": user_id,
                "email": invite_data.email,
                "role": invite_data.role
            }
        )
        
        return MessageResponse(
            message=f"User {invite_data.full_name} added successfully with role: {invite_data.role}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Add user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding user: {str(e)}"
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
    """Get user preferences from security_users_collection"""
    try:
        # Get user document from the security_users_collection
        user_doc = await security_users_collection.find_one({"user_id": user_id})
        if user_doc and "preferences" in user_doc:
            return user_doc.get("preferences", {})
        else:
            logger.warning(f"User preferences not found for user_id: {user_id}")
            return {}
    except Exception as e:
        logger.error(f"Error fetching user preferences: {e}")
        return {}


@router.post("/invite-user", response_model=MessageResponse)
async def invite_user_redirect(
    invite_data: InviteUserRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Redirect old invite-user endpoint to the new add-user endpoint for backward compatibility"""
    # Simply call the add_user function with the same parameters
    return await add_user(invite_data, credentials)


@router.get("/user-exists")
async def check_user_existence():
    """Check if any users exist in the system"""
    try:
        # Count users in the security database
        user_count = await security_users_collection.count_documents({})
        return {"userExists": user_count > 0}
    except Exception as e:
        logger.error(f"Error checking user existence: {e}")
        # Default to true as a security precaution
        return {"userExists": True}


@router.get("/users/count")
async def get_user_count():
    """Get the count of users in the system"""
    try:
        # Count users in the security database
        user_count = await security_users_collection.count_documents({})
        return {"count": user_count}
    except Exception as e:
        logger.error(f"Error counting users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error counting users: {str(e)}"
        )


# The first update-profile endpoint was removed to avoid conflicts
# Now using the implementation below that updates the security_users_collection directly


@router.post("/upload-profile-picture", response_model=ProfilePictureResponse)
async def upload_profile_picture(
    profile_picture: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    request: Request = None
):
    """Upload and update user profile picture"""
    try:
        # Validate file type
        valid_content_types = ["image/jpeg", "image/png", "image/jpg"]
        if profile_picture.content_type not in valid_content_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only JPEG and PNG files are allowed"
            )        # Create directory for profile pictures if it doesn't exist
        upload_dir = os.path.join("static", "profile_pictures")
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename with timestamp to prevent caching
        timestamp = int(datetime.now().timestamp())
        file_extension = os.path.splitext(profile_picture.filename)[1]
        unique_filename = f"{current_user['user_id']}_{timestamp}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Save the file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(profile_picture.file, buffer)
          # Generate URL for the profile picture
        profile_picture_url = f"{PROFILE_PICTURES_URL}/{unique_filename}"
        
        # Update user record with profile picture URL
        result = await security_users_collection.update_one(
            {"user_id": current_user["user_id"]},
            {"$set": {"profile_picture_url": profile_picture_url}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Log profile picture update
        await log_security_event(
            user_id=current_user["user_id"],
            action="profile_picture_updated",
            details={
                "file_type": profile_picture.content_type,
                "ip_address": str(request.client.host) if request else None
            }
        )
        
        return ProfilePictureResponse(
            message="Profile picture updated successfully",
            profile_picture_url=profile_picture_url
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile picture upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading profile picture: {str(e)}"
        )


@router.post("/update-profile")
async def update_profile(
    profile_data: ProfileUpdateRequest,
    current_user: dict = Depends(get_current_user),
    request: Request = None
):
    """Update user profile information"""
    try:
        # Prepare update data
        update_data = {}
          # Only include non-None fields in the update
        if profile_data.phoneNo is not None:
            update_data["phoneNo"] = profile_data.phoneNo
            
        if profile_data.full_name is not None:
            update_data["full_name"] = profile_data.full_name
            
        if not update_data:
            return MessageResponse(message="No changes to update")
        
        # Update user in database
        result = await security_users_collection.update_one(
            {"user_id": current_user["user_id"]},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Log profile update
        await log_security_event(
            user_id=current_user["user_id"],
            action="profile_updated",
            details={
                "fields_updated": list(update_data.keys()),
                "ip_address": str(request.client.host) if request else None
            }
        )
        
        # Return updated user data
        updated_user = await security_users_collection.find_one({"user_id": current_user["user_id"]})
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found after update"
            )
            
        # Create response with updated fields
        response_data = {
            "message": "Profile updated successfully",
        }
        
        # Add updated fields to response
        for key in update_data:
            response_data[key] = updated_user.get(key)
            
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating profile: {str(e)}"
        )


@router.post("/update-preferences", response_model=MessageResponse)
async def update_preferences(
    preferences_data: PreferencesUpdateRequest,
    current_user: dict = Depends(get_current_user),
    request: Request = None
):
    """Update user preferences"""
    try:
        user_id = current_user["user_id"]
        
        # Get the current security user
        security_user = await security_users_collection.find_one({"user_id": user_id})
        if not security_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        # Update the preferences in the user record
        security_user["preferences"] = preferences_data.preferences
        
        # Update the security user record
        result = await security_users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"preferences": preferences_data.preferences}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
          # No need to update preferences in a separate service - 
        # Security service already stores preferences directly in the security_users_collection
        
        # Log preferences update
        await log_security_event(
            user_id=user_id,
            action="preferences_updated",
            details={
                "ip_address": str(request.client.host) if request else None
            }
        )
        
        return MessageResponse(message="Preferences updated successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating preferences: {str(e)}"
        )


@router.get("/security-metrics")
async def get_security_metrics_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get security metrics - admin only"""
    try:
        # Verify current user is admin
        current_user = verify_access_token(credentials.credentials)
        if current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can access security metrics"
            )
        
        metrics = await get_security_metrics()
        return {
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Security metrics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving security metrics: {str(e)}"
        )


@router.get("/audit-logs")
async def get_audit_logs(
    limit: int = 100,
    offset: int = 0,
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get audit logs - admin only"""
    try:
        # Verify current user is admin
        current_user = verify_access_token(credentials.credentials)
        if current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can access audit logs"
            )
        
        # Build query
        query = {}
        if user_id:
            query["user_id"] = user_id
        if action:
            query["action"] = action
        
        # Get logs with pagination
        cursor = audit_logs_collection.find(query).sort("timestamp", -1).skip(offset).limit(limit)
        logs = []
        async for log in cursor:
            # Convert ObjectId to string for JSON serialization
            log["_id"] = str(log["_id"])
            logs.append(log)
        
        total = await audit_logs_collection.count_documents(query)
        
        return {
            "logs": logs,
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audit logs error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving audit logs: {str(e)}"
        )


@router.post("/refresh-token", response_model=TokenResponse)
async def refresh_token(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Refresh access token using refresh token"""
    try:
        # Verify refresh token
        refresh_token = credentials.credentials
        
        try:
            payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
            token_type = payload.get("type")
            user_id = payload.get("sub")
            
            if token_type != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
                
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Check if refresh token is blacklisted
        import hashlib
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        if await is_token_blacklisted(token_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked"
            )
        
        # Get user from database
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
        
        # Create new access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        user_permissions = security_user.get("custom_permissions") or security_user.get("permissions", [])
        access_token = create_access_token(
            data={
                "sub": user_id,
                "role": security_user["role"],
                "permissions": user_permissions
            },
            expires_delta=access_token_expires
        )
        
        # Create new refresh token (refresh token rotation)
        new_refresh_token = create_refresh_token(user_id)
        
        # Blacklist old refresh token
        old_token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        refresh_exp = datetime.fromtimestamp(payload.get("exp", 0))
        await blacklist_token(old_token_hash, refresh_exp, user_id)
        
        # Log token refresh event
        await log_security_event(
            user_id=user_id,
            action="token_refresh",
            details={
                "ip_address": str(request.client.host),
                "user_agent": request.headers.get("user-agent")
            }
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=user_id,
            role=security_user["role"],
            permissions=user_permissions,
            preferences=security_user.get("preferences", {}),
            refresh_token=new_refresh_token
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )
