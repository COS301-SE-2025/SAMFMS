import sys
import os
import json
import types
import asyncio
import importlib
from datetime import datetime, timezone

import pytest

HERE = os.path.abspath(os.path.dirname(__file__))
CANDIDATES = [
    os.path.abspath(os.path.join(HERE, "..", "..")),
    os.path.abspath(os.path.join(HERE, "..")),
    os.getcwd(),
]
for p in CANDIDATES:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    rc_mod = importlib.import_module("services.request_consumer")
except Exception:
    rc_mod = importlib.import_module("request_consumer")

ServiceRequestConsumer = rc_mod.ServiceRequestConsumer

class FakeExchange:
    def __init__(self, name="responses"):
        self.name = name
        self.published = []
        self.raise_on_publish = False

    async def publish(self, message, routing_key):
        if self.raise_on_publish:
            raise RuntimeError("publish_error")
        self.published.append((message, routing_key))

class FakeQueue:
    def __init__(self, name="q"):
        self.name = name
        self.bound = None
        self.consume_calls = []

    async def bind(self, exchange, routing_key):
        self.bound = (exchange.name, routing_key)

    async def consume(self, callback, no_ack=False):
        self.consume_calls.append({"cb": callback, "no_ack": no_ack})
        return "consumer-tag"

class FakeChannel:
    def __init__(self):
        self.exchanges = {}
        self.queues = {}

    async def declare_exchange(self, name, _type, durable=True):
        ex = FakeExchange(name)
        self.exchanges[name] = ex
        return ex

    async def declare_queue(self, name, durable=True):
        q = FakeQueue(name)
        self.queues[name] = q
        return q

class FakeConnection:
    def __init__(self, open_=True, channel=None):
        self.is_closed = not open_
        self._channel = channel or FakeChannel()
        self.closed_calls = 0

    async def channel(self):
        return self._channel

    async def close(self):
        self.is_closed = True
        self.closed_calls += 1

class FakeMessage:
    def __init__(self, body, delivery_mode=None, content_type=None, headers=None):
        self.body = body
        self.delivery_mode = delivery_mode
        self.content_type = content_type
        self.headers = headers

class FakeDeliveryMode:
    PERSISTENT = 2


async def _async_return(value):
    return value

def patch_connect_to_fake(monkeypatch):
    """Patch the exact symbol used by the module to an *async* factory returning FakeConnection."""
    async def _connect(*a, **k):
        return FakeConnection()
    if hasattr(rc_mod, "aio_pika") and hasattr(rc_mod.aio_pika, "connect_robust"):
        monkeypatch.setattr(rc_mod.aio_pika, "connect_robust", _connect, raising=True)
    elif hasattr(rc_mod, "connect_robust"):
        monkeypatch.setattr(rc_mod, "connect_robust", _connect, raising=True)
    else:
        if not hasattr(rc_mod, "aio_pika"):
            rc_mod.aio_pika = types.SimpleNamespace()
        monkeypatch.setattr(rc_mod.aio_pika, "connect_robust", _connect, raising=True)

def patch_connect_to_raise(monkeypatch, exc: Exception):
    """Patch connect_robust to *async* raise."""
    async def _boom(*a, **k):
        raise exc
    if hasattr(rc_mod, "aio_pika") and hasattr(rc_mod.aio_pika, "connect_robust"):
        monkeypatch.setattr(rc_mod.aio_pika, "connect_robust", _boom, raising=True)
    elif hasattr(rc_mod, "connect_robust"):
        monkeypatch.setattr(rc_mod, "connect_robust", _boom, raising=True)

def patch_message_types(monkeypatch):
    """Ensure Message and DeliveryMode used by the module are harmless."""
    if hasattr(rc_mod, "aio_pika"):
        monkeypatch.setattr(rc_mod.aio_pika, "Message", FakeMessage, raising=True)
        monkeypatch.setattr(rc_mod.aio_pika, "DeliveryMode", FakeDeliveryMode, raising=True)
    else:
        if hasattr(rc_mod, "Message"):
            monkeypatch.setattr(rc_mod, "Message", FakeMessage, raising=True)
        if hasattr(rc_mod, "DeliveryMode"):
            monkeypatch.setattr(rc_mod, "DeliveryMode", FakeDeliveryMode, raising=True)

