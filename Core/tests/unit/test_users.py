import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from bson import ObjectId

from routes.user import router

pytest_plugins = ("pytest_asyncio",)
pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
def app() -> FastAPI:
    """Minimal FastAPI app mounting the users router."""
    _app = FastAPI()
    _app.include_router(router)
    return _app


@pytest_asyncio.fixture
async def client(app):
    """Shared HTTPX test client (one per test)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def test_test_db_connection_success(client):
    mock_db = MagicMock(
        list_collection_names=AsyncMock(return_value=["users", "posts"]),
        users=None,
    )

    with patch("routes.user.db", mock_db):
        resp = await client.get("/test-db")

    assert resp.status_code == 200
    assert resp.json() == {"status": "success", "collections": ["users", "posts"]}


async def test_test_db_connection_error(client):
    mock_db = MagicMock(
        list_collection_names=AsyncMock(side_effect=Exception("boom")),
        users=None,
    )

    with patch("routes.user.db", mock_db):
        resp = await client.get("/test-db")

    body = resp.json()
    assert resp.status_code == 200
    assert body["status"] == "error" and "boom" in body["detail"]


async def test_create_user_persists_and_echoes_payload(client):
    payload = {
        "details": {"ID": "12345678"},
        "full_name": "John Smith",
        "email": "John@example.com",
        "password": "securepassword",
        "role": "admin",
        "phoneNo": "123-456-7890",
        "preferences": {"theme": "light_mode"},
    }

    inserted_id = ObjectId()
    collection = MagicMock(
        insert_one=AsyncMock(return_value=MagicMock(inserted_id=inserted_id)),
        find_one=AsyncMock(return_value={**payload, "_id": inserted_id}),
    )

    with patch("routes.user.users_collection", collection):
        resp = await client.post("/users/", json=payload)

    body = resp.json()
    assert resp.status_code == 200
    assert all(body[k] == v for k, v in payload.items())
    assert body["_id"] == str(inserted_id)


async def test_get_user_found(client):
    existing_id = ObjectId()
    doc = {
        "_id": existing_id,
        "details": {"ID": "87654321"},
        "full_name": "Jane Doe",
        "email": "Jane@gmail.com",
        "password": "supersecret",
        "role": "user",
        "phoneNo": "321-654-0987",
        "preferences": {"theme": "light_mode"},
    }

    collection = MagicMock(find_one=AsyncMock(return_value=doc))

    with patch("routes.user.users_collection", collection):
        resp = await client.get(f"/users/{existing_id}")

    assert resp.status_code == 200
    assert resp.json()["email"] == "Jane@gmail.com"


async def test_get_user_not_found(client):
    collection = MagicMock(find_one=AsyncMock(return_value=None))

    with patch("routes.user.users_collection", collection):
        resp = await client.get(f"/users/{ObjectId()}")

    assert resp.status_code == 404
    assert resp.json()["detail"] == "User not found"