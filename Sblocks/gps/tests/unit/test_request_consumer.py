# app/tests/unit/test_request_consumer.py
import sys
import types
import json
import time
import pytest
from unittest.mock import AsyncMock

from services.request_consumer import ServiceRequestConsumer, PRETORIA_COORDINATES


# ----------------------- robust stubs / installers -----------------------

def _ensure_module(name: str) -> types.ModuleType:
    """Create (or fetch) a real ModuleType and register it in sys.modules."""
    mod = sys.modules.get(name)
    if isinstance(mod, types.ModuleType):
        return mod
    mod = types.ModuleType(name)
    sys.modules[name] = mod
    return mod


def _install_fake_db_module(connected: bool = True):
    """
    Handlers do: `from repositories.database import db_manager`
    Provide a module 'repositories.database' with an attribute 'db_manager'
    exposing `.is_connected()`.
    """
    _ensure_module("repositories")
    db_mod = _ensure_module("repositories.database")

    class _DBMgr:
        @staticmethod
        def is_connected():
            return connected

    # export name `db_manager` exactly (imported name)
    db_mod.db_manager = _DBMgr()


def _install_response_builder_stub():
    """
    Handlers import: `from schemas.responses import ResponseBuilder`
    Build a minimal compatible stub with `.success(...).model_dump()` and
    `.error(...).model_dump()`. Also ensure parent `schemas` exists.
    """
    _ensure_module("schemas")
    resp_mod = _ensure_module("schemas.responses")

    class _RB:
        @staticmethod
        def success(data=None, message=""):
            return types.SimpleNamespace(
                model_dump=lambda: {"status": "success", "data": data, "message": message}
            )

        @staticmethod
        def error(error="", message=""):
            # The code inspects keys: "status", "error", "message"
            err_val = error if isinstance(error, str) else "Error"
            return types.SimpleNamespace(
                model_dump=lambda: {"status": "error", "error": err_val, "message": message}
            )

    resp_mod.ResponseBuilder = _RB


def _install_service_module(mod_name: str, **attrs):
    """
    Ensure `services` parent exists and install `services.<mod_name>` as a module
    exposing the given attributes (e.g., `location_service=...`).
    This makes `from services.<mod_name> import ...` work reliably.
    """
    _ensure_module("services")
    mod = types.ModuleType(f"services.{mod_name}")
    for k, v in attrs.items():
        setattr(mod, k, v)
    sys.modules[f"services.{mod_name}"] = mod


class _FakeMessage:
    """
    Minimal aio-pika-like message for handle_request().
    """
    def __init__(self, body_dict):
        self.body = json.dumps(body_dict).encode()

    class _Ctx:
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc, tb): return False

    def process(self, requeue=False):  # matches aio_pika AbstractIncomingMessage
        return self._Ctx()


# ------------------------------ tests ------------------------------

@pytest.mark.asyncio
async def test_route_request_validations_raise_value_error():
    c = ServiceRequestConsumer()
    with pytest.raises(ValueError):
        await c._route_request(method=None, user_context={}, endpoint="x")
    with pytest.raises(ValueError):
        await c._route_request(method="GET", user_context="not-a-dict", endpoint="x")
    with pytest.raises(ValueError):
        await c._route_request(method="GET", user_context={}, endpoint=123)


@pytest.mark.asyncio
async def test_health_handler_success():
    _install_response_builder_stub()
    c = ServiceRequestConsumer()
    out = await c._handle_health_request("GET", {})
    assert out["status"] == "success"
    assert out["data"]["service"] == "gps"


@pytest.mark.asyncio
async def test_locations_handler_get_vehicle_default_when_none():
    _install_fake_db_module(connected=True)
    _install_response_builder_stub()

    # Install a proper services.location_service module with a 'location_service' attr
    fake_loc = types.SimpleNamespace(get_vehicle_location=AsyncMock(return_value=None))
    _install_service_module("location_service", location_service=fake_loc)

    c = ServiceRequestConsumer()
    out = await c._handle_locations_request(
        "GET", {"data": {}, "endpoint": "locations/vehicle/ABC123"}
    )
    d = out["data"]
    assert d["vehicle_id"] == "ABC123"
    assert d["latitude"] == PRETORIA_COORDINATES[1]
    assert d["longitude"] == PRETORIA_COORDINATES[0]


