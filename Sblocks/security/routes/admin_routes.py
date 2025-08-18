from fastapi import APIRouter, HTTPException, Depends, status
from models.api_models import InviteUserRequest, MessageResponse, VerifyOTPRequest, CompleteRegistrationRequest, ResendOTPRequest, CreateUserRequest
from services.auth_service import AuthService
from services.user_service import UserService
from services.invitation_service import InvitationService, InvitationError
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
        
        # Validate role assignment permissions
        if current_user["role"] == "fleet_manager":
            # Fleet managers can only invite drivers
            if invite_data.role not in ["driver"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Fleet managers can only invite drivers"
                )
        elif current_user["role"] == "admin":
            # Admins can invite anyone but validate role exists
            valid_roles = ["admin", "fleet_manager", "driver"]
            if invite_data.role not in valid_roles:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid role. Valid roles are: {', '.join(valid_roles)}"
                )
        
        # Additional validation: prevent admins from creating too many admin users
        if invite_data.role == "admin":
            # Check existing admin count
            from config.database import get_database
            db = get_database()
            admin_count = await db.users.count_documents({"role": "admin"})
            if admin_count >= 5:  # Limit to 5 admins max
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Maximum number of admin users reached"
                )
        
        # Send invitation through invitation service
        result = await InvitationService.send_invitation(
            invite_data=invite_data,
            invited_by_user_id=current_user["user_id"]
        )
        
        return result
        
    except InvitationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
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
        
    except InvitationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
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
        
        # For fleet managers, verify they can resend this specific invitation
        if current_user["role"] == "fleet_manager":
            from config.database import get_database
            db = get_database()
            invitation = await db.invitations.find_one({
                "email": resend_data.email.lower(),
                "status": "invited"
            })
            if not invitation or invitation.get("invited_by") != current_user["user_id"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only resend invitations you sent"
                )
        
        result = await InvitationService.resend_invitation(
            email=resend_data.email,
            requester_user_id=current_user["user_id"]
        )
        
        return result
        
    except InvitationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resending invitation: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to resend invitation")


@router.delete("/cancel-invitation")
async def cancel_invitation(
    email: str,
    current_user: dict = Depends(get_current_user_secure)
):
    """Cancel a pending invitation"""
    try:
        # Check permissions
        if current_user["role"] not in ["admin", "fleet_manager"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin or Fleet Manager access required"
            )
        
        # For fleet managers, verify they can cancel this specific invitation
        if current_user["role"] == "fleet_manager":
            from config.database import get_database
            db = get_database()
            invitation = await db.invitations.find_one({
                "email": email.lower(),
                "status": "invited"
            })
            if not invitation or invitation.get("invited_by") != current_user["user_id"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only cancel invitations you sent"
                )
        
        result = await InvitationService.cancel_invitation(
            email=email,
            requester_user_id=current_user["user_id"]
        )
        
        return result
        
    except InvitationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling invitation: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to cancel invitation")


## Public endpoints for user activation

@router.post("/verify-otp")
async def verify_otp(verify_data: VerifyOTPRequest):
    """Verify OTP for invitation (public endpoint)"""
    try:
        result = await InvitationService.verify_otp(verify_data)
        return result
        
    except InvitationError as e:
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
        
    except InvitationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error completing registration: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to complete registration")


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


@router.post("/create-user")
async def create_user_manually(
    user_data: CreateUserRequest,
    current_user: dict = Depends(get_current_user_secure)
):
    """Admin can manually create a user without invitation flow"""
    # Log the incoming request data received by the Security service
    logger.info(f"Security service received user creation request with data: {user_data.model_dump() if user_data else 'None'}")
    try:
        # Only admins can create users directly
        if current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required for manual user creation"
            )
        
        # Additional validation for admin users
        if user_data.role == "admin":
            # Check existing admin count
            from config.database import get_database
            db = get_database()
            admin_count = await db.users.count_documents({"role": "admin"})
            if admin_count >= 5:  # Limit to 5 admins max
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Maximum number of admin users reached"
                )
        
        # Create user through user service
        result = await UserService.create_user_manually(
            user_data=user_data,
            created_by_user_id=current_user["user_id"]
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user")
