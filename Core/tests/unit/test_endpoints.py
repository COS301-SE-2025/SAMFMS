import pytest


pytest.importorskip("pytest_asyncio")
import pytest_asyncio 

from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from bson import ObjectId


from Core.routes.user import router



pytest_plugins = ("pytest_asyncio",)
pytestmark = pytest.mark.asyncio



class _FakeInsertResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class _MockCollection:
    """Very small AsyncIOMotorCollection replacement for tests."""

    def __init__(self, predefined=None):
        self._docs = {str(doc["_id"]): doc for doc in (predefined or [])}

    async def insert_one(self, doc):
        _id = ObjectId()
        self._docs[str(_id)] = {**doc, "_id": _id}
        return _FakeInsertResult(_id)

    async def find_one(self, query):
        _id = query.get("_id")
        return self._docs.get(str(_id))



@pytest_asyncio.fixture
def app():
    """Spin up a minimal FastAPI instance that mounts the router."""
    _app = FastAPI()
    _app.include_router(router)
    return _app


async def test_test_db_connection_success(app, monkeypatch):
    class _MockDB:
        async def list_collection_names(self):
            return ["users", "posts"]

        users = None

    monkeypatch.setattr("Core.routes.user.db", _MockDB())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/test-db")

    assert resp.status_code == 200
    assert resp.json() == {"status": "success", "collections": ["users", "posts"]}


async def test_test_db_connection_error(app, monkeypatch):
    class _MockDB:
        async def list_collection_names(self):
            raise Exception("boom")

        users = None

    monkeypatch.setattr("Core.routes.user.db", _MockDB())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/test-db")

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "error"
    assert "boom" in body["detail"]


async def test_create_user_persists_and_echoes_payload(app, monkeypatch):
    collection = _MockCollection()
    monkeypatch.setattr("Core.routes.user.users_collection", collection)

    payload = {
        "details": {"ID": "12345678"},
        "full_name": "Ada Lovelace",
        "email": "ada@example.com",
        "password": "securepassword",
        "role": "admin",
        "phoneNo": "123-456-7890",
        "preferences": ["dark_mode", "email_notifications"]
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/users/", json=payload)

    assert resp.status_code == 200
    body = resp.json()


    for key in payload:
        assert body[key] == payload[key]
    assert len(body["_id"]) == 24
    assert body["_id"] in collection._docs



async def test_get_user_found(app, monkeypatch):
    existing_id = ObjectId()
    collection = _MockCollection(
        predefined=[{
            "_id": existing_id,
            "details": {"ID": "87654321"},
            "full_name": "Grace Hopper",
            "email": "grace@example.com",
            "password": "supersecret",
            "role": "user",
            "phoneNo": "321-654-0987",
            "preferences": ["light_mode"]
        }]
    )
    monkeypatch.setattr("Core.routes.user.users_collection", collection)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/users/{existing_id}")

    assert resp.status_code == 200
    assert resp.json()["email"] == "grace@example.com"


async def test_get_user_not_found(app, monkeypatch):
    collection = _MockCollection()
    monkeypatch.setattr("Core.routes.user.users_collection", collection)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/users/{ObjectId()}")

    assert resp.status_code == 404
    assert resp.json()["detail"] == "User not found"
