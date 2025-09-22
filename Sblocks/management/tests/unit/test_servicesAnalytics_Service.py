import sys
import os
import types
import importlib
import pytest
from datetime import datetime, date, timedelta

HERE = os.path.abspath(os.path.dirname(__file__))
CANDIDATES = [
    os.path.abspath(os.path.join(HERE, "..", "..")),
    os.path.abspath(os.path.join(HERE, "..")),
    os.getcwd(),
]
for p in CANDIDATES:
    if p not in sys.path:
        sys.path.insert(0, p)

if "repositories" not in sys.modules:
    sys.modules["repositories"] = types.ModuleType("repositories")
if "repositories.repositories" not in sys.modules:
    sys.modules["repositories.repositories"] = types.ModuleType("repositories.repositories")

class _AnalyticsRepo:
    def __init__(self):
        self._cache = {}
        self.cache_calls = []
        self.cleanup_result = 0
    async def get_cached_metric(self, metric_type):
        return self._cache.get(metric_type)
    async def cache_metric(self, metric_type=None, data=None, ttl_minutes=None, **kw):
        self.cache_calls.append((metric_type, ttl_minutes))
        self._cache[metric_type] = {"data": data}
    async def cleanup_expired(self):
        return self.cleanup_result

class _AssignRepo:
    def __init__(self): self.calls = 0; self.metrics = {"status_breakdown": {"active": 2, "completed": 1}}
    async def get_assignment_metrics(self):
        self.calls += 1
        return dict(self.metrics)

class _UsageRepo:
    def __init__(self):
        self.stats = [
            {"vehicle_id": "V1", "total_distance": 100.0, "total_fuel": 12.5, "trip_count": 5, "fuel_efficiency": 8.0},
            {"vehicle_id": "V2", "total_distance": 50.0, "total_fuel": 7.5, "trip_count": 2, "fuel_efficiency": 10.0},
            {"vehicle_id": "V3", "total_distance": 10.0, "total_fuel": 1.0, "trip_count": 1, "fuel_efficiency": 10.0},
        ]
        self.driver_perf = [
            {"driver_id": "D1", "total_distance": 120.0, "trip_count": 6},
            {"driver_id": "D2", "total_distance": 40.0, "trip_count": 3},
        ]
        self._aggregate_queue = []
    async def get_vehicle_usage_stats(self):
        return list(self.stats)
    async def get_driver_performance_stats(self):
        return list(self.driver_perf)
    async def aggregate(self, pipeline):
        return self._aggregate_queue.pop(0) if self._aggregate_queue else []

class _DriverRepo:
    def __init__(self):
        self._counts = {("status", "active"): 2, ("total", None): 5}
        self._drivers = {"OK": {"name": "Jane", "employee_id": "E1", "status": "active"}}
    async def count(self, query):
        if query == {"status": "active"}:
            return self._counts[("status", "active")]
        return self._counts[("total", None)]
    async def find_by_id(self, driver_id):
        return self._drivers.get(driver_id)

class _DriverCountRepo:
    pass

repos_pkg = sys.modules["repositories.repositories"]
repos_pkg.VehicleAssignmentRepository = _AssignRepo
repos_pkg.VehicleUsageLogRepository = _UsageRepo
repos_pkg.DriverRepository = _DriverRepo
repos_pkg.AnalyticsRepository = _AnalyticsRepo
repos_pkg.DriverCountRepository = _DriverCountRepo

if "schemas" not in sys.modules:
    sys.modules["schemas"] = types.ModuleType("schemas")
if "schemas.responses" not in sys.modules:
    sresp = types.ModuleType("schemas.responses")
    class _Wrap:
        def __init__(self, d): self._d = d
        def model_dump(self): return self._d
    class ResponseBuilder:
        @staticmethod
        def success(data=None, message=""): return _Wrap({"status": "success", "data": data, "message": message})
        @staticmethod
        def error(error="Error", message=""): return _Wrap({"status": "error", "error": error, "message": message})
    sresp.ResponseBuilder = ResponseBuilder
    sys.modules["schemas.responses"] = sresp

