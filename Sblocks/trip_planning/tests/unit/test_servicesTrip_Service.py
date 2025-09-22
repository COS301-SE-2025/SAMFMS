# tests/unit/test_servicesTrip_Service.py
# Self-contained TripService tests with isolated import (no conftest.py).
# Fixes applied:
# - Force stub overrides for bson/schemas/repositories/events during import, then restore originals.
# - Ensure CreateTripRequest has route_info default (prevents AttributeError).
# - Always bind svc.db / svc.db_gps per test (or patch before constructing TripService).
# - Use 24-hex ObjectIds where code converts strings to ObjectId.
# - Keep tests small and one-branch-per-test.

import os, sys, importlib, importlib.util, types
from types import SimpleNamespace
from datetime import datetime, timedelta
import pytest

# -------------------------------- Path resolver --------------------------------
HERE = os.path.abspath(os.path.dirname(__file__))
PARENTS = [os.path.abspath(os.path.join(HERE, *([".."] * i))) for i in range(1, 6)]
CANDIDATES = list(dict.fromkeys(PARENTS + [os.getcwd(), HERE]))
for p in CANDIDATES:
    if p not in sys.path:
        sys.path.insert(0, p)

# ----------------------------- Isolated module loader ---------------------------
def _walk_roots_for(filename, roots):
    seen = set()
    SKIP = {".git", ".venv", "venv", "env", "__pycache__", ".pytest_cache", ".mypy_cache"}
    for root in roots:
        if not os.path.isdir(root): continue
        for dirpath, _, filenames in os.walk(root):
            b = os.path.basename(dirpath).lower()
            if b in SKIP: continue
            if dirpath in seen: continue
            seen.add(dirpath)
            if filename in filenames:
                yield os.path.join(dirpath, filename)

