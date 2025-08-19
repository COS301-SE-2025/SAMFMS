from fastapi import APIRouter, HTTPException, Depends, status, Request, File, UploadFile, Form
from fastapi.security import HTTPBearer
from models.api_models import (
    UpdatePermissionsRequest, UserResponse, ProfileUpdateRequest, 
    ProfilePictureResponse, PreferencesUpdateRequest, ChangePasswordRequest
)
from services.user_service import UserService
from routes.auth_routes import get_current_user_secure
from utils.auth_utils import require_role, require_permission
from typing import List
import os
import shutil
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["User Management"])
security = HTTPBearer()

# Path for storing profile pictures
PROFILE_PICTURES_DIR = os.path.join(os.getcwd(), "profile_pictures")
os.makedirs(PROFILE_PICTURES_DIR, exist_ok=True)

# Public URL for accessing profile pictures
PROFILE_PICTURES_URL = os.getenv("PROFILE_PICTURES_URL", "/static/profile_pictures")


@router.get("/", response_model=List[UserResponse])
async def get_all_users(current_user: dict = Depends(get_current_user_secure)):
    """Get all users (Admin/Fleet Manager only)"""
    try:
        # Check permissions
        if current_user["role"] not in ["admin", "fleet_manager"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )   
        
        
        users = await UserService.get_all_users()
        logger.info(f"Users in user_router : {users}")
        return users
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get all users error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get users"
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, current_user: dict = Depends(get_current_user_secure)):
    """Get user by ID"""
    try:
        # Users can only view their own profile, admins/fleet managers can view all
        if (current_user["user_id"] != user_id and 
            current_user["role"] not in ["admin", "fleet_manager"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        user = await UserService.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user"
        )


@router.put("/{user_id}/permissions")
async def update_user_permissions(
    user_id: str,
    permissions_data: UpdatePermissionsRequest,
    current_user: dict = Depends(get_current_user_secure)
):
    """Update user permissions (Admin only)"""
    try:
        # Only admins can update permissions
        if current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        success = await UserService.update_user_permissions(
            user_id=user_id,
            role=permissions_data.role,
            custom_permissions=permissions_data.custom_permissions
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found or update failed"
            )
        
        return {"message": "Permissions updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update permissions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update permissions"
        )


@router.put("/{user_id}/profile")
async def update_profile(
    user_id: str,
    profile_data: ProfileUpdateRequest,
    current_user: dict = Depends(get_current_user_secure)
):
    """Update user profile"""
    try:
        # Users can only update their own profile
        if current_user["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only update your own profile"
            )
        
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


@router.post("/{user_id}/change-password")
async def change_password(
    user_id: str,
    password_data: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user_secure)
):
    """Change user password"""
    try:
        # Users can only change their own password
        if current_user["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only change your own password"
            )
        
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


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(get_current_user_secure)
):
    """Delete user (Admin only)"""
    try:
        # Only admins can delete users
        if current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        # Cannot delete yourself
        if current_user["user_id"] == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )
        
        success = await UserService.delete_user(user_id, current_user["user_id"])
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {"message": "User deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )
