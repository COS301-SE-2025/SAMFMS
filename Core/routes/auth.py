from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer
from models import UserModel, UserResponse
from auth_utils import (
    authenticate_user, 
    create_access_token, 
    get_password_hash, 
    get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from bson import ObjectId
from datetime import timedelta
from pydantic import BaseModel, EmailStr
from database import db

router = APIRouter()
users_collection = db.users
security = HTTPBearer()

# Request/Response models
class SignupRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: str = "user"  # Default role
    phoneNo: str = None
    details: dict = {}
    preferences: list = []

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class MessageResponse(BaseModel):
    message: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/signup", response_model=TokenResponse)
async def signup(user_data: SignupRequest):
    """Create a new user account and return access token."""
    try:
        # Check if user already exists
        existing_user = await users_collection.find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="User with this email already exists"
            )

        # Hash the password
        hashed_password = get_password_hash(user_data.password)
        
        # Create user model
        user_model = UserModel(
            full_name=user_data.full_name,
            email=user_data.email,
            password=hashed_password,
            role=user_data.role,
            details=user_data.details,
            phoneNo=user_data.phoneNo,
            preferences=user_data.preferences
        )
        
        # Insert user into database
        user_dict = user_model.model_dump(by_alias=True)
        result = await users_collection.insert_one(user_dict)
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(result.inserted_id)}, 
            expires_delta=access_token_expires
        )
        
        # Get the created user for response
        created_user = await users_collection.find_one({"_id": result.inserted_id})
        user_response = UserResponse(
            id=str(created_user["_id"]),
            full_name=created_user["full_name"],
            email=created_user["email"],
            role=created_user["role"],
            phoneNo=created_user.get("phoneNo"),
            details=created_user.get("details", {}),
            preferences=created_user.get("preferences", [])
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")


@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest):
    """Authenticate user and return access token."""
    try:
        # Authenticate user
        user = await authenticate_user(login_data.email, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user["_id"])}, 
            expires_delta=access_token_expires
        )
        
        # Create user response
        user_response = UserResponse(
            id=str(user["_id"]),
            full_name=user["full_name"],
            email=user["email"],
            role=user["role"],
            phoneNo=user.get("phoneNo"),
            details=user.get("details", {}),
            preferences=user.get("preferences", [])
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")


@router.delete("/account", response_model=MessageResponse)
async def delete_account(current_user: dict = Depends(get_current_active_user)):
    """Delete the current user's account."""
    try:
        user_id = current_user["_id"]
        
        # Delete the user from database
        result = await users_collection.delete_one({"_id": user_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        return MessageResponse(message="Account deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting account: {str(e)}")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_active_user)):
    """Get current user information."""
    try:
        return UserResponse(
            id=str(current_user["_id"]),
            full_name=current_user["full_name"],
            email=current_user["email"],
            role=current_user["role"],
            phoneNo=current_user.get("phoneNo"),
            details=current_user.get("details", {}),
            preferences=current_user.get("preferences", [])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user info: {str(e)}")


@router.put("/change-password", response_model=MessageResponse)
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """Change user password."""
    try:
        # Verify current password
        user = await authenticate_user(current_user["email"], password_data.current_password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect"
            )
        
        # Hash new password
        new_hashed_password = get_password_hash(password_data.new_password)
        
        # Update password in database
        result = await users_collection.update_one(
            {"_id": current_user["_id"]},
            {"$set": {"password": new_hashed_password}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        return MessageResponse(message="Password changed successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error changing password: {str(e)}")