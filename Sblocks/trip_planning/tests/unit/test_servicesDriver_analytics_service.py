import sys, os, types, importlib, pytest
from datetime import datetime, timezone

HERE = os.path.abspath(os.path.dirname(__file__))

def _candidate_paths():
    return [
        os.path.abspath(os.path.join(HERE, "..", "..", "services", "driver_analytics_service.py")),
        os.path.abspath(os.path.join(os.getcwd(), "Sblocks", "maintenance", "services", "driver_analytics_service.py")),
        os.path.abspath(os.path.join(os.getcwd(), "services", "driver_analytics_service.py")),
        os.path.abspath(os.path.join(os.getcwd(), "driver_analytics_service.py")),
    ]

def _ensure_pkg(name: str):
    if name not in sys.modules:
        pkg = types.ModuleType(name)
        pkg.__path__ = []  
        sys.modules[name] = pkg
    elif not hasattr(sys.modules[name], "__path__"):
        sys.modules[name].__path__ = []

def _snap(names):
    return {n: sys.modules.get(n) for n in names}

def _restore(snap):
    for name, mod in snap.items():
        if mod is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = mod
    if "repositories" in snap and snap["repositories"] is not None:
        if "repositories.database" in snap:
            setattr(sys.modules["repositories"], "database", snap["repositories.database"])
    if "schemas" in snap and snap["schemas"] is not None:
        if "schemas.entities" in snap:
            setattr(sys.modules["schemas"], "entities", snap["schemas.entities"])
        if "schemas.requests" in snap:
            setattr(sys.modules["schemas"], "requests", snap["schemas.requests"])


