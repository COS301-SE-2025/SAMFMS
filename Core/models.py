from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from bson import ObjectId


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, field = None):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


class UserModel(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    details: Optional[Dict[str, str]] = {}
    full_name: str
    email: str
    password: str
    role: str
    phoneNo: Optional[str] = None
    preferences: Optional[List[str]] = []

    class Config:
        validate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "id": "60d5f484f1a2b3c4d5e6f7g8",
                "details": {"ID":"12345678"},
                "full_name": "Alice",
                "email": "alice@example.com",
                "password": "securepassword",
                "role": "admin",
                "phoneNo": "123-456-7890",
                "preferences": ["dark_mode", "email_notifications"]
            }
        }