def _load_trip_service_module():
    # Force override critical modules during import; restore right after, so other tests aren't affected.
    originals = {}
    overridden = []

    def _force(name, mod):
        originals[name] = sys.modules.get(name)
        sys.modules[name] = mod
        overridden.append(name)

    # ----- force stub: bson.ObjectId -----
    bson_mod = types.ModuleType("bson")
    class _ObjectId:
        def __init__(self, s): self._s = str(s)
        def __repr__(self): return f"ObjectId({self._s!r})"
        def __str__(self): return self._s
        def __eq__(self, o): return str(o) == self._s
    bson_mod.ObjectId = _ObjectId
    _force("bson", bson_mod)

    # ----- force stub: schemas.entities -----
    schemas_pkg = types.ModuleType("schemas")
    ent = types.ModuleType("schemas.entities")
    class Trip:
        def __init__(self, **kw):
            self.__dict__.update(kw)
            if "_id" in kw and "id" not in kw:
                self.id = kw["_id"]
    class VehicleLocation:
        def __init__(self, **kw): self.__dict__.update(kw)
    class TripStatus:
        from types import SimpleNamespace as _SN
        SCHEDULED   = _SN(value="scheduled")
        IN_PROGRESS = _SN(value="in_progress")
        PAUSED      = _SN(value="paused")
        COMPLETED   = _SN(value="completed")
        CANCELLED   = _SN(value="cancelled")
        MISSED      = _SN(value="missed")
    class TripConstraint: ...
    ent.Trip, ent.TripStatus, ent.TripConstraint, ent.VehicleLocation = Trip, TripStatus, TripConstraint, VehicleLocation
    _force("schemas", schemas_pkg)
    _force("schemas.entities", ent)

    # ----- force stub: schemas.requests -----
    req = types.ModuleType("schemas.requests")
    class CreateTripRequest:
        # Provide route_info default to avoid AttributeError in service
        def __init__(self, **kw):
            self.name = kw.get("name")
            self.description = kw.get("description")
            self.scheduled_start_time = kw.get("scheduled_start_time")
            self.scheduled_end_time = kw.get("scheduled_end_time")
            self.origin = kw.get("origin")
            self.destination = kw.get("destination")
            self.priority = kw.get("priority")
            self.driver_assignment = kw.get("driver_assignment")
            self.vehicle_id = kw.get("vehicle_id")
            self.route_info = kw.get("route_info", None)  # important default
        def dict(self, exclude_unset=False): return dict(self.__dict__)
    class UpdateTripRequest:
        def __init__(self, **kw):
            for k,v in kw.items(): setattr(self, k, v)
        def dict(self, exclude_unset=False): return dict(self.__dict__)
    class TripFilterRequest:
        def __init__(self, **kw):
            self.name = kw.get("name")
            self.status = kw.get("status")
            self.priority = kw.get("priority")
            self.driver_assignment = kw.get("driver_assignment")
            self.vehicle_id = kw.get("vehicle_id")
            self.created_by = kw.get("created_by")
            self.start_date = kw.get("start_date")
            self.end_date = kw.get("end_date")
            self.origin_area = kw.get("origin_area")
            self.destination_area = kw.get("destination_area")
            self.area_radius = kw.get("area_radius")
            self.skip = kw.get("skip", 0)
            self.limit = kw.get("limit", 50)
            self.sort_by = kw.get("sort_by", "scheduled_start_time")
            self.sort_order = kw.get("sort_order", "asc")
    req.CreateTripRequest, req.UpdateTripRequest, req.TripFilterRequest = CreateTripRequest, UpdateTripRequest, TripFilterRequest
    _force("schemas.requests", req)

    # ----- force stub: repositories.database -----
    db_mod = types.ModuleType("repositories.database")
    class _StubCol:
        async def find_one(self, q): return None
        def find(self, q): return _AsyncCursor([])
        def aggregate(self, p): return _ToList([])
        async def update_one(self, f, u): return SimpleNamespace(modified_count=1, matched_count=1)
        async def insert_one(self, d): return SimpleNamespace(inserted_id="X")
        async def delete_one(self, f): return SimpleNamespace(deleted_count=1)
        async def count_documents(self, q): return 0
    db_mod.db_manager = SimpleNamespace(trips=_StubCol(), trip_history=_StubCol(), trip_analytics=_StubCol())
    db_mod.db_manager_gps = SimpleNamespace(db=SimpleNamespace(vehicle_locations=_StubCol()))
    _force("repositories.database", db_mod)

    # ----- force stub: events.publisher.event_publisher -----
    events_pkg = types.ModuleType("events")
    ev_mod = types.ModuleType("events.publisher")
    async def _nop(*a, **k): return None
    ev_mod.event_publisher = SimpleNamespace(
        publish_trip_created=_nop, publish_trip_updated=_nop,
        publish_trip_started=_nop, publish_trip_completed=_nop,
        publish_trip_deleted=_nop
    )
    _force("events", events_pkg)
    _force("events.publisher", ev_mod)

    # helper cursor stubs used by db stub
    class _ToList:
        def __init__(self, items): self._items = list(items)
        async def to_list(self, *a, **k):
            length = k.get("length")
            data = list(self._items)
            return data if length is None else data[:length]
    class _AsyncCursor:
        def __init__(self, items): self._items = list(items); self._i=0
        def sort(self, *a): return self
        def skip(self, *a): return self
        def limit(self, *a): return self
        def __aiter__(self): return self
        async def __anext__(self):
            if self._i >= len(self._items): raise StopAsyncIteration
            v = self._items[self._i]; self._i += 1; return v

    # Load module by file path, then restore originals in sys.modules table
    try:
        for path in _walk_roots_for("trip_service.py", CANDIDATES):
            try:
                mod_name = f"loaded.trip_service_{abs(hash(path))}"
                spec = importlib.util.spec_from_file_location(mod_name, path)
                mod = importlib.util.module_from_spec(spec)
                sys.modules[mod_name] = mod
                spec.loader.exec_module(mod)  # type: ignore[attr-defined]
                return mod
            except Exception:
                continue
        raise ModuleNotFoundError("Could not locate trip_service.py")
    finally:
        for name in overridden:
            if originals.get(name) is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = originals[name]

trip_service_module = _load_trip_service_module()
TripService = trip_service_module.TripService
TripStatus = trip_service_module.TripStatus
Trip = trip_service_module.Trip
CreateTripRequest = trip_service_module.CreateTripRequest
UpdateTripRequest = trip_service_module.UpdateTripRequest
TripFilterRequest = trip_service_module.TripFilterRequest
ObjectId = trip_service_module.ObjectId

# ----------------------------- Test helpers (per test) --------------------------
class Cursor:
    """Async cursor with chainable sort/skip/limit and query capture."""
    def __init__(self, items): self.items = list(items); self.ops=[]
    def sort(self, field, direction): self.ops.append(("sort", field, direction)); return self
    def skip(self, n): self.ops.append(("skip", n)); return self
    def limit(self, n): self.ops.append(("limit", n)); return self
    def __aiter__(self): self._i=0; return self
    async def __anext__(self):
        if self._i >= len(self.items): raise StopAsyncIteration
        v = self.items[self._i]; self._i += 1; return v

