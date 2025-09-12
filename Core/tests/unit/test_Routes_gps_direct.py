import os
import sys
import pytest
from fastapi import HTTPException

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

@pytest.mark.asyncio
async def test_request_location_success(monkeypatch):
    from routes import gps_direct as gps

    calls = []

    async def fake_publish_message(exchange, exchange_type, message, routing_key):
        calls.append((exchange, exchange_type, message, routing_key))

    monkeypatch.setattr(gps, "publish_message", fake_publish_message)

    payload = {"any": "thing"}
    resp = await gps.request_gps_location(payload)

    assert resp == {"status": "Location request sent to GPS service"}
    assert len(calls) == 1
    exchange, _etype, message, routing_key = calls[0]
    assert exchange == "gps_requests_Direct"
    assert routing_key == "gps_requests_Direct"
    assert message["operation"] == "retrieve"
    assert message["type"] == "location"
    assert message["parameters"] == payload


@pytest.mark.asyncio
async def test_request_location_failure(monkeypatch):
    from routes import gps_direct as gps

    async def failing_publish_message(*args, **kwargs):
        raise Exception("boom")

    monkeypatch.setattr(gps, "publish_message", failing_publish_message)

    with pytest.raises(HTTPException) as exc:
        await gps.request_gps_location({"x": 1})
    assert exc.value.status_code == 500
    assert "Failed to send location request: boom" in exc.value.detail


@pytest.mark.asyncio
async def test_request_speed_success(monkeypatch):
    from routes import gps_direct as gps

    calls = []

    async def fake_publish_message(exchange, exchange_type, message, routing_key):
        calls.append((exchange, exchange_type, message, routing_key))

    monkeypatch.setattr(gps, "publish_message", fake_publish_message)

    vid = "veh-123"
    resp = await gps.request_gps_speed(vid)

    assert resp == {"status": "Speed request sent to GPS service"}
    assert len(calls) == 1
    exchange, _etype, message, routing_key = calls[0]
    assert exchange == "gps_requests_Direct"
    assert routing_key == "gps_requests_Direct"
    assert message["operation"] == "retrieve"
    assert message["type"] == "speed"
    assert message["vehicle_id"] == vid


@pytest.mark.asyncio
async def test_request_speed_failure(monkeypatch):
    from routes import gps_direct as gps

    async def failing_publish_message(*args, **kwargs):
        raise Exception("nope")

    monkeypatch.setattr(gps, "publish_message", failing_publish_message)

    with pytest.raises(HTTPException) as exc:
        await gps.request_gps_speed("veh-1")
    assert exc.value.status_code == 500
    assert "Failed to send speed request: nope" in exc.value.detail


@pytest.mark.asyncio
async def test_request_direction_success(monkeypatch):
    from routes import gps_direct as gps

    calls = []

    async def fake_publish_message(exchange, exchange_type, message, routing_key):
        calls.append((exchange, exchange_type, message, routing_key))

    monkeypatch.setattr(gps, "publish_message", fake_publish_message)

    vid = "veh-xyz"
    resp = await gps.request_gps_direction(vid)

    assert resp == {"status": "Direction request sent to GPS service"}
    exchange, _etype, message, routing_key = calls[0]
    assert exchange == "gps_requests_Direct"
    assert routing_key == "gps_requests_Direct"
    assert message["operation"] == "retrieve"
    assert message["type"] == "direction"
    assert message["vehicle_id"] == vid


@pytest.mark.asyncio
async def test_request_direction_failure(monkeypatch):
    from routes import gps_direct as gps

    async def failing_publish_message(*args, **kwargs):
        raise Exception("bad")

    monkeypatch.setattr(gps, "publish_message", failing_publish_message)

    with pytest.raises(HTTPException) as exc:
        await gps.request_gps_direction("veh-2")
    assert exc.value.status_code == 500
    assert "Failed to send direction request: bad" in exc.value.detail


@pytest.mark.asyncio
async def test_request_fuel_level_success(monkeypatch):
    from routes import gps_direct as gps

    calls = []

    async def fake_publish_message(exchange, exchange_type, message, routing_key):
        calls.append((exchange, exchange_type, message, routing_key))

    monkeypatch.setattr(gps, "publish_message", fake_publish_message)

    vid = "veh-777"
    resp = await gps.request_gps_fuel_level(vid)

    assert resp == {"status": "Fuel level request sent to GPS service"}
    exchange, _etype, message, routing_key = calls[0]
    assert exchange == "gps_requests_Direct"
    assert routing_key == "gps_requests_Direct"
    assert message["operation"] == "retrieve"
    assert message["type"] == "fuel_level"
    assert message["vehicle_id"] == vid


@pytest.mark.asyncio
async def test_request_fuel_level_failure(monkeypatch):
    from routes import gps_direct as gps

    async def failing_publish_message(*args, **kwargs):
        raise Exception("kaboom")

    monkeypatch.setattr(gps, "publish_message", failing_publish_message)

    with pytest.raises(HTTPException) as exc:
        await gps.request_gps_fuel_level("veh-3")
    assert exc.value.status_code == 500
    assert "Failed to send fuel level request: kaboom" in exc.value.detail


@pytest.mark.asyncio
async def test_request_last_update_success(monkeypatch):
    from routes import gps_direct as gps

    calls = []

    async def fake_publish_message(exchange, exchange_type, message, routing_key):
        calls.append((exchange, exchange_type, message, routing_key))

    monkeypatch.setattr(gps, "publish_message", fake_publish_message)

    vid = "veh-last"
    resp = await gps.request_gps_last_update(vid)

    assert resp == {"status": "Last update request sent to GPS service"}
    exchange, _etype, message, routing_key = calls[0]
    assert exchange == "gps_requests_Direct"
    assert routing_key == "gps_requests_Direct"
    assert message["operation"] == "retrieve"
    assert message["type"] == "last_update"
    assert message["vehicle_id"] == vid


@pytest.mark.asyncio
async def test_request_last_update_failure(monkeypatch):
    from routes import gps_direct as gps

    async def failing_publish_message(*args, **kwargs):
        raise Exception("timeout")

    monkeypatch.setattr(gps, "publish_message", failing_publish_message)

    with pytest.raises(HTTPException) as exc:
        await gps.request_gps_last_update("veh-9")
    assert exc.value.status_code == 500
    assert "Failed to send last update request: timeout" in exc.value.detail
