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
    preferences: Optional[Dict[str, str]] = {
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
                "preferences": {
                    "theme": "dark",
                    "animations": "true",
                    "email_alerts": "true",
                    "push_notifications": "false",
                    "timezone": "UTC-5 (Eastern Time)",
                    "date_format": "DD/MM/YYYY",
                    "two_factor": "true",
                    "activity_log": "true",
                    "session_timeout": "1 hour"
                }
            }
        }


class UserResponse(BaseModel):
    id: str = Field(alias="_id")
    details: Optional[Dict[str, str]] = {}
    full_name: str
    email: str
    role: str
    phoneNo: Optional[str] = None
    preferences: Optional[Dict[str, str]] = {}

    class Config:
        validate_by_name = True
        json_encoders = {ObjectId: str}


class VehicleModel(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    make: str
    model: str
    year: int
    vin: str
    license_plate: str
    color: Optional[str] = None
    fuel_type: Optional[str] = "gasoline"
    mileage: Optional[int] = 0
    status: Optional[str] = "active"  # active, inactive, maintenance
    driver_id: Optional[str] = None
    
    class Config:
        validate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "make": "Toyota",
                "model": "Camry",
                "year": 2020,
                "vin": "1HGBH41JXMN109186",
                "license_plate": "ABC123",
                "color": "Silver",
                "fuel_type": "gasoline",
                "mileage": 15000,
                "status": "active"
            }
        }


class VehicleResponse(BaseModel):
    id: str = Field(alias="_id")
    make: str
    model: str
    year: int
    vin: str
    license_plate: str
    color: Optional[str] = None
    fuel_type: Optional[str] = "gasoline"
    mileage: Optional[int] = 0
    status: Optional[str] = "active"
    driver_id: Optional[str] = None
    driver_name: Optional[str] = None

    class Config:
        validate_by_name = True
        json_encoders = {ObjectId: str}
        
class VehicleUpdateRequest(BaseModel):
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    vin: Optional[str] = None
    license_plate: Optional[str] = None
    color: Optional[str] = None
    fuel_type: Optional[str] = None
    mileage: Optional[int] = None
    status: Optional[str] = None
    driver_id: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class DriverModel(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: str  # Reference to the user in users collection
    license_number: str
    license_type: str  # Class A, B, C, CDL
    license_expiry: str  # Date in YYYY-MM-DD format
    status: str = "available"  # available, on_trip, on_leave, inactive
    department: Optional[str] = None
    employee_id: Optional[str] = None
    joining_date: Optional[str] = None
    emergency_contact: Optional[str] = None
    rating: Optional[float] = 0.0
    current_vehicle_id: Optional[str] = None
    
    class Config:
        validate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "user_id": "60d5f484f1a2b3c4d5e6f7g8",
                "license_number": "DL8976543",
                "license_type": "Class C",
                "license_expiry": "2025-06-15",
                "status": "available",
                "department": "Sales",
                "employee_id": "EMP-1235",
                "joining_date": "2021-05-10",
                "emergency_contact": "(555) 987-6543",
                "rating": 4.8,
                "current_vehicle_id": None
            }
        }


class DriverResponse(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    license_number: str
    license_type: str
    license_expiry: str
    status: str
    department: Optional[str] = None
    employee_id: Optional[str] = None
    joining_date: Optional[str] = None
    emergency_contact: Optional[str] = None
    rating: Optional[float] = 0.0
    current_vehicle_id: Optional[str] = None
    # User information will be included when fetching driver details
    user_info: Optional[Dict] = None
    
    class Config:
        validate_by_name = True
        json_encoders = {ObjectId: str}


class DriverCreateRequest(BaseModel):
    # User details
    full_name: str
    email: str
    phoneNo: Optional[str] = None
    role: str = "driver"
    # Driver specific details
    license_number: str
    license_type: str
    license_expiry: str
    department: Optional[str] = None
    joining_date: Optional[str] = None
    emergency_contact: Optional[str] = None


class DriverUpdateRequest(BaseModel):
    license_number: Optional[str] = None
    license_type: Optional[str] = None
    license_expiry: Optional[str] = None
    status: Optional[str] = None
    department: Optional[str] = None
    employee_id: Optional[str] = None
    emergency_contact: Optional[str] = None
    rating: Optional[float] = None
    current_vehicle_id: Optional[str] = None