def install_db_manager_stub(admin_obj):
    """
    Install a real module at repositories.database.db_manager and expose it on
    repositories.database so `from repositories.database import db_manager`
    resolves to our stub.
    """

    if "repositories" not in sys.modules:
        sys.modules["repositories"] = types.ModuleType("repositories")

    if "repositories.database" not in sys.modules:
        sys.modules["repositories.database"] = types.ModuleType("repositories.database")

    dbm = types.ModuleType("repositories.database.db_manager")
    dbm.client = types.SimpleNamespace(admin=admin_obj)
    sys.modules["repositories.database.db_manager"] = dbm

    setattr(sys.modules["repositories.database"], "db_manager", dbm)

def test_constructor_sets_names_and_cache_defaults():
    svc = ServiceRequestConsumer()
    cfg = rc_mod.RabbitMQConfig()
    assert svc.queue_name == cfg.QUEUE_NAMES["maintenance"]
    assert svc.exchange_name == cfg.EXCHANGE_NAMES["requests"]
    assert svc.response_exchange_name == cfg.EXCHANGE_NAMES["responses"]
    assert svc._db_status_cache["status"] is None
    assert svc._db_status_cache["cache_ttl"] == 30.0

@pytest.mark.asyncio
async def test_connect_success(monkeypatch):
    patch_connect_to_fake(monkeypatch)
    svc = ServiceRequestConsumer()
    ok = await svc.connect()
    assert ok is True
    assert isinstance(svc.connection, FakeConnection)
    assert svc.exchange.name == rc_mod.RabbitMQConfig().EXCHANGE_NAMES["requests"]
    assert svc.response_exchange.name == rc_mod.RabbitMQConfig().EXCHANGE_NAMES["responses"]
    assert svc.queue.name == rc_mod.RabbitMQConfig().QUEUE_NAMES["maintenance"]

@pytest.mark.asyncio
async def test_connect_raises_on_failure(monkeypatch):
    patch_connect_to_raise(monkeypatch, RuntimeError("conn_fail"))
    svc = ServiceRequestConsumer()
    with pytest.raises(RuntimeError):
        await svc.connect()

@pytest.mark.asyncio
async def test_setup_response_connection_creates_when_missing(monkeypatch):
    patch_connect_to_fake(monkeypatch)
    svc = ServiceRequestConsumer()
    svc._response_connection = None
    await svc._setup_response_connection()
    assert svc._response_exchange.name == rc_mod.RabbitMQConfig().EXCHANGE_NAMES["responses"]

@pytest.mark.asyncio
async def test_setup_response_connection_skips_when_open(monkeypatch):
    calls = {"n": 0}
    async def counting_connect(*a, **k):
        calls["n"] += 1
        return FakeConnection()
    if hasattr(rc_mod, "aio_pika") and hasattr(rc_mod.aio_pika, "connect_robust"):
        monkeypatch.setattr(rc_mod.aio_pika, "connect_robust", counting_connect, raising=True)

    svc = ServiceRequestConsumer()
    class _Open:
        is_closed = False
    svc._response_connection = _Open()
    await svc._setup_response_connection()
    assert calls["n"] == 0

@pytest.mark.asyncio
async def test_setup_response_connection_propagates_error(monkeypatch):
    patch_connect_to_raise(monkeypatch, RuntimeError("rconn_fail"))
    svc = ServiceRequestConsumer()
    with pytest.raises(RuntimeError):
        await svc._setup_response_connection()

@pytest.mark.asyncio
async def test_setup_queues_returns_existing_queue(monkeypatch):
    patch_connect_to_fake(monkeypatch)
    svc = ServiceRequestConsumer()
    await svc.connect()
    q = await svc.setup_queues()
    assert q is svc.queue

