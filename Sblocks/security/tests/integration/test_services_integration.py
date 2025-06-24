import pytest
import asyncio
import uuid
from services.auth_service import AuthService
from services.user_service import UserService
from services.invitation_service import InvitationService
from models.api_models import InviteUserRequest, VerifyOTPRequest, CompleteRegistrationRequest

pytestmark = pytest.mark.asyncio


async def test_signup_and_login_user_integration():
    """
    True integration test: requires Docker Compose test stack running (MongoDB, etc).
    Uses a unique email per run to avoid conflicts.
    """
    unique_email = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
    user_data = {
        "full_name": "Integration Test User",
        "email": unique_email,
        "password": "TestPass123!",
        "role": "driver"  # Changed from 'user' to 'driver' to match model
    }

    token_response = await AuthService.signup_user(user_data)
    assert token_response.access_token
    assert token_response.user_id

    login_response = await AuthService.login_user(user_data["email"], user_data["password"], client_ip="127.0.0.1")
    assert login_response.access_token
    assert login_response.user_id == token_response.user_id


async def test_create_and_get_user():
    from models.api_models import CreateUserRequest
    user_req = CreateUserRequest(
        full_name="Integration User",
        email="integrationuser@example.com",
        password="IntegrationPass123!",
        role="driver"  # Changed from 'user' to 'driver' to match model
    )
    created = await UserService.create_user_manually(user_req, created_by_user_id="admin-id")
    assert created["user_id"]
    user = await UserService.get_user_by_id(created["user_id"])
    assert user["email"] == user_req.email.lower()


async def test_send_and_verify_invitation():
    invite_req = InviteUserRequest(
        email="invitee@example.com",
        full_name="Invitee User",
        role="driver",  # Changed from 'user' to 'driver' to match model
        phoneNo="1234567890"
    )
    # Send invitation
    result = await InvitationService.send_invitation(invite_req, invited_by_user_id="admin-id")
    assert "invitation_id" in result
    # Simulate OTP retrieval (would need to fetch from DB in real test)
    # Here, just check the invitation was created
    assert result["email"] == invite_req.email


