# Core/tests/unit/test_routesDebug.py

import asyncio
import pytest
from fastapi import FastAPI, WebSocket
from fastapi.testclient import TestClient

import routes.debug as debug_mod
from routes.debug import router as debug_router


def make_client():
    app = FastAPI()
    app.include_router(debug_router)

    # Add a websocket route so /debug/routes sees a route without "methods"
    @app.websocket("/ws")
    async def ws_endpoint(ws: WebSocket):
        # We don't actually use it in tests; it's only for route listing coverage
        pass

    return TestClient(app)


# ---------- /test/simple ----------

def test_simple_test_ok():
    client = make_client()
    res = client.get("/test/simple")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "timestamp" in data


# ---------- /debug/routes ----------

def test_debug_routes_lists_routes_and_api_routes():
    client = make_client()
    res = client.get("/debug/routes")
    assert res.status_code == 200
    data = res.json()

    # We registered several routes; at least this one should be present
    assert any(r["path"] == "/debug/routes" for r in data["routes"])

    # All api_routes should begin with /api (branch exercised)
    assert all(r["path"].startswith("/api") for r in data["api_routes"])


# ---------- /api/services/register ----------

@pytest.mark.asyncio
async def test_register_service_success(monkeypatch):
    class FakeSD:
        def __init__(self):
            self.called = False

        async def register_service(self, **kwargs):
            self.called = True

    async def fake_get_sd():
        return FakeSD()

    monkeypatch.setattr(debug_mod, "get_service_discovery", fake_get_sd)

    client = make_client()
    payload = {"name": "svc", "host": "h", "port": 1234}
    res = client.post("/api/services/register", json=payload)
    assert res.status_code == 200
    assert res.json()["status"] == "success"


@pytest.mark.asyncio
async def test_register_service_error(monkeypatch):
    async def fake_get_sd_raises():
        raise RuntimeError("boom")

    monkeypatch.setattr(debug_mod, "get_service_discovery", fake_get_sd_raises)

    client = make_client()
    payload = {"name": "svc", "host": "h", "port": 1234}
    res = client.post("/api/services/register", json=payload)
    assert res.status_code == 500
    assert "Service registration failed" in res.json()["detail"]


# ---------- /api/services (GET) ----------

@pytest.mark.asyncio
async def test_get_registered_services_success(monkeypatch):
    class FakeSD:
        async def get_all_services(self):
            return [{"name": "a"}, {"name": "b"}]

    async def fake_get_sd():
        return FakeSD()

    monkeypatch.setattr(debug_mod, "get_service_discovery", fake_get_sd)

    client = make_client()
    res = client.get("/api/services")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["total"] == 2
    assert data["services"] == [{"name": "a"}, {"name": "b"}]


@pytest.mark.asyncio
async def test_get_registered_services_error(monkeypatch):
    async def fake_get_sd_raises():
        raise RuntimeError("fail")

    monkeypatch.setattr(debug_mod, "get_service_discovery", fake_get_sd_raises)

    client = make_client()
    res = client.get("/api/services")
    assert res.status_code == 500
    assert "Failed to get services" in res.json()["detail"]


# ---------- /api/services/{service_name} (DELETE) ----------

@pytest.mark.asyncio
async def test_deregister_service_success(monkeypatch):
    class FakeSD:
        async def deregister_service(self, name: str):
            assert name == "svc"

    async def fake_get_sd():
        return FakeSD()

    monkeypatch.setattr(debug_mod, "get_service_discovery", fake_get_sd)

    client = make_client()
    res = client.delete("/api/services/svc")
    assert res.status_code == 200
    assert res.json()["status"] == "success"


@pytest.mark.asyncio
async def test_deregister_service_error(monkeypatch):
    async def fake_get_sd_raises():
        raise RuntimeError("x")

    monkeypatch.setattr(debug_mod, "get_service_discovery", fake_get_sd_raises)

    client = make_client()
    res = client.delete("/api/services/svc")
    assert res.status_code == 500
    assert "Service deregistration failed" in res.json()["detail"]


# ---------- /test/connection ----------

def test_test_service_connection_success(monkeypatch):
    class FakeRR:
        async def send_request_and_wait(self, *_args, **_kwargs):
            return {"ok": True}

    monkeypatch.setattr(debug_mod, "request_router", FakeRR())

    client = make_client()
    res = client.get("/test/connection")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "success"
    assert body["response_received"] is True
    assert body["data"] == {"ok": True}


def test_test_service_connection_timeout(monkeypatch):
    # Make any asyncio.wait_for call here raise TimeoutError quickly
    def fake_wait_for(awaitable, timeout):
        raise asyncio.TimeoutError

    monkeypatch.setattr(asyncio, "wait_for", fake_wait_for)

    client = make_client()
    res = client.get("/test/connection")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "error"
    assert body["response_received"] is False
    assert "Timeout" in body["message"]


def test_test_service_connection_error(monkeypatch):
    class FakeRR:
        async def send_request_and_wait(self, *_args, **_kwargs):
            raise RuntimeError("bad")

    monkeypatch.setattr(debug_mod, "request_router", FakeRR())

    client = make_client()
    res = client.get("/test/connection")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "error"
    assert body["response_received"] is False
    assert "Communication error" in body["message"]


# ---------- /vehicles/direct ----------

def test_get_vehicles_direct_success(monkeypatch):
    class FakeRR:
        async def send_request_and_wait(self, *_args, **_kwargs):
            return {"vehicles": [1, 2, 3]}

    monkeypatch.setattr(debug_mod, "request_router", FakeRR())

    client = make_client()
    res = client.get("/vehicles/direct")
    assert res.status_code == 200
    assert res.json() == {"vehicles": [1, 2, 3]}


def test_get_vehicles_direct_timeout(monkeypatch):
    def fake_wait_for(awaitable, timeout):
        raise asyncio.TimeoutError

    monkeypatch.setattr(asyncio, "wait_for", fake_wait_for)

    client = make_client()
    res = client.get("/vehicles/direct")
    assert res.status_code == 504
    assert res.json()["detail"] == "Management service timeout"


def test_get_vehicles_direct_error(monkeypatch):
    def fake_wait_for(awaitable, timeout):
        raise RuntimeError("oops")

    monkeypatch.setattr(asyncio, "wait_for", fake_wait_for)

    client = make_client()
    res = client.get("/vehicles/direct")
    assert res.status_code == 500
    assert res.json()["detail"] == "Service error: oops"


# ---------- /service_presence ----------

def test_service_presence_success(monkeypatch):
    class FakeCursor:
        def __init__(self, data):
            self._data = data

        async def to_list(self, length=None):
            return self._data

    class FakeCollection:
        def __init__(self, data):
            self._data = data

        def find(self, *_args, **_kwargs):
            return FakeCursor(self._data)

    class FakeDB:
        def __init__(self, data):
            self._data = data

        def get_collection(self, name):
            assert name == "service_presence"
            return FakeCollection(self._data)

    data = [{"service": "a"}, {"service_name": "b"}, {}]
    monkeypatch.setattr(debug_mod, "db", FakeDB(data))

    client = make_client()
    res = client.get("/service_presence")
    assert res.status_code == 200
    assert res.json() == ["a", "b", "unknown"]


def test_service_presence_error(monkeypatch):
    class BadDB:
        def get_collection(self, name):
            raise RuntimeError("db down")

    monkeypatch.setattr(debug_mod, "db", BadDB())

    client = make_client()
    res = client.get("/service_presence")
    assert res.status_code == 200  # returns an error payload, not HTTPException
    assert "error" in res.json()