@pytest.mark.asyncio
async def test_start_consuming_connects_if_closed(monkeypatch):

    svc = ServiceRequestConsumer()
    svc.connection = types.SimpleNamespace(is_closed=True)

    async def fake_connect(self):
        self.connection = FakeConnection()
        self.channel = FakeChannel()
        self.exchange = FakeExchange("req")
        self.response_exchange = FakeExchange("resp")
        self.queue = FakeQueue("maintenance.queue")
        async def consume(cb, no_ack=False):
            self._consume_cb = cb
            self._consume_no_ack = no_ack
            return "tag"
        self.queue.consume = consume


    orig = ServiceRequestConsumer.connect
    try:
        object.__setattr__(svc, "connect", fake_connect.__get__(svc, ServiceRequestConsumer))
        await svc.start_consuming()
        assert svc.is_consuming is True
        assert getattr(svc, "_consume_cb") == svc.handle_request
        assert getattr(svc, "_consume_no_ack") is False
    finally:
        ServiceRequestConsumer.connect = orig

@pytest.mark.asyncio
async def test_start_consuming_propagates_consume_error(monkeypatch):
    patch_connect_to_fake(monkeypatch)
    svc = ServiceRequestConsumer()
    await svc.connect()
    async def boom(*_a, **_k):
        raise RuntimeError("consume_fail")
    svc.queue.consume = boom
    with pytest.raises(RuntimeError):
        await svc.start_consuming()

@pytest.mark.asyncio
async def test_stop_consuming_closes_open_connections():
    svc = ServiceRequestConsumer()
    class Closeable(FakeConnection):
        pass
    svc.connection = Closeable()
    svc._response_connection = Closeable()
    await svc.stop_consuming()
    assert svc.is_consuming is False
    assert svc.connection.is_closed is True
    assert svc._response_connection.is_closed is True

@pytest.mark.asyncio
async def test_disconnect_skips_when_already_closed():
    svc = ServiceRequestConsumer()
    class ClosedConn:
        def __init__(self): self.is_closed = True; self.closed_calls = 0
        async def close(self): self.closed_calls += 1
    svc.connection = ClosedConn()
    svc._response_connection = ClosedConn()
    await svc.disconnect()
    assert svc.connection.closed_calls == 0
    assert svc._response_connection.closed_calls == 0


@pytest.mark.asyncio
async def test_handle_request_success_sends_success_response(monkeypatch):
    svc = ServiceRequestConsumer()

    async def passthrough(coro, timeout):
        return await coro
    monkeypatch.setattr(asyncio, "wait_for", passthrough, raising=True)

    sent = {}
    async def fake_send(corr_id, payload):
        sent["cid"] = corr_id
        sent["payload"] = payload
    monkeypatch.setattr(svc, "_send_response", fake_send, raising=True)

    async def fake_route(method, user_ctx, endpoint):
        return {"ok": True, "endpoint": endpoint}
    monkeypatch.setattr(svc, "_route_request", fake_route, raising=True)

    msg = types.SimpleNamespace()
    msg.body = json.dumps({
        "correlation_id": "abc",
        "method": "GET",
        "endpoint": "health",
        "user_context": {"data": {}}
    }).encode()

    class Ctx:
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False
    msg.process = lambda requeue=False: Ctx()

    await svc.handle_request(msg)
    assert sent["cid"] == "abc"
    assert sent["payload"]["status"] == "success"
    assert sent["payload"]["data"] == {"ok": True, "endpoint": "health"}

@pytest.mark.asyncio
async def test_handle_request_timeout_builds_error_response(monkeypatch):
    svc = ServiceRequestConsumer()

    async def timeout(_coro, _t):
        raise asyncio.TimeoutError()
    monkeypatch.setattr(asyncio, "wait_for", timeout, raising=True)

    sent = {}
    async def fake_send(corr_id, payload):
        sent["cid"] = corr_id
        sent["payload"] = payload
    monkeypatch.setattr(svc, "_send_response", fake_send, raising=True)

    msg = types.SimpleNamespace()
    msg.body = json.dumps({
        "correlation_id": "req-1",
        "method": "GET",
        "endpoint": "health",
        "user_context": {}
    }).encode()
    class Ctx:
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False
    msg.process = lambda requeue=False: Ctx()

    await svc.handle_request(msg)
    assert sent["cid"] == "req-1"
    assert "error" in sent["payload"]

