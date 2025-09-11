import asyncio
import json
import sys
import types
from typing import Any, Dict
import pytest

if "aio_pika" not in sys.modules:
    aio_pika_stub = types.ModuleType("aio_pika")
    class _ExchangeType:
        DIRECT = "direct"
    aio_pika_stub.ExchangeType = _ExchangeType
    sys.modules["aio_pika"] = aio_pika_stub



from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

import routes.service_routing as sr



def _make_app() -> TestClient:
    app = FastAPI()
    app.include_router(sr.service_router)
    return TestClient(app)

def _success_response(data: Dict[str, Any], status: int = 200, headers: Dict[str, str] = None):
    return {"data": data, "status_code": status, "headers": headers or {}}


def test__normalize_path_variants():
    assert sr._normalize_path("/vehicles/") == "vehicles"
    assert sr._normalize_path("//a//b///") == "a/b"
    assert sr._normalize_path("///") == ""
    assert sr._normalize_path("") == ""
    assert sr._normalize_path("/trips/plan/now") == "trips/plan/now"


def test__extract_user_context_headers_and_bearer():
    headers = {
        "authorization": "Bearer abc.def",
        "x-user-id": "u1",
        "x-user-role": "admin",
        "x-user-email": "e@x",
        "x-tenant-id": "t1",
    }
    ctx = sr._extract_user_context(headers)
    assert ctx["authorization"] == "Bearer abc.def"
    assert ctx["user_id"] == "u1"
    assert ctx["role"] == "admin"
    assert ctx["email"] == "e@x"
    assert ctx["tenant_id"] == "t1"
    assert ctx["token"] == "abc.def"


@pytest.mark.parametrize(
    "service,endpoint,expected",
    [
        ("maintenance", "/records/list", 45.0),
        ("maintenance", "/analytics/report", 60.0),
        ("maintenance", "/health", 10.0),
        ("management", "/vehicles", 35.0),
        ("gps", "/tracking", 20.0),
        ("trips", "/optimization", 60.0),
        ("unknown", "/anything", 30.0), 
    ],
)
def test__get_timeout_for_operation_patterns(service, endpoint, expected):
    assert sr._get_timeout_for_operation(service, endpoint) == expected


@pytest.mark.parametrize(
    "etype,emsg,code",
    [
        ("AuthError", "", 403),
        ("", "unauthorized access", 403),
        ("ValidationError", "", 400),
        ("", "missing field foo", 400),
        ("NotFound", "", 404),
        ("", "not found", 404),
        ("DatabaseError", "", 503),
        ("", "service unavailable", 503),
        ("Conflict", "", 409),
        ("OtherThing", "misc", 500),
    ],
)
def test__map_error_to_status_code(etype, emsg, code):
    assert sr._map_error_to_status_code(etype, emsg) == code


@pytest.mark.asyncio
async def test_route_to_service_block_success_merges_query_and_body(monkeypatch):
    captured = {}

    async def fake_publish(exchange_name, exchange_type, message, routing_key):
        captured["message"] = message
        await sr.handle_service_response({
            "correlation_id": message["correlation_id"],
            "status": "ok",
            "data": {"echo": message["data"]},
            "status_code": 201,
            "headers": {"X-Test": "1"},
        })

    monkeypatch.setattr(sr, "publish_message", fake_publish)

    headers = {"authorization": "Bearer token123", "x-user-id": "u-1"}
    body = b'{"a": 1}'
    query = {"b": 2}

    resp = await sr.route_to_service_block(
        service_name="gps",
        method="POST",
        path="/tracking/locations",
        headers=headers,
        body=body,
        query_params=query,
    )

    assert resp["status_code"] == 201
    assert resp["headers"]["X-Test"] == "1"
    assert resp["data"]["echo"] == {"a": 1, "b": 2} 


    sent = captured["message"]
    assert sent["endpoint"] == "tracking/locations"   
    assert sent["body"] == body.decode()
    assert sent["user_context"]["token"] == "token123"


@pytest.mark.asyncio
async def test_route_to_service_block_invalid_json_body_graceful(monkeypatch):
    captured = {}

    async def fake_publish(exchange_name, exchange_type, message, routing_key):
        captured["message"] = message
        await sr.handle_service_response({
            "correlation_id": message["correlation_id"],
            "status": "ok",
            "data": {"echo": message["data"]},
        })

    monkeypatch.setattr(sr, "publish_message", fake_publish)

    body = b'{"a": 1' 
    query = {"q": "x"}
    resp = await sr.route_to_service_block(
        "management", "POST", "/vehicles", {}, body, query
    )

    assert resp["data"]["echo"] == {"q": "x"}
    sent = captured["message"]
    assert sent["body"] == body.decode() 


