import sys
import asyncio

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import pytest
import uuid
from services.auth_service import AuthService
from services.user_service import UserService
from services.invitation_service import InvitationService
from models.api_models import InviteUserRequest, VerifyOTPRequest, CompleteRegistrationRequest, CreateUserRequest

pytestmark = pytest.mark.asyncio


def _random_email(prefix="testuser"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"

async def test_create_and_get_user():
    user_req = CreateUserRequest(
        full_name="Integration User",
        email=_random_email("integrationuser"),
        password="IntegrationPass123!",
        role="driver"
    )
    created = await UserService.create_user_manually(user_req, created_by_user_id="admin-id")
    assert created["user_id"]
    user = await UserService.get_user_by_id(created["user_id"])
    assert user["email"] == user_req.email.lower()


async def test_signup_and_login_user_integration():
    """
    True integration test: requires Docker Compose test stack running (MongoDB, etc).
    Uses a unique email per run to avoid conflicts.
    """
    unique_email = _random_email()
    user_data = {
        "full_name": "Integration Test User",
        "email": unique_email,
        "password": "TestPass123!",
        "role": "driver"
    }

    token_response = await AuthService.signup_user(user_data)
    assert token_response.access_token
    assert token_response.user_id

    login_response = await AuthService.login_user(user_data["email"], user_data["password"], client_ip="127.0.0.1")
    assert login_response.access_token
    assert login_response.user_id == token_response.user_id





async def test_send_and_verify_invitation():
    invite_req = InviteUserRequest(
        email=_random_email("invitee"),
        full_name="Invitee User",
        role="driver",
        phoneNo="1234567890"
    )
    # Send invitation
    result = await InvitationService.send_invitation(invite_req, invited_by_user_id="admin-id")
    assert "invitation_id" in result
    assert result["email"] == invite_req.email
    # Optionally: add more checks for OTP, status, etc.


