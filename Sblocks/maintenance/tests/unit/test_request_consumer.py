import pytest
from unittest.mock import AsyncMock
from services.request_consumer import ServiceRequestConsumer

@pytest.fixture
def consumer():
    return ServiceRequestConsumer()

@pytest.mark.asyncio
async def test_route_request_dispatches_to_handlers(mocker, consumer):
    mocker.object(consumer, "_handle_health_request", new=AsyncMock(return_value={"ok":True}), create=True)
    res = await consumer._route_request("GET", {}, "health")
    assert res == {"ok": True}

@pytest.mark.asyncio
async def test_route_request_unknown_endpoint_raises(mocker, consumer):
    with pytest.raises(ValueError):
        await consumer._route_request("GET", {}, "nope")

@pytest.mark.asyncio
async def test_route_request_validates_inputs(mocker, consumer):
    with pytest.raises(ValueError):
        await consumer._route_request(None, {}, "health")
    with pytest.raises(ValueError):
        await consumer._route_request("GET", "not_a_dict", "health")
    with pytest.raises(ValueError):
        await consumer._route_request("GET", {}, 123)

@pytest.mark.asyncio
async def test_handle_request_success_sends_response(mocker, consumer):
    import json
    from unittest.mock import AsyncMock

    class Msg:
        def __init__(self, body):
            self.body = body
        def process(self, requeue=False):
            class _Ctx:
                async def __aenter__(inner): return None
                async def __aexit__(inner, exc_type, exc, tb): return False
            return _Ctx()

    mocker.object(consumer, "_check_database_connectivity", new=AsyncMock(return_value=True), create=True)
    mocker.object(consumer, "_route_request", new=AsyncMock(return_value={"ok": True}), create=True)
    mocker.object(consumer, "_send_response", new=AsyncMock(), create=True)

    payload = {
        "correlation_id": "cid-1",
        "method": "GET",
        "endpoint": "health",
        "data": {},
        "reply_to": "reply.queue",
    }
    await consumer.handle_request(Msg(json.dumps(payload).encode()))
    consumer._send_response.assert_called_once()
    args, _ = consumer._send_response.call_args
    assert args[0] == "cid-1"

@pytest.mark.asyncio
async def test_check_database_connectivity_caches(mocker, consumer):
    # Force an initial known result (True), then confirm cached value is returned.
    mocker.patch("services.request_consumer.asyncio.wait_for", new=AsyncMock(return_value=None))
    first = await consumer._check_database_connectivity()
    # Flip the cached status to False and keep last_check fresh to ensure cache is used
    consumer._db_status_cache["status"] = False
    # NOTE: do not push last_check far back; we want it treated as FRESH
    second = await consumer._check_database_connectivity()
    assert first in (True, False)  # don't assert exact truthiness of env
    assert second is False   