@pytest.mark.asyncio
async def test_route_to_service_block_invalid_inputs():
    with pytest.raises(HTTPException) as e1:
        await sr.route_to_service_block("", "GET", "/x", {}, None, None)
    assert e1.value.status_code == 400

    with pytest.raises(HTTPException) as e2:
        await sr.route_to_service_block("gps", None, "/x", {}, None, None)
    assert e2.value.status_code == 400

    with pytest.raises(HTTPException) as e3:
        await sr.route_to_service_block("nope", "GET", "/x", {}, None, None)
    assert e3.value.status_code == 404


@pytest.mark.asyncio
async def test_route_to_service_block_timeout(monkeypatch):
    monkeypatch.setattr(sr, "_get_timeout_for_operation", lambda *_: 0.01)

    async def fake_publish(exchange_name, exchange_type, message, routing_key):
        return

    before_len = len(sr.pending_responses)
    monkeypatch.setattr(sr, "publish_message", fake_publish)

    with pytest.raises(HTTPException) as exc:
        await sr.route_to_service_block("gps", "GET", "/health", {}, None, None)
    assert exc.value.status_code == 502

    assert len(sr.pending_responses) == before_len




@pytest.mark.asyncio
async def test_route_to_service_block_publish_crash_wrapped(monkeypatch):
    class _ErrBuilder:
        @staticmethod
        def service_unavailable_error(**kwargs):
            return {"built": "svc_unavailable", **kwargs}

    monkeypatch.setattr(sr, "ErrorResponseBuilder", _ErrBuilder)

    async def fake_publish(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(sr, "publish_message", fake_publish)

    with pytest.raises(HTTPException) as exc:
        await sr.route_to_service_block("gps", "GET", "/health", {}, None, None)
    assert exc.value.status_code == 502
    assert exc.value.detail.get("built") == "svc_unavailable"


@pytest.mark.asyncio
async def test_handle_service_response_sets_future_result():
    loop = asyncio.get_event_loop()
    fut = loop.create_future()
    cid = "cid-123"
    sr.pending_responses[cid] = fut

    await sr.handle_service_response({"correlation_id": cid, "data": {"ok": True}})
    assert fut.done() and fut.result()["data"]["ok"] is True


@pytest.mark.asyncio
async def test_handle_service_response_unknown_id_no_crash():
    await sr.handle_service_response({"correlation_id": "unknown", "data": {}})


def test_list_services_endpoint_simple():
    client = _make_app()
    r = client.get("/services")
    assert r.status_code == 200
    body = r.json()
    assert "gps" in body["services"]
    assert "routing_info" in body


def test_management_route_get_uses_response_fields(monkeypatch):
    client = _make_app()
    called = {}

    async def fake_route_to_block(service_name, method, path, headers, body, query_params):
        called["args"] = (service_name, method, path, headers, body, query_params)
        return _success_response({"ok": 1}, status=201, headers={"X-Managed": "yes"})

    monkeypatch.setattr(sr, "route_to_service_block", fake_route_to_block)

    r = client.get("/management/vehicles?limit=5")
    assert r.status_code == 201
    assert r.headers["X-Managed"] == "yes"
    assert r.json() == {"ok": 1}

    svc, meth, path, *_ = called["args"]
    assert svc == "management"
    assert meth == "GET"
    assert path == "/vehicles"  


def test_gps_route_post_passes_body(monkeypatch):
    client = _make_app()
    called = {}

    async def fake_route_to_block(service_name, method, path, headers, body, query_params):
        called["body"] = body
        return _success_response({"ack": True})

    monkeypatch.setattr(sr, "route_to_service_block", fake_route_to_block)

    r = client.post("/gps/tracking", json={"a": 1})
    assert r.status_code == 200
    assert r.json() == {"ack": True}

    assert isinstance(called["body"], (bytes, bytearray))
    assert json.loads(called["body"].decode()) == {"a": 1}


def test_trips_route_http_exception_bubbles(monkeypatch):
    client = _make_app()

    async def fake_route_to_block(*_args, **_kwargs):
        raise HTTPException(status_code=418, detail="teapot")

    monkeypatch.setattr(sr, "route_to_service_block", fake_route_to_block)

    r = client.get("/trips/plan")
    assert r.status_code == 418
    assert r.json()["detail"] == "teapot"
