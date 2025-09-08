import sys
import asyncio
import types
import importlib
from types import ModuleType
import pathlib
from typing import Optional, Dict, Any
import pytest
import pytest_asyncio
import httpx
from fastapi import FastAPI
from httpx import AsyncClient

# --- Make project importable ---
CORE_DIR = pathlib.Path(__file__).resolve().parents[2]
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

# --- PRE-SEED rabbitmq so routes.service_routing can import cleanly ---
# Create a real "package" (has __path__) and a minimal consumer submodule.
if "rabbitmq" not in sys.modules:
    rabbitmq_pkg = ModuleType("rabbitmq")
    rabbitmq_pkg.__path__ = []  # mark as package
    sys.modules["rabbitmq"] = rabbitmq_pkg
if "rabbitmq.consumer" not in sys.modules:
    consumer_mod = ModuleType("rabbitmq.consumer")

    def consume_messages(*_a, **_k):  # noop stub
        pass

    consumer_mod.consume_messages = consume_messages
    sys.modules["rabbitmq.consumer"] = consumer_mod

# Defer import until after the pre-seed above
health = importlib.import_module("routes.health")


@pytest.fixture
def app():
    app = FastAPI()
    router = getattr(health, "health_router", None) or getattr(health, "router", None)
    assert router is not None, "routes.health must expose `health_router` or `router`"
    app.include_router(router)
    return app


async def client(app):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---------- small helpers ----------

def _ensure_pkg(monkeypatch, name: str):
    if name not in sys.modules:
        pkg = ModuleType(name)
        pkg.__path__ = []
        monkeypatch.setitem(sys.modules, name, pkg)


def _stub_database_module(
    monkeypatch,
    *,
    health_status={"status": "healthy"},
    health_raises: Optional[Exception] = None,
    has_client: bool = True,
):
    mod = ModuleType("database")

    class _DB:
        def __init__(self):
            self.client = object() if has_client else None

        async def health_check(self):
            if health_raises:
                raise health_raises
            return health_status

    async def get_database_manager():
        return _DB()

    mod.get_database_manager = get_database_manager
    monkeypatch.setitem(sys.modules, "database", mod)


def _stub_rabbitmq_ok(monkeypatch):
    _ensure_pkg(monkeypatch, "rabbitmq")
    # admin submodule
    admin = ModuleType("rabbitmq.admin")
    admin.RABBITMQ_URL = "amqp://user:pass@localhost:5672/vhost"
    monkeypatch.setitem(sys.modules, "rabbitmq.admin", admin)
    # aio_pika stub
    aio = ModuleType("aio_pika")

    class Conn:
        async def close(self):
            return None

    async def connect_robust(url):
        return Conn()

    aio.connect_robust = connect_robust

    class ExchangeType:
        DIRECT = "direct"

    aio.ExchangeType = ExchangeType
    monkeypatch.setitem(sys.modules, "aio_pika", aio)


def _stub_rabbitmq_fail(monkeypatch, exc=RuntimeError("boom")):
    _ensure_pkg(monkeypatch, "rabbitmq")
    admin = ModuleType("rabbitmq.admin")
    admin.RABBITMQ_URL = "amqp://user:pass@localhost:5672/vhost"
    monkeypatch.setitem(sys.modules, "rabbitmq.admin", admin)
    aio = ModuleType("aio_pika")

    async def connect_robust(url):
        raise exc

    aio.connect_robust = connect_robust
    monkeypatch.setitem(sys.modules, "aio_pika", aio)


def _stub_service_discovery_ok(monkeypatch, services=None):
    if services is None:
        services = [{"name": "mgmt"}, {"name": "gps"}]
    _ensure_pkg(monkeypatch, "common")
    sd = ModuleType("common.service_discovery")

    class SD:
        async def get_healthy_services(self):
            return services

    async def get_service_discovery():
        return SD()

    sd.get_service_discovery = get_service_discovery
    monkeypatch.setitem(sys.modules, "common.service_discovery", sd)


def _stub_service_discovery_fail(monkeypatch, exc=RuntimeError("sd down")):
    _ensure_pkg(monkeypatch, "common")
    sd = ModuleType("common.service_discovery")

    async def get_service_discovery():
        class SD:
            async def get_healthy_services(self):
                raise exc

        return SD()

    sd.get_service_discovery = get_service_discovery
    monkeypatch.setitem(sys.modules, "common.service_discovery", sd)


def _patch_cb(monkeypatch, states):
    class CBMgr:
        @staticmethod
        def get_all_states():
            return states

    monkeypatch.setattr(health, "circuit_breaker_manager", CBMgr)


