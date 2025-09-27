import os, sys, types, importlib.util
from types import SimpleNamespace
from unittest.mock import AsyncMock
import pytest
from datetime import datetime, timedelta, timezone

HERE = os.path.abspath(os.path.dirname(__file__))
print("[DEBUG] Test root HERE:", HERE)
SEARCH_ROOTS = [

    os.path.abspath(os.path.join(HERE, *([".."] * i))) for i in range(1, 6)
] + [HERE, os.getcwd()]
print("[DEBUG] SEARCH_ROOTS:", SEARCH_ROOTS)

def _walk_roots_for(filename, roots):
    print(f"[DEBUG] Walking roots for {filename} ...")
    seen = set()
    for root in roots:
        if not os.path.isdir(root):
            continue
        for dirpath, _, filenames in os.walk(root):
            base = os.path.basename(dirpath).lower()
            if base in {".git", ".venv", "venv", "env", "__pycache__", ".pytest_cache"}:
                continue
            if dirpath in seen:
                continue
            seen.add(dirpath)
            if filename in filenames:
                found = os.path.join(dirpath, filename)
                print(f"[DEBUG] Found {filename} at:", found)
                yield found

def _build_stub_modules():
    bson_mod = types.ModuleType("bson")
    class _ObjectId:
        def __init__(self, s): self.s = str(s)
        def __repr__(self): return f"OID({self.s})"
        def __str__(self): return self.s
    def ObjectId(x): return _ObjectId(x)
    bson_mod.ObjectId = ObjectId

    entities = types.ModuleType("schemas.entities")
    class TripStatus:
        SCHEDULED = "scheduled"
        IN_PROGRESS = "in_progress"
        COMPLETED = "completed"
        CANCELLED = "cancelled"
    class Trip:
        def __init__(self, **kw):
            for k, v in kw.items():
                setattr(self, k, v)
    class DriverAssignment:
        def __init__(self, **kw):
            for k, v in kw.items():
                setattr(self, k, v)
    entities.TripStatus = TripStatus
    entities.Trip = Trip
    entities.DriverAssignment = DriverAssignment

    requests = types.ModuleType("schemas.requests")
    class AssignDriverRequest:
        def __init__(self, driver_id: str, vehicle_id: str, notes: str | None = None):
            self.driver_id = driver_id
            self.vehicle_id = vehicle_id
            self.notes = notes
    class DriverAvailabilityRequest:
        def __init__(self, start_time: datetime, end_time: datetime, driver_ids=None):
            self.start_time = start_time
            self.end_time = end_time
            self.driver_ids = list(driver_ids or [])
    requests.AssignDriverRequest = AssignDriverRequest
    requests.DriverAvailabilityRequest = DriverAvailabilityRequest
    publisher = types.ModuleType("events.publisher")
    class _Publisher:
        def __init__(self):
            self.publish_driver_assigned = AsyncMock()
            self.publish_driver_unassigned = AsyncMock()
    publisher.event_publisher = _Publisher()

    repos_db = types.ModuleType("repositories.database")
    repos_db.db_manager = SimpleNamespace()
    repos_db.db_manager_management = SimpleNamespace()

    schemas_pkg = types.ModuleType("schemas")
    events_pkg = types.ModuleType("events")
    repos_pkg = types.ModuleType("repositories")

    return {
        "bson": bson_mod,
        "schemas": schemas_pkg,
        "schemas.entities": entities,
        "schemas.requests": requests,
        "events": events_pkg,
        "events.publisher": publisher,
        "repositories": repos_pkg,
        "repositories.database": repos_db,
    }

