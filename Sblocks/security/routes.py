from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer
from models import (
    SignupRequest, LoginRequest, TokenResponse, MessageResponse,
    ChangePasswordRequest, SecurityUser, UserCreatedMessage,
    UserDeletedMessage, UserResponse
)
from auth_utils import (
    verify_password, get_password_hash, create_access_token,
    verify_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
)
from database import (
    security_users_collection, test_database_connection,
    log_security_event
)
from message_queue import mq_service
from bson import ObjectId
from datetime import datetime, timedelta
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
    """Create a new user account with security data separation"""
    try:
        # Check if user already exists
        existing_user = await security_users_collection.find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Generate unique user ID
        user_id = str(uuid.uuid4())
        
        # Hash the password
        hashed_password = get_password_hash(user_data.password)
        
        # Create security user record
        security_user_data = {
            "user_id": user_id,
            "email": user_data.email,
            "password_hash": hashed_password,
            "role": user_data.role,
            "is_active": True,
            "failed_login_attempts": 0,
            "two_factor_enabled": False,
            "permissions": [],
            "created_at": datetime.utcnow()
        }
        
        # Insert security data
        await security_users_collection.insert_one(security_user_data)
        
        # Publish user profile data to Users Dblock via message queue
        profile_message = UserCreatedMessage(
            user_id=user_id,
            full_name=user_data.full_name,
            phoneNo=user_data.phoneNo,
            details=user_data.details,
            preferences=user_data.preferences
        )
        
        if mq_service.connection:
            mq_service.publish_user_created(profile_message)
        else:
            logger.warning("Message queue not available, user profile not synchronized")
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user_id},
            expires_delta=access_token_expires
        )
        
        # Log security event
        await log_security_event(
            user_id=user_id,
            action="user_signup",
            details={"ip_address": str(request.client.host)}
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=user_id,
            role=user_data.role
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
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": security_user["user_id"]},
            expires_delta=access_token_expires
        )
        
        # Log successful login
        await log_security_event(
            user_id=security_user["user_id"],
            action="successful_login",
            details={"ip_address": str(request.client.host)}
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=security_user["user_id"],
            role=security_user["role"]
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
