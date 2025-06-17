import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from models.database_models import UserInvitation
from models.api_models import InviteUserRequest, VerifyOTPRequest, CompleteRegistrationRequest
from config.database import get_database
from services.auth_service import AuthService
from repositories.audit_repository import AuditRepository
import os

logger = logging.getLogger(__name__)


class InvitationService:
    """Service for managing user invitations with OTP"""
    
    @staticmethod
    async def send_invitation(
        invite_data: InviteUserRequest, 
        invited_by_user_id: str
    ) -> dict:
        """Send invitation to user with OTP"""
        try:
            db = get_database()
            invitations_collection = db.invitations
            
            # Check if user already exists
            users_collection = db.users
            existing_user = await users_collection.find_one({"email": invite_data.email})
            if existing_user:
                raise ValueError("User with this email already exists")
            
            # Check if there's already a pending invitation
            existing_invitation = await invitations_collection.find_one({
                "email": invite_data.email,
                "status": "invited"
            })
            
            if existing_invitation:
                # Update existing invitation with new OTP
                invitation = UserInvitation(**existing_invitation)
                invitation.otp = invitation.__class__.__dict__['otp'].default_factory()
                invitation.created_at = datetime.utcnow()
                invitation.expires_at = datetime.utcnow() + timedelta(hours=24)
                invitation.activation_attempts = 0
                
                await invitations_collection.update_one(
                    {"_id": invitation.id},
                    {"$set": invitation.dict(exclude={"id"})}
                )
            else:
                # Create new invitation
                invitation = UserInvitation(
                    email=invite_data.email,
                    full_name=invite_data.full_name,
                    role=invite_data.role,
                    phone_number=invite_data.phoneNo,
                    invited_by=invited_by_user_id
                )
                
                result = await invitations_collection.insert_one(invitation.dict(exclude={"id"}))
                invitation.id = result.inserted_id
            
            # Send email with OTP
            await InvitationService._send_invitation_email(invitation)
            
            # Log the invitation
            await AuditRepository.log_security_event(
                user_id=invited_by_user_id,
                action="user_invited",
                details={
                    "invited_email": invite_data.email,
                    "invited_role": invite_data.role,
                    "invitation_id": str(invitation.id)
                }
            )
            
            return {
                "message": "Invitation sent successfully",
                "invitation_id": str(invitation.id),
                "email": invite_data.email,
                "expires_at": invitation.expires_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error sending invitation: {str(e)}")
            raise
    
    @staticmethod
    async def verify_otp(verify_data: VerifyOTPRequest) -> dict:
        """Verify OTP for invitation"""
        try:
            db = get_database()
            invitations_collection = db.invitations
            
            # Find invitation
            invitation_doc = await invitations_collection.find_one({
                "email": verify_data.email,
                "status": "invited"
            })
            
            if not invitation_doc:
                raise ValueError("No pending invitation found for this email")
            
            invitation = UserInvitation(**invitation_doc)
            
            # Check if invitation is valid
            if not invitation.is_valid_for_activation():
                if invitation.is_expired():
                    raise ValueError("Invitation has expired")
                elif invitation.activation_attempts >= invitation.max_attempts:
                    raise ValueError("Maximum verification attempts exceeded")
                else:
                    raise ValueError("Invalid invitation status")
            
            # Verify OTP
            if invitation.otp != verify_data.otp:
                # Increment attempts
                await invitations_collection.update_one(
                    {"_id": invitation.id},
                    {"$inc": {"activation_attempts": 1}}
                )
                raise ValueError("Invalid OTP")
            
            return {
                "message": "OTP verified successfully",
                "email": verify_data.email,
                "full_name": invitation.full_name,
                "role": invitation.role
            }
            
        except Exception as e:
            logger.error(f"Error verifying OTP: {str(e)}")
            raise
    
    @staticmethod
    async def complete_registration(registration_data: CompleteRegistrationRequest) -> dict:
        """Complete user registration after OTP verification"""
        try:
            db = get_database()
            invitations_collection = db.invitations
            
            # Find and verify invitation again
            invitation_doc = await invitations_collection.find_one({
                "email": registration_data.email,
                "otp": registration_data.otp,
                "status": "invited"
            })
            
            if not invitation_doc:
                raise ValueError("Invalid invitation or OTP")
            
            invitation = UserInvitation(**invitation_doc)
            
            if not invitation.is_valid_for_activation():
                raise ValueError("Invitation is no longer valid")
            
            # Create user account
            signup_data = {
                "full_name": invitation.full_name,
                "email": invitation.email,
                "password": registration_data.password,
                "role": invitation.role,
                "phoneNo": invitation.phone_number,
                "details": {},
                "preferences": {}
            }
            
            # Use existing signup service to create user
            token_response = await AuthService.signup_user(signup_data)
            
            # Mark invitation as activated
            await invitations_collection.update_one(
                {"_id": invitation.id},
                {"$set": {"status": "activated", "activated_at": datetime.utcnow()}}
            )
            
            # Log successful activation
            if hasattr(AuditRepository, 'log_security_event'):
                await AuditRepository.log_security_event(
                    user_id=token_response.user_id,
                    action="invitation_activated",
                    details={
                        "invitation_id": str(invitation.id),
                        "email": invitation.email
                    }
                )
            
            return {
                "message": "Registration completed successfully",
                "access_token": token_response.access_token,
                "token_type": token_response.token_type,
                "user_id": token_response.user_id,
                "role": token_response.role,
                "permissions": token_response.permissions
            }
            
        except Exception as e:
            logger.error(f"Error completing registration: {str(e)}")
            raise
    
    @staticmethod
    async def get_pending_invitations(requester_user_id: str, requester_role: str) -> List[dict]:
        """Get list of pending invitations"""
        try:
            db = get_database()
            invitations_collection = db.invitations
            
            # Build query based on user role
            query = {"status": "invited"}
            if requester_role == "fleet_manager":
                # Fleet managers can only see invitations they sent for drivers
                query.update({
                    "invited_by": requester_user_id,
                    "role": "driver"
                })
            elif requester_role != "admin":
                # Non-admin, non-fleet-manager users can't see invitations
                return []
            
            # Get pending invitations
            cursor = invitations_collection.find(query)
            invitations = []
            
            async for doc in cursor:
                invitation = UserInvitation(**doc)
                invitations.append({
                    "id": str(invitation.id),
                    "email": invitation.email,
                    "full_name": invitation.full_name,
                    "role": invitation.role,
                    "phone_number": invitation.phone_number,
                    "created_at": invitation.created_at.isoformat(),
                    "expires_at": invitation.expires_at.isoformat(),
                    "is_expired": invitation.is_expired(),
                    "activation_attempts": invitation.activation_attempts
                })
            
            return invitations
            
        except Exception as e:
            logger.error(f"Error getting pending invitations: {str(e)}")
            raise
    
    @staticmethod
    async def resend_invitation(email: str, requester_user_id: str) -> dict:
        """Resend invitation OTP"""
        try:
            db = get_database()
            invitations_collection = db.invitations
            
            # Find invitation
            invitation_doc = await invitations_collection.find_one({
                "email": email,
                "status": "invited"
            })
            
            if not invitation_doc:
                raise ValueError("No pending invitation found for this email")
            
            invitation = UserInvitation(**invitation_doc)
            
            # Generate new OTP and extend expiry
            invitation.otp = invitation.__class__.__dict__['otp'].default_factory()
            invitation.expires_at = datetime.utcnow() + timedelta(hours=24)
            invitation.activation_attempts = 0
            
            # Update in database
            await invitations_collection.update_one(
                {"_id": invitation.id},
                {"$set": {
                    "otp": invitation.otp,
                    "expires_at": invitation.expires_at,
                    "activation_attempts": 0
                }}
            )
            
            # Send new email
            await InvitationService._send_invitation_email(invitation)
            
            return {
                "message": "Invitation resent successfully",
                "email": email,
                "expires_at": invitation.expires_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error resending invitation: {str(e)}")
            raise
    
    @staticmethod
    async def _send_invitation_email(invitation: UserInvitation):
        """Send invitation email with OTP"""
        try:            # Email configuration from environment
            smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
            smtp_username = os.getenv("SMTP_USERNAME")
            smtp_password = os.getenv("SMTP_PASSWORD")
            from_email = os.getenv("FROM_EMAIL", smtp_username)
            frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
            
            if not all([smtp_username, smtp_password]):
                logger.warning("SMTP configuration not found, skipping email send")
                return
            
            # Create activation link
            activation_link = f"{frontend_url}/activate?email={invitation.email}"
            
            # Create email
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = invitation.email
            msg['Subject'] = "Welcome to SAMFMS - Complete Your Registration"
            
            # Email body with HTML formatting
            html_body = f"""
            <html>
            <body>
                <h2>Welcome to SAMFMS</h2>
                <p>Hello <strong>{invitation.full_name}</strong>,</p>
                
                <p>You have been invited to join SAMFMS as a <strong>{invitation.role.replace('_', ' ').title()}</strong>.</p>
                
                <p>To complete your registration, please use the following One-Time Password (OTP):</p>
                
                <div style="background-color: #f0f0f0; padding: 15px; margin: 10px 0; border-radius: 5px;">
                    <h3 style="color: #0066cc;">OTP: {invitation.otp}</h3>
                </div>
                
                <p><strong>Click the link below to activate your account:</strong></p>
                <p><a href="{activation_link}" style="background-color: #0066cc; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">Activate Account</a></p>
                
                <p>Or copy and paste this link into your browser:</p>
                <p><a href="{activation_link}">{activation_link}</a></p>
                
                <p><strong>Steps to activate your account:</strong></p>
                <ol>
                    <li>Click the activation link above or go to: <a href="{activation_link}">{activation_link}</a></li>
                    <li>Your email address will be pre-filled: <strong>{invitation.email}</strong></li>
                    <li>Enter the OTP: <strong>{invitation.otp}</strong></li>
                    <li>Choose a username and password</li>
                    <li>Complete your profile information</li>
                </ol>
                
                <p><strong>⚠️ Important:</strong> This OTP will expire on <strong>{invitation.expires_at.strftime('%Y-%m-%d at %H:%M UTC')}</strong>.</p>
                
                <p>If you did not expect this invitation, please ignore this email.</p>
                
                <hr>
                <p>Best regards,<br>
                <strong>SAMFMS Team</strong><br>
                South African Fleet Management System</p>
            </body>
            </html>
            """
            
            # Also create a plain text version
            text_body = f"""
            Hello {invitation.full_name},
            
            You have been invited to join SAMFMS as a {invitation.role.replace('_', ' ').title()}.
            
            To complete your registration, please use the following One-Time Password (OTP):
            
            OTP: {invitation.otp}
            
            Click this link to activate your account:
            {activation_link}
            
            Steps to activate your account:
            1. Click the activation link above or go to: {activation_link}
            2. Your email address will be pre-filled: {invitation.email}
            3. Enter the OTP: {invitation.otp}
            4. Choose a username and password
            5. Complete your profile information
            
            ⚠️ Important: This OTP will expire on {invitation.expires_at.strftime('%Y-%m-%d at %H:%M UTC')}.
            
            If you did not expect this invitation, please ignore this email.
            
            Best regards,
            SAMFMS Team
            South African Fleet Management System
            """
            
            # Attach both HTML and plain text versions
            msg.attach(MIMEText(text_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))
            
            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Invitation email sent to {invitation.email}")
            
        except Exception as e:
            logger.error(f"Failed to send invitation email to {invitation.email}: {str(e)}")
            # Don't raise exception - invitation should still be created even if email fails
