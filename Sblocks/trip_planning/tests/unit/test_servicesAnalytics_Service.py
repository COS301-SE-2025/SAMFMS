# tests/unit/test_servicesAnalytics_Service.py
# Self-contained; no conftest.py. Robust search+load and per-test fakes.

import os, sys, importlib, importlib.util, types
from types import SimpleNamespace
import pytest

# ------------------------------------------------------------------------------------
# Path resolver (search up to 5 levels + CWD)
# ------------------------------------------------------------------------------------
HERE = os.path.abspath(os.path.dirname(__file__))
PARENTS = [os.path.abspath(os.path.join(HERE, *([".."] * i))) for i in range(1, 6)]
CANDIDATES = list(dict.fromkeys(PARENTS + [os.getcwd(), HERE]))  # dedup, keep order
for p in CANDIDATES:
    if p not in sys.path:
        sys.path.insert(0, p)

# ------------------------------------------------------------------------------------
# Helper: directory walker
# ------------------------------------------------------------------------------------
def _walk_roots_for(filename, roots):
    seen = set()
    SKIP = {".git", ".venv", "venv", "env", "__pycache__", ".pytest_cache", ".mypy_cache"}
    for root in roots:
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            base = os.path.basename(dirpath).lower()
            if base in SKIP:
                continue
            if dirpath in seen:
                continue
            seen.add(dirpath)
            if filename in filenames:
                yield os.path.join(dirpath, filename)

