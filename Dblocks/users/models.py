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
        json_schema_extra = {
            "example":{
                "id": "60d5f484f1a2b3c4d5e6f7g8",
                "user_id": "user123",
                "full_name": "Alice Smith",
                "email": "Password123#",
                "password": "securepassword",
                "role": "admin",
                "phoneNo": "123-456-7890",
                "details": {"ID": "12345678"},
                "preferences": {                    "theme": "dark",
                    "animations": "true",
                    "email_alerts": "true",
                    "push_notifications": "false",
                    "two_factor": "false",
                    "activity_log": "true",
                    "session_timeout": "30 minutes"
                },
            }
        }


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
