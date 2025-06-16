# Import all models for backward compatibility
from .database_models import SecurityUser, UserProfile, UserCreatedMessage, UserUpdatedMessage, UserDeletedMessage, PyObjectId
from .api_models import (
    SignupRequest, InviteUserRequest, LoginRequest, TokenResponse, MessageResponse,
    ChangePasswordRequest, UpdatePermissionsRequest, UserResponse,
    ProfileUpdateRequest, ProfilePictureResponse, PreferencesUpdateRequest
)

# Export all models
__all__ = [
    # Database models
    'SecurityUser', 'UserProfile', 'UserCreatedMessage', 'UserUpdatedMessage', 
    'UserDeletedMessage', 'PyObjectId',
    
    # API models
    'SignupRequest', 'InviteUserRequest', 'LoginRequest', 'TokenResponse', 
    'MessageResponse', 'ChangePasswordRequest', 'UpdatePermissionsRequest',
    'UserResponse', 'ProfileUpdateRequest', 'ProfilePictureResponse',
    'PreferencesUpdateRequest'
]