def _load_driver_service_isolated():
    print('[DEBUG] Attempting to locate and load driver_service.py')
    target_path = None
    for p in _walk_roots_for("driver_service.py", SEARCH_ROOTS):
        target_path = p
        break
    if not target_path:
        print('[DEBUG] driver_service.py NOT FOUND. Roots searched:', SEARCH_ROOTS)
        raise ModuleNotFoundError(
            f"Could not locate driver_service.py. Searched roots={SEARCH_ROOTS}"
        )

    snap = sys.modules.copy()
    try:
        stubs = _build_stub_modules()
        sys.modules.update(stubs)

        mod_name = f"loaded.driver_service_{abs(hash(target_path))}"
        spec = importlib.util.spec_from_file_location(mod_name, target_path)
        if not spec or not spec.loader:
            raise ImportError("Failed to build import spec for driver_service.py")
        mod = importlib.util.module_from_spec(spec)
        print('[DEBUG] Using driver_service module path:', target_path)
        sys.modules[mod_name] = mod
        spec.loader.exec_module(mod)
        print('[DEBUG] Loaded driver_service module:', mod)

        stub_refs = SimpleNamespace(
            TripStatus=stubs["schemas.entities"].TripStatus,
            Trip=stubs["schemas.entities"].Trip,
            DriverAssignment=stubs["schemas.entities"].DriverAssignment,
            AssignDriverRequest=stubs["schemas.requests"].AssignDriverRequest,
            DriverAvailabilityRequest=stubs["schemas.requests"].DriverAvailabilityRequest,
            event_publisher=stubs["events.publisher"].event_publisher,
        )
        return mod, stub_refs
    finally:
        to_remove = set(sys.modules) - set(snap)
        for k in to_remove:
            sys.modules.pop(k, None)
        sys.modules.clear()
        sys.modules.update(snap)

driver_service_module, _stubs = _load_driver_service_isolated()
DriverService = getattr(driver_service_module, "DriverService")

class _Cursor:
    def __init__(self, items):
        self._items = list(items)
        self._idx = 0
        self._skip = 0
        self._limit = None
    def sort(self, key, direction=1):
        rev = direction == -1
        self._items.sort(key=lambda d: d.get(key), reverse=rev)
        return self
    def skip(self, n):
        self._skip = n
        return self
    def limit(self, n):
        self._limit = n
        return self
    def __aiter__(self):
        self._idx = 0
        self._iter_items = self._sliced()
        return self
    async def __anext__(self):
        if self._idx >= len(self._iter_items):
            raise StopAsyncIteration
        item = self._iter_items[self._idx]
        self._idx += 1
        return item
    async def to_list(self, length=None):
        data = self._sliced()
        if length is not None:
            return data[:length]
        return data
    def _sliced(self):
        data = self._items[self._skip:]
        if self._limit is not None:
            data = data[:self._limit]
        return data

class _Coll:
    def __init__(self):
        self._find_one_impl = AsyncMock(return_value=None)
        self._update_one_impl = AsyncMock(return_value=None)
        self._delete_one_impl = AsyncMock(return_value=None)
        self._delete_many_impl = AsyncMock(return_value=None)
        self._insert_one_impl = AsyncMock(return_value=SimpleNamespace(inserted_id="newid"))
        self._find_impl = lambda *a, **k: _Cursor([])
        self._count_docs_impl = AsyncMock(return_value=0)
    async def find_one(self, *a, **k):
        return await self._find_one_impl(*a, **k)
    async def update_one(self, *a, **k):
        return await self._update_one_impl(*a, **k)
    async def delete_one(self, *a, **k):
        return await self._delete_one_impl(*a, **k)
    async def delete_many(self, *a, **k):
        return await self._delete_many_impl(*a, **k)
    async def insert_one(self, *a, **k):
        return await self._insert_one_impl(*a, **k)
    def find(self, *a, **k):
        return self._find_impl(*a, **k)
    async def count_documents(self, *a, **k):
        return await self._count_docs_impl(*a, **k)

def _wire_db_instance_only(svc, trips: _Coll, assigns: _Coll, drivers_mgmt: _Coll):
    print('[DEBUG] Wiring DB instances onto DriverService test stub')
    svc.db = SimpleNamespace(trips=trips, driver_assignments=assigns)
    svc.db_management = SimpleNamespace(
        drivers=drivers_mgmt,
        is_connected=lambda: True,
        database_name='testdb'
    )
    print('[DEBUG] svc.db_management.database_name=', svc.db_management.database_name)

def new_service():
    svc = DriverService()
    trips = _Coll()
    assigns = _Coll()
    drivers = _Coll()
    _wire_db_instance_only(svc, trips, assigns, drivers)
    return svc, SimpleNamespace(trips=trips, assigns=assigns, drivers=drivers)

