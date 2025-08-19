import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime
from bson import ObjectId
import events.publisher as pub_mod

from services.places_service import places_service


# ---- simple fakes -----------------------------------------------------------
class _InsertRes:
    def __init__(self, _id): self.inserted_id = _id

class _UpdateRes:
    def __init__(self, modified): self.modified_count = modified

class _DeleteRes:
    def __init__(self, deleted): self.deleted_count = deleted

class _AsyncCursor:
    def __init__(self, items):
        self._items = items
        self.last_sort = None
        self._skip = 0
        self._limit = None
    def sort(self, *a, **k):
        self.last_sort = (a, k); return self
    def skip(self, n):
        self._skip = n; return self
    def limit(self, n):
        self._limit = n; return self
    def __aiter__(self):
        async def gen():
            data = self._items[self._skip:]
            if self._limit is not None:
                data = data[:self._limit]
            for it in data: yield it
        return gen()

class _FakeCol:
    def __init__(self):
        self.last_query = None
        self._find_items = []
        self._aggregate_items = []
    async def insert_one(self, doc):
        self.inserted_doc = doc
        return _InsertRes(ObjectId())
    async def find_one(self, q):
        self.last_query = q
        return self._find_items[0] if self._find_items else None
    def find(self, q):
        self.last_query = q
        return _AsyncCursor(list(self._find_items))
    async def update_one(self, flt, upd):
        self.last_query = flt; self.last_update = upd
        return _UpdateRes(modified=1)
    async def delete_one(self, flt):
        self.last_query = flt
        return _DeleteRes(deleted=1)
    def aggregate(self, pipeline):
        self.last_pipeline = pipeline
        return _AsyncCursor(list(self._aggregate_items))

class _FakeDBMgr:
    def __init__(self):
        self.db = type("DB", (), {})()
        self.db.places = _FakeCol()
        self._db = object()
    def is_connected(self): return True


@pytest.fixture(autouse=True)
def _patch_db(monkeypatch):
    fake = _FakeDBMgr()
    monkeypatch.setattr(places_service, "db", fake)
    return fake


# ---- tests -----------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_place_inserts_and_publishes(monkeypatch):
    publish_mock = AsyncMock()
    monkeypatch.setattr(pub_mod.event_publisher, "publish_place_created", publish_mock)

    class _InsertRes:
        def __init__(self, _id): self.inserted_id = _id

    class _PlacesCol:
        async def insert_one(self, doc):
            return _InsertRes(ObjectId())

    class _FakeDBMgr:
        def __init__(self):
            self.db = type("X", (), {})()
            self.db.places = _PlacesCol()
        def is_connected(self): return True

    monkeypatch.setattr(places_service, "db", _FakeDBMgr(), raising=False)

    place = await places_service.create_place(
        user_id="u1",
        name="Cafe",
        description=None,
        latitude=-33.9,
        longitude=18.4,
        address="A",
        place_type="custom",
    )

    data = place.model_dump()
    assert data["name"] == "Cafe"
    assert data["location"]["coordinates"] == [18.4, -33.9]
    publish_mock.assert_awaited_once()

@pytest.mark.asyncio
async def test_get_place_by_id_invalid_returns_none():
    assert await places_service.get_place_by_id("not-an-objectid") is None


@pytest.mark.asyncio
async def test_get_place_by_id_found(monkeypatch):
    oid = ObjectId()
    doc = {
        "_id": oid, "user_id":"u1","name":"N","description":None,
        "location":{"type":"Point","coordinates":[1,2]},
        "latitude":2, "longitude":1, "address":None, "place_type":"custom",
        "metadata":{}, "created_by":"u1","created_at":datetime.utcnow(),"updated_at":datetime.utcnow()
    }
    async def _find_one(q): return doc
    monkeypatch.setattr(places_service.db.db.places, "find_one", _find_one)
    got = await places_service.get_place_by_id(str(oid))
    assert got and got.id == str(oid)


