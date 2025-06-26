import pytest
import uuid
from services.invitation_service import InvitationService, InvitationError
from models.api_models import InviteUserRequest, VerifyOTPRequest

pytestmark = pytest.mark.asyncio

def _random_email(prefix="testuser"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"

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