TripStatus = _stubs.TripStatus
Trip = _stubs.Trip
DriverAssignment = _stubs.DriverAssignment
AssignDriverRequest = _stubs.AssignDriverRequest
DriverAvailabilityRequest = _stubs.DriverAvailabilityRequest
event_publisher = _stubs.event_publisher

# ====================================================================================
# ====================================================================================

@pytest.mark.asyncio
async def test_deactivateDriver_success():
    svc, stubs = new_service()
    stubs.drivers._find_one_impl.return_value = {"employee_id": "E1"}
    await svc.deactivateDriver("E1")
    args, kwargs = stubs.drivers._update_one_impl.call_args
    update_doc = args[1] if len(args) >= 2 else kwargs.get("update", {})
    body = update_doc.get("$set", update_doc)
    assert args[0] == {"employee_id": "E1"}
    assert body["status"] == "unavailable"
    assert "updated_at" in body

@pytest.mark.asyncio
async def test_deactivateDriver_not_found_raises():
    svc, stubs = new_service()
    stubs.drivers._find_one_impl.return_value = None
    with pytest.raises(ValueError):
        await svc.deactivateDriver("E404")

@pytest.mark.asyncio
async def test_deactivateDriver_update_failure_propagates():
    svc, stubs = new_service()
    stubs.drivers._find_one_impl.return_value = {"employee_id": "E1"}
    stubs.drivers._update_one_impl.side_effect = RuntimeError("db err")
    with pytest.raises(RuntimeError):
        await svc.deactivateDriver("E1")

@pytest.mark.asyncio
async def test_activateDriver_success():
    svc, stubs = new_service()
    stubs.drivers._find_one_impl.return_value = {"employee_id": "E1"}
    await svc.activateDriver("E1")
    args, kwargs = stubs.drivers._update_one_impl.call_args
    update_doc = args[1] if len(args) >= 2 else kwargs.get("update", {})
    body = update_doc.get("$set", update_doc)
    assert body["status"] == "available"

@pytest.mark.asyncio
async def test_activateDriver_not_found_raises():
    svc, stubs = new_service()
    stubs.drivers._find_one_impl.return_value = None
    with pytest.raises(ValueError):
        await svc.activateDriver("E404")

# ====================================================================================
# ====================================================================================

@pytest.mark.asyncio
async def test_assign_driver_to_trip_trip_not_found():
    svc, stubs = new_service()
    stubs.trips._find_one_impl.return_value = None
    req = AssignDriverRequest("D1", "V1")
    with pytest.raises(ValueError):
        await svc.assign_driver_to_trip("T404", req, "admin")

@pytest.mark.asyncio
async def test_assign_driver_to_trip_invalid_status():
    svc, stubs = new_service()
    stubs.trips._find_one_impl.return_value = {
        "_id": "T1", "status": TripStatus.COMPLETED,
        "scheduled_start_time": datetime(2025, 9, 1, tzinfo=timezone.utc),
        "scheduled_end_time": datetime(2025, 9, 1, tzinfo=timezone.utc) + timedelta(hours=1)
    }
    req = AssignDriverRequest("D1", "V1")
    with pytest.raises(ValueError):
        await svc.assign_driver_to_trip("T1", req, "admin")

@pytest.mark.asyncio
async def test_assign_driver_to_trip_driver_unavailable(monkeypatch):
    svc, stubs = new_service()
    start = datetime(2025, 9, 1, 9, 0, tzinfo=timezone.utc)
    stubs.trips._find_one_impl.return_value = {"_id": "T1", "status": TripStatus.SCHEDULED,
                                               "scheduled_start_time": start,
                                               "scheduled_end_time": start + timedelta(hours=2)}
    monkeypatch.setattr(svc, "check_driver_availability", AsyncMock(return_value=False))
    req = AssignDriverRequest("D1", "V1")
    with pytest.raises(ValueError):
        await svc.assign_driver_to_trip("T1", req, "admin")

