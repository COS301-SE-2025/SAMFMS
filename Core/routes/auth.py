from fastapi import APIRouter, HTTPException, Request
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
        else:
            # Fallback: Try to get user count if direct endpoint doesn't exist
            count_response = requests.get(
                f"{SECURITY_URL}/auth/users/count",
                timeout=5
            )
            
            if count_response.status_code == 200:
                data = count_response.json()
                return {"userExists": data.get("count", 0) > 0}
            else:
                logger.warning(f"Failed to check user existence: {response.status_code}")
                # Default to true for security (better to show login than expose signup unnecessarily)
                return {"userExists": True}
                
    except requests.RequestException as e:
        logger.error(f"Error connecting to Security service when checking user existence: {e}")
        # Default to true if we can't connect to the security service
        return {"userExists": True}
    except Exception as e:
        logger.error(f"Error checking user existence: {e}")
        return {"userExists": True}