def set_svc_db(svc, trips=None, trip_history=None, trip_analytics=None):
    """Bind svc.db to our fakes (must be called if you patch module db_manager AFTER creating service)."""
    svc.db = SimpleNamespace(
        trips = trips if trips is not None else SimpleNamespace(
            find=lambda q: Cursor([]),
            find_one=lambda q: None,
            update_one=lambda f,u: SimpleNamespace(modified_count=0),
            insert_one=lambda d: SimpleNamespace(inserted_id="X"),
            delete_one=lambda f: SimpleNamespace(deleted_count=0),
            count_documents=lambda q: 0
        ),
        trip_history = trip_history if trip_history is not None else SimpleNamespace(
            find=lambda q: Cursor([])
        ),
        trip_analytics = trip_analytics if trip_analytics is not None else SimpleNamespace(
            insert_one=lambda d: SimpleNamespace()
        ),
    )

def set_svc_gps(svc, vehicle_locations=None):
    svc.db_gps = SimpleNamespace(
        db=SimpleNamespace(
            vehicle_locations = vehicle_locations if vehicle_locations is not None else SimpleNamespace(
                find_one=lambda q: None
            )
        )
    )

# --------------------------------- create_trip ----------------------------------
@pytest.mark.asyncio
async def test_create_trip_invalid_schedule_raises(monkeypatch):
    svc = TripService()
    req = CreateTripRequest(
        scheduled_start_time=datetime(2024,1,1,12),
        scheduled_end_time=datetime(2024,1,1,11),
        vehicle_id="V1"
    )
    with pytest.raises(ValueError):
        await svc.create_trip(req, created_by="U")

@pytest.mark.asyncio
async def test_create_trip_vehicle_unavailable_raises(monkeypatch):
    svc = TripService()
    async def fake_check(*a, **k): return False
    monkeypatch.setattr(svc, "_check_vehicle_availability", fake_check)
    req = CreateTripRequest(
        scheduled_start_time=datetime(2024,1,1,10),
        scheduled_end_time=datetime(2024,1,1,12),
        vehicle_id="V1"
    )
    with pytest.raises(ValueError):
        await svc.create_trip(req, created_by="U")

@pytest.mark.asyncio
async def test_create_trip_insert_then_fetch_none_raises(monkeypatch):
    svc = TripService()
    async def ok(*a, **k): return True
    monkeypatch.setattr(svc, "_check_vehicle_availability", ok)

    class _Trips:
        async def insert_one(self, d): return SimpleNamespace(inserted_id="T1")
    # bind svc.db to our fake collection
    set_svc_db(svc, trips=_Trips())

    async def fake_get(_): return None
    monkeypatch.setattr(svc, "get_trip_by_id", fake_get)

    req = CreateTripRequest(
        scheduled_start_time=datetime(2024,1,1,10),
        scheduled_end_time=datetime(2024,1,1,12),
        vehicle_id="V1"
    )
    with pytest.raises(RuntimeError):
        await svc.create_trip(req, created_by="U")

@pytest.mark.asyncio
async def test_create_trip_happy_path_with_route_info(monkeypatch):
    svc = TripService()
    async def ok(*a, **k): return True
    monkeypatch.setattr(svc, "_check_vehicle_availability", ok)

    class _Trips:
        async def insert_one(self, d):
            assert d["estimated_distance"] == pytest.approx(1.234)
            assert d["estimated_duration"] == pytest.approx(2.0)
            return SimpleNamespace(inserted_id="507f191e810c19729de860ea")
    set_svc_db(svc, trips=_Trips())

    async def fake_get(tid):
        return SimpleNamespace(id=tid, status=TripStatus.SCHEDULED, name="Trip A")
    monkeypatch.setattr(svc, "get_trip_by_id", fake_get)

    calls={}
    async def pub_created(trip): calls["id"]=trip.id
    monkeypatch.setattr(trip_service_module, "event_publisher", SimpleNamespace(
        publish_trip_created=pub_created,
        publish_trip_updated=lambda *a, **k: None,
        publish_trip_started=lambda *a, **k: None,
        publish_trip_completed=lambda *a, **k: None,
        publish_trip_deleted=lambda *a, **k: None,
    ))

    route_info = SimpleNamespace(distance=1234.0, duration=120.0)
    req = CreateTripRequest(
        scheduled_start_time=datetime(2024,1,1,10),
        scheduled_end_time=datetime(2024,1,1,12),
        vehicle_id="V9",
        route_info=route_info
    )
    out = await svc.create_trip(req, created_by="U")
    assert out.id == "507f191e810c19729de860ea"
    assert calls["id"] == out.id

# -------------------------------- get_all_trips --------------------------------
@pytest.mark.asyncio
async def test_get_all_trips_success():
    svc = TripService()
    docs = [{"_id":"A","name":"t1"},{"_id":"B","name":"t2"}]
    class _Trips:
        def find(self, q): return Cursor(docs)
    set_svc_db(svc, trips=_Trips())
    out = await svc.get_all_trips()
    assert [t.id for t in out] == ["A","B"]