@pytest.mark.asyncio
async def test_handle_request_bad_json_no_correlation_id_means_no_send(monkeypatch):
    svc = ServiceRequestConsumer()
    calls = {"n": 0}
    async def fake_send(*a, **k): calls["n"] += 1
    monkeypatch.setattr(svc, "_send_response", fake_send, raising=True)

    msg = types.SimpleNamespace()
    msg.body = b"{not-json"
    class Ctx:
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False
    msg.process = lambda requeue=False: Ctx()

    await svc.handle_request(msg)
    assert calls["n"] == 0

@pytest.mark.asyncio
async def test_route_validations_raise_value_error():
    svc = ServiceRequestConsumer()
    with pytest.raises(ValueError):
        await svc._route_request(None, {}, "x")
    with pytest.raises(ValueError):
        await svc._route_request("GET", "not-a-dict", "x")
    with pytest.raises(ValueError):
        await svc._route_request("GET", {}, 123)

@pytest.mark.asyncio
async def test_route_to_each_known_endpoint(monkeypatch):
    svc = ServiceRequestConsumer()

    async def make_stub(tag):
        async def _(*_a, **_k): return {"handler": tag}
        return _
    monkeypatch.setattr(svc, "_handle_health_request", await make_stub("health"), raising=True)
    monkeypatch.setattr(svc, "_handle_maintenance_records_request", await make_stub("records"), raising=True)
    monkeypatch.setattr(svc, "_handle_schedules_request", await make_stub("schedules"), raising=True)
    monkeypatch.setattr(svc, "_handle_license_request", await make_stub("licenses"), raising=True)
    monkeypatch.setattr(svc, "_handle_analytics_request", await make_stub("analytics"), raising=True)
    monkeypatch.setattr(svc, "_handle_notification_request", await make_stub("notifications"), raising=True)
    monkeypatch.setattr(svc, "_handle_vendor_request", await make_stub("vendors"), raising=True)
    monkeypatch.setattr(svc, "_handle_status_request", await make_stub("status"), raising=True)
    monkeypatch.setattr(svc, "_handle_docs_request", await make_stub("docs"), raising=True)
    monkeypatch.setattr(svc, "_handle_metrics_request", await make_stub("metrics"), raising=True)

    assert (await svc._route_request("GET", {"endpoint": ""}, ""))["handler"] == "health"
    assert (await svc._route_request("GET", {"endpoint": "health"}, "health"))["handler"] == "health"
    assert (await svc._route_request("GET", {"endpoint": "records/overdue"}, "records/overdue"))["handler"] == "records"
    assert (await svc._route_request("GET", {"endpoint": "schedules/upcoming"}, "schedules/upcoming"))["handler"] == "schedules"
    assert (await svc._route_request("GET", {"endpoint": "licenses"}, "licenses"))["handler"] == "licenses"
    assert (await svc._route_request("GET", {"endpoint": "analytics/dashboard"}, "analytics/dashboard"))["handler"] == "analytics"
    assert (await svc._route_request("GET", {"endpoint": "notifications"}, "notifications"))["handler"] == "notifications"
    assert (await svc._route_request("GET", {"endpoint": "vendors"}, "vendors"))["handler"] == "vendors"
    assert (await svc._route_request("GET", {"endpoint": "status"}, "status"))["handler"] == "status"
    assert (await svc._route_request("GET", {"endpoint": "docs"}, "docs"))["handler"] == "docs"
    assert (await svc._route_request("GET", {"endpoint": "metrics"}, "metrics"))["handler"] == "metrics"

@pytest.mark.asyncio
async def test_route_unknown_endpoint_raises():
    svc = ServiceRequestConsumer()
    with pytest.raises(ValueError):
        await svc._route_request("GET", {}, "unknown/path")