@pytest.mark.asyncio
async def test_locations_handler_post_update_vs_create():
    _install_fake_db_module(connected=True)
    _install_response_builder_stub()

    class _Obj:
        def __init__(self, which): self._which = which
        def model_dump(self): return {"which": self._which}

    fake_loc = types.SimpleNamespace(
        update_vehicle_location=AsyncMock(return_value=_Obj("update")),
        create_vehicle_location=AsyncMock(return_value=_Obj("create")),
        get_all_vehicle_locations=AsyncMock(return_value=[]),
        get_all_vehicles=AsyncMock(return_value=[]),
    )
    _install_service_module("location_service", location_service=fake_loc)

    c = ServiceRequestConsumer()

    # update path (`update` in endpoint)
    out1 = await c._handle_locations_request(
        "POST",
        {"data": {"vehicle_id": "v1", "latitude": 1.0, "longitude": 2.0}, "endpoint": "locations/update"}
    )
    assert out1["data"]["which"] == "update"
    fake_loc.update_vehicle_location.assert_awaited_once()

    # create path (no 'update' in endpoint)
    out2 = await c._handle_locations_request(
        "POST",
        {"data": {"vehicle_id": "v2", "latitude": 3.0, "longitude": 4.0}, "endpoint": "locations"}
    )
    assert out2["data"]["which"] == "create"
    fake_loc.create_vehicle_location.assert_awaited_once()


@pytest.mark.asyncio
async def test_locations_handler_delete_missing_vehicle_id_returns_error():
    _install_fake_db_module(connected=True)
    _install_response_builder_stub()

    _install_service_module(
        "location_service",
        location_service=types.SimpleNamespace(delete_vehicle_location=AsyncMock(return_value=True))
    )

    c = ServiceRequestConsumer()
    out = await c._handle_locations_request("DELETE", {"data": {}, "endpoint": "locations"})
    assert out["status"] == "error"
    assert out["error"] == "LocationRequestError"


@pytest.mark.asyncio
async def test_geofences_handler_post_missing_required_field():
    _install_fake_db_module(connected=True)
    _install_response_builder_stub()

    _install_service_module(
        "geofence_service",
        geofence_service=types.SimpleNamespace(create_geofence=AsyncMock())
    )

    c = ServiceRequestConsumer()
    # Missing 'name' should trigger required-field error
    out = await c._handle_geofences_request(
        "POST", {"data": {"geometry": {"type": "circle"}}, "endpoint": "geofences"}
    )
    assert out["status"] == "error"
    assert out["error"] == "GeofenceRequestError"


@pytest.mark.asyncio
async def test_places_handler_get_by_id_none():
    _install_fake_db_module(connected=True)
    _install_response_builder_stub()

    _install_service_module(
        "places_service",
        places_service=types.SimpleNamespace(get_place_by_id=AsyncMock(return_value=None))
    )

    c = ServiceRequestConsumer()
    out = await c._handle_places_request("GET", {"data": {}, "endpoint": "places/abc"})
    assert out["status"] == "success"
    assert out["data"] is None


@pytest.mark.asyncio
async def test_send_response_uses_exchange_publish(monkeypatch):
    _install_response_builder_stub()

    c = ServiceRequestConsumer()
    # Avoid real connections
    monkeypatch.setattr(c, "_setup_response_connection", AsyncMock())
    # Fake exchange with publish
    c._response_exchange = types.SimpleNamespace(publish=AsyncMock())
    # Provide routing key string
    c.config.ROUTING_KEYS = {"core_responses": "core.responses"}

    await c._send_response("corr-1", {"ok": True})
    c._response_exchange.publish.assert_awaited_once()


@pytest.mark.asyncio
async def test_handle_request_success_flow(monkeypatch):
    _install_response_builder_stub()
    c = ServiceRequestConsumer()
    # Observe the call; don't actually publish
    monkeypatch.setattr(c, "_send_response", AsyncMock())

    msg = _FakeMessage({
        "correlation_id": "abc",
        "method": "GET",
        "endpoint": "health",
        "user_context": {},
        "data": {}
    })
    await c.handle_request(msg)

    # The call uses positional args: (correlation_id, response_dict)
    assert c._send_response.await_args.args[0] == "abc"
    sent_payload = c._send_response.await_args.args[1]
    assert sent_payload["status"] == "success"


@pytest.mark.asyncio
async def test_handle_request_duplicate_ignored(monkeypatch):
    _install_response_builder_stub()
    c = ServiceRequestConsumer()
    # mark as recently processed
    c.processed_requests["dupe"] = time.time()

    monkeypatch.setattr(c, "_send_response", AsyncMock())
    msg = _FakeMessage({
        "correlation_id": "dupe",
        "method": "GET",
        "endpoint": "health",
        "user_context": {},
        "data": {}
    })
    await c.handle_request(msg)

    # Should be ignored due to de-duplication window
    c._send_response.assert_not_awaited()


@pytest.mark.asyncio
async def test_route_request_unknown_endpoint_raises():
    _install_response_builder_stub()
    c = ServiceRequestConsumer()
    with pytest.raises(ValueError):
        await c._route_request("GET", {}, "nope/nowhere")