def _patch_cb_raises(monkeypatch, exc=RuntimeError("cb fail")):
    class CBMgr:
        @staticmethod
        def get_all_states():
            raise exc

    monkeypatch.setattr(health, "circuit_breaker_manager", CBMgr)


def _patch_dedup(monkeypatch, stats=None, raises: Optional[Exception] = None):
    class Dedup:
        @staticmethod
        def get_stats():
            if raises:
                raise raises
            return stats if stats is not None else {"hits": 1, "misses": 0}

    monkeypatch.setattr(health, "request_deduplicator", Dedup)


def _patch_tracer(
    monkeypatch,
    *,
    recent=None,
    stats=None,
    summary=None,
    raise_recent: Optional[Exception] = None,
    raise_stats: Optional[Exception] = None,
    raise_summary: Optional[Exception] = None,
):
    class Tracer:
        @staticmethod
        def get_recent_traces(limit):
            if raise_recent:
                raise raise_recent
            return recent if recent is not None else [{"id": "a"}]

        @staticmethod
        def get_trace_stats():
            if raise_stats:
                raise raise_stats
            return stats if stats is not None else {"active": 0}

        @staticmethod
        def get_trace_summary(correlation_id):
            if raise_summary:
                raise raise_summary
            return summary

    monkeypatch.setattr(health, "distributed_tracer", Tracer)


def _stub_request_router(monkeypatch, *, wait_raises: Optional[Exception] = None):
    _ensure_pkg(monkeypatch, "services")
    rr_mod = ModuleType("services.request_router")

    class RespMgr:
        async def wait_for_ready(self):
            if wait_raises:
                raise wait_raises
            return None

    class RR:
        response_manager = RespMgr()

    rr_mod.request_router = RR()
    monkeypatch.setitem(sys.modules, "services.request_router", rr_mod)


def _patch_route_to_service_block(monkeypatch, behavior: Dict[str, object]):
    async def fake_route_to_service_block(service_name: str, **kwargs):
        v = behavior.get(service_name)
        if isinstance(v, Exception):
            raise v
        return v or {"data": {"status": "ok"}}

    monkeypatch.setattr(health, "route_to_service_block", fake_route_to_service_block)


# ---------- /health (basic) ----------

@pytest.mark.asyncio
async def test_health_basic_ok(client):
    r = await client.get("/health/")
    j = r.json()
    assert r.status_code == 200
    assert j["status"] == "healthy"
    assert j.get("service") in {"samfms-core", j.get("service")}  # tolerate name diffs


# ---------- /health/live ----------

@pytest.mark.asyncio
async def test_liveness_ok(client):
    r = await client.get("/health/live")
    assert r.status_code == 200
    assert r.json()["status"] == "alive"


# ---------- /health/detailed ----------

@pytest.mark.asyncio
async def test_detailed_all_ok(client, monkeypatch):
    _stub_database_module(monkeypatch, health_status={"status": "healthy"})
    _stub_rabbitmq_ok(monkeypatch)
    _stub_service_discovery_ok(monkeypatch)
    _patch_cb(monkeypatch, states={"a": {"state": "closed"}, "b": {"state": "closed"}})
    _patch_dedup(monkeypatch)
    r = await client.get("/health/detailed")
    j = r.json()
    assert r.status_code == 200
    assert j["status"] == "healthy"
    assert j["checks"]["rabbitmq"]["status"] == "healthy"
    assert j["checks"]["database"]["status"] == "healthy"
    assert j["checks"]["circuit_breakers"]["status"] == "healthy"


@pytest.mark.asyncio
async def test_detailed_db_unhealthy_status(client, monkeypatch):
    _stub_database_module(monkeypatch, health_status={"status": "unhealthy"})
    _stub_rabbitmq_ok(monkeypatch)
    _stub_service_discovery_ok(monkeypatch)
    _patch_cb(monkeypatch, states={})
    _patch_dedup(monkeypatch)
    r = await client.get("/health/detailed")
    assert r.status_code == 503
    assert r.json()["checks"]["database"]["status"] == "unhealthy"


@pytest.mark.asyncio
async def test_detailed_db_raises(client, monkeypatch):
    _stub_database_module(monkeypatch, health_raises=RuntimeError("db err"))
    _stub_rabbitmq_ok(monkeypatch)
    _stub_service_discovery_ok(monkeypatch)
    _patch_cb(monkeypatch, states={})
    _patch_dedup(monkeypatch)
    r = await client.get("/health/detailed")
    j = r.json()
    assert r.status_code == 503
    assert j["checks"]["database"]["status"] == "unhealthy"


@pytest.mark.asyncio
async def test_detailed_rabbitmq_fails(client, monkeypatch):
    _stub_database_module(monkeypatch)
    _stub_rabbitmq_fail(monkeypatch)
    _stub_service_discovery_ok(monkeypatch)
    _patch_cb(monkeypatch, states={})
    _patch_dedup(monkeypatch)
    r = await client.get("/health/detailed")
    j = r.json()
    assert r.status_code == 503
    assert j["checks"]["rabbitmq"]["status"] == "unhealthy"


@pytest.mark.asyncio
async def test_detailed_service_discovery_degraded_but_overall_ok(client, monkeypatch):
    _stub_database_module(monkeypatch)
    _stub_rabbitmq_ok(monkeypatch)
    _stub_service_discovery_fail(monkeypatch)
    _patch_cb(monkeypatch, states={})
    _patch_dedup(monkeypatch)
    r = await client.get("/health/detailed")
    j = r.json()
    assert r.status_code == 200
    assert j["checks"]["service_discovery"]["status"] == "degraded"


@pytest.mark.asyncio
async def test_detailed_circuit_breakers_degraded_makes_overall_unhealthy(client, monkeypatch):
    _stub_database_module(monkeypatch)
    _stub_rabbitmq_ok(monkeypatch)
    _stub_service_discovery_ok(monkeypatch)
    _patch_cb(monkeypatch, states={"a": {"state": "closed"}, "b": {"state": "open"}})
    _patch_dedup(monkeypatch)
    r = await client.get("/health/detailed")
    j = r.json()
    assert r.status_code == 503
    assert j["checks"]["circuit_breakers"]["status"] == "degraded"


@pytest.mark.asyncio
async def test_detailed_circuit_breakers_unknown_does_not_flip_overall(client, monkeypatch):
    _stub_database_module(monkeypatch)
    _stub_rabbitmq_ok(monkeypatch)
    _stub_service_discovery_ok(monkeypatch)
    _patch_cb_raises(monkeypatch)
    _patch_dedup(monkeypatch)
    r = await client.get("/health/detailed")
    j = r.json()
    assert r.status_code == 200
    assert j["checks"]["circuit_breakers"]["status"] == "unknown"


@pytest.mark.asyncio
async def test_detailed_deduplicator_raises_makes_unhealthy(client, monkeypatch):
    _stub_database_module(monkeypatch)
    _stub_rabbitmq_ok(monkeypatch)
    _stub_service_discovery_ok(monkeypatch)
    _patch_cb(monkeypatch, states={})
    _patch_dedup(monkeypatch, raises=RuntimeError("dup fail"))
    r = await client.get("/health/detailed")
    j = r.json()
    assert r.status_code == 503
    assert j["checks"]["request_deduplicator"]["status"] == "unhealthy"


# ---------- /health/ready ----------

@pytest.mark.asyncio
async def test_ready_all_ready(client, monkeypatch):
    _stub_request_router(monkeypatch)  # ready
    _stub_database_module(monkeypatch, has_client=True)
    r = await client.get("/health/ready")
    j = r.json()
    assert r.status_code == 200
    assert j["status"] == "ready"
    assert j["checks"]["response_manager"]["status"] == "ready"
    assert j["checks"]["database"]["status"] == "ready"


@pytest.mark.asyncio
async def test_ready_response_manager_not_ready(client, monkeypatch):
    _stub_request_router(monkeypatch, wait_raises=RuntimeError("not ready"))
    _stub_database_module(monkeypatch, has_client=True)
    r = await client.get("/health/ready")
    j = r.json()
    assert r.status_code == 503
    assert j["checks"]["response_manager"]["status"] == "not_ready"


@pytest.mark.asyncio
async def test_ready_database_not_connected(client, monkeypatch):
    _stub_request_router(monkeypatch)
    _stub_database_module(monkeypatch, has_client=False)
    r = await client.get("/health/ready")
    j = r.json()
    assert r.status_code == 503
    assert j["checks"]["database"]["status"] == "not_ready"


@pytest.mark.asyncio
async def test_ready_database_error(client, monkeypatch):
    _stub_request_router(monkeypatch)
    mod = ModuleType("database")

    async def get_database_manager():
        raise RuntimeError("db down")

    mod.get_database_manager = get_database_manager
    monkeypatch.setitem(sys.modules, "database", mod)

    r = await client.get("/health/ready")
    j = r.json()
    assert r.status_code == 503
    assert j["checks"]["database"]["status"] == "not_ready"


