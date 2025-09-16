import sys
import types
import importlib
import importlib.util
from pathlib import Path
import pytest
from datetime import datetime, timedelta

SERVICE_IMPORT_CANDIDATES = [
    "gps.services.location_service",
    "trip_planning.services.location_service",
    "services.location_service",
    "location_service",
]

def _compute_fallback_service_path() -> str | None:
    here = Path(__file__).resolve()
    for i in range(0, min(10, len(here.parents))):
        base = here.parents[i]
        for p in (
            base / "services" / "location_service.py",
            base / "gps" / "services" / "location_service.py",
        ):
            if p.exists():
                return str(p)
    return None

FALLBACK_SERVICE_PATH = _compute_fallback_service_path()

class FakeInsertResult:
    def __init__(self, inserted_id="fake_oid"):
        self.inserted_id = inserted_id

class FakeUpdateResult:
    def __init__(self, modified_count=1):
        self.modified_count = modified_count

class FakeDeleteResult:
    def __init__(self, deleted_count=1):
        self.deleted_count = deleted_count

class FakeCursor:
    def __init__(self, docs):
        self._docs = list(docs)
        self.sort_args = None
        self.limit_n = None

    def sort(self, key, direction):
        self.sort_args = (key, direction)
        try:
            self._docs.sort(key=lambda d: d.get(key), reverse=(direction == -1))
        except Exception:
            pass
        return self

    def limit(self, n):
        self.limit_n = n
        if n is not None:
            self._docs = self._docs[:n]
        return self

    async def to_list(self, length):
        if length is not None:
            return self._docs[:length]
        return list(self._docs)

    def __aiter__(self):
        async def gen():
            for d in self._docs:
                yield d
        return gen()

class FakeCollection:
    def __init__(self):
        self.last_find_query = None
        self.last_update_filter = None
        self.last_update_doc = None
        self.last_delete_filter = None
        self.last_insert_doc = None

        self.find_docs = []
        self.find_raises = False
        self.find_one_doc = None
        self.find_one_raises = False

        self.update_one_result = FakeUpdateResult(1)
        self.update_many_result = FakeUpdateResult(1)
        self.delete_one_result = FakeDeleteResult(1)
        self.delete_many_result = FakeDeleteResult(1)
        self.insert_result = FakeInsertResult("oid123")

    def set_find_docs(self, docs): self.find_docs = list(docs)
    def set_find_raises(self, b=True): self.find_raises = b
    def set_find_one_doc(self, doc): self.find_one_doc = doc
    def set_find_one_raises(self, b=True): self.find_one_raises = b
    def set_update_one_result(self, n): self.update_one_result = FakeUpdateResult(n)
    def set_update_many_result(self, n): self.update_many_result = FakeUpdateResult(n)
    def set_delete_one_result(self, n): self.delete_one_result = FakeDeleteResult(n)
    def set_delete_many_result(self, n): self.delete_many_result = FakeDeleteResult(n)
    def set_insert_id(self, oid): self.insert_result = FakeInsertResult(oid)

    async def insert_one(self, doc):
        self.last_insert_doc = doc
        return self.insert_result

    def find(self, query):
        if self.find_raises:
            raise RuntimeError("find blew up")
        self.last_find_query = query
        return FakeCursor(self.find_docs)

    async def find_one(self, flt):
        if self.find_one_raises:
            raise RuntimeError("find_one blew up")
        self.last_find_query = flt
        return self.find_one_doc

    async def update_one(self, flt, update, **kwargs):
        self.last_update_filter = flt
        self.last_update_doc = update
        return self.update_one_result

    async def update_many(self, flt, update):
        self.last_update_filter = flt
        self.last_update_doc = update
        return self.update_many_result

    async def delete_one(self, flt):
        self.last_delete_filter = flt
        return self.delete_one_result

    async def delete_many(self, flt):
        self.last_delete_filter = flt
        return self.delete_many_result

