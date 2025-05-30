from pydantic import BaseModel, Field
from typing import Optional, Dict
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


class UserProfile(BaseModel):
    """User profile data stored in Users Dblock"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: str  # Reference ID from Security service
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


class UserProfileResponse(BaseModel):
    """Response model for user profile"""
    user_id: str
    full_name: str
    phoneNo: Optional[str] = None
    details: Dict = {}
    preferences: Dict = {}
    created_at: datetime
    updated_at: datetime


class UserProfileUpdateRequest(BaseModel):
    """Request model for updating user profile"""
    full_name: Optional[str] = None
    phoneNo: Optional[str] = None
    details: Optional[Dict] = None
    preferences: Optional[Dict] = None


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
