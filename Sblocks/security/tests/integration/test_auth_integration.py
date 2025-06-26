import pytest
import uuid
from services.auth_service import AuthService
from database import blacklist_token, is_token_blacklisted
from datetime import datetime, timedelta

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

async def test_login_with_wrong_password_fails():
    unique_email = _random_email("failuser")
    user_data = {
        "full_name": "Fail User",
        "email": unique_email,
        "password": "RightPass123!",
        "role": "driver"
    }
    await AuthService.signup_user(user_data)
    with pytest.raises(ValueError):
        await AuthService.login_user(user_data["email"], "WrongPass!", client_ip="127.0.0.1")

async def test_token_blacklisting():
    unique_email = _random_email("blacklistuser")
    user_data = {
        "full_name": "Blacklist User",
        "email": unique_email,
        "password": "BlacklistPass123!",
        "role": "driver"
    }
    token_response = await AuthService.signup_user(user_data)
    token = token_response.access_token
    # Blacklist the token
    expires = datetime.utcnow() + timedelta(minutes=5)
    await blacklist_token(token, expires)
    is_blacklisted = await is_token_blacklisted(token)
    assert is_blacklisted is True
