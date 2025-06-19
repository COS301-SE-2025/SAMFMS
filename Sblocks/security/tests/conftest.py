import pytest
import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient
from fastapi.testclient import TestClient
import mongomock
import fakeredis

# Add the security module to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_database():
    """Mock MongoDB database for testing."""
    client = mongomock.MongoClient()
    database = client.test_security_db
    return database


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    return fakeredis.FakeRedis()


@pytest.fixture
def mock_settings():
    """Mock application settings."""
    return {
        "JWT_SECRET_KEY": "test-secret-key-for-testing-only",
        "ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": 30,
        "REFRESH_TOKEN_EXPIRE_DAYS": 7,
        "DATABASE_URL": "mongodb://localhost:27017/test_security_db",
        "REDIS_URL": "redis://localhost:6379/0",
        "RABBITMQ_URL": "amqp://localhost:5672/",
        "ENVIRONMENT": "test"
    }


@pytest.fixture
def test_user_data():
    """Sample user data for testing."""
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
            "session_timeout": "30 minutes"
        }
    }


@pytest.fixture
def test_admin_user_data():
    """Sample admin user data for testing."""
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
            "session_timeout": "60 minutes"
        }
    }


@pytest.fixture
def test_invitation_data():
    """Sample invitation data for testing."""
    return {
        "email": "invited@example.com",
        "full_name": "Invited User",
        "role": "fleet_manager",
        "phone_number": "+1234567892",
        "invited_by": "admin-user-123",
        "otp": "123456",
        "expires_at": "2025-12-31T23:59:59"
    }


@pytest.fixture
def mock_user_repository():
    """Mock UserRepository for testing."""
    repository = AsyncMock()
    repository.create_user = AsyncMock()
    repository.find_by_email = AsyncMock()
    repository.find_by_id = AsyncMock()
    repository.get_all_users = AsyncMock()
    repository.update_user = AsyncMock()
    repository.delete_user = AsyncMock()
    return repository


@pytest.fixture
def mock_invitation_repository():
    """Mock InvitationRepository for testing."""
    repository = AsyncMock()
    repository.create_invitation = AsyncMock()
    repository.find_by_email = AsyncMock()
    repository.find_by_otp = AsyncMock()
    repository.get_pending_invitations = AsyncMock()
    repository.update_invitation = AsyncMock()
    repository.delete_invitation = AsyncMock()
    return repository


@pytest.fixture
def mock_audit_repository():
    """Mock AuditRepository for testing."""
    repository = AsyncMock()
    repository.log_security_event = AsyncMock()
    repository.get_user_audit_log = AsyncMock()
    repository.get_security_events = AsyncMock()
    return repository


@pytest.fixture
def mock_rabbitmq_producer():
    """Mock RabbitMQ producer for testing."""
    producer = AsyncMock()
    producer.publish_user_created = AsyncMock()
    producer.publish_user_updated = AsyncMock()
    producer.publish_user_deleted = AsyncMock()
    return producer


@pytest.fixture
async def test_client():
    """Test client for FastAPI application."""
    # This will be implemented once we have the main app setup
    # For now, return a mock
    return MagicMock()


@pytest.fixture
def auth_headers():
    """Sample authorization headers for testing."""
    return {
        "Authorization": "Bearer test-jwt-token"
    }


@pytest.fixture
def invalid_auth_headers():
    """Invalid authorization headers for testing."""
    return {
        "Authorization": "Bearer invalid-token"
    }
