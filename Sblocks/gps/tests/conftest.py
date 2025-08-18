import sys
from pathlib import Path

CANDIDATE_ROOTS = [
    Path("/app"),             # preferred path in the container
    Path("/app/gps"),         # legacy path if code is still under gps/
    Path(__file__).resolve().parents[1],  # repo root fallback (e.g., /app/tests -> /app)
]
for root in CANDIDATE_ROOTS:
    if root.exists():
        p = str(root)
        if p not in sys.path:
            sys.path.insert(0, p)

# Optional: if code still imports `from api...` but only gps.api exists, alias it.
try:
    import api  # noqa: F401
except ModuleNotFoundError:
    try:
        import gps.api as _api
        import gps.api.routes as _routes  # ensure subpackage loads
        sys.modules["api"] = _api
        sys.modules["api.routes"] = _routes
    except ModuleNotFoundError:
        # Neither `api` nor `gps.api` exists yet; tests importing routes will fail normally.
        pass


import pytest_asyncio
import asyncio
import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from api.routes import geofences, locations, places, tracking
from api.exception_handlers import EXCEPTION_HANDLERS
import api.exception_handlers as eh
from api.dependencies import get_current_user

class JSONResponseSafe(JSONResponse):
    def render(self, content) -> bytes:

        return super().render(jsonable_encoder(content))


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

@pytest.fixture(autouse=True)
def _patch_exception_handlers_jsonresponse(monkeypatch):
    # Ensure handler functions return a JSONResponse that can serialize datetimes
    monkeypatch.setattr(eh, "JSONResponse", JSONResponseSafe)
    yield

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


@pytest_asyncio.fixture
async def async_client(app):
    """Async HTTP client bound to the app."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


# Handy alias many tests expect
@pytest_asyncio.fixture
async def client(async_client):
    return async_client


@pytest.fixture
def test_headers():
    """Default headers you can reuse in requests."""
    return {"X-Request-ID": "test-request-id"}
