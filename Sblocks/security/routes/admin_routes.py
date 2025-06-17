from fastapi import APIRouter, HTTPException, Depends, status
from models.api_models import InviteUserRequest, MessageResponse, VerifyOTPRequest, CompleteRegistrationRequest, ResendOTPRequest
from services.auth_service import AuthService
from services.user_service import UserService
from services.invitation_service import InvitationService
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
    """Admin/Fleet Manager can invite users with OTP-based registration"""
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
        
        # Send invitation through new invitation service
        result = await InvitationService.send_invitation(
            invite_data=invite_data,
            invited_by_user_id=current_user["user_id"]
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error inviting user: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to invite user")


@router.get("/pending-invitations")
async def get_pending_invitations(
    current_user: dict = Depends(get_current_user_secure)
):
    """Get list of pending invitations"""
    try:
        # Check permissions
        if current_user["role"] not in ["admin", "fleet_manager"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin or Fleet Manager access required"
            )
        
        invitations = await InvitationService.get_pending_invitations(
            requester_user_id=current_user["user_id"],
            requester_role=current_user["role"]
        )
        
        return {"invitations": invitations}
        
    except Exception as e:
        logger.error(f"Error getting pending invitations: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get invitations")


@router.post("/resend-invitation")
async def resend_invitation(
    resend_data: ResendOTPRequest,
    current_user: dict = Depends(get_current_user_secure)
):
    """Resend invitation OTP"""
    try:
        # Check permissions
        if current_user["role"] not in ["admin", "fleet_manager"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin or Fleet Manager access required"
            )
        
        result = await InvitationService.resend_invitation(
            email=resend_data.email,
            requester_user_id=current_user["user_id"]
        )
        
        return result        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error resending invitation: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to resend invitation")


## Public endpoints for user activation

@router.post("/verify-otp")
async def verify_otp(verify_data: VerifyOTPRequest):
    """Verify OTP for invitation (public endpoint)"""
    try:
        result = await InvitationService.verify_otp(verify_data)
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error verifying OTP: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to verify OTP")


@router.post("/complete-registration")
async def complete_registration(registration_data: CompleteRegistrationRequest):
    """Complete user registration after OTP verification (public endpoint)"""
    try:
        result = await InvitationService.complete_registration(registration_data)
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error completing registration: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to complete registration")


# ...existing code...


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
