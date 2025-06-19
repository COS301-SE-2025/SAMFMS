"""Unit tests for InvitationService."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

from services.invitation_service import InvitationService


class TestInvitationService:
    """Test InvitationService functionality."""
    
    @pytest.mark.asyncio
    async def test_send_invitation_success(self, mock_invitation_repository, test_invitation_data):
        """Test successful invitation sending."""
        mock_invitation_repository.find_by_email.return_value = None
        mock_invitation_repository.create_invitation.return_value = {"invitation_id": "inv-123"}
        
        with patch('services.invitation_service.InvitationRepository', mock_invitation_repository), \
             patch('services.invitation_service.generate_otp', return_value="123456"):
            
            result = await InvitationService.send_invitation(
                test_invitation_data["email"],
                test_invitation_data["full_name"],
                test_invitation_data["role"],
                test_invitation_data["invited_by"],
                test_invitation_data.get("phone_number")
            )
            
            assert result["message"] == "Invitation sent successfully"
            mock_invitation_repository.create_invitation.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_invitation_duplicate_email(self, mock_invitation_repository, test_invitation_data):
        """Test invitation sending with duplicate email."""
        mock_invitation_repository.find_by_email.return_value = test_invitation_data
        
        with patch('services.invitation_service.InvitationRepository', mock_invitation_repository):
            with pytest.raises(ValueError, match="Invitation already exists for this email"):
                await InvitationService.send_invitation(
                    test_invitation_data["email"],
                    test_invitation_data["full_name"],
                    test_invitation_data["role"],
                    test_invitation_data["invited_by"]
                )
    
    @pytest.mark.asyncio
    async def test_verify_otp_success(self, mock_invitation_repository, test_invitation_data):
        """Test successful OTP verification."""
        invitation = {**test_invitation_data, "expires_at": datetime.utcnow() + timedelta(hours=1)}
        mock_invitation_repository.find_by_otp.return_value = invitation
        
        with patch('services.invitation_service.InvitationRepository', mock_invitation_repository):
            result = await InvitationService.verify_otp(test_invitation_data["otp"])
            
            assert result["valid"] is True
            assert result["invitation"]["email"] == test_invitation_data["email"]
    
    @pytest.mark.asyncio
    async def test_verify_otp_expired(self, mock_invitation_repository, test_invitation_data):
        """Test OTP verification with expired invitation."""
        invitation = {**test_invitation_data, "expires_at": datetime.utcnow() - timedelta(hours=1)}
        mock_invitation_repository.find_by_otp.return_value = invitation
        
        with patch('services.invitation_service.InvitationRepository', mock_invitation_repository):
            result = await InvitationService.verify_otp(test_invitation_data["otp"])
            
            assert result["valid"] is False
            assert "expired" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_verify_otp_invalid(self, mock_invitation_repository):
        """Test OTP verification with invalid OTP."""
        mock_invitation_repository.find_by_otp.return_value = None
        
        with patch('services.invitation_service.InvitationRepository', mock_invitation_repository):
            result = await InvitationService.verify_otp("invalid_otp")
            
            assert result["valid"] is False
            assert "invalid" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_complete_registration_success(self, mock_invitation_repository, mock_user_repository):
        """Test successful registration completion."""
        invitation = {
            "email": "test@example.com",
            "full_name": "Test User",
            "role": "driver",
            "phone_number": "+1234567890"
        }
        registration_data = MagicMock()
        registration_data.password = "NewPassword123!"
        
        mock_invitation_repository.find_by_email.return_value = invitation
        mock_user_repository.find_by_email.return_value = None
        mock_user_repository.create_user.return_value = {"user_id": "new-user-123"}
        
        with patch('services.invitation_service.InvitationRepository', mock_invitation_repository), \
             patch('services.invitation_service.UserRepository', mock_user_repository), \
             patch('services.invitation_service.get_password_hash', return_value="hashed_password"):
            
            result = await InvitationService.complete_registration("test@example.com", registration_data)
            
            assert result["message"] == "Registration completed successfully"
            mock_user_repository.create_user.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_pending_invitations(self, mock_invitation_repository):
        """Test getting pending invitations."""
        mock_invitations = [
            {"email": "user1@example.com", "role": "driver"},
            {"email": "user2@example.com", "role": "fleet_manager"}
        ]
        mock_invitation_repository.get_pending_invitations.return_value = mock_invitations
        
        with patch('services.invitation_service.InvitationRepository', mock_invitation_repository):
            result = await InvitationService.get_pending_invitations()
            
            assert len(result["invitations"]) == 2
            mock_invitation_repository.get_pending_invitations.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_resend_invitation(self, mock_invitation_repository):
        """Test resending invitation."""
        invitation = {"email": "test@example.com", "full_name": "Test User"}
        mock_invitation_repository.find_by_email.return_value = invitation
        mock_invitation_repository.update_invitation.return_value = True
        
        with patch('services.invitation_service.InvitationRepository', mock_invitation_repository), \
             patch('services.invitation_service.generate_otp', return_value="654321"):
            
            result = await InvitationService.resend_invitation("test@example.com")
            
            assert result["message"] == "Invitation resent successfully"
            mock_invitation_repository.update_invitation.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cancel_invitation(self, mock_invitation_repository):
        """Test cancelling invitation."""
        mock_invitation_repository.find_by_email.return_value = {"email": "test@example.com"}
        mock_invitation_repository.delete_invitation.return_value = True
        
        with patch('services.invitation_service.InvitationRepository', mock_invitation_repository):
            result = await InvitationService.cancel_invitation("test@example.com")
            
            assert result["message"] == "Invitation cancelled successfully"
            mock_invitation_repository.delete_invitation.assert_called_once()