class FakeVehiclesCollection:
    def __init__(self, items=None, raise_on_find=False):
        self.items = list(items or [])
        self.raise_on_find = raise_on_find

    class _FindChain:
        def __init__(self, items, raise_on):
            self.items = items
            self.raise_on = raise_on
        async def to_list(self, length=None):
            if self.raise_on:
                raise RuntimeError("vehicles find failed")
            return list(self.items)

    def find(self, q):
        return self._FindChain(self.items, self.raise_on_find)

class FakeDB:
    def __init__(self):
        self.name = "fake_db"
        self.vehicle_locations = FakeCollection()
        self.location_history = FakeCollection()
        self.tracking_sessions = FakeCollection()

class FakeDBManager:
    def __init__(self, connected=True, db_present=True):
        self._connected = connected
        self._db = object() if db_present else None
        self.db = FakeDB()
    def is_connected(self): return self._connected

class FakeDBManagement:
    def __init__(self, vehicles_items=None, raise_on_find=False):
        self.vehicles = FakeVehiclesCollection(vehicles_items, raise_on_find)

def make_fake_entities_module():
    mod = types.ModuleType("schemas.entities")

    class VehicleLocation:
        def __init__(self, **kwargs):
            for k, v in kwargs.items(): setattr(self, k, v)

    class LocationHistory:
        def __init__(self, **kwargs):
            for k, v in kwargs.items(): setattr(self, k, v)

    class TrackingSession:
        def __init__(self, **kwargs):
            for k, v in kwargs.items(): setattr(self, k, v)

    mod.VehicleLocation = VehicleLocation
    mod.LocationHistory = LocationHistory
    mod.TrackingSession = TrackingSession
    return mod

def make_fake_events_module(raise_created=False, raise_updated=False, raise_tracking=False, calls_sink=None):
    pub = types.ModuleType("events.publisher")

    calls = calls_sink if calls_sink is not None else []

    class _Publisher:
        def __init__(self): self.calls = calls

        async def publish_location_created(self, **kwargs):
            if raise_created: raise RuntimeError("publish created failed")
            self.calls.append(("created", kwargs))

        async def publish_location_updated(self, **kwargs):
            if raise_updated: raise RuntimeError("publish updated failed")
            self.calls.append(("updated", kwargs))

        async def publish_tracking_event(self, **kwargs):
            if raise_tracking: raise RuntimeError("publish tracking failed")
            self.calls.append(("tracking", kwargs))

    pub.event_publisher = _Publisher()
    return pub

def make_fake_bson_module(store=None):
    m = types.ModuleType("bson")
    class ObjectId:
        def __init__(self, s):
            if store is not None:
                store["last_oid_arg"] = s
            self._s = s
        def __str__(self): return self._s
        def __repr__(self): return f"FakeObjectId({self._s!r})"
    m.ObjectId = ObjectId
    return m