@pytest.mark.asyncio
async def test_get_all_trips_raises():
    svc = TripService()
    class _Trips:
        def find(self, q): raise RuntimeError("db")
    set_svc_db(svc, trips=_Trips())
    with pytest.raises(RuntimeError):
        await svc.get_all_trips()

# --------------------------- vehicle route & location ---------------------------
@pytest.mark.asyncio
async def test_get_vehicle_route_found_and_none():
    svc = TripService()
    class _Trips:
        async def find_one(self, q): return {"route_info":{"coordinates":[[0,0],[1,1]]}}
    set_svc_db(svc, trips=_Trips())
    r = await svc.get_vehicle_route("V1")
    assert r == {"coordinates":[[0,0],[1,1]]}

    class _Trips2:
        async def find_one(self, q): return None
    set_svc_db(svc, trips=_Trips2())
    r2 = await svc.get_vehicle_route("V1")
    assert r2 is None

@pytest.mark.asyncio
async def test_get_vehicle_location_cases():
    svc = TripService()
    class _GPS:
        async def find_one(self, q): return {"_id":"X","vehicle_id":"V1","latitude":-26.2,"longitude":28.0}
    set_svc_gps(svc, vehicle_locations=_GPS())
    loc = await svc.get_vehicle_location("V1")
    assert loc.latitude == -26.2 and loc.longitude == 28.0

    class _GPS2:
        async def find_one(self, q): return None
    set_svc_gps(svc, vehicle_locations=_GPS2())
    assert await svc.get_vehicle_location("V1") is None

    class _GPS3:
        async def find_one(self, q): raise RuntimeError("boom")
    set_svc_gps(svc, vehicle_locations=_GPS3())
    with pytest.raises(RuntimeError):
        await svc.get_vehicle_location("V1")

# ------------------------------- get_vehicle_polyline ---------------------------
@pytest.mark.asyncio
async def test_get_vehicle_polyline_no_trip_or_no_coords():
    svc = TripService()
    class _Trips:
        async def find_one(self, q): return None
    set_svc_db(svc, trips=_Trips())
    assert await svc.get_vehicle_polyline("V1") is None

    class _Trips2:
        async def find_one(self, q): return {"vehicle_id":"V1"}  # no route_info
    set_svc_db(svc, trips=_Trips2())
    assert await svc.get_vehicle_polyline("V1") is None


@pytest.mark.asyncio
async def test_get_vehicle_polyline_location_exception_fallback():
    svc = TripService()
    class _Trips:
        async def find_one(self, q):
            return {"vehicle_id":"V1","route_info":{"coordinates":[[1,1],[2,2]]}, "_id":"T1"}
    set_svc_db(svc, trips=_Trips())
    async def boom(vid): raise RuntimeError("gps down")
    svc.get_vehicle_location = boom
    pl = await svc.get_vehicle_polyline("V1")
    assert pl == [[1,1],[2,2]]

# ------------------------------- get_active_trips --------------------------------
@pytest.mark.asyncio
async def test_get_active_trips_with_and_without_driver():
    svc = TripService()
    recorded = {}
    docs = [{"_id":"A","status":TripStatus.IN_PROGRESS},{"_id":"B","status":TripStatus.IN_PROGRESS}]
    class _Trips:
        def find(self, q): recorded["q"]=q; return Cursor(docs)
    set_svc_db(svc, trips=_Trips())
    out = await svc.get_active_trips()
    assert len(out)==2 and "driver_assignment" not in recorded["q"]

    out2 = await svc.get_active_trips(driver_id="D1")
    assert len(out2)==2 and recorded["q"]["driver_assignment"]=="D1"

# -------------------------------- get_trip_by_id --------------------------------
@pytest.mark.asyncio
async def test_get_trip_by_id_found_and_none():
    svc = TripService()
    class _Trips:
        async def find_one(self, q): return {"_id":"507f191e810c19729de860ea", "name":"X"}
    set_svc_db(svc, trips=_Trips())
    t = await svc.get_trip_by_id("507f191e810c19729de860ea")
    assert t.id == "507f191e810c19729de860ea"

    class _Trips2:
        async def find_one(self, q): return None
    set_svc_db(svc, trips=_Trips2())
    assert await svc.get_trip_by_id("X") is None

# --------------------------------- update_trip ----------------------------------
@pytest.mark.asyncio
async def test_update_trip_not_found_returns_none():
    svc = TripService()
    async def nf(_): return None
    svc.get_trip_by_id = nf
    out = await svc.update_trip("507f191e810c19729de860ea", UpdateTripRequest(name="x"), updated_by="U")
    assert out is None

