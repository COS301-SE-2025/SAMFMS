import sys
from unittest.mock import AsyncMock, MagicMock, patch

sys.modules.setdefault("jwt", MagicMock())
sys.modules.setdefault("bcrypt", MagicMock())

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from bson import ObjectId

from routes.auth import router as auth_router
from routes.auth import get_current_active_user


pytestmark = pytest.mark.asyncio

@pytest_asyncio.fixture
def app() -> FastAPI:
    """Tiny FastAPI app exposing only the auth endpoints."""
    _app = FastAPI()
    _app.include_router(auth_router)
    return _app


@pytest_asyncio.fixture
async def client(app):
    """Shared HTTPX client."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

async def test_signup_success(client):
    payload = {
        "full_name": "Alice Smith",
        "email": "alice@example.com",
        "password": "secret123",
        "role": "user",
        "phoneNo": "000-111-2222",
        "details": {},
        "preferences": {"theme": "dark"},
    }

    oid = ObjectId()
    created_doc = {**payload, "_id": oid, "password": "hashed!"}

    finder = AsyncMock(side_effect=[None, created_doc])  
    collection = MagicMock(
        find_one=finder,
        insert_one=AsyncMock(return_value=MagicMock(inserted_id=oid)),
    )

    with (
        patch("routes.auth.users_collection", collection),
        patch("routes.auth.get_password_hash", return_value="hashed!"),
        patch("routes.auth.create_access_token", return_value="dummy.token"),
    ):
        r = await client.post("/signup", json=payload)

    assert r.status_code == 200
    body = r.json()
    assert body["access_token"] == "dummy.token"
    assert body["user"]["email"] == "alice@example.com"


async def test_login_success(client):
    user_doc = {
        "_id": ObjectId(),
        "full_name": "Bob Jones",
        "email": "bob@example.com",
        "password": "hashed!",
        "role": "admin",
        "details": {},
        "phoneNo": None,
        "preferences": {},
    }

    with (
        patch("routes.auth.authenticate_user", AsyncMock(return_value=user_doc)),
        patch("routes.auth.create_access_token", return_value="dummy.token"),
    ):
        r = await client.post("/login", json={"email": "bob@example.com", "password": "pass"})

    assert r.status_code == 200
    assert r.json()["user"]["role"] == "admin"


async def test_login_unauthorized(client):
    with patch("routes.auth.authenticate_user", AsyncMock(return_value=False)):
        r = await client.post("/login", json={"email": "ghost@gmail.com", "password": "bad"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Incorrect email or password"


async def test_get_current_user(app, client):     
    user_doc = {
        "_id": ObjectId(),
        "full_name": "Charlie",
        "email": "charlie@example.com",
        "role": "user",
        "details": {},
        "phoneNo": None,
        "preferences": {},
    }

  
    app.dependency_overrides[get_current_active_user] = lambda: user_doc

    resp = await client.get("/me")               
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Charlie"

    app.dependency_overrides.clear()

