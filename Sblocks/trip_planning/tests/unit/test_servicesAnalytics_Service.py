# tests/unit/test_servicesAnalytics_Service.py
# Self-contained; no conftest.py required. Designed not to interfere with other tests.

import os, sys, types, importlib, importlib.util
from types import SimpleNamespace
from unittest.mock import AsyncMock
import pytest
from datetime import datetime, timezone

# -----------------------------------------------------------------------------
# Path resolver
# -----------------------------------------------------------------------------
HERE = os.path.abspath(os.path.dirname(__file__))
CANDIDATES = [
    os.path.abspath(os.path.join(HERE, "..", "..")),  # project-ish root
    os.path.abspath(os.path.join(HERE, "..")),
    os.getcwd(),
]
for p in CANDIDATES:
    if p not in sys.path:
        sys.path.insert(0, p)

# -----------------------------------------------------------------------------
# Minimal stubs for deps (ONLY if not already present)
# -----------------------------------------------------------------------------
if "bson" not in sys.modules:
    bson_mod = types.ModuleType("bson")
    class _ObjectId:
        def __init__(self, s): self.s = s
        def __repr__(self): return f"OID({self.s})"
    def ObjectId(x): return _ObjectId(x)
    bson_mod.ObjectId = ObjectId
    sys.modules["bson"] = bson_mod

if "schemas" not in sys.modules:
    sys.modules["schemas"] = types.ModuleType("schemas")

if "schemas.entities" not in sys.modules:
    schemas_entities = types.ModuleType("schemas.entities")
    class _Status:
        def __init__(self, val): self.value = val
        def __str__(self): return self.value
    class TripStatus:
        COMPLETED = _Status("completed")
        CANCELLED = _Status("cancelled")
    class TripAnalytics: ...
    schemas_entities.TripStatus = TripStatus
    schemas_entities.TripAnalytics = TripAnalytics
    sys.modules["schemas.entities"] = schemas_entities

if "schemas.requests" not in sys.modules:
    schemas_requests = types.ModuleType("schemas.requests")
    class AnalyticsRequest:
        def __init__(
            self,
            start_date=None, end_date=None,
            driver_ids=None, vehicle_ids=None, trip_ids=None,
            metrics=None, group_by=None
        ):
            self.start_date = start_date
            self.end_date = end_date
            self.driver_ids = driver_ids or []
            self.vehicle_ids = vehicle_ids or []
            self.trip_ids = trip_ids or []
            self.metrics = metrics or []
            self.group_by = group_by
    schemas_requests.AnalyticsRequest = AnalyticsRequest
    sys.modules["schemas.requests"] = schemas_requests

# lightweight repositories.database so imports in module can resolve if needed
if "repositories" not in sys.modules:
    sys.modules["repositories"] = types.ModuleType("repositories")
if "repositories.database" not in sys.modules:
    repos_db = types.ModuleType("repositories.database")
    repos_db.db_manager = SimpleNamespace()  # we will override on the loaded module, not globally
    repos_db.db_manager_management = SimpleNamespace()
    sys.modules["repositories.database"] = repos_db

# -----------------------------------------------------------------------------
# Robust loader for analytics_service WITHOUT importing real 'services' package
# -----------------------------------------------------------------------------
def _walk_roots_for(filename, roots):
    seen = set()
    for root in roots:
        if not os.path.isdir(root): 
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            base = os.path.basename(dirpath).lower()
            if base in {".git", ".venv", "venv", "env", "__pycache__", ".pytest_cache"}:
                continue
            if dirpath in seen:
                continue
            seen.add(dirpath)
            if filename in filenames:
                yield os.path.join(dirpath, filename)

