from fastapi import APIRouter, HTTPException, Depends, status
from models.api_models import InviteUserRequest, MessageResponse
from services.auth_service import AuthService
from services.user_service import UserService
from routes.auth_routes import get_current_user_secure
from repositories.audit_repository import AuditRepository
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Administration"])


@router.post("/invite-user")
async def invite_user(
    invite_data: InviteUserRequest,
    current_user: dict = Depends(get_current_user_secure)
):
    """Admin/Fleet Manager can invite users with specific roles"""
    try:
        # Check permissions
        if current_user["role"] not in ["admin", "fleet_manager"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin or Fleet Manager access required"
            )
        
        # Fleet managers can only invite drivers
        if current_user["role"] == "fleet_manager" and invite_data.role not in ["driver"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Fleet managers can only invite drivers"
            )
        
        # Create user through signup service
        user_data = invite_data.dict()
        token_response = await AuthService.signup_user(user_data)
        
        # Log invitation
        await AuditRepository.log_security_event(
            user_id=current_user["user_id"],
            action="user_invited",
            details={
                "invited_user_email": invite_data.email,
                "invited_user_role": invite_data.role
            }
        )
        
        return {
            "message": f"User invited successfully",
            "user_id": token_response.user_id,
            "role": token_response.role
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Invite user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to invite user: {str(e)}"
        )


@router.post("/activate-user/{user_id}")
async def activate_user(
    user_id: str,
    current_user: dict = Depends(get_current_user_secure)
):
    """Activate user account (Admin only)"""
    try:
        if current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        success = await UserService.toggle_user_status(
            user_id=user_id,
            is_active=True,
            modified_by=current_user["user_id"]
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {"message": "User activated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Activate user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate user"
        )


@router.post("/deactivate-user/{user_id}")
async def deactivate_user(
    user_id: str,
    current_user: dict = Depends(get_current_user_secure)
):
    """Deactivate user account (Admin only)"""
    try:
        if current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        # Cannot deactivate yourself
        if current_user["user_id"] == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate your own account"
            )
        
        success = await UserService.toggle_user_status(
            user_id=user_id,
            is_active=False,
            modified_by=current_user["user_id"]
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {"message": "User deactivated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deactivate user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate user"
        )


@router.get("/security-metrics")
async def get_security_metrics(current_user: dict = Depends(get_current_user_secure)):
    """Get security metrics (Admin only)"""
    try:
        if current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        metrics = await AuditRepository.get_security_metrics()
        return {"metrics": metrics}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get security metrics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get security metrics"
        )
