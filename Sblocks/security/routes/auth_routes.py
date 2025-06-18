from fastapi import APIRouter, HTTPException, Depends, status, Request, File, UploadFile
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models.api_models import SignupRequest, LoginRequest, TokenResponse, MessageResponse, ProfileUpdateRequest, ChangePasswordRequest
from services.auth_service import AuthService
from services.user_service import UserService
from repositories.user_repository import UserRepository
from utils.auth_utils import get_current_user
import logging
import time
import os
import shutil
from pathlib import Path
import time

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


async def get_current_user_secure(token: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user with comprehensive security checks"""
    try:
        return await AuthService.get_current_user_secure(token.credentials)
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


@router.post("/signup", response_model=TokenResponse)
async def signup(user_data: SignupRequest):
    """Register a new user"""
    try:
        return await AuthService.signup_user(user_data.dict())
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
        client_ip = str(request.client.host) if request.client else "unknown"
        return await AuthService.login_user(login_data.email, login_data.password, client_ip)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login error: {str(e)}"
        )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: dict = Depends(get_current_user_secure),
    request: Request = None
):
    """Logout user and invalidate token"""
    try:
        token = current_user.get("token")
        if token:
            await AuthService.logout_user(token)
        
        return MessageResponse(message="Successfully logged out")
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout error: {str(e)}"
        )


@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user_secure)):
    """Get current user information"""
    try:
        # Remove sensitive data
        user_info = {k: v for k, v in current_user.items() 
                    if k not in ["password_hash", "token", "_id"]}
        
        # Ensure preferences are included, using default if missing
        if "preferences" not in user_info or not user_info["preferences"]:
            from models.database_models import UserProfile
            user_info["preferences"] = UserProfile().preferences
            
        return user_info
    except Exception as e:
        logger.error(f"Get user info error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )


@router.get("/user-exists")
async def check_user_existence():
    """Check if any users exist in the system"""
    try:
        from repositories.user_repository import UserRepository
        user_count = await UserRepository.count_users()
        return {"userExists": user_count > 0}
    except Exception as e:
        logger.error(f"Error checking user existence: {e}")
        # Default to False for better UX - if we can't check, assume no users for initial setup
        return {"userExists": False}


@router.get("/users/count")
async def get_user_count():
    """Get total count of users in the system"""
    try:
        from repositories.user_repository import UserRepository
        user_count = await UserRepository.count_users()
        return {"count": user_count}
    except Exception as e:
        logger.error(f"Error getting user count: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user count"
        )


@router.post("/verify-token")
async def verify_token(current_user: dict = Depends(get_current_user_secure)):
    """Verify a JWT token and return user information (used by other services)"""
    try:
        # Return user information without sensitive data
        user_info = {k: v for k, v in current_user.items() 
                    if k not in ["password_hash", "token", "_id"]}
        
        # Ensure preferences are included, using default if missing
        if "preferences" not in user_info or not user_info["preferences"]:
            from models.database_models import UserProfile
            user_info["preferences"] = UserProfile().preferences
            
        return user_info
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


@router.get("/roles")
async def get_roles():
    """Get available roles and their permissions"""
    try:
        # Get roles from a predefined configuration
        # This could be fetched from a database in a real implementation
        roles = [
            {
                "id": "admin",
                "name": "Administrator",
                "description": "Full system access",
                "permissions": ["users:manage", "vehicles:manage", "trips:manage", "system:manage", "reports:view"]
            },
            {
                "id": "fleet_manager",
                "name": "Fleet Manager",
                "description": "Manage fleet operations",
                "permissions": ["vehicles:manage", "drivers:manage", "trips:manage", "reports:view"]
            },
            {
                "id": "driver",
                "name": "Driver",
                "description": "Driver access only",
                "permissions": ["trips:view", "profile:manage"]
            }
        ]
        
        return {"roles": roles}
    except Exception as e:
        logger.error(f"Error getting roles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get roles"
        )


@router.post("/update-preferences")
async def update_preferences(
    preferences_data: dict,
    current_user: dict = Depends(get_current_user_secure)
):
    """Update user preferences"""
    try:
        logger.info(f"Update preferences request for user_id: {current_user.get('user_id')}")
        logger.info(f"Current user data: {current_user}")
        
        # Extract preferences from the request data
        preferences = preferences_data.get("preferences", {})
        logger.info(f"Preferences to update: {preferences}")
        
        if not preferences:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No preferences provided"
            )
        
        # Check if user exists first
        user_exists = await UserRepository.find_by_user_id(current_user["user_id"])
        logger.info(f"User exists check: {user_exists is not None}")
        if not user_exists:
            logger.error(f"User not found with user_id: {current_user['user_id']}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in database"
            )
        
        success = await UserService.update_user_preferences(
            user_id=current_user["user_id"],
            preferences=preferences
        )
        logger.info(f"Update preferences success: {success}")
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found or update failed"
            )
        
        # Get updated user data to return the current preferences
        updated_user = await UserRepository.find_by_user_id(current_user["user_id"])
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found after update"
            )
        
        logger.info(f"Updated user preferences: {updated_user.get('preferences', {})}")
        
        # Return the updated preferences along with success message
        return {
            "message": "Preferences updated successfully", 
            "preferences": updated_user.get("preferences", {})
        }
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error updating preferences: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/update-profile")
async def update_profile(
    profile_data: ProfileUpdateRequest,
    current_user: dict = Depends(get_current_user_secure)
):
    """Update user profile - endpoint to match Core service expectations"""
    try:
        user_id = current_user["user_id"]
        success = await UserService.update_user_profile(user_id, profile_data.dict(exclude_unset=True))
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found or update failed"
            )
        
        return {"message": "Profile updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user_secure)
):
    """Change user password - endpoint to match Core service expectations"""
    try:
        user_id = current_user["user_id"]
        success = await UserService.change_user_password(
            user_id=user_id,
            current_password=password_data.current_password,
            new_password=password_data.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to change password"
            )
        
        return {"message": "Password changed successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Change password error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


@router.post("/upload-profile-picture")
async def upload_profile_picture(
    profile_picture: UploadFile = File(...),
    current_user: dict = Depends(get_current_user_secure)
):
    """Upload and update user profile picture"""
    try:
        # Validate file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png']
        if profile_picture.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only JPEG and PNG files are allowed"
            )
        
        # Validate file size (max 5MB)
        max_size = 5 * 1024 * 1024  # 5MB
        if profile_picture.size and profile_picture.size > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size must be less than 5MB"
            )
        
        user_id = current_user["user_id"]
        
        # Create profile pictures directory if it doesn't exist
        profile_pictures_dir = Path("profile_pictures")
        profile_pictures_dir.mkdir(exist_ok=True)
        
        # Generate unique filename
        file_extension = profile_picture.filename.split('.')[-1].lower()
        filename = f"{user_id}_{int(time.time())}.{file_extension}"
        file_path = profile_pictures_dir / filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(profile_picture.file, buffer)
        
        # Update user profile with picture URL
        profile_picture_url = f"/static/profile_pictures/{filename}"
        success = await UserService.update_user_profile(user_id, {
            "profile_picture_url": profile_picture_url
        })
        
        if not success:
            # Clean up uploaded file if database update failed
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update profile picture"
            )
        
        return {
            "message": "Profile picture uploaded successfully",
            "profile_picture_url": profile_picture_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload profile picture error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload profile picture"
        )