@pytest.fixture(scope="module")
def svc_env():
    names = [
        "repositories",
        "repositories.database",
        "schemas",
        "schemas.entities",
        "schemas.requests",
        "bson",
        "services.driver_analytics_service",
    ]
    snap = _snap(names)

    if snap["bson"] is None:
        bson_mod = types.ModuleType("bson")
        class ObjectId:
            @classmethod
            def is_valid(cls, s):
                return isinstance(s, str) and len(s) == 24 and all(c in "0123456789abcdefABCDEF" for c in s)
            def __init__(self, s):
                if not ObjectId.is_valid(s):
                    raise ValueError("invalid ObjectId")
                self._s = s.lower()
            def __str__(self): return self._s
            def __repr__(self): return f"ObjectId('{self._s}')"
            def __eq__(self, other): return str(self) == str(other)
            def __hash__(self): return hash(self._s)
        bson_mod.ObjectId = ObjectId
        sys.modules["bson"] = bson_mod

    _ensure_pkg("repositories")
    repodb = types.ModuleType("repositories.database")

    class _FakeCursor:
        def __init__(self, data=None, raise_exc=None):
            self._data = list(data or [])
            self._raise = raise_exc
        async def to_list(self, *_):
            if self._raise:
                raise self._raise
            return list(self._data)

    class _TripHistoryCollection:
        def __init__(self):
            self.total_count = 0
            self.completed_count = 0
            self.cancelled_count = 0
            self.raise_on_status = None
            self.find_trips = []
            self.find_raise = None
            self.aggregate_result = []
            self.aggregate_raise = None
            self.last_count_filter = None
            self.last_find_filter = None
            self.last_aggregate_pipeline = None
        async def count_documents(self, flt):
            self.last_count_filter = flt
            status = flt.get("status")
            if self.raise_on_status and (self.raise_on_status == status or self.raise_on_status == "any"):
                raise RuntimeError("count fail")
            if status == "completed":
                return self.completed_count
            if status == "cancelled":
                return self.cancelled_count
            return self.total_count
        def find(self, flt, projection=None):
            self.last_find_filter = flt
            return _FakeCursor(self.find_trips, self.find_raise)
        def aggregate(self, pipeline):
            self.last_aggregate_pipeline = pipeline
            return _FakeCursor(self.aggregate_result, self.aggregate_raise)

    class _DriversCollection:
        def __init__(self):
            self.drivers_data = []
            self.raise_exc = None
            self.last_find_filter = None
        def find(self, flt, projection=None):
            self.last_find_filter = flt
            data = list(self.drivers_data)
            try:
                in_list = flt.get("_id", {}).get("$in")
                if in_list is not None:
                    data = [d for d in data if d.get("_id") in set(in_list)]
            except Exception:
                pass
            if isinstance(projection, dict) and projection:
                keep = {k for k, v in projection.items() if v} | {"_id"}
                projected = []
                for d in data:
                    projected.append({k: v for k, v in d.items() if k in keep})
                data = projected
            return _FakeCursor(data, self.raise_exc)

    class _DBTrips:
        def __init__(self):
            self.trip_history = _TripHistoryCollection()

    class _DBMgmt:
        def __init__(self):
            self.drivers = _DriversCollection()

    repodb.db_manager = _DBTrips()
    repodb.db_manager_management = _DBMgmt()
    sys.modules["repositories.database"] = repodb
    sys.modules["repositories"].database = repodb

    _ensure_pkg("schemas")
    se = types.ModuleType("schemas.entities")
    class TripAnalytics: pass
    class TripStatus: pass
    se.TripAnalytics = TripAnalytics
    se.TripStatus = TripStatus
    sys.modules["schemas.entities"] = se
    sys.modules["schemas"].entities = se

    sr = types.ModuleType("schemas.requests")
    class AnalyticsRequest: pass
    sr.AnalyticsRequest = AnalyticsRequest
    sys.modules["schemas.requests"] = sr
    sys.modules["schemas"].requests = sr

    import importlib.util
    for path in _candidate_paths():
        if os.path.exists(path):
            if "services.driver_analytics_service" in sys.modules:
                del sys.modules["services.driver_analytics_service"]
            spec = importlib.util.spec_from_file_location("services.driver_analytics_service", path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules["services.driver_analytics_service"] = mod
            spec.loader.exec_module(mod)
            break
    else:
        _restore(snap)
        raise ImportError("driver_analytics_service.py not found")

    env = {
        "DriverAnalyticsService": sys.modules["services.driver_analytics_service"].DriverAnalyticsService,
        "repodb": repodb,
        "ObjectId": sys.modules["bson"].ObjectId,
        "_DriversCollection": _DriversCollection,
    }

    try:
        yield env
    finally:
        _restore(snap)


def _make_service(env):
    s = env["DriverAnalyticsService"]()
    assert s.db is env["repodb"].db_manager and s.db_management is env["repodb"].db_manager_management
    return s

# ================================== TESTS ==================================

@pytest.mark.asyncio
async def test_get_driver_names_empty_returns_empty(svc_env):
    s = _make_service(svc_env)
    assert await s._get_driver_names([]) == {}

@pytest.mark.asyncio
async def test_get_driver_names_mixed_ids_found_and_defaults(svc_env):
    s = _make_service(svc_env)
    OID = svc_env["ObjectId"]
    valid_hex = "507f1f77bcf86cd799439011"
    invalid_hexlen = "Z"*24
    short_id = "drv-1"
    drv = s.db_management.drivers
    drv.drivers_data = [
        {"_id": OID(valid_hex), "first_name":"Driver", "last_name":"507f1f77bcf86cd799439011"},
    ]
    out = await s._get_driver_names([valid_hex, invalid_hexlen, short_id])
    assert out[valid_hex] == "Driver 507f1f77bcf86cd799439011"
    assert out[invalid_hexlen] == f"Driver {invalid_hexlen}"
    assert out[short_id] == f"Driver {short_id}"

@pytest.mark.asyncio
async def test_get_driver_names_error_fallback_defaults(svc_env):
    s = _make_service(svc_env)
    class BoomDrivers:
        def find(self, *a, **k): raise RuntimeError("fail")
    s.db_management.drivers = BoomDrivers()
    ids = ["a","b"]
    out = await s._get_driver_names(ids)
    assert out == {i: f"Driver {i}" for i in ids}

@pytest.mark.asyncio
async def test_get_total_trips_success_and_filter_shape(svc_env):
    s = _make_service(svc_env)
    s.db.trip_history.total_count = 7
    got = await s.get_total_trips("week")
    assert got == 7
    flt = s.db.trip_history.last_count_filter
    assert "created_at" in flt and "$gte" in flt["created_at"] and "$lte" in flt["created_at"]

@pytest.mark.asyncio
async def test_get_total_trips_failure_raises(svc_env, monkeypatch):
    s = _make_service(svc_env)
    async def boom(_): raise RuntimeError("x")
    monkeypatch.setattr(s.db.trip_history, "count_documents", boom, raising=True)
    with pytest.raises(RuntimeError):
        await s.get_total_trips("day")

@pytest.mark.asyncio
async def test_get_completion_rate_zero_total_returns_zero(svc_env):
    s = _make_service(svc_env)
    th = s.db.trip_history
    th.raise_on_status = None
    th.completed_count = 0
    th.cancelled_count = 0
    assert await s.get_completion_rate("day") == 0.0

@pytest.mark.asyncio
async def test_get_completion_rate_nonzero_rounds(svc_env):
    s = _make_service(svc_env)
    th = s.db.trip_history
    th.raise_on_status = None
    th.completed_count = 8
    th.cancelled_count = 2
    assert await s.get_completion_rate("week") == 80.0

@pytest.mark.asyncio
async def test_get_completion_rate_failure_raises(svc_env):
    s = _make_service(svc_env)
    th = s.db.trip_history
    th.raise_on_status = "completed"
    with pytest.raises(RuntimeError):
        await s.get_completion_rate("month")

@pytest.mark.asyncio
async def test_get_average_trips_per_day_dayframe_nonempty(svc_env):
    s = _make_service(svc_env)
    s.db.trip_history.find_trips = [{"_id":i} for i in range(5)]
    avg = await s.get_average_trips_per_day("day")
    assert avg == 5.0

@pytest.mark.asyncio
async def test_get_average_trips_per_day_week_empty_zero(svc_env):
    s = _make_service(svc_env)
    s.db.trip_history.find_trips = []
    avg = await s.get_average_trips_per_day("week")
    assert avg == 0.0

@pytest.mark.asyncio
async def test_get_average_trips_per_day_find_raises(svc_env):
    s = _make_service(svc_env)
    s.db.trip_history.find_raise = RuntimeError("find fail")
    with pytest.raises(RuntimeError):
        await s.get_average_trips_per_day("week")

@pytest.mark.asyncio
async def test_get_driver_trip_stats_formats_names_and_counts(svc_env):
    s = _make_service(svc_env)
    th = s.db.trip_history
    hex_id = "507f1f77bcf86cd799439011"
    th.aggregate_result = [
        {"_id":"D1","completed_trips":3,"cancelled_trips":1},
        {"_id":hex_id,"completed_trips":0,"cancelled_trips":2},
    ]
    s.db_management.drivers.drivers_data = []
    out = await s.get_driver_trip_stats("week")
    out = sorted(out, key=lambda x: x["driver_name"])
    assert out[0] == {
        "driver_id": hex_id,
        "driver_name": f"Driver {hex_id}",
        "completed_trips": 0,
        "cancelled_trips": 2,
    }
    assert out[1] == {
        "driver_id": "D1",
        "driver_name": "Driver D1",
        "completed_trips": 3,
        "cancelled_trips": 1,
    }

@pytest.mark.asyncio
async def test_get_driver_trip_stats_aggregate_raises(svc_env):
    s = _make_service(svc_env)
    s.db.trip_history.aggregate_raise = RuntimeError("agg fail")
    with pytest.raises(RuntimeError):
        await s.get_driver_trip_stats("week")

def test_get_start_date_variants(svc_env):
    s = _make_service(svc_env)
    end = datetime(2030,1,31,tzinfo=timezone.utc)
    assert (end - s._get_start_date("day", end)).days == 1
    assert (end - s._get_start_date("WEEK", end)).days == 7
    assert (end - s._get_start_date("month", end)).days == 30
    assert (end - s._get_start_date("year", end)).days == 365
    assert (end - s._get_start_date("weird", end)).days == 7
