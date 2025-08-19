import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta
from bson import ObjectId
import events.publisher as pub_mod
from services.location_service import location_service


# ---- fakes -----------------------------------------------------------------
class _InsertRes: 
    def __init__(self, _id): self.inserted_id = _id
class _UpdateRes: 
    def __init__(self, modified): self.modified_count = modified
class _DeleteRes:
    def __init__(self, deleted): self.deleted_count = deleted

class _AsyncCursor:
    def __init__(self, items):
        self._items = items
        self._limit = None
        self._sort = None
    def sort(self, *a, **k): self._sort = (a,k); return self
    def limit(self, n): self._limit = n; return self
    def __aiter__(self):
        async def gen():
            data = self._items
            if self._limit is not None: data = data[:self._limit]
            for it in data: yield it
        return gen()
    # used by get_vehicle_route
    async def to_list(self, length=None):
        return self._items[:length] if length else list(self._items)

class _FindRoute:
    def __init__(self, items): self._items=items
    def sort(self, *_, **__): return self
    async def to_list(self, length=None):
        return self._items[:length] if length else list(self._items)

class _Col:
    def __init__(self):
        self.last_query = None
        self._items = []
    async def insert_one(self, doc): 
        self.inserted = doc; return _InsertRes(ObjectId())
    async def find_one(self, q):
        self.last_query = q
        return dict(self._items[0]) if self._items else None
    def find(self, q):
        self.last_query = q
        # convert stored docs to list
        return _AsyncCursor(list(self._items))
    async def update_one(self, flt, upd, **kwargs):
        self.last_query = flt; self.last_update = upd
        return _UpdateRes(modified=1)
    async def update_many(self, flt, upd): 
        self.last_update_many = (flt,upd); return _UpdateRes(modified=1)
    async def delete_one(self, flt): 
        self.last_query = flt; return _DeleteRes(deleted=1)
    async def delete_many(self, flt):
        self.last_query = flt; return _DeleteRes(deleted=len(self._items))

class _MgmtVehicles:
    def __init__(self, docs=None): self._docs = docs or []
    def find(self, q): 
        class _C:
            def __init__(self, docs): self._docs = docs
            async def to_list(self, length=None): 
                return self._docs[:length] if length else list(self._docs)
        return _C(list(self._docs))

class _FakeDBMgr:
    def __init__(self):
        self.db = type("DB", (), {})()
        self.db.vehicle_locations = _Col()
        self.db.location_history = _Col()
        self.db.tracking_sessions = _Col()
        self._db = object()
        self._connected = True
    def is_connected(self): return self._connected

class _FakeMgmt:
    def __init__(self): self.vehicles = _MgmtVehicles([])


@pytest.fixture(autouse=True)
def _patch_dbs(monkeypatch):
    fake = _FakeDBMgr()
    mgmt = _FakeMgmt()
    monkeypatch.setattr(location_service, "db", fake)
    monkeypatch.setattr(location_service, "db_management", mgmt)
    return fake


# ---- tests -----------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_vehicle_location_inserts_and_publishes(monkeypatch):
    publish_mock = AsyncMock()
    monkeypatch.setattr(pub_mod.event_publisher, "publish_location_created", publish_mock)

    out = await location_service.create_vehicle_location("v1", 1.0, 2.0)
    assert out.vehicle_id == "v1"
    publish_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_vehicle_location_upsert_and_history(monkeypatch):
    publish_mock = AsyncMock()
    monkeypatch.setattr(pub_mod.event_publisher, "publish_location_updated", publish_mock)

    out = await location_service.update_vehicle_location("v1", 1.0, 2.0)
    assert out.vehicle_id == "v1"
    publish_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_vehicle_location_found_and_not_found(monkeypatch):
    doc = {
        "_id": ObjectId(), "vehicle_id":"v1",
        "location":{"type":"Point","coordinates":[2.0,1.0]},
        "latitude":1.0,"longitude":2.0,"altitude":None,"speed":None,"heading":None,"accuracy":None,
        "timestamp":datetime.utcnow(),"updated_at":datetime.utcnow()
    }
    location_service.db.db.vehicle_locations._items = [doc]
    got = await location_service.get_vehicle_location("v1")
    assert got and got.vehicle_id == "v1"
    # none
    location_service.db.db.vehicle_locations._items = []
    assert await location_service.get_vehicle_location("v1") is None


@pytest.mark.asyncio
async def test_get_multiple_vehicle_locations(monkeypatch):
    docs = [{
        "_id": ObjectId(), "vehicle_id":"v2",
        "location":{"type":"Point","coordinates":[0,0]},
        "latitude":0,"longitude":0,"altitude":None,"speed":0,"heading":0,"accuracy":None,
        "timestamp":datetime.utcnow(),"updated_at":datetime.utcnow()
    }]
    location_service.db.db.vehicle_locations._items = docs
    out = await location_service.get_multiple_vehicle_locations(["v2"])
    assert len(out) == 1 and out[0].vehicle_id == "v2"


