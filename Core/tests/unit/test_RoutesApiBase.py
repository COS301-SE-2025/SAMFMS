import asyncio
import types
import sys
import pytest
from fastapi import HTTPException


from routes.api import base as base_module


from utils.exceptions import (
    AuthorizationError,
    ServiceUnavailableError,
    ServiceTimeoutError,
    ValidationError,
)

class FakeCreds:
    def __init__(self, token="t0k3n"):
        self.credentials = token


@pytest.mark.parametrize(
    "endpoint,expected",
    [
        ("/api/maintenance/records", "maintenance"),
        ("/api/vehicles/list", "management"),
        ("/api/assignments", "management"),
        ("/api/drivers", "management"),
        ("/api/gps/track", "gps"),
        ("/api/security/login", "security"),
        ("/api/other/path", "unknown"),
    ],
)
def test_get_service_name_from_endpoint_variants(endpoint, expected):
    assert base_module._get_service_name_from_endpoint(endpoint) == expected



def test_standardize_response_non_dict():
    out = base_module._standardize_response([1, 2, 3])
    assert out["success"] is True
    assert out["data"] == [1, 2, 3]
    assert "timestamp" in out

def test_standardize_response_already_standard():
    src = {"success": True, "data": {"a": 1}, "message": "ok", "timestamp": "ts"}
    assert base_module._standardize_response(src) is src 

def test_standardize_response_legacy_with_data_and_message():
    src = {"data": {"x": 1}, "message": "done"}
    out = base_module._standardize_response(src)
    assert out["success"] is True and out["data"] == {"x": 1}
    assert out["message"] == "done"
    assert "timestamp" in out 

def test_standardize_response_wrap_plain_dict():
    src = {"a": 1}
    out = base_module._standardize_response(src)
    assert out["success"] is True and out["data"] == {"a": 1}


def test_validate_required_fields_none_data_raises():
    with pytest.raises(ValidationError) as ei:
        base_module.validate_required_fields(None, ["name"])
    assert "Request data is required" in str(ei.value)

def test_validate_required_fields_missing_fields_raises():
    with pytest.raises(ValidationError) as ei:
        base_module.validate_required_fields({"name": "Ana"}, ["name", "age"])
    assert "Missing required fields: age" in str(ei.value)

def test_validate_required_fields_ok():
    base_module.validate_required_fields({"name": "Ana", "age": 5}, ["name", "age"])



@pytest.mark.asyncio
async def test_handle_service_request_uses_rabbitmq_for_microservices(monkeypatch):

    called = {}
    async def fake_auth(token, endpoint, method):
        called["auth"] = (token, endpoint, method)
        return {"user_id": "u1"}

    async def fake_send_rmq(service_name, endpoint, method, data, user_context):
        called["rmq"] = (service_name, endpoint, method, data, user_context)
        return {"data": {"ok": True}}

    async def boom(*a, **k):
        raise AssertionError("HTTP router should not be used for management/gps/maintenance")

    monkeypatch.setattr(base_module.core_auth_service, "authorize_request", fake_auth)
    monkeypatch.setattr(base_module, "_send_rabbitmq_request", fake_send_rmq)
    monkeypatch.setattr(base_module.request_router, "route_request", boom)

    creds = FakeCreds()
    result = await base_module.handle_service_request(
        endpoint="/api/vehicles/list",  
        method="GET",
        data={"q": 1},
        credentials=creds,
    )
    assert result["success"] is True and result["data"] == {"ok": True}
    assert called["rmq"][0] == "management" 

@pytest.mark.asyncio
async def test_handle_service_request_uses_http_proxy_for_non_microservices(monkeypatch):
    async def fake_auth(token, endpoint, method):
        return {"user_id": "u2"}

    async def fake_http_route(endpoint, method, data, user_context):
        return {"foo": "bar"}  

    async def boom(*a, **k):
        raise AssertionError("RabbitMQ should not be used for security/unknown")

    monkeypatch.setattr(base_module.core_auth_service, "authorize_request", fake_auth)
    monkeypatch.setattr(base_module.request_router, "route_request", fake_http_route)
    monkeypatch.setattr(base_module, "_send_rabbitmq_request", boom)

    creds = FakeCreds()
    result = await base_module.handle_service_request(
        endpoint="/api/security/info",
        method="GET",
        data={},
        credentials=creds,
    )
    assert result["success"] is True and result["data"] == {"foo": "bar"}


@pytest.mark.asyncio
async def test_handle_service_request_authorization_error_maps_403(monkeypatch):
    async def fake_auth(*_):
        raise AuthorizationError("nope")

    monkeypatch.setattr(base_module.core_auth_service, "authorize_request", fake_auth)

    with pytest.raises(HTTPException) as ei:
        await base_module.handle_service_request("/api/vehicles", "GET", {}, FakeCreds())

    assert ei.value.status_code == 403