@pytest.mark.asyncio
async def test_update_trip_invalid_schedule_raises():
    svc = TripService()
    async def get_existing(_): return SimpleNamespace(id="507f191e810c19729de860ea", status=TripStatus.SCHEDULED)
    svc.get_trip_by_id = get_existing
    req = UpdateTripRequest(scheduled_start_time=datetime(2024,1,1,12),
                            scheduled_end_time=datetime(2024,1,1,11))
    with pytest.raises(ValueError):
        await svc.update_trip("507f191e810c19729de860ea", req, updated_by="U")

@pytest.mark.asyncio
async def test_update_trip_modified_zero_returns_none():
    svc = TripService()
    async def get_existing(_): return SimpleNamespace(id="507f191e810c19729de860ea", status=TripStatus.SCHEDULED)
    svc.get_trip_by_id = get_existing
    class _Trips:
        async def update_one(self, f, u): return SimpleNamespace(modified_count=0, matched_count=1)
    set_svc_db(svc, trips=_Trips())
    out = await svc.update_trip("507f191e810c19729de860ea", UpdateTripRequest(name="n"), updated_by="U")
    assert out is None

@pytest.mark.asyncio
async def test_update_trip_success_publishes():
    svc = TripService()
    old = SimpleNamespace(id="507f191e810c19729de860ea", status=TripStatus.SCHEDULED, name="old")
    new = SimpleNamespace(id="507f191e810c19729de860ea", status=TripStatus.SCHEDULED, name="new")
    state={"first":True}
    async def getter(_):
        if state["first"]:
            state["first"]=False
            return old
        return new
    svc.get_trip_by_id = getter

    class _Trips:
        async def update_one(self, f, u): return SimpleNamespace(modified_count=1, matched_count=1)
    calls={}
    async def pub_updated(updated, previous): calls["ok"]= (updated.name, previous.name)
    set_svc_db(svc, trips=_Trips())
    trip_service_module.event_publisher = SimpleNamespace(publish_trip_updated=pub_updated)
    out = await svc.update_trip("507f191e810c19729de860ea", UpdateTripRequest(name="new"), updated_by="U")
    assert out.name == "new"
    assert calls["ok"] == ("new","old")

# --------------------------------- delete_trip ----------------------------------
@pytest.mark.asyncio
async def test_delete_trip_not_found_and_not_deleted():
    svc = TripService()
    async def nf(_): return None
    svc.get_trip_by_id = nf
    assert (await svc.delete_trip("507f191e810c19729de860ea","U")) is False

    async def ex(_): return SimpleNamespace(id="507f191e810c19729de860ea", status=TripStatus.SCHEDULED)
    class _Trips:
        async def delete_one(self, f): return SimpleNamespace(deleted_count=0)
    svc.get_trip_by_id = ex
    set_svc_db(svc, trips=_Trips())
    assert (await svc.delete_trip("507f191e810c19729de860ea","U")) is False

@pytest.mark.asyncio
async def test_delete_trip_success_publishes():
    svc = TripService()
    async def ex(_): return SimpleNamespace(id="507f191e810c19729de860ea", status=TripStatus.SCHEDULED)
    class _Trips:
        async def delete_one(self, f): return SimpleNamespace(deleted_count=1)
    pub={}
    async def pub_del(trip): pub["id"]=trip.id
    svc.get_trip_by_id = ex
    set_svc_db(svc, trips=_Trips())
    trip_service_module.event_publisher = SimpleNamespace(publish_trip_deleted=pub_del)
    assert (await svc.delete_trip("507f191e810c19729de860ea","U")) is True
    assert pub["id"] == "507f191e810c19729de860ea"

# ----------------------------- get_trip_by_name_and_driver ----------------------
@pytest.mark.asyncio
async def test_get_trip_by_name_and_driver_found_and_not_found():
    svc = TripService()
    class _Trips:
        async def find_one(self, q): return {"_id":"T1","name":"X","driver_assignment":"D1"}
    set_svc_db(svc, trips=_Trips())
    fr = TripFilterRequest(driver_assignment="D1", name="X")
    t = await svc.get_trip_by_name_and_driver(fr)
    assert t.id == "T1"

    class _Trips2:
        async def find_one(self, q): return None
    set_svc_db(svc, trips=_Trips2())
    with pytest.raises(ValueError):
        await svc.get_trip_by_name_and_driver(fr)