class SysModulesSandbox:
    def __init__(self, *, db_connected=True, db_present=True,
                 events_raise_created=False, events_raise_updated=False, events_raise_tracking=False,
                 publisher_calls=None, bson_store=None, vehicles_items=None, vehicles_raise=False):
        self.db_connected = db_connected
        self.db_present = db_present
        self.events_raise_created = events_raise_created
        self.events_raise_updated = events_raise_updated
        self.events_raise_tracking = events_raise_tracking
        self.publisher_calls = publisher_calls if publisher_calls is not None else []
        self.bson_store = bson_store if bson_store is not None else {}
        self.vehicles_items = vehicles_items or []
        self.vehicles_raise = vehicles_raise
        self._orig = None
        self.db_manager = None
        self.db_manager_management = None

    def __enter__(self):
        self._orig = sys.modules.copy()

        repositories_pkg = types.ModuleType("repositories")
        db_mod = types.ModuleType("repositories.database")
        self.db_manager = FakeDBManager(connected=self.db_connected, db_present=self.db_present)
        self.db_manager_management = FakeDBManagement(self.vehicles_items, self.vehicles_raise)
        db_mod.db_manager = self.db_manager
        db_mod.db_manager_management = self.db_manager_management

        schemas_pkg = types.ModuleType("schemas")
        entities_mod = make_fake_entities_module()

        events_pkg = types.ModuleType("events")
        publisher_mod = make_fake_events_module(
            raise_created=self.events_raise_created,
            raise_updated=self.events_raise_updated,
            raise_tracking=self.events_raise_tracking,
            calls_sink=self.publisher_calls
        )

        bson_mod = make_fake_bson_module(store=self.bson_store)

        sys.modules["repositories"] = repositories_pkg
        sys.modules["repositories.database"] = db_mod
        sys.modules["schemas"] = schemas_pkg
        sys.modules["schemas.entities"] = entities_mod
        sys.modules["events"] = events_pkg
        sys.modules["events.publisher"] = publisher_mod
        sys.modules["bson"] = bson_mod

        return self

    def __exit__(self, exc_type, exc, tb):
        sys.modules.clear()
        sys.modules.update(self._orig)


def import_service_module():
    last_err = None
    for name in SERVICE_IMPORT_CANDIDATES:
        try:
            if name in sys.modules: del sys.modules[name]
            return importlib.import_module(name)
        except Exception as e:
            last_err = e
    if FALLBACK_SERVICE_PATH:
        spec = importlib.util.spec_from_file_location("location_service", FALLBACK_SERVICE_PATH)
        mod = importlib.util.module_from_spec(spec)
        if "location_service" in sys.modules:
            del sys.modules["location_service"]
        spec.loader.exec_module(mod)  
        return mod
    raise last_err or ImportError("Unable to import location_service")


# ========== Tests ==========

# --- _build_location_doc ---

def test_build_location_doc_has_lon_lat_and_updated_at():
    with SysModulesSandbox() as sb:
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        ts = datetime(2025, 1, 1, 12, 0, 0)
        doc = svc._build_location_doc("veh1", 10.5, 20.25, 100.0, 55.0, 90.0, 3.0, ts)
        assert doc["location"]["coordinates"] == [20.25, 10.5]
        assert doc["timestamp"] == ts
        assert "updated_at" in doc


# --- delete_vehicle_location ---

@pytest.mark.asyncio
async def test_delete_vehicle_location_true():
    with SysModulesSandbox() as sb:
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        sb.db_manager.db.vehicle_locations.set_delete_one_result(1)
        ok = await svc.delete_vehicle_location("v1")
        assert ok is True
        assert sb.db_manager.db.vehicle_locations.last_delete_filter == {"vehicle_id": "v1"}

@pytest.mark.asyncio
async def test_delete_vehicle_location_false():
    with SysModulesSandbox() as sb:
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        sb.db_manager.db.vehicle_locations.set_delete_one_result(0)
        ok = await svc.delete_vehicle_location("v2")
        assert ok is False

@pytest.mark.asyncio
async def test_delete_vehicle_location_raises():
    class Boom(FakeCollection):
        async def delete_one(self, flt): raise RuntimeError("boom")
    with SysModulesSandbox() as sb:
        sb.db_manager.db.vehicle_locations = Boom()
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        with pytest.raises(RuntimeError):
            await svc.delete_vehicle_location("v3")


# --- create_vehicle_location ---

@pytest.mark.asyncio
async def test_create_vehicle_location_inserts_current_and_history_and_publishes():
    calls = []
    with SysModulesSandbox(publisher_calls=calls) as sb:
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        sb.db_manager.db.vehicle_locations.set_insert_id("cafebabe")
        ts = datetime(2025, 1, 2, 0, 0, 0)
        model = await svc.create_vehicle_location("vehA", 1.0, 2.0, speed=10.0, timestamp=ts)
        ins = sb.db_manager.db.vehicle_locations.last_insert_doc
        assert ins["location"]["type"] == "Point"
        assert ins["location"]["coordinates"] == [2.0, 1.0]
        assert sb.db_manager.db.location_history.last_insert_doc is not None
        assert ("created", dict) == (calls[0][0], type(calls[0][1]).__name__.__class__.__mro__[0].__name__.__class__) or calls[0][0] == "created"
        assert model._id == "cafebabe"