if "services" in sys.modules:
    del sys.modules["services"]
services_pkg = types.ModuleType("services")
services_pkg.__path__ = []
sys.modules["services"] = services_pkg

def _load_analytics_module():
    import importlib.util
    candidates = [
        os.path.abspath(os.path.join(HERE, "..", "..", "services", "analytics_service.py")),
        os.path.abspath(os.path.join(HERE, "..", "..", "..", "services", "analytics_service.py")),
        os.path.abspath(os.path.join(os.getcwd(), "Sblocks", "maintenance", "services", "analytics_service.py")),
        os.path.abspath(os.path.join(os.getcwd(), "services", "analytics_service.py")),
        os.path.abspath(os.path.join(os.getcwd(), "analytics_service.py")),
    ]
    for path in candidates:
        if os.path.exists(path):
            spec = importlib.util.spec_from_file_location("services.analytics_service", path)
            module = importlib.util.module_from_spec(spec)
            sys.modules["services.analytics_service"] = module
            spec.loader.exec_module(module)
            return module
    raise ImportError("analytics_service.py not found")

as_mod = _load_analytics_module()
AnalyticsService = as_mod.AnalyticsService

def make_service():
    svc = AnalyticsService()
    assert isinstance(svc.assignment_repo, _AssignRepo)
    assert isinstance(svc.usage_repo, _UsageRepo)
    assert isinstance(svc.driver_repo, _DriverRepo)
    assert isinstance(svc.analytics_repo, _AnalyticsRepo)
    assert isinstance(svc.drivers_repo, _DriverCountRepo)
    return svc

@pytest.mark.asyncio
async def test_get_fleet_utilization_cache_hit(monkeypatch):
    svc = make_service()
    svc.analytics_repo._cache["fleet_utilization"] = {"data": {"cached": True}}
    async def boom(): raise AssertionError("should not call repo")
    monkeypatch.setattr(svc.assignment_repo, "get_assignment_metrics", boom)
    out = await svc.get_fleet_utilization(use_cache=True)
    assert out == {"cached": True}

@pytest.mark.asyncio
async def test_get_fleet_utilization_fresh_and_zero_division():
    svc = make_service()
    svc.assignment_repo.metrics = {"status_breakdown": {"active": 2, "completed": 1}}
    out = await svc.get_fleet_utilization(use_cache=False)
    assert out["total_assignments"] == 3
    assert out["utilization_rate"] == round(2/3, 3)
    assert out["completion_rate"] == round(1/3, 3)
    assert ("fleet_utilization", svc.cache_ttl["fleet_utilization"]) in svc.analytics_repo.cache_calls
    svc.assignment_repo.metrics = {"status_breakdown": {}}
    out2 = await svc.get_fleet_utilization(use_cache=False)
    assert out2["utilization_rate"] == 0 and out2["completion_rate"] == 0

@pytest.mark.asyncio
async def test_get_vehicle_usage_analytics_default_recomputes_and_cache_paths(monkeypatch):
    svc = make_service()
    out = await svc.get_vehicle_usage_analytics(use_cache=True)
    agg = out["aggregate_metrics"]
    assert agg["total_trips"] == 8
    assert agg["total_distance_km"] == 160.0
    assert agg["total_fuel_consumed"] == 21.0
    assert ("vehicle_usage", svc.cache_ttl["vehicle_usage"]) in svc.analytics_repo.cache_calls
    svc2 = make_service()
    svc2.analytics_repo._cache["vehicle_usage"] = {"data": {"cached": 1}}
    async def boom(): raise AssertionError("no recompute on cache hit when use_cache=False bug path")
    monkeypatch.setattr(svc2.usage_repo, "get_vehicle_usage_stats", boom)
    out2 = await svc2.get_vehicle_usage_analytics(use_cache=False)
    assert out2 == {"cached": 1}
    svc3 = make_service()
    out3 = await svc3.get_vehicle_usage_analytics(use_cache=False)
    assert ("vehicle_usage", svc3.cache_ttl["vehicle_usage"]) in svc3.analytics_repo.cache_calls

