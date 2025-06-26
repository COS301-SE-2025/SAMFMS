import pytest
import uuid
from services.user_service import UserService
from models.api_models import CreateUserRequest
from database import get_security_metrics
from health_metrics import health_check

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

async def test_update_user_profile():
    user_req = CreateUserRequest(
        full_name="Profile Test User",
        email=_random_email("profileuser"),
        password="ProfilePass123!",
        role="driver"
    )
    created = await UserService.create_user_manually(user_req, created_by_user_id="admin-id")
    user_id = created["user_id"]
    # Update full name
    updated = await UserService.update_user_profile(user_id, {"full_name": "Updated Name"})
    assert updated
    user = await UserService.get_user_by_id(user_id)
    assert user["full_name"] == "Updated Name"

async def test_delete_user():
    user_req = CreateUserRequest(
        full_name="Delete Test User",
        email=_random_email("deleteuser"),
        password="DeletePass123!",
        role="driver"
    )
    created = await UserService.create_user_manually(user_req, created_by_user_id="admin-id")
    user_id = created["user_id"]
    deleted = await UserService.delete_user(user_id, deleted_by="admin-id")
    assert deleted
    user = await UserService.get_user_by_id(user_id)
    assert user is None

async def test_toggle_user_status():
    user_req = CreateUserRequest(
        full_name="Status Test User",
        email=_random_email("statususer"),
        password="StatusPass123!",
        role="driver"
    )
    created = await UserService.create_user_manually(user_req, created_by_user_id="admin-id")
    user_id = created["user_id"]
    # Deactivate
    deactivated = await UserService.toggle_user_status(user_id, is_active=False, modified_by="admin-id")
    assert deactivated
    user = await UserService.get_user_by_id(user_id)
    assert user["is_active"] is False
    # Reactivate
    reactivated = await UserService.toggle_user_status(user_id, is_active=True, modified_by="admin-id")
    assert reactivated
    user = await UserService.get_user_by_id(user_id)
    assert user["is_active"] is True

async def test_health_check():
    response = await health_check()
    assert response.status_code in (200, 503)
    assert "service" in response.body.decode() or "service" in response.body
