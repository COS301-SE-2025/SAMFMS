from fastapi import APIRouter, HTTPException, status
from models import UserProfile, UserProfileResponse, UserProfileUpdateRequest
from database import user_profiles_collection
from bson import ObjectId
from datetime import datetime
import logging
from typing import List

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["User Profiles"])


@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(user_id: str):
    """Get user profile by user_id"""
    try:
        user_profile = await user_profiles_collection.find_one({"user_id": user_id})
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        return UserProfileResponse(**user_profile)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user profile: {str(e)}"
        )


@router.put("/{user_id}", response_model=UserProfileResponse)
async def update_user_profile(user_id: str, profile_update: UserProfileUpdateRequest):
    """Update user profile"""
    try:
        # Prepare update data (only include fields that are not None)
        update_data = {}
        for field, value in profile_update.model_dump(exclude_unset=True).items():
            if value is not None:
                update_data[field] = value
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields to update"
            )
        
        # Add updated timestamp
        update_data["updated_at"] = datetime.utcnow()
        
        # Update user profile
        result = await user_profiles_collection.update_one(
            {"user_id": user_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        # Get updated profile
        updated_profile = await user_profiles_collection.find_one({"user_id": user_id})
        return UserProfileResponse(**updated_profile)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user profile: {str(e)}"
        )


@router.get("/", response_model=List[UserProfileResponse])
async def list_user_profiles(skip: int = 0, limit: int = 100):
    """List all user profiles with pagination"""
    try:
        profiles_cursor = user_profiles_collection.find({}).skip(skip).limit(limit)
        profiles = await profiles_cursor.to_list(length=None)
        
        return [UserProfileResponse(**profile) for profile in profiles]
        
    except Exception as e:
        logger.error(f"Error fetching user profiles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user profiles: {str(e)}"
        )


@router.delete("/{user_id}")
async def delete_user_profile(user_id: str):
    """Delete user profile"""
    try:
        result = await user_profiles_collection.delete_one({"user_id": user_id})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        return {"message": "User profile deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting user profile: {str(e)}"
        )