def _load_analytics_service_module():
    # Prefer direct file loading to avoid executing real packages' __init__
    for path in _walk_roots_for("analytics_service.py", CANDIDATES):
        try:
            pkg_dir = os.path.dirname(path)
            pkg_name = os.path.basename(pkg_dir)
            if pkg_name == "services" and "services" not in sys.modules:
                services_pkg = types.ModuleType("services")
                services_pkg.__path__ = [pkg_dir]  # mark as package
                sys.modules["services"] = services_pkg
                mod_name = "services.analytics_service"
            else:
                mod_name = "loaded.analytics_service"
            spec = importlib.util.spec_from_file_location(mod_name, path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[mod_name] = mod
            spec.loader.exec_module(mod)  # type: ignore[attr-defined]
            return mod
        except Exception:
            continue
    # Fallback: simple import if resolvable
    return importlib.import_module("analytics_service")

analytics_service_module = _load_analytics_service_module()
AnalyticsService = getattr(analytics_service_module, "AnalyticsService")

# -----------------------------------------------------------------------------
# DB stubs + injection helpers
# -----------------------------------------------------------------------------
class _AsyncCursor:
    """Cursor supporting both to_list and async iteration."""
    def __init__(self, items):
        self._items = list(items)
        self._idx = 0
    async def to_list(self, _):
        return list(self._items)
    def __aiter__(self):
        self._idx = 0
        return self
    async def __anext__(self):
        if self._idx >= len(self._items):
            raise StopAsyncIteration
        item = self._items[self._idx]
        self._idx += 1
        return item

class _Coll:
    """Collection stub with overrideable async-like methods."""
    def __init__(self):
        # defaults return empty/zero; tests override as needed
        self._aggregate_impl = lambda pipeline: _AsyncCursor([])
        self._find_impl = lambda query: _AsyncCursor([])
        self._count_docs_impl = AsyncMock(return_value=0)
    def aggregate(self, pipeline):
        return self._aggregate_impl(pipeline)
    def find(self, query):
        return self._find_impl(query)
    async def count_documents(self, *args, **kwargs):
        return await self._count_docs_impl(*args, **kwargs)

def _wire_db_handles(svc, trip_history: _Coll, trips: _Coll, drivers: _Coll):
    """Inject stubs onto service instance and the loaded module, covering
    all common attribute names. This avoids touching global packages and
    keeps state per-test.
    """
    core_container = SimpleNamespace(trip_history=trip_history, trips=trips)
    mgmt_container = SimpleNamespace(drivers=drivers)

    # Service instance attributes (cover many common names)
    for name in ("db", "db_manager", "dbm", "database", "mongo"):
        setattr(svc, name, core_container)
    for name in ("db_management", "db_manager_management", "management_db"):
        setattr(svc, name, mgmt_container)
    # Rare but safe: also directly set attributes in case the code uses self.trip_history
    setattr(svc, "trip_history", trip_history)
    setattr(svc, "trips", trips)
    setattr(svc, "drivers", drivers)

    # Patch module-level handles the file might have bound at import time.
    # We intentionally set multiple names; harmless if unused.
    for name in ("db", "db_manager", "dbm", "database", "mongo"):
        setattr(analytics_service_module, name, core_container)
    for name in ("db_management", "db_manager_management", "management_db"):
        setattr(analytics_service_module, name, mgmt_container)

def _fresh_service_with_injected_db():
    svc = AnalyticsService()
    trip_history = _Coll()
    trips = _Coll()
    drivers = _Coll()
    _wire_db_handles(svc, trip_history, trips, drivers)
    return svc, SimpleNamespace(trip_history=trip_history, trips=trips, drivers=drivers)

# =============================================================================
# get_analytics_first
# =============================================================================

@pytest.mark.asyncio
async def test_get_analytics_first_happy_path_monkeypatch_names(monkeypatch):
    svc, stubs = _fresh_service_with_injected_db()

    # Simulate driver rollup results; include one None _id to ensure skip
    stubs.trip_history._aggregate_impl = lambda pipeline: _AsyncCursor([
        {"_id": "D1", "completedTrips": 3, "cancelledTrips": 1, "totalHours": 5.234, "totalTrips": 4},
        {"_id": "D2", "completedTrips": 0, "cancelledTrips": 2, "totalHours": 0, "totalTrips": 2},
        {"_id": None, "completedTrips": 1, "cancelledTrips": 0, "totalHours": 1.0, "totalTrips": 1},
    ])

    # Avoid await/async mismatch by making _get_driver_names a safe sync func
    monkeypatch.setattr(AnalyticsService, "_get_driver_names",
                        lambda self, ids: {"D1": "Alice Able"},
                        raising=False)

    out = await svc.get_analytics_first(datetime(2025, 9, 1), datetime(2025, 9, 3))

    assert out["drivers"] == [
        {"driverId": "D1", "driverName": "Alice Able", "completedTrips": 3, "cancelledTrips": 1, "totalHours": 5.23},
        {"driverId": "D2", "driverName": "Driver D2", "completedTrips": 0, "cancelledTrips": 2, "totalHours": 0.0},
    ]
    tf = out["timeframeSummary"]
    assert tf["totalTrips"] == 6
    assert tf["completionRate"] == 50.0
    assert tf["averageTripsPerDay"] == 2.0

@pytest.mark.asyncio
async def test_get_analytics_first_bug_branch_returns_default(monkeypatch):
    svc, stubs = _fresh_service_with_injected_db()
    stubs.trip_history._aggregate_impl = lambda pipeline: _AsyncCursor(
        [{"_id": "D1", "completedTrips": 1, "cancelledTrips": 0, "totalHours": 1.0, "totalTrips": 1}]
    )
    # Force an exception in name resolution to hit the safe-default path
    def _boom(self, ids): raise RuntimeError("name lookup failed")
    monkeypatch.setattr(AnalyticsService, "_get_driver_names", _boom, raising=False)
    out = await svc.get_analytics_first(datetime(2025, 9, 1), datetime(2025, 9, 1))
    assert out == {
        "drivers": [],
        "timeframeSummary": {"totalTrips": 0, "completionRate": 0.0, "averageTripsPerDay": 0.0}
    }

@pytest.mark.asyncio
async def test_get_analytics_first_accepts_naive_datetimes():
    svc, stubs = _fresh_service_with_injected_db()
    stubs.trip_history._aggregate_impl = lambda pipeline: _AsyncCursor([])
    out = await svc.get_analytics_first(datetime(2025, 9, 10), datetime(2025, 9, 11))
    assert out["drivers"] == []
    assert set(out["timeframeSummary"].keys()) == {"totalTrips", "completionRate", "averageTripsPerDay"}

# =============================================================================
# get_analytics_second
# =============================================================================

@pytest.mark.asyncio
async def test_get_analytics_second_happy_path():
    svc, stubs = _fresh_service_with_injected_db()
    stubs.trip_history._aggregate_impl = lambda pipeline: _AsyncCursor([
        {"_id": "V1", "totalTrips": 2, "totalDistance": 100.2345},
        {"_id": "V2", "totalTrips": 1, "totalDistance": 5.6789},
    ])
    out = await svc.get_analytics_second(datetime(2025, 9, 1), datetime(2025, 9, 2))
    assert out["vehicles"] == [
        {"vehicleId": "V1", "totalTrips": 2, "totalDistance": 100.23},
        {"vehicleId": "V2", "totalTrips": 1, "totalDistance": 5.68},
    ]
    assert out["timeframeSummary"]["totalDistance"] == round(100.23 + 5.68, 2)

@pytest.mark.asyncio
async def test_get_analytics_second_exception_returns_default():
    svc, stubs = _fresh_service_with_injected_db()
    def _boom(_): raise RuntimeError("db down")
    stubs.trip_history._aggregate_impl = _boom
    out = await svc.get_analytics_second(datetime(2025, 9, 1), datetime(2025, 9, 2))
    assert out == {"vehicles": [], "timeframeSummary": {"totalDistance": 0}}

# =============================================================================
# get_vehicle_analytics_with_route_distance
# =============================================================================

@pytest.mark.asyncio
async def test_vehicle_analytics_with_route_distance_error_branch(monkeypatch):
    svc, stubs = _fresh_service_with_injected_db()
    stubs.trip_history._find_impl = lambda q: _AsyncCursor([{"vehicle_id": "V1", "origin": {}, "destination": {}}])
    def _boom(self, trip): raise RuntimeError("distance calc fail")
    monkeypatch.setattr(AnalyticsService, "_calculate_trip_distance", _boom, raising=False)
    out = await svc.get_vehicle_analytics_with_route_distance(datetime(2025, 9, 1), datetime(2025, 9, 2))
    assert out == {"vehicles": [], "timeframeSummary": {"totalDistance": 0}}

@pytest.mark.asyncio
async def test_vehicle_analytics_with_route_distance_happy_path(monkeypatch):
    svc, stubs = _fresh_service_with_injected_db()
    stubs.trip_history._find_impl = lambda q: _AsyncCursor(
        [{"vehicle_id": "A"}, {"vehicle_id": "A"}, {"vehicle_id": "B"}]
    )
    monkeypatch.setattr(AnalyticsService, "_calculate_trip_distance",
                        lambda self, trip: 10.5 if trip["vehicle_id"] == "A" else 5.0,
                        raising=False)
    out = await svc.get_vehicle_analytics_with_route_distance(datetime(2025, 9, 1), datetime(2025, 9, 2))
    assert out["vehicles"] == [
        {"vehicleId": "A", "totalTrips": 2, "totalDistance": 21.0},
        {"vehicleId": "B", "totalTrips": 1, "totalDistance": 5.0},
    ]
    assert out["timeframeSummary"]["totalDistance"] == 26.0

# =============================================================================
# _calculate_trip_distance (pure-ish)
# =============================================================================

def test_calculate_trip_distance_missing_coords_returns_zero():
    d = AnalyticsService._calculate_trip_distance({"origin": {}, "destination": {}})
    assert d == 0

def test_calculate_trip_distance_direct_leg_positive():
    trip = {
        "origin": {"location": {"coordinates": [0.0, 0.0]}},
        "destination": {"location": {"coordinates": [1.0, 0.0]}},
    }
    d = AnalyticsService._calculate_trip_distance(trip)
    assert 100 < d < 120  # ~111.32 km

def test_calculate_trip_distance_with_waypoints_sums_legs():
    trip = {
        "origin": {"location": {"coordinates": [0.0, 0.0]}},
        "destination": {"location": {"coordinates": [2.0, 0.0]}},
        "waypoints": [{"location": {"coordinates": [1.0, 0.0]}}],
    }
    d = AnalyticsService._calculate_trip_distance(trip)
    assert 200 < d < 230

def test_calculate_trip_distance_exception_returns_none():
    trip = {
        "origin": {"location": {"coordinates": [0.0, 0.0]}},
        "destination": {"location": {"coordinates": [1.0, 0.0]}},
        "waypoints": [{"location": {"coordinates": ["bad", "data"]}}],
    }
    d = AnalyticsService._calculate_trip_distance(trip)
    assert d is None

# =============================================================================
# get_trip_analytics (orchestrator)
# =============================================================================

@pytest.mark.asyncio
async def test_get_trip_analytics_success_merges_all(monkeypatch):
    svc, _ = _fresh_service_with_injected_db()
    monkeypatch.setattr(svc, "_build_analytics_query", AsyncMock(return_value={"q": 1}))
    monkeypatch.setattr(svc, "_calculate_trip_statistics", AsyncMock(return_value={"total_trips": 10}))
    monkeypatch.setattr(svc, "_calculate_performance_metrics", AsyncMock(return_value={"average_duration": 5}))
    monkeypatch.setattr(svc, "_calculate_efficiency_metrics", AsyncMock(return_value={"on_time_percentage": 80}))
    monkeypatch.setattr(svc, "_calculate_cost_metrics", AsyncMock(return_value={"total_cost": 0.0, "cost_per_km": 0.0}))
    monkeypatch.setattr(svc, "_get_breakdown_data", AsyncMock(return_value={"by_driver": [{"driver_id": "D1"}]}))

    req = sys.modules["schemas.requests"].AnalyticsRequest(
        start_date=datetime(2025, 9, 1), end_date=datetime(2025, 9, 2),
        metrics=["duration", "cost"], group_by="driver"
    )
    out = await svc.get_trip_analytics(req)
    assert out["period_start"] == req.start_date
    assert out["period_end"] == req.end_date
    assert out["total_trips"] == 10
    assert out["average_duration"] == 5
    assert out["on_time_percentage"] == 80
    assert out["total_cost"] == 0.0
    assert out["by_driver"] == [{"driver_id": "D1"}]

@pytest.mark.asyncio
async def test_get_trip_analytics_raises_on_error(monkeypatch):
    svc, _ = _fresh_service_with_injected_db()
    monkeypatch.setattr(svc, "_build_analytics_query", AsyncMock(side_effect=RuntimeError("boom")))
    req = sys.modules["schemas.requests"].AnalyticsRequest()
    with pytest.raises(RuntimeError):
        await svc.get_trip_analytics(req)

# =============================================================================
# get_driver_performance
# =============================================================================

@pytest.mark.asyncio
async def test_get_driver_performance_typical(monkeypatch):
    svc, stubs = _fresh_service_with_injected_db()
    stubs.trips._aggregate_impl = lambda pipeline: _AsyncCursor([{
        "_id": "D1",
        "total_trips": 4,
        "completed_trips": 3,
        "cancelled_trips": 1,
        "total_planned_duration": 100,
        "total_actual_duration": 90,
        "total_distance": 123.4,
        "on_time_trips": 2,
    }])
    monkeypatch.setattr(svc, "_get_driver_analytics_data", AsyncMock(return_value={"fuel_efficiency": 6.5}))

    out = await svc.get_driver_performance(driver_ids=["D1"],
                                           start_date=datetime(2025,9,1),
                                           end_date=datetime(2025,9,2))
    assert len(out) == 1 and out[0]["driver_id"] == "D1"
    assert out[0]["total_trips"] == 4
    assert out[0]["completed_trips"] == 3
    assert out[0]["cancelled_trips"] == 1
    assert out[0]["on_time_rate"] == 50.0
    assert out[0]["completion_rate"] == 75.0
    assert out[0]["average_trip_duration"] == 90/3
    assert out[0]["total_distance"] == 123.4
    assert out[0]["fuel_efficiency"] == 6.5

@pytest.mark.asyncio
async def test_get_driver_performance_zero_totals(monkeypatch):
    svc, stubs = _fresh_service_with_injected_db()
    stubs.trips._aggregate_impl = lambda pipeline: _AsyncCursor([{
        "_id": "D2",
        "total_trips": 0,
        "completed_trips": 0,
        "cancelled_trips": 0,
        "total_planned_duration": 0,
        "total_actual_duration": 0,
        "total_distance": 0,
        "on_time_trips": 0,
    }])
    monkeypatch.setattr(svc, "_get_driver_analytics_data", AsyncMock(return_value={}))
    out = await svc.get_driver_performance()
    assert out[0]["on_time_rate"] == 0
    assert out[0]["completion_rate"] == 0
    assert out[0]["average_trip_duration"] is None

@pytest.mark.asyncio
async def test_get_driver_performance_raises_on_error():
    svc, stubs = _fresh_service_with_injected_db()
    def _boom(_): raise RuntimeError("agg fail")
    stubs.trips._aggregate_impl = _boom
    with pytest.raises(RuntimeError):
        await svc.get_driver_performance()

# =============================================================================
# get_route_efficiency_analysis
# =============================================================================

@pytest.mark.asyncio
async def test_get_route_efficiency_analysis_with_data():
    svc, stubs = _fresh_service_with_injected_db()
    class _Agg:
        async def to_list(self, length=1):
            return [{
                "total_trips": 5,
                "avg_planned_duration": 100,
                "avg_actual_duration": 120,
                "avg_planned_distance": 200,
                "avg_actual_distance": 250,
                "total_delays": 10,
                "total_fuel": 500,
                "total_cost": 1000,
            }]
    stubs.trips._aggregate_impl = lambda pipeline: _Agg()
    out = await svc.get_route_efficiency_analysis()
    assert out["total_completed_trips"] == 5
    assert out["duration_variance"] == 20
    assert out["distance_variance"] == 50
    assert out["average_delay"] == 10/5
    assert out["fuel_efficiency"] == 500/250
    assert out["cost_per_km"] == 1000/250

@pytest.mark.asyncio
async def test_get_route_efficiency_analysis_no_results():
    svc, stubs = _fresh_service_with_injected_db()
    class _Agg:
        async def to_list(self, length=1): return []
    stubs.trips._aggregate_impl = lambda pipeline: _Agg()
    out = await svc.get_route_efficiency_analysis()
    assert out["total_completed_trips"] == 0
    assert "message" in out

@pytest.mark.asyncio
async def test_get_route_efficiency_analysis_raises():
    svc, stubs = _fresh_service_with_injected_db()
    def _boom(_): raise RuntimeError("agg fail")
    stubs.trips._aggregate_impl = _boom
    with pytest.raises(RuntimeError):
        await svc.get_route_efficiency_analysis()

# =============================================================================
# _build_analytics_query
# =============================================================================

@pytest.mark.asyncio
async def test_build_analytics_query_all_filters():
    svc, _ = _fresh_service_with_injected_db()
    req = sys.modules["schemas.requests"].AnalyticsRequest(
        start_date=datetime(2025, 9, 1), end_date=datetime(2025, 9, 2),
        driver_ids=["D1"], vehicle_ids=["V1"], trip_ids=["T1","T2"]
    )
    q = await svc._build_analytics_query(req)
    assert "scheduled_start_time" in q
    assert q.get("driver_assignment") == {"$in": ["D1"]}
    assert q.get("vehicle_id") == {"$in": ["V1"]}
    assert "_id" in q and "$in" in q["_id"]
    assert repr(q["_id"]["$in"][0]).startswith("OID(")

# =============================================================================
# _calculate_trip_statistics / _calculate_performance_metrics / _calculate_efficiency_metrics / _calculate_cost_metrics
# =============================================================================

@pytest.mark.asyncio
async def test_calculate_trip_statistics_and_efficiency_and_cost_and_performance():
    svc, stubs = _fresh_service_with_injected_db()
    # stats + efficiency use count_documents in sequence:
    # total_trips, completed_trips, cancelled_trips, on_time_trips, completed_again
    stubs.trips._count_docs_impl = AsyncMock(side_effect=[10, 7, 3, 5, 7])

    class _Agg:
        async def to_list(self, length=1): return [{"avg_duration": 12, "total_distance": 300, "avg_distance": 60}]
    stubs.trips._aggregate_impl = lambda pipeline: _Agg()

    req = sys.modules["schemas.requests"].AnalyticsRequest(metrics=["duration", "cost"])
    stats = await svc._calculate_trip_statistics({}, req)
    assert stats == {
        "total_trips": 10,
        "completed_trips": 7,
        "cancelled_trips": 3,
        "completion_rate": 70.0
    }

    perf = await svc._calculate_performance_metrics({}, req)
    assert perf == {"average_duration": 12, "total_distance": 300, "average_distance": 60}

    eff = await svc._calculate_efficiency_metrics({}, req)
    assert eff == {"on_time_percentage": pytest.approx(5/7*100)}

    cost = await svc._calculate_cost_metrics({}, req)
    assert cost == {"total_cost": 0.0, "average_cost_per_trip": 0.0, "cost_per_km": 0.0}

@pytest.mark.asyncio
async def test_performance_skipped_if_metric_not_requested():
    svc, _ = _fresh_service_with_injected_db()
    req = sys.modules["schemas.requests"].AnalyticsRequest(metrics=["somethingelse"])
    perf = await svc._calculate_performance_metrics({}, req)
    assert perf == {}

# =============================================================================
# _get_breakdown_data + driver/vehicle breakdowns
# =============================================================================

@pytest.mark.asyncio
async def test_get_breakdown_data_driver_branch(monkeypatch):
    svc, _ = _fresh_service_with_injected_db()
    monkeypatch.setattr(svc, "_get_driver_breakdown", AsyncMock(return_value=[{"driver_id":"D1"}]))
    out = await svc._get_breakdown_data({}, sys.modules["schemas.requests"].AnalyticsRequest(group_by="driver"))
    assert out == {"by_driver": [{"driver_id":"D1"}]}

@pytest.mark.asyncio
async def test_get_breakdown_data_vehicle_branch(monkeypatch):
    svc, _ = _fresh_service_with_injected_db()
    monkeypatch.setattr(svc, "_get_vehicle_breakdown", AsyncMock(return_value=[{"vehicle_id":"V1"}]))
    out = await svc._get_breakdown_data({}, sys.modules["schemas.requests"].AnalyticsRequest(group_by="vehicle"))
    assert out == {"by_vehicle": [{"vehicle_id":"V1"}]}

@pytest.mark.asyncio
async def test_get_breakdown_data_period_branch(monkeypatch):
    svc, _ = _fresh_service_with_injected_db()
    monkeypatch.setattr(svc, "_get_period_breakdown", AsyncMock(return_value=[{"period":"2025-09-01","trips":2}]))
    out = await svc._get_breakdown_data({}, sys.modules["schemas.requests"].AnalyticsRequest(group_by="week"))
    assert out == {"by_period": [{"period":"2025-09-01","trips":2}]}

@pytest.mark.asyncio
async def test_get_driver_breakdown_maps_results():
    svc, stubs = _fresh_service_with_injected_db()
    stubs.trips._aggregate_impl = lambda pipeline: _AsyncCursor([
        {"_id": "D1", "trip_count": 3, "completed_trips": 2},
        {"_id": "D2", "trip_count": 1, "completed_trips": 0},
    ])
    out = await svc._get_driver_breakdown({})
    assert out == [
        {"driver_id":"D1","trip_count":3,"completed_trips":2},
        {"driver_id":"D2","trip_count":1,"completed_trips":0},
    ]

@pytest.mark.asyncio
async def test_get_vehicle_breakdown_maps_results():
    svc, stubs = _fresh_service_with_injected_db()
    stubs.trips._aggregate_impl = lambda pipeline: _AsyncCursor([
        {"_id": "V1", "trip_count": 2, "total_distance": 50},
    ])
    out = await svc._get_vehicle_breakdown({})
    assert out == [{"vehicle_id":"V1","trip_count":2,"total_distance":50}]

@pytest.mark.asyncio
async def test_get_period_breakdown_placeholder():
    svc, _ = _fresh_service_with_injected_db()
    out = await svc._get_period_breakdown({}, "month")
    assert out == []

# =============================================================================
# get_trip_history_stats
# =============================================================================

@pytest.mark.asyncio
async def test_get_trip_history_stats_with_days_and_results():
    svc, stubs = _fresh_service_with_injected_db()
    class _Agg:
        async def to_list(self, _):
            return [{
                "total_trips": 4,
                "total_duration_hours": 10.555,
                "total_distance": 123.456,
                "avg_duration_hours": 2.638,
                "avg_distance": 30.864,
                "max_duration": 3.999,
                "min_duration": 0.1,
                "max_distance": 66.666,
                "min_distance": 0.001,
            }]
    stubs.trip_history._aggregate_impl = lambda pipeline: _Agg()
    out = await svc.get_trip_history_stats(days=7)
    assert out["total_trips"] == 4
    assert out["total_duration_hours"] == 10.55
    assert out["total_distance_km"] == 123.46
    assert out["average_duration_hours"] == 2.64
    assert out["average_distance_km"] == 30.86
    assert out["max_duration_hours"] == 4.0
    assert out["min_duration_hours"] == 0.1
    assert out["max_distance_km"] == 66.67
    assert out["min_distance_km"] == 0.0
    assert out["time_period"].startswith("Last 7 days")

@pytest.mark.asyncio
async def test_get_trip_history_stats_all_time_no_results():
    svc, stubs = _fresh_service_with_injected_db()
    class _Agg:
        async def to_list(self, _): return []
    stubs.trip_history._aggregate_impl = lambda pipeline: _Agg()
    out = await svc.get_trip_history_stats()
    assert out["time_period"] == "All time"
    assert out["total_trips"] == 0
    assert out["average_distance_km"] == 0

@pytest.mark.asyncio
async def test_get_trip_history_stats_raises_on_error():
    svc, stubs = _fresh_service_with_injected_db()
    def _boom(_): raise RuntimeError("agg fail")
    stubs.trip_history._aggregate_impl = _boom
    with pytest.raises(RuntimeError):
        await svc.get_trip_history_stats()