# ------------------------------------ list_trips --------------------------------
@pytest.mark.asyncio
async def test_list_trips_with_filters_and_sort():
    svc = TripService()
    recorded = {}
    docs = [{"_id":"A","name":"t1"},{"_id":"B","name":"t2"}]
    class _Trips:
        async def count_documents(self, q): recorded["count_q"]=q; return 2
        def find(self, q): recorded["find_q"]=q; return Cursor(docs)
    set_svc_db(svc, trips=_Trips())
    fr = TripFilterRequest(
        status=["scheduled","paused"],
        priority=["high"],
        driver_assignment="D9",
        name="TripX",
        vehicle_id="V7",
        created_by="U1",
        start_date=datetime(2024,1,1),
        end_date=datetime(2024,1,31),
        sort_by="scheduled_start_time",
        sort_order="desc",
        skip=5,
        limit=7
    )
    out = await svc.list_trips(fr)
    assert [t.id for t in out] == ["A","B"]
    q = recorded["find_q"]
    assert q["status"]["$in"] == ["scheduled","paused"]
    assert q["driver_assignment"] == "D9"
    assert q["name"] == "TripX"
    assert q["vehicle_id"] == "V7"
    assert q["created_by"] == "U1"
    assert q["scheduled_start_time"]["$gte"] == fr.start_date
    assert q["scheduled_start_time"]["$lte"] == fr.end_date

# ------------------------------------ start/pause/resume ------------------------
@pytest.mark.asyncio
async def test_start_trip_not_found_and_wrong_status():
    svc = TripService()
    async def nf(_): return None
    svc.get_trip_by_id = nf
    assert await svc.start_trip("507f191e810c19729de860ea","U") is None

    async def wrong(_): return SimpleNamespace(id="507f191e810c19729de860ea", status=TripStatus.IN_PROGRESS)
    svc.get_trip_by_id = wrong
    with pytest.raises(ValueError):
        await svc.start_trip("507f191e810c19729de860ea","U")

@pytest.mark.asyncio
async def test_start_trip_success():
    svc = TripService()
    state = {"n": 0}
    async def getter(_):
        state["n"] += 1
        return SimpleNamespace(id="507f191e810c19729de860ea", status=TripStatus.SCHEDULED) if state["n"] == 1 \
               else SimpleNamespace(id="507f191e810c19729de860ea", status=TripStatus.IN_PROGRESS)
    svc.get_trip_by_id = getter
    class _Trips:
        async def update_one(self, f, u): return SimpleNamespace()
    pub={}
    async def pub_started(trip): pub["id"]=trip.id
    set_svc_db(svc, trips=_Trips())
    trip_service_module.event_publisher = SimpleNamespace(publish_trip_started=pub_started)
    out = await svc.start_trip("507f191e810c19729de860ea","U")
    assert out.status == TripStatus.IN_PROGRESS
    assert pub["id"] == "507f191e810c19729de860ea"

@pytest.mark.asyncio
async def test_pause_resume_trip_paths():
    svc = TripService()
    # pause: not found
    async def nf(_): return None
    svc.get_trip_by_id = nf
    assert await svc.pause_trip("507f191e810c19729de860ea","U") is None

    # pause: wrong status
    async def wrong(_): return SimpleNamespace(id="507f191e810c19729de860ea", status=TripStatus.SCHEDULED)
    svc.get_trip_by_id = wrong
    with pytest.raises(ValueError):
        await svc.pause_trip("507f191e810c19729de860ea","U")

    # pause: success (IN_PROGRESS -> PAUSED)
    seq=[lambda _: SimpleNamespace(id="507f191e810c19729de860ea", status=TripStatus.IN_PROGRESS),
         lambda _: SimpleNamespace(id="507f191e810c19729de860ea", status=TripStatus.PAUSED)]
    idx={"i":0}
    async def getter(_):
        v = seq[idx["i"]]; idx["i"]=min(idx["i"]+1, len(seq)-1); return v(_)
    svc.get_trip_by_id = getter
    class _Trips:
        async def update_one(self, f, u): return SimpleNamespace()
    pub={}
    async def pub_upd(new, old): pub["ok"]=True
    set_svc_db(svc, trips=_Trips())
    trip_service_module.event_publisher = SimpleNamespace(publish_trip_updated=pub_upd)
    out = await svc.pause_trip("507f191e810c19729de860ea","U")
    assert out.status == TripStatus.PAUSED and pub["ok"]

    # resume: not found
    async def nf2(_): return None
    svc.get_trip_by_id = nf2
    assert await svc.resume_trip("507f191e810c19729de860ea","U") is None

    # resume: wrong status
    async def wrong2(_): return SimpleNamespace(id="507f191e810c19729de860ea", status=TripStatus.SCHEDULED)
    svc.get_trip_by_id = wrong2
    with pytest.raises(ValueError):
        await svc.resume_trip("507f191e810c19729de860ea","U")

    # resume: success (PAUSED -> IN_PROGRESS)
    seq2=[lambda _: SimpleNamespace(id="507f191e810c19729de860ea", status=TripStatus.PAUSED),
          lambda _: SimpleNamespace(id="507f191e810c19729de860ea", status=TripStatus.IN_PROGRESS)]
    idx2={"i":0}
    async def getter2(_):
        v = seq2[idx2["i"]]; idx2["i"]=min(idx2["i"]+1, len(seq2)-1); return v(_)
    svc.get_trip_by_id = getter2
    out2 = await svc.resume_trip("507f191e810c19729de860ea","U")
    assert out2.status == TripStatus.IN_PROGRESS