@pytest.mark.asyncio
async def test_get_assignment_metrics_cache_hit_and_fresh(monkeypatch):
    svc = make_service()
    svc.analytics_repo._cache["assignment_metrics"] = {"data": {"ok": 1}}
    assert await svc.get_assignment_metrics() == {"ok": 1}
    svc2 = make_service()
    out = await svc2.get_assignment_metrics(use_cache=False)
    assert out["generated_at"]

@pytest.mark.asyncio
async def test_get_driver_performance_cache_hit_and_fresh_and_empty():
    svc = make_service()
    svc.analytics_repo._cache["driver_performance"] = {"data": {"cached": 1}}
    assert await svc.get_driver_performance() == {"cached": 1}
    svc2 = make_service()
    out = await svc2.get_driver_performance(use_cache=False)
    assert out["summary"]["total_drivers"] == 5
    assert out["summary"]["active_drivers"] == 2
    assert out["summary"]["drivers_with_activity"] == 2
    svc3 = make_service()
    svc3.usage_repo.driver_perf = []
    out2 = await svc3.get_driver_performance(use_cache=False)
    assert out2["summary"]["drivers_with_activity"] == 0

@pytest.mark.asyncio
async def test_get_driver_performance_by_id_not_found_raises():
    svc = make_service()
    with pytest.raises(ValueError):
        await svc.get_driver_performance_by_id("NOPE")

@pytest.mark.asyncio
async def test_get_driver_performance_by_id_no_trips_returns_zeroes():
    svc = make_service()
    svc.driver_repo._drivers["OK2"] = {"name": "John", "employee_id": "E2", "status": "inactive"}
    svc.usage_repo._aggregate_queue = [[]]
    out = await svc.get_driver_performance_by_id("OK2")
    assert out["driver_id"] == "OK2"
    assert out["performance"]["trip_count"] == 0
    assert out["score"]["overall_score"] == 0

@pytest.mark.asyncio
async def test_get_driver_performance_by_id_with_stats():
    svc = make_service()
    svc.usage_repo._aggregate_queue = [[{
        "total_distance": 300.0,
        "total_fuel": 30.0,
        "trip_count": 10,
        "avg_distance": 30.0,
        "avg_fuel_per_trip": 3.0,
        "first_trip": datetime(2030,1,1,9,0,0),
        "last_trip": datetime(2030,1,10,17,0,0)
    }]]
    out = await svc.get_driver_performance_by_id("OK")
    perf = out["performance"]
    assert perf["fuel_efficiency"] == 10.0
    assert out["score"]["overall_score"] > 0
    assert perf["first_trip"].startswith("2030-01-01")

@pytest.mark.asyncio
async def test_get_dashboard_summary_all_ok_and_with_exceptions(monkeypatch):
    svc = make_service()
    out = await svc.get_dashboard_summary()
    assert "fleet_utilization" in out and "driver_performance" in out
    svc2 = make_service()
    async def bad(*a, **k): raise RuntimeError("boom")
    monkeypatch.setattr(svc2, "get_fleet_utilization", bad)
    out2 = await svc2.get_dashboard_summary()
    assert out2["fleet_utilization"] == {}

@pytest.mark.asyncio
async def test_refresh_all_cache_calls_and_swallows_errors(monkeypatch):
    svc = make_service()
    called = {"fleet":0, "usage":0, "assign":0, "driver":0}
    async def f1(use_cache): called["fleet"]+=1
    async def f2(use_cache): called["usage"]+=1; raise RuntimeError()
    async def f3(use_cache): called["assign"]+=1
    async def f4(use_cache): called["driver"]+=1
    monkeypatch.setattr(svc, "get_fleet_utilization", f1)
    monkeypatch.setattr(svc, "get_vehicle_usage_analytics", f2)
    monkeypatch.setattr(svc, "get_assignment_metrics", f3)
    monkeypatch.setattr(svc, "get_driver_performance", f4)
    await svc.refresh_all_cache()
    assert called == {"fleet":1,"usage":1,"assign":1,"driver":1}