@pytest.mark.asyncio
async def test_send_response_publishes_success_message(monkeypatch):
    patch_message_types(monkeypatch)
    svc = ServiceRequestConsumer()
    svc.response_exchange = FakeExchange("responses")
    await svc._send_response("corr-1", {"foo": "bar"})
    assert len(svc.response_exchange.published) == 1
    msg, rkey = svc.response_exchange.published[0]
    payload = json.loads(msg.body.decode())
    assert payload["correlation_id"] == "corr-1"
    assert payload["status"] == "success"
    assert payload["data"] == {"foo": "bar"}
    assert rkey == rc_mod.RabbitMQConfig().ROUTING_KEYS["core_responses"]

@pytest.mark.asyncio
async def test_send_response_raises_if_publish_fails(monkeypatch):
    patch_message_types(monkeypatch)
    svc = ServiceRequestConsumer()
    svc.response_exchange = FakeExchange("responses")
    svc.response_exchange.raise_on_publish = True
    with pytest.raises(RuntimeError):
        await svc._send_response("x", {"y": 1})

@pytest.mark.asyncio
async def test_send_error_response_swallows_publish_error(monkeypatch):
    patch_message_types(monkeypatch)
    svc = ServiceRequestConsumer()
    svc.response_exchange = FakeExchange("responses")
    await svc._send_error_response("id", "boom")
    assert len(svc.response_exchange.published) >= 1
    svc.response_exchange.raise_on_publish = True
    await svc._send_error_response("id2", "oops")

@pytest.mark.asyncio
async def test_db_check_uses_fresh_cache_true(monkeypatch):
    svc = ServiceRequestConsumer()
    svc._db_status_cache.update({"status": True, "last_check": 1000.0, "cache_ttl": 30.0})
    monkeypatch.setattr(rc_mod.time, "time", lambda: 1010.0, raising=True)  # within TTL
    class Admin:
        def __init__(self): self.calls = 0
        async def command(self, cmd): self.calls += 1; return {"ok": 1}
    install_db_manager_stub(Admin())
    ok = await svc._check_database_connectivity()
    assert ok is True

@pytest.mark.asyncio
async def test_db_check_uses_fresh_cache_false(monkeypatch):
    svc = ServiceRequestConsumer()
    svc._db_status_cache.update({"status": False, "last_check": 1000.0, "cache_ttl": 30.0})
    monkeypatch.setattr(rc_mod.time, "time", lambda: 1010.0, raising=True) 
    class Admin:
        def __init__(self): self.calls = 0
        async def command(self, cmd): self.calls += 1; return {"ok": 1}
    install_db_manager_stub(Admin())
    ok = await svc._check_database_connectivity()
    assert ok is False

@pytest.mark.asyncio
async def test_db_check_expired_cache_success(monkeypatch):
    svc = ServiceRequestConsumer()
    svc._db_status_cache.update({"status": None, "last_check": 0.0, "cache_ttl": 30.0})
    monkeypatch.setattr(rc_mod.time, "time", lambda: 2000.0, raising=True)  
    class Admin:
        def __init__(self): self.calls = 0
        async def command(self, cmd): self.calls += 1; return {"ok": 1}
    admin = Admin()
    install_db_manager_stub(admin)
    ok = await svc._check_database_connectivity()
    assert ok is True
    assert svc._db_status_cache["status"] is True
    assert svc._db_status_cache["last_check"] == 2000.0
    assert admin.calls == 1 

@pytest.mark.asyncio
async def test_db_check_expired_cache_failure(monkeypatch):
    svc = ServiceRequestConsumer()
    svc._db_status_cache.update({"status": None, "last_check": 0.0, "cache_ttl": 30.0})
    monkeypatch.setattr(rc_mod.time, "time", lambda: 3000.0, raising=True)  
    class Admin:
        def __init__(self): self.calls = 0
        async def command(self, cmd):
            self.calls += 1
            raise RuntimeError("db down")
    admin = Admin()
    install_db_manager_stub(admin)
    ok = await svc._check_database_connectivity()
    assert ok is False
    assert svc._db_status_cache["status"] is False
    assert svc._db_status_cache["last_check"] == 3000.0
    assert admin.calls == 1  
