# /app/tests/conftest.py
import asyncio
import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from api.routes import geofences, locations, places, tracking
from api.exception_handlers import EXCEPTION_HANDLERS
from api.dependencies import get_current_user


@pytest.fixture(scope="session")
def event_loop():
    """Create a fresh event loop for pytest-asyncio."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def fake_user():
    """User with full GPS permissions for tests."""
    return {
        "user_id": "test-user",
        "username": "pytest",
        "email": "pytest@example.com",
        "permissions": ["gps:read", "gps:write"],
        "is_admin": False,
    }


@pytest.fixture(scope="session")
def app(fake_user):
    """Assemble a FastAPI app with routers + handlers; override auth."""
    app = FastAPI()

    # Routers from /app/api/routes/
    app.include_router(places.router)
    app.include_router(locations.router)
    app.include_router(geofences.router)
    app.include_router(tracking.router)

    # Register central exception handlers
    for exc_cls, handler in EXCEPTION_HANDLERS.items():
        app.add_exception_handler(exc_cls, handler)

    # Make all endpoints think we're authenticated with full permissions
    async def _fake_current_user():
        return fake_user

    app.dependency_overrides[get_current_user] = _fake_current_user

    return app


@pytest.fixture
async def async_client(app):
    """Async HTTP client bound to the app."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


# Handy alias many tests expect
@pytest.fixture
async def client(async_client):
    return async_client


@pytest.fixture
def test_headers():
    """Default headers you can reuse in requests."""
    return {"X-Request-ID": "test-request-id"}