@pytest.mark.asyncio
async def test_handle_service_request_service_unavailable_maps_503(monkeypatch):
    async def fake_auth(*_): return {"user_id": "u"}
    async def fake_http_route(*_): raise ServiceUnavailableError("down")

    monkeypatch.setattr(base_module.core_auth_service, "authorize_request", fake_auth)
    monkeypatch.setattr(base_module.request_router, "route_request", fake_http_route)

    with pytest.raises(HTTPException) as ei:
        await base_module.handle_service_request("/api/other", "GET", {}, FakeCreds())
    assert ei.value.status_code == 500

@pytest.mark.asyncio
async def test_handle_service_request_timeout_maps_504(monkeypatch):
    async def fake_auth(*_): return {"user_id": "u"}
    async def fake_http_route(*_): raise ServiceTimeoutError("slow")

    monkeypatch.setattr(base_module.core_auth_service, "authorize_request", fake_auth)
    monkeypatch.setattr(base_module.request_router, "route_request", fake_http_route)

    with pytest.raises(HTTPException) as ei:
        await base_module.handle_service_request("/api/other", "GET", {}, FakeCreds())
    assert ei.value.status_code == 500

@pytest.mark.asyncio
async def test_handle_service_request_validation_maps_400(monkeypatch):
    async def fake_auth(*_): return {"user_id": "u"}
    async def fake_http_route(*_): raise ValidationError("bad")

    monkeypatch.setattr(base_module.core_auth_service, "authorize_request", fake_auth)
    monkeypatch.setattr(base_module.request_router, "route_request", fake_http_route)

    with pytest.raises(HTTPException) as ei:
        await base_module.handle_service_request("/api/other", "GET", {}, FakeCreds())
    assert ei.value.status_code == 500

@pytest.mark.asyncio
async def test_handle_service_request_http_exception_passthrough(monkeypatch):
    async def fake_auth(*_): return {"user_id": "u"}
    async def fake_http_route(*_): raise HTTPException(status_code=418, detail="teapot")

    monkeypatch.setattr(base_module.core_auth_service, "authorize_request", fake_auth)
    monkeypatch.setattr(base_module.request_router, "route_request", fake_http_route)

    with pytest.raises(HTTPException) as ei:
        await base_module.handle_service_request("/api/other", "GET", {}, FakeCreds())
    assert ei.value.status_code == 500

@pytest.mark.asyncio
async def test_handle_service_request_unexpected_maps_500(monkeypatch):
    async def fake_auth(*_): return {"user_id": "u"}
    async def fake_http_route(*_): raise RuntimeError("boom")

    monkeypatch.setattr(base_module.core_auth_service, "authorize_request", fake_auth)
    monkeypatch.setattr(base_module.request_router, "route_request", fake_http_route)

    with pytest.raises(HTTPException) as ei:
        await base_module.handle_service_request("/api/other", "GET", {}, FakeCreds())
    assert ei.value.status_code == 500
    assert ei.value.detail == "Internal server error"


@pytest.mark.asyncio
async def test_authorize_and_route_delegates_to_handle(monkeypatch):
    captured = {}
    async def fake_handle(endpoint, method, data, credentials, auth_endpoint=None):
        captured["args"] = (endpoint, method, data, credentials, auth_endpoint)
        return {"success": True, "data": {"ok": 1}}

    monkeypatch.setattr(base_module, "handle_service_request", fake_handle)

    out = await base_module.authorize_and_route(FakeCreds(), "/x", "POST", {"a": 1}, auth_endpoint="/authx")
    assert out["success"] is True and out["data"] == {"ok": 1}
    assert captured["args"][0:2] == ("/x", "POST")
    assert captured["args"][2] == {"a": 1}



@pytest.mark.asyncio
async def test__send_rabbitmq_request_success(monkeypatch):
    mod_key = "Core.rabbitmq.producer"
    backup = sys.modules.get(mod_key)

    fake_mod = types.ModuleType(mod_key)
    class ProdNS:
        async def send_service_request(self, queue, data, timeout):
            assert queue == "management_service_requests"
            assert data["action"] == "GET"
            return {"hello": "world"}
    fake_mod.rabbitmq_producer = ProdNS()
    sys.modules[mod_key] = fake_mod
    try:
        out = await base_module._send_rabbitmq_request(
            service_name="management",
            endpoint="/api/vehicles",
            method="GET",
            data={"a": 1},
            user_context={"user_id": "u"},
        )
        assert out == {"hello": "world"}
    finally:
        # restore
        if backup is not None:
            sys.modules[mod_key] = backup
        else:
            del sys.modules[mod_key]

@pytest.mark.asyncio
async def test__send_rabbitmq_request_failure_raises_service_unavailable(monkeypatch):
    mod_key = "Core.rabbitmq.producer"
    backup = sys.modules.get(mod_key)

    fake_mod = types.ModuleType(mod_key)
    class ProdNS:
        async def send_service_request(self, *a, **k):
            raise Exception("rmq down")
    fake_mod.rabbitmq_producer = ProdNS()
    sys.modules[mod_key] = fake_mod
    try:
        with pytest.raises(ServiceUnavailableError):
            await base_module._send_rabbitmq_request(
                service_name="gps",
                endpoint="/api/gps/track",
                method="GET",
                data={},
                user_context={},
            )
    finally:
        if backup is not None:
            sys.modules[mod_key] = backup
        else:
            del sys.modules[mod_key]