# ------------------------------------ cancel_trip ---------------------------------
@pytest.mark.asyncio
async def test_cancel_trip_not_found_already_final_missing_doc():
    svc = TripService()
    async def nf(_): return None
    svc.get_trip_by_id = nf
    assert await svc.cancel_trip("507f191e810c19729de860ea","U") is None

    async def final(_): return SimpleNamespace(id="507f191e810c19729de860ea", status=TripStatus.COMPLETED)
    svc.get_trip_by_id = final
    with pytest.raises(ValueError):
        await svc.cancel_trip("507f191e810c19729de860ea","U")

    async def sched(_): return SimpleNamespace(id="507f191e810c19729de860ea", status=TripStatus.SCHEDULED)
    class _Trips:
        async def find_one(self, q): return None
    svc.get_trip_by_id = sched
    set_svc_db(svc, trips=_Trips())
    assert await svc.cancel_trip("507f191e810c19729de860ea","U") is None

@pytest.mark.asyncio
async def test_cancel_trip_success():
    svc = TripService()
    async def sched(_): return SimpleNamespace(id="507f191e810c19729de860ea", status=TripStatus.SCHEDULED)
    class _Trips:
        async def find_one(self, q): return {"_id": "507f191e810c19729de860ea", "status": TripStatus.SCHEDULED}
        async def delete_one(self, q): return SimpleNamespace()
    class _Hist:
        async def insert_one(self, doc):
            assert doc["status"] == TripStatus.CANCELLED.value
            return SimpleNamespace()
    pub={}
    async def pub_upd(new, old): pub["ok"]=True
    svc.get_trip_by_id = sched
    set_svc_db(svc, trips=_Trips(), trip_history=_Hist())
    trip_service_module.event_publisher = SimpleNamespace(publish_trip_updated=pub_upd)
    out = await svc.cancel_trip("507f191e810c19729de860ea","U","no-show")
    assert out.id == "507f191e810c19729de860ea" and pub["ok"]

# ------------------------------------ complete_trip -------------------------------
@pytest.mark.asyncio
async def test_complete_trip_not_found_wrong_status_missing_doc():
    svc = TripService()
    async def nf(_): return None
    svc.get_trip_by_id = nf
    assert await svc.complete_trip("507f191e810c19729de860ea","U") is None

    async def sched(_): return SimpleNamespace(id="507f191e810c19729de860ea", status=TripStatus.SCHEDULED)
    svc.get_trip_by_id = sched
    with pytest.raises(ValueError):
        await svc.complete_trip("507f191e810c19729de860ea","U")

    async def inprog(_): return SimpleNamespace(id="507f191e810c19729de860ea", status=TripStatus.IN_PROGRESS)
    class _Trips:
        async def find_one(self, q): return None
    svc.get_trip_by_id = inprog
    set_svc_db(svc, trips=_Trips())
    assert await svc.complete_trip("507f191e810c19729de860ea","U") is None

@pytest.mark.asyncio
async def test_complete_trip_success_calls_analytics_and_publishes():
    svc = TripService()
    async def inprog(_): return SimpleNamespace(id="507f191e810c19729de860ea", status=TripStatus.IN_PROGRESS)
    class _Trips:
        async def find_one(self, q): return {"_id": "507f191e810c19729de860ea", "status": TripStatus.IN_PROGRESS,
                                             "actual_start_time": datetime.utcnow(), "actual_end_time": datetime.utcnow(),
                                             "scheduled_start_time": datetime.utcnow() - timedelta(minutes=10),
                                             "estimated_duration": 20, "estimated_distance": 10}
        async def delete_one(self, q): return SimpleNamespace()
    class _Hist:
        async def insert_one(self, doc): return SimpleNamespace()
    calls = {"analytics":0,"completed":0}
    async def fake_calc(trip): calls["analytics"]+=1
    async def pub_completed(trip): calls["completed"]+=1
    svc.get_trip_by_id = inprog
    set_svc_db(svc, trips=_Trips(), trip_history=_Hist())
    svc._calculate_trip_analytics = fake_calc
    trip_service_module.event_publisher = SimpleNamespace(publish_trip_completed=pub_completed)
    out = await svc.complete_trip("507f191e810c19729de860ea","U")
    assert out.id == "507f191e810c19729de860ea"
    assert calls["analytics"] == 1 and calls["completed"] == 1

# ------------------------------- _calculate_trip_analytics -----------------------
@pytest.mark.asyncio
async def test__calculate_trip_analytics_skips_when_missing_times():
    svc = TripService()
    class _TA:
        async def insert_one(self, d): raise AssertionError("should not insert")
    set_svc_db(svc, trip_analytics=_TA())
    t = SimpleNamespace(id="T1", actual_start_time=None, actual_end_time=None)
    await svc._calculate_trip_analytics(t)  # no exception, no insert

@pytest.mark.asyncio
async def test__calculate_trip_analytics_delay_positive_and_zero():
    svc = TripService()
    captured=[]
    class _TA:
        async def insert_one(self, d): captured.append(d)
    set_svc_db(svc, trip_analytics=_TA())
    t1 = SimpleNamespace(
        id="T1",
        actual_start_time=datetime(2024,1,1,10,5),
        actual_end_time=datetime(2024,1,1,10,45),
        scheduled_start_time=datetime(2024,1,1,10,0),
        estimated_duration=30, estimated_distance=12.3
    )
    await svc._calculate_trip_analytics(t1)
    assert captured[-1]["actual_duration"] == 40
    assert captured[-1]["delays"] == 5

    t2 = SimpleNamespace(
        id="T2",
        actual_start_time=datetime(2024,1,1,9,55),
        actual_end_time=datetime(2024,1,1,10,20),
        scheduled_start_time=datetime(2024,1,1,10,0),
        estimated_duration=30, estimated_distance=12.3
    )
    await svc._calculate_trip_analytics(t2)
    assert captured[-1]["delays"] == 0

# ------------------------------ upcoming / recent trips --------------------------
@pytest.mark.asyncio
async def test_get_all_upcoming_and_driver_upcoming():
    svc = TripService()
    docs = [{"_id":"U1"},{"_id":"U2"}]
    class _Trips:
        def find(self, q): return Cursor(docs)
    set_svc_db(svc, trips=_Trips())
    all_up = await svc.get_all_upcoming_trips()
    assert [t.id for t in all_up] == ["U1","U2"]

    driver_up = await svc.get_upcoming_trips("D9")
    assert [t.id for t in driver_up] == ["U1","U2"]

@pytest.mark.asyncio
async def test_get_recent_trips_and_all_recent():
    svc = TripService()
    docs = [{"_id":"R1"},{"_id":"R2"}]
    class _Hist:
        def find(self, q): return Cursor(docs)
    set_svc_db(svc, trip_history=_Hist())
    r = await svc.get_recent_trips("D1", limit=2, days=7)
    assert [t.id for t in r] == ["R1","R2"]
    r2 = await svc.get_all_recent_trips(limit=2, days=7)
    assert [t.id for t in r2] == ["R1","R2"]

# --------------------------- _check_vehicle_availability --------------------------
@pytest.mark.asyncio
async def test__check_vehicle_availability_conflict_no_conflict_and_error():
    svc = TripService()
    class _TripsA:
        async def find_one(self, q): return {"_id":"X"}  # conflict exists
    set_svc_db(svc, trips=_TripsA())
    ok = await svc._check_vehicle_availability("V1", datetime(2024,1,1,10), datetime(2024,1,1,12))
    assert ok is False

    class _TripsB:
        async def find_one(self, q): return None
    set_svc_db(svc, trips=_TripsB())
    ok2 = await svc._check_vehicle_availability("V1", datetime(2024,1,1,10), None)
    assert ok2 is True

    class _TripsC:
        async def find_one(self, q): raise RuntimeError("db down")
    set_svc_db(svc, trips=_TripsC())
    ok3 = await svc._check_vehicle_availability("V1", datetime(2024,1,1,10), datetime(2024,1,1,12))
    assert ok3 is False

# ---------------------------------- mark_missed_trips ----------------------------
@pytest.mark.asyncio
async def test_mark_missed_trips_counts_success_and_skips_errors():
    svc = TripService()
    docs = [{"_id":"M1","status":TripStatus.SCHEDULED}, {"_id":"M2","status":TripStatus.SCHEDULED}]
    class _Trips:
        def find(self, q): return Cursor(docs)
        async def delete_one(self, f): return SimpleNamespace()
    inserted=[]
    class _Hist:
        async def insert_one(self, doc):
            if doc["_id"]=="M2": raise RuntimeError("insert fail")
            inserted.append(doc["_id"]); return SimpleNamespace()
    pub=[]
    async def pub_upd(new, old): pub.append(new.id)
    set_svc_db(svc, trips=_Trips(), trip_history=_Hist())
    trip_service_module.event_publisher = SimpleNamespace(publish_trip_updated=pub_upd)
    count = await svc.mark_missed_trips()
    assert count == 1
    assert inserted == ["M1"]
