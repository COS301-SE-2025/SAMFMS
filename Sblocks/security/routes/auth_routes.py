from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models.api_models import SignupRequest, LoginRequest, TokenResponse, MessageResponse
from services.auth_service import AuthService
from utils.auth_utils import get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


async def get_current_user_secure(token: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user with comprehensive security checks"""
    try:
        return await AuthService.get_current_user_secure(token.credentials)
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


@router.post("/signup", response_model=TokenResponse)
async def signup(user_data: SignupRequest):
    """Register a new user"""
    try:
        return await AuthService.signup_user(user_data.dict())
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )


@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest, request: Request):
    """Authenticate user and return access token"""
    try:
        client_ip = str(request.client.host) if request.client else "unknown"
        return await AuthService.login_user(login_data.email, login_data.password, client_ip)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login error: {str(e)}"
        )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: dict = Depends(get_current_user_secure),
    request: Request = None
):
    """Logout user and invalidate token"""
    try:
        token = current_user.get("token")
        if token:
            await AuthService.logout_user(token)
        
        return MessageResponse(message="Successfully logged out")
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout error: {str(e)}"
        )


@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user_secure)):
    """Get current user information"""
    try:
        # Remove sensitive data
        user_info = {k: v for k, v in current_user.items() 
                    if k not in ["password_hash", "token", "_id"]}
        return user_info
    except Exception as e:
        logger.error(f"Get user info error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )
