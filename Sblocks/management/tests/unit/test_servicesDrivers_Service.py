import sys
import os
import types
import importlib
import pytest
from datetime import datetime

HERE = os.path.abspath(os.path.dirname(__file__))
CANDIDATE_PATHS = [
    os.path.abspath(os.path.join(HERE, "..", "..", "services", "drivers_service.py")),
    os.path.abspath(os.path.join(os.getcwd(), "Sblocks", "management", "services", "drivers_service.py")),
    os.path.abspath(os.path.join(os.getcwd(), "Sblocks", "maintenance", "services", "drivers_service.py")),
    os.path.abspath(os.path.join(os.getcwd(), "services", "drivers_service.py")),
    os.path.abspath(os.path.join(os.getcwd(), "drivers_service.py")),
]

def _ensure_mod(name):
    if name not in sys.modules:
        sys.modules[name] = types.ModuleType(name)
    return sys.modules[name]


repositories = _ensure_mod("repositories")
repos_pkg = _ensure_mod("repositories.repositories")
events = _ensure_mod("events")
events_pub = _ensure_mod("events.publisher")
schemas = _ensure_mod("schemas")
schemas_requests = _ensure_mod("schemas.requests")
schemas_entities = _ensure_mod("schemas.entities")


if not hasattr(schemas_requests, "DailyDriverCount"):
    class DailyDriverCount: ...
    schemas_requests.DailyDriverCount = DailyDriverCount
if not hasattr(schemas_entities, "DailyDriverCount"):
    class DailyDriverCountE: ...
    schemas_entities.DailyDriverCount = DailyDriverCountE


if not hasattr(events_pub, "event_publisher"):
    class _EP:
        def __init__(self): self.events = []
        async def publish_event(self, event): self.events.append(event)
    events_pub.event_publisher = _EP()

class _DriverCountRepo:
    def __init__(self):
        self.calls = []
        self.add_calls = 0
        self.remove_calls = 0
        self.next_counts = {"ok": True}
        self.raise_on_get = None
        self.raise_on_add = None
        self.raise_on_remove = None
    async def get_daily_driver_counts(self, start_date=None):
        self.calls.append(start_date)
        if self.raise_on_get:
            raise self.raise_on_get
        return self.next_counts
    async def add_driver(self):
        self.add_calls += 1
        if self.raise_on_add:
            raise self.raise_on_add
    async def remove_driver(self):
        self.remove_calls += 1
        if self.raise_on_remove:
            raise self.raise_on_remove

repos_pkg.DriverCountRepository = _DriverCountRepo


def _load_drivers_module():
    import importlib.util
    if "services" not in sys.modules:
        pkg = types.ModuleType("services")
        pkg.__path__ = []
        sys.modules["services"] = pkg
    for path in CANDIDATE_PATHS:
        if os.path.exists(path):
            spec = importlib.util.spec_from_file_location("services.drivers_service", path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules["services.drivers_service"] = mod
            spec.loader.exec_module(mod)
            return mod
    raise ImportError("drivers_service.py not found in expected locations")

ds_mod = _load_drivers_module()
DriversService = ds_mod.DriversService

def make_service():
    svc = DriversService()
    assert isinstance(svc.drivers_repo, _DriverCountRepo)
    return svc



@pytest.mark.asyncio
async def test_get_daily_driver_counts_none_and_with_date():
    svc = make_service()

    out1 = await svc.get_daily_driver_counts()
    assert out1 == {"ok": True}

    sd = datetime(2030, 1, 1, 9, 30, 0)
    out2 = await svc.get_daily_driver_counts(sd)
    assert out2 == {"ok": True}

    assert svc.drivers_repo.calls[0] is None
    assert svc.drivers_repo.calls[1] == sd

@pytest.mark.asyncio
async def test_get_daily_driver_counts_raises_propagates():
    svc = make_service()
    svc.drivers_repo.raise_on_get = RuntimeError("boom")
    with pytest.raises(RuntimeError):
        await svc.get_daily_driver_counts()



@pytest.mark.asyncio
async def test_add_driver_success_and_error():
    svc = make_service()
    await svc.add_driver()
    assert svc.drivers_repo.add_calls == 1
    svc.drivers_repo.raise_on_add = ValueError("bad")
    with pytest.raises(ValueError):
        await svc.add_driver()

@pytest.mark.asyncio
async def test_remove_driver_success_and_error():
    svc = make_service()
    await svc.remove_driver()
    assert svc.drivers_repo.remove_calls == 1
    svc.drivers_repo.raise_on_remove = ValueError("bad")
    with pytest.raises(ValueError):
        await svc.remove_driver()

# ----------------- handle_request -----------------

@pytest.mark.asyncio
async def test_handle_request_post_with_start_date_and_without():
    svc = make_service()
    sd = datetime(2030, 2, 2, 10, 0, 0)
    res1 = await svc.handle_request("POST", {"endpoint": "daily-driver-count", "data": {"start_date": sd}})
    assert res1 == {"success": True, "data": {"ok": True}}
    assert svc.drivers_repo.calls[-1] == sd
    res2 = await svc.handle_request("POST", {"endpoint": "daily_driver_count", "data": {}})
    assert res2 == {"success": True, "data": {"ok": True}}
    assert svc.drivers_repo.calls[-1] is None  

@pytest.mark.asyncio
async def test_handle_request_post_non_matching_endpoint_returns_none_current_behavior():
    svc = make_service()
    res = await svc.handle_request("POST", {"endpoint": "other_endpoint", "data": {}})
    assert res is None 

@pytest.mark.asyncio
async def test_handle_request_non_post_returns_unsupported():
    svc = make_service()
    ctx = {"endpoint": "anything", "data": {"x": 1}}
    res = await svc.handle_request("GET", ctx)
    assert res["success"] is False
    assert res["error"] == "Unsupported drivers operation"
    assert res["method"] == "GET"
    assert res["user_context"] == ctx

@pytest.mark.asyncio
async def test_handle_request_error_wrapped_with_context(monkeypatch):
    svc = make_service()
    async def boom(*a, **k): raise RuntimeError("explode")
    monkeypatch.setattr(svc, "get_daily_driver_counts", boom)
    ctx = {"endpoint": "daily_driver_count", "data": {}}
    res = await svc.handle_request("POST", ctx)
    assert res["success"] is False
    assert "explode" in res["error"]
    assert res["method"] == "POST"
    assert res["user_context"] == ctx