@pytest.mark.asyncio
async def test_get_location_history_with_filters(monkeypatch):
    location_service.db.db.location_history._items = []
    start, end = datetime.utcnow() - timedelta(days=1), datetime.utcnow()
    await location_service.get_location_history("v1", start_time=start, end_time=end, limit=10)
    q = location_service.db.db.location_history.last_query
    assert q["vehicle_id"] == "v1"
    assert set(q["timestamp"].keys()) == {"$gte", "$lte"}


@pytest.mark.asyncio
async def test_get_vehicles_in_area_builds_query(monkeypatch):
    location_service.db.db.vehicle_locations._items = []
    await location_service.get_vehicles_in_area(-25.7, 28.2, 500)
    q = location_service.db.db.vehicle_locations.last_query
    assert "$geoWithin" in q["location"]
    center_sphere = q["location"]["$geoWithin"]["$centerSphere"]
    assert center_sphere[0] == [28.2, -25.7]
    assert pytest.approx(center_sphere[1], rel=1e-3) == 500/6378100


@pytest.mark.asyncio
async def test_start_and_end_tracking_session(monkeypatch):
    # start
    out = await location_service.start_tracking_session("v1", "u1")
    assert out.vehicle_id == "v1" and out.user_id == "u1"
    # end
    async def _update_one(flt, upd):
        return _UpdateRes(modified=1)
    monkeypatch.setattr(location_service.db.db.tracking_sessions, "update_one", _update_one)
    assert await location_service.end_tracking_session(str(ObjectId())) is True


@pytest.mark.asyncio
async def test_get_active_tracking_sessions_filter_by_user(monkeypatch):
    docs = [{
        "_id": ObjectId(),
        "vehicle_id":"v1","user_id":"u1","is_active":True,
        "started_at":datetime.utcnow(),"created_at":datetime.utcnow()
    }]
    location_service.db.db.tracking_sessions._items = docs
    out = await location_service.get_active_tracking_sessions("u1")
    assert len(out) == 1
    assert location_service.db.db.tracking_sessions.last_query == {"is_active": True, "user_id": "u1"}


@pytest.mark.asyncio
async def test_cleanup_old_locations_skips_when_not_connected(monkeypatch):
    location_service.db._connected = False
    # should not set last_query
    await location_service.cleanup_old_locations(days_to_keep=1)
    assert location_service.db.db.location_history.last_query is None


@pytest.mark.asyncio
async def test_cleanup_old_locations_deletes_when_connected(monkeypatch):
    location_service.db._connected = True
    await location_service.cleanup_old_locations(days_to_keep=1)
    assert "timestamp" in location_service.db.db.location_history.last_query


@pytest.mark.asyncio
async def test_validate_tracking_sessions_skips_when_no_db(monkeypatch):
    location_service.db._connected = True
    # simulate missing underlying DB instance
    location_service.db._db = None
    await location_service.validate_tracking_sessions()
    # since _db is None, nothing should be set
    assert not hasattr(location_service.db.db.tracking_sessions, "last_update_many")


@pytest.mark.asyncio
async def test_get_vehicle_route_no_locations_returns_empty(monkeypatch):
    class _Hist:
        def find(self, q): return _FindRoute([])
    location_service.db.db.location_history = _Hist()
    out = await location_service.get_vehicle_route("v1")
    assert out["vehicle_id"] == "v1"
    assert out["total_points"] == 0 and out["distance_km"] == 0


@pytest.mark.asyncio
async def test_get_vehicle_route_two_points_has_points(monkeypatch):
    t0 = datetime.utcnow() - timedelta(hours=1)
    t1 = datetime.utcnow()
    docs = [
        {"latitude": 0.0, "longitude": 0.0, "timestamp": t0},
        {"latitude": 0.0, "longitude": 0.01, "timestamp": t1},
    ]
    class _Hist:
        def find(self, q): return _FindRoute(docs)
    location_service.db.db.location_history = _Hist()
    out = await location_service.get_vehicle_route("v1", start_time=t0, end_time=t1)
    assert out["total_points"] == 2
    assert out["route"][0]["timestamp"] <= out["route"][1]["timestamp"]


@pytest.mark.asyncio
async def test_start_vehicle_tracking_already_active(monkeypatch):
    async def _find_one(q): return {"_id": ObjectId(), "started_at": datetime.utcnow(), "is_active": True}
    monkeypatch.setattr(location_service.db.db.tracking_sessions, "find_one", _find_one)
    out = await location_service.start_vehicle_tracking("v9")
    assert out["status"] == "already_active"