@pytest.mark.asyncio
async def test_assign_driver_to_trip_already_assigned(monkeypatch):
    svc, stubs = new_service()
    start = datetime(2025, 9, 1, 9, 0, tzinfo=timezone.utc)
    stubs.trips._find_one_impl.return_value = {"_id": "T1", "status": TripStatus.SCHEDULED,
                                               "scheduled_start_time": start,
                                               "scheduled_end_time": start + timedelta(hours=2)}
    monkeypatch.setattr(svc, "check_driver_availability", AsyncMock(return_value=True))
    stubs.assigns._find_one_impl.return_value = {"trip_id": "T1", "driver_id": "D1"}
    req = AssignDriverRequest("D1", "V1")
    with pytest.raises(ValueError):
        await svc.assign_driver_to_trip("T1", req, "admin")

@pytest.mark.asyncio
async def test_assign_driver_to_trip_success_with_implicit_8h(monkeypatch):
    svc, stubs = new_service()
    start = datetime(2025, 9, 1, 9, 0, tzinfo=timezone.utc)
    stubs.trips._find_one_impl.return_value = {"_id": "T1", "status": TripStatus.SCHEDULED,
                                               "scheduled_start_time": start,
                                               "scheduled_end_time": None}
    captured = {}
    async def fake_check(driver_id, s, e):
        captured["s"], captured["e"] = s, e
        return True
    monkeypatch.setattr(svc, "check_driver_availability", fake_check)
    stubs.assigns._find_one_impl.return_value = None
    stubs.assigns._delete_many_impl = AsyncMock()
    stubs.assigns._insert_one_impl = AsyncMock(return_value=SimpleNamespace(inserted_id="NEWID"))
    stubs.trips._update_one_impl = AsyncMock()
    req = AssignDriverRequest("D1", "V1", "note")
    assignment = await svc.assign_driver_to_trip("T1", req, "admin")

    assert captured["s"] == start and captured["e"] == start + timedelta(hours=8)
    assert event_publisher.publish_driver_assigned.await_count >= 1
    assert assignment.driver_id == "D1"
    assert assignment.trip_id == "T1"
    assert assignment.vehicle_id == "V1"
    assert assignment._id == "NEWID"

@pytest.mark.asyncio
async def test_assign_driver_to_trip_insert_raises(monkeypatch):
    svc, stubs = new_service()
    start = datetime(2025, 9, 1, 9, 0, tzinfo=timezone.utc)
    stubs.trips._find_one_impl.return_value = {"_id": "T1", "status": TripStatus.SCHEDULED,
                                               "scheduled_start_time": start,
                                               "scheduled_end_time": start + timedelta(hours=1)}
    monkeypatch.setattr(svc, "check_driver_availability", AsyncMock(return_value=True))
    stubs.assigns._find_one_impl.return_value = None
    stubs.assigns._delete_many_impl = AsyncMock()
    stubs.assigns._insert_one_impl.side_effect = RuntimeError("insert fail")
    with pytest.raises(RuntimeError):
        await svc.assign_driver_to_trip("T1", AssignDriverRequest("D1", "V1"), "admin")

# ====================================================================================
# ====================================================================================

@pytest.mark.asyncio
async def test_unassign_driver_no_assignment_returns_false():
    svc, stubs = new_service()
    stubs.assigns._find_one_impl.return_value = None
    ok = await svc.unassign_driver_from_trip("T1", "admin")
    assert ok is False

@pytest.mark.asyncio
async def test_unassign_driver_trip_missing_returns_false():
    svc, stubs = new_service()
    stubs.assigns._find_one_impl.return_value = {"_id": "A1", "driver_id": "D1", "trip_id": "T1"}
    stubs.trips._find_one_impl.return_value = None
    ok = await svc.unassign_driver_from_trip("T1", "admin")
    assert ok is False

@pytest.mark.asyncio
async def test_unassign_driver_in_progress_raises():
    svc, stubs = new_service()
    stubs.assigns._find_one_impl.return_value = {"_id": "A1", "driver_id": "D1", "trip_id": "T1"}
    stubs.trips._find_one_impl.return_value = {"_id": "T1", "status": TripStatus.IN_PROGRESS}
    with pytest.raises(ValueError):
        await svc.unassign_driver_from_trip("T1", "admin")

@pytest.mark.asyncio
async def test_unassign_driver_success():
    svc, stubs = new_service()
    stubs.assigns._find_one_impl.return_value = {"_id": "A1", "driver_id": "D1", "trip_id": "T1"}
    stubs.trips._find_one_impl.return_value = {"_id": "T1", "status": TripStatus.SCHEDULED}
    stubs.assigns._delete_one_impl = AsyncMock()
    stubs.trips._update_one_impl = AsyncMock()
    ok = await svc.unassign_driver_from_trip("T1", "admin")
    assert ok is True
    assert event_publisher.publish_driver_unassigned.await_count >= 1

