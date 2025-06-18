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


@router.get("/user-exists")
async def check_user_existence():
    """Check if any users exist in the system"""
    try:
        from repositories.user_repository import UserRepository
        user_count = await UserRepository.count_users()
        return {"userExists": user_count > 0}
    except Exception as e:
        logger.error(f"Error checking user existence: {e}")
        # Default to False for better UX - if we can't check, assume no users for initial setup
        return {"userExists": False}


@router.get("/users/count")
async def get_user_count():
    """Get total count of users in the system"""
    try:
        from repositories.user_repository import UserRepository
        user_count = await UserRepository.count_users()
        return {"count": user_count}
    except Exception as e:
        logger.error(f"Error getting user count: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user count"
        )


@router.post("/verify-token")
async def verify_token(current_user: dict = Depends(get_current_user_secure)):
    """Verify a JWT token and return user information (used by other services)"""
    try:
        # Return user information without sensitive data
        user_info = {k: v for k, v in current_user.items() 
                    if k not in ["password_hash", "token", "_id"]}
        return user_info
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


@router.get("/roles")
async def get_roles():
    """Get available roles and their permissions"""
    try:
        # Get roles from a predefined configuration
        # This could be fetched from a database in a real implementation
        roles = [
            {
                "id": "admin",
                "name": "Administrator",
                "description": "Full system access",
                "permissions": ["users:manage", "vehicles:manage", "trips:manage", "system:manage", "reports:view"]
            },
            {
                "id": "fleet_manager",
                "name": "Fleet Manager",
                "description": "Manage fleet operations",
                "permissions": ["vehicles:manage", "drivers:manage", "trips:manage", "reports:view"]
            },
            {
                "id": "driver",
                "name": "Driver",
                "description": "Driver access only",
                "permissions": ["trips:view", "profile:manage"]
            }
        ]
        
        return {"roles": roles}
    except Exception as e:
        logger.error(f"Error getting roles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get roles"
        )