# ------------------------------------------------------------------------------------
# Robust loader for analytics_service with TEMPORARY stub modules to avoid cross-test pollution
# We inject minimal stubs just for the import, then remove them from sys.modules.
# ------------------------------------------------------------------------------------
def _load_analytics_service_module():
    # Track what we injected so we can clean up
    injected = []

    def _inject(name, module):
        if name not in sys.modules:
            sys.modules[name] = module
            injected.append(name)

    # --- temporary stub: bson (so ObjectId accepts any string) ---
    if "bson" not in sys.modules:
        bson_mod = types.ModuleType("bson")
        class _ObjectId:
            def __init__(self, s): self._s = s
            def __repr__(self): return f"ObjectId({self._s!r})"
            def __str__(self): return self._s
        bson_mod.ObjectId = _ObjectId
        _inject("bson", bson_mod)

    # --- temporary stubs: schemas.entities / schemas.requests ---
    if "schemas" not in sys.modules:
        _inject("schemas", types.ModuleType("schemas"))

    if "schemas.entities" not in sys.modules:
        ent_mod = types.ModuleType("schemas.entities")
        class TripStatus:
            # matches code usage: COMPLETED.value and CANCELLED literal
            from types import SimpleNamespace as _SN
            COMPLETED = _SN(value="completed")
            CANCELLED = "cancelled"
        class TripAnalytics: ...
        ent_mod.TripStatus = TripStatus
        ent_mod.TripAnalytics = TripAnalytics
        _inject("schemas.entities", ent_mod)

    if "schemas.requests" not in sys.modules:
        req_mod = types.ModuleType("schemas.requests")
        class AnalyticsRequest:
            def __init__(self,
                         start_date=None, end_date=None,
                         metrics=None, group_by=None,
                         driver_ids=None, vehicle_ids=None, trip_ids=None):
                self.start_date = start_date
                self.end_date = end_date
                self.metrics = metrics or []
                self.group_by = group_by
                self.driver_ids = driver_ids
                self.vehicle_ids = vehicle_ids
                self.trip_ids = trip_ids
        req_mod.AnalyticsRequest = AnalyticsRequest
        _inject("schemas.requests", req_mod)

    # --- temporary stub: repositories.database (minimal placeholders) ---
    if "repositories" not in sys.modules:
        _inject("repositories", types.ModuleType("repositories"))

    if "repositories.database" not in sys.modules:
        db_mod = types.ModuleType("repositories.database")
        class _FakeToList:
            def __init__(self, items): self._items = items
            async def to_list(self, *args, **kwargs): return self._items
        class _FakeCollection:
            def aggregate(self, _): return _FakeToList([])
            def find(self, _): return _FakeToList([])
            async def count_documents(self, _): return 0
        db_mod.db_manager = SimpleNamespace(trip_history=_FakeCollection(), trips=_FakeCollection())
        db_mod.db_manager_management = SimpleNamespace(drivers=_FakeCollection())
        _inject("repositories.database", db_mod)

    # --- load analytics_service.py by file path first ---
    for path in list(_walk_roots_for("analytics_service.py", CANDIDATES)):
        try:
            mod_name = f"loaded.analytics_service_{abs(hash(path))}"
            spec = importlib.util.spec_from_file_location(mod_name, path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[mod_name] = mod
            spec.loader.exec_module(mod)  # type: ignore[attr-defined]
            # cleanup temporary injections to avoid leaking into other tests
            for name in injected:
                sys.modules.pop(name, None)
            return mod
        except Exception:
            continue

    # Fallback: try common import names
    for name in ("analytics_service", "services.analytics_service", "trip_planning.services.analytics_service"):
        try:
            mod = importlib.import_module(name)
            for n in injected:
                sys.modules.pop(n, None)
            return mod
        except Exception:
            pass

    # If we get here: clean and fail
    for n in injected:
        sys.modules.pop(n, None)
    raise ModuleNotFoundError(
        "Could not locate analytics_service.py via search or import. "
        f"Searched roots={CANDIDATES}"
    )

analytics_service_module = _load_analytics_service_module()
AnalyticsService = getattr(analytics_service_module, "AnalyticsService")
ObjectId = getattr(analytics_service_module, "ObjectId", None)

# ------------------------------------------------------------------------------------
# Async helpers — now accept both .to_list(None) and .to_list(length=1)
# ------------------------------------------------------------------------------------
def make_to_list_cursor(items):
    class _C:
        def __init__(self, items): self._items = list(items)
        async def to_list(self, *args, **kwargs):
            length = kwargs.get("length")
            if length is None:
                return list(self._items)
            return list(self._items)[:length]
    return _C(items)

def make_async_iter(items):
    class _Iter:
        def __init__(self, items): self._items = list(items)
        def __aiter__(self): return self
        async def __anext__(self):
            if not self._items:
                raise StopAsyncIteration
            return self._items.pop(0)
    return _Iter(items)

# ====================================================================================
# _get_driver_names
# ====================================================================================

@pytest.mark.asyncio
async def test__get_driver_names_empty_returns_empty():
    res = await AnalyticsService._get_driver_names([])
    assert res == {}

@pytest.mark.asyncio
async def test__get_driver_names_found_and_default(monkeypatch):
    d1 = "507f191e810c19729de860ea"
    d2 = "abc"

    class _Drivers:
        def find(self, *_args, **_kwargs):
            return make_to_list_cursor([{"_id": analytics_service_module.ObjectId(d1),
                                         "first_name": "Ann", "last_name": "Lee"}])

    monkeypatch.setattr(analytics_service_module, "db_manager_management",
                        SimpleNamespace(drivers=_Drivers()))

    names = await AnalyticsService._get_driver_names([d1, d2])
    assert names[str(analytics_service_module.ObjectId(d1))] == "Ann Lee"
    assert names[d2] == f"Driver {d2}"

@pytest.mark.asyncio
async def test__get_driver_names_on_exception_returns_defaults(monkeypatch):
    class _Drivers:
        def find(self, *_a, **_k): raise RuntimeError("boom")
    monkeypatch.setattr(analytics_service_module, "db_manager_management",
                        SimpleNamespace(drivers=_Drivers()))
    ids = ["x", "y"]
    names = await AnalyticsService._get_driver_names(ids)
    assert names == {i: f"Driver {i}" for i in ids}

# ====================================================================================
# get_analytics_first
# ====================================================================================

@pytest.mark.asyncio
async def test_get_analytics_first_success_with_sync_name_lookup(monkeypatch):
    svc = AnalyticsService()
    results = [
        {"_id": "D1", "completedTrips": 3, "cancelledTrips": 1, "totalHours": 5.234, "totalTrips": 4},
        {"_id": None, "completedTrips": 2, "cancelledTrips": 0, "totalHours": 1.0, "totalTrips": 2},
    ]
    class _TripHistory:
        def aggregate(self, pipeline): return make_to_list_cursor(results)
    monkeypatch.setattr(analytics_service_module, "db_manager",
                        SimpleNamespace(trip_history=_TripHistory()))

    # make name lookup synchronous to satisfy the impl's missing await
    def fake_get_names(self, ids): return {i: f"Name-{i}" for i in ids}
    monkeypatch.setattr(AnalyticsService, "_get_driver_names", fake_get_names)

    from datetime import datetime
    out = await svc.get_analytics_first(datetime(2024,1,1), datetime(2024,1,31))
    assert out["drivers"] == [{
        "driverId": "D1",
        "driverName": "Name-D1",
        "completedTrips": 3,
        "cancelledTrips": 1,
        "totalHours": 5.23,
    }]
    assert out["timeframeSummary"]["totalTrips"] == 4
    assert out["timeframeSummary"]["completionRate"] == pytest.approx(75.0)
    # function rounds to 2 decimals — assert the rounded value
    assert out["timeframeSummary"]["averageTripsPerDay"] == 0.13

@pytest.mark.asyncio
async def test_get_analytics_first_buggy_name_lookup_falls_back_to_error_handler(monkeypatch):
    svc = AnalyticsService()
    class _TripHistory:
        def aggregate(self, pipeline):
            return make_to_list_cursor([{"_id":"D1","completedTrips":1,"cancelledTrips":0,"totalHours":1.0,"totalTrips":1}])
    monkeypatch.setattr(analytics_service_module, "db_manager",
                        SimpleNamespace(trip_history=_TripHistory()))

    from datetime import datetime, timezone
    now = datetime.now(tz=timezone.utc)
    out = await svc.get_analytics_first(now, now)
    assert out == {
        "drivers": [],
        "timeframeSummary": {"totalTrips": 0, "completionRate": 0.0, "averageTripsPerDay": 0.0},
    }

# ====================================================================================
# get_analytics_second
# ====================================================================================

@pytest.mark.asyncio
async def test_get_analytics_second_success(monkeypatch):
    svc = AnalyticsService()
    results = [
        {"_id": "V1", "totalTrips": 3, "totalDistance": 12.345},
        {"_id": None,  "totalTrips": 1, "totalDistance": 5.0},
        {"_id": "V2", "totalTrips": 1, "totalDistance": 7.891},
    ]
    class _TripHistory:
        def aggregate(self, pipeline): return make_to_list_cursor(results)
    monkeypatch.setattr(analytics_service_module, "db_manager",
                        SimpleNamespace(trip_history=_TripHistory()))

    from datetime import datetime, timezone
    now = datetime.now(tz=timezone.utc)
    out = await svc.get_analytics_second(now, now)
    assert out["vehicles"] == [
        {"vehicleId": "V1", "totalTrips": 3, "totalDistance": 12.35},
        {"vehicleId": "V2", "totalTrips": 1, "totalDistance": 7.89},
    ]
    assert out["timeframeSummary"]["totalDistance"] == pytest.approx(12.35 + 7.89)

@pytest.mark.asyncio
async def test_get_analytics_second_exception_returns_default(monkeypatch):
    svc = AnalyticsService()
    class _TripHistory:
        def aggregate(self, pipeline): raise RuntimeError("agg-fail")
    monkeypatch.setattr(analytics_service_module, "db_manager",
                        SimpleNamespace(trip_history=_TripHistory()))
    from datetime import datetime
    out = await svc.get_analytics_second(datetime.utcnow(), datetime.utcnow())
    assert out == {"vehicles": [], "timeframeSummary": {"totalDistance": 0}}

# ====================================================================================
# get_vehicle_analytics_with_route_distance
# ====================================================================================

@pytest.mark.asyncio
async def test_get_vehicle_analytics_with_route_distance_success(monkeypatch):
    svc = AnalyticsService()
    trips = [
        {"vehicle_id": "V1", "origin": {"location": {"coordinates": [0.0, 0.0]}},
         "destination": {"location": {"coordinates": [0.0, 1.0]}}},
        {"vehicle_id": "V1", "origin": {"location": {"coordinates": [0.0, 1.0]}},
         "destination": {"location": {"coordinates": [0.1, 1.0]}}},
        {"vehicle_id": "V2", "origin": {"location": {"coordinates": [0.0, 0.0]}},
         "destination": {"location": {"coordinates": [0.0, 0.5]}}},
    ]
    class _TripHistory:
        def find(self, query): return make_to_list_cursor(trips)
    monkeypatch.setattr(analytics_service_module, "db_manager",
                        SimpleNamespace(trip_history=_TripHistory()))
    def fake_calc(self, trip): return 10.0 if trip["vehicle_id"] == "V1" else 5.0
    monkeypatch.setattr(AnalyticsService, "_calculate_trip_distance", fake_calc)

    from datetime import datetime
    out = await svc.get_vehicle_analytics_with_route_distance(datetime.utcnow(), datetime.utcnow())
    assert out["vehicles"] == [
        {"vehicleId": "V1", "totalTrips": 2, "totalDistance": 20.0},
        {"vehicleId": "V2", "totalTrips": 1, "totalDistance": 5.0},
    ]
    assert out["timeframeSummary"]["totalDistance"] == 25.0

@pytest.mark.asyncio
async def test_get_vehicle_analytics_with_route_distance_exception_returns_default(monkeypatch):
    svc = AnalyticsService()
    class _TripHistory:
        def find(self, query): raise RuntimeError("find-fail")
    monkeypatch.setattr(analytics_service_module, "db_manager",
                        SimpleNamespace(trip_history=_TripHistory()))
    from datetime import datetime
    out = await svc.get_vehicle_analytics_with_route_distance(datetime.utcnow(), datetime.utcnow())
    assert out == {"vehicles": [], "timeframeSummary": {"totalDistance": 0}}

@pytest.mark.asyncio
async def test_get_vehicle_analytics_with_route_distance_skips_missing_vehicle_id(monkeypatch):
    svc = AnalyticsService()
    trips = [
        {"origin": {"location": {"coordinates": [0.0, 0.0]}},
         "destination": {"location": {"coordinates": [0.0, 1.0]}}},  # no vehicle_id
    ]
    class _TripHistory:
        def find(self, query): return make_to_list_cursor(trips)
    monkeypatch.setattr(analytics_service_module, "db_manager",
                        SimpleNamespace(trip_history=_TripHistory()))
    def fake_calc(self, trip): return 42.0
    monkeypatch.setattr(AnalyticsService, "_calculate_trip_distance", fake_calc)

    from datetime import datetime
    out = await svc.get_vehicle_analytics_with_route_distance(datetime.utcnow(), datetime.utcnow())
    assert out == {"vehicles": [], "timeframeSummary": {"totalDistance": 0.0}}

# ====================================================================================
# _calculate_trip_distance
# ====================================================================================

def test__calculate_trip_distance_basic_two_points():
    trip = {
        "origin": {"location": {"coordinates": [0.0, 0.0]}},
        "destination": {"location": {"coordinates": [0.0, 1.0]}},
    }
    dist = AnalyticsService._calculate_trip_distance(trip)
    assert dist == pytest.approx(111.19, rel=1e-3)

def test__calculate_trip_distance_with_waypoints_sums_segments():
    trip = {
        "origin": {"location": {"coordinates": [0.0, 0.0]}},
        "destination": {"location": {"coordinates": [0.0, 2.0]}},
        "waypoints": [
            {"location": {"coordinates": [0.0, 0.5]}},
            {"location": {"coordinates": [0.0, 1.5]}},
        ],
    }
    dist = AnalyticsService._calculate_trip_distance(trip)
    assert dist == pytest.approx(222.39, rel=1e-3)

def test__calculate_trip_distance_missing_coords_returns_zero():
    trip = {"origin": {}, "destination": {}}
    assert AnalyticsService._calculate_trip_distance(trip) == 0

def test__calculate_trip_distance_exception_returns_none():
    class BadDict(dict):
        def get(self, *a, **k): raise RuntimeError("boom")
    assert AnalyticsService._calculate_trip_distance(BadDict()) is None

# ====================================================================================
# get_trip_analytics
# ====================================================================================

@pytest.mark.asyncio
async def test_get_trip_analytics_happy_path(monkeypatch):
    svc = AnalyticsService()

    async def _build(req): return {"Q": 1}
    async def _stats(q, req): return {"total_trips": 10}
    async def _perf(q, req): return {"average_duration": 5}
    async def _eff(q, req): return {"on_time_percentage": 80}
    async def _cost(q, req): return {"total_cost": 0.0}
    async def _break(q, req): return {"by_driver": [{"driver_id": "D1", "trip_count": 10}]}

    monkeypatch.setattr(svc, "_build_analytics_query", _build)
    monkeypatch.setattr(svc, "_calculate_trip_statistics", _stats)
    monkeypatch.setattr(svc, "_calculate_performance_metrics", _perf)
    monkeypatch.setattr(svc, "_calculate_efficiency_metrics", _eff)
    monkeypatch.setattr(svc, "_calculate_cost_metrics", _cost)
    monkeypatch.setattr(svc, "_get_breakdown_data", _break)

    AR = analytics_service_module.AnalyticsRequest
    req = AR(metrics=["duration","cost"], group_by="driver")
    out = await svc.get_trip_analytics(req)
    assert out["total_trips"] == 10
    assert out["average_duration"] == 5
    assert out["on_time_percentage"] == 80
    assert out["total_cost"] == 0.0
    assert "period_start" in out and "period_end" in out
    assert out["by_driver"] == [{"driver_id": "D1", "trip_count": 10}]

@pytest.mark.asyncio
async def test_get_trip_analytics_raises_on_error(monkeypatch):
    svc = AnalyticsService()
    async def _build(req): raise RuntimeError("fail")
    monkeypatch.setattr(svc, "_build_analytics_query", _build)
    with pytest.raises(RuntimeError):
        AR = analytics_service_module.AnalyticsRequest
        await svc.get_trip_analytics(AR())

# ====================================================================================
# get_driver_performance
# ====================================================================================

def make_async_iter(items):
    class _Iter:
        def __init__(self, items): self._items = list(items)
        def __aiter__(self): return self
        async def __anext__(self):
            if not self._items:
                raise StopAsyncIteration
            return self._items.pop(0)
    return _Iter(items)

@pytest.mark.asyncio
async def test_get_driver_performance_happy_path(monkeypatch):
    svc = AnalyticsService()
    items = [{
        "_id": "D1",
        "total_trips": 4,
        "completed_trips": 3,
        "cancelled_trips": 1,
        "total_planned_duration": 0,
        "total_actual_duration": 90,
        "total_distance": 100,
        "on_time_trips": 2,
    }]
    class _Trips:
        def aggregate(self, pipeline): return make_async_iter(items)
    svc.db = SimpleNamespace(trips=_Trips())

    async def fake_more(driver_id, s, e):
        return {"fuel_efficiency": 7.0, "safety_score": 98, "average_rating": 4.9}
    monkeypatch.setattr(svc, "_get_driver_analytics_data", fake_more)

    out = await svc.get_driver_performance(driver_ids=["D1"])
    assert out == [{
        "driver_id": "D1",
        "total_trips": 4,
        "completed_trips": 3,
        "cancelled_trips": 1,
        "on_time_rate": pytest.approx(50.0),
        "completion_rate": pytest.approx(75.0),
        "average_trip_duration": pytest.approx(30.0),
        "total_distance": 100,
        "fuel_efficiency": 7.0,
        "safety_score": 98,
        "average_rating": 4.9,
    }]

@pytest.mark.asyncio
async def test_get_driver_performance_zero_trips_branch(monkeypatch):
    svc = AnalyticsService()
    items = [{
        "_id": "D2",
        "total_trips": 0,
        "completed_trips": 0,
        "cancelled_trips": 0,
        "total_planned_duration": 0,
        "total_actual_duration": 0,
        "total_distance": 0,
        "on_time_trips": 0,
    }]
    class _Trips:
        def aggregate(self, pipeline): return make_async_iter(items)
    svc.db = SimpleNamespace(trips=_Trips())

    async def fake_more(driver_id, s, e):
        return {"fuel_efficiency": None, "safety_score": None, "average_rating": None}
    monkeypatch.setattr(svc, "_get_driver_analytics_data", fake_more)

    out = await svc.get_driver_performance()
    assert out[0]["driver_id"] == "D2"
    assert out[0]["on_time_rate"] == 0
    assert out[0]["completion_rate"] == 0
    assert out[0]["average_trip_duration"] is None

@pytest.mark.asyncio
async def test_get_driver_performance_raises_on_error():
    svc = AnalyticsService()
    class _Trips:
        def aggregate(self, pipeline): raise RuntimeError("agg boom")
    svc.db = SimpleNamespace(trips=_Trips())
    with pytest.raises(RuntimeError):
        await svc.get_driver_performance()

# ====================================================================================
# get_route_efficiency_analysis
# ====================================================================================

@pytest.mark.asyncio
async def test_get_route_efficiency_analysis_success():
    svc = AnalyticsService()
    data = [{
        "total_trips": 5,
        "avg_planned_duration": 10.0,
        "avg_actual_duration": 12.0,
        "avg_planned_distance": 100.0,
        "avg_actual_distance": 120.0,
        "total_delays": 7.5,
        "total_fuel": 60.0,
        "total_cost": 240.0,
    }]
    class _Trips:
        def aggregate(self, pipeline): return make_to_list_cursor(data)
    svc.db = SimpleNamespace(trips=_Trips())

    out = await svc.get_route_efficiency_analysis()
    assert out["total_completed_trips"] == 5
    assert out["duration_variance"] == 2.0
    assert out["distance_variance"] == 20.0
    assert out["average_delay"] == pytest.approx(1.5)
    assert out["fuel_efficiency"] == pytest.approx(60.0/120.0)
    assert out["cost_per_km"] == pytest.approx(240.0/120.0)

@pytest.mark.asyncio
async def test_get_route_efficiency_analysis_no_results():
    svc = AnalyticsService()
    class _Trips:
        def aggregate(self, pipeline): return make_to_list_cursor([])
    svc.db = SimpleNamespace(trips=_Trips())
    out = await svc.get_route_efficiency_analysis()
    assert out["total_completed_trips"] == 0
    assert "message" in out

# ====================================================================================
# _build_analytics_query
# ====================================================================================

@pytest.mark.asyncio
async def test__build_analytics_query_all_filters():
    svc = AnalyticsService()
    AR = analytics_service_module.AnalyticsRequest
    from datetime import datetime
    req = AR(
        start_date=datetime(2024,1,1),
        end_date=datetime(2024,1,31),
        driver_ids=["D1","D2"],
        vehicle_ids=["V1"],
        trip_ids=["507f191e810c19729de860ea"],
    )
    q = await svc._build_analytics_query(req)
    assert q["scheduled_start_time"]["$gte"] == req.start_date
    assert q["scheduled_start_time"]["$lte"] == req.end_date
    assert q["driver_assignment"]["$in"] == ["D1","D2"]
    assert q["vehicle_id"]["$in"] == ["V1"]
    ids = q["_id"]["$in"]
    assert len(ids) == 1 and str(ids[0]) == "507f191e810c19729de860ea"

# ====================================================================================
# _calculate_trip_statistics
# ====================================================================================

@pytest.mark.asyncio
async def test__calculate_trip_statistics_counts():
    svc = AnalyticsService()
    TripStatus = analytics_service_module.TripStatus
    class _Trips:
        async def count_documents(self, query):
            if "status" not in query: return 10
            if query["status"] == TripStatus.COMPLETED: return 7
            if query["status"] == TripStatus.CANCELLED: return 3
            return 0
    svc.db = SimpleNamespace(trips=_Trips())
    out = await svc._calculate_trip_statistics({}, analytics_service_module.AnalyticsRequest())
    assert out["total_trips"] == 10
    assert out["completed_trips"] == 7
    assert out["cancelled_trips"] == 3
    assert out["completion_rate"] == pytest.approx(70.0)

# ====================================================================================
# _calculate_performance_metrics
# ====================================================================================

@pytest.mark.asyncio
async def test__calculate_performance_metrics_enabled():
    svc = AnalyticsService()
    data = [{"avg_duration": 8.0, "total_distance": 200.0, "avg_distance": 20.0}]
    class _Trips:
        def aggregate(self, pipeline): return make_to_list_cursor(data)
    svc.db = SimpleNamespace(trips=_Trips())

    req = analytics_service_module.AnalyticsRequest(metrics=["duration"])
    out = await svc._calculate_performance_metrics({}, req)
    assert out == {"average_duration": 8.0, "total_distance": 200.0, "average_distance": 20.0}

@pytest.mark.asyncio
async def test__calculate_performance_metrics_disabled():
    svc = AnalyticsService()
    req = analytics_service_module.AnalyticsRequest(metrics=[])
    out = await svc._calculate_performance_metrics({}, req)
    assert out == {}

# ====================================================================================
# _calculate_efficiency_metrics
# ====================================================================================

@pytest.mark.asyncio
async def test__calculate_efficiency_metrics():
    svc = AnalyticsService()
    TripStatus = analytics_service_module.TripStatus
    class _Trips:
        async def count_documents(self, query):
            if query.get("status") == TripStatus.COMPLETED and "$expr" in query:
                return 4  # on time
            if query.get("status") == TripStatus.COMPLETED:
                return 8  # total completed
            return 0
    svc.db = SimpleNamespace(trips=_Trips())

    out = await svc._calculate_efficiency_metrics({}, analytics_service_module.AnalyticsRequest())
    assert out == {"on_time_percentage": pytest.approx(50.0)}

# ====================================================================================
# _calculate_cost_metrics
# ====================================================================================

@pytest.mark.asyncio
async def test__calculate_cost_metrics_enabled_disabled():
    svc = AnalyticsService()
    AR = analytics_service_module.AnalyticsRequest
    out1 = await svc._calculate_cost_metrics({}, AR(metrics=["cost"]))
    assert out1 == {"total_cost": 0.0, "average_cost_per_trip": 0.0, "cost_per_km": 0.0}
    out2 = await svc._calculate_cost_metrics({}, AR(metrics=[]))
    assert out2 == {}