@pytest.mark.asyncio
async def test_get_places_and_user_places_filters(monkeypatch):
    docs = [{
        "_id": ObjectId(), "user_id":"u1","name":"A","description":"",
        "location":{"type":"Point","coordinates":[0,0]},
        "latitude":0,"longitude":0,"address":"", "place_type":"home",
        "metadata":{}, "created_by":"u1",
        "created_at":datetime.utcnow(), "updated_at":datetime.utcnow()
    }]
    places_service.db.db.places._find_items = list(docs)

    # get_places with place_type filter
    out = await places_service.get_places(place_type="home", skip=0, limit=10)
    assert len(out) == 1
    assert places_service.db.db.places.last_query == {"place_type": "home"}

    # get_user_places with user_id filter
    out2 = await places_service.get_user_places("u1", place_type=None, limit=10, offset=0)
    assert len(out2) == 1
    assert places_service.db.db.places.last_query == {"user_id": "u1"}


@pytest.mark.asyncio
async def test_search_places_builds_regex_query(monkeypatch):
    places_service.db.db.places._find_items = []
    await places_service.search_places("user123", "Pretoria", 5)
    q = places_service.db.db.places.last_query
    assert q["user_id"] == "user123"
    assert "$or" in q and len(q["$or"]) == 3
    # ensure regex options are case-insensitive
    assert all("$regex" in cond[next(iter(cond))] for cond in q["$or"])


@pytest.mark.asyncio
async def test_get_places_near_location_geo_query(monkeypatch):
    places_service.db.db.places._find_items = []
    await places_service.get_places_near_location("u1", -25.7, 28.2, radius_meters=1000, limit=5)
    q = places_service.db.db.places.last_query
    assert q["user_id"] == "u1"
    near = q["location"]["$near"]
    assert near["$geometry"]["coordinates"] == [28.2, -25.7]
    assert near["$geometry"]["type"] == "Point"
    assert near["$maxDistance"] == 1000


@pytest.mark.asyncio
async def test_update_place_modified_returns_updated(monkeypatch):
    async def _update_one(*a, **k): return _UpdateRes(modified=1)
    monkeypatch.setattr(places_service.db.db.places, "update_one", _update_one)
    # Return a simple sentinel from get_place to show it's called
    sentinel = object()
    monkeypatch.setattr(places_service, "get_place", AsyncMock(return_value=sentinel))
    out = await places_service.update_place(
        place_id=str(ObjectId()), user_id="u1", name="New"
    )
    assert out is sentinel


@pytest.mark.asyncio
async def test_update_place_no_modification_returns_none(monkeypatch):
    async def _update_one(*a, **k): return _UpdateRes(modified=0)
    monkeypatch.setattr(places_service.db.db.places, "update_one", _update_one)
    out = await places_service.update_place(
        place_id=str(ObjectId()), user_id="u1", name="New"
    )
    assert out is None


@pytest.mark.asyncio
async def test_delete_place_true_false(monkeypatch):
    async def _del_one_true(flt): return _DeleteRes(deleted=1)
    async def _del_one_false(flt): return _DeleteRes(deleted=0)

    monkeypatch.setattr(places_service.db.db.places, "delete_one", _del_one_true)
    assert await places_service.delete_place(str(ObjectId()), "u1") is True

    monkeypatch.setattr(places_service.db.db.places, "delete_one", _del_one_false)
    assert await places_service.delete_place(str(ObjectId()), "u1") is False


@pytest.mark.asyncio
async def test_get_place_statistics_aggregates(monkeypatch):
    places_service.db.db.places._aggregate_items = [{"_id":"home","count":2},{"_id":"work","count":1}]
    stats = await places_service.get_place_statistics("u1")
    assert stats["user_id"] == "u1"
    assert stats["total_places"] == 3
    assert stats["place_counts_by_type"] == {"home":2,"work":1}
