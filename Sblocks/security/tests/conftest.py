import sys
import types

# ──────────────────────────────────────────────────────────────────────────────
# Stub out repository modules so tests won't skip when they import them
# Module-level imports in test files will now find these dummies in sys.modules
for repo_name, coll_attr in [
    ("repositories.session_repository", "sessions_collection"),
    ("repositories.token_repository", "blacklisted_tokens_collection"),
]:
    if repo_name not in sys.modules:
        dummy = types.ModuleType(repo_name)
        setattr(dummy, coll_attr, None)
        sys.modules[repo_name] = dummy

import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock

import mongomock
import fakeredis
import motor.motor_asyncio
import pytest
import importlib

# Create dummy repository modules if they don't exist so tests won't be skipped.
import sys, types
if 'repositories.session_repository' not in sys.modules:
    mod = types.ModuleType('repositories.session_repository')
    # placeholder attribute to satisfy tests
    mod.sessions_collection = None
    sys.modules['repositories.session_repository'] = mod
if 'repositories.token_repository' not in sys.modules:
    mod2 = types.ModuleType('repositories.token_repository')
    mod2.blacklisted_tokens_collection = None
    sys.modules['repositories.token_repository'] = mod2

# Ensure the project root is on the import path so that "config" and other
# first‑party packages resolve regardless of where pytest is invoked from.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ──────────────────────────────────────────────────────────────────────────────
# Core asyncio/pytest configuration
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def event_loop():
    """Provide a *single* asyncio event‑loop for the entire test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ──────────────────────────────────────────────────────────────────────────────
# Fake external services (MongoDB, Redis, etc.)
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_database():
    """In‑memory MongoDB provided by *mongomock*."""
    client = mongomock.MongoClient()
    return client.test_security_db


@pytest.fixture
def mock_redis():
    """In‑memory Redis stub using *fakeredis*."""
    return fakeredis.FakeRedis()


# ──────────────────────────────────────────────────────────────────────────────
# Application settings & sample objects
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_settings():
    """Minimal settings dict used by code that expects env config."""
    return {
        "JWT_SECRET_KEY": "test-secret-key-for-testing-only",
        "ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": 30,
        "REFRESH_TOKEN_EXPIRE_DAYS": 7,
        "DATABASE_URL": "mongodb://localhost:27017/test_security_db",
        "REDIS_URL": "redis://localhost:6379/0",
        "RABBITMQ_URL": "amqp://localhost:5672/",
        "ENVIRONMENT": "test",
    }


# Sample domain objects used by multiple tests
# ──────────────────────────────────────────────────────────────────────────────

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


# ──────────────────────────────────────────────────────────────────────────────
# Repository / service mocks
# ──────────────────────────────────────────────────────────────────────────────

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


# ──────────────────────────────────────────────────────────────────────────────
# FastAPI / HTTP client helpers
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
async def test_client():
    """Placeholder until the FastAPI app object exists."""
    return MagicMock()


@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test-jwt-token"}


@pytest.fixture
def invalid_auth_headers():
    return {"Authorization": "Bearer invalid-token"}


# ──────────────────────────────────────────────────────────────────────────────
# Fresh Motor client per test to avoid closed event-loop
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _fresh_motor_per_test(monkeypatch, event_loop):
    """
    For every test, build a new AsyncIOMotorClient bound to the current loop
    and patch all cached collections in config.database and repositories.
    """
    from config import database as _db

    # 1) fresh client + db tied to this test’s loop
    new_client = motor.motor_asyncio.AsyncIOMotorClient(_db.settings.MONGODB_URL)
    new_db = new_client[_db.settings.DATABASE_NAME]

    # 2) patch the globals in config.database
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

    # 3) patch every repo that cached a collection at import
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

    # 4) close sockets (while loop still alive)
    new_client.close()
