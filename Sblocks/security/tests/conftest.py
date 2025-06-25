import os
import sys
import asyncio
import importlib
from unittest.mock import AsyncMock, MagicMock

import pytest
import motor.motor_asyncio


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))



@pytest.fixture(scope="session")
def event_loop():
    """Provide a *single* asyncio event‑loop for the entire test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()




@pytest.fixture
def test_user_data():
    return {
        "user_id": "test-user-123",
        "email": "test@example.com",
        "full_name": "Test User",
        "role": "driver",
        "password": "TestPassword123!",
        "phoneNo": "+1234567890",
        "is_active": True,
        "approved": True,
        "preferences": {
            "theme": "light",
            "animations": "true",
            "email_alerts": "true",
            "push_notifications": "true",
            "two_factor": "false",
            "activity_log": "true",
            "session_timeout": "30 minutes",
        },
    }


@pytest.fixture
def test_admin_user_data():
    return {
        "user_id": "admin-user-123",
        "email": "admin@example.com",
        "full_name": "Admin User",
        "role": "admin",
        "password": "AdminPassword123!",
        "phoneNo": "+1234567891",
        "is_active": True,
        "approved": True,
        "preferences": {
            "theme": "dark",
            "animations": "true",
            "email_alerts": "true",
            "push_notifications": "true",
            "two_factor": "true",
            "activity_log": "true",
            "session_timeout": "60 minutes",
        },
    }


@pytest.fixture
def test_invitation_data():
    return {
        "email": "invited@example.com",
        "full_name": "Invited User",
        "role": "fleet_manager",
        "phone_number": "+1234567892",
        "invited_by": "admin-user-123",
        "otp": "123456",
        "expires_at": "2025-12-31T23:59:59",
    }




@pytest.fixture
def mock_user_repository():
    repo = AsyncMock()
    repo.create_user = AsyncMock()
    repo.find_by_email = AsyncMock()
    repo.find_by_id = AsyncMock()
    repo.get_all_users = AsyncMock()
    repo.update_user = AsyncMock()
    repo.delete_user = AsyncMock()
    return repo


@pytest.fixture
def mock_invitation_repository():
    repo = AsyncMock()
    repo.create_invitation = AsyncMock()
    repo.find_by_email = AsyncMock()
    repo.find_by_otp = AsyncMock()
    repo.get_pending_invitations = AsyncMock()
    repo.update_invitation = AsyncMock()
    repo.delete_invitation = AsyncMock()
    return repo


@pytest.fixture
def mock_audit_repository():
    repo = AsyncMock()
    repo.log_security_event = AsyncMock()
    repo.get_user_audit_log = AsyncMock()
    repo.get_security_events = AsyncMock()
    return repo


@pytest.fixture
def mock_rabbitmq_producer():
    producer = AsyncMock()
    producer.publish_user_created = AsyncMock()
    producer.publish_user_updated = AsyncMock()
    producer.publish_user_deleted = AsyncMock()
    return producer




@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test-jwt-token"}


@pytest.fixture
def invalid_auth_headers():
    return {"Authorization": "Bearer invalid-token"}




@pytest.fixture(autouse=True)
def _fresh_motor_per_test(monkeypatch, event_loop):
    """
    For every test, build a new AsyncIOMotorClient bound to the current loop
    and patch all cached collections in config.database and repositories.
    """
    from config import database as _db


    new_client = motor.motor_asyncio.AsyncIOMotorClient(_db.settings.MONGODB_URL)
    new_db = new_client[_db.settings.DATABASE_NAME]


    monkeypatch.setattr(_db, "client", new_client, raising=False)
    monkeypatch.setattr(_db, "db", new_db, raising=False)
    monkeypatch.setattr(
        _db, "security_users_collection", new_db.security_users, raising=False
    )
    monkeypatch.setattr(_db, "sessions_collection", new_db.sessions, raising=False)
    monkeypatch.setattr(_db, "audit_logs_collection", new_db.audit_logs, raising=False)
    monkeypatch.setattr(
        _db,
        "blacklisted_tokens_collection",
        new_db.blacklisted_tokens,
        raising=False,
    )


    for mod_name, attr, coll in [
        ("repositories.user_repository", "security_users_collection", "security_users"),
        ("repositories.audit_repository", "audit_logs_collection", "audit_logs"),
        ("repositories.session_repository", "sessions_collection", "sessions"),
        ("repositories.token_repository", "blacklisted_tokens_collection", "blacklisted_tokens"),
    ]:
        try:
            repo_mod = importlib.import_module(mod_name)
        except ImportError:
            continue
        monkeypatch.setattr(repo_mod, attr, getattr(new_db, coll), raising=False)

    yield


    new_client.close()
