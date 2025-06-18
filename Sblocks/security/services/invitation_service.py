import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import asyncio
import re

from models.database_models import UserInvitation
from models.api_models import InviteUserRequest, VerifyOTPRequest, CompleteRegistrationRequest
from config.database import get_database
from services.auth_service import AuthService
from repositories.audit_repository import AuditRepository
import os

logger = logging.getLogger(__name__)


class InvitationError(Exception):
    """Custom exception for invitation-related errors"""
    pass


class InvitationService:
    """Service for managing user invitations with OTP"""
    
    # Rate limiting storage (in production, use Redis)
    _rate_limit_storage: Dict[str, List[datetime]] = {}
    
    @staticmethod
    async def _check_rate_limit(email: str, max_attempts: int = 5, window_minutes: int = 15) -> bool:
        """Check if email is within rate limit for OTP requests"""
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=window_minutes)
        
        if email not in InvitationService._rate_limit_storage:
            InvitationService._rate_limit_storage[email] = []
        
        # Clean old attempts
        InvitationService._rate_limit_storage[email] = [
            attempt for attempt in InvitationService._rate_limit_storage[email]
            if attempt > window_start
        ]
        
        # Check if under limit
        if len(InvitationService._rate_limit_storage[email]) >= max_attempts:
            return False
        
        # Add current attempt
        InvitationService._rate_limit_storage[email].append(now)
        return True
    
    @staticmethod
    async def send_invitation(
        invite_data: InviteUserRequest, 
        invited_by_user_id: str
    ) -> dict:
        """Send invitation to user with OTP"""
        try:
            # Validate invite data
            if not invite_data.email or not invite_data.full_name:
                raise InvitationError("Email and full name are required")
            
            # Check rate limiting
            if not await InvitationService._check_rate_limit(invite_data.email.lower()):
                raise InvitationError("Too many invitation requests. Please try again later.")
            
            db = get_database()
            invitations_collection = db.invitations
            
            # Check if user already exists
            users_collection = db.users
            existing_user = await users_collection.find_one({"email": invite_data.email.lower()})
            if existing_user:
                raise InvitationError("User with this email already exists")
            
            # Check if there's already a pending invitation
            existing_invitation = await invitations_collection.find_one({
                "email": invite_data.email.lower(),
                "status": "invited"
            })
            
            if existing_invitation:
                # Update existing invitation with new OTP
                invitation = UserInvitation(**existing_invitation)
                
                # Check if can resend
                if not invitation.can_resend_otp():
                    if invitation.resend_count >= invitation.max_resends:
                        raise InvitationError("Maximum resend limit reached for this invitation")
                    else:
                        raise InvitationError("Please wait before requesting another OTP")
                
                # Generate new OTP and update
                invitation.generate_otp()
                invitation.expires_at = datetime.utcnow() + timedelta(hours=24)
                invitation.activation_attempts = 0
                invitation.mark_otp_sent()
                
                await invitations_collection.update_one(
                    {"_id": invitation.id},
                    {"$set": invitation.dict(exclude={"id"})}
                )
            else:
                # Create new invitation
                invitation = UserInvitation(
                    email=invite_data.email.lower(),
                    full_name=invite_data.full_name.strip(),
                    role=invite_data.role,
                    phone_number=invite_data.phoneNo,
                    invited_by=invited_by_user_id
                )
                
                # Generate OTP
                invitation.generate_otp()
                invitation.mark_otp_sent()
                
                result = await invitations_collection.insert_one(invitation.dict(exclude={"id"}))
                invitation.id = result.inserted_id
              # Try to send email with OTP
            email_sent = await InvitationService._send_invitation_email_with_retry(invitation)
            
            if not email_sent:
                # If email fails, mark invitation for retry but don't block the process
                await invitations_collection.update_one(
                    {"_id": invitation.id},
                    {"$set": {
                        "email_status": "pending_retry", 
                        "retry_count": 0,
                        "next_retry": datetime.utcnow() + timedelta(minutes=5),
                        "last_error": "Email sending temporarily unavailable"
                    }}
                )
                
                logger.warning(f"Email sending failed for {invitation.email} - will retry later")
                
                # Log the event for tracking
                await AuditRepository.log_security_event(
                    user_id=invited_by_user_id,
                    action="invitation_email_queued",
                    details={
                        "invited_email": invite_data.email,
                        "invitation_id": str(invitation.id)
                    }
                )
                
                # Return success but note that email is queued
                return {
                    "message": "Invitation created successfully. Email will be sent when the service is available.",
                    "invitation_id": str(invitation.id),
                    "email": invite_data.email,
                    "expires_at": invitation.expires_at.isoformat(),
                    "email_status": "queued"
                }
            
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
            
        except InvitationError:
            raise
        except Exception as e:
            logger.error(f"Error sending invitation: {str(e)}")
            raise InvitationError("Failed to send invitation. Please try again later.")
    
    @staticmethod
    async def verify_otp(verify_data: VerifyOTPRequest) -> dict:
        """Verify OTP for invitation"""
        try:
            # Check rate limiting for OTP verification
            if not await InvitationService._check_rate_limit(f"verify_{verify_data.email.lower()}", max_attempts=10):
                raise InvitationError("Too many verification attempts. Please try again later.")
            
            db = get_database()
            invitations_collection = db.invitations
            
            # Find invitation
            invitation_doc = await invitations_collection.find_one({
                "email": verify_data.email.lower(),
                "status": "invited"
            })
            
            if not invitation_doc:
                # Log failed attempt
                await AuditRepository.log_security_event(
                    user_id="anonymous",
                    action="otp_verification_failed",
                    details={"email": verify_data.email, "reason": "No pending invitation"}
                )
                raise InvitationError("No pending invitation found for this email")
            
            invitation = UserInvitation(**invitation_doc)
            
            # Check if invitation is valid
            if not invitation.is_valid_for_activation():
                if invitation.is_expired():
                    await invitations_collection.update_one(
                        {"_id": invitation.id},
                        {"$set": {"status": "expired"}}
                    )
                    raise InvitationError("Invitation has expired")
                elif invitation.activation_attempts >= invitation.max_attempts:
                    await invitations_collection.update_one(
                        {"_id": invitation.id},
                        {"$set": {"status": "attempts_exceeded"}}
                    )
                    raise InvitationError("Maximum verification attempts exceeded")
                else:
                    raise InvitationError("Invalid invitation status")
            
            # Verify OTP
            if invitation.otp != verify_data.otp:
                # Increment attempts
                invitation.increment_attempts()
                await invitations_collection.update_one(
                    {"_id": invitation.id},
                    {"$set": {"activation_attempts": invitation.activation_attempts}}
                )
                
                # Log failed attempt
                await AuditRepository.log_security_event(
                    user_id="anonymous",
                    action="otp_verification_failed",
                    details={"email": verify_data.email, "attempts": invitation.activation_attempts}
                )
                
                raise InvitationError("Invalid OTP")
            
            # Log successful verification
            await AuditRepository.log_security_event(
                user_id="anonymous",
                action="otp_verified",
                details={"email": verify_data.email, "invitation_id": str(invitation.id)}
            )
            
            return {
                "message": "OTP verified successfully",
                "email": verify_data.email,
                "full_name": invitation.full_name,
                "role": invitation.role
            }
            
        except InvitationError:
            raise
        except Exception as e:
            logger.error(f"Error verifying OTP: {str(e)}")
            raise InvitationError("Failed to verify OTP. Please try again.")
    
    @staticmethod
    async def complete_registration(registration_data: CompleteRegistrationRequest) -> dict:
        """Complete user registration after OTP verification"""
        try:
            db = get_database()
            invitations_collection = db.invitations
            
            # Find and verify invitation again
            invitation_doc = await invitations_collection.find_one({
                "email": registration_data.email.lower(),
                "otp": registration_data.otp,
                "status": "invited"
            })
            
            if not invitation_doc:
                raise InvitationError("Invalid invitation or OTP")
            
            invitation = UserInvitation(**invitation_doc)
            
            if not invitation.is_valid_for_activation():
                raise InvitationError("Invitation is no longer valid")
            
            # Generate username if not provided
            username = registration_data.username
            if not username:
                username = registration_data.email.split('@')[0]
                # Ensure username is unique
                users_collection = db.users
                counter = 1
                original_username = username
                while await users_collection.find_one({"username": username}):
                    username = f"{original_username}{counter}"
                    counter += 1
            
            # Get default preferences from UserProfile model
            from models.database_models import UserProfile
            default_preferences = UserProfile().preferences
            
            # Create user account
            signup_data = {
                "full_name": invitation.full_name,
                "email": invitation.email,
                "password": registration_data.password,
                "role": invitation.role,
                "phoneNo": invitation.phone_number,
                "details": {},
                "preferences": default_preferences,  # Use default preferences
                "username": username
            }
            
            # Use existing signup service to create user
            token_response = await AuthService.signup_user(signup_data)
            
            # Mark invitation as activated
            await invitations_collection.update_one(
                {"_id": invitation.id},
                {"$set": {"status": "activated", "activated_at": datetime.utcnow()}}
            )
            
            # Log successful activation
            await AuditRepository.log_security_event(
                user_id=token_response.user_id,
                action="invitation_activated",
                details={
                    "invitation_id": str(invitation.id),
                    "email": invitation.email,
                    "username": username
                }
            )
            
            return {
                "message": "Registration completed successfully",
                "access_token": token_response.access_token,
                "token_type": token_response.token_type,
                "user_id": token_response.user_id,
                "role": token_response.role,
                "permissions": token_response.permissions,
                "preferences": token_response.preferences,  # Include preferences in response
                "username": username
            }
            
        except InvitationError:
            raise
        except Exception as e:
            logger.error(f"Error completing registration: {str(e)}")
            raise InvitationError("Failed to complete registration. Please try again.")
    
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
            cursor = invitations_collection.find(query).sort("created_at", -1)
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
                    "activation_attempts": invitation.activation_attempts,
                    "resend_count": invitation.resend_count,
                    "can_resend": invitation.can_resend_otp()
                })
            
            return invitations
            
        except Exception as e:
            logger.error(f"Error getting pending invitations: {str(e)}")
            raise InvitationError("Failed to retrieve invitations")
    
    @staticmethod
    async def resend_invitation(email: str, requester_user_id: str) -> dict:
        """Resend invitation OTP"""
        try:
            # Check rate limiting
            if not await InvitationService._check_rate_limit(f"resend_{email.lower()}"):
                raise InvitationError("Too many resend requests. Please try again later.")
            
            db = get_database()
            invitations_collection = db.invitations
            
            # Find invitation
            invitation_doc = await invitations_collection.find_one({
                "email": email.lower(),
                "status": "invited"
            })
            
            if not invitation_doc:
                raise InvitationError("No pending invitation found for this email")
            
            invitation = UserInvitation(**invitation_doc)
            
            # Check if can resend
            if not invitation.can_resend_otp():
                if invitation.resend_count >= invitation.max_resends:
                    raise InvitationError("Maximum resend limit reached")
                else:
                    raise InvitationError("Please wait before requesting another OTP")
            
            # Generate new OTP and extend expiry
            invitation.generate_otp()
            invitation.expires_at = datetime.utcnow() + timedelta(hours=24)
            invitation.activation_attempts = 0
            invitation.mark_otp_sent()
            
            # Update in database
            await invitations_collection.update_one(
                {"_id": invitation.id},
                {"$set": {
                    "otp": invitation.otp,
                    "expires_at": invitation.expires_at,
                    "activation_attempts": 0,
                    "last_otp_sent": invitation.last_otp_sent,
                    "resend_count": invitation.resend_count
                }}
            )
            
            # Send new email
            email_sent = await InvitationService._send_invitation_email_with_retry(invitation)
            
            if not email_sent:
                raise InvitationError("Failed to send invitation email")
            
            # Log resend
            await AuditRepository.log_security_event(
                user_id=requester_user_id,
                action="invitation_resent",
                details={"email": email, "resend_count": invitation.resend_count}
            )
            
            return {
                "message": "Invitation resent successfully",
                "email": email,
                "expires_at": invitation.expires_at.isoformat()
            }
            
        except InvitationError:
            raise
        except Exception as e:
            logger.error(f"Error resending invitation: {str(e)}")
            raise InvitationError("Failed to resend invitation")
    
    @staticmethod
    async def _send_invitation_email_with_retry(invitation: UserInvitation, max_retries: int = 3) -> bool:
        """Send invitation email with retry logic"""
        for attempt in range(max_retries):
            try:
                await InvitationService._send_invitation_email(invitation)
                return True
            except Exception as e:
                logger.warning(f"Email send attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"All email send attempts failed for {invitation.email}")
        return False
    @staticmethod
    async def _send_invitation_email(invitation: UserInvitation):
        """Send invitation email with OTP"""
        try:
            # Email configuration from environment
            smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
            smtp_username = os.getenv("SMTP_USERNAME")
            smtp_password = os.getenv("SMTP_PASSWORD")
            from_email = os.getenv("FROM_EMAIL", smtp_username)
            frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
            
            if not all([smtp_username, smtp_password]):
                logger.error("SMTP configuration not found")
                raise Exception("Email configuration not available")
            
            # Validate email configuration
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', from_email):
                raise Exception("Invalid sender email address")
            
            # Create activation link
            activation_link = f"{frontend_url}/activate?email={invitation.email}"
            
            # Create email
            msg = MIMEMultipart('alternative')
            msg['From'] = from_email
            msg['To'] = invitation.email
            msg['Subject'] = "Welcome to SAMFMS - Complete Your Registration"
            
            # Escape HTML content
            def escape_html(text):
                return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')
            
            escaped_name = escape_html(invitation.full_name)
            escaped_role = escape_html(invitation.role.replace('_', ' ').title())
            escaped_email = escape_html(invitation.email)
            
            # Email body with HTML formatting
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>SAMFMS Invitation</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #0066cc; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; background-color: #f9f9f9; }}
                    .otp-box {{ background-color: #e6f3ff; padding: 15px; margin: 20px 0; border-radius: 5px; text-align: center; }}
                    .otp {{ font-size: 24px; font-weight: bold; color: #0066cc; letter-spacing: 3px; }}
                    .button {{ background-color: #0066cc; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px 0; }}
                    .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
                    .warning {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; border-radius: 5px; margin: 10px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Welcome to SAMFMS</h1>
                    </div>
                    <div class="content">
                        <p>Hello <strong>{escaped_name}</strong>,</p>
                        
                        <p>You have been invited to join SAMFMS as a <strong>{escaped_role}</strong>.</p>
                        
                        <p>To complete your registration, please use the following One-Time Password (OTP):</p>
                        
                        <div class="otp-box">
                            <div class="otp">{invitation.otp}</div>
                        </div>
                        
                        <p><strong>Click the link below to activate your account:</strong></p>
                        <p><a href="{activation_link}" class="button">Activate Account</a></p>
                        
                        <p>Or copy and paste this link into your browser:</p>
                        <p><a href="{activation_link}">{activation_link}</a></p>
                        
                        <div class="warning">
                            <p><strong>⚠️ Important Security Information:</strong></p>
                            <ul>
                                <li>This OTP will expire on <strong>{invitation.expires_at.strftime('%Y-%m-%d at %H:%M UTC')}</strong></li>
                                <li>Never share your OTP with anyone</li>
                                <li>SAMFMS will never ask for your OTP via phone or email</li>
                                <li>If you did not request this invitation, please ignore this email</li>
                            </ul>
                        </div>
                        
                        <p><strong>Steps to activate your account:</strong></p>
                        <ol>
                            <li>Click the activation link above</li>
                            <li>Your email address will be pre-filled: <strong>{escaped_email}</strong></li>
                            <li>Enter the OTP: <strong>{invitation.otp}</strong></li>
                            <li>Choose a secure password</li>
                            <li>Complete your registration</li>
                        </ol>
                    </div>
                    <div class="footer">
                        <p>Best regards,<br>
                        <strong>SAMFMS Team</strong><br>
                        South African Fleet Management System</p>
                        <p>This is an automated email. Please do not reply to this message.</p>
                    </div>
                </div>
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
            4. Choose a secure password
            5. Complete your registration
            
            ⚠️ Important Security Information:
            - This OTP will expire on {invitation.expires_at.strftime('%Y-%m-%d at %H:%M UTC')}
            - Never share your OTP with anyone
            - SAMFMS will never ask for your OTP via phone or email
            - If you did not request this invitation, please ignore this email
            
            Best regards,
            SAMFMS Team
            South African Fleet Management System
            
            This is an automated email. Please do not reply to this message.
            """
            
            # Attach both HTML and plain text versions
            msg.attach(MIMEText(text_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))
              # Send email with timeout
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)  # 30 second timeout
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Invitation email sent successfully to {invitation.email}")
            
        except Exception as e:
            logger.error(f"Failed to send invitation email to {invitation.email}: {str(e)}")
            raise Exception(f"Email sending failed: {str(e)}")

    @staticmethod
    async def cleanup_expired_invitations():
        """Cleanup expired invitations - should be called periodically"""
        try:
            db = get_database()
            invitations_collection = db.invitations
            
            # Mark expired invitations
            now = datetime.utcnow()
            result = await invitations_collection.update_many(
                {
                    "status": "invited",
                    "expires_at": {"$lt": now}
                },
                {"$set": {"status": "expired"}}
            )
            
            logger.info(f"Marked {result.modified_count} invitations as expired")
              # Delete very old invitations (older than 30 days)
            cutoff_date = now - timedelta(days=30)
            delete_result = await invitations_collection.delete_many(
                {
                    "status": {"$in": ["expired", "activated", "cancelled"]},
                    "created_at": {"$lt": cutoff_date}
                }
            )
            
            logger.info(f"Deleted {delete_result.deleted_count} old invitations")
            
            # Also fail any very old pending retries (older than 7 days)
            old_retry_cutoff = now - timedelta(days=7)
            failed_result = await invitations_collection.update_many(
                {
                    "email_status": "pending_retry",
                    "created_at": {"$lt": old_retry_cutoff}
                },
                {"$set": {"email_status": "failed", "last_error": "Retry window expired"}}
            )
            
            if failed_result.modified_count > 0:
                logger.info(f"Marked {failed_result.modified_count} old email retries as failed")
            
        except Exception as e:
            logger.error(f"Error during invitation cleanup: {str(e)}")

    @staticmethod
    async def cancel_invitation(email: str, requester_user_id: str) -> dict:
        """Cancel a pending invitation"""
        try:
            db = get_database()
            invitations_collection = db.invitations
            
            # Find and cancel invitation
            result = await invitations_collection.update_one(
                {
                    "email": email.lower(),
                    "status": "invited"
                },
                {
                    "$set": {
                        "status": "cancelled",
                        "cancelled_at": datetime.utcnow(),
                        "cancelled_by": requester_user_id
                    }
                }
            )
            
            if result.matched_count == 0:
                raise InvitationError("No pending invitation found for this email")
            
            # Log cancellation
            await AuditRepository.log_security_event(
                user_id=requester_user_id,
                action="invitation_cancelled",
                details={"email": email}
            )
            
            return {"message": "Invitation cancelled successfully"}
            
        except InvitationError:
            raise
        except Exception as e:
            logger.error(f"Error cancelling invitation: {str(e)}")
            raise InvitationError("Failed to cancel invitation")
