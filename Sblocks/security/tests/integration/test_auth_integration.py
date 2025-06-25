import pytest
import uuid
from services.auth_service import AuthService

pytestmark = pytest.mark.asyncio

def _random_email(prefix="testuser"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"

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