@pytest.mark.asyncio
async def test_create_vehicle_location_publisher_failure_swallowed():
    with SysModulesSandbox(events_raise_created=True) as sb:
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        model = await svc.create_vehicle_location("vehB", 1.0, 2.0)
        assert getattr(model, "_id", None) is not None  

@pytest.mark.asyncio
async def test_create_vehicle_location_timestamp_auto_now():
    with SysModulesSandbox() as sb:
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        model = await svc.create_vehicle_location("vehC", 5.0, 6.0)
        assert isinstance(model.timestamp, datetime)


# --- get_all_vehicle_locations ---

@pytest.mark.asyncio
async def test_get_all_vehicle_locations_empty_list():
    with SysModulesSandbox() as sb:
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        sb.db_manager.db.vehicle_locations.set_find_docs([])
        res = await svc.get_all_vehicle_locations()
        assert res == []

@pytest.mark.asyncio
async def test_get_all_vehicle_locations_nonempty():
    with SysModulesSandbox() as sb:
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        sb.db_manager.db.vehicle_locations.set_find_docs([{"_id": "OID1", "vehicle_id": "v1", "latitude": 1, "longitude": 2}])
        res = await svc.get_all_vehicle_locations()
        assert len(res) == 1
        assert res[0]._id == "OID1"

@pytest.mark.asyncio
async def test_get_all_vehicle_locations_raises():
    class Boom(FakeCollection):
        def find(self, q): raise RuntimeError("boom")
    with SysModulesSandbox() as sb:
        sb.db_manager.db.vehicle_locations = Boom()
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        with pytest.raises(RuntimeError):
            await svc.get_all_vehicle_locations()


# --- update_vehicle_location ---

@pytest.mark.asyncio
async def test_update_vehicle_location_upsert_and_history_and_publish():
    calls = []
    with SysModulesSandbox(publisher_calls=calls) as sb:
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        ts = datetime(2025, 1, 3, 0, 0, 0)
        model = await svc.update_vehicle_location("vehD", 9.0, 8.0, speed=30.0, timestamp=ts)
        upd = sb.db_manager.db.vehicle_locations.last_update_doc["$set"]
        assert upd["location"]["coordinates"] == [8.0, 9.0]
        assert sb.db_manager.db.location_history.last_insert_doc is not None
        assert sb.db_manager.db.vehicle_locations.last_update_filter == {"vehicle_id": "vehD"}
        assert ("updated" in [c[0] for c in calls])
        assert isinstance(model.timestamp, datetime)

@pytest.mark.asyncio
async def test_update_vehicle_location_publisher_failure_swallowed():
    with SysModulesSandbox(events_raise_updated=True) as sb:
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        model = await svc.update_vehicle_location("vehE", 1, 1)
        assert isinstance(model, object)

@pytest.mark.asyncio
async def test_update_vehicle_location_raises_on_db_error():
    class Boom(FakeCollection):
        async def update_one(self, *a, **k): raise RuntimeError("boom")
    with SysModulesSandbox() as sb:
        sb.db_manager.db.vehicle_locations = Boom()
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        with pytest.raises(RuntimeError):
            await svc.update_vehicle_location("vehX", 0, 0)


# --- get_vehicle_location ---

@pytest.mark.asyncio
async def test_get_vehicle_location_found():
    with SysModulesSandbox() as sb:
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        sb.db_manager.db.vehicle_locations.set_find_one_doc({"_id": "OID2", "vehicle_id": "v2", "latitude": 3, "longitude": 4})
        res = await svc.get_vehicle_location("v2")
        assert res._id == "OID2"

