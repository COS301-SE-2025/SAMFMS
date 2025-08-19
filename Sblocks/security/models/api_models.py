from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, Dict, List
import re
from datetime import datetime


class SignupRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    role: Optional[str] = None  # No default role - must be assigned
    phoneNo: Optional[str] = None
    details: Dict = {}
    preferences: Dict = {
        "theme": "light",
        "animations": "true",
        "email_alerts": "true",
        "push_notifications": "true",
        "two_factor": "false",
        "activity_log": "true",
        "session_timeout": "30 minutes"
    }

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('Password must contain at least one letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v

    @validator('phoneNo')
    def validate_phone(cls, v):
        if v and not re.match(r'^\+?[\d\s\-\(\)]{10,15}$', v):
            raise ValueError('Invalid phone number format')
        return v


class InviteUserRequest(BaseModel):
    """Admin/Fleet Manager can invite users - updated for OTP flow"""
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    role: str = Field(..., pattern='^(admin|fleet_manager|driver)$')  # Validate allowed roles
    phoneNo: Optional[str] = None

    @validator('phoneNo')
    def validate_phone(cls, v):
        if v and not re.match(r'^\+?[\d\s\-\(\)]{10,15}$', v):
            raise ValueError('Invalid phone number format')
        return v

    @validator('full_name')
    def validate_full_name(cls, v):
        if not v.strip():
            raise ValueError('Full name cannot be empty')
        return v.strip()


class CreateUserRequest(BaseModel):
    """Admin can manually create users without invitation flow"""
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    role: str = Field(..., pattern='^(admin|fleet_manager|driver)$')  # Validate allowed roles
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    phoneNo: Optional[str] = None
    details: Dict = {}

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('Password must contain at least one letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v

    @validator('phoneNo')
    def validate_phone(cls, v):
        if v and not re.match(r'^\+?[\d\s\-\(\)]{10,15}$', v):
            raise ValueError('Invalid phone number format')
        return v

    @validator('full_name')
    def validate_full_name(cls, v):
        if not v.strip():
            raise ValueError('Full name cannot be empty')
        return v.strip()


class VerifyOTPRequest(BaseModel):
    """Request to verify OTP and complete user registration"""
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6, pattern='^\\d{6}$')


class CompleteRegistrationRequest(BaseModel):
    """Complete user registration after OTP verification"""
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6, pattern='^\\d{6}$')
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    username: Optional[str] = None  # Optional - will use email prefix if not provided

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('Password must contain at least one letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v

    @validator('username')
    def validate_username(cls, v):
        if v and not re.match(r'^[a-zA-Z0-9_]{3,20}$', v):
            raise ValueError('Username must be 3-20 characters, alphanumeric and underscores only')
        return v


class ResendOTPRequest(BaseModel):
    """Request to resend OTP"""
    email: EmailStr


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
    phone: Optional[str] = None
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
