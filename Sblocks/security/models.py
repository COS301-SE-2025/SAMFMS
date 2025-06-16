# Backward compatibility - redirect to new structure
# This file provides backward compatibility for existing imports

from models.database_models import (
    PyObjectId, SecurityUser, UserProfile, 
    UserCreatedMessage, UserUpdatedMessage, UserDeletedMessage
)
from models.api_models import (
    SignupRequest, InviteUserRequest, LoginRequest, TokenResponse, 
    MessageResponse, ChangePasswordRequest, UpdatePermissionsRequest, 
    UpdatePreferencesRequest, UserResponse, ProfileUpdateRequest, 
    ProfilePictureResponse, PreferencesUpdateRequest
)

# Keep all exports for backward compatibility
__all__ = [
    # Database models
    "PyObjectId", "SecurityUser", "UserProfile",
    "UserCreatedMessage", "UserUpdatedMessage", "UserDeletedMessage",
    
    # API models
    "SignupRequest", "InviteUserRequest", "LoginRequest", "TokenResponse",
    "MessageResponse", "ChangePasswordRequest", "UpdatePermissionsRequest",
    "UpdatePreferencesRequest", "UserResponse", "ProfileUpdateRequest",
    "ProfilePictureResponse", "PreferencesUpdateRequest"
]