@pytest.mark.asyncio
async def test_get_vehicle_location_not_found_returns_none():
    with SysModulesSandbox() as sb:
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        sb.db_manager.db.vehicle_locations.set_find_one_doc(None)
        res = await svc.get_vehicle_location("v3")
        assert res is None

@pytest.mark.asyncio
async def test_get_vehicle_location_raises_on_db_error():
    with SysModulesSandbox() as sb:
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        sb.db_manager.db.vehicle_locations.set_find_one_raises(True)
        with pytest.raises(RuntimeError):
            await svc.get_vehicle_location("v4")


# --- get_multiple_vehicle_locations ---

@pytest.mark.asyncio
async def test_get_multiple_vehicle_locations_returns_many():
    with SysModulesSandbox() as sb:
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        docs = [{"_id": "A", "vehicle_id":"v1"}, {"_id":"B", "vehicle_id":"v2"}]
        sb.db_manager.db.vehicle_locations.set_find_docs(docs)
        res = await svc.get_multiple_vehicle_locations(["v1","v2"])
        assert [r._id for r in res] == ["A","B"]
        assert sb.db_manager.db.vehicle_locations.last_find_query == {"vehicle_id":{"$in":["v1","v2"]}}

@pytest.mark.asyncio
async def test_get_multiple_vehicle_locations_raises_on_db_error():
    class Boom(FakeCollection):
        def find(self, q): raise RuntimeError("boom")
    with SysModulesSandbox() as sb:
        sb.db_manager.db.vehicle_locations = Boom()
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        with pytest.raises(RuntimeError):
            await svc.get_multiple_vehicle_locations(["v"])


# --- get_location_history ---

@pytest.mark.asyncio
async def test_get_location_history_no_filters():
    with SysModulesSandbox() as sb:
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        sb.db_manager.db.location_history.set_find_docs([{"_id":"H1","vehicle_id":"v1","timestamp":datetime(2025,1,1)}])
        res = await svc.get_location_history("v1")
        assert len(res) == 1
        assert sb.db_manager.db.location_history.last_find_query == {"vehicle_id":"v1"}

@pytest.mark.asyncio
async def test_get_location_history_start_only():
    with SysModulesSandbox() as sb:
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        s = datetime(2025,1,1)
        await svc.get_location_history("v1", start_time=s)
        assert sb.db_manager.db.location_history.last_find_query == {"vehicle_id":"v1","timestamp":{"$gte":s}}

@pytest.mark.asyncio
async def test_get_location_history_end_only():
    with SysModulesSandbox() as sb:
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        e = datetime(2025,2,1)
        await svc.get_location_history("v1", end_time=e)
        assert sb.db_manager.db.location_history.last_find_query == {"vehicle_id":"v1","timestamp":{"$lte":e}}

@pytest.mark.asyncio
async def test_get_location_history_start_and_end():
    with SysModulesSandbox() as sb:
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        s = datetime(2025,1,1); e = datetime(2025,2,1)
        await svc.get_location_history("v1", start_time=s, end_time=e)
        assert sb.db_manager.db.location_history.last_find_query == {"vehicle_id":"v1","timestamp":{"$gte":s,"$lte":e}}

@pytest.mark.asyncio
async def test_get_location_history_raises_on_db_error():
    class Boom(FakeCollection):
        def find(self, q): raise RuntimeError("boom")
    with SysModulesSandbox() as sb:
        sb.db_manager.db.location_history = Boom()
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        with pytest.raises(RuntimeError):
            await svc.get_location_history("v1")


# --- get_vehicles_in_area ---

