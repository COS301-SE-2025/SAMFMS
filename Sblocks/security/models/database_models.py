from pydantic import BaseModel, Field, EmailStr, root_validator
from typing import Optional, Dict, List
from bson import ObjectId
from datetime import datetime, timedelta
import secrets
import string


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
    approved: bool = False
    profile_picture_url: Optional[str] = None
    full_name: Optional[str] = None

    @root_validator(pre=True)
    def enforce_approved_based_on_role(cls, values):
        role = values.get("role")
        approved = values.get("approved", False)
        if role == "admin":
            values["approved"] = True
        return values
    
    class Config:
        validate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class UserProfile(BaseModel):
    """User profile data stored in Users Dblock"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    full_name: str
    email: str
    password: str
    role: str
    phoneNo: Optional[str] = None
    details: Optional[Dict[str, str]] = {}
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
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        validate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


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


class UserInvitation(BaseModel):
    """User invitation model for OTP-based user activation"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    email: EmailStr
    full_name: str
    role: str
    phone_number: Optional[str] = None
    otp: str = Field(default_factory=lambda: ''.join(secrets.choice(string.digits) for _ in range(6)))
    invited_by: str  # user_id of admin/fleet_manager who sent the invitation
    status: str = "invited"  # invited, activated, expired
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(hours=24))
    activation_attempts: int = 0
    max_attempts: int = 3
    
    class Config:
        validate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at
    
    def is_valid_for_activation(self) -> bool:
        return (
            self.status == "invited" and 
            not self.is_expired() and 
            self.activation_attempts < self.max_attempts
        )
