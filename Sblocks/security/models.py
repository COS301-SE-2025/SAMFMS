from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, List
from bson import ObjectId
from datetime import datetime


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, field=None):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


# Security-specific models
class SecurityUser(BaseModel):
    """Security-related user data stored in Security service"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: str  # Reference to user in Users Dblock
    email: EmailStr
    password_hash: str
    role: str = "user"
    is_active: bool = True
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    password_reset_token: Optional[str] = None
    two_factor_enabled: bool = False
    permissions: list = []
    
    class Config:
        validate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class UserProfile(BaseModel):
    """Non-security user data for Users Dblock"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    full_name: str
    phoneNo: Optional[str] = None
    details: Dict = {}
    preferences: Dict = {
        "theme": "light",
        "animations": "true",
        "email_alerts": "true",
        "push_notifications": "true",
        "timezone": "UTC-5 (Eastern Time)",
        "date_format": "MM/DD/YYYY",
        "two_factor": "false",
        "activity_log": "true",
        "session_timeout": "30 minutes"
    }
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        validate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# Request/Response models
class SignupRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: Optional[str] = None  # No default role - must be assigned
    phoneNo: Optional[str] = None
    details: Dict = {}
    preferences: Dict = {}


class InviteUserRequest(BaseModel):
    """Admin/Fleet Manager can invite users with specific roles"""
    full_name: str
    email: EmailStr
    role: str  # Required - either "fleet_manager" or "driver"
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


# Message Queue models
class UserCreatedMessage(BaseModel):
    user_id: str
    full_name: str
    phoneNo: Optional[str] = None
    details: Dict = {}
    preferences: Dict = {}


class UserUpdatedMessage(BaseModel):
    user_id: str
    updates: Dict


class UserDeletedMessage(BaseModel):
    user_id: str