@pytest.mark.asyncio
async def test_get_vehicles_in_area_builds_query_and_returns_docs():
    with SysModulesSandbox() as sb:
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        sb.db_manager.db.vehicle_locations.set_find_docs([{"_id":"V1","vehicle_id":"v1"}])
        res = await svc.get_vehicles_in_area(10.0, 20.0, 1000.0)
        q = sb.db_manager.db.vehicle_locations.last_find_query
        assert "location" in q and "$geoWithin" in q["location"]
        sphere = q["location"]["$geoWithin"]["$centerSphere"]
        assert sphere[0] == [20.0, 10.0]
        assert abs(sphere[1] - (1000.0/6378100)) < 1e-12
        assert len(res) == 1 and res[0]._id == "V1"

@pytest.mark.asyncio
async def test_get_vehicles_in_area_raises_on_db_error():
    class Boom(FakeCollection):
        def find(self, q): raise RuntimeError("boom")
    with SysModulesSandbox() as sb:
        sb.db_manager.db.vehicle_locations = Boom()
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        with pytest.raises(RuntimeError):
            await svc.get_vehicles_in_area(0,0,1)


# --- start_tracking_session ---

@pytest.mark.asyncio
async def test_start_tracking_session_happy_path():
    with SysModulesSandbox() as sb:
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        sb.db_manager.db.tracking_sessions.set_insert_id("TS1")
        model = await svc.start_tracking_session("vehS", "user1")
        assert isinstance(model, sb.db_manager.db.__class__.__name__.__class__) or hasattr(model, "vehicle_id")
        assert sb.db_manager.db.tracking_sessions.last_update_filter == {"vehicle_id":"vehS","is_active":True}
        assert sb.db_manager.db.tracking_sessions.last_insert_doc["vehicle_id"] == "vehS"
        assert sb.db_manager.db.tracking_sessions.insert_result.inserted_id == "TS1"

@pytest.mark.asyncio
async def test_start_tracking_session_raises_on_db_error():
    class Boom(FakeCollection):
        async def update_many(self, *a, **k): raise RuntimeError("boom")
    with SysModulesSandbox() as sb:
        sb.db_manager.db.tracking_sessions = Boom()
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        with pytest.raises(RuntimeError):
            await svc.start_tracking_session("veh", "user")


# --- end_tracking_session ---

@pytest.mark.asyncio
async def test_end_tracking_session_true_and_false():
    store = {}
    with SysModulesSandbox(bson_store=store) as sb:
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        sb.db_manager.db.tracking_sessions.set_update_one_result(1)
        ok = await svc.end_tracking_session("ABCDEF1234567890ABCDEF12")
        assert ok is True
        assert store["last_oid_arg"] == "ABCDEF1234567890ABCDEF12"
        sb.db_manager.db.tracking_sessions.set_update_one_result(0)
        ok2 = await svc.end_tracking_session("ABCDEF1234567890ABCDEF12")
        assert ok2 is False

@pytest.mark.asyncio
async def test_end_tracking_session_raises_on_db_error():
    class Boom(FakeCollection):
        async def update_one(self, *a, **k): raise RuntimeError("boom")
    with SysModulesSandbox() as sb:
        sb.db_manager.db.tracking_sessions = Boom()
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        with pytest.raises(RuntimeError):
            await svc.end_tracking_session("id")


# --- get_active_tracking_sessions ---

@pytest.mark.asyncio
async def test_get_active_tracking_sessions_with_and_without_user():
    with SysModulesSandbox() as sb:
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        sb.db_manager.db.tracking_sessions.set_find_docs([{"_id":"S1","is_active":True,"user_id":"u1"}])
        res = await svc.get_active_tracking_sessions()
        assert len(res) == 1 and res[0]._id == "S1"
        # with user filter
        await svc.get_active_tracking_sessions(user_id="u1")
        assert sb.db_manager.db.tracking_sessions.last_find_query == {"is_active":True,"user_id":"u1"}