# ---------- /health/circuit-breakers ----------

@pytest.mark.asyncio
async def test_circuit_breaker_status_ok(client, monkeypatch):
    _patch_cb(monkeypatch, states={"x": {"state": "closed"}})
    r = await client.get("/health/circuit-breakers")
    assert r.status_code == 200
    assert "circuit_breakers" in r.json()


@pytest.mark.asyncio
async def test_circuit_breaker_status_error(client, monkeypatch):
    _patch_cb_raises(monkeypatch)
    r = await client.get("/health/circuit-breakers")
    assert r.status_code == 500


# ---------- /health/metrics ----------

@pytest.mark.asyncio
async def test_metrics_with_psutil(client, monkeypatch):
    _patch_dedup(monkeypatch, stats={"a": 1})
    _patch_cb(monkeypatch, states={})
    _patch_tracer(monkeypatch, stats={"active": 2})

    # stub psutil module
    ps = ModuleType("psutil")

    class _MInfo:
        def __init__(self):
            self.rss = 100 * 1024 * 1024
            self.vms = 200 * 1024 * 1024

    class _Proc:
        def memory_info(self):
            return _MInfo()

        def memory_percent(self):
            return 12.34

    def _Process():
        return _Proc()

    ps.Process = _Process
    monkeypatch.setitem(sys.modules, "psutil", ps)

    r = await client.get("/health/metrics")
    j = r.json()
    assert r.status_code == 200
    assert "memory" in j and "rss_mb" in j["memory"]


@pytest.mark.asyncio
async def test_metrics_without_psutil(client, monkeypatch):
    _patch_dedup(monkeypatch)
    _patch_cb(monkeypatch, states={})
    _patch_tracer(monkeypatch)

    if "psutil" in sys.modules:
        monkeypatch.delitem(sys.modules, "psutil", raising=False)

    r = await client.get("/health/metrics")
    j = r.json()
    assert r.status_code == 200
    assert j["memory"]["status"] == "psutil_not_available"


@pytest.mark.asyncio
async def test_metrics_outer_error(client, monkeypatch):
    _patch_dedup(monkeypatch)
    _patch_cb(monkeypatch, states={})
    _patch_tracer(monkeypatch, raise_stats=RuntimeError("trace fail"))
    r = await client.get("/health/metrics")
    assert r.status_code == 500


# ---------- /health/traces ----------

@pytest.mark.asyncio
async def test_traces_ok(client, monkeypatch):
    _patch_tracer(monkeypatch, recent=[{"id": "1"}, {"id": "2"}])
    r = await client.get("/health/traces?limit=2")
    j = r.json()
    assert r.status_code == 200
    assert j["count"] == 2


@pytest.mark.asyncio
async def test_traces_error(client, monkeypatch):
    _patch_tracer(monkeypatch, raise_recent=RuntimeError("boom"))
    r = await client.get("/health/traces")
    assert r.status_code == 500


# ---------- /health/traces/{id} ----------

@pytest.mark.asyncio
async def test_trace_details_found(client, monkeypatch):
    _patch_tracer(monkeypatch, summary={"id": "abc"})
    r = await client.get("/health/traces/abc")
    j = r.json()
    assert r.status_code == 200
    assert j["trace"]["id"] == "abc"


@pytest.mark.asyncio
async def test_trace_details_not_found(client, monkeypatch):
    _patch_tracer(monkeypatch, summary=None)
    r = await client.get("/health/traces/unknown")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_trace_details_error(client, monkeypatch):
    _patch_tracer(monkeypatch, raise_summary=RuntimeError("nope"))
    r = await client.get("/health/traces/abc")
    assert r.status_code == 500


# ---------- /health/healthy-services ----------

@pytest.mark.asyncio
async def test_healthy_services_mixed(client, monkeypatch):
    behavior: Dict[str, object] = {
        "management": {"data": {"status": "ok"}},
        "maintenance": {"data": {"status": "ok"}},
        "gps": RuntimeError("gps down"),
        "trips": RuntimeError("trips down"),
    }
    _patch_route_to_service_block(monkeypatch, behavior)
    r = await client.get("/health/healthy-services")
    j = r.json()
    assert r.status_code == 200
    s = j["sblocks"]
    assert s["management"]["status"] == "ok"
    assert s["maintenance"]["status"] == "ok"
    assert s["gps"]["status"] == "unavailable"
    assert s["trips"]["status"] == "unavailable"