# ====================================================================================
# ====================================================================================

@pytest.mark.asyncio
async def test_check_driver_availability_true_no_conflicts():
    svc, stubs = new_service()
    stubs.trips._find_impl = lambda *a, **k: _Cursor([])  # no conflicts
    assert await svc.check_driver_availability("D1", datetime.utcnow(), datetime.utcnow() + timedelta(hours=1)) is True

@pytest.mark.asyncio
async def test_check_driver_availability_false_with_conflicts():
    svc, stubs = new_service()
    stubs.trips._find_impl = lambda *a, **k: _Cursor([{"_id": "T1"}])
    assert await svc.check_driver_availability("D1", datetime.utcnow(), datetime.utcnow() + timedelta(hours=1)) is False

@pytest.mark.asyncio
async def test_check_driver_availability_raises_on_error():
    svc, stubs = new_service()
    def _boom(*a, **k): raise RuntimeError("find fail")
    stubs.trips._find_impl = _boom
    with pytest.raises(RuntimeError):
        await svc.check_driver_availability("D1", datetime.utcnow(), datetime.utcnow() + timedelta(hours=1))

# ====================================================================================
# ====================================================================================

@pytest.mark.asyncio
async def test_get_driver_availability_with_ids_mixed(monkeypatch):
    svc, stubs = new_service()
    async def check_av(driver, s, e):
        return driver == "D1" 
    monkeypatch.setattr(svc, "check_driver_availability", check_av)
    stubs.trips._find_impl = lambda *a, **k: _Cursor([{"_id": "T2"}])  
    monkeypatch.setattr(svc, "_find_next_available_time", AsyncMock(return_value=datetime(2025, 9, 2, tzinfo=timezone.utc)))

    req = DriverAvailabilityRequest(
        start_time=datetime(2025, 9, 1, tzinfo=timezone.utc),
        end_time=datetime(2025, 9, 1, 12, tzinfo=timezone.utc),
        driver_ids=["D1", "D2"]
    )
    out = await svc.get_driver_availability(req)
    d1 = next(r for r in out if r["driver_id"] == "D1")
    d2 = next(r for r in out if r["driver_id"] == "D2")
    assert d1["is_available"] is True and "conflicting_trips" not in d1
    assert d2["is_available"] is False and d2["conflicting_trips"] == ["T2"]
    assert isinstance(d2["next_available"], datetime)

@pytest.mark.asyncio
async def test_get_driver_availability_without_ids_uses_active(monkeypatch):
    svc, stubs = new_service()
    monkeypatch.setattr(svc, "_get_all_active_drivers", AsyncMock(return_value=["D3"]))
    monkeypatch.setattr(svc, "check_driver_availability", AsyncMock(return_value=True))
    req = DriverAvailabilityRequest(
        start_time=datetime(2025, 9, 1, tzinfo=timezone.utc),
        end_time=datetime(2025, 9, 1, 12, tzinfo=timezone.utc),
        driver_ids=[]
    )
    out = await svc.get_driver_availability(req)
    assert out == [{"driver_id": "D3", "is_available": True}]

# ====================================================================================
# ====================================================================================

@pytest.mark.asyncio
async def test_get_driver_assignments_active_only_limits_results():
    svc, stubs = new_service()
    stubs.trips._find_impl = lambda *a, **k: _Cursor([{"_id": "T1"}, {"_id": "T2"}])

    def _assigns_find(query):
        docs = [
            {"_id": "A1", "trip_id": "T1", "driver_id": "D1", "vehicle_id": "V1"},
            {"_id": "A3", "trip_id": "T3", "driver_id": "D1", "vehicle_id": "V2"},
        ]
        if "trip_id" in query and isinstance(query["trip_id"], dict) and "$in" in query["trip_id"]:
            allow = set(query["trip_id"]["$in"])
            docs = [d for d in docs if d["trip_id"] in allow]
        return _Cursor(docs)
    stubs.assigns._find_impl = _assigns_find

    out = await svc.get_driver_assignments(driver_id="D1", active_only=True)
    assert len(out) == 1 and out[0]._id == "A1" and out[0].trip_id == "T1"