@pytest.mark.asyncio
async def test_get_active_tracking_sessions_raises_on_db_error():
    class Boom(FakeCollection):
        def find(self, q): raise RuntimeError("boom")
    with SysModulesSandbox() as sb:
        sb.db_manager.db.tracking_sessions = Boom()
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        with pytest.raises(RuntimeError):
            await svc.get_active_tracking_sessions()


# --- cleanup_old_locations ---

@pytest.mark.asyncio
async def test_cleanup_old_locations_skips_when_not_connected():
    with SysModulesSandbox(db_connected=False) as sb:
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        await svc.cleanup_old_locations(days_to_keep=7)
        assert sb.db_manager.db.location_history.last_delete_filter is None  

@pytest.mark.asyncio
async def test_cleanup_old_locations_skips_when_db_none():
    with SysModulesSandbox(db_present=False) as sb:
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        await svc.cleanup_old_locations(days_to_keep=7)
        assert sb.db_manager.db.location_history.last_delete_filter is None

@pytest.mark.asyncio
async def test_cleanup_old_locations_calls_delete_and_handles_counts_and_errors():
    with SysModulesSandbox() as sb:
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        sb.db_manager.db.location_history.set_delete_many_result(5)
        await svc.cleanup_old_locations(days_to_keep=1)
        flt = sb.db_manager.db.location_history.last_delete_filter
        assert "timestamp" in flt and "$lt" in flt["timestamp"]
    with SysModulesSandbox() as sb:
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        sb.db_manager.db.location_history.set_delete_many_result(0)
        await svc.cleanup_old_locations(days_to_keep=1)
    class Boom(FakeCollection):
        async def delete_many(self, flt): raise RuntimeError("boom")
    with SysModulesSandbox() as sb:
        sb.db_manager.db.location_history = Boom()
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        await svc.cleanup_old_locations(days_to_keep=1)  


# --- validate_tracking_sessions ---

@pytest.mark.asyncio
async def test_validate_tracking_sessions_guards_and_updates_and_errors():
    with SysModulesSandbox(db_connected=False) as sb:
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        await svc.validate_tracking_sessions()
        assert sb.db_manager.db.tracking_sessions.last_update_doc is None
    with SysModulesSandbox(db_present=False) as sb:
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        await svc.validate_tracking_sessions()
        assert sb.db_manager.db.tracking_sessions.last_update_doc is None
    with SysModulesSandbox() as sb:
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        sb.db_manager.db.tracking_sessions.set_update_many_result(3)
        await svc.validate_tracking_sessions()
        assert sb.db_manager.db.tracking_sessions.last_update_doc is not None
    class Boom(FakeCollection):
        async def update_many(self, flt, upd): raise RuntimeError("boom")
    with SysModulesSandbox() as sb:
        sb.db_manager.db.tracking_sessions = Boom()
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        await svc.validate_tracking_sessions() 


# --- get_vehicle_route ---

@pytest.mark.asyncio
async def test_get_vehicle_route_empty():
    with SysModulesSandbox() as sb:
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        sb.db_manager.db.location_history.set_find_docs([])
        class CursorWithToList(FakeCursor):
            async def to_list(self, length): return []
        def find(q): return CursorWithToList([])
        sb.db_manager.db.location_history.find = find
        start = datetime(2025,1,1); end = datetime(2025,1,2)
        res = await svc.get_vehicle_route("vehR", start_time=start, end_time=end)
        assert res["total_points"] == 0 and res["distance_km"] == 0