@pytest.mark.asyncio
async def test_cleanup_expired_cache_zero_positive_and_error(monkeypatch):
    svc = make_service()
    svc.analytics_repo.cleanup_result = 0
    await svc.cleanup_expired_cache()
    svc.analytics_repo.cleanup_result = 3
    await svc.cleanup_expired_cache()
    async def boom(): raise RuntimeError()
    monkeypatch.setattr(svc.analytics_repo, "cleanup_expired", boom)
    await svc.cleanup_expired_cache()

@pytest.mark.asyncio
async def test_get_maintenance_costs_cache_and_fresh(monkeypatch):
    svc = make_service()
    svc.analytics_repo._cache["maintenance_costs"] = {"data": {"cached": 1}}
    assert await svc.get_maintenance_costs() == {"cached": 1}
    svc2 = make_service()
    out = await svc2.get_maintenance_costs(use_cache=False)
    assert out["total_costs"] == 50000
    assert ("maintenance_costs", svc2.cache_ttl["cost_analytics"]) in svc2.analytics_repo.cache_calls

@pytest.mark.asyncio
async def test_get_fuel_consumption_cache_and_fresh(monkeypatch):
    svc = make_service()
    svc.analytics_repo._cache["fuel_consumption"] = {"data": {"cached": 1}}
    assert await svc.get_fuel_consumption() == {"cached": 1}
    svc2 = make_service()
    out = await svc2.get_fuel_consumption(use_cache=False)
    assert out["total_consumption"] == 12500
    assert ("fuel_consumption", svc2.cache_ttl["cost_analytics"]) in svc2.analytics_repo.cache_calls

@pytest.mark.asyncio
async def test_get_analytics_data_routes_and_default_and_error(monkeypatch):
    svc = make_service()
    assert "generated_at" in (await svc.get_analytics_data({"type":"dashboard"}))
    assert "total_assignments" in (await svc.get_analytics_data({"type":"fleet_utilization"}))
    assert "summary" in (await svc.get_analytics_data({"type":"driver_performance"}))
    assert "total_costs" in (await svc.get_analytics_data({"type":"maintenance_costs","use_cache":False}))
    assert "total_consumption" in (await svc.get_analytics_data({"type":"fuel_consumption","use_cache":False}))
    bundle = await svc.get_analytics_data({"type":"unknown"})
    assert "dashboard" in bundle and "fuel_consumption" in bundle
    async def boom(*a, **k): raise RuntimeError("x")
    monkeypatch.setattr(svc, "get_dashboard_summary", boom)
    with pytest.raises(RuntimeError):
        await svc.get_analytics_data({"type":"dashboard"})

@pytest.mark.asyncio
async def test_handle_request_get_routes_post_and_unsupported():
    svc = make_service()
    ok = (await svc.handle_request("GET", {"endpoint":"dashboard","data":{}}))
    assert ok["status"] == "success" and "fleet_utilization" in ok["data"]
    ok2 = (await svc.handle_request("GET", {"endpoint":"fleet-utilization","data":{}}))
    assert ok2["status"] == "success" and "total_assignments" in ok2["data"]
    ok3 = (await svc.handle_request("GET", {"endpoint":"driver-performance","data":{}}))
    assert ok3["status"] == "success" and "summary" in ok3["data"]
    ok4 = (await svc.handle_request("GET", {"endpoint":"maintenance-costs","data":{}}))
    assert ok4["status"] == "success" and "total_costs" in ok4["data"]
    ok5 = (await svc.handle_request("GET", {"endpoint":"vehicle-usage","data":{}}))
    assert ok5["status"] == "success" and "vehicle_stats" in ok5["data"]
    ok6 = (await svc.handle_request("GET", {"endpoint":"fuel-consumption","data":{}}))
    assert ok6["status"] == "success" and "total_consumption" in ok6["data"]
    post = (await svc.handle_request("POST", {"endpoint":"anything","data":{"type":"dashboard"}}))
    assert post["status"] == "success" and "fleet_utilization" in post["data"]
    bad = (await svc.handle_request("PUT", {"endpoint":"x","data":{}}))
    assert bad["status"] == "error" and bad["error"] == "AnalyticsRequestError"
