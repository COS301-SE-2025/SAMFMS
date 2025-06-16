from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field
from typing import Dict, List, Optional
import logging
import requests
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

# Define the URL for the Security Sblock
SECURITY_URL = os.getenv("SECURITY_URL", "http://security_service:8000")

# Models to mirror the ones in security service
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class SignupRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: Optional[str] = None
    phoneNo: Optional[str] = None
    details: Dict = {}
    preferences: Dict = {}

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    role: str
    permissions: List[str]
    preferences: Dict = {}

class ProfileUpdateRequest(BaseModel):
    phoneNo: Optional[str] = None
    full_name: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class PreferencesUpdateRequest(BaseModel):
    preferences: Dict

@router.post("/login", response_model=TokenResponse)
async def login(login_request: LoginRequest):
    """Proxy the login request to the Security service"""
    try:
        # Forward the request to the Security service
        response = requests.post(
            f"{SECURITY_URL}/auth/login",
            json=login_request.dict(),
            timeout=10
        )
        
        # Check if the request was successful
        if response.status_code == 200:
            # Return the response from the Security service
            return response.json()
        else:
            # Return the error from the Security service
            error_detail = response.json().get("detail", "Authentication failed")
            raise HTTPException(
                status_code=response.status_code,
                detail=error_detail
            )
    except requests.RequestException as e:
        logger.error(f"Error connecting to Security service: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Security service unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Login error: {str(e)}"
        )

@router.post("/signup", response_model=TokenResponse)
async def signup(signup_request: SignupRequest):
    """Proxy the signup request to the Security service"""
    try:
        # Forward the request to the Security service
        response = requests.post(
            f"{SECURITY_URL}/auth/signup",
            json=signup_request.dict(),
            timeout=10
        )
        
        # Check if the request was successful
        if response.status_code == 200:
            # Return the response from the Security service
            return response.json()
        else:
            # Return the error from the Security service
            error_detail = response.json().get("detail", "Signup failed")
            raise HTTPException(
                status_code=response.status_code,
                detail=error_detail
            )
    except requests.RequestException as e:
        logger.error(f"Error connecting to Security service: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Security service unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Signup error: {str(e)}"
        )

@router.post("/verify-token")
async def verify_token(request: Request):
    """Proxy the token verification request to the Security service"""
    try:
        # Get the Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(
                status_code=401,
                detail="Authorization header is missing"
            )
        
        # Forward the request to the Security service
        headers = {"Authorization": auth_header}
        response = requests.post(
            f"{SECURITY_URL}/auth/verify-token",
            headers=headers,
            timeout=10
        )
        
        # Return the response from the Security service
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error connecting to Security service: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Security service unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )


@router.post("/logout", response_model=dict)
async def logout(request: Request):
    """Proxy the logout request to the Security service"""
    try:
        # Get the Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(
                status_code=401,
                detail="Authorization header is missing"
            )
        
        # Forward the request to the Security service
        headers = {"Authorization": auth_header}
        response = requests.post(
            f"{SECURITY_URL}/auth/logout",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            detail = response.json().get("detail", "Logout failed")
            raise HTTPException(status_code=response.status_code, detail=detail)
            
    except requests.RequestException as e:
        logger.error(f"Error connecting to Security service: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Security service unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Logout error: {str(e)}"
        )


@router.post("/logout-all", response_model=dict)
async def logout_all(request: Request):
    """Proxy the logout-all request to the Security service"""
    try:
        # Get the Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(
                status_code=401,
                detail="Authorization header is missing"
            )
        
        # Forward the request to the Security service
        headers = {"Authorization": auth_header}
        response = requests.post(
            f"{SECURITY_URL}/auth/logout-all",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            detail = response.json().get("detail", "Logout from all devices failed")
            raise HTTPException(status_code=response.status_code, detail=detail)
            
    except requests.RequestException as e:
        logger.error(f"Error connecting to Security service: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Security service unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Logout all error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Logout all error: {str(e)}"
        )


@router.post("/refresh", response_model=dict)
async def refresh_token(request: Request):
    """Proxy the token refresh request to the Security service"""
    try:
        # Get request body
        body = await request.body()
        
        # Forward the request to the Security service
        response = requests.post(
            f"{SECURITY_URL}/auth/refresh",
            data=body,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            detail = response.json().get("detail", "Token refresh failed")
            raise HTTPException(status_code=response.status_code, detail=detail)
            
    except requests.RequestException as e:
        logger.error(f"Error connecting to Security service: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Security service unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Token refresh error: {str(e)}"
        )

@router.get("/health")
async def auth_health():
    """Check if the auth routes are working and if the Security service is reachable"""
    try:
        # Try to connect to the Security service
        response = requests.get(f"{SECURITY_URL}/health", timeout=5)
        security_status = "reachable" if response.status_code == 200 else f"error: {response.status_code}"
    except Exception as e:
        security_status = f"unreachable: {str(e)}"
    
    return {
        "auth_routes": "working",
        "security_service": security_status,
        "security_url": SECURITY_URL
    }

@router.get("/user-exists")
async def check_user_existence():
    """Check if any users exist in the system"""
    try:
        # Forward the request to the Security service
        response = requests.get(
            f"{SECURITY_URL}/auth/user-exists",
            timeout=5
        )
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            # Endpoint doesn't exist, try the count endpoint
            logger.info("user-exists endpoint not found, trying users/count endpoint")
            count_response = requests.get(
                f"{SECURITY_URL}/auth/users/count",
                timeout=5
            )
            
            if count_response.status_code == 200:
                data = count_response.json()
                return {"userExists": data.get("count", 0) > 0}
            else:
                logger.warning(f"Both user-exists and users/count endpoints failed. Status: {count_response.status_code}")
                # Default to false for better UX when endpoints are missing
                return {"userExists": False}
        else:
            logger.warning(f"Security service returned unexpected status: {response.status_code}")
            # Default to false for better UX when there are errors
            return {"userExists": False}
                
    except requests.RequestException as e:
        logger.error(f"Error connecting to Security service when checking user existence: {e}")
        # Default to false if we can't connect to allow signup flow
        return {"userExists": False}
    except Exception as e:
        logger.error(f"Error checking user existence: {e}")
        return {"userExists": False}

@router.post("/update-profile")
async def update_profile(request: Request, data: ProfileUpdateRequest):
    """Update user profile information"""
    try:
        # Get the token from the request
        token = request.headers.get("Authorization")
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Forward the request to the Security service
        response = requests.post(
            f"{SECURITY_URL}/auth/update-profile",
            headers={"Authorization": token},
            json=data.dict(exclude_none=True),
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            detail = response.json().get("detail", "Failed to update profile")
            raise HTTPException(status_code=response.status_code, detail=detail)
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/upload-profile-picture")
async def upload_profile_picture(request: Request, profile_picture: UploadFile = File(...)):
    """Upload and update user profile picture"""
    try:
        # Get the token from the request
        token = request.headers.get("Authorization")
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Forward the request and file to the Security service
        files = {"profile_picture": (profile_picture.filename, profile_picture.file, profile_picture.content_type)}
        
        response = requests.post(
            f"{SECURITY_URL}/auth/upload-profile-picture",
            headers={"Authorization": token},
            files=files,
            timeout=30  # Longer timeout for file upload
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            detail = response.json().get("detail", "Failed to upload profile picture")
            raise HTTPException(status_code=response.status_code, detail=detail)
    except Exception as e:
        logger.error(f"Error uploading profile picture: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/update-preferences")
async def update_preferences(request: Request, data: PreferencesUpdateRequest):
    """Update user preferences"""
    try:
        # Get the token from the request
        token = request.headers.get("Authorization")
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Forward the request to the Security service
        response = requests.post(
            f"{SECURITY_URL}/auth/update-preferences",
            headers={"Authorization": token},
            json=data.dict(),
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            detail = response.json().get("detail", "Failed to update preferences")
            raise HTTPException(status_code=response.status_code, detail=detail)
    except Exception as e:
        logger.error(f"Error updating preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/change-password")
async def change_password(request: Request, data: ChangePasswordRequest):
    """Forward change password request to Security service"""
    try:
        # Get the token from the request
        token = request.headers.get("Authorization")
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Forward the request to the Security service
        response = requests.post(
            f"{SECURITY_URL}/auth/change-password",
            headers={"Authorization": token},
            json=data.dict(),
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            detail = response.json().get("detail", "Failed to change password")
            raise HTTPException(status_code=response.status_code, detail=detail)
    except requests.RequestException as e:
        logger.error(f"Error connecting to Security service: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Security service unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error changing password: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/me")
async def get_user_info(request: Request):
    """Get current user information"""
    try:
        # Get the token from the request
        token = request.headers.get("Authorization")
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Forward the request to the Security service
        response = requests.get(
            f"{SECURITY_URL}/auth/me",
            headers={"Authorization": token},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            detail = response.json().get("detail", "Failed to get user information")
            raise HTTPException(status_code=response.status_code, detail=detail)
    except requests.RequestException as e:
        logger.error(f"Error connecting to Security service: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Security service unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error getting user info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