@pytest.mark.asyncio
async def test_get_driver_assignments_no_active_only_respects_filters():
    svc, stubs = new_service()
    stubs.assigns._find_impl = lambda q: _Cursor([
        {"_id": "A1", "trip_id": "T9", "driver_id": "D9", "vehicle_id": "V1"}
    ])
    out = await svc.get_driver_assignments(driver_id="D9", trip_id="T9", active_only=False)
    assert len(out) == 1 and out[0].driver_id == "D9" and out[0]._id == "A1"

# ====================================================================================
# ====================================================================================

@pytest.mark.asyncio
async def test_get_all_drivers_pagination_and_clean_ids():
    svc, stubs = new_service()
    stubs.drivers._count_docs_impl = AsyncMock(return_value=5)
    stubs.drivers._find_impl = lambda *a, **k: _Cursor([
        {"_id": "X1", "name": "A"}, {"_id": "X2", "name": "B"}, {"_id": "X3", "name": "C"}
    ])
    res = await svc.get_all_drivers(status="available", department="ops", skip=0, limit=2)
    assert res["total"] == 3 and res["has_more"] is True and res["limit"] == 2
    assert res["drivers"][0]["id"] == "X1" and "_id" not in res["drivers"][0]

@pytest.mark.asyncio
async def test_get_all_drivers_empty():
    svc, stubs = new_service()
    stubs.drivers._count_docs_impl = AsyncMock(return_value=0)
    stubs.drivers._find_impl = lambda *a, **k: _Cursor([])
    res = await svc.get_all_drivers()
    assert res["drivers"] == [] and res["total"] == 0 and res["has_more"] is False

# ====================================================================================
# ====================================================================================

@pytest.mark.asyncio
async def test__get_all_active_drivers_unique_and_recent():
    svc, stubs = new_service()
    stubs.assigns._find_impl = lambda q: _Cursor([
        {"driver_id": "D1"}, {"driver_id": "D1"}, {"driver_id": "D2"}
    ])
    ids = await svc._get_all_active_drivers()
    assert sorted(ids) == ["D1", "D2"]

@pytest.mark.asyncio
async def test__get_all_active_drivers_error_returns_empty():
    svc, stubs = new_service()
    def _boom(*a, **k): raise RuntimeError("fail")
    stubs.assigns._find_impl = _boom
    ids = await svc._get_all_active_drivers()
    assert ids == []

# ====================================================================================
# ====================================================================================

@pytest.mark.asyncio
async def test__find_next_available_time_returns_end_time_when_present():
    svc, stubs = new_service()
    end = datetime(2025, 9, 1, 12, tzinfo=timezone.utc)
    stubs.trips._find_impl = lambda q: _Cursor([{"scheduled_end_time": end}])
    got = await svc._find_next_available_time("D1", datetime(2025, 9, 1, 9, tzinfo=timezone.utc))
    assert got == end

@pytest.mark.asyncio
async def test__find_next_available_time_uses_plus_8h_if_no_end():
    svc, stubs = new_service()
    start = datetime(2025, 9, 1, 9, tzinfo=timezone.utc)
    stubs.trips._find_impl = lambda q: _Cursor([{"scheduled_start_time": start, "scheduled_end_time": None}])
    got = await svc._find_next_available_time("D1", start)
    assert got == start + timedelta(hours=8)

@pytest.mark.asyncio
async def test__find_next_available_time_no_conflicts_returns_after_time():
    svc, stubs = new_service()
    stubs.trips._find_impl = lambda q: _Cursor([])
    after = datetime(2025, 9, 1, 15, tzinfo=timezone.utc)
    got = await svc._find_next_available_time("D1", after)
    assert got == after

@pytest.mark.asyncio
async def test__find_next_available_time_error_returns_none():
    svc, stubs = new_service()
    def _boom(*a, **k): raise RuntimeError("find fail")
    stubs.trips._find_impl = _boom
    got = await svc._find_next_available_time("D1", datetime(2025, 9, 1, tzinfo=timezone.utc))
    assert got is None