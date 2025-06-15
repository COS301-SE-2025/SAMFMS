from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, List
from datetime import datetime


class SignupRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: Optional[str] = None  # No default role - must be assigned
    phoneNo: Optional[str] = None
    details: Dict = {}
    preferences: Dict = {
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


class InviteUserRequest(BaseModel):
    """Admin/Fleet Manager can add users with specific roles"""
    full_name: str
    email: EmailStr
    password: str  # Password for the new user
    role: str  # Required - either "admin", "fleet_manager" or "driver"
    phoneNo: Optional[str] = None
    details: Dict = {}
    preferences: Dict = {}
    custom_permissions: Optional[List[str]] = None  # Admin can grant custom permissions


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    role: str
    permissions: List[str]
    preferences: Dict = {}
    refresh_token: Optional[str] = None


class MessageResponse(BaseModel):
    message: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class UpdatePermissionsRequest(BaseModel):
    """Admin can update user permissions"""
    user_id: str
    role: Optional[str] = None
    custom_permissions: Optional[List[str]] = None


class UpdatePreferencesRequest(BaseModel):
    preferences: Dict


class UserResponse(BaseModel):
    id: str
    full_name: str
    email: str
    role: str
    permissions: List[str]
    phoneNo: Optional[str] = None
    details: Dict = {}
    preferences: Dict = {}
    is_active: bool = True
    last_login: Optional[datetime] = None


class ProfileUpdateRequest(BaseModel):
    """Model for updating user profile information"""
    phoneNo: Optional[str] = None
    full_name: Optional[str] = None


class ProfilePictureResponse(BaseModel):
    """Response after uploading a profile picture"""
    message: str
    profile_picture_url: str


class PreferencesUpdateRequest(BaseModel):
    """Model for updating user preferences"""
    preferences: Dict