@pytest.mark.asyncio
async def test_get_vehicle_route_with_points_and_distance_rounding(monkeypatch):
    with SysModulesSandbox() as sb:
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()

        pts = [
            {"latitude": 0.0, "longitude": 0.0, "timestamp": datetime(2025,1,1,0,0,0), "speed": 10, "heading": 0},
            {"latitude": 0.0, "longitude": 1.0, "timestamp": datetime(2025,1,1,1,0,0), "speed": 20, "heading": 90},
            {"latitude": 1.0, "longitude": 1.0, "timestamp": datetime(2025,1,1,2,0,0), "speed": 30, "heading": 180},
        ]

        class CursorWithToList(FakeCursor):
            async def to_list(self, length): return pts

        def find(q): return CursorWithToList(pts)

        sb.db_manager.db.location_history.find = find

        async def fake_distance(*a, **k): pass
        def _fake_calc(lat1, lon1, lat2, lon2):
            if lat1 == 0.0 and lon1 == 0.0 and lat2 == 0.0 and lon2 == 1.0: return 100.004
            return 50.004
        svc._calculate_distance = _fake_calc

        start = datetime(2025,1,1); end = datetime(2025,1,2)
        res = await svc.get_vehicle_route("vehR", start_time=start, end_time=end)
        assert res["total_points"] == 3
        assert res["distance_km"] == 150.01
        assert res["route"][0]["timestamp"].endswith("00:00:00")

@pytest.mark.asyncio
async def test_get_vehicle_route_error_handling():
    class BadCursor:
        def sort(self, *a, **k): raise RuntimeError("boom")
    class BadHistory(FakeCollection):
        def find(self, q): return BadCursor()
    with SysModulesSandbox() as sb:
        sb.db_manager.db.location_history = BadHistory()
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        start = datetime(2025,1,1); end = datetime(2025,1,2)
        res = await svc.get_vehicle_route("veh", start_time=start, end_time=end)
        assert res["total_points"] == 0 and res["distance_km"] == 0 and "error" in res


# --- start_vehicle_tracking (public tracking) ---

@pytest.mark.asyncio
async def test_start_vehicle_tracking_already_active():
    with SysModulesSandbox() as sb:
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        sb.db_manager.db.tracking_sessions.set_find_one_doc({"_id":"EXIST","is_active":True,"started_at":datetime(2025,1,1)})
        res = await svc.start_vehicle_tracking("vehZ")
        assert res["status"] == "already_active"
        assert res["session_id"] == "EXIST"
        assert "started_at" in res

@pytest.mark.asyncio
async def test_start_vehicle_tracking_started_and_publish_ok():
    with SysModulesSandbox() as sb:
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        sb.db_manager.db.tracking_sessions.set_find_one_doc(None)
        sb.db_manager.db.tracking_sessions.set_insert_id("NEWTS")
        res = await svc.start_vehicle_tracking("vehZ")
        assert res["status"] == "started" and res["session_id"] == "NEWTS"

@pytest.mark.asyncio
async def test_start_vehicle_tracking_publish_failure_swallowed():
    with SysModulesSandbox(events_raise_tracking=True) as sb:
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        sb.db_manager.db.tracking_sessions.set_find_one_doc(None)
        res = await svc.start_vehicle_tracking("vehZ")
        assert res["status"] == "started"

@pytest.mark.asyncio
async def test_start_vehicle_tracking_db_error_returns_error_status():
    class Boom(FakeCollection):
        async def find_one(self, flt): raise RuntimeError("boom")
    with SysModulesSandbox() as sb:
        sb.db_manager.db.tracking_sessions = Boom()
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        res = await svc.start_vehicle_tracking("vehZ")
        assert res["status"] == "error"


# --- get_all_vehicles (management DB) ---

@pytest.mark.asyncio
async def test_get_all_vehicles_success_and_error():
    with SysModulesSandbox(vehicles_items=[{"id":"1"},{"id":"2"}]) as sb:
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        res = await svc.get_all_vehicles()
        assert len(res) == 2
    with SysModulesSandbox(vehicles_raise=True) as sb:
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        res = await svc.get_all_vehicles()
        assert res == []


# --- _calculate_distance smoke test ---

def test_calculate_distance_smoke():
    with SysModulesSandbox() as sb:
        svc_mod = import_service_module()
        svc = svc_mod.LocationService()
        d = svc._calculate_distance(0, 0, 0, 1)  
        assert 100 < d < 130
